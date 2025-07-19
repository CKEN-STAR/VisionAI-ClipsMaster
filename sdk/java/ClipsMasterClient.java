/**
 * VisionAI-ClipsMaster SDK
 * 用于与VisionAI-ClipsMaster API进行交互的Java客户端SDK
 *
 * @version 1.0.0
 * @author VisionAI Team
 */

package com.visionai.clipsmaster;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;

/**
 * VisionAI-ClipsMaster API客户端
 */
public class ClipsMasterClient {
    private static final Logger LOGGER = Logger.getLogger(ClipsMasterClient.class.getName());
    private static final String USER_AGENT = "ClipsMaster-Java-SDK/1.0.0";
    
    private final String apiKey;
    private final String baseUrl;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final int timeout;
    private final int maxRetries;
    private final int retryDelay;
    private final boolean enableLogging;
    
    /**
     * API错误异常类
     */
    public static class APIError extends Exception {
        private final int statusCode;
        private final String endpoint;
        
        public APIError(int statusCode, String message, String endpoint) {
            super(String.format("API错误 (%d): %s [endpoint: %s]", statusCode, message, endpoint));
            this.statusCode = statusCode;
            this.endpoint = endpoint;
        }
        
        public int getStatusCode() {
            return statusCode;
        }
        
        public String getEndpoint() {
            return endpoint;
        }
    }
    
    /**
     * 任务状态常量
     */
    public static class TaskStatus {
        public static final String PENDING = "pending";
        public static final String PROCESSING = "processing";
        public static final String SUCCESS = "success";
        public static final String FAILED = "failed";
    }
    
    /**
     * 进度回调接口
     */
    public interface ProgressCallback {
        void onProgress(double progress, String message);
    }
    
    /**
     * 批量进度回调接口
     */
    public interface BatchProgressCallback {
        void onProgress(int completed, int total, String message);
    }
    
    /**
     * 构造器
     */
    public static class Builder {
        private final String apiKey;
        private String baseUrl = "http://localhost:8000";
        private int timeout = 30;
        private int maxRetries = 3;
        private int retryDelay = 2;
        private boolean enableLogging = false;
        
        public Builder(String apiKey) {
            this.apiKey = apiKey;
        }
        
        public Builder baseUrl(String baseUrl) {
            this.baseUrl = baseUrl;
            return this;
        }
        
        public Builder timeout(int timeoutSeconds) {
            this.timeout = timeoutSeconds;
            return this;
        }
        
        public Builder maxRetries(int maxRetries) {
            this.maxRetries = maxRetries;
            return this;
        }
        
        public Builder retryDelay(int retryDelaySeconds) {
            this.retryDelay = retryDelaySeconds;
            return this;
        }
        
        public Builder enableLogging(boolean enableLogging) {
            this.enableLogging = enableLogging;
            return this;
        }
        
        public ClipsMasterClient build() {
            return new ClipsMasterClient(this);
        }
    }
    
    /**
     * 私有构造器，通过Builder创建实例
     */
    private ClipsMasterClient(Builder builder) {
        this.apiKey = builder.apiKey;
        this.baseUrl = builder.baseUrl.endsWith("/") ? builder.baseUrl.substring(0, builder.baseUrl.length() - 1) : builder.baseUrl;
        this.timeout = builder.timeout;
        this.maxRetries = builder.maxRetries;
        this.retryDelay = builder.retryDelay;
        this.enableLogging = builder.enableLogging;
        
        // 创建HTTP客户端
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_2)
                .connectTimeout(Duration.ofSeconds(timeout))
                .build();
        
        // 创建JSON序列化工具
        this.objectMapper = new ObjectMapper();
        
        log("已初始化客户端: " + this.baseUrl);
    }
    
    /**
     * 日志方法
     */
    private void log(String message) {
        if (enableLogging) {
            LOGGER.info("[ClipsMaster-SDK] " + message);
        }
    }
    
    /**
     * 构建完整的API URL
     */
    private String buildUrl(String endpoint) {
        if (endpoint.startsWith("/")) {
            endpoint = endpoint.substring(1);
        }
        return baseUrl + "/" + endpoint;
    }
    
    /**
     * 发送GET请求
     */
    private Map<String, Object> get(String endpoint) throws APIError {
        return request("GET", endpoint, null);
    }
    
    /**
     * 发送POST请求
     */
    private Map<String, Object> post(String endpoint, Map<String, Object> data) throws APIError {
        return request("POST", endpoint, data);
    }
    
    /**
     * 发送DELETE请求
     */
    private Map<String, Object> delete(String endpoint) throws APIError {
        return request("DELETE", endpoint, null);
    }
    
    /**
     * 发送API请求
     */
    private Map<String, Object> request(String method, String endpoint, Map<String, Object> data) throws APIError {
        return request(method, endpoint, data, 0);
    }
    
    /**
     * 发送API请求（带重试）
     */
    private Map<String, Object> request(String method, String endpoint, Map<String, Object> data, int retryCount) throws APIError {
        String url = buildUrl(endpoint);
        
        try {
            HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .header("X-API-Key", apiKey)
                    .header("User-Agent", USER_AGENT)
                    .header("Accept", "application/json")
                    .timeout(Duration.ofSeconds(timeout));
            
            if ("GET".equals(method)) {
                requestBuilder.GET();
            } else if ("DELETE".equals(method)) {
                requestBuilder.DELETE();
            } else if ("POST".equals(method)) {
                // 将数据转换为JSON字符串
                String jsonData = objectMapper.writeValueAsString(data);
                requestBuilder.header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(jsonData));
            }
            
            HttpRequest request = requestBuilder.build();
            
            // 发送请求并获取响应
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            
            // 检查状态码
            int statusCode = response.statusCode();
            if (statusCode >= 400) {
                // 尝试解析错误消息
                String errorMessage = "未知错误";
                try {
                    Map<String, Object> errorData = objectMapper.readValue(response.body(), new TypeReference<Map<String, Object>>() {});
                    errorMessage = (String) errorData.getOrDefault("detail", "未知错误");
                } catch (Exception e) {
                    errorMessage = response.body();
                }
                
                throw new APIError(statusCode, errorMessage, endpoint);
            }
            
            // 解析响应JSON
            return objectMapper.readValue(response.body(), new TypeReference<Map<String, Object>>() {});
            
        } catch (IOException | InterruptedException e) {
            // 尝试重试
            if (retryCount < maxRetries) {
                log(String.format("请求失败，正在重试 (%d/%d): %s", retryCount + 1, maxRetries, e.getMessage()));
                
                try {
                    // 等待重试延迟
                    Thread.sleep(retryDelay * 1000);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                }
                
                // 递归调用自身进行重试
                return request(method, endpoint, data, retryCount + 1);
            }
            
            // 超过最大重试次数
            throw new APIError(500, e.getMessage(), endpoint);
        } catch (APIError e) {
            throw e;
        } catch (Exception e) {
            throw new APIError(500, e.getMessage(), endpoint);
        }
    }
    
    /**
     * 获取模型状态
     */
    public Map<String, Object> getModelsStatus() throws APIError {
        return get("/api/v1/models/status");
    }
    
    /**
     * 创建视频剪辑任务
     */
    public Map<String, Object> generateClip(
            String videoPath,
            String srtPath,
            String lang,
            String quantLevel,
            String exportFormat,
            Double maxDuration,
            List<String> narrativeFocus,
            double temperature,
            List<Map<String, Double>> preserveSegments
    ) throws APIError {
        Map<String, Object> requestData = new HashMap<>();
        requestData.put("video_path", videoPath);
        requestData.put("srt_path", srtPath);
        requestData.put("lang", lang);
        requestData.put("quant_level", quantLevel);
        requestData.put("export_format", exportFormat);
        requestData.put("temperature", temperature);
        
        // 添加可选参数
        if (maxDuration != null) {
            requestData.put("max_duration", maxDuration);
        }
        if (narrativeFocus != null) {
            requestData.put("narrative_focus", narrativeFocus);
        }
        if (preserveSegments != null) {
            requestData.put("preserve_segments", preserveSegments);
        }
        
        return post("/api/v1/generate", requestData);
    }
    
    /**
     * 创建视频剪辑任务（使用默认参数）
     */
    public Map<String, Object> generateClip(String videoPath, String srtPath) throws APIError {
        return generateClip(videoPath, srtPath, "zh", "Q4_K_M", "both", null, null, 0.7, null);
    }
    
    /**
     * 获取任务状态
     */
    public Map<String, Object> getTaskStatus(String taskId) throws APIError {
        return get("/api/v1/task/" + taskId);
    }
    
    /**
     * 取消任务
     */
    public Map<String, Object> cancelTask(String taskId) throws APIError {
        return delete("/api/v1/task/" + taskId);
    }
    
    /**
     * 等待任务完成
     */
    public Map<String, Object> waitForTask(String taskId, int pollIntervalSeconds, int timeoutSeconds, ProgressCallback callback) throws APIError, InterruptedException {
        long startTime = System.currentTimeMillis();
        double lastProgress = -1;
        
        while (true) {
            // 检查是否超时
            if (timeoutSeconds > 0 && (System.currentTimeMillis() - startTime > timeoutSeconds * 1000)) {
                throw new APIError(408, "任务等待超时", "/api/v1/task/" + taskId);
            }
            
            // 获取任务状态
            Map<String, Object> taskInfo = getTaskStatus(taskId);
            String status = (String) taskInfo.get("status");
            double progress = taskInfo.containsKey("progress") ? Double.parseDouble(taskInfo.get("progress").toString()) : 0;
            String message = (String) taskInfo.getOrDefault("message", "");
            
            // 如果进度变化，调用回调函数
            if (progress != lastProgress && callback != null) {
                callback.onProgress(progress, message);
                lastProgress = progress;
            }
            
            // 检查任务是否完成
            if (TaskStatus.SUCCESS.equals(status)) {
                if (callback != null) {
                    callback.onProgress(1.0, "任务完成");
                }
                return taskInfo;
            } else if (TaskStatus.FAILED.equals(status)) {
                String errorMsg = (String) taskInfo.getOrDefault("message", "未知错误");
                throw new APIError(500, "任务失败: " + errorMsg, "/api/v1/task/" + taskId);
            }
            
            // 等待一段时间后再次检查
            Thread.sleep(pollIntervalSeconds * 1000);
        }
    }
    
    /**
     * 创建视频剪辑任务并同步等待完成
     */
    public Map<String, Object> generateClipSync(
            String videoPath,
            String srtPath,
            String lang,
            String quantLevel,
            String exportFormat,
            Double maxDuration,
            List<String> narrativeFocus,
            double temperature,
            List<Map<String, Double>> preserveSegments,
            int pollIntervalSeconds,
            int timeoutSeconds,
            ProgressCallback callback
    ) throws APIError, InterruptedException {
        // 创建任务
        Map<String, Object> taskResponse = generateClip(
                videoPath,
                srtPath,
                lang,
                quantLevel,
                exportFormat,
                maxDuration,
                narrativeFocus,
                temperature,
                preserveSegments
        );
        
        String taskId = (String) taskResponse.get("task_id");
        log("已创建任务: " + taskId);
        
        // 等待任务完成
        return waitForTask(taskId, pollIntervalSeconds, timeoutSeconds, callback);
    }
    
    /**
     * 创建视频剪辑任务并同步等待完成（使用默认参数）
     */
    public Map<String, Object> generateClipSync(String videoPath, String srtPath, ProgressCallback callback) throws APIError, InterruptedException {
        return generateClipSync(videoPath, srtPath, "zh", "Q4_K_M", "both", null, null, 0.7, null, 2, 3600, callback);
    }
    
    /**
     * 异步创建视频剪辑任务
     */
    public CompletableFuture<Map<String, Object>> generateClipAsync(
            String videoPath,
            String srtPath,
            String lang,
            String quantLevel,
            String exportFormat,
            Double maxDuration,
            List<String> narrativeFocus,
            double temperature,
            List<Map<String, Double>> preserveSegments
    ) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return generateClip(
                        videoPath,
                        srtPath,
                        lang,
                        quantLevel,
                        exportFormat,
                        maxDuration,
                        narrativeFocus,
                        temperature,
                        preserveSegments
                );
            } catch (APIError e) {
                throw new RuntimeException(e);
            }
        });
    }
} 