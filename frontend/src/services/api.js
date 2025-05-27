import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API错误:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// 热门视频相关API
export const videoAPI = {
  // 手动触发爬取
  crawlPopular: () => api.post('/api/crawl/popular'),
  
  // 获取视频分析结果
  getAnalysis: () => api.get('/api/analysis/videos'),
  
  // 获取分析图表
  getChart: () => `${API_BASE_URL}/api/analysis/chart?t=${Date.now()}`,
  
  // 获取视频列表（支持分页）
  getVideos: (page = 1, pageSize = 10, limit = null) => {
    if (limit !== null) {
      // 向后兼容，使用limit参数
      return api.get(`/api/videos?limit=${limit}`);
    }
    return api.get(`/api/videos?page=${page}&page_size=${pageSize}`);
  },
};

// 用户数据相关API
export const userAPI = {
  // 获取用户信息
  getUserInfo: (cookie = null) => {
    if (cookie) {
      return api.post('/api/user/info', { cookie });
    }
    return api.post('/api/user/info');
  },
  
  // 获取观看历史
  getHistory: (cookie = null) => {
    if (cookie) {
      return api.post('/api/user/history', { cookie });
    }
    return api.post('/api/user/history');
  },
  
  // 获取收藏
  getFavorites: (cookie = null) => {
    if (cookie) {
      return api.post('/api/user/favorites', { cookie });
    }
    return api.post('/api/user/favorites');
  },
  
  // 获取用户分析
  getUserAnalysis: (userMid) => api.get(`/api/user/analysis/${userMid}`),
};

// 报告相关API
export const reportAPI = {
  // 生成日报
  generateDaily: (data) => api.post('/api/reports/generate-daily', data),
  
  // 生成周报
  generateWeekly: (data) => api.post('/api/reports/generate-weekly', data),
  
  // 获取报告列表
  getList: () => api.get('/api/reports/list'),
  
  // 查看报告内容
  view: (filename) => api.get(`/api/reports/view/${filename}`),
  
  // 下载报告（特殊处理blob响应）
  download: async (filename) => {
    const response = await axios.get(`${API_BASE_URL}/api/reports/download/${filename}`, {
      responseType: 'blob'
    });
    return response.data;
  },
  
  // 删除报告
  delete: (filename) => api.delete(`/api/reports/${filename}`),
};

export default api; 