from fastapi import APIRouter, Request
from services.telegram import telegram
import asyncio

router = APIRouter()

@router.post("/get-tg-message")
async def get_tg_messages(request: Request):
    form = await request.form()
    channel = form.get('channel')
    keyword = form.get('keyword')
    count = form.get('count', 10)
    if not channel:
        return {"error": "channel is required"}
    
    channels = channel.split(',')
    tasks = [telegram.search_messages(ch, keyword, count) for ch in channels]
    results = await asyncio.gather(*tasks)
    messages = {channels[i]: results[i] for i in range(len(channels))}
    return messages