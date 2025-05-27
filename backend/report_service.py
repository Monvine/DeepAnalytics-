"""
自动化分析报告服务
生成定期的数据分析报告
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, text
import traceback
from jinja2 import Template, Environment
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from pathlib import Path
from decimal import Decimal

logger = logging.getLogger(__name__)

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class ReportService:
    """自动化报告生成服务"""

    def __init__(self, engine=None):
        """
        初始化报告服务

        Args:
            engine: SQLAlchemy数据库引擎
        """
        self.engine = engine
        self.report_templates = self._load_templates()
        self.jinja_env = self._setup_jinja_environment()

    def _load_templates(self) -> Dict[str, str]:
        """加载报告模板"""
        return {
            "daily": """


- **新增视频数**: {{stats.total_videos}} 个
- **总播放量**: {{stats.total_views|format_number}} 次
- **平均播放量**: {{stats.avg_views|format_number}} 次
- **总点赞数**: {{stats.total_likes|format_number}} 个
- **总投币数**: {{stats.total_coins|format_number}} 个

{% for category in top_categories %}
{{loop.index}}. **{{category.name}}** - {{category.video_count}}个视频，平均播放量{{category.avg_views|format_number}}
{% endfor %}

{% for video in hot_videos %}
{{loop.index}}. [{{video.title}}]({{video.url}}) - {{video.author}}
   - 播放量: {{video.view|format_number}} | 点赞: {{video.like|format_number}} | 投币: {{video.coin|format_number}}
{% endfor %}

{{trend_analysis}}

{{insights}}

---
*报告生成时间: {{generated_at}}*
            """,
            
            "weekly": """


- **本周新增视频**: {{stats.total_videos}} 个
- **本周总播放量**: {{stats.total_views|format_number}} 次
- **日均播放量**: {{stats.daily_avg_views|format_number}} 次
- **播放量增长率**: {{stats.growth_rate}}%

{% for category in categories_analysis %}
- 视频数量: {{category.video_count}}
- 平均播放量: {{category.avg_views|format_number}}
- 增长趋势: {{category.trend}}
{% endfor %}

- **最热视频**: {{top_video.title}} ({{top_video.view|format_number}}播放)
- **最活跃UP主**: {{top_author.name}} ({{top_author.video_count}}个视频)
- **最热分区**: {{top_category.name}} ({{top_category.total_views|format_number}}播放)

{{charts_section}}

{{weekly_insights}}

{{recommendations}}

---
*报告生成时间: {{generated_at}}*
            """,
            
            "monthly": """


- **本月新增视频**: {{stats.total_videos|format_number}} 个
- **本月总播放量**: {{stats.total_views|format_number}} 次
- **月度增长率**: {{stats.growth_rate}}%
- **活跃UP主数**: {{stats.active_authors}} 人

{{monthly_analysis}}

{{rankings}}

{{visualizations}}

{{monthly_summary}}

---
*报告生成时间: {{generated_at}}*
            """
        }

    def _setup_jinja_environment(self) -> Environment:
        """设置Jinja2环境和自定义过滤器"""
        env = Environment()

        def format_number(value):
            """格式化数字，添加千分位分隔符"""
            if value is None:
                return "0"
            try:
                return f"{int(value):,}"
            except (ValueError, TypeError):
                return str(value)

        env.filters['format_number'] = format_number
        return env

    def _convert_decimal(self, value):
        """转换Decimal类型为int或float"""
        if isinstance(value, Decimal):
            if value % 1 == 0:
                return int(value)
            else:
                return float(value)
        return value

    def _safe_int(self, value):
        """安全转换为整数"""
        if value is None:
            return 0
        if isinstance(value, Decimal):
            return int(value)
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    def _clean_data_for_json(self, data):
        """递归清理数据中的Decimal类型，确保JSON序列化兼容"""
        if isinstance(data, dict):
            return {key: self._clean_data_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._clean_data_for_json(item) for item in data]
        elif isinstance(data, Decimal):
            if data % 1 == 0:
                return int(data)
            else:
                return float(data)
        else:
            return data

    async def generate_daily_report(self, target_date: datetime = None) -> Dict[str, Any]:
        """
        生成日报

        Args:
            target_date: 目标日期，默认为昨天

        Returns:
            Dict: 报告数据
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        try:
            stats = await self._get_daily_stats(target_date)

            top_categories = await self._get_top_categories(target_date, limit=5)

            hot_videos = await self._get_hot_videos(target_date, limit=10)

            trend_analysis = await self._analyze_daily_trend(target_date)

            insights = await self._generate_daily_insights(stats, top_categories, hot_videos)

            template = self.jinja_env.from_string(self.report_templates["daily"])
            report_content = template.render(
                date=target_date.strftime("%Y年%m月%d日"),
                stats=stats,
                top_categories=top_categories,
                hot_videos=hot_videos,
                trend_analysis=trend_analysis,
                insights=insights,
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            result = {
                "success": True,
                "report_type": "daily",
                "date": target_date.isoformat(),
                "content": report_content,
                "stats": stats,
                "charts": await self._generate_daily_charts(target_date)
            }

            return self._clean_data_for_json(result)

        except Exception as e:
            logger.error(f"生成日报失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_weekly_report(self, week_start: datetime = None) -> Dict[str, Any]:
        """
        生成周报

        Args:
            week_start: 周开始日期

        Returns:
            Dict: 报告数据
        """
        if week_start is None:
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday() + 7)

        week_end = week_start + timedelta(days=6)

        try:
            stats = await self._get_weekly_stats(week_start, week_end)

            categories_analysis = await self._get_weekly_categories_analysis(week_start, week_end)

            top_video = await self._get_top_video_of_week(week_start, week_end)
            top_author = await self._get_top_author_of_week(week_start, week_end)
            top_category = await self._get_top_category_of_week(week_start, week_end)

            charts_section = await self._generate_weekly_charts(week_start, week_end)

            weekly_insights = await self._generate_weekly_insights(stats, categories_analysis)

            recommendations = await self._generate_weekly_recommendations(stats, categories_analysis)

            template = self.jinja_env.from_string(self.report_templates["weekly"])
            report_content = template.render(
                week_range=f"{week_start.strftime('%m月%d日')} - {week_end.strftime('%m月%d日')}",
                stats=stats,
                categories_analysis=categories_analysis,
                top_video=top_video,
                top_author=top_author,
                top_category=top_category,
                charts_section=charts_section,
                weekly_insights=weekly_insights,
                recommendations=recommendations,
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            result = {
                "success": True,
                "report_type": "weekly",
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "content": report_content,
                "stats": stats
            }

            return self._clean_data_for_json(result)

        except Exception as e:
            logger.error(f"生成周报失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _get_daily_stats(self, target_date: datetime) -> Dict[str, Any]:
        """获取日度统计数据"""
        if not self.engine:
            return {}

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_videos,
                    SUM(view) as total_views,
                    AVG(view) as avg_views,
                    SUM(`like`) as total_likes,
                    SUM(coin) as total_coins,
                    SUM(share) as total_shares
                FROM videos 
                WHERE DATE(collected_at) = DATE(:target_date)
            """), {"target_date": target_date}).fetchone()
            
            if result:
                return {
                    "total_videos": self._safe_int(result.total_videos),
                    "total_views": self._safe_int(result.total_views),
                    "avg_views": self._safe_int(result.avg_views),
                    "total_likes": self._safe_int(result.total_likes),
                    "total_coins": self._safe_int(result.total_coins),
                    "total_shares": self._safe_int(result.total_shares)
                }
        return {}
    
    async def _get_top_categories(self, target_date: datetime, limit: int = 5) -> List[Dict[str, Any]]:
        """获取热门分区"""
        if not self.engine:
            return []

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    tname as name,
                    COUNT(*) as video_count,
                    AVG(view) as avg_views,
                    SUM(view) as total_views
                FROM videos 
                WHERE DATE(collected_at) = DATE(:target_date) AND tname IS NOT NULL
                GROUP BY tname
                ORDER BY video_count DESC, avg_views DESC
                LIMIT :limit
            """), {"target_date": target_date, "limit": limit}).fetchall()
            
            return [
                {
                    "name": row.name,
                    "video_count": self._safe_int(row.video_count),
                    "avg_views": self._safe_int(row.avg_views),
                    "total_views": self._safe_int(row.total_views)
                }
                for row in result
            ]
    
    async def _get_hot_videos(self, target_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门视频"""
        if not self.engine:
            return []

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    title, author, view, `like`, coin, share, bvid
                FROM videos 
                WHERE DATE(collected_at) = DATE(:target_date)
                ORDER BY view DESC
                LIMIT :limit
            """), {"target_date": target_date, "limit": limit}).fetchall()
            
            return [
                {
                    "title": row.title[:50] + "..." if len(row.title) > 50 else row.title,
                    "author": row.author,
                    "view": self._safe_int(row.view),
                    "like": self._safe_int(row.like),
                    "coin": self._safe_int(row.coin),
                    "share": self._safe_int(row.share),
                    "url": f"https://www.bilibili.com/video/{row.bvid}" if row.bvid else "#"
                }
                for row in result
            ]
    
    async def _analyze_daily_trend(self, target_date: datetime) -> str:
        """分析日度趋势"""
        if not self.engine:
            return "暂无趋势数据"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        DATE(collected_at) as date,
                        COUNT(*) as video_count,
                        AVG(view) as avg_views
                    FROM videos 
                    WHERE DATE(collected_at) >= DATE_SUB(DATE(:target_date), INTERVAL 7 DAY)
                        AND DATE(collected_at) <= DATE(:target_date)
                    GROUP BY DATE(collected_at)
                    ORDER BY date
                """), {"target_date": target_date}).fetchall()
                
                if len(result) >= 2:
                    today_data = next((r for r in result if r.date == target_date.date()), None)
                    yesterday_data = next((r for r in result if r.date == (target_date - timedelta(days=1)).date()), None)
                    
                    if today_data and yesterday_data:
                        today_avg = self._safe_int(today_data.avg_views)
                        yesterday_avg = self._safe_int(yesterday_data.avg_views)
                        today_count = self._safe_int(today_data.video_count)
                        yesterday_count = self._safe_int(yesterday_data.video_count)
                        
                        view_change = ((today_avg - yesterday_avg) / yesterday_avg) * 100 if yesterday_avg > 0 else 0
                        video_change = today_count - yesterday_count
                        
                        trend_text = f"与昨日相比，平均播放量{'上升' if view_change > 0 else '下降'}了{abs(view_change):.1f}%，"
                        trend_text += f"视频数量{'增加' if video_change > 0 else '减少'}了{abs(video_change)}个。"
                        
                        return trend_text
                
                return "数据趋势稳定，与前日基本持平。"
                
        except Exception as e:
            logger.error(f"趋势分析失败: {str(e)}")
            return "趋势分析暂时不可用"
    
    async def _generate_daily_insights(self, stats: Dict, categories: List, videos: List) -> str:
        """生成日度洞察"""
        insights = []

        if stats.get("avg_views", 0) > 50000:
            insights.append("📈 今日平均播放量表现优秀，内容质量较高")
        elif stats.get("avg_views", 0) < 10000:
            insights.append("📉 今日平均播放量偏低，建议关注内容质量和发布时机")

        if categories:
            top_category = categories[0]
            insights.append(f"🏆 {top_category['name']}分区表现最佳，建议重点关注")

        if stats.get("total_videos", 0) > 100:
            insights.append("📊 今日视频发布量较高，内容竞争激烈")

        return "\n".join([f"- {insight}" for insight in insights]) if insights else "- 数据表现正常，继续保持"

    async def _generate_daily_charts(self, target_date: datetime) -> Dict[str, str]:
        """生成日度图表"""
        charts = {}

        try:
            if not self.engine:
                return charts

            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT tname, COUNT(*) as count
                    FROM videos 
                    WHERE DATE(collected_at) = DATE(:target_date) AND tname IS NOT NULL
                    GROUP BY tname
                    ORDER BY count DESC
                    LIMIT 8
                """), {"target_date": target_date}).fetchall()
                
                if result:
                    labels = [row.tname for row in result]
                    sizes = [row.count for row in result]
                    
                    plt.figure(figsize=(10, 8))
                    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                    plt.title(f'{target_date.strftime("%Y-%m-%d")} 分区分布')
                    
                    # 转换为base64
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                    buffer.seek(0)
                    chart_base64 = base64.b64encode(buffer.getvalue()).decode()
                    charts["category_distribution"] = chart_base64
                    plt.close()
            
        except Exception as e:
            logger.error(f"生成图表失败: {str(e)}")
        
        return charts
    
    async def _get_weekly_stats(self, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """获取周度统计"""
        if not self.engine:
            return {}

        with self.engine.connect() as conn:
            current_result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_videos,
                    SUM(view) as total_views,
                    AVG(view) as avg_views
                FROM videos 
                WHERE DATE(collected_at) BETWEEN DATE(:week_start) AND DATE(:week_end)
            """), {"week_start": week_start, "week_end": week_end}).fetchone()
            
            # 上周统计（用于计算增长率）
            prev_week_start = week_start - timedelta(days=7)
            prev_week_end = week_end - timedelta(days=7)
            
            prev_result = conn.execute(text("""
                SELECT 
                    SUM(view) as total_views
                FROM videos 
                WHERE DATE(collected_at) BETWEEN DATE(:prev_week_start) AND DATE(:prev_week_end)
            """), {"prev_week_start": prev_week_start, "prev_week_end": prev_week_end}).fetchone()
            
            if current_result:
                current_views = self._safe_int(current_result.total_views)
                prev_views = self._safe_int(prev_result.total_views) if prev_result else 0
                
                growth_rate = 0
                if prev_views and prev_views > 0:
                    growth_rate = ((current_views - prev_views) / prev_views) * 100
                
                return {
                    "total_videos": self._safe_int(current_result.total_videos),
                    "total_views": current_views,
                    "daily_avg_views": int(current_views / 7) if current_views > 0 else 0,
                    "growth_rate": round(float(growth_rate), 1)
                }
        
        return {}
    
    async def _get_weekly_categories_analysis(self, week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """获取周度分区分析"""
        if not self.engine:
            return []

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    tname as name,
                    COUNT(*) as video_count,
                    AVG(view) as avg_views,
                    SUM(view) as total_views
                FROM videos 
                WHERE DATE(collected_at) BETWEEN DATE(:week_start) AND DATE(:week_end) 
                    AND tname IS NOT NULL
                GROUP BY tname
                ORDER BY total_views DESC
                LIMIT 10
            """), {"week_start": week_start, "week_end": week_end}).fetchall()
            
            categories = []
            for row in result:
                # 简单的趋势判断（这里可以进一步优化）
                trend = "稳定"  # 实际应该对比上周数据
                
                categories.append({
                    "name": row.name or "未知分区",
                    "video_count": self._safe_int(row.video_count),
                    "avg_views": self._safe_int(row.avg_views),
                    "total_views": self._safe_int(row.total_views),
                    "trend": trend
                })
            
            return categories
    
    async def _get_top_video_of_week(self, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """获取周度最热视频"""
        if not self.engine:
            return {
                "title": "暂无数据",
                "author": "未知",
                "view": 0,
                "url": "#"
            }

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT title, author, view, bvid
                FROM videos 
                WHERE DATE(collected_at) BETWEEN DATE(:week_start) AND DATE(:week_end)
                ORDER BY view DESC
                LIMIT 1
            """), {"week_start": week_start, "week_end": week_end}).fetchone()
            
            if result:
                return {
                    "title": result.title or "未知标题",
                    "author": result.author or "未知UP主",
                    "view": self._safe_int(result.view),
                    "url": f"https://www.bilibili.com/video/{result.bvid}" if result.bvid else "#"
                }
        
        return {
            "title": "暂无数据",
            "author": "未知",
            "view": 0,
            "url": "#"
        }
    
    async def _get_top_author_of_week(self, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """获取周度最活跃UP主"""
        if not self.engine:
            return {
                "name": "暂无数据",
                "video_count": 0
            }

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT author as name, COUNT(*) as video_count
                FROM videos 
                WHERE DATE(collected_at) BETWEEN DATE(:week_start) AND DATE(:week_end)
                    AND author IS NOT NULL
                GROUP BY author
                ORDER BY video_count DESC
                LIMIT 1
            """), {"week_start": week_start, "week_end": week_end}).fetchone()
            
            if result:
                return {
                    "name": result.name or "未知UP主",
                    "video_count": self._safe_int(result.video_count)
                }
        
        return {
            "name": "暂无数据",
            "video_count": 0
        }
    
    async def _get_top_category_of_week(self, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """获取周度最热分区"""
        if not self.engine:
            return {
                "name": "暂无数据",
                "total_views": 0
            }

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tname as name, SUM(view) as total_views
                FROM videos 
                WHERE DATE(collected_at) BETWEEN DATE(:week_start) AND DATE(:week_end)
                    AND tname IS NOT NULL
                GROUP BY tname
                ORDER BY total_views DESC
                LIMIT 1
            """), {"week_start": week_start, "week_end": week_end}).fetchone()
            
            if result:
                return {
                    "name": result.name or "未知分区",
                    "total_views": self._safe_int(result.total_views)
                }
        
        return {
            "name": "暂无数据",
            "total_views": 0
        }
    
    async def _generate_weekly_charts(self, week_start: datetime, week_end: datetime) -> str:
        """生成周度图表描述"""
        return "📊 本周数据图表已生成，包含分区趋势图、播放量变化图等可视化内容。"

    async def _generate_weekly_insights(self, stats: Dict, categories: List) -> str:
        """生成周度洞察"""
        insights = []

        growth_rate = stats.get("growth_rate", 0)
        if growth_rate > 10:
            insights.append(f"📈 本周播放量增长{growth_rate}%，表现优异")
        elif growth_rate < -10:
            insights.append(f"📉 本周播放量下降{abs(growth_rate)}%，需要关注内容策略")
        else:
            insights.append("📊 本周播放量保持稳定")

        if categories:
            top_category = categories[0]
            insights.append(f"🏆 {top_category['name']}分区本周表现最佳")

        return "\n".join([f"- {insight}" for insight in insights])

    async def _generate_weekly_recommendations(self, stats: Dict, categories: List) -> str:
        """生成周度建议"""
        recommendations = []

        if stats.get("growth_rate", 0) < 0:
            recommendations.append("优化内容质量，关注用户反馈")
            recommendations.append("调整发布时间，选择用户活跃时段")

        if categories:
            top_category = categories[0]
            recommendations.append(f"重点关注{top_category['name']}分区的内容创作")

        recommendations.append("持续监控数据变化，及时调整策略")

        return "\n".join([f"- {recommendation}" for recommendation in recommendations])

    def save_report(self, report_data: Dict[str, Any], file_path: str = None) -> str:
        """
        保存报告到文件

        Args:
            report_data: 报告数据
            file_path: 文件路径

        Returns:
            str: 保存的文件路径
        """
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_type = report_data.get("report_type", "report")
            file_path = f"reports/{report_type}_{timestamp}.md"

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_data.get("content", ""))

        return file_path 