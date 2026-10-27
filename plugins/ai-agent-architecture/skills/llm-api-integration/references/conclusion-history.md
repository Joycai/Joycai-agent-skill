# 结论历史

此处保存被替代的判断，不作为当前能力依据。迁移日期不是重新验证日期。原始记录没有完整日志定位的，来源标记为待补；不虚构证据。其余正文仍含带日期的历史对照，后续修改对应事实时按知识维护规范逐条归档。

## HIST-MEDIA-001

**旧：「透明模式锁死原图 alpha 遮罩」→ 新：主体可变形、只保证结果背景透明（2026-09-23 箭头改向实测推翻）**

来源：原媒体矩阵对应行（原始日志位置待补）。当前结论见 [媒体矩阵](../../ai-media-api-integration/references/media-matrix.md)。归档：2026-10-25。

## HIST-MEDIA-002

——旧：「最多 3 张」→ 新：按 5 截断（2026-09-21 推翻）

来源：原媒体矩阵对应行（原始日志位置待补）。当前结论见 [媒体矩阵](../../ai-media-api-integration/references/media-matrix.md)。归档：2026-10-25。

## HIST-ACCOUNTING-001 · 原核算实现的精度取舍

迁移前 pricing-rules 的 token 说明同时维护协议字段和固定价格。字段事实统一移交 API usage 正文；原项目“不区分图像/文本输入单价”“缓存写没有第四个价就归全价桶”是旧实现取舍，不应当作精确核算规则。原始内容可在 Git 的 3.x 对应文件追溯；没有新增 API 实测。当前规则见 [核算规则](../../ai-usage-accounting/references/pricing-rules.md)。

## HIST-CAPABILITY-001

旧：显式 `strict:true` 才丢（第八个样本）→ 新：不论写不写都丢（2026-09-24）

当前表述：不论是否发送 `strict:true` 都丢（2026-09-24）。

来源：原模型能力矩阵对应条目；原始日志位置待补。当前结论见 [模型矩阵](model-capability-matrix.md)。归档：2026-10-25，不代表重新验证。

## HIST-CAPABILITY-002

旧：sol 发 `max` 回显 `none` 且 0 推理 token → 2026-09-24 另一台四上游未复现（按「当时当档」理解）

当前表述：sol 的跨网关 `max` 行为未统一：2026-09-24 另一台四上游未复现原观测，按当时渠道判断。

来源：原模型能力矩阵对应条目；原始日志位置待补。当前结论见 [模型矩阵](model-capability-matrix.md)。归档：2026-10-25，不代表重新验证。

## HIST-CAPABILITY-003

旧：显式 `strict:true` 才丢 `text.format` → 新：2026-09-24 同台 `[Pro]` 不论写不写都丢

当前表述：2026-09-24 同台 `[Pro]` 不论是否发送 `strict:true` 都丢 `text.format`。

来源：原模型能力矩阵对应条目；原始日志位置待补。当前结论见 [模型矩阵](model-capability-matrix.md)。归档：2026-10-25，不代表重新验证。

## HIST-CAPABILITY-004

旧：④ 只有 cue → 新：2026-09-26 更正。

当前表述：2026-09-26 已更正为原生结构化输出。。

来源：原模型能力矩阵对应条目；原始日志位置待补。当前结论见 [模型矩阵](model-capability-matrix.md)。归档：2026-10-25，不代表重新验证。

## HIST-CAPABILITY-005

旧：2026-09-26 前 off → `MINIMAL` → 新：`LOW`。

当前表述：参考实现 off 映射为 `LOW`（2026-09-26）。。

来源：原模型能力矩阵对应条目；原始日志位置待补。当前结论见 [模型矩阵](model-capability-matrix.md)。归档：2026-10-25，不代表重新验证。

## HIST-CAPABILITY-006

旧：⚠ → 新：见上两行

当前表述：已测子集见上两行。

来源：原模型能力矩阵对应条目；原始日志位置待补。当前结论见 [模型矩阵](model-capability-matrix.md)。归档：2026-10-25，不代表重新验证。

## HIST-CAPABILITY-007

——旧：「`file_url` 仅 ② 且只在按量 base」→ 新：三面都通（2026-09-23）

当前表述：（2026-09-23，三面均通过）。

来源：原模型能力矩阵对应条目；原始日志位置待补。当前结论见 [模型矩阵](model-capability-matrix.md)。归档：2026-10-25，不代表重新验证。

## HIST-CAPABILITY-008

旧：思考**默认关**、真关 → 新（2026-09-28）：**按型号**

当前表述：2026-09-28 观测：**按型号**。

来源：原模型能力矩阵对应条目；原始日志位置待补。当前结论见 [模型矩阵](model-capability-matrix.md)。归档：2026-10-25，不代表重新验证。

## HIST-CAPABILITY-009

旧：一次 $0.028 按请求 → 新：按条

当前表述：按查询条数核算。

来源：原模型能力矩阵对应条目；原始日志位置待补。当前结论见 [模型矩阵](model-capability-matrix.md)。归档：2026-10-25，不代表重新验证。


<a id="hist-probe-status-20261025"></a>
## 2026-10-25 验证任务状态沿革

以下是当日逐轮记录，包含后来已关闭的超时/上限缺口，不是当前待办。当前状态见 [待核实项](open-questions.md#current-probe-status)。

## 2026-10-25 官方文档补充后的待复核项

- **OQ-MODEL-001 / CONFLICT-ANT-051**：Fable 5.1 的强制工具、enabled + budget_tokens：当前官方文档拒绝，旧 OrcaRouter 记录成功。需分别抓官方直连与网关的请求、响应、模型 ID 和时间；本次未执行。当前接入遵循 [官方规则](tools-and-server-tools.md#official-model-updates)，保留原网关观测。
- **OQ-MODEL-002**：Qwen3.8-27B 托管生产 ID、地区与上线状态未核实；[官方权重卡](model-versions.md#qwen-27b) 不能证明 DashScope 已部署同名服务。
- **OQ-MODEL-003**：旧 Gemini ID 在第三方网关是否跟随官方路由、DeepSeek 旧别名实测实际权重均未核实；记录原请求 ID，不凭当前映射改写历史。


### OrcaRouter 2026-10-25 跟进

- OQ-MODEL-001：本轮网关再次接受 Fable 5.1 强制工具请求；仍无官方直连对照，不关闭冲突。见 [ORCA-1025-08](orcarouter-verification.md)。
- OQ-MODEL-003：Gemini 3.5 网关已观测回显 3.6；3.7 未测，DeepSeek 历史权重仍不可反推。
- OQ-MODEL-004：Qwen 27B 目录 ID 调用回显 Flash，需供应方说明路由、实际权重及回显字段语义。当前只标记“路由可用、模型身份未确认”。


### 2026-10-25 扩展验证跟进

- OQ-MODEL-001：Fable 具名强制非流式/流式各一例有效，any 一例无调用，bogus thinking 200。官方冲突未关闭，手动预算未测；见 [扩展验证](orcarouter-extended-verification.md#fable-tools)。
- OQ-MODEL-003：Gemini 3.5 工具样例回显 3.5，其余 5 例回显 3.6；3.7 本次 404。需查清网关按请求条件的路由/回显语义。
- OQ-MODEL-004：Qwen 两个 27B 路由扩展测试 12/12 回显 Flash，身份问题持续存在；见 [身份对照](orcarouter-extended-verification.md#qwen-identity)。


### Gemini 当前范围调整

仅继续验证 google/gemini-3.8-flash 与 google/gemini-3.6-flash；3.5/3.7 旧记录保留。当前待核实：3.8 工具与两项基线超时；3.6 schema 在 384 输出预算下截断；不得将这些结果推广成模型不支持。详见 [本轮证据](orcarouter-extended-verification.md#gemini-current)。


Gemini 3.6 的低输出上限 schema 缺口已通过 [1,024 token 补测](orcarouter-extended-verification.md#gemini-schema-1k) 补齐；3.8 的超时项仍待核实。


### 2026-10-25 图片/PDF/effort 补测

9 条目标路由的小图片、单页文本 PDF 与 35 个 effort 条件均已实测，见 [当前汇总](model-support-status.md)。原“未测”只适用于之前测试轮次；复杂文档、实际档位映射、真实权重与工具闭环仍未确认。Qwen 27B 身份问题保留，Fable 强制工具契约差异保留，Gemini 3.8 之前的工具/基线超时不由多模态测试消除。


### OQ-C46-001：4.6 系强制工具条件差异

OrcaRouter Messages 上 Sonnet/Opus 4.6 在 adaptive+low、反向提示下，具名/any 都未触发调用。其他 thinking 模式与 effort、强制工具流式、跨轮闭环未测。见 [26 条记录](orcarouter-claude46-verification.md)，不覆盖旧平台/渠道观测。


### Gemini 3.8 超时项重试结论

工具、schema 无约束基线、思考 LOW 基线已在授权重试中完成，关闭这三个“未取得结果”的缺口。预算 0 仍返回 132 思考 token；保留前次缺失字段观测，不能认定稳定关闭。见 [重试证据](orcarouter-extended-verification.md#gemini38-retry)。

<a id="minimax-h3-billing-history"></a>
## 2026-10-27：MiniMax H3 视频计量与计费分离

旧视频正文、媒体矩阵及横切规则将 H3“秒数 + token 双口径”解释为相加计费。旧记录标注 2026-08-29 Joycai 实测，但未提供该计费推断的账单或原始日志位置。2026-10-27 官方查询 schema 明确视频 token 由用量折算；定价页以输入/输出视频秒数与超额图片收费，Context-IR 才单独按 tokens 定价。当前结论与官方来源见 [FACT-MINIMAX-VIDEO-004](../../ai-media-api-integration/references/video-generation.md#minimax-h3-v2)。这是纠正计费推断，不是否定历史任务返回过 token 字段。

<a id="grok-video-retirement"></a>
## HIST-MEDIA-003 · Grok 初代下线与统一单价

旧正文和矩阵写“初代 `grok-imagine-video` 已下线（2026-09-22），不再追”，来源 Joycai，原始日志待补。2026-10-27 核对官方总览仍列初代及其编辑/延长能力，因此不能继续作为全平台下线结论；本轮未实测初代账号可用性。旧 1.5 $0.080/s 仅来自 480p 样本，当前文档已列分辨率分档价格。历史样本保留，当前结论见 [FACT-XAI-VIDEO-001–005](../../ai-media-api-integration/references/video-generation.md#grok-imagine-video)。
