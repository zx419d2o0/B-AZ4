from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_helper
import asyncio
import os

from app.bot.local import register_handlers
from app.bot.middleware import Middleware
from app.core.config import config


def create_app() -> AsyncTeleBot:
    if os.uname().sysname == 'Linux':
        bot = AsyncTeleBot(config.BOT_HTTP_TOKEN_NEW)
    else:
        bot = AsyncTeleBot(config.BOT_HTTP_TOKEN_TEST)
    asyncio_helper.proxy = 'http://192.168.3.11:7893'
    print('Using proxy:', asyncio_helper.proxy)
    register_handlers(bot)
    bot.setup_middleware(Middleware(bot))
    return bot

def run():
    print('Bot is debugging...')
    bot = create_app()
    asyncio.run(bot.polling())

if __name__ == '__main__':
    run()

app = create_app()