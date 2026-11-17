# Qwen4-Max：阿里云百炼接入

适用于百炼 `qwen4-max`；不将本页契约套用到 Qwen3、Preview、开源权重或其他网关同名路由。

## 模型与端点

文本、图片、视频输入，文本输出；支持流式、并行 Function Calling、联网搜索、前缀补全、JSON Object / JSON Schema、显式与隐式缓存。不支持批量推理、模型调优及模型部署。

| 长度 | 非思考模式 | 思考模式 |
| --- | --- | --- |
| 上下文 | 1,000,000 | 1,000,000 |
| 最大输入 | 991,808 | 983,616 |
| 最大输出 | 131,072 | 262,144（思考与回答合计） |

最大思维链长度 262,144；默认 `thinking_budget=131072`，不要把默认预算当成最大长度。Responses 另外预留约 20% 窗口，超长输入可自动截断，不能把模型窗口直接当作该接口可完整保留的输入长度。

北京业务空间域名为 `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com`，其他地域使用对应域名。协议路径：

| 协议 | HTTP 路径 |
| --- | --- |
| Chat Completions | `/compatible-mode/v1/chat/completions` |
| Responses | `/compatible-mode/v1/responses` |
| Anthropic Messages | `/apps/anthropic/v1/messages` |
| DashScope 多模态 | `/api/v1/services/aigc/multimodal-generation/generation` |

前三者不能因兼容名称相同就共用所有字段；DashScope 使用 `input.messages` 与 `parameters` 信封。Responses 旧路径 `/api/v2/apps/protocols/compatible-mode/v1/responses` 已停止维护。

来源：[模型规格](https://docs.bailian.console.aliyun.com/zh/model-studio/qwen4-max)、[Responses API](https://docs.bailian.console.aliyun.com/zh/model-studio/qwen-api-via-openai-responses)、[四协议示例](https://docs.bailian.console.aliyun.com/zh/model-studio/cot-summary)。

## 思考参数

默认开启思考并保留历史思考：`enable_thinking=true`、`preserve_thinking=true`，默认强度 `high`。

| 协议 | 强度字段 | 实际档位 | 兼容映射 |
| --- | --- | --- | --- |
| Chat / DashScope | `reasoning_effort` | `low/high/xhigh` | `minimal→low`、`medium→high`、`max→xhigh` |
| Responses | `reasoning.effort` | `low/high/xhigh` | 同上；`none` 关闭思考 |
| Anthropic | `output_config.effort` | `low/high/xhigh` | `medium→high`、`max→xhigh` |

Responses 优先使用 `reasoning.effort`，其优先级高于 `enable_thinking`，后者将不再支持。不要套用旧款“switch 方言停发 effort”的规则。Chat 的非标准字段通过 OpenAI Python SDK 的 `extra_body` 传入，在线路 JSON 中仍位于顶层。

来源：[模型默认参数与档位](https://docs.bailian.console.aliyun.com/zh/model-studio/qwen4-max)、[Responses reasoning](https://docs.bailian.console.aliyun.com/zh/model-studio/qwen-api-via-openai-responses)。

## 思维链摘要、密文与流式回传

默认输出完整思维链；开启摘要与加密后，摘要用于展示，密文用于恢复历史思考。每轮都要开启此功能，并保存、原样回传各条 assistant 消息对应的密文。图片与视频历史仍需保留。

| 协议 | 开启参数 | 摘要 / 密文 |
| --- | --- | --- |
| Chat | `enable_thinking=true`、`thinking_display="summarized"`；续推时 `preserve_thinking=true` | `message.reasoning_content` / `message.encrypted_content` |
| Responses | `reasoning.summary="auto"` | reasoning item 的 `summary` / `encrypted_content` |
| Anthropic | `thinking.type="enabled"`、`thinking.display="summarized"`，配合预算 | thinking block 的 `thinking` / `signature` |
| DashScope | 在 `parameters` 中使用 Chat 的三个参数 | `output.choices[i].message` 内同名字段 |

Chat 的密文是独立帧，一次返回；不要按空文本过滤，也不要另建 assistant 消息。Responses 从 reasoning item 完成事件或最终快照补齐密文，避免重复拼接摘要；历史可保留空 `summary` 数组。Anthropic 在 `thinking_delta` 后返回完整 `signature_delta`；无思考或加密失败时签名可为空。摘要与密文可能缺失，不应据此伪造原始思维链。

DashScope 中间 `finish_reason` 可为字符串 `"null"`，最终为 `"stop"`；usage 为累计值，不能逐帧相加。

来源：[思维链摘要与加密](https://docs.bailian.console.aliyun.com/zh/model-studio/cot-summary)。

## 结构化输出与工具

模型支持 JSON Object / JSON Schema。百炼 Responses 已提供 `text.format`；其文档描述的 schema 配置位于 `text.format.json_schema`（含 `name/schema/strict`），不同于 OpenAI 原生 Responses 的平铺格式，适配时按平台选择信封。JSON Object 提示词需明确要求 JSON。

Responses 的 `tool_choice="required"` 仅适用于工具列表只有一个工具；对象形式使用 `type="allowed_tools"`、`mode` 和 `tools`。不要将“模型支持并行工具”解释为所有强制选工具形式都兼容，也不要沿用旧款思考模式仅允许 `auto/none` 的全家族限制。

来源：[模型能力](https://docs.bailian.console.aliyun.com/zh/model-studio/qwen4-max)、[Responses 输出与工具参数](https://docs.bailian.console.aliyun.com/zh/model-studio/qwen-api-via-openai-responses)。

## 显式缓存与 usage

Chat / Responses 的内容块可设置 `prompt_cache_breakpoint={"mode":"explicit"}`；Chat 兼容旧 `cache_control`，同一请求只选一种。前缀至少 1,024 token，TTL 为 `5m` 或 `1h`。Responses 顶层 `prompt_cache_options` 控制模式与 TTL：`explicit` 依赖手动断点；该对象中的 `implicit` 表示自动在输入末尾设置断点，不能与不传缓存参数时的隐式缓存混为一谈。

| 协议 | 读取量 | 写入量 / TTL 明细 | 输入总量 |
| --- | --- | --- | --- |
| Chat | `prompt_tokens_details.cached_tokens` | 同对象的 `cache_write_tokens`；`cache_creation` 分 TTL | `prompt_tokens` 已含缓存 |
| Responses | `input_tokens_details.cached_tokens` | 同对象的 `cache_write_tokens`；`cache_write_tokens_details.ttl_5m_tokens/ttl_1h_tokens` | `input_tokens` 已含缓存 |
| Anthropic | `cache_read_input_tokens` | `cache_creation_input_tokens`；`cache_creation` 分 TTL | `input_tokens` + 读取 + 写入 |

Chat 的 `cache_creation_input_tokens` 与写入量重复，Anthropic 的 `prompt_tokens_details.cached_tokens` 与读取量重复，不重复相加。Responses 流式 usage 从 `response.completed.response.usage` 获取，不使用 Chat 的 `stream_options.include_usage`。成本归一化见 [用量核算](../../ai-usage-accounting/SKILL.md)。

来源：[Qwen4 显式缓存](https://docs.bailian.console.aliyun.com/zh/model-studio/explicit-cache-qwen4)。
