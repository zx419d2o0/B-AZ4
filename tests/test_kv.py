import pytest
from app.databases.kv import KV
from urllib.request import Request, urlopen
from urllib.parse import urlencode

@pytest.fixture(scope='session')
def kv():
    return KV()

def test_get(kv):
    key = "vod:drive_a115"
    print('key:', kv.redis.get(key), 'ttl:', kv.redis.ttl(key))

def test_kv_get():
    payload = {
        "key": "vod:drive_a115"
    }
    data = urlencode(payload).encode("utf-8")
    req = Request(
        url="http://localhost:43210/kv-get",
        data=data,
        method="POST",
    )

    with urlopen(req) as resp:
        assert resp.status == 200
        print(resp.read().decode("utf-8"))