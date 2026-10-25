# 火山套餐 Kimi K3.1 Pro 验证（2026-10-26）

**后续更新：** [24 次流式补测](volcengine-kimi-k31-stream-verification.md) 已补齐 Chat SSE、多模态、结构化与工具闭环，并验证 usage 重复快照和截断终态。以下数字及未测项描述首轮范围，当前结论以主题正文及补测为准。

精确组合：火山方舟订阅套餐 `https://ark.cn-beijing.volces.com/api/plan/v3` × Responses / Chat Completions × 请求 ID `kimi-k3.1-pro`。优先验证 Responses；不查询 model 列表。62 个成功响应均回显 `kimi-k3-1-pro-261024`，仅表示响应版本声明，不认证权重身份。

共 **67 次远端请求：47 Responses（11 流式）、20 Chat（全部非流式）**；62 次 HTTP 200 且正常结束，5 次 HTTP 400。另有 1 次本地网络失败，不计远端样本。每条件默认 n=1，重复样本单列；输出上限 4096（最初基线 2048），socket timeout 900 秒，最多双并发，不自动重试。只验证本线路，不外推 `/api/coding/v3`、按量 API 或 Moonshot 直连；没有应用 adapter，属于协议探测，不宣称端到端产品集成通过。

## 接入结论与正文索引

| 能力 | 当前结论 | 事实正文 |
| --- | --- | --- |
| 文本与流式 | Responses 可用，11 条 SSE 终态与 delta 重建通过 | [FACT-KIMI-PROTOCOL-001](protocol-differences.md#kimi-k31-ark) |
| effort | 两面 7 档均被接受；映射和关闭有差异，不认证七档独立 | [FACT-KIMI-REASON-001–003](reasoning.md#kimi-k31-ark) |
| 图片 / PDF | 内联夹具 6/6 读取正确 | [FACT-KIMI-INPUT-001](protocol-differences.md#kimi-k31-ark) |
| JSON Schema | 冲突枚举 + 禁额外字段 5/5；JSON mode 2/2 | [FACT-KIMI-SCHEMA-001](structured-output.md#kimi-k31-ark) |
| 函数工具闭环 | Responses 非流式/流式和 Chat 共 3 个闭环成功 | [FACT-KIMI-TOOL-001](tools-and-server-tools.md#kimi-k31-ark) |
| tool_choice | Responses 冲突样本未遵从；Chat required/none 通过，具名思考模式 400 | [FACT-KIMI-TOOL-002](tools-and-server-tools.md#kimi-k31-ark) |
| 会话续接 | 本轮默认 store:false；显式 true 后 previous_response_id 续接成功 | [FACT-KIMI-STATE-001](protocol-differences.md#kimi-k31-ark) |
| 采样 / 用量 | temperature:0.2 两面均拒绝；usage 无金额 | [FACT-KIMI-OBS-001](errors-probing-observability.md#kimi-k31-ark) |

实际接入建议以 Responses + `low/high/max` 为起点，省略固定采样字段；SSE 分开处理 reasoning、正文、函数参数与终态。函数工具可用，但调用执行端必须自行检查允许的工具名和参数；业务硬性依赖 required/none 时，参考 Chat 的已测范围，不能将 Responses 的 tool_choice 当执行边界。不要把客户端超时当服务端停止生成的确认。

最小请求（Bearer 密钥仅由本地环境提供）：

```json
{
  "model": "kimi-k3.1-pro",
  "input": "Reply with exactly OK.",
  "reasoning": {"effort": "low"},
  "max_output_tokens": 4096,
  "stream": true,
  "store": false
}
```

该示例组合用于接入说明；逐案实际请求以证据 JSON 为准。需要服务端保存历史时改为 `store:true`；否则在后续请求中回传完整合法历史。

<a id="efforts"></a>
## Effort 对照与组合样本

统一题：最小正整数 n 满足 n mod 7 = 3、n mod 11 = 5，仅回答整数；期望 38，答案未传入请求。下表数值只是此题观测，不作速度、质量或档位映射排名。R=Responses，C=Chat；S=流式，N=非流式。默认样本与关闭组合均列出，便于区分字段接受、回显和输出通道。

| case | HTTP | 模式 | reasoning tokens | effort / thinking 回显 | 输出校验 |
| --- | --- | --- | --- | --- | --- |
| r-effort-low | 200 | R/N | 99 | low/— | 38（精确） |
| r-effort-high | 200 | R/N | 105 | high/— | 38（精确） |
| r-effort-medium | 200 | R/N | 56 | medium/— | 38（精确） |
| r-effort-max | 200 | R/N | 119 | max/— | 38（精确） |
| r-effort-minimal | 200 | R/N | 0 | minimal/— | 38（精确） |
| r-effort-none | 200 | R/N | 0 | none/— | 38（精确） |
| r-effort-xhigh | 200 | R/N | 174 | xhigh/— | 38（精确） |
| r-effort-bogus | 200 | R/N | 107 | medium/— | 38（精确） |
| r-thinking-disabled | 200 | R/N | 0 | —/disabled | 38（精确） |
| r-effort-default | 200 | R/N | 201 | —/enabled | 38（精确） |
| c-effort-low | 200 | C/N | 72 | —/— | 38（精确） |
| c-effort-medium | 200 | C/N | 139 | —/— | 38（精确） |
| c-effort-high | 200 | C/N | 76 | —/— | 38（精确） |
| c-effort-xhigh | 200 | C/N | 156 | —/— | 38（精确） |
| c-effort-max | 200 | C/N | 156 | —/— | 38（精确） |
| c-effort-minimal | 200 | C/N | 0 | —/— | 38（精确） |
| c-effort-bogus | 400 | C/N | — | —/— | InvalidParameter |
| c-effort-none | 200 | C/N | 0 | —/— | 普通正文含推导，未遵守仅数字 |
| r-effort-none-repeat2 | 200 | R/N | 0 | none/— | 38（精确） |
| r-effort-minimal-repeat2 | 200 | R/N | 0 | minimal/— | 普通正文含推导，未遵守仅数字 |
| r-effort-bogus-repeat2 | 200 | R/N | 81 | medium/— | 38（精确） |
| r-disabled-repeat2 | 200 | R/N | 0 | —/disabled | 普通正文含推导，未遵守仅数字 |
| r-effort-none-repeat3 | 200 | R/S | 0 | none/— | 普通正文含推导，未遵守仅数字 |
| r-effort-minimal-repeat3 | 200 | R/S | 0 | minimal/— | 38（精确） |
| r-disabled-repeat3 | 200 | R/S | 0 | —/disabled | 38（精确） |
| r-effort-bogus-repeat3 | 200 | R/S | 56 | medium/— | 38（精确） |
| r-enabled-none | 200 | R/N | 123 | none/enabled | 38（精确） |
| r-enabled-minimal | 200 | R/N | 120 | minimal/enabled | 38（精确） |
| r-enabled-low | 200 | R/N | 50 | low/enabled | 38（精确） |
| r-disabled-high | 200 | R/N | 0 | high/disabled | 38（精确） |

官方对照及解释只在 [reasoning 正文](reasoning.md#kimi-k31-ark) 维护。`none/minimal/disabled` 的 0 reasoning 计数与正文推导并存，不能将“无专用思考输出”写成“模型没有推理”。

<a id="inputs"></a>
## 多模态与流式证据

夹具复用 [300×160 PNG](../assets/api-probes/probe-shapes.png)（3 红方块、2 蓝圆）及 [单页文本 PDF](../assets/api-probes/probe-code.pdf)（DOC-CODE: MANGO-7392）。请求内联原文件，SHA-256 见 JSON 的 fixtures。图像只问计数，PDF 只问校验码；两者均未在提示提供答案。

| case | HTTP | 最终文本 | 秒 |
| --- | --- | --- | --- |
| r-image | 200 | `red=3,blue=2` | 3.064 |
| r-image-stream | 200 | `red=3,blue=2` | 3.851 |
| r-pdf-stream | 200 | `MANGO-7392` | 5.15 |
| r-pdf | 200 | `MANGO-7392` | 6.074 |
| c-image | 200 | `red=3,blue=2` | 3.894 |
| c-pdf | 200 | `MANGO-7392` | 6.011 |

11 条 Responses SSE 均校验 `response.completed`、`[DONE]` 及普通文本 delta；含函数的流再校验按 item_id 拼接 arguments 与终态 JSON 相等。首次收到任意流行耗时 1.450–4.260 秒，这不是首个答案 token 延迟，也未必是首字节延迟。流式使用 `response.reasoning_summary_text.delta`，其文本在证据中已脱敏；计数保留。

<a id="structured"></a>
## 结构化输出对照

schema 限定 code 的单值枚举并禁止额外字段，提示却要求 WRONG 与 extra 字段。schema 不在用户提示里重复，以避免仅测提示遵从。

| case | HTTP | 最终对象 | 本地校验 |
| --- | --- | --- | --- |
| r-schema-ALPHA | 200 | `{"code":"ALPHA"}` | 通过 |
| r-schema-BRAVO | 200 | `{"code":"BRAVO"}` | 通过 |
| r-json-object | 200 | `{"count":7}` | 通过 |
| c-schema-ALPHA | 200 | `{"code":"ALPHA"}` | 通过 |
| c-schema-BRAVO | 200 | `{"code":"BRAVO"}` | 通过 |
| c-json-object | 200 | `{"count":7}` | 通过 |
| r-schema-stream | 200 | `{"code":"CHARLIE"}` | 通过 |

仅证明所用 schema；未知关键字、复杂 schema、截断与拒答行为保持未验。

<a id="tools"></a>
## 工具与状态对照

`lookup_probe` 只读取本地固定返回 `{"code":"CEDAR-4826"}`；没有连接外部系统。三个闭环均先验证工具名称与 `label:cedar`，再将完整原始 output/assistant 与对应结果回传。原始 reasoning 载体只在内存中用于续接，磁盘证据脱敏，不能把脱敏后的对象直接发给 API。

| 样本 | 观测 |
| --- | --- |
| r-tool → r-tool-return | 两轮 200，最终 CEDAR-4826 |
| r-tool-stream → r-tool-stream-return | 两轮流式 200，最终 CEDAR-4826，参数 delta 重建成功 |
| c-tool → c-tool-return | 两轮 200，最终 CEDAR-4826 |
| r-tool-choice-auto | 生成 lookup_probe，参数 label:cedar |
| r-tool-choice-none + 两次复测 | 3/3 仍生成 lookup_probe，含 1 流式 |
| r-tool-conflict-required | 提示不调用工具时，只返回 OK |
| r-tool-conflict-named | 要求 lookup_probe，但遵从提示调用 other_probe |
| c-tool-conflict-required | 忽略“只答 OK、不用工具”的提示，确实调用 lookup_probe |
| c-tool-conflict-none | 无函数调用，正文说明工具已禁用 |
| c-tool-conflict-named | 400 InvalidParameter；文案还称不支持 required，但 required 样本已成功 |
| r-tool-previous-id | 前轮未启用 store，400 PreviousResponseNotFound |
| r-store-true → r-store-true-followup | 显式存储后，仅用 ID 续接，精确恢复 ORBIT-6379 |

顺向提示的 required / 具名成功仅证明能调用函数；冲突样本才揭示选择约束。没有测试多函数并行执行或服务端工具。

## 来源、复现与范围

官方来源均于 2026-10-26 核对：

- [Kimi K3.1 Pro 指南](https://platform.kimi.ai/docs/guide/kimi-k3-1-pro-quickstart)：请求 ID、三档思考、固定采样、上下文与工具历史；以官方契约标识，未直连测试。
- [Kimi Reasoning Effort](https://platform.kimi.ai/docs/guide/use-reasoning-effort)、[response_format](https://platform.kimi.ai/docs/guide/response_format)：字段与严格结构化接口。
- [火山 Responses 深度思考](https://docs.volcengine.com/docs/ark/responses-api-deep-thinking?lang=zh)：页面更新 2026-10-24，含日期版 Kimi 的七档兼容映射；与套餐实测冲突处并列保留。
- [火山多模态](https://docs.volcengine.com/docs/ark/multimodal-understanding?lang=zh)、[工具调用](https://docs.volcengine.com/docs/ark/responses-api-tool-calling?lang=zh)：页面更新 2026-10-09，分别说明 PDF 预处理、store 与工具结果续接。
- [火山结构化输出](https://docs.volcengine.com/docs/ark/responses-api-structured-output?lang=zh)：页面更新 2026-09-22，text.format 和 strict。火山正文通过浏览器加载核对，网页文本抓取仅返回 JavaScript 提示时没有将其当作正文证据。

[脱敏证据 JSON](volcengine-kimi-k31-evidence.json) 保存全部请求形状、状态、响应版本、普通输出、usage、SSE 事件和夹具哈希。专用 reasoning 文本、签名、加密块与附件 data URL 不入库；普通正文中的异常推导保留用于格式校验。密钥与请求头未记录。

[显式运行探测脚本](../../../scripts/probe_kimi_k31.py) 从环境读取 SEEDDACE_KEY，固定访问用户指定的套餐 base，默认向 /tmp 追加脱敏 JSONL，不读取 shell 配置。阶段必须显式选取，不进入普通测试或自动网络重试：

| 参数 | 范围 | 当前阶段请求数 |
| --- | --- | --- |
| baseline | 最小 Responses | 1 |
| phase1 | Responses effort、默认、关闭、SSE 与 Chat 基线 | 12 |
| phase2 | PNG/PDF 与结构化 | 12 |
| phase3 | Chat effort、关闭复测、流式 schema | 17 |
| phase4 | 三个工具闭环、选择顺向样本、未存储 ID | 10 |
| phase5 | thinking 组合、显式存储、采样拒绝 | 8 |
| phase6 | tool_choice 冲突对照 | 7 |

脚本复跑是新一轮付费/套餐额度消耗，应显式选择需要复核的阶段；原始基线输出上限为 2048，复跑脚本统一为 4096。当前阶段请求数依赖前序是否成功，表中为本次执行数量。无需访问 model 列表。

成功响应原始用量合计输入 **41,044**、输出 **5,369** token；没有平台金额报价，未对账。输出已包含 reasoning，不能重复相加；不套 Moonshot 价格估算本套餐账单。完成离线证据检查：67 条记录唯一、终止正常、11 条 SSE 重建、6 个附件答案、5 个 strict 对象、2 个 JSON 对象、3 个工具闭环、冲突反例、状态续接及夹具哈希一致。HTTP 200 数量不等于能力全部通过。

本轮没有长上下文/长任务性能测试、扫描 PDF、复杂版面、URL、视频、Files API、服务端工具、Chat SSE 或复杂 schema 测试。待核实项见 [Kimi 清单](open-questions.md#kimi-k31-ark)。
