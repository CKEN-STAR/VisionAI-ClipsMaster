# 服务配置
http_host = os.getenv("HTTP_HOST", "0.0.0.0")
http_port = int(os.getenv("HTTP_PORT", "8000"))
websocket_host = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
websocket_port = int(os.getenv("WEBSOCKET_PORT", "8765"))
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
debug_mode = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# 操作日志配置
operation_log_enabled = os.getenv("OPERATION_LOG_ENABLED", "true").lower() in ("true", "1", "yes")
operation_log_dir = os.getenv("OPERATION_LOG_DIR", "logs/operations")
operation_log_s3_enabled = os.getenv("OPERATION_LOG_S3_ENABLED", "false").lower() in ("true", "1", "yes")
operation_log_s3_bucket = os.getenv("OPERATION_LOG_S3_BUCKET", "visionai-logs")
operation_log_s3_prefix = os.getenv("OPERATION_LOG_S3_PREFIX", "operations/")
operation_log_flush_interval = int(os.getenv("OPERATION_LOG_FLUSH_INTERVAL", "300")) 