# Kimi K3.1 Pro 流式补测（2026-10-26）

延续[首轮 67 次验证](volcengine-kimi-k31-verification.md)，精确组合仍为火山订阅套餐 `/api/plan/v3` × `kimi-k3.1-pro`。本轮 **24 个 stream:true 请求：20 Chat Completions、4 Responses**；22 个 HTTP 200 成功建立 SSE，其中 20 个正常结束、2 个故意限制输出后截断；另 2 个请求在建流前 HTTP 400 拒绝。每条件 n=1，无重试，最多双并发，socket timeout 900 秒。全部 22 条 SSE 回显 `kimi-k3-1-pro-261024`。

## 当前支持

| 检查 | 结果 | 正文 |
| --- | --- | --- |
| Chat 文本与思考 | 七档 effort 均正常 stop，答案 38；low/medium/high/xhigh/max 有独立 reasoning_content 增量 | [思考](reasoning.md#kimi-k31-ark) |
| Chat 图片 / PDF | 流式精确读取计数和校验码，各 1/1 | [输入](protocol-differences.md#kimi-k31-ark) |
| Chat strict schema / JSON | 两组冲突枚举 2/2、JSON mode 1/1 正确 | [结构化](structured-output.md#kimi-k31-ark) |
| Chat 工具闭环 | 按 tool_calls.index 累积名称/参数、保留 id 和 reasoning_content，回传后取得 CEDAR-4826 | [工具](tools-and-server-tools.md#kimi-k31-ark) |
| Chat tool_choice | required/none 冲突样本遵从；具名思考模式建流前 400 | [工具](tools-and-server-tools.md#kimi-k31-ark) |
| Responses tool_choice | 流式 required/none/具名三个冲突样本均未遵从，复现首轮差异 | [工具](tools-and-server-tools.md#kimi-k31-ark) |
| 结束 / usage | 全部 22 条 SSE 有 DONE；Chat usage 重复快照不能求和 | [流协议](protocol-differences.md#kimi-k31-ark)、[观测](errors-probing-observability.md#kimi-k31-ark) |
| 输出截断 | Responses incomplete + reason:length；Chat finish_reason:length，均 HTTP 200 | [流协议](protocol-differences.md#kimi-k31-ark) |

“支持流式”不等于所有字段受控，也不代表 HTTP 200 就生成完整答案。首轮已测 Responses 的文本、图片/PDF、schema 和工具闭环，本轮重点补齐 Chat；本轮没有网络中断、取消、重连、长任务、多个并行调用或代理拆包压力测试。

## 逐案观测

秒数从客户端发起请求前计起；“首正文增量”只计非空 content/output_text delta，排除思考和工具参数，未输出正文记 —。这些是小样本时延，不是服务 SLA。reasoning 数值使用最终 usage，不能据此证明七档独立或质量差异。

| case | HTTP | 终态 | reasoning tokens | 首正文增量秒 | 总秒 | 校验 |
| --- | --- | --- | --- | --- | --- | --- |
| s-chat-effort-medium | 200 | stop | 104 | 5.334 | 5.34 | `38` |
| s-chat-effort-low | 200 | stop | 98 | 5.411 | 5.412 | `38` |
| s-chat-effort-high | 200 | stop | 116 | 5.848 | 5.853 | `38` |
| s-chat-effort-xhigh | 200 | stop | 147 | 6.334 | 6.34 | `38` |
| s-chat-effort-none | 200 | stop | 0 | 2.795 | 2.817 | `38` |
| s-chat-effort-minimal | 200 | stop | 0 | 2.938 | 2.977 | `38` |
| s-chat-effort-bogus | 400 | HTTP error | — | — | 0.117 | InvalidParameter |
| s-chat-effort-max | 200 | stop | 141 | 8.887 | 8.889 | `38` |
| s-chat-image | 200 | stop | 59 | 3.307 | 3.506 | `red=3,blue=2` |
| s-chat-pdf | 200 | stop | 28 | 6.539 | 6.543 | `MANGO-7392` |
| s-chat-schema-DELTA | 200 | stop | 85 | 8.05 | 8.08 | `{"code":"DELTA"}` |
| s-chat-schema-ECHO | 200 | stop | 118 | 4.389 | 4.39 | `{"code":"ECHO"}` |
| s-chat-json | 200 | stop | 61 | 4.505 | 4.508 | `{"count": 7}` |
| s-chat-no-usage-option | 200 | stop | 32 | 3.595 | 3.596 | `OK` |
| s-responses-truncated | 200 | incomplete | 13 | — | 1.145 | 预算 16，空正文；正确标记截断 |
| s-chat-truncated | 200 | length | 13 | — | 1.207 | 预算 16，空正文；正确标记截断 |
| s-chat-tool | 200 | tool_calls | 15 | — | 2.909 | tool_calls；label=cedar；参数拼接正确 |
| s-chat-tool-return | 200 | stop | 5 | 2.107 | 2.112 | `CEDAR-4826` |
| s-responses-choice-required | 200 | completed | 35 | 2.576 | 2.576 | 返回 OK，无调用（约束失效） |
| s-responses-choice-none | 200 | completed | 29 | — | 4.521 | 仍调用 lookup_probe（约束失效） |
| s-responses-choice-named | 200 | completed | 39 | — | 4.88 | 调用 other_probe（约束失效） |
| s-chat-choice-required | 200 | tool_calls | 155 | — | 6.404 | 生成工具调用（约束遵从） |
| s-chat-choice-named | 400 | HTTP error | — | — | 0.287 | InvalidParameter |
| s-chat-choice-none | 200 | stop | 155 | 6.862 | 7.172 | 无工具调用（约束遵从） |

## 事件与证据检查

- Chat 18 条实际 SSE 都收到 finish_reason 和 DONE；17 条显式 `stream_options.include_usage:true`，每条在 finish 块及 `choices:[]` 的独立 usage 块出现两份相同快照。省略该选项的 1 条在 finish 块仍有一份 usage；不能推断所有平台都如此。
- Chat 正文按 delta.content 累积、专用思考按 delta.reasoning_content 累积。工具按 index 配对，调用 id 非空且唯一，拼接的 arguments 经 JSON 解析后校验名称和参数。原始专用思考仅在内存保留用于工具结果回传，磁盘已脱敏。
- Responses 3 个正常样本均 completed，1 个截断样本为 incomplete；全部随后有 DONE。文本和 function_call_arguments delta 与终态对象一致。
- 截断样本将输出预算设为 16 token，两面均报告输出 16、reasoning 13、无最终正文；这是预算耗尽，不应归类为“不支持流式”或完整成功。
- Chat `reasoning_effort:bogus` 与思考模式下具名 tool_choice 均为 HTTP 400 JSON 错误，未产生 SSE；没有复现 HTTP 200 内嵌 error，不据此保证其永远不出现。

新增原始 usage 合计输入 **14,140**、输出 **1,950** token；只取一次最终快照，输出含 reasoning。累计两轮 91 次远端请求（84 个 HTTP 200，其中 2 个截断；7 个 400），输入 55,184、输出 7,319 token。平台没有金额字段，未对账。

[脱敏证据](volcengine-kimi-k31-stream-evidence.json) 包含所有请求、原始事件（专用思考脱敏）、每个 JSON 事件到达时间及本地重建 Chat 对象；重建对象明确标记 assembled_from_sse，不冒充服务端非流式回包。附件沿用首轮夹具和哈希。

[探测脚本](../../../scripts/probe_kimi_k31.py) 新增 phase7（16 次：effort、多模态、格式、usage、截断）与 phase8（本次 8 次：工具闭环和双协议冲突）。仍从环境读取 SEEDDACE_KEY，运行前需显式授权额度消耗，不自动进入常规测试。
