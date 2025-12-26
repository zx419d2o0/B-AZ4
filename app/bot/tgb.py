from fastapi import APIRouter, Request
from telebot.async_telebot import AsyncTeleBot
from core.config import config
import telebot
import importlib

router = APIRouter()
bot = AsyncTeleBot(config.BOT_HTTP_TOKEN)
MODULES = ["chat", "git_search", "others", "welcome", "redisdb"]
for mod in MODULES:
    module = importlib.import_module(f'bot.{mod}')
    module.register_handler(bot)

@router.post(f'/webhook')
async def process_webhook(update: dict):
    """
    Process webhook calls
    """
    if update:
        update = telebot.types.Update.de_json(update)
        await bot.process_new_updates([update])
    else:
        return
    
@router.post(f'/set_webhook')
async def set_webhook(request: Request):
    form = await request.form()
    try:
        await bot.set_webhook(url=form.get('url'))
        return 'ok'
    except Exception as e:
        return 'error'
    
@router.post(f'/get_webhook')
async def get_webhook():
    try:
        info = await bot.get_webhook_info()
        return info
    except Exception as e:
        return 'error'
    
@router.post(f'/del_webhook')
async def del_webhook():
    try:
        await bot.delete_webhook()
        return 'ok'
    except Exception as e:
        return 'error'

@router.post('/push')
async def push(request: Request):
    form = await request.form()
    try:
        chat_id = form.get('id', config.TG_ADMIN_ID)
        message: str = form.get('message', '')
        photo: str = form.get('photo', '')
        html: str = form.get('html', '')
        if photo:
            await bot.send_photo(chat_id, photo=photo, caption=message)
        elif html:
            await bot.send_message(chat_id, html, parse_mode='html')  
        else:
            await bot.send_message(chat_id, message)
        return 'ok'
    except Exception as e:
        return 'error'
    
def form_or_json(request: Request) -> dict:
    if "application/json" in request.headers.get("Content-Type"):
        return request.json()
    else:
        return request.form()

@router.post("/trigger")
async def trigger_bot(request: Request):
    try:
        form = await form_or_json(request)
        id = form.get('id')
        chat_id = form.get('chat_id', config.TG_ADMIN_ID)
        text = form.get('text', '')
        # 创建一个伪造的 Telegram 消息对象
        json_message = {
            "message": {
                "message_id": id,
                "chat": {
                    "id": chat_id or config.TG_ADMIN_ID,
                    "type": ""
                },
                "date": "",
                "text": text
            },
            "update_id": ""
        }

        # 调用 Telegram bot handler 处理消息
        # 手动调用 handler
        await bot.process_new_updates([telebot.types.Update.de_json(json_message)])

        return {"message": "Bot handled the message successfully!"}
    except Exception as e:
        print(e)
        return {"error": "An error occurred while triggering the bot.", "log": e}
