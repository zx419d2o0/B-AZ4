from fastapi import Request
import logging
from datetime import datetime


# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def middleware(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    end_time = datetime.now()
    info = {
        'interface': request.scope["path"],
        'status_code': response.status_code,
        'source_ip': request.client.host,
         start_time.strftime('%Y-%m-%d %H:%M:%S'): f'{(end_time - start_time).total_seconds()*1000:.2f}(ms)'
    }

    logger.info('-'.join([f"[{key}:{val}]" for key, val in info.items()]))
    
    return response