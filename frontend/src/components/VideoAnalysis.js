import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Statistic, 
  Row, 
  Col, 
  Table, 
  message, 
  Spin, 
  Tag, 
  Image, 
  Typography,
  Space,
  Progress,
  Avatar,
  Tooltip,
  Badge,
  Divider
} from 'antd';
import { 
  ReloadOutlined, 
  BarChartOutlined, 
  PlayCircleOutlined,
  EyeOutlined,
  LikeOutlined,
  ShareAltOutlined,
  MessageOutlined,
  StarOutlined,
  TrophyOutlined,
  FireOutlined,
  ClockCircleOutlined,
  UserOutlined,
  TagOutlined,
  RiseOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { videoAPI } from '../services/api';
import moment from 'moment';
import './VideoAnalysis.css';

const { Title, Text, Paragraph } = Typography;

const VideoAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [crawling, setCrawling] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [videos, setVideos] = useState([]);
  const [chartUrl, setChartUrl] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
    totalPages: 0
  });

  // 获取分析数据
  const fetchAnalysis = async () => {
    setLoading(true);
    try {
      const data = await videoAPI.getAnalysis();
      setAnalysis(data);
      setChartUrl(videoAPI.getChart());
      message.success('分析数据获取成功');
    } catch (error) {
      if (error.response?.status === 404) {
        message.warning('暂无数据，请先爬取热门视频');
      } else {
        message.error('获取分析数据失败: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  // 获取视频列表（支持分页）
  const fetchVideos = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await videoAPI.getVideos(page, pageSize);
      
      // 检查响应格式
      if (response.data && response.pagination) {
        // 新的分页格式
        setVideos(response.data);
        setPagination(response.pagination);
      } else {
        // 旧的格式（向后兼容）
        setVideos(response);
        setPagination({
          current: 1,
          pageSize: response.length,
          total: response.length,
          totalPages: 1
        });
      }
    } catch (error) {
      console.error('获取视频列表失败:', error);
      message.error('获取视频列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理分页变化
  const handleTableChange = (page, pageSize) => {
    fetchVideos(page, pageSize);
  };

  // 处理分页大小变化
  const handleShowSizeChange = (current, size) => {
    fetchVideos(1, size); // 改变页面大小时回到第一页
  };

  // 手动爬取
  const handleCrawl = async () => {
    setCrawling(true);
    try {
      await videoAPI.crawlPopular();
      message.success('爬取任务已启动，请稍后查看结果');
      // 延迟获取数据
      setTimeout(() => {
        fetchAnalysis();
        fetchVideos(1, 10); // 重置到第一页，每页10条
      }, 5000);
    } catch (error) {
      message.error('启动爬取失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setCrawling(false);
    }
  };

  // 强制刷新整个组件
  const forceRefresh = () => {
    setRefreshKey(prev => prev + 1);
    setVideos([]);
    setPagination({
      current: 1,
      pageSize: 10,
      total: 0,
      totalPages: 0
    });
    fetchAnalysis();
    fetchVideos(1, 10);
  };

  useEffect(() => {
    fetchAnalysis();
    fetchVideos(1, 10); // 明确指定第一页，每页10条
  }, []);

  // 视频表格列定义
  const videoColumns = [
    {
      title: '视频信息',
      key: 'info',
      width: 400,
      render: (_, record) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Avatar 
            size={48} 
            icon={<PlayCircleOutlined />} 
            style={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              marginRight: 12,
              flexShrink: 0
            }}
          />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ 
              fontWeight: 600, 
              fontSize: '14px',
              marginBottom: 4,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {record.title}
            </div>
            <Space size={8}>
              <Tag 
                color="green" 
                style={{ 
                  fontFamily: 'monospace', 
                  fontSize: '11px',
                  margin: 0
                }}
              >
                {record.bvid}
              </Tag>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                <UserOutlined style={{ marginRight: 4 }} />
                {record.author}
              </Text>
            </Space>
          </div>
        </div>
      ),
    },
    {
      title: '数据表现',
      key: 'performance',
      width: 400,
      render: (_, record) => (
        <div style={{ padding: '8px' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '6px',
            flexWrap: 'wrap'
          }}>
            <div style={{ 
              display: 'inline-flex',
              alignItems: 'center',
              padding: '4px 8px',
              borderRadius: '12px',
              border: '1px solid #91d5ff',
              background: 'linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%)',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
              textAlign: 'center',
              justifyContent: 'center',
              flex: '1 1 auto', 
              minWidth: '70px'
            }}>
              <EyeOutlined style={{ color: '#1890ff', marginRight: 4, fontSize: '12px' }} />
              <div>
                <div style={{ 
                  color: '#1890ff', 
                  fontWeight: 600,
                  fontSize: '13px',
                  lineHeight: 1
                }}>
                  {record.view ? (record.view / 10000).toFixed(1) + '万' : '0'}
                </div>
                <div style={{ fontSize: '9px', color: '#666', lineHeight: 1, marginTop: '1px' }}>
                  播放
                </div>
              </div>
            </div>

            <div style={{ 
              display: 'inline-flex',
              alignItems: 'center',
              padding: '4px 8px',
              borderRadius: '12px',
              border: '1px solid #ffbb96',
              background: 'linear-gradient(135deg, #fff2e8 0%, #fff7f0 100%)',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
              textAlign: 'center',
              justifyContent: 'center',
              flex: '1 1 auto', 
              minWidth: '70px'
            }}>
              <LikeOutlined style={{ color: '#f5222d', marginRight: 4, fontSize: '12px' }} />
              <div>
                <div style={{ 
                  color: '#f5222d', 
                  fontWeight: 600,
                  fontSize: '13px',
                  lineHeight: 1
                }}>
                  {record.like ? (record.like / 10000).toFixed(1) + '万' : '0'}
                </div>
                <div style={{ fontSize: '9px', color: '#666', lineHeight: 1, marginTop: '1px' }}>
                  点赞
                </div>
              </div>
            </div>

            <div style={{ 
              display: 'inline-flex',
              alignItems: 'center',
              padding: '4px 8px',
              borderRadius: '12px',
              border: '1px solid #ffe58f',
              background: 'linear-gradient(135deg, #fffbe6 0%, #fffef0 100%)',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
              textAlign: 'center',
              justifyContent: 'center',
              flex: '1 1 auto', 
              minWidth: '60px'
            }}>
              <MessageOutlined style={{ color: '#faad14', marginRight: 4, fontSize: '12px' }} />
              <div>
                <div style={{ 
                  color: '#faad14', 
                  fontWeight: 600,
                  fontSize: '13px',
                  lineHeight: 1
                }}>
                  {record.coin || 0}
                </div>
                <div style={{ fontSize: '9px', color: '#666', lineHeight: 1, marginTop: '1px' }}>
                  投币
                </div>
              </div>
            </div>

            <div style={{ 
              display: 'inline-flex',
              alignItems: 'center',
              padding: '4px 8px',
              borderRadius: '12px',
              border: '1px solid #b7eb8f',
              background: 'linear-gradient(135deg, #f6ffed 0%, #fcffe6 100%)',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
              textAlign: 'center',
              justifyContent: 'center',
              flex: '1 1 auto', 
              minWidth: '60px'
            }}>
              <ShareAltOutlined style={{ color: '#52c41a', marginRight: 4, fontSize: '12px' }} />
              <div>
                <div style={{ 
                  color: '#52c41a', 
                  fontWeight: 600,
                  fontSize: '13px',
                  lineHeight: 1
                }}>
                  {record.share || 0}
                </div>
                <div style={{ fontSize: '9px', color: '#666', lineHeight: 1, marginTop: '1px' }}>
                  分享
                </div>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      title: '分区时间',
      key: 'category',
      width: 180,
      render: (_, record) => (
        <Space direction="vertical" size={4}>
          <Tag 
            color="blue" 
            style={{ 
              borderRadius: '12px',
              padding: '2px 8px',
              fontSize: '12px'
            }}
          >
            <TagOutlined style={{ marginRight: 4 }} />
            {record.tname}
          </Tag>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            <ClockCircleOutlined style={{ marginRight: 4 }} />
            {record.pubdate ? moment(record.pubdate).format('MM-DD HH:mm') : '-'}
          </Text>
        </Space>
      ),
    },
  ];

  // 统计卡片组件
  const StatCard = ({ title, value, icon, color, suffix = '', formatter, trend }) => (
    <Card 
      className="stat-card"
      style={{
        background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
        border: `1px solid ${color}30`,
        borderRadius: '16px',
        overflow: 'hidden'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <Text type="secondary" style={{ fontSize: '14px', display: 'block', marginBottom: 8 }}>
            {title}
          </Text>
          <div style={{ fontSize: '24px', fontWeight: 700, color: color, marginBottom: 4 }}>
            {formatter ? formatter(value) : value}{suffix}
          </div>
          {trend && (
            <Text style={{ fontSize: '12px', color: trend > 0 ? '#52c41a' : '#f5222d' }}>
              <RiseOutlined style={{ marginRight: 4 }} />
              {trend > 0 ? '+' : ''}{trend}%
            </Text>
          )}
        </div>
        <div 
          style={{ 
            fontSize: '32px', 
            color: color,
            opacity: 0.8,
            background: `${color}20`,
            borderRadius: '50%',
            width: 64,
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {icon}
        </div>
      </div>
    </Card>
  );

  return (
    <div className="video-analysis">
      {/* 页面头部 */}
      <div className="page-header">
        <div className="header-content">
          <div className="header-left">
            <div className="header-icon">
              <FireOutlined />
            </div>
            <div>
              <Title level={2} style={{ margin: 0, color: '#fff' }}>
                热门视频分析
              </Title>
              <Paragraph style={{ margin: 0, color: 'rgba(255,255,255,0.8)' }}>
                实时分析B站热门视频数据，洞察内容趋势
              </Paragraph>
            </div>
          </div>
          <div className="header-actions">
            <Space size={12}>
              <Button 
                type="primary" 
                size="large"
                icon={<PlayCircleOutlined />}
                loading={crawling}
                onClick={handleCrawl}
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  height: '44px',
                  padding: '0 24px'
                }}
              >
                {crawling ? '爬取中...' : '开始爬取'}
              </Button>
              <Button 
                size="large"
                icon={<ReloadOutlined />}
                loading={loading}
                onClick={forceRefresh}
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  color: '#fff',
                  borderRadius: '8px',
                  height: '44px'
                }}
              >
                刷新数据
              </Button>
            </Space>
          </div>
        </div>
      </div>

      <div className="page-content">
        <Row gutter={[24, 24]}>
          {/* 统计数据卡片 */}
          {analysis && (
            <>
              <Col xs={24} sm={12} lg={6}>
                <StatCard
                  title="视频总数"
                  value={analysis.total_videos}
                  icon={<PlayCircleOutlined />}
                  color="#1890ff"
                  suffix="个"
                  trend={8.5}
                />
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <StatCard
                  title="平均播放量"
                  value={analysis.avg_views}
                  icon={<EyeOutlined />}
                  color="#52c41a"
                  formatter={(value) => `${(value / 10000).toFixed(1)}万`}
                  trend={12.3}
                />
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <StatCard
                  title="平均互动率"
                  value={(analysis.avg_interaction_rate * 100).toFixed(2)}
                  icon={<LikeOutlined />}
                  color="#faad14"
                  suffix="%"
                  trend={-2.1}
                />
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <StatCard
                  title="最佳发布时间"
                  value={analysis.best_publish_hours ? analysis.best_publish_hours.join(', ') + '点' : '暂无'}
                  icon={<ClockCircleOutlined />}
                  color="#722ed1"
                />
              </Col>
            </>
          )}

          {/* 热门标签和图表 */}
          <Col xs={24} lg={12}>
            <Card 
              className="content-card"
              title={
                <Space>
                  <TrophyOutlined style={{ color: '#faad14' }} />
                  <span>热门标签</span>
                  <Badge count={analysis?.top_tags?.length || 0} style={{ backgroundColor: '#52c41a' }} />
                </Space>
              }
              extra={<ThunderboltOutlined style={{ color: '#1890ff' }} />}
            >
              {analysis && analysis.top_tags ? (
                <div className="tags-container">
                  {analysis.top_tags.map(([tag, count], index) => (
                    <Tag 
                      key={tag} 
                      className={`trending-tag ${index < 3 ? 'top-tag' : ''}`}
                      style={{
                        background: index < 3 
                          ? 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)'
                          : 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '20px',
                        padding: '6px 16px',
                        margin: '6px',
                        fontSize: '13px',
                        fontWeight: 500,
                        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                      }}
                    >
                      {index < 3 && <TrophyOutlined style={{ marginRight: 4 }} />}
                      {tag} ({count})
                    </Tag>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                  <TagOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                  <div>暂无标签数据</div>
                </div>
              )}
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card 
              className="content-card"
              title={
                <Space>
                  <BarChartOutlined style={{ color: '#52c41a' }} />
                  <span>数据分析图表</span>
                </Space>
              }
              extra={<Button type="link" size="small">查看详情</Button>}
            >
              {chartUrl ? (
                <div className="chart-container">
                  <Image
                    src={chartUrl}
                    alt="分析图表"
                    style={{ 
                      width: '100%', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                    }}
                    preview={{
                      mask: (
                        <div style={{ color: '#fff', textAlign: 'center' }}>
                          <EyeOutlined style={{ fontSize: '20px', marginBottom: '8px', display: 'block' }} />
                          点击查看大图
                        </div>
                      )
                    }}
                  />
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                  <BarChartOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                  <div>暂无图表数据</div>
                </div>
              )}
            </Card>
          </Col>

          {/* 视频列表 */}
          <Col span={24}>
            <Card 
              className="content-card"
              title={
                <Space>
                  <PlayCircleOutlined style={{ color: '#1890ff' }} />
                  <span>热门视频列表</span>
                  <Badge count={pagination.total} style={{ backgroundColor: '#1890ff' }} />
                </Space>
              }
              extra={
                <Space>
                  <Text type="secondary">
                    共 {pagination.total} 个视频，当前第 {pagination.current} 页
                  </Text>
                  <Divider type="vertical" />
                  <Button type="link" size="small" onClick={forceRefresh}>
                    <ReloadOutlined />
                  </Button>
                </Space>
              }
            >
              <Spin spinning={loading}>
                <Table
                  key={refreshKey}
                  columns={videoColumns}
                  dataSource={videos}
                  rowKey="bvid"
                  pagination={{
                    current: pagination.current,
                    pageSize: pagination.pageSize,
                    total: pagination.total,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => 
                      `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
                    onChange: handleTableChange,
                    onShowSizeChange: handleShowSizeChange,
                    pageSizeOptions: ['10', '20', '50', '100']
                  }}
                  scroll={{ x: 1000 }}
                  className="modern-table"
                  rowClassName={(record, index) => index % 2 === 0 ? 'table-row-light' : 'table-row-dark'}
                />
              </Spin>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default VideoAnalysis; 