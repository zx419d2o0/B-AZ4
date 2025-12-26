from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from telebot.async_telebot import AsyncTeleBot
    from telebot.types import Message


def register_handler(bot: 'AsyncTeleBot'):
    @bot.message_handler(commands=['start'])
    async def send_welcome(message: 'Message'):
        await bot.reply_to(message, """
Use Less BOT
""")