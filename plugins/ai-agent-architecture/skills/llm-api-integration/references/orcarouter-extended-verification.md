# OrcaRouter 协议与能力对照：2026-10-25

> 最新 [Gemini 3.8 重试](#gemini38-retry)：工具与 schema 基线已完成；thinkingBudget=0 仍报告思考计数，不是可靠关闭开关。此前超时保留为历史。

> 最新补测：Gemini 3.6 在 [1,024 token schema 对照](#gemini-schema-1k) 中正常完成；此前 384 token 截断保留为历史。

> Gemini 当前目标已调整为 [3.8 Flash / 3.6 Flash](#gemini-current)。前 51 次测试中的 3.5/3.7 仅为历史记录。

【实测，网关范围】接入点 `https://api.orcarouter.ai`；本轮 51 次请求（37 初测 + 14 基线/对照），每例 n=1，串行、无自动重试，每次输出上限 384 token。8 条可用路由 + Gemini 3.7 可用性检查；47 次 HTTP 200、3 次 400、1 次 404。没有执行模型工具、没有厂商直连对照。

可复现请求、模型回显、文本/工具结果、usage、事件类型及错误见 [脱敏证据 JSON](orcarouter-extended-evidence.json)。未保存密钥、思考原文或签名。基本连通性前测见 [上一轮记录](orcarouter-verification.md)。

## 目录

- [费用与测试判据](#criteria)
- [能力结果](#results)
- [Qwen 身份差异](#qwen-identity)
- [Fable 强制工具差异](#fable-tools)
- [流式与模型回显](#streaming)
- [适用范围](#limits)

<a id="criteria"></a>
## 费用与测试判据

网关报价合计 **$0.075768**；四个错误响应没有费用字段，不能断言免费。预算记账对缺失报价保守预留，共占用 $0.175768，低于 $0.50 停止阈值。此阈值是客户端停止策略，不是供应方硬限额。含上一轮 $0.008740，已报告费用共 $0.084508；均未与账单对账。流式重复累计 usage / cost 只取最终快照，不逐块相加。

- 流式：提示输出 STREAM_OK；实际解析 SSE、拼接正文，并检查终止事件。HTTP 200 不等于流成功。
- 结构化：提示要求 JSON color=green、禁止 red；schema 仅允许 `{color:red}`，额外字段禁止。8 条路由加 schema 都得到 red，无 schema 基线都得到 green（有些带 Markdown 围栏）。只证明本组枚举约束表现，不代表全面 JSON Schema 实现合规。
- 工具：定义本地虚拟 report(color)，auto + 提示要求调用；8 条路由均返回 report 和 `{color:red}`。没有执行工具或回传工具结果，不能宣称跨轮工具闭环已验证。
- 思考：观察参数接受/拒绝、思考计数与文本；计数缺失不能当作显式 0。Qwen 两路、DeepSeek、Gemini 使用同一算术题对照；Opus disabled 无同题开启对照，仅记录接受与 0 计数。

<a id="results"></a>
## 能力结果

全部结论仅针对表中 OrcaRouter 请求 ID 和协议；`qwen` 与 `obsidian` 均非已确认 27B 权重。

| 请求 ID | 协议 | 流式正文/终止 | schema 对照 | auto 工具 | 思考控制 |
| --- | --- | --- | --- | --- | --- |
| `openai/gpt-6.1-sol` | Responses | 通过 | red / 基线 green | report(red) | low 请求成功；none → 400，网关通用 upstream_rejected_request |
| `anthropic/claude-opus-4.8` | Messages | 通过 | red / green | report(red) | disabled → 200，thinking_tokens=0 |
| `anthropic/claude-fable-5` | Messages | 通过 | red / green | report(red) | disabled → 400，提示用 adaptive |
| `anthropic/claude-fable-5.1` | Messages | 通过 | red / green | report(red) | disabled → 400；bogus → 200，thinking_tokens=3 |
| `google/gemini-3.5-flash` | Gemini | 通过 | red / green，但 schema finishReason=MAX_TOKENS | report(red) | LOW 同题 thoughtsTokenCount=99；thinkingBudget=0 后字段缺失，total=prompt+candidates，不能直接记显式 0 |
| `qwen/qwen3.8-27b` | Chat Completions | 通过 | red / green | report(red) | 顶层 enable_thinking=false 后无 reasoning 内容/计数字段；同题默认 reasoning_tokens=41 |
| `obsidian/Qwen3.8-27B` | Chat Completions | 通过 | red / green | report(red) | 同上；默认 reasoning_tokens=43 |
| `deepseek/deepseek-v4.1-flash-1017` | Chat Completions | 通过 | red / green | report(red) | thinking.type=disabled，reasoning_tokens=0；同题默认=19 |

Gemini schema 虽得到完整、可解析的 red JSON，仍触发输出上限；保留 finishReason，不标作正常完成。DeepSeek 此次网关接受 json_schema 并满足枚举，与旧官方 json_object 知识区分，不能据此升级官方能力。

<a id="qwen-identity"></a>
## Qwen 身份差异

两条 27B 目录路由各 6 次请求（流式、schema、工具、关闭思考、schema 基线、思考基线），**12/12 均回显 `qwen3.8-flash`**。两条路由的费用不同，参数行为近似。这证明回显与请求标识稳定不一致，不能证明实际权重相同或都是 Flash，也不能认证 27B。

保持请求 ID、响应 model、平台与时间分开；不要在模型配置或计费归属中用回显自动覆盖用户选定的请求 ID。顶层 enable_thinking 在这两条网关路由中的行为不能代替官方开源部署的 chat_template_kwargs 规则。真实后端与模型回显字段语义仍需供应方解释，本轮没有发送外部询问。

<a id="fable-tools"></a>
## Fable 强制工具差异

对应证据 `fable51-contrast-*`。共同提示为“Do not call any tools. Reply with exactly NO_TOOL.”；同时提供 report 和 other 两个同 schema 工具。

| tool_choice | 模式 | 结果 |
| --- | --- | --- |
| auto | 非流式 | 200，NO_TOOL，无调用 |
| none | 非流式 | 200，NO_TOOL，无调用（仅证明此提示下结果） |
| tool, name=other | 非流式 | 200，other({color:red})，stop_reason=tool_use |
| tool, name=other | 流式 | 200，拼接 input_json_delta 得到 other({color:red})，message_stop |
| any | 非流式 | 200，NO_TOOL，无调用：**所测样例未强制执行** |

具名强制有非流式/流式各一条有效对照；any 的失败样本只有一次，不推断永远失效。旧的“强制工具支持”应拆为“参数被接受”和“具体取值的语义是否生效”。非法 thinking.type=bogus 也 200，证明这条网关不严格遵循官方该项校验；不能仅凭此确定网关删字段、提示词注入或真实后端变更。

[官方文档](tools-and-server-tools.md#official-model-updates) 对 Fable 5.1 的 any / tool 都规定 400；本次网关观测与其并列，不修改官方契约。没有测试手动 enabled + budget_tokens，此项旧冲突仍待复核。

<a id="streaming"></a>
## 流式与模型回显

- Responses：response.output_text.delta 拼接；response.completed 带最终 usage。
- Messages：content_block_delta 拼接；message_delta 给最终 usage，message_stop 终止。强制工具流解析 input_json_delta，不能当正文 text_delta。
- Chat Completions：choices[].delta.content 拼接；include_usage=true，下游需处理空 choices 的 usage 块与 [DONE]。
- Gemini：本例两个 SSE 数据块，最终 STOP；两块重复 usage，不能累加。
- Gemini 3.5 请求：本轮除工具样例回显 `gemini-3.5-flash` 外，其余 5 条回显 `gemini-3.6-flash`。这与前测统一回显 3.6 的简化印象不同；当前只记请求条件下的回显差异，不能确定真实路由原因或权重。
- Gemini 3.7：一次请求返回 404 / model_not_found，正文称无容量、metadata.reason 为 err_model_unknown；停止后续能力测试，不推断永久下线。

<a id="limits"></a>
## 适用范围

本轮各条件单次采样；不保证所有提示/时间/账户一致。未验证长上下文、视觉、流式 schema、完整工具回传闭环、官方直连、真实模型权重。使用 [官方版本记录](model-versions.md) 与本报告时保持“官方文档”及“网关实测”标签分离。


<a id="gemini-current"></a>
## Gemini 当前验证范围：3.8 Flash 与 3.6 Flash

用户于 2026-10-25 明确将 Gemini 验证范围限定为 `google/gemini-3.8-flash` 与 `google/gemini-3.6-flash`。上文 3.5/3.7 仅作历史记录，不作为当前目标的替代测试。官方生命周期资料保留。

【网关实测】本轮 12 个样例，每条件 n=1，Gemini 原生协议；每次输出上限 384，串行、无重试，工具不执行。响应与请求参数见 [脱敏证据](orcarouter-gemini-current-evidence.json)。超时不证明服务端未执行或未收费。

| 案例 | HTTP | 回显 | 正文 / 工具 | 结束 / 错误 | 报价 USD |
| --- | --- | --- | --- | --- | --- |
| gemini38-stream | 200 | gemini-3.8-flash | `STREAM_OK` | STOP | 1.6e-05 |
| gemini38-schema | 200 | gemini-3.8-flash | `{"color":"red"}` | STOP | 0.000778 |
| gemini38-tool | 未收到 | — | `—` | timeout | 未知 |
| gemini38-off | 200 | gemini-3.8-flash | `323` | STOP | 2.2e-05 |
| gemini36-stream | 200 | gemini-3.6-flash | `STREAM_OK` | STOP | 0.000284 |
| gemini36-schema | 200 | gemini-3.6-flash | `{"color":"red` | MAX_TOKENS | 0.00139 |
| gemini36-tool | 200 | gemini-3.6-flash | `[{"name": "report", "arguments": {"color": "red"}}]` | STOP | 7.2e-05 |
| gemini36-off | 200 | gemini-3.6-flash | `323` | STOP | 2.4e-05 |
| gemini38-schema-baseline | 未收到 | — | `—` | timeout | 未知 |
| gemini38-thinking-baseline | 未收到 | — | `—` | timeout | 未知 |
| gemini36-schema-baseline | 200 | gemini-3.6-flash | `{   "color": "green" }` | STOP | 0.000556 |
| gemini36-thinking-baseline | 200 | gemini-3.6-flash | `323` | STOP | 0.00057 |

网关已报告费用 **$0.003712**；缺失报价和超时费用未知，未与账单对账。SSE 的重复 usage 不相加。


本轮结论：

- 3.8 / 3.6 各一条流式样例均拼出 STREAM_OK 并以 STOP 收尾；9 个成功响应的 modelVersion 全部与请求型号一致。
- 3.8 schema 样例为合法 red JSON / STOP；无 schema 基线超时，因此不宣称完整对照通过。工具和同题思考基线也超时，相关能力本轮未完成确认。
- 3.6 工具返回 report({color:red}) / STOP；schema 样例 MAX_TOKENS，正文不完整、JSON 无法解析，不能据此判定不支持 schema。无 schema 基线正常返回 green。
- 两款 thinkingBudget=0 均返回 323，thoughtsTokenCount 缺失且 total=prompt+candidates；3.6 的 LOW 同题基线计数为 146，3.8 同题基线超时。只记录这组参数/观测，不将字段缺失写成显式 0，也不推翻旧不同日期/请求条件下“预算 0 仍思考”的记录。
- 9 个 HTTP 200、3 个客户端 timeout；不重试。用量缺失时保守预留后预算占用 $0.048712，已报告金额 $0.003712，不宣称实际总费用上限。


<a id="gemini-schema-1k"></a>
## Gemini 3.6 schema：1,024 token 补测

【网关实测 2026-10-25】用户允许提高输出上限后，针对当前范围内唯一因 MAX_TOKENS 未完成的 schema 样例补测。请求 ID `google/gemini-3.6-flash`，Gemini 原生协议，LOW，maxOutputTokens 从 384 改为 1024；提示词/schema 保持原样，另做同上限无 schema 基线，每条件 n=1，无重试。

| 条件 | HTTP / finishReason | 正文 | thoughtsTokenCount | 报价 USD |
| --- | --- | --- | --- | --- |
| schema 仅允许 red，提示要求 green | 200 / STOP | {"color":"red"} | 318 | 0.001220 |
| 相同提示，无 schema | 200 / STOP | {"color":"green"} | 128 | 0.000530 |

两条回显均为 gemini-3.6-flash。解析并核对 JSON 后，本组枚举约束对照通过，关闭“3.6 schema 因低上限而未完成”这一缺口；不代表完整 JSON Schema 合规或所有请求必然成功。采样具有波动，不能由本次计数推导 384 必定不够或 1024 普遍足够。旧 MAX_TOKENS 样例保留，接入仍须检查终止原因和 JSON 完整性。

补测报价共 **$0.001750**，未对账；详情在 [证据 JSON](orcarouter-gemini-current-evidence.json) 的 followup_1k。3.8 schema 已正常完成，其工具与基线超时属于另一原因，本次未重试。3.5/3.7 不在当前验证范围内。


<a id="gemini38-retry"></a>
## Gemini 3.8 Flash：超时项重试（2026-10-25）

【网关实测】用户授权重试后，工具、schema、无 schema 基线、思考 LOW 基线、thinkingBudget=0 共 5 个请求；与此前相应请求仅将 maxOutputTokens 改为 1024。无自动循环重试，全部 200 / STOP，modelVersion 全为 gemini-3.8-flash。

| 条件 | 结果 |
| --- | --- |
| schema 仅允许 red，提示要求 green | 完整合法 JSON color=red |
| 相同提示，无 schema | Markdown JSON 围栏内 color=green |
| 普通函数工具 | report({color:red})，未执行工具 |
| thinkingLevel=LOW，同题 17×19 | 正文 323，thoughtsTokenCount=69 |
| thinkingBudget=0，同题 17×19 | 正文 323，thoughtsTokenCount=132 |

工具调用与 schema 枚举对照缺口已补齐；工具结果回传闭环未测。**thinkingBudget=0 被接受不等于关闭思考**：本次明确报告 132 个思考 token，前次同类请求未报告该字段，保留两次观测，不将缺失计数推断为稳定关闭。不能用一次高低计数比较证明 LOW 与预算 0 的强度关系。

本轮报价 **$0.001850**；与此前预算周期已报告 $0.227024 合计 **$0.228874**，未对账。详细请求、usage 和响应见 [证据 JSON](orcarouter-gemini-current-evidence.json) 的 gemini38_retry_1k。
