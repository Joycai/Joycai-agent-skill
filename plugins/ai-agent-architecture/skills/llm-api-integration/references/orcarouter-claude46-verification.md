# Claude Sonnet 4.6 / Opus 4.6 网关验证（2026-10-25）

【实测】`anthropic/claude-sonnet-4.6`、`anthropic/claude-opus-4.6`，OrcaRouter `/v1/messages`，Bearer 与 anthropic-version: 2023-06-01。每条件 n=1、输出上限 1024，无重试，未执行工具/回传工具结果。沿用此前 $1 预算，先计入已报告 $0.151。

## 方法与来源

- 图片/PDF 使用 [前轮附件](orcarouter-multimodal-effort-verification.md#inputs)，提示不包含答案；仅验证小图片计数、单页文本 PDF 读取。
- Effort：adaptive + output_config.effort，low/medium/high/max；同一道同余算术题，正确答案 38。官方 [effort 页](https://platform.claude.com/docs/en/build-with-claude/effort)（核对 2026-10-25）列两款支持 max，xhigh 支持名单未列这两款，因此本轮不将 xhigh 当合法档位测试。
- 流式提示 STREAM_OK；检查 SSE 文本拼接和 message_stop。schema 提示 green、枚举仅 red，另做相同提示无 schema 基线。
- 工具 auto 提示调用 report(red)；具名/any 则用反向提示“Do not call any tools. Reply with exactly NO_TOOL.”，提供 report/other。具名指定 other。区分参数被接受、是否实际发起工具调用。
- 思考关闭：low + disabled，算术题 17×19，只答 323。若计数为 0，仅证明本题观测，不证明所有题都关闭。

## 逐例结果

| 案例 | HTTP | 正文 / 工具 | 结束 | 思考 token | USD |
| --- | --- | --- | --- | --- | --- |
| sonnet46-image | 200 | `red=3,blue=2` | end_turn | 0 | 0.000444 |
| opus46-image | 200 | `red=3,blue=2` | end_turn | 0 | 0.00074 |
| sonnet46-pdf | 200 | `MANGO-7392` | end_turn | 0 | 0.004966 |
| opus46-pdf | 200 | `MANGO-7392` | end_turn | 0 | 0.008276 |
| sonnet46-effort-low | 200 | `38` | end_turn | 86 | 0.001498 |
| opus46-effort-low | 200 | `38` | end_turn | 0 | 0.00032 |
| sonnet46-effort-medium | 200 | `38` | end_turn | 124 | 0.002068 |
| opus46-effort-medium | 200 | `38` | end_turn | 345 | 0.008946 |
| sonnet46-effort-high | 200 | `**38** /  / **Verification:** / - 38 = 5 × 7 + 3 → 38 mod 7 = **3** ✓ / - 38 = 3 × 11 + 5 → 38 mod 11 = **5** ✓` | end_turn | 225 | 0.004648 |
| opus46-effort-high | 200 | `38` | end_turn | 0 | 0.00032 |
| sonnet46-effort-max | 200 | `**38** /  / **Verification:** / - 38 = 5 × 7 + 3 → 38 mod 7 = 3 ✓ / - 38 = 3 × 11 + 5 → 38 mod 11 = 5 ✓` | end_turn | 363 | 0.006718 |
| opus46-effort-max | 200 | `38` | end_turn | 626 | 0.01597 |
| sonnet46-stream | 200 | `STREAM_OK` | end_turn | 0 | 0.00015 |
| sonnet46-schema | 200 | `{"color":"red"}` | end_turn | 0 | 0.000642 |
| sonnet46-schema-baseline | 200 | ````json / { /   "color": "green" / } / ```` | end_turn | 0 | 0.00034 |
| sonnet46-tool | 200 | `Sure! I'll call the `Report` function with the color **red** right away!` | tool_use | 26 | 0.003202 |
| sonnet46-off | 200 | `323` | end_turn | 未报告 | 0.000138 |
| sonnet46-forced-named | 200 | `NO_TOOL` | end_turn | 0 | 0.002032 |
| sonnet46-forced-any | 200 | `NO_TOOL` | end_turn | 0 | 0.002032 |
| opus46-stream | 200 | `STREAM_OK` | end_turn | 0 | 0.00025 |
| opus46-schema | 200 | `{"color":"red"}` | end_turn | 0 | 0.00107 |
| opus46-schema-baseline | 200 | `{"color": "green"}` | end_turn | 0 | 0.000316 |
| opus46-tool | 200 | `[{"name": "report", "arguments": {"color": "red"}}]` | tool_use | 0 | 0.003936 |
| opus46-off | 200 | `323` | end_turn | 未报告 | 0.00023 |
| opus46-forced-named | 200 | `NO_TOOL` | end_turn | 0 | 0.003386 |
| opus46-forced-any | 200 | `NO_TOOL` | end_turn | 0 | 0.003386 |

本轮 26 次请求，网关报价 **$0.076024**；与此前 $0.151 合计 **$0.227024**，未与账单对账。

[脱敏证据](orcarouter-claude46-evidence.json) 保存具体请求、响应正文/工具、usage、回显与终止标记，不保存密钥、签名或原生思考内容。fixture 占位符对应前轮保存的 PNG / PDF。正常响应只证明所测路由；单题一次不证明 effort 质量或 token 单调。


## 当前结论

- 26 次均 200，正常终止；两个请求 ID 分别回显 claude-sonnet-4-6 / claude-opus-4-6，未出现不同代次回显。
- 两款流式、图片、单页文本 PDF、schema 枚举/无 schema 基线与 auto 工具样例通过。
- 两款 low/medium/high/max 均被接受且答对 38；Sonnet high/max 额外解释，未遵守仅数字，Opus 四档仅答数字。没有 effort 回显，不能证明网关未改写；思考计数不单调。
- disabled 两款均 200，返回 323，usage 不含 thinking_tokens，不能将字段缺失记成显式 0。没有同题 adaptive 对照，因此只证明参数接受和此次无可见思考。
- **强制工具未生效**：adaptive + effort low、反向提示下，具名 other 与 any 各一次都回复 NO_TOOL、无调用；不能把“200”当强制语义支持。只限此组合；其他 effort、thinking 关闭、流式强制、重试及真实工具闭环本轮未测。
- 保留旧渠道/日期的强制工具成功记录；本轮网关证据不改变官方契约，不把一个失败样本扩大到所有调用。
