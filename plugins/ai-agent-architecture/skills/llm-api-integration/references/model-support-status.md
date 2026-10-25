# 当前模型支持情况（OrcaRouter，2026-10-25）

本表汇总本次会话中的网关实测；不是厂商官方支持表，也不是实际权重认证。✅ 表示所测样例通过，不能扩大为所有输入/提示均成功。图片为 300×160 几何图，PDF 为单页文本文件。effort 每档一个问题、1,024 输出上限，成功表示请求被接受、正确回答并正常结束；不能由此证明档位没有被改写或高档质量更好。

| 请求模型 | 协议 | 流式 | 图片 | PDF | Effort / thinking | 工具调用 | 结构化输出 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `openai/gpt-6.1-sol` | Responses | ✅ | ✅ | ✅ | low/medium/high/xhigh/max 均通过且回显同档；none 旧测 400 | auto ✅ | schema/基线 ✅ |
| `anthropic/claude-sonnet-4.6` | Messages | ✅ | ✅ | ✅ | low/medium/high/max 正常答对；high/max 附解释；disabled 接受、计数未报告 | auto ✅；adaptive+low 下具名/any 对照未强制 | schema/基线 ✅ |
| `anthropic/claude-opus-4.6` | Messages | ✅ | ✅ | ✅ | low/medium/high/max 正常答对；disabled 接受、计数未报告 | auto ✅；adaptive+low 下具名/any 对照未强制 | schema/基线 ✅ |
| `anthropic/claude-opus-4.8` | Messages | ✅ | ✅ | ✅ | low/medium/high/xhigh/max 均通过；disabled 旧测接受、计数 0 | auto ✅ | schema/基线 ✅ |
| `anthropic/claude-fable-5` | Messages | ✅ | ✅ | ✅ | low/medium/high/xhigh/max 均通过；disabled 旧测 400 | auto ✅ | schema/基线 ✅ |
| `anthropic/claude-fable-5.1` | Messages | ✅ | ✅ | ✅ | 五档均正常回答；low/medium 额外输出解释；disabled 旧测 400；bogus 却接受 | auto ✅；具名强制流式/非流式各通过；any 样例未强制 | schema/基线 ✅ |
| `google/gemini-3.8-flash` | Gemini | ✅ | ✅ | ✅ | LOW/MEDIUM/HIGH 均通过；预算 0 最新实测仍有 132 思考 token，不能可靠关闭 | ✅ 普通调用（重试成功） | schema/基线 ✅（1024 重试） |
| `google/gemini-3.6-flash` | Gemini | ✅ | ✅ | ✅ | LOW/MEDIUM/HIGH 均通过；旧测预算 0 后不报告思考计数 | ✅ | schema/基线 ✅（1024 补测） |
| `qwen/qwen3.8-27b` | Chat Completions | ✅ | ✅ | ✅ | low/medium/xhigh 均通过；enable_thinking=false 旧测后不返回思考内容/计数 | auto ✅ | schema/基线 ✅ |
| `obsidian/Qwen3.8-27B` | Chat Completions | ✅ | ✅ | ✅ | low/medium/xhigh 均通过；同上 | auto ✅ | schema/基线 ✅ |
| `deepseek/deepseek-v4.1-flash-1017` | Chat Completions | ✅ | ✅ | ✅ | low/high/max 均通过；disabled 旧测计数 0 | auto ✅ | 网关 schema/基线 ✅ |

## 必须保留的边界

- **Qwen 身份未确认**：上述两个 27B 请求 ID 在此次图片/PDF/effort 样例中仍回显 qwen3.8-flash。所有 ✅ 只记录路由行为，不认证 27B 权重，不将回显自动写回用户配置的请求 ID。
- **Fable 官方与网关分开**：官方文档规定 Fable 5.1 强制 tool/any 返回 400；本库网关观测是具名强制有效、any 样例未强制且均 200。原因未查明。
- **多模态范围有限**：未验证扫描 PDF、复杂版面、多页/超大文件、公网 URL。网关可能预处理 PDF，文件内容读取成功不证明模型原生 PDF 编码。
- **工具闭环未测**：验证了调用名和参数；未执行工具、未回传工具结果。流式 ✅ 为文本流，不能自动扩展为流式 schema 或所有工具流。
- **Gemini 范围**：仅 3.8/3.6；3.5/3.7 保留历史。3.8 工具与结构化基线已在后续授权重试中完成；历史超时不删除。

## 证据与状态

- [图片、PDF 与 effort 本轮记录](orcarouter-multimodal-effort-verification.md)：输入、35 个 effort 条件、思考 token、费用与脱敏证据。
- [流式、工具、结构化与思考开关](orcarouter-extended-verification.md)：前轮对照和 Fable 强制差异。
- [Gemini 当前范围](orcarouter-extended-verification.md#gemini-current)、[3.6 schema 1024 补测](orcarouter-extended-verification.md#gemini-schema-1k)。
- [官方型号与版本](model-versions.md)：官方文档结论不因网关成功而改写。

新增 [Sonnet / Opus 4.6 的 26 条实测](orcarouter-claude46-verification.md)：强制工具结果按 adaptive+low 组合限定，不与其他型号未显式 effort 的条件混为同一对照。

[Gemini 3.8 重试证据](orcarouter-extended-verification.md#gemini38-retry)：5 次正常完成，思考预算 0 仍计费思考。

当前未决问题与已关闭缺口统一维护在 [验证状态](open-questions.md#current-probe-status)，历史报告中的“未测/待重试”仅代表该轮当时状态。
