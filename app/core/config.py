from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

class Config:
    TG_API_ID = os.getenv('TG_API_ID')
    TG_API_HASH = os.getenv('TG_API_HASH')
    TG_ADMIN_ID = os.getenv('TG_ADMIN_ID')
    TG_CHANNEL_ID = os.getenv('TG_CHANNEL_ID')
    TG_SESSION = os.getenv('TG_SESSION')
    BOT_HTTP_TOKEN = os.getenv('BOT_HTTP_TOKEN')
    BOT_HTTP_TOKEN_NEW = os.getenv('BOT_HTTP_TOKEN_NEW')
    BOT_HTTP_TOKEN_TEST = os.getenv('BOT_HTTP_TOKEN_TEST')
    BARD_API_KEY = os.getenv('BARD_API_KEY')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    REDIS_URL = os.getenv('REDIS_URL')

# 配置实例
config = Config()