/**
 * VisionAI-ClipsMaster SDK
 * 用于与VisionAI-ClipsMaster API进行交互的JavaScript客户端SDK
 * 
 * @version 1.0.0
 * @author VisionAI Team
 */

class APIError extends Error {
  /**
   * API错误异常类
   * @param {number} statusCode - HTTP状态码
   * @param {string} message - 错误消息
   * @param {string} endpoint - 请求端点
   */
  constructor(statusCode, message, endpoint) {
    super(`API错误 (${statusCode}): ${message} [endpoint: ${endpoint}]`);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.endpoint = endpoint;
  }
}

/**
 * 任务状态常量
 */
const TaskStatus = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  SUCCESS: 'success',
  FAILED: 'failed'
};

/**
 * VisionAI-ClipsMaster API客户端
 */
class ClipsMasterClient {
  /**
   * 初始化API客户端
   * 
   * @param {Object} options - 配置选项
   * @param {string} options.apiKey - API密钥
   * @param {string} [options.baseUrl='http://localhost:8000'] - API基础URL
   * @param {number} [options.timeout=30000] - 请求超时时间(毫秒)
   * @param {number} [options.maxRetries=3] - 最大重试次数
   * @param {number} [options.retryDelay=2000] - 重试延迟时间(毫秒)
   */
  constructor(options) {
    if (!options || !options.apiKey) {
      throw new Error('必须提供API密钥');
    }
    
    this.apiKey = options.apiKey;
    this.baseUrl = (options.baseUrl || 'http://localhost:8000').replace(/\/$/, '');
    this.timeout = options.timeout || 30000;
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 2000;
    
    // 默认请求头
    this.headers = {
      'X-API-Key': this.apiKey,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': 'ClipsMaster-JavaScript-SDK/1.0.0'
    };
    
    // 日志选项
    this.enableLogging = options.enableLogging || false;
    
    // 记录初始化
    this._log('已初始化客户端:', this.baseUrl);
  }

  /**
   * 内部日志方法
   * @private
   */
  _log(...args) {
    if (this.enableLogging) {
      console.log('[ClipsMaster-SDK]', ...args);
    }
  }

  /**
   * 构建完整的API URL
   * @private
   * @param {string} endpoint - API端点
   * @returns {string} 完整URL
   */
  _buildUrl(endpoint) {
    endpoint = endpoint.replace(/^\//, '');
    return `${this.baseUrl}/${endpoint}`;
  }

  /**
   * 发送API请求
   * @private
   * @param {string} method - HTTP方法
   * @param {string} endpoint - API端点
   * @param {Object} [options={}] - 请求选项
   * @param {Object} [options.data] - 请求数据
   * @param {Object} [options.params] - 查询参数
   * @param {FormData} [options.formData] - 表单数据
   * @param {number} [retryCount=0] - 当前重试次数
   * @returns {Promise<Object>} API响应数据
   */
  async _request(method, endpoint, options = {}, retryCount = 0) {
    const url = this._buildUrl(endpoint);
    const { data, params, formData } = options;
    
    // 准备请求配置
    const config = {
      method,
      headers: { ...this.headers },
      // 设置超时
      signal: AbortSignal.timeout(this.timeout)
    };
    
    // 添加查询参数
    if (params) {
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          queryParams.append(key, value);
        }
      });
      const queryString = queryParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }
    
    // 添加请求体
    if (formData) {
      // 使用表单数据
      delete config.headers['Content-Type']; // 让fetch自动设置正确的Content-Type
      config.body = formData;
    } else if (data) {
      // 使用JSON数据
      config.body = JSON.stringify(data);
    }
    
    try {
      const response = await fetch(url, config);
      
      // 处理响应
      let responseData;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        responseData = await response.json();
      } else {
        const text = await response.text();
        responseData = { message: text };
      }
      
      // 检查是否成功
      if (!response.ok) {
        this._log('API错误:', response.status, responseData);
        throw new APIError(
          response.status,
          responseData.detail || '未知错误',
          endpoint
        );
      }
      
      return responseData;
      
    } catch (error) {
      // 处理网络错误、超时等
      if (error instanceof APIError) {
        throw error; // 直接抛出API错误
      }
      
      this._log('请求失败:', error.message);
      
      // 尝试重试
      if (retryCount < this.maxRetries) {
        this._log(`请求失败，正在重试 (${retryCount+1}/${this.maxRetries})`, error.message);
        
        // 等待重试延迟
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        
        // 递归调用自身进行重试
        return this._request(method, endpoint, options, retryCount + 1);
      }
      
      // 超过最大重试次数
      throw new APIError(500, error.message, endpoint);
    }
  }
  
  /**
   * 获取模型状态
   * @returns {Promise<Object>} 模型状态信息字典
   */
  async getModelsStatus() {
    return this._request('GET', '/api/v1/models/status');
  }
  
  /**
   * 创建视频剪辑任务
   * 
   * @param {Object} options - 剪辑请求选项
   * @param {string} options.videoPath - 视频文件路径
   * @param {string} options.srtPath - 字幕文件路径
   * @param {string} [options.lang='zh'] - 语言 ('zh' 或 'en')
   * @param {string} [options.quantLevel='Q4_K_M'] - 量化等级
   * @param {string} [options.exportFormat='both'] - 导出格式 ('video', 'project', 'both')
   * @param {number} [options.maxDuration] - The maximum clip duration in seconds
   * @param {string[]} [options.narrativeFocus] - 叙事重点关键词列表
   * @param {number} [options.temperature=0.7] - 生成温度(0.1-1.0)
   * @param {Object[]} [options.preserveSegments] - 必须保留的片段时间点列表
   * @returns {Promise<Object>} 任务信息
   */
  async generateClip(options) {
    const {
      videoPath,
      srtPath,
      lang = 'zh',
      quantLevel = 'Q4_K_M',
      exportFormat = 'both',
      maxDuration,
      narrativeFocus,
      temperature = 0.7,
      preserveSegments
    } = options;
    
    // 构建请求数据
    const requestData = {
      video_path: videoPath,
      srt_path: srtPath,
      lang,
      quant_level: quantLevel,
      export_format: exportFormat,
      temperature
    };
    
    // 添加可选参数
    if (maxDuration !== undefined) requestData.max_duration = maxDuration;
    if (narrativeFocus) requestData.narrative_focus = narrativeFocus;
    if (preserveSegments) requestData.preserve_segments = preserveSegments;
    
    return this._request('POST', '/api/v1/generate', { data: requestData });
  }
  
  /**
   * 获取任务状态
   * 
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} 任务状态信息
   */
  async getTaskStatus(taskId) {
    return this._request('GET', `/api/v1/task/${taskId}`);
  }
  
  /**
   * 取消任务
   * 
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} 操作结果
   */
  async cancelTask(taskId) {
    return this._request('DELETE', `/api/v1/task/${taskId}`);
  }
  
  /**
   * 批量创建视频剪辑任务
   * 
   * @param {Object} options - 批量请求选项
   * @param {Object[]} options.clips - 剪辑请求列表
   * @param {number} [options.parallel=1] - 并行处理数量
   * @returns {Promise<Object>} 批量任务信息
   */
  async batchGenerate(options) {
    const { clips, parallel = 1 } = options;
    
    const requestData = {
      clips,
      parallel
    };
    
    return this._request('POST', '/api/v1/batch', { data: requestData });
  }
  
  /**
   * 获取批量任务状态
   * 
   * @param {string} batchId - 批次ID
   * @returns {Promise<Object>} 批量任务状态信息
   */
  async getBatchStatus(batchId) {
    return this._request('GET', `/api/v1/batch/${batchId}`);
  }

  /**
   * 等待任务完成
   * 
   * @param {Object} options - 等待选项
   * @param {string} options.taskId - 任务ID
   * @param {number} [options.pollInterval=2000] - 轮询间隔时间(毫秒)
   * @param {number} [options.timeout=3600000] - 超时时间(毫秒)，0表示无限等待
   * @param {Function} [options.progressCallback] - 进度回调函数，接收进度和消息参数
   * @returns {Promise<Object>} 最终任务状态信息
   */
  async waitForTask(options) {
    const {
      taskId,
      pollInterval = 2000,
      timeout = 3600000, // 1小时
      progressCallback
    } = options;
    
    const startTime = Date.now();
    let lastProgress = -1;
    
    // 轮询检查任务状态
    while (true) {
      // 检查是否超时
      if (timeout > 0 && (Date.now() - startTime > timeout)) {
        throw new Error(`任务等待超时: ${taskId}`);
      }
      
      // 获取任务状态
      const taskInfo = await this.getTaskStatus(taskId);
      const status = taskInfo.status;
      const progress = taskInfo.progress || 0;
      const message = taskInfo.message || '';
      
      // 如果进度变化，调用回调函数
      if (progress !== lastProgress && progressCallback) {
        progressCallback(progress, message);
        lastProgress = progress;
      }
      
      // 检查任务是否完成
      if (status === TaskStatus.SUCCESS) {
        if (progressCallback) {
          progressCallback(1.0, '任务完成');
        }
        return taskInfo;
      } else if (status === TaskStatus.FAILED) {
        const errorMsg = taskInfo.message || '未知错误';
        throw new Error(`任务失败: ${errorMsg}`);
      }
      
      // 等待一段时间后再次检查
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  }
  
  /**
   * 等待批量任务完成
   * 
   * @param {Object} options - 等待选项
   * @param {string} options.batchId - 批次ID
   * @param {number} [options.pollInterval=5000] - 轮询间隔时间(毫秒)
   * @param {number} [options.timeout=7200000] - 超时时间(毫秒)，0表示无限等待
   * @param {Function} [options.progressCallback] - 进度回调函数，接收完成数量、总数量和消息参数
   * @returns {Promise<Object>} 最终批量任务状态信息
   */
  async waitForBatch(options) {
    const {
      batchId,
      pollInterval = 5000,
      timeout = 7200000, // 2小时
      progressCallback
    } = options;
    
    const startTime = Date.now();
    let lastCompleted = -1;
    
    // 轮询检查批量任务状态
    while (true) {
      // 检查是否超时
      if (timeout > 0 && (Date.now() - startTime > timeout)) {
        throw new Error(`批量任务等待超时: ${batchId}`);
      }
      
      // 获取批量任务状态
      const batchInfo = await this.getBatchStatus(batchId);
      const status = batchInfo.status;
      const completed = batchInfo.completed || 0;
      const total = batchInfo.total || 0;
      const message = batchInfo.message || '';
      
      // 如果完成数量变化，调用回调函数
      if (completed !== lastCompleted && progressCallback) {
        progressCallback(completed, total, message);
        lastCompleted = completed;
      }
      
      // 检查批量任务是否完成
      if (status === TaskStatus.SUCCESS) {
        if (progressCallback) {
          progressCallback(total, total, '所有任务完成');
        }
        return batchInfo;
      } else if (status === TaskStatus.FAILED) {
        // 批量任务可能部分失败，返回结果供调用者进一步处理
        if (progressCallback) {
          progressCallback(completed, total, '部分任务失败');
        }
        return batchInfo;
      }
      
      // 等待一段时间后再次检查
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  }
  
  /**
   * 创建视频剪辑任务并同步等待完成
   * 
   * @param {Object} options - 剪辑和等待选项
   * @param {string} options.videoPath - 视频文件路径
   * @param {string} options.srtPath - 字幕文件路径
   * @param {string} [options.lang='zh'] - 语言 ('zh' 或 'en')
   * @param {string} [options.quantLevel='Q4_K_M'] - 量化等级
   * @param {string} [options.exportFormat='both'] - 导出格式
   * @param {number} [options.maxDuration] - 最大输出时长(秒)
   * @param {string[]} [options.narrativeFocus] - 叙事重点关键词列表
   * @param {number} [options.temperature=0.7] - 生成温度(0.1-1.0)
   * @param {Object[]} [options.preserveSegments] - 必须保留的片段时间点列表
   * @param {number} [options.pollInterval=2000] - 轮询间隔时间(毫秒)
   * @param {number} [options.timeout=3600000] - 超时时间(毫秒)
   * @param {Function} [options.progressCallback] - 进度回调函数
   * @returns {Promise<Object>} 最终任务状态信息
   */
  async generateClipSync(options) {
    // 创建任务
    const taskResponse = await this.generateClip(options);
    const taskId = taskResponse.task_id;
    
    this._log(`已创建任务: ${taskId}`);
    
    // 等待任务完成
    return this.waitForTask({
      taskId,
      pollInterval: options.pollInterval,
      timeout: options.timeout,
      progressCallback: options.progressCallback
    });
  }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ClipsMasterClient, APIError, TaskStatus };
} else if (typeof window !== 'undefined') {
  window.ClipsMaster = { ClipsMasterClient, APIError, TaskStatus };
} 