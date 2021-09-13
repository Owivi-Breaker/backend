from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.apis import api_router
from core.config import settings

app = FastAPI(title=settings.APP_NAME)
# 注册路由
app.include_router(api_router, prefix=settings.API_PREFIX)


app.add_middleware(
    CORSMiddleware,
    # allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app='main:app', host='127.0.0.1',
                port=settings.PORT, reload=settings.RELOAD)
