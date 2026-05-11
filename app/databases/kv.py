import redis
from fastapi import APIRouter, Request
from core.config import config

class KV:
    def __init__(self):
        self._r = None

    @property
    def redis(self):
        if self._r is None:
            self._r = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
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

@router.post("/kv-set")
async def kv_set(request: Request):
    form = await request.form()
    key = form.get('key')
    value = form.get('value')
    ttl = form.get('ttl')

    if not key or value is None:
        return {"error": "missing key or value parameter"}

    try:
        ttl = int(ttl) if ttl is not None else 60 * 60 * 24 * 7
    except Exception:
        ttl = 60 * 60 * 24 * 7

    kv.redis.set(key, value, ex=ttl)

    return {
        "key": key,
        "ttl": ttl
    }

@router.post("/kv-get")
async def kv_get(request: Request):
    form = await request.form()
    key = form.get('key')
    
    if not key:
        return {"error": "missing key parameter"}

    return kv.redis.get(key)