from fastapi import APIRouter, Response
from curl_cffi import requests
from bs4 import BeautifulSoup
from paddleocr import PaddleOCR
import numpy as np
import cv2

from databases.kv import kv
from core.file_helper import file_manager

router = APIRouter()

ocr = PaddleOCR(lang='en')

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

    def get_captcha(self) -> str:
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
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    result = ocr.predict(image)

    text = ""
    if isinstance(result, list) and result:
        item = result[0]
        if isinstance(item, dict) and "rec_texts" in item:
            text = "".join(item["rec_texts"])
        else:
            text = str(item)

    # remove spaces
    text = text.replace(" ", "")

    return text

@router.get("/qnve")
async def pass_verify():
    qw = Qiwei()

    for i in range(10):
        content, captcha = qw.get_captcha()
        captcha = captcha.replace(" ", "")
        # 2️⃣ 格式校验（必须4位数字）
        print(f'第{i+1}次尝试[{captcha}]')

        if not (captcha.isdigit() and len(captcha) == 4):
            continue

        # 3️⃣ 提交验证
        result = qw.verify_captcha(captcha)

        # 4️⃣ 判断结果
        if isinstance(result, dict):
            if result.get("code") == 1:
                file_manager.save_file(f"qiwei_captcha/{captcha}.png", content)
                return captcha
            else:
                print(captcha, result.get("msg"))

    return Response(content=content, media_type='image/png')