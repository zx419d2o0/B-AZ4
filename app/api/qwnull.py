from fastapi import APIRouter, Response
from curl_cffi import requests
from bs4 import BeautifulSoup
import ddddocr

from databases.kv import kv
from core.file_helper import file_manager

router = APIRouter()

ocr = ddddocr.DdddOcr(show_ad=False)

class Qiwei:
    def __init__(self):
        self.url =  kv.redis.get('site:url:qn63')
        if not self.url:
            html = requests.get('https://www.qn63.com').text
            soup = BeautifulSoup(html, "html.parser")
            self.url = soup.select('a[href]')[0].get('href')
            if self.url:
                kv.redis.set('site:url:qn63', self.url, ex=60*60*24*3)
        cookie = kv.redis.get('site:cookie:qn63')
        self.headers = { "Cookie": cookie }

    def get_captcha(self) -> tuple[bytes, str]:
        response = requests.get(self.url + '/verify/index.html', headers=self.headers)
        digits = recognize_captcha(response.content)
        return response.content, digits
    
    def check_captcha(self) -> str:
        pass
    
    def verify_captcha(self, captcha: str) -> bool:
        headers = {
            **self.headers,
            "X-Requested-With": "XMLHttpRequest"
        }
        response = requests.post(
            self.url + '/index.php/ajax/verify_check?',
            params={"type": "search", "verify": captcha},
            headers=headers,
            )
        return response.json()

def recognize_captcha(image_bytes: bytes) -> str:
    # ddddocr directly supports raw image bytes
    try:
        text = ocr.classification(image_bytes)
    except Exception as e:
        print("[OCR ERROR] type(image_bytes):", type(image_bytes))
        print("[OCR ERROR] len(image_bytes):", len(image_bytes) if image_bytes else 0)
        print("[OCR ERROR] exception:", repr(e))
        text = ""

    if not text:
        return ""

    return text

@router.get("/qnve")
async def pass_verify():
    qw = Qiwei()

    for i in range(10):
        content, captcha = qw.get_captcha()
        captcha = captcha.replace(" ", "")
        print(f'第{i+1}次尝试[{captcha}]')

        if not (captcha.isdigit() and len(captcha) == 4):
            continue

        result = qw.verify_captcha(captcha)
        if isinstance(result, dict) and result.get("code") == 1:
            file_manager.save_file(f"qiwei_captcha/{captcha}.png", content)
            return captcha
        else:
            print(captcha, result.get("msg"))

    return Response(content=content, media_type='image/png')