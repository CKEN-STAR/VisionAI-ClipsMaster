#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时通信模块

提供基于WebSocket和gRPC的双工通信功能，支持实时数据传输和交互。
"""

from src.realtime.duplex_engine import (
    Message, 
    MessageType, 
    ProtocolType,
    DuplexProtocol,
    get_duplex_engine,
    get_delta_broadcaster,
    set_delta_broadcaster,
    initialize_duplex_engine,
    shutdown_duplex_engine
)

from src.realtime.duplex_client import DuplexClient

from src.realtime.session_manager import (
    RealTimeSession,
    SessionStatus,
    SessionManager,
    get_session_manager,
    initialize_session_manager
)

from src.realtime.command_router import (
    CommandRouter,
    CommandHandler,
    CommandResult,
    CommandStatus,
    get_command_router,
    initialize_command_router
)

from src.realtime.delta_broadcaster import DeltaBroadcaster

from src.realtime.op_logger import (
    OperationLogger,
    get_operation_logger,
    initialize_operation_logger
)

from src.realtime.conflict_resolver import (
    OTResolver,
    get_ot_resolver,
    initialize_ot_resolver
)

from src.realtime.latency_optimizer import (
    LagReducer,
    GeoDistributedCache,
    get_lag_reducer,
    initialize_lag_reducer
)

from src.realtime.feedback_loop import (
    BioFeedbackCollector,
    BiometricData,
    BioMetricType,
    WearableSDK,
    get_feedback_collector,
    initialize_feedback_collector
)

from src.realtime.sandbox import (
    InteractionSandbox,
    DockerSandbox,
    SubprocessSandbox,
    get_interaction_sandbox,
    initialize_interaction_sandbox
)

from src.realtime.monitoring import (
    TelemetryDashboard,
    PrometheusClient,
    GrafanaIntegrator,
    get_telemetry_dashboard,
    initialize_telemetry_dashboard
)

__all__ = [
    'Message',
    'MessageType',
    'ProtocolType',
    'DuplexProtocol',
    'DuplexClient',
    'get_duplex_engine',
    'get_delta_broadcaster',
    'set_delta_broadcaster',
    'initialize_duplex_engine',
    'shutdown_duplex_engine',
    'RealTimeSession',
    'SessionStatus',
    'SessionManager',
    'get_session_manager',
    'initialize_session_manager',
    'CommandRouter',
    'CommandHandler',
    'CommandResult',
    'CommandStatus',
    'get_command_router',
    'initialize_command_router',
    'DeltaBroadcaster',
    'OperationLogger',
    'get_operation_logger',
    'initialize_operation_logger',
    'OTResolver',
    'get_ot_resolver',
    'initialize_ot_resolver',
    'LagReducer',
    'GeoDistributedCache',
    'get_lag_reducer',
    'initialize_lag_reducer',
    'BioFeedbackCollector',
    'BiometricData',
    'BioMetricType',
    'WearableSDK',
    'get_feedback_collector',
    'initialize_feedback_collector',
    'InteractionSandbox',
    'DockerSandbox',
    'SubprocessSandbox',
    'get_interaction_sandbox',
    'initialize_interaction_sandbox',
    'TelemetryDashboard',
    'PrometheusClient',
    'GrafanaIntegrator',
    'get_telemetry_dashboard',
    'initialize_telemetry_dashboard'
] 