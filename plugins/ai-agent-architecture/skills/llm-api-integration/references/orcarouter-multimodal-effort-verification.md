# OrcaRouter 图片、PDF 与 effort 验证（2026-10-25）

【网关实测】仅代表 api.orcarouter.ai 的所测路由，不是厂商直连认证。每条件 n=1，非流式，输出上限 1024，无重试；图片/PDF 与 effort 分开测。用户最高预算 $1；发下一请求前预留保守成本，缺失费用按预留占用，累计接近 $0.95 停止，留 $0.05 余量；单路由两次传输超时后跳过余项。客户端预算不等于服务端账单硬限额。

## 目录

- [输入测试](#inputs)
- [Effort 对照](#efforts)
- [证据与限制](#evidence)

<a id="inputs"></a>
## 输入测试

自制 [300×160 PNG](../assets/api-probes/probe-shapes.png)：3 个红方块、2 个蓝圆；提示只要求计数，不含答案。自制 [单页文本 PDF](../assets/api-probes/probe-code.pdf) 包含 DOC-CODE: MANGO-7392，提示只要求读取值。附件直接编码入请求，没有 URL 下载、OCR 预处理或把 PDF 文本追加到提示词。网关是否自行转图/抽文未知。

| 路由 | 图片 | PDF | 回显 |
| --- | --- | --- | --- |
| GPT 6.1 Sol | 通过 | 通过 | `gpt-6.1-sol` |
| Claude Opus 4.8 | 通过 | 通过 | `claude-opus-4-8` |
| Claude Fable 5 | 通过 | 通过 | `claude-fable-5` |
| Claude Fable 5.1 | 通过 | 通过 | `claude-fable-5-1` |
| Gemini 3.8 Flash | 通过 | 通过 | `gemini-3.8-flash` |
| Gemini 3.6 Flash | 通过 | 通过 | `gemini-3.6-flash` |
| Qwen 27B（qwen 路由） | 通过 | 通过 | `qwen3.8-flash` |
| Qwen 27B（obsidian 路由） | 通过 | 通过 | `qwen3.8-flash` |
| DeepSeek V4.1 Flash 1017 | 通过 | 通过 | `deepseek-v4-1-flash-261017` |

请求形状：Responses 为 input_image / input_file；Messages 为 image / document + base64 source；Gemini 为 inlineData + MIME；Chat Completions 为 image_url(data URL) / file:{filename,file_data}。均通过自包含附件测试，不代表公网 URL、扫描 PDF、长文档或复杂版面已验证。

Qwen 两路若回显 Flash，图片/PDF 成功仍只归属于网关路由，不能认证 27B 权重。PDF usage 带 image_tokens 也不能证明由模型原生解析 PDF。

<a id="efforts"></a>
## Effort 对照

统一问题：求满足 n mod 7 = 3 且 n mod 11 = 5 的最小正整数，仅回答 n。期望 38；不在请求中提供答案。此处的“通过”表示参数请求被接受、正常结束且答案正确，不证明档位没有被改写或档位质量单调。

参数：GPT 为 reasoning.effort；Claude 为 thinking.type=adaptive + output_config.effort；Gemini 为 generationConfig.thinkingConfig.thinkingLevel；Qwen / DeepSeek 为顶层 reasoning_effort。所有请求 max output=1024，较高 effort 受到相同输出预算限制，因此不作模型能力排名。

选档来源：【官方文档核对 2026-10-25】[Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort) 列 low/medium/high/xhigh/max；[Qwen 官方模型卡](https://huggingface.co/Qwen/Qwen3.8-27B) 列 low/medium/xhigh。GPT 与 DeepSeek 参数来源见 [型号补充](reasoning.md#official-model-updates)。Gemini 采用 LOW/MEDIUM/HIGH 三档实测，不能类推不存在的 max 档。

| 案例 | HTTP | 答案 / 格式 | 终止 | 思考 token | effort 回显 | USD |
| --- | --- | --- | --- | --- | --- | --- |
| sol-effort-low | 200 | 38 | completed | 29 | low | 0.00043 |
| opus48-effort-low | 200 | 38 | end_turn | 83 | 无 | 0.002386 |
| fable5-effort-low | 200 | 38 | end_turn | 67 | 无 | 0.00397 |
| fable51-effort-low | 200 | 38，附解释（未遵守仅数字） | end_turn | 0 | 无 | 0.00429 |
| gemini38-effort-LOW | 200 | 38 | STOP | 231 | 无 | 0.000896 |
| gemini36-effort-LOW | 200 | 38 | STOP | 230 | 无 | 0.000894 |
| qwen-effort-low | 200 | 38 | stop | 281 | 无 | 0.000712 |
| obsidian-effort-low | 200 | 38 | stop | 284 | 无 | 0.001248 |
| deepseek-effort-low | 200 | 38 | stop | 98 | 无 | 0.000138 |
| sol-effort-medium | 200 | 38 | completed | 29 | medium | 0.00043 |
| opus48-effort-medium | 200 | 38 | end_turn | 120 | 无 | 0.00331 |
| fable5-effort-medium | 200 | 38 | end_turn | 55 | 无 | 0.00337 |
| fable51-effort-medium | 200 | 38，附解释（未遵守仅数字） | end_turn | 0 | 无 | 0.00474 |
| gemini38-effort-MEDIUM | 200 | 38 | STOP | 257 | 无 | 0.000994 |
| gemini36-effort-MEDIUM | 200 | 38 | STOP | 324 | 无 | 0.001246 |
| qwen-effort-medium | 200 | 38 | stop | 297 | 无 | 0.000742 |
| obsidian-effort-medium | 200 | 38 | stop | 312 | 无 | 0.001356 |
| deepseek-effort-high | 200 | 38 | stop | 90 | 无 | 0.000126 |
| sol-effort-high | 200 | 38 | completed | 35 | high | 0.00049 |
| opus48-effort-high | 200 | 38 | end_turn | 127 | 无 | 0.003486 |
| fable5-effort-high | 200 | 38 | end_turn | 55 | 无 | 0.00337 |
| fable51-effort-high | 200 | 38 | end_turn | 172 | 无 | 0.00924 |
| gemini38-effort-HIGH | 200 | 38 | STOP | 271 | 无 | 0.001046 |
| gemini36-effort-HIGH | 200 | 38 | STOP | 491 | 无 | 0.001872 |
| qwen-effort-xhigh | 200 | 38 | stop | 134 | 无 | 0.000364 |
| obsidian-effort-xhigh | 200 | 38 | stop | 129 | 无 | 0.0006 |
| deepseek-effort-max | 200 | 38 | stop | 114 | 无 | 0.000156 |
| sol-effort-xhigh | 200 | 38 | completed | 52 | xhigh | 0.00066 |
| opus48-effort-xhigh | 200 | 38 | end_turn | 152 | 无 | 0.00411 |
| fable5-effort-xhigh | 200 | 38 | end_turn | 78 | 无 | 0.00452 |
| fable51-effort-xhigh | 200 | 38 | end_turn | 194 | 无 | 0.01034 |
| sol-effort-max | 200 | 38 | completed | 71 | max | 0.00085 |
| opus48-effort-max | 200 | 38 | end_turn | 126 | 无 | 0.00346 |
| fable5-effort-max | 200 | 38 | end_turn | 62 | 无 | 0.00372 |
| fable51-effort-max | 200 | 38 | end_turn | 225 | 无 | 0.01189 |

单题每档一次，token 不保证随 effort 递增。只有 GPT 响应若携带 reasoning.effort，才能直接核对回显；其他型号无回显不等于参数被忽略。没有本次非法枚举对照，不把 200 当作严格参数校验。

<a id="evidence"></a>
## 证据与限制

本轮完成 53 次请求，网关报价合计 **$0.151000**；预算记账占用 $0.151000，未与账户账单对账。缺失报价项：无。

[脱敏证据 JSON](orcarouter-multimodal-effort-evidence.json) 包含请求形状、返回文本、usage、回显与费用；附件数据由 fixture 文件名替代，实际文件及 SHA-256 一并保存。无密钥、原生思考字段内容、签名或加密块；普通正文中模型自行添加的解释保留。流式/工具/schema 沿用 [前轮验证](orcarouter-extended-verification.md)，本轮未重复这些测试。

结果复核：53 条均 200 并正常终止；18 个附件答案精确匹配。35 个 effort 样例答案均为 38，其中 Fable 5.1 low / medium 额外输出解释，33/35 遵守只返回数字。参数可调用与输出格式遵从分别判断，不将这两例写成完全遵从。
