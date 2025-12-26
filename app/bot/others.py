from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from telebot.async_telebot import AsyncTeleBot
    from telebot.types import Message
from core.req import http_client
from databases.kv import kv
from datetime import datetime
import asyncio


def register_handler(bot: 'AsyncTeleBot'):
    @bot.message_handler(commands=['today'])
    async def today(message: 'Message'):
        current_date = datetime.now()
        formatted_date = current_date.strftime("%Y-%m-%d")
        req_rili = http_client.get('https://www.36jxs.com/api/Commonweal/almanac', params={'sun': formatted_date}, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'})
        req_60s = http_client.get('https://60s-api.viki.moe/v2/60s')
        res_rili, res_60s = await asyncio.gather(req_rili, req_60s)

        parts = []
        if res_rili.status_code == 200:
            json_data: dict = res_rili.json().get('data', {})
            content = f"农历 {json_data.get('LMonth')}{json_data.get('LDay')} {json_data.get('SolarTermName')}\n"
            parts.append(content)
        if res_60s.status_code == 200:
            json_data = res_60s.json().get('data', {})
            cover = json_data.get('cover')
            parts += [f'· {x}' for x in json_data.get('news', [])]
        await bot.send_photo(message.chat.id, cover or 'https://www.xvfr.com/60s.php', '\n'.join(parts))

    @bot.message_handler(commands=['news'])
    async def news(message: 'Message'):
        news = []
        req_toutiao = http_client.get('http://60s-api.viki.moe/v2/toutiao')
        req_weibo = http_client.get('https://60s-api.viki.moe/v2/weibo')
        req_douyin = http_client.get('https://60s-api.viki.moe/v2/douyin')
        res_toutiao, res_weibo, res_douyin = await asyncio.gather(req_toutiao, req_weibo, req_douyin)

        # news.append('\n头条热榜')
        json_data: list[dict] = res_toutiao.json().get('data', [])
        # news += [f"· {x.get('title')} <a href='{x.get('link')}'>🔗</a>" for x in json_data[:10]]
        news += filter_news(json_data, 10, '头条热榜')

        # news.append('\n微博热搜')
        json_data = res_weibo.json().get('data', [])
        # news += [f"· {x.get('title')} <a href='{x.get('link')}'>🔗</a>" for x in json_data[:10]]
        news += filter_news(json_data, 10, '微博热搜')

        # news.append('\n抖音热榜')
        json_data = res_douyin.json().get('data', [])
        # news += [f"· {x.get('title')} <a href='{x.get('link')}'>🔗</a>" for x in json_data[:10]]
        news += filter_news(json_data, 10, '抖音热榜')

        content = '\n'.join([f'{x}' for x in news])
        await bot.send_message(message.chat.id, content, disable_web_page_preview=True, parse_mode='HTML')

def filter_news(data: list[dict], total: int = 10, title: str = '') -> list[str]:
    result = [f'\n{title}']
    count = 0
    for news in data:
        if count >= total:
            break
        added = kv.redis.setnx(news.get('link'), news.get('title')) 
        if added:
            kv.redis.expire(news.get('link'), 86400)
            count += 1
            result.append(f"· {news.get('title')} <a href='{news.get('link')}'>🔗</a>")
    if count == 0:
        return []
    return result