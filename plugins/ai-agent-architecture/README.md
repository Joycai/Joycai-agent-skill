# ai-agent-architecture

一个插件，五个按任务加载的 skill。插件安装名不变，4.0.0 调整了三个 skill 名称，并拆出媒体 API 接入。

| 任务 | 显式调用 |
| --- | --- |
| 聊天 API 接入、协议兼容、模型能力、流式与排错 | `/ai-agent-architecture:llm-api-integration` |
| 图片/视频生成与 ASR API、上传、轮询、产物与时间码 | `/ai-agent-architecture:ai-media-api-integration` |
| Agent 工具循环、执行权限、子代理、上下文与会话 | `/ai-agent-architecture:agent-runtime-architecture` |
| 凭据、端点、线路、模型参数配置及迁移 | `/ai-agent-architecture:llm-provider-config` |
| 用量、价格快照、成本统计与异步结算 | `/ai-agent-architecture:ai-usage-accounting` |

## 内容归属

- 协议字段、原始 usage 与厂商行为归 API 接入；媒体专有行为归媒体接入。
- 平台/模型能力矩阵给简明结论与正文链接；厂商按平台索引定位，不新增厂商 skill。
- 配置实体和画像结构归供应商配置；用量归一化后的价格和核算规则归成本核算。
- 工具执行、审批、取消与会话生命周期归 runtime。
- 知识维护规范由聊天 API skill 保存，媒体 skill 引用；只有维护请求才写回知识库。

入口只加载当前任务所需资料。参考实现与带日期的证据需区分，历史记录不代表当前所有端点的保证。单纯使用已有工具生成图片不触发 API 工程 skill；图片创作使用独立的 reference-image-studio 插件。

## 4.0.5 更新

新增 Gemini 4 Argon [官方型号与能力](skills/llm-api-integration/references/model-versions.md#gemini-4-argon)及[协议迁移](skills/llm-api-integration/references/protocol-differences.md#gemini-4-argon)知识，区分 Developer API / Google Cloud、Interactions / GenerateContent、长输出与思考预算规则。均为 2026-10-27 核对的官方文档，未做 Argon API 实测。LLM skill 内容版本为 2.2.10。

## 4.0.1 更新

新增火山套餐 `kimi-k3.1-pro` 接入知识，包含 91 次请求的[协议与能力验证](skills/llm-api-integration/references/volcengine-kimi-k31-verification.md)、[流式补测](skills/llm-api-integration/references/volcengine-kimi-k31-stream-verification.md)、脱敏证据及按阶段运行的探测脚本。LLM skill 内容版本为 2.2.9；重点记录 Responses 工具选择约束、思考字段差异、SSE usage 快照及截断终态。

## 从 3.x 迁移

| 原调用 | 新调用 |
| --- | --- |
| `ai-agent-architecture:ai-agent-architecture` | `ai-agent-architecture:llm-api-integration`；媒体任务改用 `ai-agent-architecture:ai-media-api-integration` |
| `ai-agent-architecture:channel-route-model` | `ai-agent-architecture:llm-provider-config` |
| `ai-agent-architecture:llm-billing-model` | `ai-agent-architecture:ai-usage-accounting` |
| `ai-agent-architecture:agent-runtime-architecture` | 不变 |

更新自定义提示词、工作流与引用；旧入口不保留重复别名。原参考文件去掉历史编号，完整路径对应见 [迁移清单](MIGRATION.md)。已有问题编号与证据日期保留，文件迁移不刷新实测日期。

## 检查

在仓库根运行 `python3 plugins/ai-agent-architecture/scripts/validate_structure.py`，检查五个入口、清单版本、内部文件与锚点链接、迁移目标和参考资料可达性。再运行 `claude plugin validate plugins/ai-agent-architecture` 与 `claude plugin validate .` 检查插件格式。

路由场景和人工检查结果见 [验证记录](VALIDATION.md)。结构检查不能证明实际模型的自动选择效果，也不重新验证厂商 API。
