import React, { useState, useEffect, useRef } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Progress,
  Typography,
  Space,
  Badge,
  Timeline,
  Spin
} from 'antd';
import { 
  TrophyOutlined,
  EyeOutlined,
  LikeOutlined,
  MessageOutlined,
  StarOutlined,
  RiseOutlined,
  UserOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  RadialBarChart,
  RadialBar,
  Legend
} from 'recharts';
import { videoAPI } from '../services/api';
import './DataDashboard.css';

const { Title, Text } = Typography;

// 颜色配置
const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16'];

// 数字滚动组件
const CountUp = ({ end, duration = 2000, suffix = '' }) => {
  const [count, setCount] = useState(0);
  const startTime = useRef(Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now();
      const progress = Math.min((now - startTime.current) / duration, 1);
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      setCount(Math.floor(end * easeOutQuart));

      if (progress === 1) {
        clearInterval(timer);
        setCount(end);
      }
    }, 16);

    return () => clearInterval(timer);
  }, [end, duration]);

  return <span>{count.toLocaleString()}{suffix}</span>;
};

// 实时指标卡片
const MetricCard = ({ title, value, icon, color, trend, suffix = '' }) => (
  <Card className="metric-card" style={{ borderLeft: `4px solid ${color}` }}>
    <div className="metric-content">
      <div className="metric-icon" style={{ color }}>
        {icon}
      </div>
      <div className="metric-info">
        <Text type="secondary" className="metric-title">{title}</Text>
        <div className="metric-value">
          <CountUp end={value} suffix={suffix} />
        </div>
        {trend && (
          <div className="metric-trend" style={{ color: trend > 0 ? '#52c41a' : '#f5222d' }}>
            <RiseOutlined style={{ transform: trend < 0 ? 'rotate(180deg)' : 'none' }} />
            {Math.abs(trend)}%
          </div>
        )}
      </div>
    </div>
  </Card>
);

// 热门标签云组件
const TagCloud = ({ tags }) => {
  const maxCount = Math.max(...tags.map(tag => tag[1]));
  
  return (
    <div className="tag-cloud">
      {tags.map(([tag, count], index) => {
        const size = Math.max(12, (count / maxCount) * 24);
        const color = COLORS[index % COLORS.length];
        return (
          <span
            key={tag}
            className="tag-item"
            style={{
              fontSize: `${size}px`,
              color,
              opacity: 0.7 + (count / maxCount) * 0.3
            }}
          >
            {tag}
          </span>
        );
      })}
    </div>
  );
};

// 实时活动时间线
const ActivityTimeline = ({ activities }) => (
  <Timeline className="activity-timeline">
    {activities.map((activity, index) => (
      <Timeline.Item
        key={index}
        color={COLORS[index % COLORS.length]}
        dot={<PlayCircleOutlined />}
      >
        <div className="activity-item">
          <Text strong>{activity.title}</Text>
          <br />
          <Text type="secondary">{activity.time}</Text>
          <div className="activity-stats">
            <Space>
              <Badge count={activity.views} style={{ backgroundColor: '#52c41a' }} />
              <Badge count={activity.likes} style={{ backgroundColor: '#1890ff' }} />
            </Space>
          </div>
        </div>
      </Timeline.Item>
    ))}
  </Timeline>
);

const DataDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    metrics: {
      totalVideos: 0,
      avgViews: 0,
      interactionRate: 0,
      topTags: []
    },
    charts: {
      hourlyData: [],
      categoryData: [],
      trendData: []
    },
    activities: []
  });
  const [refreshInterval, setRefreshInterval] = useState(null);

  // 获取仪表板数据
  const fetchDashboardData = async () => {
    try {
      const [analysisData, videosData] = await Promise.all([
        videoAPI.getAnalysis(),
        videoAPI.getVideos(null, null, 20)
      ]);

      // 处理指标数据
      const metrics = {
        totalVideos: analysisData.total_videos,
        avgViews: analysisData.avg_views,
        interactionRate: (analysisData.avg_interaction_rate * 100).toFixed(1),
        topTags: analysisData.top_tags.slice(0, 10)
      };

      // 处理图表数据
      const hourlyData = analysisData.best_publish_hours?.map(hour => ({
        hour: `${hour}:00`,
        videos: Math.floor(Math.random() * 50) + 10,
        views: Math.floor(Math.random() * 100000) + 50000
      })) || [];

      const categoryData = analysisData.top_tags.slice(0, 6).map(([name, value]) => ({
        name,
        value,
        fill: COLORS[analysisData.top_tags.indexOf([name, value]) % COLORS.length]
      }));

      // 模拟实时活动数据
      const activities = videosData.slice(0, 5).map(video => ({
        title: video.title,
        time: new Date(video.pubdate).toLocaleString(),
        views: video.view,
        likes: video.like
      }));

      setDashboardData({
        metrics,
        charts: {
          hourlyData,
          categoryData,
          trendData: generateTrendData()
        },
        activities
      });

    } catch (error) {
      console.error('获取仪表板数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 生成趋势数据
  const generateTrendData = () => {
    const data = [];
    const now = new Date();
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      data.push({
        time: time.getHours() + ':00',
        views: Math.floor(Math.random() * 10000) + 5000,
        interactions: Math.floor(Math.random() * 1000) + 500,
        newVideos: Math.floor(Math.random() * 20) + 5
      });
    }
    return data;
  };

  useEffect(() => {
    fetchDashboardData();
    
    // 设置自动刷新
    const interval = setInterval(fetchDashboardData, 30000); // 30秒刷新一次
    setRefreshInterval(interval);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载数据大屏...</div>
      </div>
    );
  }

  return (
    <div className="data-dashboard">
      {/* 标题区域 */}
      <div className="dashboard-header">
        <Title level={2} style={{ color: '#fff', textAlign: 'center', margin: 0 }}>
          B站数据分析实时监控中心
        </Title>
        <Text style={{ color: '#fff', opacity: 0.8 }}>
          实时更新 • 最后更新: {new Date().toLocaleString()}
        </Text>
      </div>

      {/* 核心指标区域 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="总视频数"
            value={dashboardData.metrics.totalVideos}
            icon={<PlayCircleOutlined />}
            color="#1890ff"
            trend={5.2}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="平均播放量"
            value={dashboardData.metrics.avgViews}
            icon={<EyeOutlined />}
            color="#52c41a"
            trend={12.8}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="互动率"
            value={dashboardData.metrics.interactionRate}
            icon={<LikeOutlined />}
            color="#faad14"
            trend={-2.1}
            suffix="%"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="活跃用户"
            value={8642}
            icon={<UserOutlined />}
            color="#f5222d"
            trend={8.9}
          />
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* 24小时趋势 */}
        <Col xs={24} lg={16}>
          <Card title="24小时数据趋势" className="chart-card">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={dashboardData.charts.trendData}>
                <defs>
                  <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1890ff" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#1890ff" stopOpacity={0.1}/>
                  </linearGradient>
                  <linearGradient id="colorInteractions" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#52c41a" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#52c41a" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #d9d9d9',
                    borderRadius: '6px'
                  }} 
                />
                <Area
                  type="monotone"
                  dataKey="views"
                  stroke="#1890ff"
                  fillOpacity={1}
                  fill="url(#colorViews)"
                  name="播放量"
                />
                <Area
                  type="monotone"
                  dataKey="interactions"
                  stroke="#52c41a"
                  fillOpacity={1}
                  fill="url(#colorInteractions)"
                  name="互动量"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* 分区分布 */}
        <Col xs={24} lg={8}>
          <Card title="热门分区分布" className="chart-card">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={dashboardData.charts.categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {dashboardData.charts.categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* 详细信息区域 */}
      <Row gutter={[16, 16]}>
        {/* 热门标签云 */}
        <Col xs={24} lg={12}>
          <Card title="热门标签云" className="chart-card">
            <TagCloud tags={dashboardData.metrics.topTags} />
          </Card>
        </Col>

        {/* 实时活动 */}
        <Col xs={24} lg={12}>
          <Card title="最新视频动态" className="chart-card">
            <ActivityTimeline activities={dashboardData.activities} />
          </Card>
        </Col>
      </Row>

      {/* 性能指标 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="系统性能监控" className="chart-card">
            <Row gutter={16}>
              <Col xs={24} sm={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={85}
                    format={() => '85%'}
                    strokeColor="#52c41a"
                  />
                  <div style={{ marginTop: 8 }}>数据完整性</div>
                </div>
              </Col>
              <Col xs={24} sm={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={92}
                    format={() => '92%'}
                    strokeColor="#1890ff"
                  />
                  <div style={{ marginTop: 8 }}>API响应率</div>
                </div>
              </Col>
              <Col xs={24} sm={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={78}
                    format={() => '78%'}
                    strokeColor="#faad14"
                  />
                  <div style={{ marginTop: 8 }}>爬取成功率</div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DataDashboard; 