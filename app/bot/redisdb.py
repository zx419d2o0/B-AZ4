from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from telebot.async_telebot import AsyncTeleBot
    from telebot.types import Message
from databases.kv import kv as db

# 命令名称，例如：/redis set key value
cmd_redis = "redis"

def register_handler(bot: 'AsyncTeleBot'):
    @bot.message_handler(commands=[cmd_redis])
    async def redis_handler(message: 'Message'):
        """
        用法：
            /redis set key value
        （仅支持 set，用于存储敏感数据）
        """
        text = message.text.split(maxsplit=3)
        # text 示例: ['/redis', 'set', 'key', 'value']
        if len(text) < 4:
            await bot.reply_to(message, "用法错误：\n/redis set key value")
            return

        action = text[1].lower()
        key = text[2]

        # set 操作
        if action == "set":
            try:
                value = text[3].encode().decode("unicode_escape")
                db.redis.set(key, value)
                ttl = db.redis.ttl(key)
                await bot.reply_to(message, f"已保存: {ttl}")
            except Exception as e:
                await bot.reply_to(message, f"保存失败：{e}")
            return

        await bot.reply_to(message, "未知操作，仅支持 set")