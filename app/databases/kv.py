import redis
from fastapi import APIRouter, Request
from core.config import config

class KV:
    def __init__(self):
        self._r = None

    @property
    def redis(self):
        if self._r is None:
            self._r = redis.Redis.from_url(config.REDIS_URL)
        return self._r
    
    def print(self):
        keys = self.redis.keys("*")  # 获取所有以 "news:" 开头的 key
        for key in keys:
            ttl = self.redis.ttl(key)  # 获取 key 的剩余有效时间（秒）
            print(f"Key: {key}, TTL: {ttl} seconds")
            break
        print("Total keys: ", len(keys))
    
    def flush_db(self):
        self.redis.flushdb()

kv = KV()
router = APIRouter()

@router.post("/kv-get")
async def kv_get(request: Request):
    form = await request.form()
    key = form.get('key')
    
    if not key:
        return {"error": "missing key parameter"}

    return kv.redis.get(key)