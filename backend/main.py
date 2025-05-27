import requests
import json
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from datetime import datetime, timedelta
from tqdm import tqdm
from collections import defaultdict
import jieba
import jieba.analyse
import re
from sqlalchemy import create_engine, text, Column, String, Integer, DateTime, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql
from typing import Optional, Dict, Any, List
import os
import base64
from io import BytesIO
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from ml_models import MLService
from auth import AuthService
from ai_service import AIService
from report_service import ReportService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_chinese_font():
    """获取可用的中文字体路径"""
    import os
    font_paths = [
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simkai.ttf',
        '/System/Library/Fonts/PingFang.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path

    return None

jieba.initialize()

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'htlovewql1314',
    'database': 'bilibili_analysis',
    'charset': 'utf8mb4'
}

engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@"
    f"{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}?charset={MYSQL_CONFIG['charset']}"
)

from config import DEFAULT_COOKIE, DEEPSEEK_API_KEY, validate_config

class CookieRequest(BaseModel):
    cookie: str

class AnalysisResponse(BaseModel):
    total_videos: int
    avg_views: int
    avg_interaction_rate: float
    top_tags: List[List]
    best_publish_hours: Optional[List[int]] = None

class UserInfoResponse(BaseModel):
    name: str
    mid: int
    level: int
    following: int
    follower: int

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class BilibiliCookieUpdate(BaseModel):
    cookie: str

class AIQueryRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None

class AIQueryResponse(BaseModel):
    success: bool
    response: str
    intent: Optional[Dict[str, Any]] = None
    data_context_available: bool = False
    timestamp: str
    model: str = "deepseek-v3"
    error: Optional[str] = None

class DailyReportRequest(BaseModel):
    target_date: Optional[str] = None

class WeeklyReportRequest(BaseModel):
    week_start: Optional[str] = None

app = FastAPI(title="B站数据分析系统", version="1.0.0")

ml_service = MLService()

auth_service = AuthService(engine)

ai_service = AIService(
    api_key=DEEPSEEK_API_KEY,
    engine=engine
)

report_service = ReportService(engine=engine)

security = HTTPBearer(auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BiliBiliAnalyticsSystem:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "Origin": "https://www.bilibili.com"
        }
        self.base_url = "https://api.bilibili.com"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.encoding = 'utf-8'
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS videos (
                    bvid VARCHAR(20) PRIMARY KEY,
                    title TEXT,
                    aid VARCHAR(20),
                    author VARCHAR(100),
                    mid VARCHAR(20),
                    view INT,
                    danmaku INT,
                    reply INT,
                    favorite INT,
                    coin INT,
                    share INT,
                    `like` INT,
                    duration INT,
                    pubdate DATETIME,
                    tid INT,
                    tname VARCHAR(50),
                    copyright TINYINT,
                    tags TEXT,
                    `desc` TEXT,
                    ctime DATETIME,
                    collected_at DATETIME,
                    INDEX idx_mid (mid),
                    INDEX idx_pubdate (pubdate),
                    INDEX idx_tid (tid)
                )
                """))

                # 创建用户数据表
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_mid VARCHAR(20),
                    data_type VARCHAR(50),
                    data_content JSON,
                    created_at DATETIME,
                    INDEX idx_user_mid (user_mid),
                    INDEX idx_data_type (data_type)
                )
                """))

            logger.info("数据库表初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise

    def crawl_popular_videos(self, pages=5):
        """爬取热门视频（移除UP主信息部分）"""
        for page in tqdm(range(1, pages + 1), desc="爬取热门视频"):
            try:
                url = f"{self.base_url}/x/web-interface/popular?pn={page}"
                response = self.session.get(url, timeout=10)
                response.encoding = 'utf-8'
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 0:
                    for item in data["data"]["list"]:
                        self._process_video_item(item)

                time.sleep(1.5)

            except requests.exceptions.RequestException as e:
                logger.error(f"第{page}页请求失败: {str(e)}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"第{page}页处理失败: {str(e)}")
                time.sleep(3)

    def get_video_details(self, bvid: str) -> Optional[Dict[str, Any]]:
        """获取视频详情"""
        try:
            detail_url = f"{self.base_url}/x/web-interface/view?bvid={bvid}"
            detail_res = self.session.get(detail_url, timeout=10)
            detail_res.encoding = 'utf-8'
            detail_res.raise_for_status()
            detail_data = detail_res.json()

            if detail_data.get("code") != 0:
                return None

            detail = detail_data["data"]

            tags = []
            if "aid" in detail:
                tag_url = f"{self.base_url}/x/tag/archive/tags?aid={detail['aid']}"
                tag_res = self.session.get(tag_url, timeout=10)
                tag_res.encoding = 'utf-8'
                if tag_res.status_code == 200:
                    tag_data = tag_res.json()
                    if tag_data.get("code") == 0:
                        tags = [tag["tag_name"] for tag in tag_data.get("data", [])]

            if not tags and "dynamic" in detail:
                dynamic_text = str(detail.get("dynamic", ""))
                tags = re.findall(r'#([^#\s]+)#', dynamic_text)

            if not tags and "tname" in detail:
                tags = [detail["tname"]]

            detail["processed_tags"] = tags
            return detail

        except Exception as e:
            logger.error(f"获取视频{bvid}详情失败: {str(e)}")
            return None

    def _process_video_item(self, item: Dict[str, Any]):
        """处理视频数据并存入MySQL（移除UP主信息处理）"""
        try:
            detail = self.get_video_details(item["bvid"])
            if not detail:
                return

            video_data = {
                "bvid": detail.get("bvid", ""),
                "title": detail.get("title", ""),
                "aid": str(detail.get("aid", "")),
                "author": detail.get("owner", {}).get("name", ""),
                "mid": str(detail.get("owner", {}).get("mid", "")),
                "view": detail.get("stat", {}).get("view", 0),
                "danmaku": detail.get("stat", {}).get("danmaku", 0),
                "reply": detail.get("stat", {}).get("reply", 0),
                "favorite": detail.get("stat", {}).get("favorite", 0),
                "coin": detail.get("stat", {}).get("coin", 0),
                "share": detail.get("stat", {}).get("share", 0),
                "like": detail.get("stat", {}).get("like", 0),
                "duration": detail.get("duration", 0),
                "pubdate": datetime.fromtimestamp(detail.get("pubdate", 0)) if detail.get("pubdate") else None,
                "tid": detail.get("tid", 0),
                "tname": detail.get("tname", ""),
                "copyright": detail.get("copyright", 0),
                "tags": ",".join(detail.get("processed_tags", [])),
                "desc": detail.get("desc", ""),
                "ctime": datetime.fromtimestamp(detail.get("ctime", 0)) if detail.get("ctime") else None,
                "collected_at": datetime.now()
            }

            with engine.begin() as conn:
                conn.execute(text("""
                INSERT INTO videos (
                    bvid, title, aid, author, mid, view, danmaku, reply, 
                    favorite, coin, share, `like`, duration, pubdate, tid, 
                    tname, copyright, tags, `desc`, ctime, collected_at
                ) VALUES (
                    :bvid, :title, :aid, :author, :mid, :view, 
                    :danmaku, :reply, :favorite, :coin, :share, 
                    :like, :duration, :pubdate, :tid, :tname, 
                    :copyright, :tags, :desc, :ctime, :collected_at
                )
                ON DUPLICATE KEY UPDATE 
                    title=VALUES(title), view=VALUES(view), danmaku=VALUES(danmaku),
                    reply=VALUES(reply), favorite=VALUES(favorite), coin=VALUES(coin),
                    share=VALUES(share), `like`=VALUES(`like`), tags=VALUES(tags)
                """), video_data)

            logger.info(f"成功处理视频: {item['bvid']}")

        except Exception as e:
            logger.error(f"处理视频{item['bvid']}失败: {str(e)}")

    def load_data_to_dataframe(self) -> pd.DataFrame:
        """从MySQL加载数据到DataFrame"""
        try:
            with engine.connect() as conn:
                df = pd.read_sql("""
                SELECT 
                    bvid, title, author, view, danmaku, reply, 
                    favorite, coin, share, `like`, duration, 
                    pubdate, tname, tags, `desc`
                FROM videos
                ORDER BY collected_at DESC
                """, conn)

            if df.empty:
                return pd.DataFrame()

            if 'pubdate' in df:
                df['pubdate'] = pd.to_datetime(df['pubdate'])

            interaction_cols = ['danmaku', 'reply', 'favorite', 'coin', 'share', 'like']
            for col in interaction_cols:
                if col not in df:
                    df[col] = 0

            df['interaction_rate'] = (
                df['danmaku'] + df['reply'] + df['favorite'] +
                df['coin'] + df['share'] + df['like']
            ) / df['view'].clip(lower=1)

            if 'pubdate' in df:
                df['pub_hour'] = df['pubdate'].dt.hour

            return df

        except Exception as e:
            logger.error(f"加载数据失败: {str(e)}")
            return pd.DataFrame()

    def analyze_and_visualize(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """数据分析和可视化"""
        if df.empty:
            return None

        try:
            plt.figure(figsize=(18, 15))
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
            plt.style.use('default')
            plt.rcParams['text.color'] = 'black'
            plt.rcParams['axes.labelcolor'] = 'black'
            plt.rcParams['xtick.color'] = 'black'
            plt.rcParams['ytick.color'] = 'black'
            plt.rcParams['axes.titlecolor'] = 'black'
            plt.rcParams['figure.facecolor'] = 'white'
            plt.rcParams['axes.facecolor'] = 'white'

            plt.subplot(3, 2, 1)
            sns.histplot(np.log10(df['view'] + 1), bins=30, kde=True, color='skyblue', alpha=0.7)
            plt.title('热门视频播放量分布', color='black', fontsize=12, fontweight='bold')
            plt.xlabel('播放量(log10)', color='black')
            plt.ylabel('视频数量', color='black')

            plt.subplot(3, 2, 2)
            all_tags = ' '.join(df['tags'].fillna('').astype(str))

            font_path = get_chinese_font()
            wordcloud_config = {
                'background_color': 'white',
                'width': 800, 
                'height': 600,
                'max_words': 100,
                'collocations': False
            }
            if font_path:
                wordcloud_config['font_path'] = font_path

            if not all_tags.strip():
                all_titles = ' '.join(df['title'].dropna().astype(str))
                word_list = jieba.analyse.extract_tags(all_titles, topK=100, withWeight=True)
                word_dict = {word: weight for word, weight in word_list}
                wordcloud = WordCloud(**wordcloud_config).generate_from_frequencies(word_dict)
            else:
                wordcloud = WordCloud(**wordcloud_config).generate(all_tags)

            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('热门视频标签词云', color='black', fontsize=12, fontweight='bold')

            plt.subplot(3, 2, 3)
            if 'tname' in df and not df['tname'].isna().all():
                category_stats = df['tname'].value_counts().head(10)
                plt.pie(category_stats.values, labels=category_stats.index, autopct='%1.1f%%', textprops={'color': 'black'})
                plt.title('热门视频分区分布', color='black', fontsize=12, fontweight='bold')
            else:
                plt.text(0.5, 0.5, '暂无分区数据', ha='center', va='center', transform=plt.gca().transAxes, color='black')
                plt.title('视频分区分布', color='black', fontsize=12, fontweight='bold')

            plt.subplot(3, 2, 4)
            interaction_df = df[['danmaku', 'reply', 'favorite', 'coin', 'share', 'like']].corr()
            sns.heatmap(interaction_df, annot=True, cmap='coolwarm', center=0, fmt=".2f", 
                       annot_kws={'color': 'black'}, cbar_kws={'label': '相关系数'})
            plt.title('热门视频互动行为相关性', color='black', fontsize=12, fontweight='bold')

            plt.subplot(3, 2, 5)
            if 'pub_hour' in df and not df['pub_hour'].isna().all():
                hour_stats = df['pub_hour'].value_counts().sort_index()
                plt.bar(hour_stats.index, hour_stats.values, color='skyblue', alpha=0.7)
                plt.title('热门视频发布时间分布', color='black', fontsize=12, fontweight='bold')
                plt.xlabel('发布时间(小时)', color='black')
                plt.ylabel('视频数量', color='black')
                plt.xticks(range(0, 24, 2), color='black')
                plt.yticks(color='black')
                plt.grid(True, alpha=0.3)
            else:
                plt.text(0.5, 0.5, '暂无时间数据', ha='center', va='center', transform=plt.gca().transAxes, color='black')
                plt.title('视频发布时间分布', color='black', fontsize=12, fontweight='bold')

            plt.subplot(3, 2, 6)
            corr_cols = ['view', 'danmaku', 'reply', 'favorite', 'coin', 'share', 'like', 'interaction_rate']
            available_cols = [col for col in corr_cols if col in df]
            corr_df = df[available_cols].corr()

            sns.heatmap(corr_df[['view']].sort_values('view', ascending=False),
                        annot=True, cmap='viridis', vmin=-1, vmax=1, fmt=".2f",
                        annot_kws={'color': 'white'}, cbar_kws={'label': '相关系数'})
            plt.title('热门视频播放量与互动指标相关性', color='black', fontsize=12, fontweight='bold')

            plt.tight_layout()

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)

            plt.savefig('static/bilibili_analysis.png', dpi=300, bbox_inches='tight')
            plt.close()

            analysis_results = {
                "total_videos": len(df),
                "avg_views": int(df['view'].mean()),
                "avg_interaction_rate": float(df['interaction_rate'].mean()),
                "top_tags": self._extract_top_tags(df),
            }

            if 'pub_hour' in df:
                hour_stats = df.groupby('pub_hour')['view'].agg(['mean', 'count'])
                hour_stats = hour_stats[hour_stats['count'] > 5]
                analysis_results["best_publish_hours"] = hour_stats.sort_values('mean', ascending=False).head(3).index.tolist()

            return analysis_results

        except Exception as e:
            logger.error(f"数据分析失败: {str(e)}")
            return None

    def _extract_top_tags(self, df: pd.DataFrame, n: int = 10) -> list:
        """提取热门标签"""
        tag_counter = defaultdict(int)
        for tags in df['tags'].dropna().astype(str):
            for tag in tags.split(','):
                if tag.strip():
                    tag_counter[tag.strip()] += 1
        return [[tag, count] for tag, count in sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)[:n]]


class BiliBiliUserCrawler:
    def __init__(self, cookie: str = DEFAULT_COOKIE):
        self.cookie = self._clean_cookie(cookie.strip() if cookie else DEFAULT_COOKIE)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
            'Connection': 'keep-alive',
            'Cookie': self.cookie,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=4',
            'TE': 'trailers'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.encoding = 'utf-8'

    def _clean_cookie(self, cookie: str) -> str:
        """清理Cookie中的特殊字符"""
        if not cookie:
            return DEFAULT_COOKIE

        import re
        cleaned = re.sub(r'[^\x20-\x7E]', '', cookie)
        cleaned = ' '.join(cleaned.split())

        return cleaned if cleaned else DEFAULT_COOKIE

    def check_cookie_validity(self) -> bool:
        """检查Cookie是否有效"""
        try:
            user_info = self.get_user_info()
            return user_info is not None
        except:
            return False

    def get_user_info(self):
        """获取B站个人信息"""
        url = 'https://api.bilibili.com/x/space/myinfo'
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    return data['data']
                elif data.get('code') == -101:
                    logger.warning("Cookie已过期或账号未登录")
                    return None
                else:
                    logger.error(f"获取个人信息失败: {data.get('message')} (code: {data.get('code')})")
            else:
                logger.error(f"请求失败，状态码: {response.status_code}")
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取个人信息时出错: {str(e)}")
        return None

    def get_watch_history(self, max_pages=5):
        """获取观看历史记录"""
        history = []
        url = 'https://api.bilibili.com/x/web-interface/history/cursor'
        params = {
            'view_at': 0,
            'business': 'archive'
        }

        for _ in range(max_pages):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.encoding = 'utf-8'

                if response.status_code != 200:
                    break

                data = response.json()
                if data.get('code') != 0:
                    break

                history_data = data.get('data', {})
                history.extend(history_data.get('list', []))

                if not history_data.get('cursor', {}).get('max'):
                    break

                params['view_at'] = history_data['cursor']['max']
                time.sleep(1)

            except Exception as e:
                logger.error(f"获取历史记录时出错: {str(e)}")
                break

        return history

    def get_favorites(self, mid):
        """获取收藏内容"""
        favorites = []
        folder_url = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all'
        folder_params = {'up_mid': mid}

        try:
            folder_response = self.session.get(folder_url, params=folder_params, timeout=10)
            folder_response.encoding = 'utf-8'

            if folder_response.status_code == 200:
                folder_data = folder_response.json()
                if folder_data.get('code') == 0:
                    folders = folder_data.get('data', {}).get('list', [])

                    for folder in folders:
                        media_url = 'https://api.bilibili.com/x/v3/fav/resource/list'
                        media_params = {
                            'media_id': folder['id'],
                            'ps': 20,
                            'pn': 1
                        }

                        media_response = self.session.get(media_url, params=media_params, timeout=10)
                        media_response.encoding = 'utf-8'

                        if media_response.status_code == 200:
                            media_data = media_response.json()
                            if media_data.get('code') == 0:
                                folder['resources'] = media_data.get('data', {}).get('medias', [])
                                favorites.append(folder)
                        time.sleep(0.5)
        except Exception as e:
            logger.error(f"获取收藏内容时出错: {str(e)}")

        return favorites

    def save_user_data(self, user_mid: str, data_type: str, data_content: dict):
        """保存用户数据到数据库"""
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                INSERT INTO user_data (user_mid, data_type, data_content, created_at)
                VALUES (:user_mid, :data_type, :data_content, :created_at)
                """), {
                    'user_mid': user_mid,
                    'data_type': data_type,
                    'data_content': json.dumps(data_content, ensure_ascii=False),
                    'created_at': datetime.now()
                })
        except Exception as e:
            logger.error(f"保存用户数据失败: {str(e)}")


# 全局实例
analytics_system = BiliBiliAnalyticsSystem()
scheduler = BackgroundScheduler()

# 创建静态文件目录
os.makedirs('static', exist_ok=True)

def scheduled_crawl():
    """定时爬取任务"""
    logger.info("开始定时爬取热门视频...")
    try:
        analytics_system.crawl_popular_videos(pages=3)
        logger.info("定时爬取完成")
    except Exception as e:
        logger.error(f"定时爬取失败: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("🚀 B站数据分析系统启动中...")

    if not validate_config():
        logger.warning("⚠️  部分配置缺失，某些功能可能无法正常使用")

    scheduler.add_job(
        scheduled_crawl,
        'interval',
        hours=2,
        id='crawl_popular_videos'
    )
    scheduler.start()
    logger.info("✅ 应用启动完成，定时任务已启动")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    scheduler.shutdown()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    if not credentials:
        return None

    user = auth_service.get_user_by_token(credentials.credentials)
    return user

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """需要认证的中间件"""
    if not credentials:
        raise HTTPException(status_code=401, detail="需要登录")

    user = auth_service.get_user_by_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    return user

@app.get("/")
async def root():
    return {"message": "B站数据分析系统API"}


@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    """用户注册"""
    result = auth_service.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )

    if result['success']:
        return {
            "message": "注册成功",
            "user": {
                "user_id": result['user_id'],
                "username": result['username'],
                "email": result['email']
            },
            "token": result['token']
        }
    else:
        raise HTTPException(status_code=400, detail=result['error'])

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    """用户登录"""
    result = auth_service.login_user(
        username=user_data.username,
        password=user_data.password
    )

    if result['success']:
        return {
            "message": "登录成功",
            "user": {
                "user_id": result['user_id'],
                "username": result['username'],
                "email": result['email'],
                "bilibili_mid": result['bilibili_mid'],
                "bilibili_name": result['bilibili_name']
            },
            "token": result['token']
        }
    else:
        raise HTTPException(status_code=401, detail=result['error'])

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(require_auth), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """用户登出"""
    success = auth_service.logout_user(credentials.credentials)
    if success:
        return {"message": "登出成功"}
    else:
        raise HTTPException(status_code=500, detail="登出失败")

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(require_auth)):
    """获取当前用户信息"""
    return {
        "user": current_user
    }

@app.post("/api/auth/update-bilibili")
async def update_bilibili_cookie(
    cookie_data: BilibiliCookieUpdate,
    current_user: dict = Depends(require_auth)
):
    """更新用户的B站Cookie"""
    try:
        crawler = BiliBiliUserCrawler(cookie_data.cookie)

        if not crawler.check_cookie_validity():
            raise HTTPException(status_code=400, detail="Cookie无效或已过期")

        user_info = crawler.get_user_info()
        if not user_info:
            raise HTTPException(status_code=400, detail="无法获取B站用户信息")

        success = auth_service.update_bilibili_info(
            user_id=current_user['user_id'],
            cookie=cookie_data.cookie,
            mid=str(user_info['mid']),
            name=user_info['name']
        )

        if not success:
            raise HTTPException(status_code=500, detail="更新失败")

        await sync_user_bilibili_data(current_user['user_id'], cookie_data.cookie)

        return {
            "message": "B站信息更新成功",
            "bilibili_info": {
                "mid": user_info['mid'],
                "name": user_info['name'],
                "level": user_info.get('level', 0),
                "following": user_info.get('following', 0),
                "follower": user_info.get('follower', 0)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

async def sync_user_bilibili_data(user_id: int, cookie: str):
    """同步用户的B站数据"""
    try:
        crawler = BiliBiliUserCrawler(cookie)

        user_info = crawler.get_user_info()
        if user_info:
            with engine.begin() as conn:
                conn.execute(text("""
                INSERT INTO user_data (user_mid, data_type, data_content, created_at)
                VALUES (:user_mid, :data_type, :data_content, :created_at)
                ON DUPLICATE KEY UPDATE 
                data_content = VALUES(data_content), created_at = VALUES(created_at)
                """), {
                    'user_mid': str(user_id),  # 使用系统用户ID
                    'data_type': 'user_info',
                    'data_content': json.dumps(user_info, ensure_ascii=False),
                    'created_at': datetime.now()
                })
        
        # 获取观看历史
        watch_history = crawler.get_watch_history(max_pages=10)  # 获取更多页面
        if watch_history:
            with engine.begin() as conn:
                conn.execute(text("""
                INSERT INTO user_data (user_mid, data_type, data_content, created_at)
                VALUES (:user_mid, :data_type, :data_content, :created_at)
                ON DUPLICATE KEY UPDATE 
                data_content = VALUES(data_content), created_at = VALUES(created_at)
                """), {
                    'user_mid': str(user_id),
                    'data_type': 'watch_history',
                    'data_content': json.dumps(watch_history, ensure_ascii=False),
                    'created_at': datetime.now()
                })
        
        # 获取收藏
        if user_info:
            favorites = crawler.get_favorites(user_info['mid'])
            if favorites:
                with engine.begin() as conn:
                    conn.execute(text("""
                    INSERT INTO user_data (user_mid, data_type, data_content, created_at)
                    VALUES (:user_mid, :data_type, :data_content, :created_at)
                    ON DUPLICATE KEY UPDATE 
                    data_content = VALUES(data_content), created_at = VALUES(created_at)
                    """), {
                        'user_mid': str(user_id),
                        'data_type': 'favorites',
                        'data_content': json.dumps(favorites, ensure_ascii=False),
                        'created_at': datetime.now()
                    })
        
        logger.info(f"用户 {user_id} 的B站数据同步完成")
        
    except Exception as e:
        logger.error(f"同步用户 {user_id} 的B站数据失败: {str(e)}")

@app.post("/api/crawl/popular")
async def crawl_popular(background_tasks: BackgroundTasks):
    """手动触发热门视频爬取"""
    background_tasks.add_task(analytics_system.crawl_popular_videos, 5)
    return {"message": "热门视频爬取任务已启动"}

@app.get("/api/analysis/videos")
async def get_video_analysis():
    """获取视频分析结果"""
    try:
        df = analytics_system.load_data_to_dataframe()
        if df.empty:
            raise HTTPException(status_code=404, detail="暂无数据")

        results = analytics_system.analyze_and_visualize(df)
        if not results:
            raise HTTPException(status_code=500, detail="分析失败")

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/chart")
async def get_analysis_chart():
    """获取分析图表"""
    chart_path = "static/bilibili_analysis.png"
    if os.path.exists(chart_path):
        return FileResponse(chart_path)
    else:
        raise HTTPException(status_code=404, detail="图表文件不存在")

@app.get("/api/videos")
async def get_videos(page: int = 1, page_size: int = 10, limit: int = None):
    """获取视频列表（支持分页）"""
    try:
        with engine.connect() as conn:
            if limit is not None:
                df = pd.read_sql(f"""
                SELECT bvid, title, author, view, danmaku, reply, 
                       favorite, coin, share, `like`, pubdate, tname
                FROM videos 
                ORDER BY collected_at DESC 
                LIMIT {limit}
                """, conn)
                return df.to_dict('records')
            
            # 新的分页逻辑
            offset = (page - 1) * page_size
            
            # 获取总数
            total_count_result = conn.execute(text("SELECT COUNT(*) as count FROM videos"))
            total_count = total_count_result.fetchone()[0]
            
            # 获取分页数据
            df = pd.read_sql(f"""
            SELECT bvid, title, author, view, danmaku, reply, 
                   favorite, coin, share, `like`, pubdate, tname
            FROM videos 
            ORDER BY collected_at DESC 
            LIMIT {page_size} OFFSET {offset}
            """, conn)
            
            return {
                "data": df.to_dict('records'),
                "pagination": {
                    "current": page,
                    "pageSize": page_size,
                    "total": total_count,
                    "totalPages": (total_count + page_size - 1) // page_size
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/info")
async def get_user_info_with_cookie(cookie_req: CookieRequest = None):
    """获取用户信息（可选择传入Cookie）"""
    try:
        cookie = cookie_req.cookie if cookie_req else DEFAULT_COOKIE
        logger.info(f"尝试获取用户信息，Cookie长度: {len(cookie) if cookie else 0}")

        crawler = BiliBiliUserCrawler(cookie)

        user_info = crawler.get_user_info()
        if not user_info:
            logger.warning("获取用户信息失败")
            if cookie_req and cookie_req.cookie:
                raise HTTPException(
                    status_code=401, 
                    detail="自定义Cookie已过期或无效。请重新获取Cookie：\n1. 打开B站并登录\n2. 按F12打开开发者工具\n3. 刷新页面\n4. 在Network标签中找到任意请求\n5. 复制完整的Cookie值"
                )
            else:
                raise HTTPException(
                    status_code=401, 
                    detail="默认Cookie已过期。请设置自定义Cookie：\n1. 打开B站并登录\n2. 按F12打开开发者工具\n3. 刷新页面\n4. 在Network标签中找到任意请求\n5. 复制完整的Cookie值"
                )

        logger.info(f"成功获取用户信息: {user_info.get('name', 'Unknown')}")
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@app.post("/api/user/history")
async def get_user_history(cookie_req: CookieRequest = None):
    """获取用户观看历史"""
    try:
        cookie = cookie_req.cookie if cookie_req else DEFAULT_COOKIE
        crawler = BiliBiliUserCrawler(cookie)

        if not crawler.check_cookie_validity():
            raise HTTPException(status_code=401, detail="Cookie已过期或无效")

        user_info = crawler.get_user_info()
        if not user_info:
            raise HTTPException(status_code=404, detail="无法获取用户信息")

        history = crawler.get_watch_history()

        crawler.save_user_data(str(user_info['mid']), 'watch_history', history)

        return {
            "user_info": user_info,
            "history": history,
            "total_count": len(history)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/favorites")
async def get_user_favorites(cookie_req: CookieRequest = None):
    """获取用户收藏"""
    try:
        cookie = cookie_req.cookie if cookie_req else DEFAULT_COOKIE
        crawler = BiliBiliUserCrawler(cookie)

        if not crawler.check_cookie_validity():
            raise HTTPException(status_code=401, detail="Cookie已过期或无效")

        user_info = crawler.get_user_info()
        if not user_info:
            raise HTTPException(status_code=404, detail="无法获取用户信息")

        favorites = crawler.get_favorites(user_info['mid'])

        crawler.save_user_data(str(user_info['mid']), 'favorites', favorites)

        total_resources = sum(len(folder.get('resources', [])) for folder in favorites)

        return {
            "user_info": user_info,
            "favorites": favorites,
            "folder_count": len(favorites),
            "total_resources": total_resources
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/analysis/{user_mid}")
async def get_user_analysis(user_mid: str):
    """获取用户数据分析"""
    try:
        with engine.connect() as conn:
            query = text("""
            SELECT data_content, created_at 
            FROM user_data 
            WHERE user_mid = :user_mid AND data_type = 'watch_history'
            ORDER BY created_at DESC 
            LIMIT 1
            """)
            result = conn.execute(query, {'user_mid': user_mid})
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(status_code=404, detail="未找到用户数据")
            
            # 解析历史数据
            history = json.loads(rows[0][0])
            
            # 分析观看偏好
            categories = defaultdict(int)
            view_times = []
            
            for item in history:
                # 优先使用tag_name，其次使用tname
                category = item.get('tag_name') or item.get('tname')
                if category:
                    categories[category] += 1
                if 'view_at' in item:
                    view_times.append(datetime.fromtimestamp(item['view_at']))
            
            # 分析观看时间分布
            hour_distribution = defaultdict(int)
            for vt in view_times:
                hour_distribution[vt.hour] += 1
            
            # 转换为列表格式，避免tuple序列化问题
            most_active_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            most_active_hours_list = [{"hour": hour, "count": count} for hour, count in most_active_hours]
            
            analysis = {
                "total_watched": len(history),
                "category_preferences": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]),
                "watch_time_distribution": dict(hour_distribution),
                "most_active_hours": most_active_hours_list
            }
            
            return analysis
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 机器学习API端点 ====================

@app.get("/api/ml/recommendations")
async def get_video_recommendations(
    video_bvid: str = None, 
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """获取视频推荐"""
    try:
        with engine.connect() as conn:
            videos_df = pd.read_sql("""
            SELECT bvid, title, view, `like`, coin, share, tname, pubdate, `desc`
            FROM videos 
            ORDER BY collected_at DESC 
            LIMIT 200
            """, conn)
        
        if videos_df.empty:
            raise HTTPException(status_code=404, detail="暂无视频数据")
        
        user_history = None
        recommendation_type = "popular"
        
        # 如果用户已登录，获取用户历史
        if current_user:
            with engine.connect() as conn:
                query = text("""
                SELECT data_content 
                FROM user_data 
                WHERE user_mid = :user_mid AND data_type = 'watch_history'
                ORDER BY created_at DESC 
                LIMIT 1
                """)
                result = conn.execute(query, {'user_mid': str(current_user['user_id'])})
                rows = result.fetchall()
                
                if rows:
                    user_history = json.loads(rows[0][0])
                    recommendation_type = "collaborative_filtering"
        
        if video_bvid:
            recommendation_type = "content_based"
        
        recommendations = ml_service.get_video_recommendations(
            user_history=user_history,
            video_bvid=video_bvid,
            videos_df=videos_df,
            top_n=limit
        )
        
        return {
            "recommendations": recommendations,
            "total_count": len(recommendations),
            "recommendation_type": recommendation_type,
            "user_logged_in": current_user is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ml/train-prediction-model")
async def train_prediction_model():
    """训练播放量预测模型"""
    try:
        with engine.connect() as conn:
            videos_df = pd.read_sql("""
            SELECT bvid, title, view, `like`, coin, share, tname, pubdate, duration
            FROM videos 
            WHERE view > 0
            ORDER BY collected_at DESC 
            LIMIT 1000
            """, conn)
        
        if len(videos_df) < 50:
            raise HTTPException(status_code=400, detail="数据量不足，至少需要50个视频数据")
        
        results = ml_service.train_view_prediction_model(videos_df)
        
        return {
            "message": "模型训练完成",
            "model_performance": results,
            "training_data_size": len(videos_df)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ml/predict-views")
async def predict_video_views(video_features: dict):
    """预测视频播放量"""
    try:
        prediction = ml_service.predict_video_views(video_features)

        if prediction is None:
            raise HTTPException(status_code=400, detail="模型未训练或预测失败")

        return {
            "predicted_views": prediction,
            "input_features": video_features
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/user-clustering")
async def analyze_user_clustering():
    """用户聚类分析"""
    try:
        real_users = []

        with engine.connect() as conn:
            users_query = text("""
            SELECT DISTINCT u.id, u.username, u.bilibili_mid, u.bilibili_name
            FROM users u
            WHERE u.bilibili_mid IS NOT NULL
            """)
            users_result = conn.execute(users_query)
            users = users_result.fetchall()
            
            for user in users:
                user_id, username, bilibili_mid, bilibili_name = user
                
                # 获取用户的观看历史
                history_query = text("""
                SELECT data_content 
                FROM user_data 
                WHERE user_mid = :user_mid AND data_type = 'watch_history'
                ORDER BY created_at DESC 
                LIMIT 1
                """)
                history_result = conn.execute(history_query, {'user_mid': str(user_id)})
                history_rows = history_result.fetchall()
                
                watch_history = []
                if history_rows:
                    watch_history = json.loads(history_rows[0][0])
                
                # 获取用户基本信息
                info_query = text("""
                SELECT data_content 
                FROM user_data 
                WHERE user_mid = :user_mid AND data_type = 'user_info'
                ORDER BY created_at DESC 
                LIMIT 1
                """)
                info_result = conn.execute(info_query, {'user_mid': str(user_id)})
                info_rows = info_result.fetchall()
                
                user_info = {}
                if info_rows:
                    user_info = json.loads(info_rows[0][0])
                
                real_users.append({
                    'user_info': {
                        'user_id': user_id,
                        'username': username,
                        'bilibili_mid': bilibili_mid,
                        'bilibili_name': bilibili_name,
                        **user_info
                    },
                    'watch_history': watch_history
                })
        
        users_data = real_users
        
        # 如果用户数据不足，生成模拟数据
        if len(users_data) < 5:
            # 获取一些视频数据用于生成模拟历史
            with engine.connect() as conn:
                videos_df = pd.read_sql("""
                SELECT bvid, title, tname, view, `like`, coin, share, duration
                FROM videos 
                ORDER BY collected_at DESC 
                LIMIT 50
                """, conn)
            
            if not videos_df.empty:
                # 生成5个模拟用户
                import random
                categories = videos_df['tname'].unique().tolist()
                
                for i in range(5):
                    user_mid = f"mock_user_{i+1}"
                    
                    # 为每个用户生成不同的观看偏好
                    if i == 0:  # 重度用户，喜欢科技
                        preferred_cats = ['科技', '数码']
                        watch_count = random.randint(80, 120)
                    elif i == 1:  # 娱乐用户
                        preferred_cats = ['娱乐', '音乐']
                        watch_count = random.randint(40, 60)
                    elif i == 2:  # 游戏用户
                        preferred_cats = ['游戏', '电竞']
                        watch_count = random.randint(60, 80)
                    elif i == 3:  # 学习用户
                        preferred_cats = ['知识', '教育']
                        watch_count = random.randint(30, 50)
                    else:  # 综合用户
                        preferred_cats = categories[:3]
                        watch_count = random.randint(20, 40)
                    
                    # 生成观看历史
                    watch_history = []
                    for _ in range(watch_count):
                        # 70%概率选择偏好分区的视频
                        if random.random() < 0.7 and preferred_cats:
                            cat_videos = videos_df[videos_df['tname'].isin(preferred_cats)]
                            if not cat_videos.empty:
                                video = cat_videos.sample(1).iloc[0]
                            else:
                                video = videos_df.sample(1).iloc[0]
                        else:
                            video = videos_df.sample(1).iloc[0]
                        
                        watch_history.append({
                            'bvid': video['bvid'],
                            'title': video['title'],
                            'tname': video['tname'],
                            'duration': video.get('duration', 300),
                            'view_at': int(time.time()) - random.randint(0, 30*24*3600),  # 最近30天
                            'like': random.randint(0, int(video.get('like', 0) * 0.1)),
                            'coin': random.randint(0, int(video.get('coin', 0) * 0.1)),
                            'share': random.randint(0, int(video.get('share', 0) * 0.1))
                        })
                    
                    users_data.append({
                        'user_mid': user_mid,
                        'user_info': {'mid': user_mid},
                        'watch_history': watch_history
                    })
        
        if len(users_data) < 5:
            raise HTTPException(status_code=400, detail="无法生成足够的用户数据进行聚类分析")
        
        cluster_analysis = ml_service.analyze_user_clusters(users_data)
        
        # 计算真实用户数量
        real_users_count = len(real_users)
        simulated_users_count = len(users_data) - real_users_count
        
        if simulated_users_count > 0:
            note = f"基于 {real_users_count} 个真实用户和 {simulated_users_count} 个模拟用户的聚类分析"
        else:
            note = f"基于 {real_users_count} 个真实用户的聚类分析"
        
        return {
            "cluster_analysis": cluster_analysis,
            "total_users": len(users_data),
            "real_users_count": real_users_count,
            "simulated_users_count": simulated_users_count,
            "note": note
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ml/sentiment-analysis")
async def analyze_sentiment(texts: List[str]):
    """情感分析"""
    try:
        if not texts:
            raise HTTPException(status_code=400, detail="文本列表不能为空")

        sentiment_analysis = ml_service.analyze_sentiment(texts)

        return {
            "sentiment_analysis": sentiment_analysis,
            "analyzed_texts_count": len(texts)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ml/trend-prediction")
async def predict_trends(time_series_data: List[dict], periods: int = 7):
    """趋势预测"""
    try:
        if not time_series_data:
            raise HTTPException(status_code=400, detail="时间序列数据不能为空")

        predictions = ml_service.predict_trends(time_series_data, periods)

        return {
            "predictions": predictions,
            "prediction_periods": periods,
            "input_data_points": len(time_series_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/model-status")
async def get_model_status():
    """获取机器学习模型状态"""
    try:
        status = {
            "recommendation_system": {
                "initialized": ml_service.recommendation_system is not None,
                "content_features_ready": ml_service.recommendation_system.content_similarity_matrix is not None
            },
            "view_predictor": {
                "initialized": ml_service.view_predictor is not None,
                "model_trained": ml_service.view_predictor.best_model is not None,
                "best_model": getattr(ml_service.view_predictor, 'best_model_name', None),
                "feature_importance": ml_service.view_predictor.feature_importance
            },
            "user_clustering": {
                "initialized": ml_service.user_clustering is not None,
                "n_clusters": ml_service.user_clustering.n_clusters
            },
            "sentiment_analyzer": {
                "initialized": ml_service.sentiment_analyzer is not None
            },
            "trend_predictor": {
                "initialized": ml_service.trend_predictor is not None
            }
        }

        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/similar-users")
async def find_similar_users(current_user: dict = Depends(require_auth)):
    """找到相似用户"""
    try:
        users_data = []

        with engine.connect() as conn:
            users_query = text("""
            SELECT DISTINCT u.id, u.username, u.bilibili_mid, u.bilibili_name
            FROM users u
            WHERE u.bilibili_mid IS NOT NULL
            """)
            users_result = conn.execute(users_query)
            users = users_result.fetchall()
            
            for user in users:
                user_id, username, bilibili_mid, bilibili_name = user
                
                # 获取用户的观看历史
                history_query = text("""
                SELECT data_content 
                FROM user_data 
                WHERE user_mid = :user_mid AND data_type = 'watch_history'
                ORDER BY created_at DESC 
                LIMIT 1
                """)
                history_result = conn.execute(history_query, {'user_mid': str(user_id)})
                history_rows = history_result.fetchall()
                
                watch_history = []
                if history_rows:
                    watch_history = json.loads(history_rows[0][0])
                
                users_data.append({
                    'user_info': {
                        'user_id': user_id,
                        'username': username,
                        'bilibili_mid': bilibili_mid,
                        'bilibili_name': bilibili_name
                    },
                    'watch_history': watch_history
                })
        
        if len(users_data) < 2:
            return {
                "similar_users": [],
                "message": "用户数据不足，无法进行相似度分析"
            }
        
        # 找到相似用户
        similar_users = ml_service.find_similar_users(
            target_user_id=current_user['user_id'],
            users_data=users_data,
            top_n=5
        )
        
        return {
            "similar_users": similar_users,
            "total_users": len(users_data),
            "current_user_id": current_user['user_id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/user-based-recommendations")
async def get_user_based_recommendations(
    limit: int = 10,
    current_user: dict = Depends(require_auth)
):
    """基于相似用户的推荐"""
    try:
        with engine.connect() as conn:
            videos_df = pd.read_sql("""
            SELECT bvid, title, view, `like`, coin, share, tname, pubdate, `desc`
            FROM videos 
            ORDER BY collected_at DESC 
            LIMIT 500
            """, conn)
        
        if videos_df.empty:
            raise HTTPException(status_code=404, detail="暂无视频数据")
        
        # 获取所有用户数据
        users_data = []
        
        with engine.connect() as conn:
            # 获取所有有B站数据的用户
            users_query = text("""
            SELECT DISTINCT u.id, u.username, u.bilibili_mid, u.bilibili_name
            FROM users u
            WHERE u.bilibili_mid IS NOT NULL
            """)
            users_result = conn.execute(users_query)
            users = users_result.fetchall()
            
            for user in users:
                user_id, username, bilibili_mid, bilibili_name = user
                
                # 获取用户的观看历史
                history_query = text("""
                SELECT data_content 
                FROM user_data 
                WHERE user_mid = :user_mid AND data_type = 'watch_history'
                ORDER BY created_at DESC 
                LIMIT 1
                """)
                history_result = conn.execute(history_query, {'user_mid': str(user_id)})
                history_rows = history_result.fetchall()
                
                watch_history = []
                if history_rows:
                    watch_history = json.loads(history_rows[0][0])
                
                users_data.append({
                    'user_info': {
                        'user_id': user_id,
                        'username': username,
                        'bilibili_mid': bilibili_mid,
                        'bilibili_name': bilibili_name
                    },
                    'watch_history': watch_history
                })
        
        if len(users_data) < 2:
            # 如果用户数据不足，回退到普通推荐
            recommendations = ml_service.get_video_recommendations(
                videos_df=videos_df,
                top_n=limit
            )
            return {
                "recommendations": recommendations,
                "recommendation_type": "popular",
                "message": "用户数据不足，显示热门推荐"
            }
        
        # 基于用户相似度的推荐
        recommendations = ml_service.get_user_based_recommendations(
            target_user_id=current_user['user_id'],
            users_data=users_data,
            videos_df=videos_df,
            top_n=limit
        )
        
        return {
            "recommendations": recommendations,
            "recommendation_type": "user_collaborative_filtering",
            "total_users": len(users_data),
            "current_user_id": current_user['user_id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== AI智能问答相关接口 ==============

@app.post("/api/ai/chat", response_model=AIQueryResponse)
async def ai_chat(request: AIQueryRequest):
    """
    AI智能问答接口

    Args:
        request: 包含用户查询和对话历史的请求

    Returns:
        AIQueryResponse: AI回答结果
    """
    try:
        result = await ai_service.chat(
            user_query=request.query,
            conversation_history=request.conversation_history
        )

        return AIQueryResponse(**result)

    except Exception as e:
        logger.error(f"AI聊天服务失败: {str(e)}")
        return AIQueryResponse(
            success=False,
            response="抱歉，AI服务暂时不可用，请稍后再试。",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

@app.get("/api/ai/suggestions")
async def get_ai_suggestions():
    """
    获取智能问题建议

    Returns:
        Dict: 包含建议问题列表
    """
    try:
        suggestions = ai_service.get_smart_suggestions("")

        return {
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取AI建议失败: {str(e)}")
        return {
            "suggestions": [
                "最近一周哪个分区的视频表现最好？",
                "播放量趋势如何变化？",
                "什么类型的视频更容易火爆？",
                "最佳发布时间是什么时候？"
            ],
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.post("/api/ai/analyze-trend")
async def ai_analyze_trend(metric: str = "view", time_range: str = "7d"):
    """
    AI数据趋势分析

    Args:
        metric: 分析指标 (view, like, coin, share等)
        time_range: 时间范围

    Returns:
        Dict: 趋势分析结果
    """
    try:
        result = await ai_service.analyze_data_trend(
            metric=metric,
            time_range=time_range
        )

        return result

    except Exception as e:
        logger.error(f"AI趋势分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/status")
async def get_ai_status():
    """
    获取AI服务状态

    Returns:
        Dict: AI服务状态信息
    """
    try:
        test_query = "测试连接"
        test_result = await ai_service.chat(test_query, [])

        status = {
            "service_available": test_result.get("success", False),
            "model": "deepseek-v3",
            "api_endpoint": "https://api.deepseek.com",
            "database_connected": ai_service.engine is not None,
            "last_check": datetime.now().isoformat()
        }

        return status

    except Exception as e:
        logger.error(f"AI状态检查失败: {str(e)}")
        return {
            "service_available": False,
            "model": "deepseek-v3",
            "api_endpoint": "https://api.deepseek.com",
            "database_connected": ai_service.engine is not None,
            "last_check": datetime.now().isoformat(),
            "error": str(e)
        }


@app.post("/api/reports/generate-daily")
async def generate_daily_report(request: DailyReportRequest):
    """生成日报"""
    try:
        target_date = None
        if request.target_date:
            target_date = datetime.fromisoformat(request.target_date)

        report = await report_service.generate_daily_report(target_date)

        if report["success"]:
            file_path = report_service.save_report(report)
            report["file_path"] = file_path

            clean_report = report_service._clean_data_for_json(report)

            return JSONResponse(content={
                "success": True,
                "message": "日报生成成功",
                "report": clean_report
            })
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"日报生成失败: {report.get('error', '未知错误')}"
                }
            )

    except Exception as e:
        logger.error(f"生成日报API失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }
        )

@app.post("/api/reports/generate-weekly")
async def generate_weekly_report(request: WeeklyReportRequest):
    """生成周报"""
    try:
        logger.info(f"收到周报生成请求: {request}")
        logger.info(f"请求参数 - week_start: {request.week_start}")

        week_start = None
        if request.week_start:
            week_start = datetime.fromisoformat(request.week_start)
            logger.info(f"解析后的week_start: {week_start}")

        logger.info("开始生成周报...")
        report = await report_service.generate_weekly_report(week_start)
        logger.info(f"周报生成结果: success={report.get('success')}")

        if report["success"]:
            logger.info("保存报告...")
            file_path = report_service.save_report(report)
            report["file_path"] = file_path
            logger.info(f"报告保存完成: {file_path}")

            logger.info("清理数据进行JSON序列化...")
            try:
                clean_report = report_service._clean_data_for_json(report)
                logger.info("数据清理完成")
            except Exception as clean_error:
                logger.error(f"数据清理失败: {str(clean_error)}")
                raise clean_error

            logger.info("构建响应...")
            response_data = {
                "success": True,
                "message": "周报生成成功",
                "report": clean_report
            }

            try:
                import json
                json.dumps(response_data)
                logger.info("JSON序列化测试成功")
            except Exception as json_error:
                logger.error(f"JSON序列化测试失败: {str(json_error)}")
                raise json_error

            return JSONResponse(content=response_data)
        else:
            logger.error(f"周报生成失败: {report.get('error', '未知错误')}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"周报生成失败: {report.get('error', '未知错误')}"
                }
            )

    except Exception as e:
        logger.error(f"生成周报API失败: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }
        )

@app.get("/api/reports/list")
async def list_reports():
    """获取报告列表"""
    try:
        import os
        from pathlib import Path

        reports_dir = Path("reports")
        if not reports_dir.exists():
            return JSONResponse(content={
                "success": True,
                "reports": []
            })

        reports = []
        for file_path in reports_dir.glob("*.md"):
            stat = file_path.stat()
            reports.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        reports.sort(key=lambda x: x["modified_at"], reverse=True)

        return JSONResponse(content={
            "success": True,
            "reports": reports
        })

    except Exception as e:
        logger.error(f"获取报告列表失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }
        )

@app.get("/api/reports/download/{filename}")
async def download_report(filename: str):
    """下载报告文件"""
    try:
        from pathlib import Path

        file_path = Path("reports") / filename

        if not file_path.exists():
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "报告文件不存在"
                }
            )

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='text/markdown'
        )

    except Exception as e:
        logger.error(f"下载报告失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }
        )

@app.get("/api/reports/view/{filename}")
async def view_report(filename: str):
    """查看报告内容"""
    try:
        from pathlib import Path

        file_path = Path("reports") / filename

        if not file_path.exists():
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "报告文件不存在"
                }
            )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "content": content
        })

    except Exception as e:
        logger.error(f"查看报告失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }
        )

@app.delete("/api/reports/{filename}")
async def delete_report(filename: str):
    """删除报告文件"""
    try:
        from pathlib import Path

        file_path = Path("reports") / filename

        if not file_path.exists():
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "报告文件不存在"
                }
            )

        file_path.unlink()

        return JSONResponse(content={
            "success": True,
            "message": "报告删除成功"
        })

    except Exception as e:
        logger.error(f"删除报告失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"服务器错误: {str(e)}"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 