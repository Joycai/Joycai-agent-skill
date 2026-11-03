# 图像生成/编辑管线（文生图、改图、DashScope 千问/万相、火山方舟 Seedream、MiniMax、xAI、Imagen、Midjourney）

本篇导航：

- [1. 出图入口是对话流式入口的兄弟，不是变体](#1-出图入口是对话流式入口的兄弟不是变体)
- [2. ImageRoute：按端点分发，不按供应商](#2-imageroute按端点分发不按供应商)
- [3. 能力声明而非探测（ImageCaps）](#3-能力声明而非探测imagecaps)
- [4. DashScope 原生协议（千问/万相出图）](#4-dashscope-原生协议千问万相出图)
- [4.1 火山方舟 Seedream（字节跳动 · 豆包）](#41-火山方舟-seedream字节跳动--豆包)
- [4.2 其余几家的逐家事实（按 route）](#42-其余几家的逐家事实按-route)
- [5. 编辑降级的判定：宽松方向的误判 = 二次计费](#5-编辑降级的判定宽松方向的误判--二次计费)
- [6. 响应统一化：一切归一到字节](#6-响应统一化一切归一到字节)
- [7. 计费与观测](#7-计费与观测)
- [8. 结构化出图结果：拆图层的落库与画布还原（Joycai 2026-09 实现）](#8-结构化出图结果拆图层的落库与画布还原joycai-2026-09-实现)
- [本篇检查清单](#本篇检查清单)


> 阅读边界：带日期的厂商行为只适用于所记录组合；类名、路由表、存储格式与 UI 属于参考实现。付费验证与失败重试遵循 [媒体接入入口](../SKILL.md)，不将历史“零成本”描述当作当前保证。


> 本篇解决的问题：在多协议 AI 层里加一条图像生成与编辑管线——OpenAI images API、
> 中继经 chat 出图、Gemini generateContent、DashScope 原生（qwen-image / wan /
> z-image）、字节跳动火山方舟 Seedream（含流式逐张推送与拆图层）、MiniMax image-01、
> xAI Grok Imagine、Imagen `:predict`、Midjourney 代理，以及异步任务型出图接口该怎么接；
> 结构化出图结果（图层）怎么落库、怎么在画布上还原。
> 不读会踩的坑：把出图塞进流式管线、按供应商写子类；短时效签名 URL 直接入库，
> 图库一小时后全 404；把「内容审核拒绝」误判成「端点不能编辑」，触发第二次计费
> 的降级重生成；用 model-id 嗅探决定同步/异步，违反分层铁律且一换名就崩。

出处：simple-ai-writer `src/lib/ai/image.ts`（四条 route 全在一个文件），
`docs/feature/image-generation-plan.md`（决策记录）、`docs/api/landscape.md`（协议事实）；
Joycai Image AI Toolkits（Flutter）`lib/services/llm/protocols/*_images_protocol.dart`、
`chat_image_extraction.dart`、`docs/api/{volcengine-ark,minimax,qianwen-bailian}.md`。

目录：
- §1 出图入口是对话流式入口的兄弟，不是变体
- §2 route：按端点分发，不按供应商（总表 + surface 由用户声明）
- §3 能力声明而非探测
- §4 DashScope 原生（千问 / 万相）：逐模型参数档、异步任务流
- §4.1 火山方舟 Seedream：版本能力表（含 5.0 flash）、组图、5.0 pro 专属任务、透明背景的语义与校验、不支持参数的 400、流式出图、拆图层实测形状
- §4.2 其余几家：images-api（OpenAI）· imagen · xai-images · minimax · midjourney · 经 chat 出图的中继
- §5 编辑降级的判定
- §6 响应统一化：一切归一到字节（含中继回图形状、去重、空结果即失败）
- §7 计费与观测
- §8 结构化出图结果：拆图层的落库与画布还原

---

## 1. 出图入口是对话流式入口的兄弟，不是变体

图像响应是**一个 JSON body**（base64 或短时效 URL），没有 SSE、没有 token
delta、没有 tool loop。硬塞进 `StreamChunk` 会让每个文本消费者绕一个永远
打不中的分支。所以独立一个入口，与流式入口平级：

```text
出图(连接, 请求) -> 结果

请求 = { prompt,
         images?     data URL 列表；非空即「编辑」语义——不拆两个入口，
                     否则按供应商分派的差异会被推给每个调用方
         mask?       仅 OpenAI edits 有；其余 route 忽略而非报错
         n?, size?, aspect?,
         extraBody?  长尾旋钮逃生口（与对话入口同义）
         取消信号 }
结果 = { images: [{ 字节或 data URL, mime }]   一切归一到字节
         text?     模型附带的文字（Gemini 的 text part、DashScope 扩写后的提示词、dall-e-3 的 revised_prompt）
         usage?    { inputTokens, outputTokens }  仅 token 计费的模型有 }
```

## 2. ImageRoute：按端点分发，不按供应商

出图端点**不能从 ApiStandard 推导**：newAPI 式中继讲 OpenAI 协议，却把
Gemini/Flux 图像模型挂在 `/chat/completions` 上，它们的 `/images/generations`
只认 Imagen（"only imagen models are supported"）。同一供应商、同一协议、
按模型走不同端点——所以 route 是 **L3 可声明**的枚举，默认值按协议族推导
（gemini 族 → `gemini`，其余 → `images-api`），显式声明永远赢：

| route | 端点 | 编辑的表达 | 响应形状 |
| --- | --- | --- | --- |
| `images-api` | `POST /images/generations`；编辑另走 `/images/edits`（**multipart**） | 不同 URL + 不同编码 | `data[].b64_json / url` |
| `chat` | `POST /chat/completions` | 多模态 user 消息 | `message.images[]` / content parts / 正文里的 `![](…)` markdown——中继各放各的，全都要接 |
| `gemini` | `POST /models/{id}:generateContent` + `responseModalities:["TEXT","IMAGE"]` | 输入图就是额外 parts | `candidates[].content.parts[].inlineData` |
| `dashscope` | 原生 `/api/v1`（见 §4） | 输入图是 content parts | Qwen／Wan 2.7 同步及 Wan 异步读 choices；Qwen 文生图异步读 results，见 §4 |
| `ark` | `POST {base}/images/generations`（与 `images-api` 同路径，见 §4.1） | JSON 的 `image` 字段（URL / data URL，单张或数组） | `data[].{url\|b64_json, size}`，组图里单项可以是 `{error}`；`stream:true` 时是 SSE 逐张事件 |
| `imagen` | `POST /models/{id}:predict`（**不是** `:generateContent`） | 无——纯文生图 | `predictions[].bytesBase64Encoded`，无 usage |
| `xai-images` | `/images/generations`；编辑 `/images/edits`（**JSON**，不是 multipart） | 1 张 `image:{url}`，2–3 张 `images:[{url}…]`（互斥），提示词里用 `<IMAGE_0>` 指代 | OpenAI 形 `data[]` |
| `minimax` | `POST /v1/image_generation`（挂在 `/v1` 下但**不是** Images API） | 没有编辑——只有 `subject_reference` 主体参考（§4.2） | `data.image_urls[]` + `base_resp`，逐图计数在 `metadata` |
| `midjourney` | midjourney-proxy 的 `/mj/submit/imagine` → `/mj/task/{id}/fetch`（异步） | `base64Array` 垫图 | 任务记录 `{status, progress, imageUrl, failReason}` |

**surface 由用户声明，id 分类只做默认值。** 中转站的模型名是自由文本（`nano-banana-pro`
按 id 分类是 chat、`my-sora` 什么都不是）；让模型行上一个用户可改的「类型」字段（图像 / 视频 /
对话）决定走哪个 surface，未声明时才退回按 id 分类——退回路径与改动前逐字节相同。再给「走
渠道的 chat 面出图」起一个名字（如 `chat-image`），它不是新协议，是一直存在的 chat 兜底路由，
有了名字中转上的 `gpt-image-1` 才能被强制走 chat。它的能力保底表必须 `isImageGenerator:true`：
③ 据此发 `responseModalities:["IMAGE"]`，① 据此把「整条回复就是一个链接」当图下载——假了就是
请求成功、图被丢。**中转不提供厂商原生出图协议**（原生路径从 endpoint 推导，在中转 host 上
无意义）；例外是路径本身就是 `{base}/images/generations` 的（Seedream、grok-imagine），可在
中转上作为 auto。

新增一条 route 的完整清单：枚举加一个值 + dispatch 加一个 case + 设置界面的
route 下拉加一项 + 对应 i18n + 测试文件里一个新 describe 块。route 永远不做
新的默认值——已有供应商行的推导结果不能因为加了新枚举而改变。

## 3. 能力声明而非探测（ImageCaps）

文本模型的能力可以探测（一次便宜的小请求）；**图像端点的探测 = 一次真实计费的
生成**。所以能力全部由作者声明，默认值按协议族猜（官方端点乐观、compat 悲观），
运行期证明声明错了就**可见地**降级：

```text
出图能力声明（模型级，全部可选）：
  edit?       false = 编辑请求直接跳过，不浪费一次调用
  sizes?      空 = 请求里完全不带 size（xAI 等端点会 400 该字段）
  maxRefs?    一次编辑最多几张参考图
  route?      不设 = 按协议族推导
  asyncTask?  sync-only | async-only | both   dashscope 专用，三态（见下）
```

**同步/异步是声明的能力，不是 model-id 嗅探**（嗅探 = 按模型名分支，改名/新模型
即崩，且违反「供应商是数据不是代码」）。且它是**三态**，不是布尔：qwen-image
全系**仅同步**；`wan2.7-image(-pro)` **同步异步皆可**——同一模型两条路都通，
走哪条是用户偏好（同步简单、异步不怕长任务超时），只有 `both` 档才值得给用户
一个选择。声明错了会收到端点自己的明确报错（同步/异步**提交路径不同**，
打错路径报的是路径级 4xx），和 caps 体系其余部分的降级哲学一致。

## 4. DashScope 原生协议（千问/万相出图）

<a id="qwen-text-to-image-qianwen"></a>
### 千问AI平台 Qwen 无参考图文生图（FACT-QWEN-T2I-001）

📄【文档 2026-11-03 查阅；页面未标发布日期；无 API 实测】依据[同步](https://platform.qianwenai.com/docs/api-reference/image-generation/qwen-text-to-image)、[异步提交](https://platform.qianwenai.com/docs/api-reference/image-generation/qwen-text-to-image-30-async)、[结果查询](https://platform.qianwenai.com/docs/api-reference/image-generation/qwen-text-to-image-task-query)。本节只覆盖千问AI平台原生无参考图请求，不将编辑、旧百炼或兼容接口规则外推到此处。

**请求与能力选择**：base 为 `https://maas.qianwenaiapi.com/api/v1`，Bearer API Key；POST 使用 JSON `{model,input:{messages:[{role:"user",content:[{text:prompt}]}]},parameters}`。必须单条 user、单个文本对象，不含 image。同步型号为 `qwen-image-3.0-pro`、`qwen-image-3.0`、`qwen-image-2.1-pro`、`qwen-image-2.1-turbo`、`qwen-image-2.0-pro`、`qwen-image-2.0` 及页面枚举的 2.0 日期版；异步仅前四款。异步页提示词段提到 2.0／其他型号，不构成扩大 model 枚举的依据。

| 参数 | 文生图约束 |
| --- | --- |
| text | 中英文；3.0／2.1 推荐 ≤4500 Token，2.0 上限 1300 Token，超出截断；不能按字符数代替 Token 校验 |
| size | `宽*高`，面积 512²–2048²；3.0／2.1 比例 1:8–8:1，省略时按提示词推荐；2.0 默认 `2048*2048`，页面未单列其比例范围。不是输入图比例，也不使用初代五档枚举 |
| n | 1–6，默认 1 |
| negative_prompt | 最多 500 字符，超出截断；2.1 不支持，按型号省略 |
| prompt_extend / prompt_extend_mode | 前者默认 true；3.0／2.1 支持后者，默认 direct，也支持 agent。编辑不支持 agent 的限制不能套到文生图 |
| enable_thinking | 默认 true，仅 prompt_extend=true 生效；文生图 direct／agent 均适用，开启可能增加耗时；页面未逐型号展开其适用范围 |
| watermark / seed | 水印默认 false；种子 0–2147483647，省略时随机，相同种子不保证完全相同结果 |

**响应必须按操作解析**（FACT-QWEN-T2I-002）：

| 操作 | 路径／请求差异 | 响应契约 |
| --- | --- | --- |
| 同步 | POST `/services/aigc/multimodal-generation/generation`；无需异步头 | `output.choices[].message.content[].image`，PNG URL 24h；保留 finish_reason（stop 表示正常结束）及 assistant role |
| 提交 | POST `/services/aigc/image-generation/generation`；必须 `X-DashScope-Async: enable` | `output.task_id/task_status`、request_id；初态通常 PENDING，HTTP 200 不是生成完成。缺异步头会报不支持同步调用 |
| 查询 | GET `/tasks/{task_id}`，Bearer；无需重发生成 body | 成功读取 `output.results[].url`，并保留 orig_prompt／actual_prompt；**不是同步的 choices，也不是 Wan 2.7 的查询结构** |

同步 `output.rewrite_status` 仅 3.0 返回；`output.task_metric`（单数）的 TOTAL／SUCCEEDED／FAILED 在 2.0 和 3.0 不返回。同步 usage 仅统计成功结果：3.0 使用 output_width／output_height、output_image_count、input_image_count（文生图为 0）及 input_image_type／output_image_type；其他系列使用 image_count／width／height。3.0 分档规则与[编辑计量](#qwen-image-editing-qianwen)相同；输入档位字段存在不代表有输入图片费用。

查询页另列 `output.task_metrics`（复数）的 TOTAL／SUCCEEDED／FAILED 和 `usage.image_count`，没有展开 3.0 同步的计量档位字段。按该查询契约读取并保留原始 usage，不能保证查询一定补齐同步字段，也不能由文档未列断言永不返回。记录实际成功数和失败数，不能仅凭任务成功或请求 n 认定全部图片成功。

异步提交页建议每 **10 秒**查询一次；PENDING／RUNNING 继续，SUCCEEDED／FAILED／CANCELED／UNKNOWN 结束轮询，UNKNOWN 的原文含义为任务不存在或状态未知。FAILED 才要求读取 output.code/message；成功才读取 results。查询保留 request_id、task_id、submit_time／scheduled_time／end_time；任务结果和 URL 24h 后过期，及时保存。查询失败或客户端取消不自动重发生成请求；状态枚举中的 CANCELED 不证明存在取消接口。查询 usage 缺失不等于免费；不要只凭路径相同复用 Wan 的结果解析器。

<a id="qwen-image-editing-qianwen"></a>
### 千问AI平台 Qwen 图像编辑（FACT-QWEN-IMAGE-EDIT-001）

📄【文档 2026-11-03 查阅；页面未标发布日期；无 API 实测】[官方参考](https://platform.qianwenai.com/docs/api-reference/image-generation/qwen-image-editing)。范围：千问AI平台原生接口、Qwen 3.0／2.1／2.0 系列；具体模型 ID 使用时复核页面枚举，不套用到旧 `qwen-image-edit*` 或中继。

- JSON POST `https://maas.qianwenaiapi.com/api/v1/services/aigc/multimodal-generation/generation`，Bearer API Key。请求结构为 `model`、`input.messages`、`parameters`；单条 `user` 消息，content 中恰好一个 `{text}`，参考图用 `{image}`。2.1 支持 1–10 图，其余所列模型 1–3 图；保留输入顺序。
- 图片支持公网 URL 或 MIME data URI；JPG/JPEG、PNG、BMP、TIFF、WEBP、GIF（首帧）；单图 ≤10 MB、边长 1–8000（建议 384–2048）、长短边比 ≤10。输出 `n` 为 1–6，默认 1。
- `size` 使用 `宽*高`，面积 512²–2048²；3.0／2.1 比例 1:8–8:1，缺省自动推荐；2.0 缺省跟随输入，多图取末图。页面 content 段另泛称末图决定比例，与 size 段存在表述差异；需确定画幅时显式指定，不据此推断未测行为。
- 编辑指令支持中英文：3.0／2.1 推荐 ≤4500 Token，2.0 上限 1300 Token，超出截断；缺少文本或多个文本对象会报错。
- 2.1 不支持 `negative_prompt`；其他所列系列该字段最多 500 字符，超出截断。3.0／2.1 编辑使用 `prompt_extend_mode: "direct"`，`agent` 会返回 400。`prompt_extend` 与 `enable_thinking` 默认 true，后者仅在前者开启时生效；页面未逐型号说明 thinking 能力，不额外推断。`watermark` 默认 false；`seed` 范围 0–2147483647，相同值不保证完全相同结果。
- 结果读取 `output.choices[].message.content[].image`（URL 24 小时有效）。3.0 usage 使用 `output_image_count/output_width/output_height` 及输入计量字段；其他系列使用 `image_count/width/height`。保留原始 usage，不能统一只读 `image_count`。3.0 的输入／输出 `qima_*_1k` 与 `qima_*_2k` 均按**输出面积**分档：≤2,250,000 为 1k，大于为 2k；这些是计量档位，不是价格表。保留 `request_id`、`rewrite_status` 和 `finish_reason` 供排障。

适配边界：本节是所列 Qwen 系列图像编辑的当前文档依据；以下通用说明按此修正。旧推断已移至结论历史。其他平台或旧型号仍需核对自身契约，不能自动替换主机。

<a id="z-image-turbo-qianwen"></a>
### 千问AI平台 Z-Image 文生图（FACT-Z-IMAGE-001）

📄【文档 2026-11-03 查阅；页面未标发布日期；无 API 实测】[官方参考](https://platform.qianwenai.com/docs/api-reference/image-generation/z-image)。原有条目仅列模型名，本节补齐 `z-image-turbo` 的独立契约；不继承 Qwen 参数能力。

- 同步 JSON POST `https://maas.qianwenaiapi.com/api/v1/services/aigc/multimodal-generation/generation`，Bearer Key；body 为 model、input.messages、parameters。单条 user 的 content 恰好一个 text，无参考图；文本支持中英文，最多 **800 字符**，超出截断，不是 800 Token。零个或多个内容对象报错。
- `size` 为 `宽*高`，默认 `1024*1536`。页面给出范围 512×512–2048×2048、推荐 1024×1024–1536×1536，并列多种比例的推荐值；这些推荐值不是穷尽枚举。文档未明确范围按面积还是单边校验，也未声明 16 倍数或独立比例上限；不要套用 Qwen 面积校验。需确定合法值时使用页面推荐尺寸，例如方图 `1024*1024`、竖图 `1024*1536`、横图 `1536*1024`，其他边界待澄清。
- `prompt_extend` 默认 **false**；关闭时返回原提示词，开启后返回优化提示词和推理内容，并增加耗时与费用。“关闭无额外费用”仅指改写，不代表生成免费。`seed` 为 0–2147483647，缺省随机，相同值不保证完全复现。
- 参数表仅列 size、prompt_extend、seed；不主动发送 Qwen 的 n、negative_prompt、watermark、prompt_extend_mode 或 enable_thinking。该页只说明同步文生图，不能据此宣称异步／编辑受支持；未列参数的实际拒绝或忽略行为未测。
- 结果为单个 choice，提图读 `output.choices[].message.content[].image`（PNG URL，24h），同一 content 另含 text；保留 `message.reasoning_content`，改写关闭时为空字符串。读取 finish_reason、request_id，不将文本项当作图像，也不依赖 content 的固定顺序。示例返回文字与输入猫的提示词不一致；以字段说明为契约，不把示例内容当作实际改写行为。
- usage 仅统计成功结果：width、height、image_count（固定 1），以及 input_tokens、output_tokens、total_tokens；关闭改写时三项 token 为 0，不能据此认定没有图片用量。开启时还可返回 `output_tokens_details.reasoning_tokens`。保留图像与改写用量，单价及计价算法另查，不从字段猜测。
- 页面列出 400／401／429 响应；具体错误码和未列参数行为尚未核实，不将别的模型报错当作本模型实测。

### 原生协议接入与历史观测

本节讨论 qwen-image / wan / z-image 的原生 `/api/v1` 协议，不能据此断言平台没有其他兼容入口。
原生 body 与 OpenAI images API 不同，按 [provider-layering](../../llm-api-integration/references/provider-layering.md)的标准配得上一个 route
枚举值：

- **原生 base 从既有供应商行推导**（剥 `/compatible-mode/v1` 拼 `/api/v1`，见[provider-layering](../../llm-api-integration/references/provider-layering.md) §8.4）：同一供应商行、同一个密钥同时服务文本与出图——不要让作者为出图建第二个供应商（那意味着同一个 key 存两份）。
- **同步端点**（当前 Qwen 3.0／2.1／2.0、历史 qwen-image-edit\*、z-image-turbo、wan 改图）：
  `POST /services/aigc/multimodal-generation/generation`。
- **body 两段式**：`input.messages[].content` 是 `{image}`/`{text}` part 数组
  （image 收公网 URL 或 data URL；保留多图相对顺序），旋钮全在
  `parameters`（`n`、`size`、`negative_prompt`（仅声明支持的模型）、`seed`、
  `watermark`、`prompt_extend`…）。**`extraBody` 要并进 `parameters` 而非顶层**
  ——顶层为 `model`、`input`、`parameters`，不要把参数平铺到顶层。
  qwen 与 wan 使用相似信封，但参数能力不同；示例中的 qwen 图前文后、wan 文前图后
  不构成服务端强制文本顺序的证据。Qwen 多张图片的相对顺序必须保留。【实测 2026-09-19】wan2.7-image-pro 把 `messages`
  放在顶层会得到 `400 InvalidParameter: Field required: input.messages`。
  这个顶层写法来自一份二手文档镜像，官方页没有这么写（坑 101）。
- **尺寸拼写是 `宽*高`**（如 `1024*1024`）。**只有 wan** 另收 `"1K"/"2K"/"4K"` 预设；
  qwen-image-3.0 收到 `"1K"` 会回 400 `Expected format: '<width>*<height>'`。
  通用侧的尺寸解析分隔符放宽为 `/[x*×]/`，发出前把作者写的 `1024x1024`
  归一成端点拼写。`"2K"` 这类预设本身不编码宽高比（Wan Pro 编辑跟随末图），
  不参与按 aspect 挑选，只作兜底。
- **`size` 可选，不强制首图比例或 16 倍数**：Qwen 按上方文生图／编辑各自契约处理缺省尺寸。
  产品要求固定画幅时显式发送合法尺寸；不要将历史单次 2K 输出推广为省略参数的保证，
  也不要默默按第一张图裁定输出比例。旧默认尺寸推断见 [结论历史](../../llm-api-integration/references/conclusion-history.md#hist-qwen-image-edit-001)。
  Wan 当前默认尺寸和场景限制见 [FACT-WAN27-IMAGE-001](#wan27-image-editing)。
- **发之前先按目标模型的规则校验 `size`**：任务参数会比选它的模型活得久，比如重试
  时换了模型，或者值是从别的厂商那边留下来的（`auto`、另一家的像素值）。
  不合当前模型规则时给出校验错误或让调用方明确选择合法值，避免静默改掉用户要求的画幅。
- **响应里的图是 URL 且 24 小时过期**——拿到立刻下载内联（§6）。
- **错误是顶层 `{code, message}`**（不是 OpenAI 的 `{error:{…}}`；任务失败时
  嵌在 `output` 里）。错误解析必须兼容两种形状，否则 `DataInspectionFailed`
  （内容审核拒绝）丢掉结构化 code，掉进 prose 正则被误读（§5）。
  `Throttling`/429 = 限流；HTTP 200 带 `code` = body 里送达的错误，照常抛。

<a id="wan27-image-editing"></a>
### Wan 2.7 图像生成与编辑（FACT-WAN27-IMAGE-001）

📄【文档 2026-11-03 查阅；页面未标发布日期；无新增实测】千问AI平台 `wan2.7-image`、`wan2.7-image-pro`：[创建任务](https://platform.qianwenai.com/docs/api-reference/image-generation/wan27-image-gen-edit/create-task)、[同步调用](https://platform.qianwenai.com/docs/api-reference/image-generation/wan27-image-gen-edit/synchronous)。两种调用共享请求体，端点与响应处理分开。

- 输入：单条 `user`，恰好一个 `text`（中英文 ≤5000 字符，超出截断），0–9 个 `image`；编辑至少一图，顺序保留。图片为公开 HTTP(S) URL 或 MIME data URI，JPEG/JPG、PNG（无 Alpha）、BMP、WEBP；单图 ≤20 MB、边长 240–8000、比例 1:8–8:1。
- `enable_sequential` 默认 false：普通模式 `n` 为 1–4、默认 1；图像集模式为 1–12、默认 12，表示输出上限而非保证张数。按成功图片数计费，不按请求上限直接结算。
- `size` 默认 `2K`。编辑时两款都仅支持 `1K`／`2K`，或面积 768²–2048²、比例 1:8–8:1 的 `宽*高`。Pro 的 `4K` 预设仅限无图且非图像集的文生图；其文生图自定义面积上限 4096²，其他场景为 2048²。标准版所有场景上限 2048²。预设按像素面积定义；Pro 有图时跟随末图比例，无图时文档称正方形，标准版段落未单独说明比例来源。实际输出像素可能略有偏差，读取 usage 和产物，不能保证逐像素相等。
- `thinking_mode` 默认 true，仅无图且非图像集时生效，不能当作图像编辑的思考开关。`bbox_list` 若传入，长度与输入图数相等；每图最多两组原图绝对像素 `[x1,y1,x2,y2]`，无需选区的位置填 `[]`。
- `color_palette` 仅非图像集可用，3–10 个 `{hex,ratio}`；ratio 为两位小数百分比字符串，总和 100.00%。`watermark` 默认 false；`seed` 为 0–2147483647，不保证复现完全相同图片。
- 当前参数表未列 `negative_prompt`／`prompt_extend`，适配器不主动发送；未实测其拒绝或忽略行为，不能直接写成必然 400。
- 同步解析 `output.choices[].message.content[].image` 与 `output.finished`；usage 保留 `image_count`、`size`、`input_tokens`、`output_tokens`、`total_tokens`。token 字段存在不等于按 token 计费。输出 URL 24 小时有效。

<a id="wan27-response-contract"></a>
### Wan 同步／查询响应边界（FACT-WAN27-IMAGE-002）

📄【文档 2026-11-03】来源：[同步接口](https://platform.qianwenai.com/docs/api-reference/image-generation/wan27-image-gen-edit/synchronous)、[查询接口](https://platform.qianwenai.com/docs/api-reference/image-generation/wan27-image-gen-edit/query-result)。

| 项目 | 同步 POST | 异步结果 GET |
| --- | --- | --- |
| 路径（相对原生 base） | `/services/aigc/multimodal-generation/generation` | `/tasks/{task_id}` |
| 请求 | Bearer 鉴权、JSON 请求体；无需异步提交头 | Bearer 鉴权、路径 task_id；无需再次发送生成请求体或异步提交头 |
| 完成判据 | 单次响应直接含结果；检查 `output.finished`、choices 和图像产物 | 先判 `output.task_status`；`finished` 仅表示结束，不能替代成功状态 |
| 产物 | 遍历所有 choices 的 message.content 图像项 | 文档仅在 SUCCEEDED 给出 choices；与同步共用提图逻辑 |
| 诊断 | 顶层 `request_id`，每个 choice 的 `finish_reason` | 另有任务 ID 和提交／调度／结束时间；每次查询的 request_id 与任务 ID 分开记录 |

实现建议：保留 `message.role`、`content.type` 等原始字段，不能把示例的 `stop` 当作穷尽枚举；HTTP 200 或 `finished:true` 都不足以独立证明交付成功。非成功状态不强读 choices／usage，成功响应缺少可用图片时报告异常，不自动重发生成请求。

文档内部仍有两点不能过度推断：同步示例在无图、`size:"2K"` 时展示 `2985*1405`，与 size 字段“无图正方形”的描述不一致；Pro 自定义尺寸段落没有像预设段落那样明确展开“无图图像集”条件。需要确定画幅时显式设置合法尺寸；无图图像集不借自定义尺寸绕过已明确的 4K 预设限制，具体自定义上限仍待澄清。两者均未做 API 验证。

### 其他模型参数与解析边界

- 当前 Qwen 3.0／2.1／2.0 编辑的参考图、参数和用量规则统一见 [FACT-QWEN-IMAGE-EDIT-001](#qwen-image-editing-qianwen)。旧 `qwen-image-edit` 基础版固定 `n:1` 且无 `size` 为历史文档范围，不外推到新系列。
- 响应提图的键：qwen 系 content 项只有 `image` 键，wan 系多一个
  `type:"image"`——提图逻辑不得依赖 `type` 存在。

### 自由尺寸的规则（逐模型不同，按数据建档）

【文档 2026-09，2026-09-19 复核】各模型对 `宽*高` 的约束不是同一种，校验器要能表达
「面积区间」和「单边区间」两类规则：

| 模型 | 约束 | 比例上限 | 关键字 |
| --- | --- | --- | --- |
| `z-image-turbo` | [当前尺寸说明与未明边界](#z-image-turbo-qianwen) | 页面未单列 | 仅文档化宽*高 |
| Qwen 3.0／2.1／2.0 文生图 | [当前文生图尺寸契约](#qwen-text-to-image-qianwen)（2026-11-03 文档） | 按系列 | 不收 |
| Qwen 3.0／2.1／2.0 图像编辑 | [当前尺寸契约](#qwen-image-editing-qianwen)（2026-11-03 文档） | 按系列；2.0 页面未单列输出比例限制 | 不收 |
| `qwen-image-edit-max` / `qwen-image-edit-plus` | **单边** 512–2048（不是面积）；缺省约 1024² 且保持原图比例 | 由单边区间推出，最多 4:1 | 不收 |
| `qwen-image` / `qwen-image-plus` / `qwen-image-max`（初代文生图） | **只收五个固定值**：`1664*928`（缺省）、`1472*1104`、`1328*1328`、`1104*1472`、`928*1664` ⚠ | — | 不收 |
| `qwen-image-edit`（基础版） | 不支持 `size` | — | — |
| `wan2.7-image` | [当前场景规则](#wan27-image-editing) | 同正文 | 同正文 |
| `wan2.7-image-pro` | [当前场景规则](#wan27-image-editing)，编辑不支持 4K | 同正文 | 同正文 |

Qwen 当前编辑文档未要求边长为 16 的倍数，不应把实现中的取整策略当作服务端限制。

**wan 官方推荐尺寸不是精确比例**【文档 2026-09-19】：`1K`=1024²、`2K`=2048²、`4K`=4096²；
16:9 → 1696×960 / 2688×1536 / 4096×2304；4:3 → 1472×1104 / 2368×1728 / 4096×3072
（竖版对调）。其中 2688×1536 是 1.75:1，不是 1.778:1。所以用精确比例去反查「这是
哪个比例芯片」会把官方格子认成自定义比例。反查要给容差（参考实现用 3%），
认出芯片后改用芯片的精确比例继续算。

**用量与价格分开**：Qwen 同步计量字段及分档见 [编辑契约](#qwen-image-editing-qianwen)，文生图同步／异步差异见 [FACT-QWEN-T2I-002](#qwen-text-to-image-qianwen)，不能由档位名字推断单价倍数；wan 既有记录按张计费，usage 回显 `size`。

**实测结果**【实测 2026-09-19，北京节点，每次 `n:1`、`prompt_extend:false`】：
返回图片的像素（读 PNG IHDR）与发送的 `size` 完全一致。

| 模型 | 发送 `size` | 返回 | usage 要点 |
| --- | --- | --- | --- |
| wan2.7-image-pro | `2688*1536`（16:9 · 2K 官方格） | 2688×1536 | `{image_count:1, size:"2688*1536", input_tokens:1351, output_tokens:2}` |
| qwen-image-3.0 | `2304*1728`（4:3，≈3.98 MP） | 2304×1728 | `{output_width:2304, output_height:1728, output_image_type:"qima_output_2k", input_image_type:"qima_input_2k"}` |
| wan2.7-image | `960*1696`（9:16 · 1K） | 960×1696 | `{image_count:1, size:"960*1696"}` |

这些样本仅证明所列尺寸原样返回；单个 3.98 MP 样本不能定位分档边界，也不能保证全部尺寸原样输出。当前 Qwen 分档按上方文档处理，实际规格仍读取产物与 usage。

### 异步任务流（wan2.7，用户可选的第二条路）

📄【文档 2026-11-03】[查询结果](https://platform.qianwenai.com/docs/api-reference/image-generation/wan27-image-gen-edit/query-result)，请求参数见 [FACT-WAN27-IMAGE-001](#wan27-image-editing)。原生 base 为 `https://maas.qianwenaiapi.com/api/v1`，提交与查询均带 Bearer Key。

提交 `POST /services/aigc/image-generation/generation`，JSON + `X-DashScope-Async: enable`；同步路径为 `/services/aigc/multimodal-generation/generation`。创建返回 `request_id`、`output.task_id` 和初始 `PENDING`，不代表图片完成。随后 `GET /tasks/{task_id}`，建议间隔 5–10 秒；不要重新提交来查询进度。

状态为 `PENDING/RUNNING` 或终态 `SUCCEEDED/FAILED/CANCELED/UNKNOWN`，UNKNOWN 表示 ID 无效或过期。成功时从 `output.choices[].message.content[].image` 提图，**不是 `output.results[].url`**；usage 与同步同形。失败详情在 `output.code/message`；usage 仅文档化于成功响应，缺失不能认定零费用。保留 `submit_time/scheduled_time/end_time`、`finished` 与 request/task ID。任务 ID 和产物 URL 均有 24 小时有效期。文档列出 CANCELED 状态不等于提供了取消端点，本地停止轮询也不代表服务端取消。

轮询循环的设计点：

1. **一个总 deadline 罩住整个任务**（参考值 600s，提交、全部轮询、下载都在
   其内）——生成以分钟计，逐请求的 180s 帽子在这里语义就是错的。总 deadline
   与调用方 `signal` 合成一个信号，喂给每次 fetch **和轮询间的 sleep**
   （`sleep(ms, signal)`，abort 即拒绝）——用户按「停止」必须立刻生效，
   而不是等下一次轮询醒来。
2. **节奏**：使用上方文档的轮询间隔；项目若需要退避或抖动，应标为客户端策略。
3. **瞬时失败限次容忍**：查询遇到网络抖动或 429 可有界重试，遵守总 deadline；达到上限时保留 task_id 供续查，不断言服务端任务失败，也不重复提交。
4. **task_id 提交成功后立刻写进 API 日志**（mid-call note，见 §7）——轮询
   挂死时这是唯一能拿去查任务状态的线索，等成功日志就永远拿不到了。
5. `FAILED` 读取 `output.code/message`；`CANCELED` 单独记录取消，`UNKNOWN` 单独记录 ID 无效或过期，不要求后二者也带错误字段。未识别的状态保留原始响应并报协议异常，不能等同于文档中的 `UNKNOWN`。

## 4.1 火山方舟 Seedream（字节跳动 · 豆包）

> 2026-09-18，官方文档（Seedream 4.0–5.0、5.0 pro 教程与 API 参考）+ 订阅套餐 key 实测。
> **2026-09-23 增补**（simple-ai-writer，对照 09-22 版文档：新增 5.0 flash、透明背景两款都收）：套餐 key
> 31 次零成本探测 + 4 张计费；见下文「5.0 pro / flash 的透明背景」「不支持的参数都在出图前 400」。
> 供应商行（按量/套餐两个 base、套餐挑拼写、`ep-…` 接入点）见[provider-layering](../../llm-api-integration/references/provider-layering.md) §9.3。
> 控制台文档是 SPA：WebFetch 只拿到标题，要浏览器渲染后取正文。

**为什么是一条独立 route 而不是 `images-api` 的变体**：路径与 OpenAI 生成端点同形
（`{base}/images/generations`），`model`/`prompt`/`size`/`response_format` 同名同义，但
body 是**超集且缺字段**——没有 `n`/`quality`，参考图走 JSON 的 `image`（不是 `/images/edits`
的 multipart），张数由组图开关表达。body 形状不同 = 配一个枚举值（[provider-layering](../../llm-api-integration/references/provider-layering.md) §2）。
好处是：只要中转站原样透传 Images API 的 body，同一 route 在中转上也能用（[provider-layering](../../llm-api-integration/references/provider-layering.md) §9.3 的中转例外）。

- **仅同步**（`stream:true` 例外，逐张推事件，5.0 pro 不支持）：一次请求等到**全部**图画完才
  返回。实测 5.0 pro 1K 单张 **43 s**、5.0 lite 2K 单张 26 s；组图最多 15 张。逐请求超时必须
  **按一次请求可能画的张数放宽**（参考：5 分钟起，每多一张 +40 s，封顶 15 分钟；图层拆分按 17
  张算）——固定 3 分钟的帽子会在组图上把一个已计费的请求判超时。
- **`watermark` 默认 `true`**：不写就在右下角加「AI 生成」字样，照常计费，文档每个示例都显式写
  `false`。客户端**永远明发**这个字段，UI 默认关。
- **尺寸两种写法不可混用**：档位（`1K`/`1.5K`/`2K`/`3K`/`4K`，**按模型不同**）或 `WxH`。
  填档位时宽高比由模型**从提示词里猜**（实测 5.0 pro `1K` 无比例提示回了 `1248x832`，3:2）。
  所以 UI 做成「档位 + 比例」两个控件：比例为自动 = 只发档位；选了比例 = 查文档给的
  「档位 × 比例 → 像素」映射表发 `WxH`（表是 L3 数据，协议只查表，不自己算）。
  `WxH` 约束的是**总像素乘积**，不是单边：5.0 lite 下限 3686400（2560×1440），`1500x1500` 无效；
  5.0 pro 区间 [921600, 4624220]。`1.5K` 这类**小数档位**会撞上按 `\d+K` 解析/排序的通用代码。
- **能力逐版本建档**（坑全在档位差里）：

| 版本 | 档位 | 参考图 | 组图 | 输出格式 | 提示词优化 | 联网搜索 | 专属 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5.0 pro | 1K·1.5K·2K | 10 | ✗ | png/jpeg | standard/fast | ✗ | 图层拆分、透明背景 |
| 5.0 flash | 1K·1.5K·2K（与 pro 同表同区间） | 10 | ✗ | png/jpeg | standard | ✗ | 图层拆分、透明背景【文档 2026-09】；**套餐 key 不服务**（三种拼法 404，只在按量） |
| 5.0 lite | 2K·3K·4K | 14 | ✓ | png/jpeg | standard | ✓（`tools:[{type:"web_search"}]`） | — |
| 4.5 | 2K·4K | 14 | ✓ | 仅 jpeg | standard | ✗ | — |
| 4.0 | 1K·2K·4K | 14 | ✓ | 仅 jpeg | standard/fast | ✗ | — |

  发了不支持的字段就是 400——`output_format` 只能发给 5.0，`fast` 只能发给 5.0 pro / 4.0
  （lite 实测 400「optimize_prompt_options.mode must be 'standard'」【实测 2026-09-23】）。
  flash 与 pro 参数表相同、只少 `fast`，客户端可复用 pro 的尺寸方言，但「能否 fast」要单独判。
- **组图**：`sequential_image_generation:"auto"` + `sequential_image_generation_options.max_images`
  （1–15，**默认 15**）。`auto` 时模型**自行决定**画几张，`max_images` 只是上限；且**参考图数 +
  生成数 ≤ 15**——客户端发送前按参考图数收紧上限，不要让端点 400。
- **参考图**：URL 或 `data:image/<fmt>;base64,…`，**`<fmt>` 必须小写**（`image/PNG` 被拒）。
- **张数上限数的是全部输入图**：pro 11 张 → 400「number of reference images cannot exceed 10」，
  lite 15 张 →「cannot exceed 14」【实测 2026-09-23】。改图时**被改的源图也占一张**（它和参考图走
  同一个 `image` 字段）——只数「参考图」的校验会放过「源图 + 满额参考图」，在用户批准、以为要
  画了之后才 400。
- **5.0 pro 专属任务是互斥模式，不是开关组合**：`layer_decomposition:true`（底图 + 最多 16 个
  带透明通道的图层，`data[]` 按 `z_index` 排，图层带 `name` 与 `bounding_box`；任一层失败 = 整个
  请求失败；`size` 只收档位或 `auto`）与 `background:"transparent"`（只用于图生图，输出恒 png，
  同时发 `output_format:jpeg` 报错）。二者都要求**恰好 1 张参考图**（透明背景还要求它带 alpha）——
  这是纯客户端能判定的前置条件，**发请求前检查**并抛不重试、不计费的错误，别花一次调用去换一个 400
  （但「带 alpha」只能部分预判，见下「透明背景」）。
  UI 上收成一个「任务：生成 / 拆图层 / 透明编辑」的分段控件。编辑选区没有字段，写在 prompt 里：
  `<bbox>x1 y1 x2 y2</bbox>` / `<point>x y</point>`（0–1000 归一化）。
- **响应**：`data[]` 每项 `url`（**24 小时过期**，当场下载，§6）或 `b64_json`，加 `size`。
  **组图里单张失败不影响其余**：那一项只有 `error{code,message}`（审核不通过继续画下一张，500 则
  停止后续）；顶层 `error` 只在一张都没画出来时出现。客户端收下成功的、把失败张数报出来，**不能**
  因为一项 error 就判整次失败——别的图已经计费了。
- **计费按张**：`usage.generated_images`（成功张数）是账单口径；`output_tokens` = Σ(宽×高)/256，
  **仅供参考**。把它塞进通用的 token 用量键，按 token 计价的费用组就会算出一笔假钱——放进私有的
  元数据键里只展示。实测回显的 `model`：非流式是去掉日期的 id（`doubao-seedream-5-0-pro`），**流式是请求里的拼写**【实测 2026-09-18】——
  拿回显做模型识别或回显比对时两条路径要分开对待。`usage.input_images` 是参考图张数（实测拆图层 1、文生图 0）；
  `usage.tool_usage.web_search` 是实际搜索次数，0 = 开了联网但没搜【文档 2026-09-18】。
- **错误信封是 OpenAI 形**（`{"error":{"code","message","param","type"}}`，消息尾带 Request id）；
  审核类 code：`InputTextSensitiveContentDetected` / `InputImageSensitiveContentDetected` /
  `OutputImageSensitiveContentDetected`——按 §5，这些**永远不是**「端点不能编辑」的证据。
- **免费探测一个模型能不能用**：发一个非法 `size`（如 `"1x1"`）。支持的模型在生成前就回
  `400 InvalidParameter`（消息里写该模型的最小像素），不支持的回 `404 UnsupportedModel`——
  一次零成本的请求区分「套餐没开这个模型」与「参数错」，比真画一张便宜（[errors-probing-observability](../../llm-api-integration/references/errors-probing-observability.md) §8 的纪律）。

### 5.0 pro / flash 的透明背景（`background:"transparent"`，2026-09-23 实测 pro）

- **校验规则**（全部出图前 400、零成本；`param` 点名字段）【实测 2026-09-23】：
  - 无图或两张以上 →`param:"background"`「transparent background requires exactly one input image」；
  - 同时 `output_format:"jpeg"` → `param:"output_format"`「must be png when background is transparent」——
    **要 png 就必须明发** `output_format:"png"`，两个字段成对出现；
  - RGB PNG、**无 tRNS 的调色板 PNG**、或带 alpha 通道但每个像素都不透明的 PNG →
    `param:"image"`「transparent background requires a PNG input with at least one transparent pixel」。
    上游是**解码后**判定的：PNG 头部（color type 4/6、tRNS）只能说「可能透明」。客户端只读头部时，
    这条 400 免费，正确做法是**去掉 `background` 与 `output_format` 重试一次**——没有透明像素就没有可保留
    的东西，画出来与不带这两个字段一样；不要在客户端全量解码只为省一次免费 400。
- **语义：保证的是「结果背景透明」，不是锁住原图轮廓**【实测 2026-09-23，各 1 张计费】：
  - 透明底红圆「改成蓝色」→ png，圆外全透明 ✅；
  - 透明底向右箭头「改成竖直向上」→ 按新形状重画，新箭尖处（源图透明）不透明、旧箭杆处变透明 ✅——
    主体可以变形、换姿势；
  - 透明底红圆「加上蓝天白云背景」→ 圆外**依旧全透明**，天空被画进了圆里、上半圆成了天空，200、计费 ❌。
    「要一张填满的背景」与透明模式的承诺矛盾，模型不报错，折中成在主体里画背景——**静默**（坑 130）。
  - 所以「输入是透明 PNG 就自动开」是错的，按提示词关键词判断是多语种猜测；要不要填满背景只有写指令的一方知道
    （参考实现：改图工具加 `keep_transparency` 参数，默认保留，要背景时由 agent 设 `false`）。
    只对**改图**开：只带参考图的新生成，参考图的透明背景不是结果要保留的。
- 响应 `data[]` 多 `output_format:"png"`；`usage.input_images:1`。
- 早先写法「透明模式锁死原图 alpha 遮罩」是本次初判、被箭头改向实测推翻（simple-ai-writer 同日更正）。

### 不支持的参数都在出图前 400，报错点名字段（2026-09-23，套餐 key）

| 请求 | 回应 |
| --- | --- |
| pro `sequential_image_generation:"auto"` / `stream:true` / `tools:[{type:"web_search"}]` | 各 400 `param` 为该字段，「is not supported by the current model」 |
| lite `optimize_prompt_options.mode:"fast"` | 400「mode must be 'standard'」 |
| pro/lite `output_format:"webp"` | 400「must be one of: jpeg, png」 |
| 5.0 flash（`doubao-seedream-5.0-flash` / `-5-0-flash` / `-5-0-flash-260915`）、4.5、4.0 | 套餐 404 `UnsupportedModel` |

对探测的意义：一个参数「收不收」可以配一个**别处必错**的字段（非法 `size`、`output_format:"gif"`）零成本问出来——
但只有**先于必错字段校验**的那个才会点名；校验顺序不固定（lite 先报 `size`，pro 先报 `background`），报的
是别的字段就等于没问到，不能当「收下」。

### 流式出图（`stream:true`，2026-09-18 实测 5.0 lite）

5.0 lite / 4.5 / 4.0 支持，5.0 pro 回 `400 InvalidParameter param:"stream"`。标准 SSE，`event:` 与
`data.type` 同名：

```
event: image_generation.partial_succeeded
data: {"type":"image_generation.partial_succeeded","image_index":0,"url":"https://…","size":"2496x1664",…}

event: image_generation.completed
data: {"type":"image_generation.completed","usage":{"generated_images":2,"output_tokens":32448,…}}

data: [DONE]
```

- 每张一个 `partial_succeeded`（`image_index` 从 0 起），单张失败是 `partial_failed`（带 `error`
  对象）；`usage` 只在 `completed` 里。
- **响应头要等第一张画完才回来**（`x-envoy-upstream-service-time` ≈ 27 s）。聊天用的「首块 120 s
  空闲守卫」会在 4K 图还在画时把一个已计费的请求掐掉——出图流的首块与后续块都按**单图期限**
  （参考 5 分钟）计，首块超时判期限、不重试。
- **参数校验失败不走 SSE**：`stream:true` 的请求照样回 `400 application/json` 普通错误信封。200 时
  是 SSE 还是 JSON 看 **body 首行**，不看 `Content-Type`——误读会丢掉已计费的一整组。
- **已知事件不做通用错误信封检查**：`partial_failed` 里有 `error` 对象，通用检查会把它当成整个
  请求失败、扔掉已到的图。只对不认识的事件做信封检查。
- **边到边存、按已送达记账**：每张到了就下载落盘；后面失败或用户取消，已落盘的保留，用量按已
  送达张数记（原先只在流跑完时记 = 取消的任务在统计里消失，钱照扣）。
- 只在官方渠道、且表上声明了流式的版本发 `stream:true`；中转与 5.0 pro 照旧同步——中转是否透传
  SSE 未知，拒收 `stream` 的中转会把能用的渠道变成 400。
- App 内实测（套餐、5.0 lite、`2K`、组图上限 2）：第一张 **27.9 s** 落盘，第二张 **48.4 s**；只发档位
  时模型两张都自选了 16:9（2848×1600）。

### 拆图层的实测形状（5.0 pro，1500×1920 单人立绘，`size:"1K"`，不写 prompt）

200，**37 s**。`data[]` 两项：`z_index:0` 底图 912×1168 jpeg（人物被抹掉只剩背景）；`z_index:1`
图层 861×1137 RGBA png，带 `name`、中文 `description`、`bounding_box.absolute:[27,0,888,1137]`
（**底图像素**，不是输入图像素）与 `.normalized`（0–1000）。自动拆时整个人物是**一层**，不会再拆
头发、衣服。`usage.generated_images` = 实出张数（2），不是超时预算用的 17。落库与还原见 §8。


<a id="gpt-image-token-accounting"></a>
### GPT Image 2/2.5 的 token 计量

**FACT-OPENAI-IMAGE-BILLING-001** — 📄 OpenAI 官方 Images API 与 Responses 图像工具，`gpt-image-2`、`gpt-image-2.5-sunburst`、`gpt-image-2.5-flare`；【文档 2026-10-27，本轮未发付费请求】。文本输入、图像输入、图像输出分别计价。标准处理每百万 token：文本输入 $5、缓存文本 $1.25；图像输入 $8、缓存图像 $2；图像输出 $30。模型/服务档位需独立快照，Batch 价格不能误作 Standard；相同 token 单价不保证相同单图成本。来源：[Flare 模型页](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare)（明确与 GPT Image 2 同价）、[Sunburst 模型页](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst)、[定价](https://developers.openai.com/api/docs/pricing)。

**FACT-OPENAI-IMAGE-BILLING-002** — 📄 原始字段提取【文档 2026-10-27】。Images `usage.input_tokens_details.text_tokens/image_tokens` 为输入模态明细，`input_tokens` 是合计；`output_tokens_details` 可含图像/文本明细，缺明细时仅在模型契约确认纯图像输出后使用 `output_tokens`。`total_tokens` 仅校验，不另计费。非流式响应的 `usage` 与 SSE `image_generation.completed.usage` 是采集入口；partial 图片块不是最终汇总。官方参考的 usage 说明仍有“仅 gpt-image-1”旧文字，但同页 2.5 示例已带上述字段；保留这一文档不一致，运行时按回包判定，缺字段标 unknown，不声称本轮已验证所有模型。来源：[Images API 参考](https://developers.openai.com/api/reference/resources/images/methods/generate)。

**FACT-OPENAI-IMAGE-BILLING-003** — 📄 缓存与组合请求边界【文档 2026-10-27】。GPT Image 2/2.5 的缓存价仅适用于 Responses 图像工具，直连 Images（含 edits）不适用；图像工具的缓存命中计数不在 Responses 输出中，不能用响应验证优惠。Responses 还包含主模型费用，二者按独立范围记录。partial 每张额外 100 图像输出 token；最终 usage 是否已包含这部分须核对，不能无条件再加。尺寸/质量估算仅覆盖输出且随模型变化，不沿用旧模型 token 表。来源：[图像生成指南：成本](https://developers.openai.com/api/docs/guides/image-generation#cost-and-latency)。

适配层保留原始 usage、模型、API 路径、服务档位和调用范围，再规范化模态桶；核算公式、缺失缓存的估算口径及报价覆盖规则见 [计费规则](../../ai-usage-accounting/references/pricing-rules.md)。将全部输入 token 乘文本价会少算，额外按参考图张数收费会双算。未验证回包、缓存账单与 partial 包含关系见 [待核实项](../../llm-api-integration/references/open-questions.md#gpt-image-billing-verification)。

## 4.2 其余几家的逐家事实（按 route）

- **`images-api`（OpenAI / 兼容）**：编辑的 multipart 字段名**跟张数走**——1 张发 `image`、多张发
  `image[]`。只发复数时 dall-e-2 的编辑与照它写的中继对单张图 400，而单数哪里都收。每个文件
  part 显式带 `Content-Type`（有中继对默认的 octet-stream 400【实测 2026-09-05】）。gpt-image-1 参考图上限 16。
  dall-e-3 逐项回 `revised_prompt`（实际画的提示词，放进结果 text），gpt-image-1 不回。
  用量拼写是 `input_tokens`/`output_tokens`（不是 chat 的 `prompt_/completion_tokens`），
  记账要两种都认。端点回显的 `size`/`quality` 是**定了的规格**（请求写 `auto` 时只有回显才有规格），
  按规格计价的费用组优先用回显。
- **`imagen`（Gemini `:predict`）**：纯文生图。用户附了参考图要**显式警告**而不是静默丢掉；
  响应没有 token 用量——元数据至少放张数，否则按次计费的调用在统计里整条消失（§7）。
- **`xai-images`（Grok Imagine）**：编辑是 JSON（`image:{url:<data URI>}` 或 `images:[…]`，二者互斥）；
  参考图上限**文档写 3 张【文档 2026-09】，实测 5 张 HTTP 200 并按 5 张收费【实测 2026-09-21】**——旧结论
  「最多 3 张」被推翻，按 5 截断。`aspect_ratio` 收 `auto`；清晰度走 `resolution: 1k|1.5k|2k`（不是 `size`；`1.5k`
  只有 2.0 收）；要 `response_format:"b64_json"` 省一次下载。`respect_moderation:false` 之类会让 `url`/`b64` 都空——
  空即失败。
  **质量（`grok-imagine-image-2.0`，【实测 2026-09-22】）**：请求字段 `quality`，枚举 `low | medium | high | auto`
  （别的值 → 422，错误信息列出枚举）；2.0 只收 `low / medium / auto`（`high` → 400 `This model only supports the following
  quality value(s): low, medium, auto.`）；**不带 = medium**。OpenAPI（`docs.x.ai/openapi.json`）的请求体**没列** `quality`，
  只有 `ImagePricingTier` 一句「Medium is the default quality a request serves at when it leaves `quality` unset」——文档与
  OpenAPI 不一致，以实测为准。`GET /v1/image-generation-models/{id}` 回 `image_price` + `pricing[{quality, resolution,
  price_per_image}]`（`price_per_image` 单位 1e-8 美分 = 1 tick，见 §7）；2.0 六格：1K·Low $0.04 / 1.5K·Low $0.05 /
  2K·Low $0.06 / 1K·Medium $0.06 / 1.5K·Medium $0.07 / 2K·Medium $0.08。**初代 `grok-imagine-image`（$0.02）与
  `grok-imagine-image-quality`（$0.05）是 `pricing: []`（各质量同价）**：它们**默默收下** `quality`（一个骗人的旋钮，别在
  UI 上给），而 `resolution: 1.5k` → 400 `1.5K resolution is not supported for this model.`（坑 125）。`quality: auto` 由模型
  定档（一次实测选了 Low，$0.04）——按规格计价的表写不出它（坑 124）。
- **`minimax`（`image-01` / `image-01-live`）**：**不是** Images API，也到不了 Images API。
  `aspect_ratio`（8 种）与 `width/height`（512–2048、8 的倍数、仅 `image-01`）是同一件事的两种拼法；
  `n` 1–9；`style` 仅 `-live`；`aigc_watermark` 默认关。`subject_reference[{type:"character", image_file}]`
  是**主体参考**，把参考图里的**人物**带进新画面——这条 wire 上不存在「编辑」：喂风景图要求调色
  会正常返回一张无关的图，所以 caps 要声明 `edit:false`、UI 要说清。**两层失败**：`base_resp.status_code≠0`
  是请求级（过期 key、余额、审核都是 HTTP 200）；`status_code==0` 但 `metadata.success_count==0`
  是逐图失败——只看前者，症状只是「结果为空」。**`success_count`/`failed_count` 实际是字符串**
  （`"0"`/`"3"`），按数字判会静默永不命中，两种都认。URL 24 小时过期。同步但慢：模型声明
  「长任务」，路由据此放宽单请求超时。
- **`midjourney`（midjourney-proxy / New API `/mj/*`）**：独立 L1 协议，异步：submit → 轮询 →
  下载。提交回执 `code` 1 = 成功、22 = 排队中（也算建好）；**task id 一出现就写日志**（已计费，
  轮询死了这是唯一线索）。轮询 3 s、总帽 10 分钟，走共享轮询循环（可取消、容忍几次失败的 fetch）；
  放弃时抛「已放弃的任务」且**永不重试**——重试 = 再付一次 imagine。把每次进度作为一个文本 chunk
  推出，顺带让 chat 的空闲守卫不超时。参数（比例、版本、stylize、chaos、quality）在 UI 用下拉，
  发出前改写成 `--ar/--v/--s/--c/--q` 拼进 prompt；**用户自己写了的 flag 优先**；`--v niji 6` 改写成
  `--niji`。代理没有 `/models`，给内置目录。调试日志里把 `base64Array` 截断成计数。
- **经 chat 出图的中继（`chat` route）**：见 §6 的形状清单。New API 的 Gemini 出图走 ① 形状时
  出图参数**只认 `extra_body.google.image_config`**（snake_case：`aspect_ratio`/`image_size`；
  camelCase 被拒、顶层 `image_config` 不读）——发错位置宽高比与分辨率**静默无效**；走 ③ 原生形状
  时中继**不替你补** `responseModalities`，老模型只回文本。所以同一个模型走 ① 反而更稳。
  **出图模型的纯文本消息也发成单元素 part 数组**：有中转把这次 chat 调用翻译成出图请求，字符串形 `content` 回
  `400 images[0] must be an http/https URL or image data URI`，同一段文字包成 `[{"type":"text","text":…}]` 就收【实测 2026-09-05；坑 110】。
  只对声明为出图的模型这样发；对话模型保持字符串——那是所有宿主都收的形状。

## 5. 编辑降级的判定：宽松方向的误判 = 二次计费

「这个端点不能编辑」触发可见的降级重生成（**另一次全价调用**），所以判定
必须只认「路由缺失」证据，拿不准一律不降级：

1. **模型自己说的话永远不是证据**。「模型只回了文字」（NoImageError）常见于
   文本模型被配成图像模型，其正文里往往就有 "I don't support image editing"
   ——拿去匹配正则就是白花一次生成费。
2. **404 / 405 / 501** = 端点不存在，降级最初就是为这个存在的。
3. **有结构化 code/param 就信它**：只有指名「模型」的才算路由缺失
   （`param === "model"` 或 model_not_found 类 code）。
   `Unsupported parameter: 'x' is not supported with this model.` 带
   `param:"x"`——请求被理解了，丢掉那个字段就能修，重生成是双倍计费。
4. **纯 prose 才落到正则**，且只匹配明确谈「编辑」或「模型」的措辞；正文里
   出现 param/parameter 字样直接判否。

配合两层跳过：声明 `edit:false` 的模型连第一次调用都不发；运行期失败经上述
判定后重试为纯生成，并把 `degraded` 标记透出到 UI/工具结果——降级必须可见。

## 6. 响应统一化：一切归一到字节

- **URL 一律当场下载内联成 data URL**。签名 URL 普遍短时效（DashScope 明文
  24 小时），存链接的图库会静默腐烂。已计费的图值得**一次重试**（刚铸的链接
  + 抖动的网络都常见，另一边是整次生成打水漂）。
- **下载校验 content-type**：中继用 200 + HTML 错误页应答很常见，不校验就会
  往图库写一个谁都打不开的 `.png` 而 UI 报成功。
- **mime 从 magic bytes 嗅探**：`data[].b64_json` 线格式不带 mime，端点却
  可能按 `output_format` 回 JPEG——猜 PNG 会写出扩展名撒谎的文件。
- **base64 出现在 `url` 字段**（中继习惯）：识别 `data:` 前缀直接收下——
  当链接 fetch 在浏览器里碰巧能跑，在桌面端 HTTP 栈里不行。
- **multipart 编辑（OpenAI `/images/edits`）绝不手动设 `Content-Type`**：
  boundary 由运行时序列化 FormData 时生成，手写的头恰好把它抹掉，服务端
  永远解析失败。
- **只有一个交付物的端点，空 = 失败**。Images API / Imagen / xAI / MiniMax 回 200 却一张图都解不出
  （中继的 200 + `{"error":…}`、审核拦截、字段缺失），返回空结果会被任务层读成「成功生成了零张」，
  与模型拒绝无法区分——要抛错并说明实际回来了什么。解析顺序：状态码 → 是不是 JSON → 形状 →
  错误信封。
- **经 chat 出图的回复形状（中继各放各的，全都要接）**：`content` 里的 markdown
  `![image](data:…)` 或 `![image](https://…)`（对象存储型中继给链接，只认 data URI 就是零张图）；
  `message.images[].image_url.url` / `images[].b64_json` / `images[].url` / 裸字符串；
  `message.image_b64_json`；以及**整条回复就是一个裸链接或裸 base64**（同一中继同一模型一小时内
  两种都见过，取决于它挑的上游）。两道闸防误收：裸链接只在模型声明为出图模型时才下载（对话
  模型回一个 URL 是在引用，不是交付）；裸 base64 至少 64 个字符**且解码后 magic bytes 是图片**
  （一个英文单词也在 base64 字母表里）。
- **同一张图在一个回复里出现多次**：见过中继把同一张图同时放在 `content`（裸 base64）、
  `images[0].b64_json`、`image_b64_json` 三处，各存成一个文件。按**字节的 SHA-256** 去重，
  与字段、编码无关。

## 7. 计费与观测

- 无 token 用量的按 `pricePerImage × 张数` 记账，与 token 计费**相加**而非
  二选一（两种口径的模型都存在）。
- 出图调用必须进与文本同一份 API 调试日志（request/response/error 三类目），
  它们按次计费且失败最难复现——恰恰最不该缺席。日志器加一个 **mid-call
  `note(data)`** 通道，记录「调用没走完就没了也想要」的事实（异步任务的
  task_id 是第一个用例）。
- **按次计费的出图，用量元数据永不为空。** 很多记账路径「元数据非空才记一行」；Imagen、MiniMax
  这类不回 token 的端点返回 `{}` 就会在统计里整条消失——上游照扣。至少放张数。
- **按张计费的端点，别把像素折算的 token 塞进通用 token 键**（Seedream 的 `output_tokens`
  = 像素/256），放私有键只展示（坑 83）。
- **有的端点直接报钱。** xAI images 的 `usage` 只有一个字段 `cost_in_usd_ticks`，**1 tick = $10⁻¹⁰**（OpenAPI 把
  `price_per_image` 定义为 "1/100,000,000ths of a USD cent"；实测 400 000 000 = 1K·Low $0.04）【实测 2026-09-21/22】。
  它**含输入图**（$0.06 + 5 × $0.01 = 1 100 000 000），是**整单实扣**——压过任何本地算式，不与 token / 按张**相加**
  （上一条的「相加」规则对它不适用）；回包里**没有**输入张数，张数只能自己数。「没报」（字段缺）与「报了 0」要分开存
  （NULL vs 0）。经中转（走 Images API 形状）时这个字段可能原样透传，但**那是 xAI 收中转的价，不是用户付中转的价**——
  只在自家协议上读它。**视频面同样报**（`GET /v1/videos/{id}` 的 done 回包 `usage.cost_in_usd_ticks`，提交回包没有；[video-generation](video-generation.md) §2）【实测 2026-09-22】。
- **输入图按张计费，与输出分开标价**【2026-09-21 查证】：xAI 2.0 **$0.01/张、线性、无免费张数**，`n:2` 时**按请求收一次、
  不乘输出张数**（1 张参考图 + `n:2` + low = 900 000 000 = 2 × 0.04 + 1 × 0.01【实测 2026-09-22】）；**xAI 视频面同价**（1.5：首帧
  `image` +$0.01、`reference_images` 每张 +$0.01，标价页只写 $0.08/s【实测 2026-09-22】）——按秒计价的组也要有输入图一侧；Seedream 5.0 pro
  0.02 元/张、**每次请求首张免费**，回报 `usage.input_images`（原始张数）。gpt-image / Gemini image 的输入图在 `input_tokens` 里
  （不能按同一输入价核算；GPT Image 当前模态与缓存规则见 [FACT-OPENAI-IMAGE-BILLING-001–003](#gpt-image-token-accounting)）。**张数要在组完请求体之后数**：
  按上限截断、再丢掉读不出的附件——截断后的长度会为没发出去的图收钱。**一张没交付就不该收输入费**（方舟明说失败免费）。
  失败 / 被审核拦下的请求上游是否仍收输入费：【未验】——失败的回包走不到记账，只能对账单。
- **计费相关的请求默认值要明发**（与 [video-generation](video-generation.md) §3 第 6 条同一条）：xAI 不带 `quality` 按 Medium 计（$0.06），不是标价表第一格的
  Low（$0.04）；只发分辨率、本地按「表第一行」估价，会把每张图**低估三分之一**而不报错（坑 123）。默认值写死并发出去，
  用量记录才带得上规格。
- **记账读的中性键是保留键。** 记账层对所有厂商一视同仁地读 `input_image_count` / `reported_cost_usd` 这类**应用自己**的键；
  凡把上游 `usage`（或任何上游 map）**原样铺进** metadata 的地方，都要先剔掉这些键——否则中转或厂商起个同名字段就能定账
  （坑 126）。只有协议自己的换算（tick → 美元、数出来的张数）能写它们，且写在铺之后。聊天四族与 images 各家都有这种原样铺的
  代码（[errors-probing-observability](../../llm-api-integration/references/errors-probing-observability.md) §1 给 DeepSeek 补 `cached_tokens` 的那种地方就是）。**流式出图的每个图片块也要带**这两个键：流在出图后、收尾块前
  被放弃时，记账只看到图片块（坑 127）。设计层（计费组 / 用量行快照 / 档位匹配 / 用量页）见 `ai-usage-accounting` skill。

## 8. 结构化出图结果：拆图层的落库与画布还原（Joycai 2026-09 实现）

一次请求出一组有**叠放关系**的图（底图 + N 个透明图层，各带名字、描述、底图坐标的框），
数据要能跨重启、跨改名还原成原来的画面。

1. **逐图属性是类型化字段，按位置与图对齐，不进通用 metadata。** 响应层
   `imageLayers[i] ↔ generatedImages[i]`；流式时图层信息与它的图**在同一个 chunk** 上。通用
   metadata 跨 chunk 合并，放进去就丢了「哪条属性属于哪张图」。
2. **下载要逐项、保位置。** 通用的「批量解析图片引用」会跳过下载失败的项——后面每张的
   属性全部错位一格。要么逐项下载、失败的位置留空，要么整组失败。
3. **落库按文件路径为主键**，同一次响应一个 `set_id`，列：`z_index`、`name`、`description`、
   `box_left/top/right/bottom`、`created_at`。存图成功后再写；写库失败只记日志、**不丢图**。
   覆盖写同名文件时先删旧行（否则旧图层信息挂在新图上）。这张表是本机索引，**不进备份**
   （路径换机器无意义）。
4. **路径是主键，就要跟着文件走。** 应用内一切改名 / 移动 / 跨目录搬运（改名对话框、AI 批量
   重命名、文件与文件夹移动）都调 `move(old, new)`；文件夹移动按前缀改写（`UPDATE OR REPLACE`，
   目标已有行时以搬来的为准）；删除调 `forget`。为了不让每次文件操作都碰库，维护一个内存索引
   （路径 → z_index，一个可监听值），不在索引里的路径直接跳过——它同时驱动图库卡片上的「图层」角标。
   应用外的改名无法跟踪，行就成了孤儿，读取时文件不存在即忽略。
5. **画布的坐标系是底图像素。** 整个叠放在底图像素网格里摆好，只在最外层整体缩放一次——
   单层分别缩放的话缩放 / 平移时各层会漂移。没有框的层铺满底图。点选 = 从最上层往下找第一个
   可见且框包含该点的层；空白处（含图外地面）取消选择。选中描边用两层描边而**不是 BoxShadow**
   （阴影是填充形状，会把被指的那层染色）。
6. **导出合成图** = 按底图分辨率新建透明画布，可见层自下而上按框拉伸合成；底图隐藏时地面透明、
   画布不缩（图层位置不变）。解码 + 缩放每层几兆像素，放后台 isolate/worker；文件存底图旁
   `<stem>_composite.png`，重名编号 `(2)`、`(3)`，永不覆盖。
7. **实测提醒**：自动拆图时一个人物就是一层，别在 UI 上承诺「头发 / 衣服分层」；要细分得在
   prompt 里点名元素或用 `<bbox>`。

---

## 本篇检查清单

- [ ] 出图入口独立于流式入口；编辑 = `images` 非空，没有第二个函数。
- [ ] 分发按 `ImageRoute` 枚举，route 是 L3 可声明字段；grep 不到按供应商名
      或 model-id 分支的出图代码。
- [ ] `ImageCaps` 全部声明、无探测；`edit:false` 跳过调用；`sizes` 空 = 不发
      size 字段。
- [ ] dashscope route：原生 base 从 compatible-mode base 推导（幂等，裸 host /
      已原生地址均通过）；`extraBody` 并进 `parameters`；尺寸发出前归一成
      `宽*高`；错误解析兼容顶层 `{code,message}` 与 `{error:{…}}` 两种形状。
- [ ] ark route（火山方舟 Seedream）：`watermark` 恒明发（上游默认 true）；档位与 `WxH` 不混发，
      选了比例才查表发像素；按版本出参数表，不支持的字段不发；`max_images` 按参考图数收紧；
      5.0 pro 的拆图层/透明背景在发请求前校验「恰好 1 张参考图」；参考图上限把改图的源图算进去；
      透明背景成对发 `background` + `output_format:"png"`，「无透明像素」400 去字段重试一次，要填满背景的
      改图不开透明（判定交给写指令的一方）；组图单项 `error` 不判整次失败；
      计费按 `generated_images`，`output_tokens` 不进 token 用量键；超时随张数放宽。
- [ ] ark 流式：只对声明了流式的版本、只在官方渠道发 `stream:true`；首块与后续块按单图期限计；
      SSE/JSON 按 body 首行判断；已知事件不做信封检查；边到边存、按已送达记账。
- [ ] minimax：`base_resp` 与 `success_count`（字符串！）两层失败都查；caps `edit:false`；
      images-api：multipart 字段名按张数 `image` / `image[]`；imagen 附图要警告不静默丢。
- [ ] midjourney：task id 出现即入日志；放弃的任务永不重试；用户写的 `--flag` 优先。
- [ ] 单交付物端点 200 但零张图 = 抛错；chat 出图接住 markdown / `images[]` / 裸链接 / 裸 base64
      全部形状，裸内容过两道闸；按字节 SHA-256 去重；按次计费的用量元数据永不为空。
- [ ] 结构化逐图属性（图层）：类型化、按位置对齐、与图同 chunk；逐项下载保位置；按路径落库，
      应用内改名 / 移动带着行走；画布只在最外层缩放一次；合成在后台按底图分辨率做。
- [ ] 异步任务：总 deadline 罩全程；sleep 可被 abort 打断；瞬时失败限次容忍；
      task_id 提交后立刻入日志；FAILED 把 `output` 整段作错误 body。
- [ ] 编辑降级判定：NoImageError 永不触发；结构化 code/param 优先且只认指名
      模型的；prose 正则排除含 param 字样的 body；降级结果带可见的 degraded 标记。
- [ ] 一切 URL 响应当场下载内联（一次重试）；下载校验 content-type；mime 从
      magic bytes 嗅探；multipart 不手动设 Content-Type。
- [ ] 出图调用进 API 日志，异步路径有 mid-call note；per-image 与 token 计费
      相加记账。
