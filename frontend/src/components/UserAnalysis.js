import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Input, 
  Row, 
  Col, 
  Table, 
  message, 
  Spin, 
  Tag, 
  Statistic,
  Modal,
  Descriptions,
  Progress,
  Alert
} from 'antd';
import { 
  UserOutlined, 
  HistoryOutlined, 
  HeartOutlined, 
  BarChartOutlined,
  ReloadOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { userAPI } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import moment from 'moment';

const { TextArea } = Input;

// 图表颜色配置
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#FF7C7C'];

const UserAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [history, setHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [customCookie, setCustomCookie] = useState('');
  const [cookieModalVisible, setCookieModalVisible] = useState(false);
  const [currentCookie, setCurrentCookie] = useState(null);

  // 获取用户信息
  const fetchUserInfo = async (cookie = null) => {
    setLoading(true);
    try {
      const data = await userAPI.getUserInfo(cookie);
      setUserInfo(data);
      setCurrentCookie(cookie);
      message.success('用户信息获取成功');
      return data;
    } catch (error) {
      if (error.response?.status === 401) {
        const errorDetail = error.response?.data?.detail || 'Cookie已过期或无效';
        // 显示详细的错误信息
        Modal.error({
          title: 'Cookie验证失败',
          content: (
            <div>
              <p>{errorDetail}</p>
              <p style={{ marginTop: 16 }}>
                <Button type="primary" onClick={() => setCookieModalVisible(true)}>
                  设置新Cookie
                </Button>
              </p>
            </div>
          ),
          width: 500,
        });
      } else {
        message.error('获取用户信息失败: ' + (error.response?.data?.detail || error.message));
      }
      return null;
    } finally {
      setLoading(false);
    }
  };

  // 获取观看历史
  const fetchHistory = async (cookie = null) => {
    setLoading(true);
    try {
      const data = await userAPI.getHistory(cookie);
      setHistory(data.history || []);
      if (!userInfo) {
        setUserInfo(data.user_info);
      }
      message.success(`获取到 ${data.total_count} 条观看记录`);
    } catch (error) {
      if (error.response?.status === 401) {
        message.error('Cookie已过期或无效');
      } else {
        message.error('获取观看历史失败: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  // 获取收藏
  const fetchFavorites = async (cookie = null) => {
    setLoading(true);
    try {
      const data = await userAPI.getFavorites(cookie);
      setFavorites(data.favorites || []);
      if (!userInfo) {
        setUserInfo(data.user_info);
      }
      message.success(`获取到 ${data.folder_count} 个收藏夹，共 ${data.total_resources} 个收藏`);
    } catch (error) {
      if (error.response?.status === 401) {
        message.error('Cookie已过期或无效');
      } else {
        message.error('获取收藏失败: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  // 获取用户分析
  const fetchUserAnalysis = async (userMid) => {
    try {
      const data = await userAPI.getUserAnalysis(userMid);
      setAnalysis(data);
      message.success('用户分析数据获取成功');
    } catch (error) {
      if (error.response?.status === 404) {
        message.warning('暂无用户分析数据');
      } else {
        message.error('获取用户分析失败: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  // 使用默认Cookie初始化
  useEffect(() => {
    fetchUserInfo();
  }, []);

  // 使用自定义Cookie
  const handleCustomCookie = async () => {
    if (!customCookie.trim()) {
      message.warning('请输入Cookie');
      return;
    }
    
    const user = await fetchUserInfo(customCookie);
    if (user) {
      setCookieModalVisible(false);
      setCustomCookie('');
    }
  };

  // 获取所有数据
  const fetchAllData = async () => {
    if (!userInfo) {
      message.warning('请先获取用户信息');
      return;
    }

    await Promise.all([
      fetchHistory(currentCookie),
      fetchFavorites(currentCookie)
    ]);

    // 获取分析数据
    await fetchUserAnalysis(userInfo.mid);
  };

  // 历史记录表格列
  const historyColumns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'UP主',
      dataIndex: 'owner',
      key: 'owner',
      width: 120,
      render: (owner) => owner?.name || '-',
    },
    {
      title: '分区',
      dataIndex: 'tname',
      key: 'tname',
      width: 100,
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '观看时间',
      dataIndex: 'view_at',
      key: 'view_at',
      width: 150,
      render: (timestamp) => moment.unix(timestamp).format('YYYY-MM-DD HH:mm'),
    },
  ];

  // 收藏夹展开内容
  const expandedRowRender = (folder) => {
    const columns = [
      { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
      { title: 'UP主', dataIndex: 'upper', key: 'upper', render: (upper) => upper?.name || '-' },
      { title: '收藏时间', dataIndex: 'fav_time', key: 'fav_time', render: (time) => moment.unix(time).format('MM-DD HH:mm') },
    ];

    return (
      <Table
        columns={columns}
        dataSource={folder.resources || []}
        pagination={false}
        size="small"
        rowKey="id"
      />
    );
  };

  // 收藏夹表格列
  const favoriteColumns = [
    {
      title: '收藏夹名称',
      dataIndex: 'title',
      key: 'title',
      width: 200,
    },
    {
      title: '内容数量',
      dataIndex: 'media_count',
      key: 'media_count',
      width: 100,
      render: (count) => `${count} 个`,
    },
    {
      title: '创建时间',
      dataIndex: 'ctime',
      key: 'ctime',
      width: 150,
      render: (timestamp) => moment.unix(timestamp).format('YYYY-MM-DD'),
    },
    {
      title: '描述',
      dataIndex: 'intro',
      key: 'intro',
      ellipsis: true,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        {/* 操作区域 */}
        <Col span={24}>
          <Card>
            <Row gutter={16} align="middle">
              <Col>
                <Button 
                  type="primary" 
                  icon={<UserOutlined />}
                  loading={loading}
                  onClick={() => fetchUserInfo(currentCookie)}
                >
                  获取用户信息
                </Button>
              </Col>
              <Col>
                <Button 
                  icon={<SettingOutlined />}
                  onClick={() => setCookieModalVisible(true)}
                >
                  设置Cookie
                </Button>
              </Col>
              <Col>
                <Button 
                  icon={<ReloadOutlined />}
                  loading={loading}
                  onClick={fetchAllData}
                  disabled={!userInfo}
                >
                  获取所有数据
                </Button>
              </Col>
            </Row>
            
            {/* Cookie状态提示 */}
            {!userInfo && (
              <Alert
                message="Cookie状态"
                description={
                  currentCookie 
                    ? "当前使用自定义Cookie，如果获取失败请检查Cookie是否有效" 
                    : "当前使用默认Cookie，如果获取失败请设置自定义Cookie"
                }
                type="warning"
                showIcon
                style={{ marginTop: 16 }}
                action={
                  <Button size="small" onClick={() => setCookieModalVisible(true)}>
                    设置Cookie
                  </Button>
                }
              />
            )}
          </Card>
        </Col>

        {/* 用户信息 */}
        {userInfo && (
          <Col span={24}>
            <Card title="用户信息" extra={<UserOutlined />}>
              <Descriptions column={4}>
                <Descriptions.Item label="用户名">{userInfo.name}</Descriptions.Item>
                <Descriptions.Item label="用户ID">{userInfo.mid}</Descriptions.Item>
                <Descriptions.Item label="等级">Lv{userInfo.level}</Descriptions.Item>
                <Descriptions.Item label="粉丝数">{userInfo.follower}</Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>
        )}

        {/* 数据统计 */}
        {(history.length > 0 || favorites.length > 0) && (
          <Col span={24}>
            <Card title="数据概览">
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="观看记录"
                    value={history.length}
                    suffix="条"
                    prefix={<HistoryOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="收藏夹"
                    value={favorites.length}
                    suffix="个"
                    prefix={<HeartOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="收藏内容"
                    value={favorites.reduce((sum, folder) => sum + (folder.media_count || 0), 0)}
                    suffix="个"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Cookie状态"
                    value={currentCookie ? "自定义" : "默认"}
                    valueStyle={{ color: currentCookie ? '#cf1322' : '#3f8600' }}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
        )}

        {/* 用户分析图表 */}
        {analysis && (
          <>
            <Col span={12}>
              <Card title="观看分区偏好" size="small">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(analysis.category_preferences).map(([name, value]) => ({ name, value }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.entries(analysis.category_preferences).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>

            <Col span={12}>
              <Card title="观看时间分布" size="small">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={Object.entries(analysis.watch_time_distribution).map(([hour, count]) => ({ hour: `${hour}时`, count }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>

            <Col span={24}>
              <Card title="分析结果" size="small">
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="总观看数"
                      value={analysis.total_watched}
                      suffix="个视频"
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="最活跃时段"
                      value={analysis.most_active_hours.map(item => `${item.hour}时`).join(', ')}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="最喜欢分区"
                      value={Object.keys(analysis.category_preferences)[0] || '暂无'}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </>
        )}

        {/* 观看历史 */}
        {history.length > 0 && (
          <Col span={24}>
            <Card title={`观看历史 (${history.length})`} extra={<HistoryOutlined />}>
              <Table
                columns={historyColumns}
                dataSource={history}
                rowKey={(record) => `${record.aid}_${record.view_at}`}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total) => `共 ${total} 条记录`,
                }}
                scroll={{ x: 800 }}
                size="small"
              />
            </Card>
          </Col>
        )}

        {/* 收藏夹 */}
        {favorites.length > 0 && (
          <Col span={24}>
            <Card title={`收藏夹 (${favorites.length})`} extra={<HeartOutlined />}>
              <Table
                columns={favoriteColumns}
                dataSource={favorites}
                rowKey="id"
                expandable={{
                  expandedRowRender,
                  rowExpandable: (record) => (record.resources && record.resources.length > 0),
                }}
                pagination={{
                  pageSize: 5,
                  showTotal: (total) => `共 ${total} 个收藏夹`,
                }}
                size="small"
              />
            </Card>
          </Col>
        )}
      </Row>

      {/* Cookie设置弹窗 */}
      <Modal
        title="设置自定义Cookie"
        open={cookieModalVisible}
        onOk={handleCustomCookie}
        onCancel={() => {
          setCookieModalVisible(false);
          setCustomCookie('');
        }}
        width={800}
        confirmLoading={loading}
      >
        <Alert
          message="Cookie获取详细步骤"
          description={
            <div>
              <p><strong>方法一：通过开发者工具获取</strong></p>
              <ol>
                <li>打开 <a href="https://www.bilibili.com" target="_blank" rel="noopener noreferrer">B站官网</a> 并登录你的账号</li>
                <li>按 <code>F12</code> 打开开发者工具</li>
                <li>切换到 <code>Network</code>（网络）标签</li>
                <li>刷新页面（按F5）</li>
                <li>在请求列表中点击任意一个请求</li>
                <li>在右侧找到 <code>Request Headers</code>，复制 <code>Cookie</code> 的完整值</li>
              </ol>
              <p><strong>方法二：通过控制台获取</strong></p>
              <ol>
                <li>在B站页面按 <code>F12</code> 打开开发者工具</li>
                <li>切换到 <code>Console</code>（控制台）标签</li>
                <li>输入 <code>document.cookie</code> 并按回车</li>
                <li>复制输出的完整Cookie值</li>
              </ol>
              <p style={{ color: '#ff4d4f', marginTop: 8 }}>
                ⚠️ 注意：Cookie包含敏感信息，请勿分享给他人
              </p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <TextArea
          rows={6}
          placeholder="请粘贴完整的Cookie..."
          value={customCookie}
          onChange={(e) => setCustomCookie(e.target.value)}
        />
      </Modal>
    </div>
  );
};

export default UserAnalysis; 