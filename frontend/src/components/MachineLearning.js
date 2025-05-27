import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Button, 
  Input, 
  Select, 
  Table, 
  Progress,
  Typography,
  Space,
  Alert,
  Spin,
  Form,
  Tag,
  Divider,
  Statistic,
  message
} from 'antd';
import { 
  RobotOutlined,
  BulbOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  LikeOutlined,
  ShareAltOutlined,
  GiftOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { useAuth } from './Auth';
import './MachineLearning.css';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

// API配置
const API_BASE_URL = 'http://localhost:8000';

const MachineLearning = () => {
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [userBasedRecommendations, setUserBasedRecommendations] = useState([]);
  const { token, isAuthenticated } = useAuth();

  // 获取视频推荐
  const getRecommendations = async (userMid = null, videoBvid = null) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (userMid) params.append('user_mid', userMid);
      if (videoBvid) params.append('video_bvid', videoBvid);
      params.append('limit', '10');

      const response = await axios.get(`${API_BASE_URL}/api/ml/recommendations?${params}`);
      setRecommendations(response.data.recommendations);
      message.success(`获取到 ${response.data.total_count} 个推荐视频`);
    } catch (error) {
      message.error('获取推荐失败: ' + error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  // 获取基于用户的推荐
  const getUserBasedRecommendations = async () => {
    if (!isAuthenticated) {
      message.warning('请先登录以获取个性化推荐');
      return;
    }
    
    setLoading(true);
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const response = await axios.get(`${API_BASE_URL}/api/ml/user-based-recommendations`, { headers });
      setUserBasedRecommendations(response.data.recommendations);
      message.success(`获取到 ${response.data.recommendations?.length || 0} 个用户推荐`);
    } catch (error) {
      if (error.response?.status === 401) {
        message.error('登录已过期，请重新登录');
      } else {
        message.error('获取用户推荐失败: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  // 智能推荐系统组件
  const RecommendationSystem = () => {
    const [videos, setVideos] = useState([]);
    const [form] = Form.useForm();

    const fetchVideos = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/videos?limit=20`);
        // 处理不同的响应格式
        let videoData = response.data;
        if (response.data.data) {
          videoData = response.data.data;
        }
        
        const videoList = videoData.slice(0, 20).map(video => ({
          bvid: video.bvid,
          title: video.title,
          view: video.view,
          like: video.like
        }));
        setVideos(videoList);
      } catch (error) {
        console.error('获取视频列表失败:', error);
      }
    };

    const onFinish = (values) => {
      getRecommendations(values.user_mid, values.video_bvid);
    };

    useEffect(() => {
      fetchVideos();
    }, []);

    const recommendationColumns = [
      {
        title: '视频信息',
        dataIndex: 'title',
        key: 'title',
        width: '40%',
        render: (text, record) => (
          <div>
            <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{text}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              BV号: {record.bvid}
            </div>
          </div>
        ),
      },
      {
        title: '数据表现',
        key: 'stats',
        width: '35%',
        render: (_, record) => (
          <Space direction="vertical" size="small">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <EyeOutlined style={{ color: '#1890ff' }} />
              <span>{(record.view || 0).toLocaleString()} 播放</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <LikeOutlined style={{ color: '#f5222d' }} />
              <span>{(record.like || 0).toLocaleString()} 点赞</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <ShareAltOutlined style={{ color: '#52c41a' }} />
              <span>{(record.share || 0).toLocaleString()} 分享</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <GiftOutlined style={{ color: '#faad14' }} />
              <span>{(record.coin || 0).toLocaleString()} 投币</span>
            </div>
          </Space>
        ),
      },
      {
        title: '推荐分数',
        key: 'score',
        width: '25%',
        render: (_, record) => {
          // 获取推荐分数，支持多种字段名
          let score = record.score || record.popularity_score || record.final_score || record.similarity_score || record.recommendation_score || 0;
          
          // 如果分数是负数（协同过滤可能产生），转换为正数并标准化
          if (score < 0) {
            score = Math.abs(score);
          }
          
          // 如果分数大于1，说明不是0-1范围，需要标准化
          if (score > 1) {
            score = Math.min(score / 10, 1); // 简单标准化
          }
          
          const percentage = Math.round(score * 100);
          
          return (
            <div>
              <Progress 
                percent={percentage} 
                size="small" 
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
              <Text style={{ fontSize: '12px', color: '#666' }}>
                匹配度: {percentage}%
              </Text>
            </div>
          );
        },
      },
    ];

    return (
      <Card title="智能推荐系统" icon={<BulbOutlined />}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="智能推荐说明"
            description="基于协同过滤算法，为用户推荐可能感兴趣的视频内容。支持基于用户历史行为和视频相似度的推荐。"
            type="info"
            showIcon
          />

          <Card size="small" title="推荐参数设置">
            <Form form={form} onFinish={onFinish} layout="inline">
              <Form.Item name="user_mid" label="用户ID">
                <Input placeholder="输入用户ID（可选）" style={{ width: 200 }} />
              </Form.Item>
              
              <Form.Item name="video_bvid" label="参考视频">
                <Select 
                  placeholder="选择参考视频（可选）" 
                  style={{ width: 300 }}
                  showSearch
                  optionFilterProp="children"
                  allowClear
                >
                  {videos.map(video => (
                    <Option key={video.bvid} value={video.bvid}>
                      {video.title.length > 30 ? video.title.substring(0, 30) + '...' : video.title}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<BulbOutlined />}>
                  获取推荐
                </Button>
              </Form.Item>
            </Form>
          </Card>

          <Row gutter={16}>
            <Col span={12}>
              <Button 
                type="default" 
                onClick={getUserBasedRecommendations} 
                loading={loading}
                block
                icon={<RobotOutlined />}
              >
                获取用户协同推荐
              </Button>
            </Col>
            <Col span={12}>
              <Button 
                type="default" 
                onClick={() => getRecommendations()} 
                loading={loading}
                block
                icon={<PlayCircleOutlined />}
              >
                获取热门推荐
              </Button>
            </Col>
          </Row>

          {recommendations.length > 0 && (
            <Card size="small" title={`推荐结果 (${recommendations.length}个)`}>
              <Table
                columns={recommendationColumns}
                dataSource={recommendations}
                rowKey="bvid"
                pagination={{ pageSize: 5, showSizeChanger: false }}
                size="small"
              />
            </Card>
          )}

          {userBasedRecommendations.length > 0 && (
            <Card size="small" title={`用户协同推荐 (${userBasedRecommendations.length}个)`}>
              <Table
                columns={recommendationColumns}
                dataSource={userBasedRecommendations}
                rowKey="bvid"
                pagination={{ pageSize: 5, showSizeChanger: false }}
                size="small"
              />
            </Card>
          )}

          {(recommendations.length > 0 || userBasedRecommendations.length > 0) && (
            <Alert
              message="推荐算法说明"
              description={
                <div>
                  <p><strong>协同过滤:</strong> 基于用户行为相似度进行推荐</p>
                  <p><strong>内容推荐:</strong> 基于视频特征相似度进行推荐</p>
                  <p><strong>推荐分数:</strong> 综合考虑用户偏好、视频质量、热度等因素</p>
                </div>
              }
              type="success"
              showIcon
            />
          )}
        </Space>
      </Card>
    );
  };

  return (
    <div className="machine-learning">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <RobotOutlined style={{ marginRight: 8 }} />
          智能推荐系统
        </Title>
        <Paragraph>
          基于先进的机器学习算法，为用户提供个性化的视频推荐服务。
        </Paragraph>
      </div>

      <RecommendationSystem />
    </div>
  );
};

export default MachineLearning; 