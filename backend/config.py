"""
B站数据分析系统配置文件
请根据实际情况修改配置项
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "bilibili_analytics"),
    "charset": "utf8mb4"
}

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

DEFAULT_COOKIE = os.getenv("DEFAULT_COOKIE", "")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

API_CONFIG: Dict[str, Any] = {
    'host': '0.0.0.0',
    'port': 8000,
    'debug': True,
    'reload': True
}

CRAWLER_CONFIG: Dict[str, Any] = {
    'headers': {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com"
    },

    'request_interval': 1.5,

    'request_timeout': 10,

    'max_retries': 3,

    'schedule_interval': 2
}

LOGGING_CONFIG: Dict[str, Any] = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/bilibili_analysis.log'
}

PATHS: Dict[str, str] = {
    'static': 'static',
    'logs': 'logs',
    'data': 'data'
}

CORS_CONFIG: Dict[str, Any] = {
    'allow_origins': ["http://localhost:3000", "http://127.0.0.1:3000"],
    'allow_credentials': True,
    'allow_methods': ["*"],
    'allow_headers': ["*"]
}

ANALYSIS_CONFIG: Dict[str, Any] = {
    'chart': {
        'figsize': (18, 15),
        'dpi': 300,
        'font_family': 'SimHei',
        'save_format': 'png'
    },

    'wordcloud': {
        'width': 800,
        'height': 600,
        'background_color': 'white',
        'max_words': 100,
        'font_path': 'simhei.ttf'
    },

    'top_tags_count': 10,
    'min_hour_videos': 5
}

def get_database_url() -> str:
    """获取数据库连接URL"""
    return (f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}")

def create_directories():
    """创建必要的目录"""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)

def validate_config():
    """验证必要的配置是否存在"""
    missing_vars = []

    if not DEEPSEEK_API_KEY:
        missing_vars.append("DEEPSEEK_API_KEY")

    if not DEFAULT_COOKIE:
        missing_vars.append("DEFAULT_COOKIE")

    if missing_vars:
        print(f"⚠️  警告: 以下环境变量未设置: {', '.join(missing_vars)}")
        print("请创建 .env 文件并配置这些变量")
        return False

    return True

"""
可以通过设置环境变量来覆盖默认配置：

export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=bilibili_analysis
export DEFAULT_COOKIE="your_cookie_here"
""" 