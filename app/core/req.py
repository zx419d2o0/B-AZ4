import aiohttp
import asyncio
import json
from functools import wraps
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class HttpResponse:
    url: str
    status_code: int
    headers: Dict[str, str]
    body: Optional[str] = None
    content: Optional[bytes] = None
    error: Optional[str] = None

    @property
    def text(self) -> str:
        return self.body or ""

    def json(self) -> Dict[str, Any]:
        if not self.body:
            return {"error": "Empty response"}
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return {"error": "JSON parse error", "body": self.body}


# 定义重试装饰器
def retry(retries: int = 3, backoff_factor: float = 1.0, status_forcelist=None):
    if status_forcelist is None:
        status_forcelist = [429, 500, 502, 503, 504]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            attempt = 0
            while attempt <= retries:
                try:
                    return await func(self, *args, **kwargs)
                except (aiohttp.ClientError, aiohttp.ServerTimeoutError) as e:
                    if attempt == retries:
                        raise e
                    attempt += 1
                    backoff_time = backoff_factor * (2 ** (attempt - 1))
                    print(f"Retrying request... (Attempt {attempt}/{retries})")
                    await asyncio.sleep(backoff_time)
        return wrapper
    return decorator


class HttpClient:
    def __init__(self, default_headers: Optional[dict] = None):
        self.default_headers = default_headers or {}

    async def _send(self, method: str, url: str, headers: Optional[dict] = None, **kwargs) -> HttpResponse:
        # 合并传入的 headers 和默认的 headers
        headers = {**self.default_headers, **(headers or {})}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method, url, headers=headers, **kwargs) as response:
                    body = await response.text()
                    content = await response.read()
                    return HttpResponse(
                        url=str(response.real_url),
                        status_code=response.status,
                        headers=dict(response.request_info.headers),
                        body=body,
                        content=content if body == "" else None,  # 避免文本响应占用 `content`
                    )
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"[{url}] params={kwargs.get('params')} -> (error={e})")
                raise e

    @retry()  # 添加重试装饰器
    async def request(self, method: str, url: str, headers: Optional[dict] = None, **kwargs) -> HttpResponse:
        """
        请求方法，支持 GET、POST、HEAD、DELETE
        """
        response = await self._send(method, url, headers=headers, **kwargs)
        return response  # 返回 JSON 数据，其他类型的响应可以自行处理

    async def get(self, url: str, headers: Optional[dict] = None, **kwargs) -> HttpResponse:
        """发起 GET 请求"""
        return await self.request('GET', url, headers=headers, **kwargs)

    async def post(self, url: str, headers: Optional[dict] = None, **kwargs) -> HttpResponse:
        """发起 POST 请求"""
        return await self.request('POST', url, headers=headers, **kwargs)

    async def head(self, url: str, headers: Optional[dict] = None, **kwargs) -> HttpResponse:
        """发起 HEAD 请求"""
        return await self.request('HEAD', url, headers=headers, **kwargs)

    async def delete(self, url: str, headers: Optional[dict] = None, **kwargs) -> HttpResponse:
        """发起 DELETE 请求"""
        return await self.request('DELETE', url, headers=headers, **kwargs)

http_client = HttpClient()