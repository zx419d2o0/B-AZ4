import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import PeerChannel, Message
from core.config import config

class Telegram:
    _client_instance = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.str_session = config.TG_SESSION
        self.api_id = config.TG_API_ID
        self.api_hash = config.TG_API_HASH

        if not self.api_id or not self.api_hash:
            raise RuntimeError("TG_API_ID / TG_API_HASH not set")

        if Telegram._client_instance is None:
            Telegram._client_instance = TelegramClient(
                StringSession(self.str_session),
                self.api_id,
                self.api_hash,
                # proxy=('SOCKS5', '192.168.3.11', 7891)
            )
        self.client = Telegram._client_instance

    async def ensure_connected(self):
        async with Telegram._lock:
            if not self.client.is_connected():
                await self.client.start()

    async def get_channel(self, channel_id: int):
        await self.ensure_connected()
        if isinstance(channel_id, str):
            channel_id = int(channel_id)
        return await self.client.get_entity(PeerChannel(channel_id))

    async def search_messages(
        self,
        channel: str,
        search: str = '',
        limit: int = 10,
    ) -> list[str]:
        """
        搜索指定频道中包含关键词的消息

        :param channel: 频道 username / 链接 / id
                        例如: 'durov', 'https://t.me/durov'
        :param keyword: 要搜索的关键词
        :param limit: 返回的消息数量限制
        """
        await self.ensure_connected()
        messages: list[Message] = await self.client.get_messages(channel, search=search, limit=limit)
        return [message.message for message in messages]

telegram = Telegram()