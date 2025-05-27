import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
from textblob import TextBlob
import snownlp
import jieba
import re
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class VideoRecommendationSystem:
    """视频推荐系统"""

    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
        self.content_similarity_matrix = None
        self.video_features = None
        self.user_similarity_matrix = None
        self.user_features = None

    def prepare_content_features(self, videos_df):
        """准备内容特征"""
        videos_df['content'] = videos_df['title'].fillna('') + ' ' + videos_df.get('desc', '').fillna('')

        videos_df['content_seg'] = videos_df['content'].apply(
            lambda x: ' '.join(jieba.cut(str(x)))
        )

        tfidf_matrix = self.tfidf_vectorizer.fit_transform(videos_df['content_seg'])

        self.content_similarity_matrix = cosine_similarity(tfidf_matrix)
        self.video_features = videos_df[['bvid', 'title', 'view', 'like', 'coin', 'share']].copy()

        return self.content_similarity_matrix

    def get_content_based_recommendations(self, video_bvid, top_n=10):
        """基于内容的推荐"""
        if self.content_similarity_matrix is None:
            return []

        try:
            video_idx = self.video_features[self.video_features['bvid'] == video_bvid].index[0]
            sim_scores = list(enumerate(self.content_similarity_matrix[video_idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

            similar_videos = sim_scores[1:top_n+1]
            recommended_indices = [i[0] for i in similar_videos]

            recommendations = self.video_features.iloc[recommended_indices].to_dict('records')

            for i, rec in enumerate(recommendations):
                rec['similarity_score'] = similar_videos[i][1]

            return recommendations
        except:
            return []

    def get_popular_recommendations(self, all_videos, top_n=10):
        """热门视频推荐"""
        recommendations = all_videos.copy()

        view_norm = recommendations['view'] / recommendations['view'].max()
        like_norm = recommendations['like'] / recommendations['like'].max()
        coin_norm = recommendations['coin'] / recommendations['coin'].max()
        share_norm = recommendations['share'] / recommendations['share'].max()

        recommendations['popularity_score'] = (
            view_norm * 0.4 + 
            like_norm * 0.25 + 
            coin_norm * 0.2 + 
            share_norm * 0.15
        )

        if 'pubdate' in recommendations.columns:
            recommendations['pubdate'] = pd.to_datetime(recommendations['pubdate'])
            days_ago = (pd.Timestamp.now() - recommendations['pubdate']).dt.days
            time_factor = np.exp(-days_ago / 30)
            recommendations['popularity_score'] *= time_factor

        return recommendations.nlargest(top_n, 'popularity_score').to_dict('records')

    def get_collaborative_filtering_recommendations(self, user_history, all_videos, top_n=10):
        """协同过滤推荐（简化版）"""
        if not user_history:
            return self.get_popular_recommendations(all_videos, top_n)

        history_df = pd.DataFrame(user_history)
        avg_duration = history_df.get('duration', 0).mean() if 'duration' in history_df.columns else 300
        preferred_categories = history_df.get('tag_name', '').value_counts().head(3).index.tolist()

        recommendations = all_videos.copy()

        watched_bvids = []
        for item in user_history:
            history = item.get('history', {})
            bvid = history.get('bvid', '') if isinstance(history, dict) else ''
            if bvid:
                watched_bvids.append(bvid)

        recommendations = recommendations[~recommendations['bvid'].isin(watched_bvids)]

        if preferred_categories:
            recommendations['category_score'] = recommendations.get('tname', '').apply(
                lambda x: 2.0 if x in preferred_categories else 1.0
            )
        else:
            recommendations['category_score'] = 1.0

        recommendations['recommendation_score'] = (
            recommendations['view'] * 0.3 + 
            recommendations['like'] * 0.3 + 
            recommendations['coin'] * 0.2 + 
            recommendations['share'] * 0.2
        ) * recommendations['category_score']

        return recommendations.nlargest(top_n, 'recommendation_score').to_dict('records')

    def prepare_user_features(self, users_data):
        """准备用户特征矩阵"""
        user_profiles = []
        user_ids = []

        for user in users_data:
            user_info = user.get('user_info', {})
            watch_history = user.get('watch_history', [])

            user_id = user_info.get('user_id') or user_info.get('username') or user_info.get('mid')
            if not user_id:
                continue

            user_ids.append(str(user_id))

            profile = self._calculate_user_profile(watch_history)
            user_profiles.append(profile)

        if not user_profiles:
            return None, None

        feature_names = [
            'avg_view', 'avg_like', 'avg_coin', 'avg_share', 'avg_duration',
            'total_videos', 'unique_categories', 'activity_score',
            'tech_preference', 'entertainment_preference', 'game_preference',
            'knowledge_preference', 'music_preference', 'other_preference'
        ]

        user_features_df = pd.DataFrame(user_profiles, columns=feature_names, index=user_ids)

        scaler = StandardScaler()
        user_features_normalized = scaler.fit_transform(user_features_df)

        self.user_similarity_matrix = cosine_similarity(user_features_normalized)
        self.user_features = user_features_df

        return self.user_similarity_matrix, user_ids

    def _calculate_user_profile(self, watch_history):
        """计算单个用户的特征档案"""
        if not watch_history:
            return [0] * 14

        history_df = pd.DataFrame(watch_history)

        avg_view = history_df.get('view', 0).mean() if 'view' in history_df.columns else 0
        avg_like = history_df.get('like', 0).mean() if 'like' in history_df.columns else 0
        avg_coin = history_df.get('coin', 0).mean() if 'coin' in history_df.columns else 0
        avg_share = history_df.get('share', 0).mean() if 'share' in history_df.columns else 0
        avg_duration = history_df.get('duration', 300).mean() if 'duration' in history_df.columns else 300

        total_videos = len(watch_history)
        unique_categories = len(history_df.get('tag_name', []).unique()) if 'tag_name' in history_df.columns else 1

        activity_score = min(total_videos / 100, 1.0)

        category_counts = history_df.get('tag_name', pd.Series()).value_counts()
        total_count = len(history_df)

        tech_preference = category_counts.get('科技', 0) / total_count
        entertainment_preference = category_counts.get('娱乐', 0) / total_count
        game_preference = category_counts.get('游戏', 0) / total_count
        knowledge_preference = category_counts.get('知识', 0) / total_count
        music_preference = category_counts.get('音乐', 0) / total_count

        main_categories = ['科技', '娱乐', '游戏', '知识', '音乐']
        other_preference = sum(
            count for cat, count in category_counts.items() 
            if cat not in main_categories
        ) / total_count

        return [
            avg_view, avg_like, avg_coin, avg_share, avg_duration,
            total_videos, unique_categories, activity_score,
            tech_preference, entertainment_preference, game_preference,
            knowledge_preference, music_preference, other_preference
        ]

    def find_similar_users(self, target_user_id, users_data, top_n=5):
        """找到相似用户"""
        if self.user_similarity_matrix is None:
            self.prepare_user_features(users_data)

        if self.user_similarity_matrix is None:
            return []

        try:
            user_ids = list(self.user_features.index)
            target_idx = user_ids.index(str(target_user_id))

            sim_scores = list(enumerate(self.user_similarity_matrix[target_idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

            similar_users = sim_scores[1:top_n+1]

            results = []
            for idx, similarity in similar_users:
                similar_user_id = user_ids[idx]
                user_info = next(
                    (u['user_info'] for u in users_data 
                     if str(u['user_info'].get('user_id', u['user_info'].get('username', u['user_info'].get('mid')))) == similar_user_id),
                    {}
                )

                results.append({
                    'user_id': similar_user_id,
                    'user_info': user_info,
                    'similarity_score': similarity,
                    'user_features': self.user_features.loc[similar_user_id].to_dict()
                })

            return results
        except (ValueError, IndexError):
            return []

    def get_user_collaborative_recommendations(self, target_user_id, users_data, all_videos, top_n=10):
        """基于用户相似度的协同过滤推荐"""
        similar_users = self.find_similar_users(target_user_id, users_data, top_n=5)

        if not similar_users:
            return self.get_popular_recommendations(all_videos, top_n)

        target_user = next(
            (u for u in users_data 
             if str(u['user_info'].get('user_id', u['user_info'].get('username', u['user_info'].get('mid')))) == str(target_user_id)),
            None
        )

        if not target_user:
            return self.get_popular_recommendations(all_videos, top_n)

        target_watched = set()
        for item in target_user.get('watch_history', []):
            history = item.get('history', {})
            bvid = history.get('bvid', '') if isinstance(history, dict) else ''
            if bvid:
                target_watched.add(bvid)

        recommended_videos = {}

        for similar_user in similar_users:
            similar_user_data = next(
                (u for u in users_data 
                 if str(u['user_info'].get('user_id', u['user_info'].get('username', u['user_info'].get('mid')))) == similar_user['user_id']),
                None
            )

            if not similar_user_data:
                continue

            similarity_weight = similar_user['similarity_score']
            watch_history = similar_user_data.get('watch_history', [])

            for video in watch_history:
                history = video.get('history', {})
                bvid = history.get('bvid', '') if isinstance(history, dict) else ''

                if bvid and bvid not in target_watched:
                    if bvid not in recommended_videos:
                        recommended_videos[bvid] = {
                            'bvid': bvid,
                            'title': video.get('title', ''),
                            'tname': video.get('tag_name', ''),
                            'view': 0,
                            'like': 0,
                            'coin': 0,
                            'share': 0,
                            'recommendation_score': 0,
                            'similar_users_count': 0,
                            'similarity_sum': 0
                        }

                    recommended_videos[bvid]['recommendation_score'] += similarity_weight
                    recommended_videos[bvid]['similar_users_count'] += 1
                    recommended_videos[bvid]['similarity_sum'] += similarity_weight

        for video in recommended_videos.values():
            video['final_score'] = (
                video['similarity_sum'] / video['similar_users_count'] * 
                np.log(video['similar_users_count'] + 1)
            )

        sorted_recommendations = sorted(
            recommended_videos.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )

        return sorted_recommendations[:top_n]

class ViewPredictionModel:
    """播放量预测模型"""

    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'xgboost': xgb.XGBRegressor(random_state=42),
            'lightgbm': lgb.LGBMRegressor(random_state=42),
            'gradient_boosting': GradientBoostingRegressor(random_state=42)
        }
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.best_model = None
        self.feature_importance = None

    def prepare_features(self, videos_df):
        """准备特征工程"""
        df = videos_df.copy()

        df['pubdate'] = pd.to_datetime(df['pubdate'], unit='s', errors='coerce')
        df['hour'] = df['pubdate'].dt.hour
        df['day_of_week'] = df['pubdate'].dt.dayofweek
        df['month'] = df['pubdate'].dt.month

        df['title_length'] = df['title'].str.len()
        df['title_word_count'] = df['title'].apply(lambda x: len(str(x).split()))

        df['like_rate'] = df['like'] / (df['view'] + 1)
        df['coin_rate'] = df['coin'] / (df['view'] + 1)
        df['share_rate'] = df['share'] / (df['view'] + 1)
        df['interaction_rate'] = (df['like'] + df['coin'] + df['share']) / (df['view'] + 1)

        if 'tname' in df.columns:
            le_tname = LabelEncoder()
            df['tname_encoded'] = le_tname.fit_transform(df['tname'].fillna('其他'))
            self.label_encoders['tname'] = le_tname

        if 'owner' in df.columns:
            pass

        return df

    def train_models(self, videos_df, target_col='view'):
        """训练多个模型"""
        try:
            df = self.prepare_features(videos_df)

            feature_cols = [
                'hour', 'day_of_week', 'month', 'title_length', 'title_word_count'
            ]

            if 'tname_encoded' in df.columns:
                feature_cols.append('tname_encoded')

            if 'duration' in df.columns:
                df['duration_minutes'] = df['duration'] / 60
                feature_cols.append('duration_minutes')

            available_cols = [col for col in feature_cols if col in df.columns]
            df = df.dropna(subset=available_cols + [target_col])

            if len(df) < 10:
                return {"error": "数据量不足，无法训练模型", "data_count": len(df)}

            X = df[available_cols]
            y = df[target_col]

            if X.empty or len(available_cols) == 0:
                return {"error": "没有可用的特征列"}

            X_scaled = self.scaler.fit_transform(X)

            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )

            results = {}

            for name, model in self.models.items():
                try:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)

                    mse = mean_squared_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)

                    results[name] = {
                        'mse': float(mse),
                        'rmse': float(np.sqrt(mse)),
                        'r2': float(r2),
                        'model': model
                    }
                except Exception as e:
                    results[name] = {'error': str(e)}

            valid_results = {k: v for k, v in results.items() if 'error' not in v}
            if valid_results:
                self.best_model_name = min(valid_results.keys(), key=lambda x: valid_results[x]['mse'])
                self.best_model = valid_results[self.best_model_name]['model']

                if hasattr(self.best_model, 'feature_importances_'):
                    self.feature_importance = dict(zip(available_cols, self.best_model.feature_importances_))

                self.feature_cols = available_cols

            clean_results = {}
            for name, result in results.items():
                if 'model' in result:
                    clean_result = {k: v for k, v in result.items() if k != 'model'}
                    clean_results[name] = clean_result
                else:
                    clean_results[name] = result

            return clean_results

        except Exception as e:
            return {"error": f"训练过程中发生错误: {str(e)}"}

    def predict_views(self, video_features):
        """预测播放量"""
        if self.best_model is None:
            return None

        try:
            df = pd.DataFrame([video_features])
            df = self.prepare_features(df)

            if hasattr(self, 'feature_cols'):
                feature_cols = self.feature_cols
            else:
                feature_cols = ['hour', 'day_of_week', 'month', 'title_length', 'title_word_count']
                if 'tname_encoded' in df.columns:
                    feature_cols.append('tname_encoded')
                if 'duration_minutes' in df.columns:
                    feature_cols.append('duration_minutes')

            available_cols = [col for col in feature_cols if col in df.columns]

            if len(available_cols) == 0:
                return None

            X = df[available_cols]
            X_scaled = self.scaler.transform(X)

            prediction = self.best_model.predict(X_scaled)[0]
            return max(0, int(prediction))
        except Exception as e:
            print(f"预测错误: {e}")
            return None

class UserClusteringAnalysis:
    """用户聚类分析"""

    def __init__(self, n_clusters=5):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.scaler = StandardScaler()
        self.cluster_labels = None
        self.cluster_centers = None

    def prepare_user_features(self, user_data, watch_history):
        """准备用户特征"""
        features = []

        total_watch_time = sum([item.get('duration', 0) for item in watch_history])
        avg_watch_time = total_watch_time / len(watch_history) if watch_history else 0

        categories = [item.get('tname', '其他') for item in watch_history]
        category_counts = pd.Series(categories).value_counts()

        hours = [datetime.fromtimestamp(item.get('view_at', 0)).hour for item in watch_history if item.get('view_at')]
        hour_counts = pd.Series(hours).value_counts()
        most_active_hour = hour_counts.index[0] if len(hour_counts) > 0 else 12

        total_likes = sum([item.get('like', 0) for item in watch_history])
        total_coins = sum([item.get('coin', 0) for item in watch_history])
        total_shares = sum([item.get('share', 0) for item in watch_history])

        features = {
            'total_videos': len(watch_history),
            'avg_watch_time': avg_watch_time,
            'total_watch_time': total_watch_time,
            'most_active_hour': most_active_hour,
            'total_likes': total_likes,
            'total_coins': total_coins,
            'total_shares': total_shares,
            'diversity_score': len(category_counts),
            'top_category_ratio': category_counts.iloc[0] / len(watch_history) if len(category_counts) > 0 else 0
        }

        return features

    def cluster_users(self, users_data):
        """对用户进行聚类"""
        if len(users_data) < self.n_clusters:
            return {"error": "用户数量不足，无法进行聚类分析"}

        feature_matrix = []
        for user in users_data:
            features = self.prepare_user_features(user.get('user_info', {}), user.get('watch_history', []))
            feature_matrix.append(list(features.values()))

        feature_matrix = np.array(feature_matrix)

        feature_matrix_scaled = self.scaler.fit_transform(feature_matrix)

        self.cluster_labels = self.kmeans.fit_predict(feature_matrix_scaled)
        self.cluster_centers = self.kmeans.cluster_centers_

        cluster_analysis = {}
        for i in range(self.n_clusters):
            cluster_users = [users_data[j] for j in range(len(users_data)) if self.cluster_labels[j] == i]

            if cluster_users:
                cluster_features = [
                    self.prepare_user_features(user.get('user_info', {}), user.get('watch_history', []))
                    for user in cluster_users
                ]

                cluster_df = pd.DataFrame(cluster_features)

                cluster_analysis[f'cluster_{i}'] = {
                    'user_count': len(cluster_users),
                    'avg_features': cluster_df.mean().to_dict(),
                    'description': self._describe_cluster(cluster_df.mean())
                }

        return cluster_analysis

    def _describe_cluster(self, avg_features):
        """描述聚类特征"""
        descriptions = []

        if avg_features['total_videos'] > 50:
            descriptions.append("重度用户")
        elif avg_features['total_videos'] > 20:
            descriptions.append("中度用户")
        else:
            descriptions.append("轻度用户")

        if avg_features['avg_watch_time'] > 600:
            descriptions.append("长视频偏好")
        else:
            descriptions.append("短视频偏好")

        if avg_features['diversity_score'] > 5:
            descriptions.append("兴趣广泛")
        else:
            descriptions.append("兴趣专一")

        if avg_features['most_active_hour'] >= 18 or avg_features['most_active_hour'] <= 6:
            descriptions.append("夜猫子")
        else:
            descriptions.append("白天活跃")

        return " | ".join(descriptions)

class SentimentAnalyzer:
    """情感分析器"""

    def __init__(self):
        pass

    def analyze_sentiment(self, text):
        """分析文本情感"""
        if not text or not isinstance(text, str):
            return {"sentiment": "neutral", "score": 0.0}

        try:
            s = snownlp.SnowNLP(text)
            sentiment_score = s.sentiments

            if sentiment_score > 0.6:
                sentiment = "positive"
            elif sentiment_score < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            return {
                "sentiment": sentiment,
                "score": sentiment_score,
                "confidence": abs(sentiment_score - 0.5) * 2
            }
        except:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity

                if polarity > 0.1:
                    sentiment = "positive"
                elif polarity < -0.1:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                return {
                    "sentiment": sentiment,
                    "score": (polarity + 1) / 2,
                    "confidence": abs(polarity)
                }
            except:
                return {"sentiment": "neutral", "score": 0.5}

    def analyze_batch_sentiment(self, texts):
        """批量情感分析"""
        results = []
        for text in texts:
            results.append(self.analyze_sentiment(text))
        return results

    def get_sentiment_summary(self, texts):
        """获取情感分析摘要"""
        results = self.analyze_batch_sentiment(texts)

        sentiments = [r['sentiment'] for r in results]
        scores = [r['score'] for r in results]

        sentiment_counts = pd.Series(sentiments).value_counts()

        return {
            "total_texts": len(texts),
            "sentiment_distribution": sentiment_counts.to_dict(),
            "average_score": np.mean(scores),
            "positive_ratio": sentiment_counts.get('positive', 0) / len(texts),
            "negative_ratio": sentiment_counts.get('negative', 0) / len(texts),
            "neutral_ratio": sentiment_counts.get('neutral', 0) / len(texts)
        }

class TrendPredictor:
    """趋势预测器"""

    def __init__(self):
        self.model = LinearRegression()

    def predict_trend(self, time_series_data, periods=7):
        """预测未来趋势"""
        if len(time_series_data) < 3:
            return []

        df = pd.DataFrame(time_series_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        df['time_numeric'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()

        X = df[['time_numeric']].values
        y = df['value'].values

        self.model.fit(X, y)

        last_time = df['time_numeric'].max()
        time_step = (df['time_numeric'].iloc[-1] - df['time_numeric'].iloc[-2]) if len(df) > 1 else 86400

        predictions = []
        for i in range(1, periods + 1):
            future_time = last_time + (time_step * i)
            pred_value = self.model.predict([[future_time]])[0]

            future_timestamp = df['timestamp'].max() + timedelta(seconds=time_step * i)

            predictions.append({
                'timestamp': future_timestamp.isoformat(),
                'predicted_value': max(0, pred_value),
                'confidence': 0.8 - (i * 0.1)
            })

        return predictions

class MLService:
    """机器学习服务"""

    def __init__(self):
        self.recommendation_system = VideoRecommendationSystem()
        self.view_predictor = ViewPredictionModel()
        self.user_clustering = UserClusteringAnalysis()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.trend_predictor = TrendPredictor()

    def get_video_recommendations(self, user_history=None, video_bvid=None, videos_df=None, top_n=10):
        """获取视频推荐"""
        if videos_df is None or len(videos_df) == 0:
            return []

        self.recommendation_system.prepare_content_features(videos_df)

        if video_bvid:
            return self.recommendation_system.get_content_based_recommendations(video_bvid, top_n)
        elif user_history:
            return self.recommendation_system.get_collaborative_filtering_recommendations(
                user_history, videos_df, top_n
            )
        else:
            return self.recommendation_system.get_popular_recommendations(videos_df, top_n)

    def train_view_prediction_model(self, videos_df):
        """训练播放量预测模型"""
        return self.view_predictor.train_models(videos_df)

    def predict_video_views(self, video_features):
        """预测视频播放量"""
        return self.view_predictor.predict_views(video_features)

    def analyze_user_clusters(self, users_data):
        """用户聚类分析"""
        return self.user_clustering.cluster_users(users_data)

    def analyze_sentiment(self, texts):
        """情感分析"""
        return self.sentiment_analyzer.get_sentiment_summary(texts)

    def predict_trends(self, time_series_data, periods=7):
        """趋势预测"""
        return self.trend_predictor.predict_trend(time_series_data, periods)

    def get_user_based_recommendations(self, target_user_id, users_data, videos_df, top_n=10):
        """基于用户相似度的推荐"""
        if not users_data or videos_df is None or len(videos_df) == 0:
            return []

        return self.recommendation_system.get_user_collaborative_recommendations(
            target_user_id, users_data, videos_df, top_n
        )

    def find_similar_users(self, target_user_id, users_data, top_n=5):
        """找到相似用户"""
        if not users_data:
            return []

        return self.recommendation_system.find_similar_users(target_user_id, users_data, top_n) 