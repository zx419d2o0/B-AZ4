from enum import Enum
from json import loads
from urllib.parse import urlencode
from urllib.request import urlopen, Request

class YYW:
    def __init__(self):
        self._payload = None

    def get_enum_name(self, val, cls):
        if isinstance(val, cls):
            return val.name
        try:
            if isinstance(val, str):
                return cls[val].name
        except KeyError:
            pass
        return cls(val).name

    def get_qrcode_token(self):
        """获取登录二维码，扫码可用
        GET https://qrcodeapi.115.com/api/1.0/web/1.0/token/
        :return: dict
        """
        api = "https://qrcodeapi.115.com/api/1.0/web/1.0/token/"
        return loads(urlopen(api).read())

    def get_qrcode_status(self, payload):
        """获取二维码的状态（未扫描、已扫描、已登录、已取消、已过期等）
        GET https://qrcodeapi.115.com/get/status/
        :param payload: 请求的查询参数，取自 `login_qrcode_token` 接口响应，有 3 个
            - uid:  str
            - time: int
            - sign: str
        :return: dict
        """
        api = "https://qrcodeapi.115.com/get/status/?" + urlencode(payload)
        return loads(urlopen(api).read())

    def post_qrcode_result(self, uid, app="web"):
        """获取扫码登录的结果，并且绑定设备，包含 cookie
        POST https://passportapi.115.com/app/1.0/{app}/1.0/login/qrcode/
        :param uid: 二维码的 uid，取自 `login_qrcode_token` 接口响应
        :param app: 扫码绑定的设备，可以是 int、str 或者 AppEnum
            app 目前发现的可用值：
                - 1,  "web",        AppEnum.web
                - 2,  "android",    AppEnum.android
                - 3,  "ios",        AppEnum.ios
                - 4,  "linux",      AppEnum.linux
                - 5,  "mac",        AppEnum.mac
                - 6,  "windows",    AppEnum.windows
                - 7,  "tv",         AppEnum.tv
                - 8,  "alipaymini", AppEnum.alipaymini
                - 9,  "wechatmini", AppEnum.wechatmini
                - 10, "qandroid",   AppEnum.qandroid
        :return: dict，包含 cookie
        """
        app = self.get_enum_name(app, AppEnum)
        payload = {"app": app, "account": uid}
        api = "https://passportapi.115.com/app/1.0/%s/1.0/login/qrcode/" % app
        return loads(urlopen(Request(api, data=urlencode(payload).encode("utf-8"), method="POST")).read())

    def get_qrcode(self, uid):
        """获取二维码图片（注意不是链接）
        :return: 一个可读的 bytes 对象
        """
        url = "https://qrcodeapi.115.com/api/1.0/mac/1.0/qrcode?uid=%s" % uid
        return urlopen(url)

    def start_login(self):
        """启动一个二维码登录会话并返回二维码图片 bytes 和会话 payload（uid/time/sign）。
        该方法**不阻塞**。Bot 负责把二维码发送给用户，之后使用 check_login_status 查询状态。
        返回格式:
            {
                "qrcode": bytes,       # 二维码图片数据
                "payload": dict        # 用于后续查询状态的 payload（uid,time,sign）
            }
        """
        data = self.get_qrcode_token()["data"]
        # data 包含 qrcode, uid, time, sign 等字段
        # 保留 payload（uid,time,sign）供后续轮询使用
        payload = {k: v for k, v in data.items() if k != "qrcode"}
        self._payload = payload
        uid = payload["uid"]
        img_bytes = self.get_qrcode(uid).read()
        return {"qrcode": img_bytes, "payload": payload}

    def check_login_status(self, app="web"):
        """使用 start_login 返回的 payload 查询二维码当前状态。
        返回值示例：
            {"status": <int>}  # status 为 -2/-1/0/1/2
        当 status == 2 时，会额外返回登录结果：
            {"status": 2, "result": <post_qrcode_result 返回值>}
        """
        if not self._payload:
            return {"error": "missing payload"}

        resp = self.get_qrcode_status(self._payload)
        status = resp.get("data", {}).get("status")

        if status == 2:
            # 登录成功，调用 post_qrcode_result 取得 cookie 等信息
            uid = self._payload.get("uid")
            login_result = self.post_qrcode_result(uid, app)
            return {"status": 2, "result": login_result}

        return {"status": status}

AppEnum = Enum("AppEnum", "web, android, ios, linux, mac, windows, tv, alipaymini, wechatmini, qandroid")
pan115 = YYW()