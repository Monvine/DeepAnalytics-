"""
AI智能服务模块
基于DeepSeek V3模型实现智能问答助手
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from openai import OpenAI
from sqlalchemy import create_engine, text
import traceback

logger = logging.getLogger(__name__)

class AIService:
    """AI智能服务类"""

    def __init__(self, api_key: str, engine=None):
        """
        初始化AI服务

        Args:
            api_key: DeepSeek API密钥
            engine: SQLAlchemy数据库引擎
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.engine = engine

        self.system_prompt = """你是一个专业的B站数据分析助手，名字叫"B站小助手"。你的主要职责是：

1. 分析B站视频数据，包括播放量、点赞数、投币数、分享数等指标
2. 解答用户关于B站数据趋势、热门内容、UP主表现等问题
3. 提供数据洞察和建议
4. 用中文回答，语言要专业但易懂
5. 如果用户问题超出B站数据分析范围，请礼貌地引导回主题

回答格式要求：
- **必须使用Markdown格式**回答，让内容更清晰易读
- 使用标题（
- 使用**粗体**强调重要数据和关键点
- 使用列表（-、1.）来展示数据统计
- 使用表格展示对比数据
- 使用代码块（```）展示具体数值或公式
- 使用引用（>）来突出重要结论或建议

内容要求：
- 基于实际数据进行分析
- 提供具体的数字和事实
- 给出有价值的洞察和建议
- 保持专业和客观的态度

示例格式：

- **播放量**：123,456 次
- **点赞数**：12,345 个

> 根据数据显示，该分区呈现上升趋势

1. 建议一
2. 建议二
"""

    def get_data_context(self, query: str) -> str:
        """
        根据查询获取相关的数据上下文

        Args:
            query: 用户查询

        Returns:
            str: 数据上下文信息
        """
        if not self.engine:
            return "暂无数据库连接，无法获取最新数据。"

        try:
            context_parts = []

            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_videos,
                        AVG(view) as avg_views,
                        AVG(`like`) as avg_likes,
                        AVG(coin) as avg_coins,
                        AVG(share) as avg_shares,
                        MAX(view) as max_views,
                        MIN(view) as min_views
                    FROM videos 
                    WHERE collected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                """)).fetchone()
                
                if result:
                    context_parts.append(f"""
最近7天数据统计：
- 总视频数：{result.total_videos}
- 平均播放量：{int(result.avg_views):,}
- 平均点赞数：{int(result.avg_likes):,}
- 平均投币数：{int(result.avg_coins):,}
- 平均分享数：{int(result.avg_shares):,}
- 最高播放量：{int(result.max_views):,}
- 最低播放量：{int(result.min_views):,}
""")

                # 热门分区统计
                result = conn.execute(text("""
                    SELECT 
                        tname,
                        COUNT(*) as video_count,
                        AVG(view) as avg_views,
                        SUM(view) as total_views
                    FROM videos 
                    WHERE collected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                        AND tname IS NOT NULL
                    GROUP BY tname
                    ORDER BY video_count DESC
                    LIMIT 5
                """)).fetchall()
                
                if result:
                    context_parts.append("\n热门分区TOP5：")
                    for row in result:
                        context_parts.append(f"- {row.tname}：{row.video_count}个视频，平均播放量{int(row.avg_views):,}")

                # 最近热门视频
                result = conn.execute(text("""
                    SELECT title, author, view, `like`, coin, share, tname
                    FROM videos 
                    WHERE collected_at >= DATE_SUB(NOW(), INTERVAL 3 DAY)
                    ORDER BY view DESC
                    LIMIT 5
                """)).fetchall()
                
                if result:
                    context_parts.append("\n最近3天热门视频：")
                    for i, row in enumerate(result, 1):
                        context_parts.append(f"{i}. {row.title[:30]}...（{row.author}）- 播放量：{int(row.view):,}")

                # 根据查询关键词获取特定数据
                if "游戏" in query or "game" in query.lower():
                    result = conn.execute(text("""
                        SELECT COUNT(*) as count, AVG(view) as avg_views
                        FROM videos 
                        WHERE (tname LIKE '%游戏%' OR title LIKE '%游戏%')
                            AND collected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    """)).fetchone()
                    if result and result.count > 0:
                        context_parts.append(f"\n游戏相关视频：{result.count}个，平均播放量{int(result.avg_views):,}")

                if "科技" in query or "tech" in query.lower():
                    result = conn.execute(text("""
                        SELECT COUNT(*) as count, AVG(view) as avg_views
                        FROM videos 
                        WHERE (tname LIKE '%科技%' OR title LIKE '%科技%')
                            AND collected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    """)).fetchone()
                    if result and result.count > 0:
                        context_parts.append(f"\n科技相关视频：{result.count}个，平均播放量{int(result.avg_views):,}")

            return "".join(context_parts) if context_parts else "暂无相关数据。"
            
        except Exception as e:
            logger.error(f"获取数据上下文失败: {str(e)}")
            return f"数据获取出现错误：{str(e)}"

    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        分析用户查询意图

        Args:
            query: 用户查询

        Returns:
            Dict: 查询意图分析结果
        """
        intent = {
            "type": "general",
            "entities": [],
            "time_range": None,
            "metrics": []
        }

        if any(word in query for word in ["趋势", "变化", "增长", "下降", "对比"]):
            intent["type"] = "trend_analysis"
        elif any(word in query for word in ["推荐", "建议", "怎么", "如何"]):
            intent["type"] = "recommendation"
        elif any(word in query for word in ["多少", "统计", "数据", "排行"]):
            intent["type"] = "data_query"

        categories = ["游戏", "科技", "娱乐", "音乐", "舞蹈", "影视", "知识", "美食"]
        for category in categories:
            if category in query:
                intent["entities"].append(category)

        if "今天" in query or "今日" in query:
            intent["time_range"] = "today"
        elif "昨天" in query:
            intent["time_range"] = "yesterday"
        elif "本周" in query or "这周" in query:
            intent["time_range"] = "this_week"
        elif "上周" in query:
            intent["time_range"] = "last_week"
        elif "本月" in query or "这个月" in query:
            intent["time_range"] = "this_month"

        metrics_map = {
            "播放量": "view", "观看": "view", "点击": "view",
            "点赞": "like", "喜欢": "like",
            "投币": "coin", "硬币": "coin",
            "分享": "share", "转发": "share",
            "弹幕": "danmaku", "评论": "reply",
            "收藏": "favorite"
        }

        for keyword, metric in metrics_map.items():
            if keyword in query:
                intent["metrics"].append(metric)

        return intent

    async def chat(self, user_query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        智能问答主方法

        Args:
            user_query: 用户查询
            conversation_history: 对话历史

        Returns:
            Dict: 回答结果
        """
        try:
            intent = self.analyze_query_intent(user_query)

            data_context = self.get_data_context(user_query)

            messages = [{"role": "system", "content": self.system_prompt}]

            if data_context:
                messages.append({
                    "role": "system", 
                    "content": f"当前数据上下文：\n{data_context}"
                })

            if conversation_history:
                for msg in conversation_history[-5:]:
                    messages.append(msg)

            messages.append({"role": "user", "content": user_query})

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=1.0,
                max_tokens=2000,
                stream=False
            )

            assistant_response = response.choices[0].message.content

            return {
                "success": True,
                "response": assistant_response,
                "intent": intent,
                "data_context_available": bool(data_context and data_context != "暂无相关数据。"),
                "timestamp": datetime.now().isoformat(),
                "model": "deepseek-v3"
            }

        except Exception as e:
            logger.error(f"AI聊天服务失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "response": "抱歉，AI服务暂时不可用，请稍后再试。",
                "timestamp": datetime.now().isoformat()
            }

    async def analyze_data_trend(self, metric: str, time_range: str = "7d") -> Dict[str, Any]:
        """
        分析数据趋势

        Args:
            metric: 指标名称 (view, like, coin, share等)
            time_range: 时间范围

        Returns:
            Dict: 趋势分析结果
        """
        if not self.engine:
            return {"success": False, "error": "数据库连接不可用"}

        try:
            with self.engine.connect() as conn:
                query = f"""
                    SELECT 
                        DATE(collected_at) as date,
                        COUNT(*) as video_count,
                        AVG({metric}) as avg_value,
                        SUM({metric}) as total_value
                    FROM videos 
                    WHERE collected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    GROUP BY DATE(collected_at)
                    ORDER BY date
                """

                result = conn.execute(text(query)).fetchall()

                if not result:
                    return {"success": False, "error": "暂无数据"}

                trend_data = []
                for row in result:
                    trend_data.append({
                        "date": row.date.strftime("%Y-%m-%d"),
                        "video_count": row.video_count,
                        "avg_value": float(row.avg_value),
                        "total_value": float(row.total_value)
                    })

                if len(trend_data) >= 2:
                    recent_avg = sum(item["avg_value"] for item in trend_data[-3:]) / min(3, len(trend_data))
                    earlier_avg = sum(item["avg_value"] for item in trend_data[:3]) / min(3, len(trend_data))

                    if recent_avg > earlier_avg * 1.1:
                        trend_direction = "上升"
                    elif recent_avg < earlier_avg * 0.9:
                        trend_direction = "下降"
                    else:
                        trend_direction = "稳定"
                else:
                    trend_direction = "数据不足"

                return {
                    "success": True,
                    "metric": metric,
                    "time_range": time_range,
                    "trend_direction": trend_direction,
                    "data": trend_data,
                    "summary": {
                        "total_videos": sum(item["video_count"] for item in trend_data),
                        "avg_metric": sum(item["avg_value"] for item in trend_data) / len(trend_data),
                        "peak_date": max(trend_data, key=lambda x: x["avg_value"])["date"]
                    }
                }

        except Exception as e:
            logger.error(f"趋势分析失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_smart_suggestions(self, context: str) -> List[str]:
        """
        基于上下文生成智能建议

        Args:
            context: 上下文信息

        Returns:
            List[str]: 建议列表
        """
        suggestions = [
            "最近一周哪个分区的视频表现最好？",
            "播放量趋势如何变化？",
            "什么类型的视频更容易火爆？",
            "最佳发布时间是什么时候？",
            "热门视频有什么共同特点？",
            "用户喜欢什么样的内容？",
            "如何提高视频的互动率？",
            "不同分区的数据对比如何？"
        ]

        return suggestions[:4]