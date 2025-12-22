# 任务：迁移 FastAPI on_event → lifespan，并增强叙事锚点 API 边界用例

## 背景
pytest 冒烟已通过，但存在 FastAPI @on_event 弃用告警。为消除告警并提升一致性，迁移到 lifespan 事件模型。同时补充叙事锚点 API 的边界用例以稳固行为。

## 改动摘要
- src/server.py：
  - 新增 app_lifespan（asynccontextmanager），在 startup 中尝试集成 realtime；移除 @app.on_event("startup")
  - FastAPI 实例传入 lifespan=app_lifespan
- src/api/api_routes.py：
  - 新增 router_lifespan（asynccontextmanager），封装 DeltaBroadcaster 的初始化/关闭（依赖存在才启用）
  - APIRouter(tags=["clips"], lifespan=router_lifespan)
  - 移除 @router.on_event("startup"/"shutdown")
- tests/api/test_narrative_edges.py：新增 3 个边界用例（空场景/缺字段/字符串强度）

## 风险与兼容性
- Lifespan 与 TestClient 兼容，替换不影响现有路由/中间件。
- Realtime/DeltaBroadcaster 保持可选：失败仅记录日志，不影响主流程启动。

## 验证
- pytest -q tests/api 通过
- /healthz、/api/narrative/detect-anchors 正常

## 后续建议
- 逐步将其它 router 的 on_event 也统一迁移至 lifespan
- 扩展异常路径用例（非法类型、超大输入）

