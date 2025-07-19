"""模型分片模块

此模块提供高级模型分片功能，包括：
1. 智能模型分片切割
2. 模型层级依赖分析
3. 模型内存优化加载
4. 高性能并行分片处理
5. 分片元数据管理与追踪
6. 分片缓存管理与LRU调度
7. 分片完整性验证与安全校验
8. 智能后台预加载系统
9. 优先级分片卸载策略
10. 分片加载监控与分析
11. 容错恢复系统
"""

from src.sharding.model_splitter import ModelSplitter
from src.sharding.layer_analyzer import LayerAnalyzer
from src.sharding.metadata_manager import ShardMetadata, MetadataManager
from src.sharding.cache_manager import ShardCache, ShardManager
from src.sharding.integrity_checker import (
    IntegrityChecker, VerificationLevel, IntegrityError, 
    CorruptedShardError, SignatureError, HeaderError
)
from src.sharding.preloader import (
    ShardPreloader, PreloadStrategy, PreloaderState,
    get_cpu_usage, predict_next_shard, background_preload
)
from src.sharding.unload_strategy import (
    ShardUnloadStrategy, UnloadPriority, create_unload_strategy
)
from src.sharding.monitor import (
    ShardMonitor, LoadStatus, create_shard_monitor
)
from src.sharding.recovery import (
    ShardRecoveryManager, RecoveryStrategy, RecoveryAction, FailureType,
    handle_load_failure, create_recovery_manager
)

__all__ = [
    'ModelSplitter', 
    'LayerAnalyzer', 
    'ShardMetadata', 
    'MetadataManager',
    'ShardCache',
    'ShardManager',
    'IntegrityChecker',
    'VerificationLevel',
    'IntegrityError',
    'CorruptedShardError',
    'SignatureError',
    'HeaderError',
    'ShardPreloader',
    'PreloadStrategy',
    'PreloaderState',
    'get_cpu_usage',
    'predict_next_shard',
    'background_preload',
    'ShardUnloadStrategy',
    'UnloadPriority',
    'create_unload_strategy',
    'ShardMonitor',
    'LoadStatus',
    'create_shard_monitor',
    'ShardRecoveryManager',
    'RecoveryStrategy',
    'RecoveryAction',
    'FailureType',
    'handle_load_failure',
    'create_recovery_manager'
] 