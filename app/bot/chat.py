from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from telebot.async_telebot import AsyncTeleBot
    from telebot.types import Message
# from loguru import logger
from services.google import gemini
from core.string_helper import split_markdown


# genai.configure(api_key=os.getenv("BARD_API_KEY"))
# model = genai.GenerativeModel('gemini-2.0-flash-exp')
# chat = model.start_chat(history=[])
# logger.add("cache/logs/file_{time}.log", rotation="1 day", retention=7)
def all_text_without_command(message: 'Message') -> bool:
    return message.content_type == 'text' and not message.text.startswith('/')

def register_handler(bot: 'AsyncTeleBot'):
    @bot.message_handler(func=all_text_without_command)
    async def gemini_google(message: 'Message'):
        """
        Handle all other messages
        """
        content = await gemini.ask(message.text)
        parts = split_markdown(content)
        # print('count of parts: ', len(parts))
        for part in parts:
            # print('length of part: ', len(part))
            try:
                await bot.reply_to(message, part, parse_mode='markdown')
            except Exception as e:
                print(len(part), e)
                await bot.reply_to(message, part)