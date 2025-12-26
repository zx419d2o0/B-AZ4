from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from telebot.async_telebot import AsyncTeleBot
    from telebot.types import Message
from services.pan_yyw import pan115

CHAT_PAYLOADS = {}

def register_handler(bot: 'AsyncTeleBot'):
    @bot.message_handler(commands=['115login'])
    async def login(message: 'Message'):
        data = pan115.start_login()
        await bot.send_photo(message.chat.id, data["qrcode"])

    @bot.message_handler(commands=['115token'])
    async def token(message: 'Message'):
        info = pan115.check_login_status("qandroid")

        status = info.get("status")
        if status == -2:
            await bot.send_message(message.chat.id, "二维码已取消 (-2)")
        elif status == -1:
            await bot.send_message(message.chat.id, "二维码已过期 (-1)，请重新 /115login")
        elif status == 0:
            await bot.send_message(message.chat.id, "等待扫码 (0)")
        elif status == 1:
            await bot.send_message(message.chat.id, "已扫描，请在手机确认 (1)")
        elif status == 2:
            cookie = info.get("result").get('cookie')
            cookies = "; ".join("%s=%s" % t for t in cookie.items())
            await bot.send_message(message.chat.id, f"登录成功！\nToken: {cookies}")
        else:
            await bot.send_message(message.chat.id, f"未知状态：{status}")