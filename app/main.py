import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from core.middleware import middleware
from bot.tgb import router as bot_router
from databases.kv import router as kv_router
from api.mtproto import router as mtproto_router
from api.ffmpeg import router as ffmpeg_router
from api.xuexi import router as tv_router


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None)
    app.include_router(bot_router, prefix='/bot', tags=['tgbot'])
    app.include_router(kv_router, tags=['redis'])
    app.include_router(mtproto_router, prefix='/svc', tags=['tgapi'])
    app.include_router(ffmpeg_router, prefix='/svc', tags=['service'])
    app.include_router(tv_router, prefix='/live', tags=['tv'])
    app.middleware('http')(middleware)

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/redoc")
    return app

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=43210, reload=True)

app = create_app()