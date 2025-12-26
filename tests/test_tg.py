from urllib.request import Request, urlopen
from urllib.parse import urlencode

def test_search_message():
    payload = {
        "channel": "tgsearchers4,wydwpzy",
        "keyword": "非自然死亡"
    }
    data = urlencode(payload).encode("utf-8")
    req = Request(
        url="http://localhost:43210/svc/get-tg-message",
        data=data,
        method="POST",
    )

    with urlopen(req) as resp:
        assert resp.status == 200
        print(resp.read().decode("utf-8"))