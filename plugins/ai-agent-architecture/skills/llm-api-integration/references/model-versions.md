# 模型名称、版本归属与生命周期

本页为【官方文档，核对 2026-10-25】，不是实测。页面未提供更新日期时，核对日期仅表示读取时间。主键仍为平台 × 协议 × 请求模型 ID；别名映射会变化，不能反推历史请求的实际后端。参数细节见 [思考补充](reasoning.md#official-model-updates) 与 [工具补充](tools-and-server-tools.md#official-model-updates)。

## 目录

- [GPT 6.1 Sol](#gpt-sol)
- [Claude Opus 4.8、Fable 5 和 5.1](#claude-versions)
- [Gemini 3.5 和 3.7 Flash](#gemini-versions)
- [Qwen3.8-27B](#qwen-27b)
- [DeepSeek V4.1 Flash](#deepseek-flash)

<a id="gpt-sol"></a>
## GPT 6.1 Sol

**VER-OAI-001** — OpenAI 官方 ID 为 `gpt-6.1-sol`，不是 `gpt-6-sol` 的拼写别名。上下文 1,050,000、最大输出 128,000 token。工具调用使用 Responses；Chat Completions 仅支持不带工具的请求。不能继承旧 GPT-6 经 OrcaRouter ① 面的工具实测。

来源：[模型页](https://developers.openai.com/api/docs/models/gpt-6.1-sol)，定位模型说明与 token limits；[GPT-6 指南](https://developers.openai.com/api/docs/guides/latest-model)，GPT-6.1 Sol 小节。当前官方端点尚无本库实测。

<a id="claude-versions"></a>
## Claude Opus 4.8、Fable 5 和 5.1

**VER-ANT-001** — Claude API 的三个独立 ID：

| 型号 | API ID | 文档状态 | 上下文 / 最大常规输出 |
| --- | --- | --- | --- |
| Opus 4.8 | `claude-opus-4-8` | Active / legacy，仍可用 | 1M / 128K |
| Fable 5 | `claude-fable-5` | Active / legacy，仍可用 | 1M / 128K |
| Fable 5.1 | `claude-fable-5-1` | Fable 5 的后继版本 | 1M / 128K |

Opus 4.8 和 Fable 5 均为文字、图像输入，文字输出；不是图像生成模型。Fable 5 与 5.1 不能合为同一能力格，尤其强制工具调用不同。其他云平台的 ID 按其文档选取，不直接复制 Claude API ID。

来源：[Opus 4.8 概览](https://platform.claude.com/docs/en/models/opus-4-8/overview)，Specifications / Availability；[Fable 5 概览](https://platform.claude.com/docs/en/models/fable-5/overview)，同小节；[Fable 5.1 新特性](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)，基线与 Breaking changes。

<a id="gemini-versions"></a>
## Gemini 3.5 和 3.7 Flash

**VER-GGL-001 / 002** — 官方模型页（页面更新 2026-10-12）明确标记弃用：

| 请求 ID | 官方文档指定的转路由目标 | 原型号规格 |
| --- | --- | --- |
| `gemini-3.5-flash` | `gemini-3.6-flash` | 输入 1,048,576 / 输出 65,536 token |
| `gemini-3.7-flash` | `gemini-3.8-flash` | 输入 1,048,576 / 输出 65,536 token |

两款原型号均支持文字、图像、视频、音频、PDF 输入及文字输出；支持函数调用、结构化输出、搜索 grounding、代码执行、URL context；不支持图像生成、音频生成或 Live API。3.7 文档明确 thinking 档位为 low / medium / high，minimal 报错；本次未核实 3.5 的具体档位，不由 3.7 反推。它们不是 Flash-Lite、TTS 或 `gemini-3.5-transcribe`。

接入时记录请求 ID 与文档转路由目标，不能把今天调用旧 ID 当成旧权重的复测；第三方网关是否跟随转路由仍需单独核实。

来源：[3.5 Flash 模型页](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash)、[3.7 Flash 模型页](https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash)，页首 Deprecated 与规格表。较早的发布指南仍可能写 GA，生命周期以此次读到的模型页为准。

<a id="qwen-27b"></a>
## Qwen3.8-27B

**VER-QWN-001** — 官方权重仓库为 `Qwen/Qwen3.8-27B`，Apache-2.0。它是独立的 27B 模型，不是 `qwen3.8-max` / `qwen3.8-flash` 的别名。原生上下文 262,144，扩展至 1,000,000 需对应部署配置；不能将托管宣传的 1M 当作本地默认值。

官方卡提供图像和视频输入示例；自部署服务的请求 ID 可由部署配置决定。卡中将 Qwen Cloud 托管版描述为将提供的版本，本次没有核实其生产 API ID、可用区域或上线状态，不能自行造出 DashScope ID。JSON schema enforcement、服务端搜索与代码执行也不能继承 Max / Flash 的记录。

来源：[Qwen 官方模型卡](https://huggingface.co/Qwen/Qwen3.8-27B)，开头说明、Model Overview、Image / Video Input、Instruct Mode。思考参数见主题补充。

<a id="deepseek-flash"></a>
## DeepSeek V4.1 Flash

**VER-DS-001** — 官方请求 ID 为 `deepseek-flash`；核对日的版本是 **DeepSeek-V4.1-Flash-1017**。9 月 10 日发布 V4.1 Flash，10 月 17 日更新，调用名不变。`deepseek-v4-flash` 与 `deepseek-v4-flash-vision-exp` 对应的旧模型已退役，兼容请求当前也服务于 1017 版；不要自行改成未文档化的 `deepseek-v4.1-flash`。

官方规格列出 1M 上下文、最大输出 384K、视觉输入、JSON Output、Tool Calls、Responses 与 Anthropic 接口。JSON Output 不能直接解释为 JSON Schema strict。9 月 28 日旧 `deepseek-flash` 日志保留其日期和别名，不能改标为 1017 版实测；当时拒绝 `video_url` 也不能概括为当前无视觉能力。

来源：[更新日志](https://api-docs.deepseek.com/updates/)，2026-09-10 与 2026-10-17；[模型规格](https://api-docs.deepseek.com/quick_start/pricing/)，Model Details 与脚注 1。价格及峰谷时段会变，核算时重新读取报价页。
