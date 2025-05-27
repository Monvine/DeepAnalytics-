import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Select, 
  DatePicker, 
  Button, 
  Space,
  Slider,
  Switch,
  Typography,
  Tooltip
} from 'antd';
import { 
  ZoomInOutlined,
  FilterOutlined,
  DownloadOutlined,
  FullscreenOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  Brush,
  ReferenceLine
} from 'recharts';
import { videoAPI } from '../services/api';
import './InteractiveCharts.css';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

// 颜色配置
const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16'];

// 自定义工具提示
const CustomTooltip = ({ active, payload, label, formatter }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="tooltip-label">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ color: entry.color }}>
            {`${entry.name}: ${formatter ? formatter(entry.value) : entry.value}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// 可缩放的折线图
const ZoomableLineChart = ({ data, title, xKey, yKeys, colors }) => {
  const [zoomDomain, setZoomDomain] = useState(null);
  const [showBrush, setShowBrush] = useState(true);

  const handleZoom = (domain) => {
    setZoomDomain(domain);
  };

  const resetZoom = () => {
    setZoomDomain(null);
  };

  return (
    <Card 
      title={title}
      className="interactive-chart-card"
      extra={
        <Space>
          <Tooltip title="显示/隐藏缩放条">
            <Switch 
              checked={showBrush} 
              onChange={setShowBrush}
              size="small"
            />
          </Tooltip>
          <Tooltip title="重置缩放">
            <Button 
              icon={<ReloadOutlined />} 
              size="small" 
              onClick={resetZoom}
            />
          </Tooltip>
        </Space>
      }
    >
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey={xKey} 
            stroke="#666"
            domain={zoomDomain}
          />
          <YAxis stroke="#666" />
          <RechartsTooltip 
            content={<CustomTooltip formatter={(value) => value.toLocaleString()} />}
          />
          <Legend />
          {yKeys.map((key, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[index] || COLORS[index]}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
          {showBrush && (
            <Brush 
              dataKey={xKey} 
              height={30} 
              stroke="#1890ff"
              onChange={handleZoom}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};

// 可钻取的饼图
const DrillablePieChart = ({ data, title, onDrill }) => {
  const [selectedSegment, setSelectedSegment] = useState(null);
  const [drillData, setDrillData] = useState(null);

  const handleClick = (data, index) => {
    setSelectedSegment(index);
    if (onDrill) {
      const drillDownData = onDrill(data);
      setDrillData(drillDownData);
    }
  };

  const goBack = () => {
    setSelectedSegment(null);
    setDrillData(null);
  };

  const currentData = drillData || data;

  return (
    <Card 
      title={title}
      className="interactive-chart-card"
      extra={
        drillData && (
          <Button 
            size="small" 
            onClick={goBack}
            icon={<ReloadOutlined />}
          >
            返回
          </Button>
        )
      }
    >
      <ResponsiveContainer width="100%" height={350}>
        <PieChart>
          <Pie
            data={currentData}
            cx="50%"
            cy="50%"
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            onClick={handleClick}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {currentData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={COLORS[index % COLORS.length]}
                stroke={selectedSegment === index ? '#fff' : 'none'}
                strokeWidth={selectedSegment === index ? 2 : 0}
              />
            ))}
          </Pie>
          <RechartsTooltip />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  );
};

// 可筛选的柱状图
const FilterableBarChart = ({ data, title, xKey, yKey, filters }) => {
  const [filteredData, setFilteredData] = useState(data);
  const [activeFilters, setActiveFilters] = useState({});
  const [sortOrder, setSortOrder] = useState('desc');

  useEffect(() => {
    let result = [...data];
    
    // 应用筛选器
    Object.entries(activeFilters).forEach(([key, value]) => {
      if (value) {
        // 修复：使用精确匹配而不是包含匹配
        result = result.filter(item => item[key] === value);
      }
    });

    // 排序
    result.sort((a, b) => {
      const aVal = a[yKey];
      const bVal = b[yKey];
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });

    setFilteredData(result);
  }, [data, activeFilters, sortOrder, yKey]);

  const handleFilterChange = (key, value) => {
    setActiveFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <Card 
      title={title}
      className="interactive-chart-card"
      extra={
        <Space>
          {filters?.map(filter => (
            <Select
              key={filter.key}
              placeholder={filter.label}
              style={{ width: 120 }}
              allowClear
              onChange={(value) => handleFilterChange(filter.key, value)}
            >
              {filter.options.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          ))}
          <Select
            value={sortOrder}
            onChange={setSortOrder}
            style={{ width: 100 }}
          >
            <Option value="desc">降序</Option>
            <Option value="asc">升序</Option>
          </Select>
        </Space>
      }
    >
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={filteredData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey={xKey} 
            stroke="#666"
            angle={-45}
            textAnchor="end"
            height={100}
          />
          <YAxis stroke="#666" />
          <RechartsTooltip 
            content={<CustomTooltip formatter={(value) => value.toLocaleString()} />}
          />
          <Bar 
            dataKey={yKey} 
            fill="#1890ff"
            radius={[4, 4, 0, 0]}
          >
            {filteredData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

// 雷达图
const RadarChartComponent = ({ data, title, keys }) => {
  const [selectedMetrics, setSelectedMetrics] = useState(keys);

  const filteredData = data.map(item => {
    const filtered = { subject: item.subject };
    selectedMetrics.forEach(key => {
      filtered[key] = item[key];
    });
    return filtered;
  });

  return (
    <Card 
      title={title}
      className="interactive-chart-card"
      extra={
        <Select
          mode="multiple"
          placeholder="选择指标"
          value={selectedMetrics}
          onChange={setSelectedMetrics}
          style={{ width: 200 }}
        >
          {keys.map(key => (
            <Option key={key} value={key}>{key}</Option>
          ))}
        </Select>
      }
    >
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={filteredData}>
          <PolarGrid />
          <PolarAngleAxis dataKey="subject" />
          <PolarRadiusAxis />
          {selectedMetrics.map((key, index) => (
            <Radar
              key={key}
              name={key}
              dataKey={key}
              stroke={COLORS[index % COLORS.length]}
              fill={COLORS[index % COLORS.length]}
              fillOpacity={0.1}
            />
          ))}
          <Legend />
          <RechartsTooltip />
        </RadarChart>
      </ResponsiveContainer>
    </Card>
  );
};

const InteractiveCharts = () => {
  const [loading, setLoading] = useState(true);
  const [chartsData, setChartsData] = useState({
    timeSeries: [],
    categories: [],
    videoPerformance: [],
    radar: []
  });
  const [timeRange, setTimeRange] = useState([]);

  // 获取图表数据
  const fetchChartsData = async () => {
    try {
      const [analysisData, videosData] = await Promise.all([
        videoAPI.getAnalysis(),
        videoAPI.getVideos(null, null, 50)
      ]);

      console.log('视频数据:', videosData.slice(0, 5)); // 调试信息
      console.log('分析数据:', analysisData); // 调试信息

      // 生成时间序列数据
      const timeSeriesData = generateTimeSeriesData(videosData);
      
      // 生成分区数据
      const categoryData = analysisData.top_tags.slice(0, 8).map(([name, value]) => ({
        name,
        value,
        fill: COLORS[analysisData.top_tags.indexOf([name, value]) % COLORS.length]
      }));

      // 生成视频表现数据
      const videoPerformanceData = videosData.slice(0, 20).map(video => ({
        title: video.title.length > 20 ? video.title.substring(0, 20) + '...' : video.title,
        views: video.view,
        likes: video.like,
        coins: video.coin,
        shares: video.share,
        category: video.tname || '其他'
      }));

      console.log('视频表现数据:', videoPerformanceData); // 调试信息
      console.log('分区分布:', Array.from(new Set(videoPerformanceData.map(item => item.category)))); // 调试信息

      // 生成雷达图数据
      const radarData = generateRadarData(analysisData);

      setChartsData({
        timeSeries: timeSeriesData,
        categories: categoryData,
        videoPerformance: videoPerformanceData,
        radar: radarData
      });

    } catch (error) {
      console.error('获取图表数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 生成时间序列数据
  const generateTimeSeriesData = (videos) => {
    const data = [];
    const now = new Date();
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      const dayVideos = videos.filter(video => {
        const videoDate = new Date(video.pubdate);
        return videoDate.toDateString() === date.toDateString();
      });

      data.push({
        date: date.toLocaleDateString(),
        videos: dayVideos.length,
        totalViews: dayVideos.reduce((sum, v) => sum + v.view, 0),
        totalLikes: dayVideos.reduce((sum, v) => sum + v.like, 0),
        avgDuration: dayVideos.length > 0 ? 
          dayVideos.reduce((sum, v) => sum + (v.duration || 300), 0) / dayVideos.length : 0
      });
    }
    
    return data;
  };

  // 生成雷达图数据
  const generateRadarData = (analysisData) => {
    // 修复：将互动率转换为合理的0-100范围数值
    const interactionScore = Math.min(Math.max(analysisData.avg_interaction_rate * 100, 0), 100);
    
    return [
      {
        subject: '内容质量',
        '实际数据': 85,
        '行业平均': 90,
        '竞品对比': 78,
        fullMark: 100
      },
      {
        subject: '用户互动',
        '实际数据': Math.round(interactionScore), // 修复：使用合理的数值范围
        '行业平均': 75,
        '竞品对比': 82,
        fullMark: 100
      },
      {
        subject: '传播效果',
        '实际数据': 88,
        '行业平均': 85,
        '竞品对比': 90,
        fullMark: 100
      },
      {
        subject: '创新程度',
        '实际数据': 92,
        '行业平均': 78,
        '竞品对比': 85,
        fullMark: 100
      },
      {
        subject: '技术水平',
        '实际数据': 87,
        '行业平均': 92,
        '竞品对比': 88,
        fullMark: 100
      }
    ];
  };

  // 钻取函数
  const handleCategoryDrill = (data) => {
    // 模拟钻取到子分类
    return [
      { name: `${data.name}-子类1`, value: Math.floor(data.value * 0.4) },
      { name: `${data.name}-子类2`, value: Math.floor(data.value * 0.3) },
      { name: `${data.name}-子类3`, value: Math.floor(data.value * 0.3) }
    ];
  };

  useEffect(() => {
    fetchChartsData();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '100px' }}>加载交互式图表...</div>;
  }

  return (
    <div className="interactive-charts">
      <div style={{ marginBottom: 24 }}>
        <Title level={3}>交互式数据分析</Title>
        <Text type="secondary">支持缩放、筛选、钻取的高级数据可视化</Text>
      </div>

      <Row gutter={[16, 16]}>
        {/* 可缩放时间序列图 */}
        <Col span={24}>
          <ZoomableLineChart
            data={chartsData.timeSeries}
            title="30天数据趋势 (支持缩放)"
            xKey="date"
            yKeys={['videos', 'totalViews', 'totalLikes']}
            colors={['#1890ff', '#52c41a', '#faad14']}
          />
        </Col>

        {/* 可钻取饼图和可筛选柱状图 */}
        <Col xs={24} lg={12}>
          <DrillablePieChart
            data={chartsData.categories}
            title="分区分布 (点击钻取)"
            onDrill={handleCategoryDrill}
          />
        </Col>

        <Col xs={24} lg={12}>
          <FilterableBarChart
            data={chartsData.videoPerformance}
            title="视频表现 (支持筛选排序)"
            xKey="title"
            yKey="views"
            filters={[
              {
                key: 'category',
                label: '分区',
                options: [
                  // 动态生成分区选项
                  ...Array.from(new Set(chartsData.videoPerformance.map(item => item.category)))
                    .filter(category => category && category !== '其他')
                    .map(category => ({ value: category, label: category })),
                  { value: '其他', label: '其他' }
                ]
              }
            ]}
          />
        </Col>

        {/* 雷达图 */}
        <Col span={24}>
          <RadarChartComponent
            data={chartsData.radar}
            title="多维度分析雷达图"
            keys={['实际数据', '行业平均', '竞品对比']}
          />
        </Col>
      </Row>
    </div>
  );
};

export default InteractiveCharts; 