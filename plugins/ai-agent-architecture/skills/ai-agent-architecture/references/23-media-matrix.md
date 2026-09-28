# 23 · 出图 ／ 视频 ／ 语音识别 矩阵

这张表回答：**某个出图／视频／ASR 模型在某个平台上走哪个 route（或线格式）、请求怎么写、尺寸／时长／参考图规则是什么、同步还是异步、响应长什么样、怎么计费、哪些参数会 400、哪些会被静默忽略**。主键 = （route 或线格式，平台，模型）。表是结论，报文细节与原因在 13（出图）、14（视频）、16（ASR）篇里，用「详见」列跳过去；坑的编号指向 11 篇。

图例：

| 记号 | 含义 |
| --- | --- |
| ✅ | 实测生效（发了有效果、回包有对应字段） |
| ❌ | 实测拒绝，**会响**（4xx/5xx 或流内 error），括号里写状态码或原文 |
| 🔇 | **静默失败**：收下 200 但不生效 / 被丢 / 被改写——最危险的一类 |
| 🔀 | 被中转站改写或劫持（写清改成什么） |
| 📄 | 只有文档口径，未实测 |
| — | 未测 / 来源没写 |
| ⚠ | 来源标注为推断或含糊 |

面的编号：① OpenAI Chat Completions ／ ② OpenAI Responses ／ ③ Gemini generateContent ／ ④ Anthropic Messages ／ Ⓓ DashScope 私有 ／ 🖼 出图 ／ 🎬 视频 ／ 🎤 ASR。ASR 线格式：ⓐ OpenAI 兼容转写 ／ ⓑ 百炼同步识别 ／ ⓒ 百炼录音文件转写（filetrans）。证据记法沿用原篇：【实测 YYYY-MM-DD】本库作者在真实服务上跑过；【文档 YYYY-MM】官方文档；【外部实测】他人实测；【实现】来自 pyVideoTrans 等原代码、本库未独立复核报文；⚠ 原文明示未验或含糊。

维护：新增 / 修正按 `30-knowledge-ingestion.md` 的流程；本表每行必须带证据与指针，没有证据的格子写 `—`。被推翻的旧结论在同一格里写「旧：… → 新：…（日期推翻）」不删；文档与实测冲突写「文档：…；实测：…」。

目录：

- [§1 出图](#1-出图)
  - [§1.1 route 速览](#11-route-速览)
  - [§1.2 模型 × 平台 主表](#12-模型--平台-主表)
  - [§1.3 每 route 展开（实测数值）](#13-每-route-展开实测数值)
  - [§1.4 横切不变量](#14-横切不变量)
- [§2 视频](#2-视频)
- [§3 语音识别](#3-语音识别)
  - [§3.1 三种线格式对照](#31-三种线格式对照)
  - [§3.2 模型 × 平台 主表](#32-模型--平台-主表)
  - [§3.3 横切数值附表](#33-横切数值附表)
- [§4 尚未覆盖](#4-尚未覆盖)
- [附录 本表引用的坑](#附录-本表引用的坑)

---

## 1 出图

### 1.1 route 速览

route 按**端点**分发、不按供应商；它是 L3 可声明的枚举，默认按协议族推导（gemini 族 → `gemini`，其余 → `images-api`），显式声明永远赢（13 §2）。surface（图像／视频／对话）由用户声明，id 分类只做默认值；给 chat 兜底路由起名 `chat-image`。中转不提供厂商原生出图协议，例外是路径本身就是 `{base}/images/generations` 的（Seedream `ark`、grok-imagine `xai-images`）。

| route | 端点与判定 | 同步／异步／流式 | 响应形状 | 平台 | 详见 |
| --- | --- | --- | --- | --- | --- |
| `images-api` | `POST /images/generations`；编辑另走 `POST /images/edits`（**multipart**，字段名跟张数走：1 张 `image`、多张 `image[]`） | 同步，一个 JSON body | `data[].b64_json` ／ `data[].url`（`b64_json` 不带 mime，要嗅探 magic bytes） | OpenAI 官方、OpenAI 兼容中继 | 13 §2、§4.2、§6 |
| `chat`（`chat-image`） | `POST /chat/completions`，多模态 user 消息；出图模型纯文本也发成单元素 part 数组；能力保底表必须 `isImageGenerator:true` | 同步（chat 响应） | 中继各放各的：markdown `![image](…)`、`message.images[]`、`message.image_b64_json`、整条回复裸链接／裸 base64——全都要接 | New API 式中继（`nano-banana-pro`、中转上的 `gpt-image-1`、Gemini 出图、Flux…） | 13 §2、§4.2 末条、§6 |
| `gemini` | `POST /models/{id}:generateContent` + `responseModalities:["TEXT","IMAGE"]`；输入图 = 额外 parts | 同步 | `candidates[].content.parts[].inlineData`；可附 text part | Google 官方（AI Studio） | 13 §2 |
| `imagen` | `POST /models/{id}:predict`（**不是** `:generateContent`） | 同步 | `predictions[].bytesBase64Encoded`；**无 usage** | Google 官方 | 13 §2、§4.2、§7 |
| `dashscope` 同步 | `POST {原生base}/services/aigc/multimodal-generation/generation`；原生 base = 供应商行剥 `/compatible-mode/v1` 拼 `/api/v1` | 同步（qwen 全系仅同步；wan2.7 both） | `output.choices[].message.content[].{image}`；URL 24h 过期 | 阿里百炼 DashScope | 13 §3、§4 |
| `dashscope` 异步 | `POST {原生base}/services/aigc/image-generation/generation` + 头 `X-DashScope-Async: enable`（**路径与同步不同**，body 一致）→ `GET /tasks/{id}` | 异步；`PENDING/RUNNING → SUCCEEDED/FAILED/CANCELED/UNKNOWN` | `output.results[].url`；task_id 与 URL 均 24h | 阿里百炼 DashScope（wan2.7 家族） | 13 §4 异步任务流 |
| `ark` | `POST {base}/images/generations`（与 OpenAI 同路径；body 是超集且缺 `n`／`quality`，参考图走 JSON `image` 字段） | 仅同步；`stream:true` 例外（5.0 lite／4.5／4.0） | `data[].{url 或 b64_json, size}`，组图单项可为 `{error}`；流式是 SSE 逐张事件 | 火山方舟 · 按量／套餐；① 族中转站（同路径透传） | 13 §4.1 |
| `xai-images` | `/images/generations`；编辑 `/images/edits`（**JSON**，不是 multipart） | 同步 | OpenAI 形 `data[]`（url／b64）；`usage.cost_in_usd_ticks` | xAI 官方 | 13 §4.2、§7 |
| `minimax` | `POST /v1/image_generation`（挂在 `/v1` 下但**不是** Images API） | 同步但慢（声明「长任务」放宽超时） | `data.image_urls[]` + `base_resp`；逐图计数在 `metadata`；URL 24h | MiniMax | 13 §2、§4.2 |
| `midjourney` | `POST /mj/submit/imagine` → `GET /mj/task/{id}/fetch` | 异步：轮询 3 s、总帽 10 分钟 | 任务记录 `{status, progress, imageUrl, failReason}` | midjourney-proxy ／ New API `/mj/*` | 13 §2、§4.2 |

### 1.2 模型 × 平台 主表

| route | 平台 | 模型 id（含被接受的拼法） | 请求关键字段 | 尺寸／分辨率规则 | 编辑／参考图（张数上限、透明背景） | 响应（url／b64、URL 有效期） | 计费（每张／质量档／输入图／报价字段） | 不支持参数的报法 | 静默失败 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| images-api | OpenAI ／ 兼容 | 通用（route 级） | 生成 JSON；编辑 multipart，1 张 `image`、多张 `image[]`，每个文件 part 显式带 `Content-Type`；**绝不手动设整体 `Content-Type`**（boundary 由运行时生成） | `sizes` 声明为空 = 请求里完全不带 `size`；回显 `size`／`quality` 是定了的规格（请求写 `auto` 时只有回显才有），按规格计价优先用回显 | 编辑 = `images` 非空；`mask` 仅此 route 有 | `data[].b64_json`／`data[].url`；`b64_json` 不带 mime，端点可能按 `output_format` 回 JPEG → mime 从 magic bytes 嗅探 | 用量拼写 `input_tokens`／`output_tokens`（不是 `prompt_/completion_tokens`），记账两种都认；图像输入 $8/M vs 文本 $5/M，`input_tokens_details.image_tokens` 有明细 | ❌ 有中继对默认 `octet-stream` 的 part 回 400【实测 2026-09-05】；`Unsupported parameter: 'x' is not supported with this model.` 带 `param:"x"` = 请求被理解、丢字段即可修（永不触发降级） | 🔇 中继 200 + HTML 错误页 → 不校验 content-type 会写出打不开的 `.png` 且 UI 报成功；中继 200 + `{"error":…}` 零张图要抛错 | 【实测 2026-09-05】（Content-Type）；其余【实现／文档】 | 13 §2、§4.2、§5、§6 | 57、93 |
| images-api | OpenAI | `dall-e-2` | `/images/edits` multipart | — | 编辑单张必须用 `image`（单数）；❌ 只发复数 `image[]` 对单张 400（照它写的中继同样） | `data[]` | — | ❌ 复数字段名对单张 400 | — | 【实现】 | 13 §4.2 | 93 |
| images-api | OpenAI | `dall-e-3` | 同上 | — | — | `data[]` 逐项回 `revised_prompt`（实际画的提示词，放进结果 text） | — | — | — | 【文档／实现】 | 13 §1、§4.2 | — |
| images-api | OpenAI | `gpt-image-1` | 同上 | 尺寸／质量档具体枚举与单价：来源未列（§4 第 22 条） | 参考图上限 **16** | 不回 `revised_prompt` | 输入图在 `input_tokens` 里计（$8/M） | — | — | 【文档／实现】 | 13 §4.2、§7 | — |
| images-api（中继） | New API 式中继 | 仅 Imagen | 中继的 `/images/generations` **只认 Imagen**（❌ "only imagen models are supported"）；Gemini／Flux 图像模型挂在 `/chat/completions` | — | — | — | — | ❌ 非 Imagen 模型被拒 | 同供应商同协议按模型走不同端点 → route 不能从 ApiStandard 推导 | 【实现】 | 13 §2 | — |
| chat（chat-image） | 中继（New API 等） | 任意声明为出图的模型（`nano-banana-pro`、中转上的 `gpt-image-1`、Gemini 出图、Flux…） | `POST /chat/completions`，多模态 user 消息；**出图模型的纯文本也要发成** `[{"type":"text","text":…}]`；对话模型保持字符串 | — | 多模态消息附图 | 全部形状都接：`content` 里 `![image](data:…)`／`![image](https://…)`；`message.images[].image_url.url`／`images[].b64_json`／`images[].url`／裸字符串；`message.image_b64_json`；整条回复裸链接或裸 base64（同中继同模型一小时内两种都见过）；同图三处出现 → 按字节 SHA-256 去重 | — | ❌ 字符串形 `content` → `400 images[0] must be an http/https URL or image data URI`【实测 2026-09-05】 | 🔇 `isImageGenerator` 假了 = 请求成功、图被丢；🔇 对象存储型中继给 https 链接，只认 data URI 就是零张图；裸链接只在声明为出图模型时下载；裸 base64 ≥64 字符且 magic bytes 是图片才收 | 【实测 2026-09-05】（part 数组）；其余【实现】 | 13 §2、§4.2 末条、§6 | 92、110 |
| chat（chat-image） | New API · Gemini 出图走 ① 形状 | Gemini 出图模型 | 出图参数**只认 `extra_body.google.image_config`**（snake_case `aspect_ratio`／`image_size`） | 同左；camelCase 被拒、顶层 `image_config` 不读 | — | 同上行 | — | ❌ camelCase 被拒 | 🔇 宽高比／分辨率发错位置（顶层）静默无效；走 ③ 原生形状时中继**不替你补** `responseModalities`，老模型只回文本（同一模型走 ① 反而更稳） | 【实现】 | 13 §4.2 末条 | 2 |
| gemini | Google 官方（AI Studio） | Gemini 出图模型（原生） | `:generateContent` + `responseModalities:["TEXT","IMAGE"]`；输入图 = 额外 parts | — | 输入图 = parts | `candidates[].content.parts[].inlineData`；可附 text part | 输入图在 `input_tokens` 里（`input_tokens_details.image_tokens`） | — | — | 【实现】 | 13 §2、§7 | — |
| imagen | Google 官方 | Imagen（`:predict`） | `POST /models/{id}:predict` | — | **无编辑**——纯文生图；用户附参考图要显式警告 | `predictions[].bytesBase64Encoded`；**无 usage** | 按次计费；元数据至少放张数，否则 `{}` 在统计里整条消失 | — | 🔇 附参考图若静默丢弃 = 静默失败（要求警告） | 【实现】 | 13 §2、§4.2、§7 | — |
| dashscope 同步 | 阿里百炼 DashScope 原生 | 通用（qwen-image ／ wan ／ z-image 家族） | 顶层只有 `model` 和 `input`；`input.messages[].content` = `{image}`／`{text}` part 数组；旋钮全在 `parameters`（`n`、`size`、`negative_prompt`、`seed`、`watermark`、`prompt_extend`…）；**`extraBody` 并进 `parameters`**；qwen 图在前文在后，wan 文在前图在后（信封相同）；**不走 compatible-mode** | 拼写 **`宽*高`**（`1024*1024`）；发出前把 `1024x1024` 归一（解析放宽 `/[x*×]/`）；**`size` 永远显式发**；发之前按目标模型规则校验，不合规换默认值；所有边长 16 的倍数 | image part 收公网 URL 或 data URL | `output.choices[].message.content[].{image}`；qwen 系只有 `image` 键，wan 系多 `type:"image"`（提图不得依赖 `type`）；**URL 24 小时过期** | qwen 按输出面积分 `qima_output_1k`／`qima_output_2k`；wan 按张，usage 回显 `size` | 错误顶层 `{code, message}`（不是 `{error:{…}}`；任务失败时嵌在 `output`）；`Throttling`／429 = 限流；HTTP 200 带 `code` = body 里的错误 | 🔇 省略 `size` → 出 2048² 并按 2K 档计费【外部实测 2026-09-04】；🔇 `extraBody` 放顶层 = 逃生口整个失效；错误解析不兼容两种形状 → `DataInspectionFailed` 丢 code 掉进 prose 正则 | 【实测 2026-09-19】【外部实测 2026-09-04】【文档 2026-08/09】 | 13 §3、§4 | 58、59、101、102、103 |
| dashscope 同步 | 百炼 | `wan2.7-image-pro` | 同上；`messages` 必须在 `input` 下：❌ 放顶层 → `400 InvalidParameter: Field required: input.messages`【实测 2026-09-19】（顶层写法来自二手文档镜像） | 总像素 768²–4096²（4K 只在文生图语境，改图是否收 4K ⚠）；比例 1:8–8:1；关键字 `1K`／`2K`／`4K`；默认发 `"1K"`；官方格见 §1.3 | 参考图 0–9 张（≤20MB，单边 240–8000px）；特有 `enable_sequential`（组图，n 上限 12）、`bbox_list`、`color_palette`、`thinking_mode`；**不支持 `negative_prompt`** | ✅ 发 `2688*1536` 回 2688×1536；usage `{image_count:1, size:"2688*1536", input_tokens:1351, output_tokens:2}` | 按张；**`n` 默认 4**——不显式 `n:1` 每次花四倍 | `negative_prompt` 不支持（报法未写 ⚠） | 🔇 `n` 默认 4 静默四倍计费；🔇 省略 `size` 出 2048² 按 2K 计 | 【实测 2026-09-19 北京节点 n:1 prompt_extend:false】【文档 2026-09-19】【外部实测 2026-09-04】 | 13 §4 逐模型参数档、自由尺寸表、实测表 | 101、102、104 |
| dashscope 同步 | 百炼 | `wan2.7-image` | 同上 | 总像素 768²–2048²；1:8–8:1；`1K` `2K` | 同 pro（0–9 张） | ✅ 发 `960*1696` 回 960×1696；usage `{image_count:1, size:"960*1696"}` | 按张；`n` 默认 4 | 同上 | 同上 | 【实测 2026-09-19】 | 13 §4 | 102、104 |
| dashscope 同步 | 百炼 | `qwen-image-3.0`、`qwen-image-3.0-pro`、`qwen-image-2.0`、`qwen-image-2.0-pro` | 同通用行（qwen：图在前文在后） | **总像素** 512²–2048²；1:8–8:1；❌ 不收关键字：`"1K"` → 400 `Expected format: '<width>*<height>'`；默认文生图发 `1024*1024` | 参考图 1–3 张（≤10MB）；`n` 1–6；有 `negative_prompt` | ✅ 发 `2304*1728` 回 2304×1728；usage `{output_width:2304, output_height:1728, output_image_type:"qima_output_2k", input_image_type:"qima_input_2k"}` | 按面积落档 `qima_output_1k`／`_2k`；越过 1024² 面积落 2K（1K 档两倍价） | ❌ `"1K"` → 400 点名格式 | 🔇 省略 `size` 出 2048² 按 2K 计 | 【实测 2026-09-19】【外部实测 2026-09-04】【文档 2026-09】 | 13 §4 | 102、103 |
| dashscope 同步 | 百炼 | `qwen-image-edit-max` ／ `qwen-image-edit-plus` | 同上（改图：image part 在前、指令在后） | **单边** 512–2048（不是面积）；缺省约 1024² 且保持原图比例；比例最多 4:1；不收关键字；默认写法：按第一张输入图比例在 1K 面积内重算（16 的倍数） | 1–3 张 | 同上 | 🔇 改图省略 `size` 画幅跟随输入但放大到 2K 面积（768×1376 输入出 1520×2736）按 2K 计【外部实测 2026-09-04】 | — | 🔇 省略 size 静默放大 | 【文档 2026-09，2026-09-19 复核】【外部实测 2026-09-04】 | 13 §4 | 102、103 |
| dashscope 同步 | 百炼 | `qwen-image` ／ `qwen-image-plus` ／ `qwen-image-max`（初代文生图） | 同上 | **只收五个固定值** `1664*928`（缺省）、`1472*1104`、`1328*1328`、`1104*1472`、`928*1664` ⚠ | — | 同上 | — | — | — | 📄【文档 2026-09】⚠ | 13 §4 自由尺寸表 | 103 |
| dashscope 同步 | 百炼 | `qwen-image-edit`（基础版） | 同上 | **不支持 `size`**——唯一不发 size 的模型 | `n` 固定 1 | 同上 | — | ❌ 填 size 即 400 | — | 📄【文档 2026-08】 | 13 §4 | 102 |
| dashscope 同步 | 百炼 | `z-image-turbo` | 同步端点 `multimodal-generation/generation` | ⚠ 未写明 | ⚠ | 同上 | ⚠ | ⚠ | — | 📄【文档】仅列名 | 13 §4 | — |
| dashscope 异步 | 百炼 | `wan2.7-image`、`wan2.7-image-pro` | 提交 `POST /services/aigc/image-generation/generation` + 头 `X-DashScope-Async: enable`（路径与同步不同，body 一致）→ `output.task_id` → `GET /tasks/{id}` | 同同步行 | 同同步行 | `output.results[].url`；`task_id` 与 URL 均 24h；`task_status` 见 §1.1（过期也报 UNKNOWN） | 同同步 | 打错路径报路径级 4xx（声明错了三态会响） | 🔇 FAILED／CANCELED 嵌在 HTTP 200 的 `output` 里 | 📄【文档 2026-08】 | 13 §3、§4 异步任务流 | 60 |
| ark | 火山方舟 · 按量（`/api/v3`）／套餐（`/api/plan/v3`） | 通用（Seedream 家族；`ep-…` 接入点；两个 base） | `POST {base}/images/generations`；`model`／`prompt`／`size`／`response_format` 与 OpenAI 同名同义；**无 `n`／`quality`**；参考图 JSON `image`（URL 或 `data:image/<fmt>;base64,…`，**`<fmt>` 小写**，`image/PNG` 被拒；单张或数组）；**`watermark` 永远明发**（默认 `true` 加「AI 生成」照常计费） | 档位（`1K`／`1.5K`／`2K`／`3K`／`4K`，按模型）或 `WxH` **不可混用**；档位时宽高比由模型从提示词猜；`WxH` 约束**总像素乘积**；`1.5K` 小数档位会撞 `\d+K` 解析 | 组图 `sequential_image_generation:"auto"` + `sequential_image_generation_options.max_images`（1–15，**默认 15**）；**参考图数 + 生成数 ≤ 15**；上限数**全部输入图**（改图源图也占一张）；编辑选区写 prompt：`<bbox>x1 y1 x2 y2</bbox>`／`<point>x y</point>`（0–1000） | `data[]` 每项 `url`（**24h 过期**）或 `b64_json` + `size`；组图单项失败只有 `error{code,message}`（审核不过继续画下一张，500 则停）；顶层 `error` 只在零张时出现；非流式回显 `model` 去日期（`doubao-seedream-5-0-pro`），流式是请求拼写【实测 2026-09-18】 | 按张：`usage.generated_images`（成功张数）是账单口径；`output_tokens` = Σ(宽×高)/256 仅供参考（不进通用 token 键）；`usage.input_images` = 参考图张数；`usage.tool_usage.web_search` = 实际搜索次数；5.0 pro 输入图 0.02 元/张、**每次请求首张免费**；失败免费（方舟明说） | 信封 OpenAI 形 `{"error":{"code","message","param","type"}}`，尾带 Request id；❌ 不支持参数**出图前 400、`param` 点名**「is not supported by the current model」；审核 `InputTextSensitiveContentDetected`／`InputImageSensitiveContentDetected`／`OutputImageSensitiveContentDetected`（永远不是「不能编辑」证据）；免费探测：发非法 `size`（`"1x1"`）→ 支持 `400 InvalidParameter`（含最小像素），不支持 `404 UnsupportedModel` | 🔇 `watermark` 不发加水印；固定 3 分钟超时在组图上把已计费请求判超时（超时按张数放宽：5 分钟起、每张 +40 s、封顶 15 分钟、拆图层按 17 张）；一项 `error` 判整次失败丢掉已计费的图；校验顺序不固定（lite 先报 `size`，pro 先报 `background`）→ 报的是别的字段 = 没问到 | 【文档 2026-09-18／09-22】【实测 2026-09-18、2026-09-23 套餐 key】 | 13 §4.1；01 §9.3 | 79、80、81、82、83、84、131 |
| ark | 火山方舟 · 套餐 | `doubao-seedream-5.0-pro`（收 `doubao-seedream-5.0-pro`、`doubao-seedream-5-0-pro-260628`；回显 `doubao-seedream-5-0-pro`） | 同上；`optimize_prompt_options.mode: standard/fast`；`output_format: png/jpeg`（只能发给 5.0） | 档位 1K·1.5K·2K；`WxH` 总像素区间 [921600, 4624220]；✅ `1K` 无比例提示回 `1248x832`（3:2）；拆图层时 `size` 只收档位或 `auto` | 参考图 **10**（❌ 11 张 → 400「number of reference images cannot exceed 10」【实测 2026-09-23】）；组图 ✗；联网 ✗；专属：图层拆分、透明背景 | 同上 | 同上 | ❌ **不支持流式**（`stream:true` → `400 InvalidParameter param:"stream"`）；❌ `sequential_image_generation:"auto"`／`tools:[{type:"web_search"}]` → 各 400 `param` 为该字段；❌ `output_format:"webp"` → 400「must be one of: jpeg, png」 | 见透明背景行 | 【实测 2026-09-18、2026-09-23】 | 13 §4.1 | 81、131 |
| ark | 火山方舟 · 套餐 | `doubao-seedream-5.0-pro` **`layer_decomposition:true`** | 同上 + `layer_decomposition:true`；与 `background:"transparent"` 互斥模式（不是开关组合）；要求**恰好 1 张参考图**——发请求前客户端检查，抛不重试不计费的错 | `size` 只收档位或 `auto` | 恰好 1 张 | 底图 + 最多 16 个带透明通道图层；`data[]` 按 `z_index` 排，图层带 `name`、中文 `description`、`bounding_box.absolute`（**底图像素**非输入图像素）与 `.normalized`（0–1000）；任一层失败 = 整个请求失败；实测形状见 §1.3 | `usage.generated_images` = 实出张数（2），不是超时预算的 17；`usage.input_images:1` | — | 自动拆时整个人物是**一层**，不再拆头发／衣服——UI 别承诺 | 【实测 2026-09-18】 | 13 §4.1 拆图层实测形状、§8 | 82、88 |
| ark | 火山方舟 · 套餐 | `doubao-seedream-5.0-pro` **`background:"transparent"`** | 同上 + `background:"transparent"`；只用于图生图；输出恒 png，**要 png 必须明发 `output_format:"png"`**（成对出现）；只对**改图**开 | — | 恰好 1 张且带 alpha（至少一个透明像素）。校验全部出图前 400 零成本、`param` 点名：❌ 无图或 ≥2 张 → `param:"background"`「transparent background requires exactly one input image」；❌ 同时 `output_format:"jpeg"` → `param:"output_format"`「must be png when background is transparent」；❌ RGB PNG／无 tRNS 调色板 PNG／有 alpha 但全不透明 → `param:"image"`「transparent background requires a PNG input with at least one transparent pixel」（上游解码后判定；客户端只读头部时收到这条 400 **去掉两个字段重试一次**） | `data[]` 多 `output_format:"png"`；`usage.input_images:1` | 每张计费（实测各 1 张） | 见左 | 🔇 **语义是「结果背景透明」不是锁原图轮廓**：透明底红圆「改成蓝色」→ 圆外全透明 ✅；透明底箭头「改成竖直向上」→ 按新形状重画 ✅；透明底红圆「加上蓝天白云背景」→ 圆外依旧透明、天空画进圆里，200 计费（坑 130）。**旧：「透明模式锁死原图 alpha 遮罩」→ 新：主体可变形、只保证结果背景透明（2026-09-23 箭头改向实测推翻）**；「输入是透明 PNG 就自动开」是错的；参考实现 `keep_transparency` 参数默认保留 | 【实测 2026-09-23 pro，31 次零成本探测 + 4 张计费】【文档 2026-09-22】 | 13 §4.1 透明背景 | 130、132 |
| ark | 火山方舟 · 按量 | `doubao-seedream-5.0-flash`（`doubao-seedream-5.0-flash`／`-5-0-flash`／`-5-0-flash-260915`） | 与 pro 参数表相同，只少 `fast`（提示词优化仅 standard） | 1K·1.5K·2K（与 pro 同表同区间） | 参考图 10；组图 ✗；联网 ✗；专属：图层拆分、透明背景 📄【文档 2026-09】 | 同 pro | — | ❌ **套餐 key 不服务**：三种拼法均 `404 UnsupportedModel`，只在按量 | ⚠ 流式未写明 | 📄【文档 2026-09】【实测 2026-09-23 套餐 404】 | 13 §4.1 能力表、400 表；01 §9.3 | 81、130 |
| ark | 火山方舟 · 套餐 | `doubao-seedream-5.0-lite`（收 `doubao-seedream-5.0-lite`、`doubao-seedream-5-0-lite-260128`；❌ 不带 `lite` 的 `doubao-seedream-5-0-260128`——按量文档 lite 正式 id——套餐 404） | 同通用行；联网 `tools:[{type:"web_search"}]`；提示词优化仅 standard | 档位 2K·3K·4K；`WxH` 下限 3686400（2560×1440），`1500x1500` 无效 | 参考图 **14**（❌ 15 张 → 400「cannot exceed 14」【实测 2026-09-23】）；组图 ✓ | 同上；2K 单张实测 26 s；流式见 ark 流式行 | 同上 | ❌ `optimize_prompt_options.mode:"fast"` → 400「optimize_prompt_options.mode must be 'standard'」【实测 2026-09-23】；❌ `output_format:"webp"` → 400 | — | 【实测 2026-09-18、2026-09-23】 | 13 §4.1；01 §9.3 | 81、131 |
| ark | 火山方舟 · 按量 | `doubao-seedream-4.5` | 输出格式**仅 jpeg**（不发 `output_format`）；提示词优化 standard | 档位 2K·4K | 参考图 14；组图 ✓；联网 ✗ | 同上 | 同上 | ❌ 套餐 key 404 `UnsupportedModel` | — | 📄【文档 2026-09-18】【实测 2026-09-23 套餐 404】 | 13 §4.1 | 81 |
| ark | 火山方舟 · 按量 | `doubao-seedream-4.0` | 输出格式仅 jpeg；提示词优化 standard/fast | 档位 1K·2K·4K | 参考图 14；组图 ✓；联网 ✗ | 同上 | 同上 | ❌ 套餐 key 404 `UnsupportedModel` | — | 📄【文档 2026-09-18】【实测 2026-09-23】 | 13 §4.1 | 81 |
| ark 流式 | 火山方舟 · 套餐（官方渠道） | 5.0 lite（实测）／4.5／4.0（文档）；5.0 pro 不支持 | `stream:true`；只在官方渠道、且表上声明流式的版本发；中转照旧同步（是否透传 SSE 未知） | 只发档位时两张都自选 16:9（2848×1600） | 组图上限按 `max_images` | SSE，`event:` 与 `data.type` 同名：`image_generation.partial_succeeded`（`image_index` 从 0、`url`、`size`）、`partial_failed`（带 `error`）、`image_generation.completed`（`usage`）、`data: [DONE]`；**响应头等第一张画完才回**（≈27 s）；App 内第一张 27.9 s、第二张 48.4 s | 按已送达张数记账；`usage` 只在 `completed`（`generated_images:2, output_tokens:32448`）；每个图片块也要带 `input_image_count`／`reported_cost_usd` | ❌ **参数校验失败不走 SSE**：`stream:true` 照样回 `400 application/json`；200 时 SSE 还是 JSON 看 **body 首行**不看 Content-Type | 🔇 聊天「首块 120 s 空闲守卫」掐掉已计费请求；通用信封检查把 `partial_failed` 的 `error` 当整次失败丢掉已到的图；只在流跑完记用量 = 取消的任务统计里消失钱照扣；拒收 `stream` 的中转把能用渠道变 400 | 【实测 2026-09-18 5.0 lite】 | 13 §4.1 流式出图 | 85、86、87、127 |
| ark | ① 族中转站 | Seedream（认得出的 id） | 默认 route 也是 `ark`（路径 = `{base}/images/generations`，无私有路径推导）；要求中转原样透传 Images API 的 body | — | — | — | — | — | 中转是否透传 SSE 未知 | 【实现】 | 01 §9.3；13 §4.1 | — |
| ark | 火山方舟 | Endpoint ID `ep-…`（推理接入点） | 从 id 看不出哪一代，分类失败是正常：让作者点单（声明出图模型 + 选 `ark` route） | — | — | — | — | — | — | 📄【文档】 | 01 §9.3 | — |
| xai-images | xAI 官方 | `grok-imagine-image-2.0` | `/images/generations`；编辑 `/images/edits`（**JSON**）：1 张 `image:{url:<data URI>}`，2–3 张 `images:[{url}…]`（互斥），prompt 里 `<IMAGE_0>` 指代；`aspect_ratio` 收 `auto`；`resolution: 1k／1.5k／2k`（不是 `size`；`sizes` 声明空 = 不带 size）；`response_format:"b64_json"` 省一次下载；`quality: low／medium／high／auto`（**不带 = medium**）；`GET /v1/image-generation-models/{id}` 回 `image_price` + `pricing[{quality, resolution, price_per_image}]` | `resolution` 1k／1.5k／2k（`1.5k` 只有 2.0 收） | 参考图上限：**文档：3 张【文档 2026-09】；实测：5 张 HTTP 200 并按 5 张收费【实测 2026-09-21】**——旧：「最多 3 张」→ 新：按 5 截断（2026-09-21 推翻） | OpenAI 形 `data[]`（url／b64）；`respect_moderation:false` 之类会让 `url`／`b64` 都空 → 空即失败 | `usage` 只有 `cost_in_usd_ticks`，**1 tick = $10⁻¹⁰**（实测 400 000 000 = 1K·Low $0.04）；六格见 §1.3；2.0 只收 `low/medium/auto`；输入图 **$0.01/张、线性、无免费张数**，`n:2` 时按请求收一次；报价含输入图、**整单实扣、替换不叠加**；回包没有输入张数；`quality: auto` 由模型定档（一次实测选 Low）——按规格表写不出 | ❌ `quality` 非枚举 → **422**（列出枚举）；❌ 2.0 发 `high` → 400 `This model only supports the following quality value(s): low, medium, auto.`；❌ `size` 字段 → 400 | 🔇 不带 `quality` 按 Medium（$0.06）计，本地按表第一行 Low 估价每张**低估三分之一**不报错；OpenAPI（`docs.x.ai/openapi.json`）请求体**没列** `quality`——文档与 OpenAPI 不一致以实测为准；经中转透传的 `cost_in_usd_ticks` 是 xAI 收中转的价 | 【文档 2026-09】【实测 2026-09-21、2026-09-22】 | 13 §4.2、§7 | 123、124、126、128 |
| xai-images | xAI 官方 | `grok-imagine-image`（初代，$0.02）、`grok-imagine-image-quality`（$0.05） | 同上 | ❌ `resolution: 1.5k` → 400 `1.5K resolution is not supported for this model.` | 同上 | 同上 | `pricing: []`（各质量同价） | ❌ `1.5k` → 400 点名 | 🔇 **默默收下 `quality`** 无效果（骗人的旋钮，UI 别给） | 【实测 2026-09-22】 | 13 §4.2 | 125 |
| minimax | MiniMax | `image-01`、`image-01-live` | `POST /v1/image_generation`；`aspect_ratio`（8 种）与 `width/height`（512–2048、8 的倍数、仅 `image-01`）是同一件事两种拼法；`n` 1–9；`style` 仅 `-live`；`aigc_watermark` 默认关 | `aspect_ratio` 8 种 或 `width/height` 512–2048（8 的倍数） | **没有编辑**——只有 `subject_reference[{type:"character", image_file}]` 主体参考（把参考图里的**人物**带进新画面）；caps 声明 `edit:false` | `data.image_urls[]` + `base_resp`；逐图计数在 `metadata`；URL **24h 过期** | 按次；不回 token → 元数据至少放张数 | 两层失败：`base_resp.status_code≠0` 请求级（过期 key、余额、审核都是 **HTTP 200**）；`status_code==0` 但 `metadata.success_count==0` 逐图失败 | 🔇 喂风景图要求调色返回一张无关的图；🔇 **`success_count`／`failed_count` 是字符串**（`"0"`／`"3"`），按数字判永不命中；只看 `base_resp` 时逐图失败症状只是「结果为空」 | 【实现／文档】（docs/api/minimax.md） | 13 §2、§4.2、§7 | 6、90、91 |
| midjourney | midjourney-proxy ／ New API `/mj/*` | Midjourney（内置目录，代理没有 `/models`） | `POST /mj/submit/imagine` → `GET /mj/task/{id}/fetch`；垫图 `base64Array`；参数（比例、版本、stylize、chaos、quality）UI 下拉，发出前改写成 `--ar/--v/--s/--c/--q` 拼进 prompt；**用户自己写的 flag 优先**；`--v niji 6` 改写成 `--niji` | 由 `--ar` 表达 | `base64Array` 垫图（张数上限未写 ⚠） | 任务记录 `{status, progress, imageUrl, failReason}`；提交回执 `code` 1 = 成功、22 = 排队中（也算建好）；每次进度推成一个文本 chunk | 按次 imagine（单价未写）；放弃时抛「已放弃的任务」且**永不重试**（重试 = 再付一次） | — | 🔇 task id 出现前不入日志 → 轮询死了无线索 | 【实现，日期未标】⏳待复核 | 13 §2、§4.2 | 60 |

### 1.3 每 route 展开（实测数值）

**dashscope（百炼 qwen-image ／ wan）**

- 实测表【实测 2026-09-19，北京节点，每次 `n:1`、`prompt_extend:false`】：返回像素（读 PNG IHDR）与发送的 `size` 完全一致——自由 `宽*高` 在两个家族上照原样出图，不被悄悄改尺寸。

| 模型 | 发送 `size` | 返回 | usage 要点 |
| --- | --- | --- | --- |
| wan2.7-image-pro | `2688*1536`（16:9 · 2K 官方格） | 2688×1536 | `{image_count:1, size:"2688*1536", input_tokens:1351, output_tokens:2}` |
| qwen-image-3.0 | `2304*1728`（4:3，≈3.98 MP） | 2304×1728 | `{output_width:2304, output_height:1728, output_image_type:"qima_output_2k", input_image_type:"qima_input_2k"}` |
| wan2.7-image | `960*1696`（9:16 · 1K） | 960×1696 | `{image_count:1, size:"960*1696"}` |

- wan 官方推荐尺寸【文档 2026-09-19】：`1K`=1024²、`2K`=2048²、`4K`=4096²；16:9 → 1696×960 ／ 2688×1536 ／ 4096×2304；4:3 → 1472×1104 ／ 2368×1728 ／ 4096×3072（竖版对调）。**2688×1536 是 1.75:1 不是 1.778:1** → 反查比例芯片要 3% 容差，认出后用芯片精确比例（坑 104）。
- size 与计费档【外部实测 2026-09-04】：qwen-image-3.0-pro 与 wan2.7-image-pro 省略 `size` 都出 2048² 按 2K 档计（qwen 是 1K 档两倍价）；qwen 改图省略 `size` 画幅跟随输入但放大到 2K 面积（768×1376 → 1520×2736）。qwen 越过 1024² 面积落 2K 档——尺寸选择器要标出计费档。
- 尺寸校验器要能表达「面积区间」（qwen-image-3.0／2.0、wan）与「单边区间」（qwen-image-edit-max／plus）两类规则；初代 qwen-image 只收五个固定值；`qwen-image-edit` 基础版不收 `size`；`2K` 关键字无宽高比信息只作兜底（13 §4）。
- 异步轮询【文档 2026-08】：官方建议 5–10 s、前 30 s 密集；参考实现 ~3 s 起步、十来次后 5 s；总 deadline 600 s 罩提交 + 轮询 + 下载，与调用方 signal 合成喂给每次 fetch 和 sleep；瞬时失败连续 3 次才抛；task_id 提交成功立刻写 mid-call note；FAILED／CANCELED／未知 → 抛错并把 `output` 整段作错误 body。
- 限流：`Throttling`／429；RPM 数值来源未写（§4 第 21 条）。

**ark（火山方舟 Seedream）**

- 用时【实测 2026-09-18】：5.0 pro 1K 单张 **43 s**；5.0 pro 拆图层 **37 s**（1500×1920 单人立绘，`size:"1K"`，不写 prompt）；5.0 lite 2K 单张 **26 s**；流式 5.0 lite（套餐、`2K`、组图上限 2）第一张 **27.9 s** 落盘、第二张 **48.4 s**；响应头 `x-envoy-upstream-service-time` ≈ 27 s。
- 逐请求超时公式（13 §4.1）：5 分钟起，每多一张 +40 s，封顶 15 分钟；拆图层按 17 张算。
- 版本能力表【文档 2026-09-18／09-22】：

| 版本 | 档位 | 参考图 | 组图 | 输出格式 | 提示词优化 | 联网 | 专属 | 套餐 key |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5.0 pro | 1K·1.5K·2K | 10 | ✗ | png/jpeg | standard/fast | ✗ | 图层拆分、透明背景 | ✅ |
| 5.0 flash | 1K·1.5K·2K | 10 | ✗ | png/jpeg | standard | ✗ | 图层拆分、透明背景 📄 | ❌ 404 |
| 5.0 lite | 2K·3K·4K | 14 | ✓ | png/jpeg | standard | ✓ `tools:[{type:"web_search"}]` | — | ✅ |
| 4.5 | 2K·4K | 14 | ✓ | 仅 jpeg | standard | ✗ | — | ❌ 404 |
| 4.0 | 1K·2K·4K | 14 | ✓ | 仅 jpeg | standard/fast | ✗ | — | ❌ 404 |

- `WxH` 像素区间：5.0 pro [921600, 4624220]；5.0 lite 下限 3686400（2560×1440），`1500x1500` 无效。5.0 pro `1K` 无比例提示回 `1248x832`（3:2）；lite 流式只发档位两张都自选 2848×1600。
- 拆图层实测形状【实测 2026-09-18】：200，`data[]` 两项：`z_index:0` 底图 912×1168 jpeg（人物抹掉只剩背景）；`z_index:1` 图层 861×1137 RGBA png，带 `name`、中文 `description`、`bounding_box.absolute:[27,0,888,1137]`（底图像素）与 `.normalized`（0–1000）。`usage.generated_images:2`、`usage.input_images:1`。落库与画布还原见 13 §8。
- 透明背景四次计费实测【实测 2026-09-23】：红圆改蓝 ✅；箭头改向（新箭尖处不透明、旧箭杆处变透明）✅；「加上蓝天白云背景」→ 圆外依旧透明、天空画进圆里 ❌ 静默（坑 130）。31 次零成本探测确认三条 400 文案（见主表）。
- 不支持参数的 400 表【实测 2026-09-23 套餐 key】：pro `sequential_image_generation:"auto"`／`stream:true`／`tools:[{type:"web_search"}]` → 各 400 `param` 为该字段「is not supported by the current model」；lite `optimize_prompt_options.mode:"fast"` → 400「mode must be 'standard'」；pro／lite `output_format:"webp"` → 400「must be one of: jpeg, png」；5.0 flash 三拼法、4.5、4.0 → 套餐 404 `UnsupportedModel`。探测只有「先于必错字段校验」的那个才点名，校验顺序不固定。
- 计费口径：`usage.generated_images` 是账单；`output_tokens` = Σ(宽×高)/256（流式实测 `generated_images:2, output_tokens:32448`）；`usage.input_images` 实测拆图层 1、文生图 0；`usage.tool_usage.web_search` 0 = 开了联网但没搜【文档 2026-09-18】；5.0 pro 输入图 0.02 元/张、每次请求首张免费；失败免费。失败／被审核拦下是否仍收输入费【未验】。
- 套餐 vs 按量【实测 2026-09-18／09-23】：套餐 base `https://ark.cn-beijing.volces.com/api/plan/v3`，按量 `https://ark.cn-beijing.volces.com/api/v3`；套餐 key 打按量 base 401；套餐 `GET /api/plan/v3/models` 404 非 JSON → 退回静态目录，再发最小补全定论（错 key 401、造的 id 404 `UnsupportedModel`）；变体按地址回读（去尾斜杠比对），否则套餐渠道被「恢复」成按量 base 之后每次 401（坑 80）。

**xai-images（Grok Imagine）**

- 六格价目（`grok-imagine-image-2.0`，`GET /v1/image-generation-models/{id}`）【实测 2026-09-21／22】：1K·Low $0.04 ／ 1.5K·Low $0.05 ／ 2K·Low $0.06 ／ 1K·Medium $0.06 ／ 1.5K·Medium $0.07 ／ 2K·Medium $0.08。`price_per_image` 单位 "1/100,000,000ths of a USD cent" = 1 tick = $10⁻¹⁰。
- 输入图计费【实测 2026-09-22】：1 张参考图 + `n:2` + low = 900 000 000 = 2 × $0.04 + 1 × $0.01（按请求收一次、不乘输出张数）；5 张参考图 + medium 1K = $0.06 + 5 × $0.01 = 1 100 000 000。
- 初代 `grok-imagine-image` $0.02、`grok-imagine-image-quality` $0.05：`pricing: []`。
- `quality: auto` 一次实测选了 Low（$0.04）；有上游报价按报价记，UI 不提供 `auto`（坑 124）。

**minimax**：`width/height` 仅 `image-01`；`n` 1–9；`style` 仅 `-live`；URL 24h；两层失败与字符串计数见主表；无编辑（`subject_reference` 是主体参考，坑 91）。

**midjourney**：轮询 3 s、总帽 10 分钟；回执 `code` 1 成功、22 排队中；垫图张数上限与单价未写（§4 第 8 条）。

**images-api ／ chat-image ／ gemini ／ imagen**：无本库实测数值；仅 Content-Type 400【实测 2026-09-05】与 part 数组 400【实测 2026-09-05】两条为实测，其余【实现／文档】。

### 1.4 横切不变量

只列结论 + 指针，原因在 13 篇。

1. 出图入口是流式入口的兄弟：独立函数 `出图(连接, 请求) -> 结果`，`images` 非空即编辑，不拆两个入口（13 §1）。
2. route 按端点分发、不按供应商；新增 route 清单固定五项（枚举值 + dispatch case + 设置下拉 + i18n + 测试 describe）；route 永不做新默认值（13 §2）。
3. **永不探测出图**：能力全部声明（`edit`、`sizes`、`maxRefs`、`route`、`asyncTask` 三态 sync-only／async-only／both），运行期证明错了才可见降级；图像端点的探测 = 一次真实计费的生成（13 §3）。唯一的零成本探测是 ark 的非法 `size`（400 = 支持、404 = 不支持）。
4. **编辑降级判定只认「路由缺失」证据**：404／405／501；结构化 code/param 只认指名模型的（`param === "model"`／model_not_found）；`param:"x"` = 丢字段即可修；NoImageError 永不触发；prose 正则排除含 param 字样；降级带可见 `degraded` 标记。宽松方向误判 = 二次全价计费（13 §5；坑 57）。
5. **响应归一到字节**：URL 一律当场下载内联，一次重试；校验 content-type；mime 从 magic bytes 嗅探；识别 `url` 字段里的 `data:` 前缀；multipart 不手动设 Content-Type；单交付物端点 200 但零张图 = 抛错；解析顺序：状态码 → 是否 JSON → 形状 → 错误信封（13 §6；坑 56）。
6. chat 出图接住所有形状；裸链接只对声明为出图模型下载；裸 base64 ≥64 字符且 magic bytes 是图片；按字节 SHA-256 去重（13 §6；坑 92）。
7. **计费口径**：per-image 与 token **相加**记账；上游直接报钱（`cost_in_usd_ticks`）的面**替换不叠加**、只在自家协议上读；「没报」与「报了 0」分开存（NULL vs 0）；按次计费的用量元数据永不为空（至少张数）；像素折算 token（Seedream `output_tokens`）不进通用 token 键；输入图按张与输出分开标价，张数在组完请求体之后数，一张没交付不收输入费；计费相关默认值明发（xAI `quality`、wan `n`、千问视频 `audio`、ark `watermark`）；记账中性键 `input_image_count`／`reported_cost_usd` 是保留键，铺上游 `usage` 前先剔掉，流式每个图片块也带（13 §7；坑 83、123、126、127）。
8. 出图调用进同一份 API 日志；日志器加 mid-call `note(data)` 通道，异步 task_id 是第一个用例（13 §7；坑 60）。
9. 尺寸发之前按目标模型规则校验，不合规换默认值而非转发吃 400；校验器表达面积区间 + 单边区间；关键字预设不参与按 aspect 挑选（13 §4；坑 103）。
10. Seedream：`watermark` 永远明发；档位 + 比例两个控件，`WxH` 只查 L3 映射表；能力逐版本建档、不支持字段不发；`max_images` 按参考图数收紧、源图算进上限；5.0 pro 专属任务互斥分段控件、「恰好 1 张」客户端校验；透明背景「无透明像素」400 去字段重试一次；组图单项 `error` 不判整次失败；回显 `model` 流式／非流式分开对待（13 §4.1）。
11. 拆图层结果：逐图属性类型化、按位置与图对齐、与图同 chunk；逐项下载保位置；按文件路径为主键落库、不进备份（13 §8；坑 88）。

---

## 2 视频

视频没有同步形态——全行业一律「提交拿 task_id → 轮询 → 结果 URL」。统一形状：`提交(连接, 请求) -> task id`、`轮询(连接, task id) -> {done:false, status?} 或 {done:true, videoUrl}`，失败一律抛错不进返回值；首帧／尾帧／参考素材统一 `media[].role`（`first_frame`／`last_frame`／`reference_image`／`reference_video`／`reference_audio`），adapter 转各家拼写（14 §1）。

| 平台 | 模型 | 提交端点与 body 关键字段 | 轮询端点与状态词 | 参考图／首帧 | 时长／分辨率 | 计费 | 失败／超时行为 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 阿里百炼 千问 | `wan3.0` | `POST /api/v1/services/aigc/video-generation/video-synthesis` + 头 `X-DashScope-Async: enable`；`input.prompt`（≤2 万字符，可用「图1」指代素材）+ `input.media[]{type, url}`；`parameters`：`resolution`（480P/720P/1080P，默认 1080P）、`ratio`（adaptive/16:9/…）、`duration`（2–30s，`-1` 智能）、**`audio` 默认 true**、`prompt_extend` 默认 true | `GET /api/v1/tasks/{id}`（与图片任务、ASR filetrans 共用）；`PENDING/RUNNING/SUCCEEDED/FAILED/CANCELED/UNKNOWN`；结果 `output.video_url`（顶层扁平） | `input.media[].type` 标 role（首帧／尾帧／参考） | 2–30s；480P/720P/1080P | usage 报秒数/fps/分辨率，无 token：`video_count`(=1)／`duration`／`fps`／`SR`／`ratio`；🔇 `audio:true` 默认直接乘在账单上 → 显式发 | 🔇 失败 `task_status: FAILED` 装在 HTTP 200，错误码在 `output.code/message`；task_id **24h** 保留，过期 = 查无此任务（独立错误「任务已过期」，不重试不报 FAILED）；`UNKNOWN` 是已知终态要进抛错分支；无取消端点；结果 URL 24h，下载 GET 不带 API 认证头 | 【实测 2026-08-29，Joycai 用户账号】创建 → 轮询 → 取结果跑通；失败态与取消分支**未走到**；【文档 2026-08 全量核对】 | 14 §2、§3；01 §8.1 | 60、126 |
| MiniMax | `MiniMax-H3`（v2 API） | `POST /v2/video_generation`（`api.minimaxi.com`；base 从 chat 行剥 `/v1` 或 `/anthropic/v1` 拼 `/v2/…`）；`content[]`（至少一个 text 项 ≤7000 字符 + 媒体项）；媒体项**嵌套** `{"type":"image_url","image_url":{"url":…},"role":"first_frame"}`，`role` 与 `type` 平级，`first_frame`／`last_frame`，两个媒体项放同一 `content[]`；**`resolution`（768P/2K）与 `duration`（4–15s）必填、无服务端默认**；可选 `callback_url`（注册时 3 秒内回显 challenge）；创建响应 `{"task_id": "…"}` | `GET /v2/query/video_generation/{id}`；`queued/running/succeeded/failed/cancelled`；结果 `task.content.url`（直链；v1 的 file_id→retrieve 二段式已废除） | ✅ 首帧 + 尾帧跑通；媒体项旁边**必须有 text 项**（纯图生视频也要）；带媒体时 `ratio:"adaptive"` 原样接受 | 4–15s；768P／2K（✅ `2K` 接受并正常出片；`768P` 未实测） | usage 报秒数 + token 双口径（相加记账） | 🔇 失败 `task.error` 在 HTTP 200；任务记录保留 **7 天**；取消 `DELETE /v2/video_generation/{id}` **仅 `queued` 可取消**（免扣费），succeeded/failed 变删除记录，running 不可操作；❌ 缺 resolution/duration → 400 | 【实测 2026-08-29，首帧+尾帧全链路，来源 Joycai】；未实测：纯文生视频 `ratio` 替换、帧与参考素材互斥、`reference_image` role、取消 DELETE、`768P` | 14 §2、§3；01 §8.1 | 113（🔇 平铺 `"url"` 静默失败：解析器照收、任务成功、照样计费，只当没附图——「跑通」判据是出片遵守首尾帧不是 HTTP 200） |
| xAI 官方 | `grok-imagine-video-1.5` | `POST /v1/videos/generations`（JSON）；提交回包只有 `{"request_id"}`；`GET /v1/video-generation-models` 只列 id／模态／别名，**没有 `pricing`**；`input_modalities` = text／image／audio（`reference_audios`） | `GET /v1/videos/{request_id}`；pending 是 **HTTP 202** + `{status: pending, progress}`；done 是 200 + `{status: done, video: {url, duration, respect_moderation}, model, usage: {cost_in_usd_ticks}, progress: 100}`；词表 `pending/done/expired/failed` | 首帧 `image`；`reference_images`；`reference_audios` | 实测三条 1 s · 480p；`video.duration` 报实际渲染秒数（可用于结算）；`duration: 1` 按 1 s 计，无最低计费秒数；720p／1080p 是否加价【未验】 | 标价页只写 $0.080/s；**报价只在终态回包** `usage.cost_in_usd_ticks`（OpenAPI `VideoResponse.usage` 是 `MediaUsage`，`cost_in_usd_ticks` 必有，token 字段视频一律省略）；文生 800 000 000 = $0.08；首帧 `image` 900 000 000 = +$0.01；`reference_images` 两张 1 000 000 000 = +$0.02 → **$0.01/张、线性**，与出图面同价；提交时按请求秒数先记一行，终态用报价改写整行 | `video.url` 为空且 `respect_moderation: false` = 被审核拦下；`expired` 是已知终态要抛错 | 【实测 2026-09-22，来源 Joycai】 | 14 §2、§3 第 8 条；13 §7；01 §9.1 | 129（只改写秒数的结算漏掉参考图 $0.01/张） |
| xAI 官方 | `grok-imagine-video`（初代，$0.050/s） | `input_modalities` = text／image／video（`/videos/edits`、`/videos/extensions`） | 同上 | — | — | $0.050/s | **已下线（2026-09-22），不再追** | 【实测 2026-09-22】 | 14 §2 | — |
| OpenAI 官方 | Sora | `POST /v1/videos`（**multipart**） | `GET /v1/videos/{id}` + `/content` 下载；`queued/in_progress/completed/failed` | ⚠ 未写 | ⚠ | ⚠ | `/content` 是 API 端点，下载**要带**认证头（与签名直链相反）；`/content` 流式下载；保留期／取消 — | 📄【文档】⚠ 未标注实测 | 14 §2、§3 第 4 条 | — |
| Google 官方 | Veo | `:predictLongRunning` | operations `GET`；`{done: bool}`；结果在 operation response 内 URI | ⚠ | ⚠ | ⚠ | 🔇 轮询把 operation body 整个当内部信封（坑 126）；保留期／取消 — | 📄【文档】⚠ | 14 §2 | 126 |
| 火山方舟 · 套餐 | Seedance（`doubao-seedance-1-0-pro-250528`、`-1.0-pro`、`-2.0`、`-1-0-lite-t2v-250428`） | 订阅套餐 base 上 `/contents/generations/tasks` | — | — | — | — | ❌ 四个 id 全回 `404 UnsupportedModel`——要按量 key；协议形状本库**未覆盖** | 【实测 2026-09-18】 | 14 §2；01 §9.3 | — |
| 中继（New API 等） | sora、grok-imagine、wan2.5、kling、hailuo… | 收敛到 OpenAI 式 `/v1/videos`（openai-videos 协议） | 同 OpenAI 式 | — | — | — | **同一个模型 id 在官方与中继上走不同协议**：官方行 video 槽位指向私有协议，中继行指向 openai-videos，model id 不变；按 model-id 硬编码路由会在一边坏掉 | 【实现】 | 14 §4 | — |

横切不变量（14 §3，漏一条就是一类静默失败）：

1. **失败装在 HTTP 200 里**：千问 `output.code/message`、MiniMax `task.error`；轮询面跳过通用错误信封检查，状态机自己报错并保留结构化 code（审核类 code 丢了会被误判）。
2. **状态词表逐家归一化**：未知状态当 in-progress 容忍但受总 deadline 罩；已知终态（CANCELED／expired／UNKNOWN）显式进抛错分支。
3. **过期 task_id ≠ 失败任务**：MiniMax 7 天、千问 24h；过期后查到的是「查无此任务」，报成独立错误「任务已过期」，不重试不报 FAILED。
4. **结果 URL 当场下载**：签名直链**不带** API 认证头，Sora `/content` 是 API 端点**要带**；校验 content-type + magic bytes（同 13 §6）。
5. **取消分两层**：本地放弃轮询 ≠ 上游停止计费；有取消端点的（MiniMax 仅 queued）先试上游取消，失败静默降级为本地放弃；无取消端点的家 UI 别承诺「已取消」。
6. **计费相关默认值显式下发**：`audio: true`（千问）、`n: 4`（wan 图片）直接乘在账单上。
7. **必填无默认参数是 L3 参数表的责任**：MiniMax `resolution`／`duration` 不发就 400，缺省由模型能力表声明，adapter 只读不编。
8. **usage 两套口径并存**（按秒／按张 vs token）相加记账；上游直接报钱（xAI `cost_in_usd_ticks`）替换不叠加，且**只在 done 回包**——提交时按请求秒数先记一行，终态再改写；只改秒数会漏掉参考图 $0.01/张（坑 129）。
9. submit／poll 两个入口分离，task_id 暴露给调用方持久化；同一模型 id 官方／中继走不同协议，经 L2 菜单解析，无 model-id 硬编码（14 §1、§4）。

---

## 3 语音识别

### 3.1 三种线格式对照

三种线格式 = 三个适配器，不是一个适配器加一堆 if；百炼 ⓑ／ⓒ 按模型名后缀分发（`model.endsWith('-filetrans')` → ⓒ），不按厂商（16 §1）。选路：要说话人 → 只有 ⓒ；要准确时间码模型未指定 → ⓒ；用户点名同步模型又要时间码 → ⓑ + 静音切片并告知 ⓒ 替代，不擅自换模型；已用 OpenAI 兼容只要粗时间码 → ⓐ。

| 维度 | ⓐ OpenAI 兼容转写 | ⓑ 百炼同步识别 | ⓒ 百炼录音文件转写（filetrans） | 私有 SDK／HTTP（豆包、Gemini、Deepgram、ElevenLabs、CAMB、Gladia、MiMo…） |
| --- | --- | --- | --- | --- |
| 端点 | `POST {base}/audio/transcriptions` | `POST {base}/services/aigc/multimodal-generation/generation` | `GET /uploads?action=getPolicy` → OSS 表单上传 → `POST /services/audio/asr/transcription`（异步）→ `GET /tasks/{id}` → 下载结果 JSON | 各家 SDK 或私有 HTTP；Gladia 是 ⓒ 型三步异步；MiMo 走 ① `chat/completions` 的 `input_audio` 块 |
| 上传方式 | multipart 文件字段 `file`；`Authorization: Bearer`（本地无密钥时不发） | base64 data URI 放进 JSON 请求体 | 上传到百炼临时 OSS 得 `oss://` 地址（48 小时有效），上传**不带 `Authorization`** | 整文件（豆包 base64 放 `audio.data`；Gemini Files API；Deepgram >50 MB 先转 mp3） |
| 单次上限 | OpenAI 25 MB【文档】；各家不同 | 约 10 MB、3–5 分钟（文档两种说法）【文档】 | 以凭证 `max_file_size_mb` 为准；时长 12 小时【文档】 | Gemini ≤300 s 整段；CAMB 轮询上限 600 s；Deepgram 超时 600 s |
| 时间码来源 | `verbose_json` 给 `segments[].start/end`（**秒**，浮点）；`gpt-4o-*-transcribe` 不给 | **无句级时间戳**，时间码只能来自「送去识别的那一片在哪」（静音切片） | 句级 + 词级（**毫秒**整数），相对整个文件；`enable_words:true` 才有词级 | 豆包 `utterances[]` 毫秒；Gemini 词级（带 `s` 后缀字符串）；Deepgram／ElevenLabs／CAMB 秒；Gladia／自定义 API 直接 SRT |
| 说话人分离 | 标准 whisper 无；`gpt-4o-transcribe-diarize` `diarized_json` 有 | 🔇 传了也被忽略【实测 2026-09-13】（文档称支持） | ✅ `qwen-audio-3.0-asr-flash-filetrans` 可用，整文件编号一致【实测 2026-09-13】 | 豆包 `enable_speaker_info`；Deepgram `diarize`；ElevenLabs `speaker_id`；CAMB `speaker`；WhisperX 本地有 |
| 限流 | 429／断网／超时不计失败按 Retry-After | 账号共享约 100 RPM【文档】以控制台为准；Retry-After 只认秒数（1–300 s），缺失时 5/10/20/40/60 s 阶梯 | 轮询 2 → 3 → 5 → 8 → 10 s 封顶 | GLM `error.code` 1302／1303／1214 是限流；Gemini 原实现 429 也不等（坑） |
| 错误分类 | 401/403/404 致命；200 非 JSON 致命；5xx 计一次失败同段 3 次后跳过 | 400 + `ASR_RESPONSE_HAVE_NO_WORDS` = 成功空文本；413 片段太大；其他 400/422 非致命跳过这段；404 `Model not exist` 致命 | 按步骤：取凭证／上传 403 = 凭证过期重取；提交 400 = `oss://` 过期丢 fileUrl；轮询 404 = 丢 taskId 重提交；FAILED 含 download/url/file/format 全丢；下载 403/404 = 签名过期丢 taskId 保留 fileUrl | 豆包成败看头 `X-Api-Status-Code == 20000000` 不看 HTTP 状态 |
| 代表 | OpenAI `whisper-1`、Groq、硅基流动、中转站、本地 OpenAI 兼容服务 | `qwen3-asr-flash`、`qwen-audio-3.0-asr-flash`、`fun-asr-flash-*` | 模型名以 `-filetrans` 结尾 | 见 §3.2 |
| 证据 | 本库 ⓐ **只有实现、没有实测、没有离线测试** | 【实测 2026-09-13】 | 【实测 2026-09-13】（qwen-audio-3.0 族） | 【实现】（pyVideoTrans，本库未独立复核报文；据此判错前先实测） |

### 3.2 模型 × 平台 主表

| 线格式 | 平台 | 模型 | 端点与上传 | 时间码（词级／句级／无） | 说话人分离 | 语种／限流 | 错误分类 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ⓐ | OpenAI 官方 | `whisper-1` | `POST {base}/audio/transcriptions` multipart（Bearer；本地无密钥时不发）；字段 `file`、`model`、`response_format=verbose_json`、`timestamp_granularities[]=segment`（只在 verbose_json 下有效，可加 `word`）、`language`（主标签，自动检测不发）、`prompt`；文件上限 **25 MB** | 句级 `segments[].start/end`（**秒**，×1000 取整）；`text` 前常带空格要 trim；`avg_logprob` 自然对数 exp() 夹 0..1 当置信度；无 `segments` 时退回整段 `text`，时间码 `[0, duration]` | ❌ 无 | — | 401/403 致命；404 致命；200 非 JSON 致命；429／断网／超时不计失败按 Retry-After；5xx 计一次失败同段 3 次后跳过 | 📄【文档】；本库 ⓐ 只有实现、无实测、无离线测试 | 16 §1、§3、§8 | 116 |
| ⓐ | OpenAI 官方 | `gpt-4o-transcribe` ／ `gpt-4o-mini-transcribe` | 同上；原 Python 版整文件转 16 kHz 单声道 mp3、无 25 MB 检查，响应无 `segments` 就改走切片 | `response_format` 只支持 `json`／`text`，**不给 segments**；时间码来自切片 | ❌ 无 | — | — | 【文档 + 实现】 | 16 §3 模型差异表、§10.2 | 116 |
| ⓐ | OpenAI 官方 | `gpt-4o-transcribe-diarize` | 整文件，`chunking_strategy: "auto"`，不带 prompt，`response_format: "diarized_json"` | `segments[].start/end/text/speaker` | ✅ `speaker`（按首次出现顺序重编号） | — | — | 【实现】 | 16 §10.2 | — |
| ⓐ | Groq | `whisper-large-v3`、`whisper-large-v3-turbo` | OpenAI 兼容地址 `https://api.groq.com/openai/v1` | 同 ⓐ | — | — | — | 【实现】 | 16 §3 | — |
| ⓐ | 硅基流动 | `FunAudioLLM/SenseVoiceSmall` | OpenAI 兼容 | ⚠ 时间码形态未写 | — | 语种 zh／yue／en／ja／ko | — | 【实现】 | 16 §3 | — |
| ⓐ | OpenAI 兼容第三方（通用） | 非 `api.openai.com` 地址 | SDK 同上；VAD 切片逐段 | `response_format: "json"` 只取 `text`，时间码来自切片（第三方对 `verbose_json` 支持不齐，干脆不要） | ❌ 无 | — | — | 【实现】 | 16 §10.2 | — |
| ⓐ | 302.AI | whisper ／ `gpt-4o-*` | `POST https://api.302.ai/v1/audio/transcriptions`，Bearer；whisper 整文件，`gpt-4o-*` 切片 | whisper `verbose_json`；gpt-4o 只能 `json` | 说话人编号曾用「当前条数」当新编号（同一人不同编号，已修复为首次出现顺序） | — | 请求**没有超时**；带 `error` 或缺 `text` 的片段记下后跳过，全部失败才报错 | 【实现】 | 16 §10.2、§10.3 | — |
| ⓐ | 智谱 BigModel | `glm-asr-2512` | `POST https://open.bigmodel.cn/api/paas/v4/audio/transcriptions`，Bearer；multipart `file` + `model=glm-asr-2512`、`stream=false`；VAD 切片 | 只有 `text`，时间码来自切片 | ❌ 无 | 错误体 `error.code` 为 `1302`／`1303`／`1214` 是**限流**（HTTP 状态之外第二层判据） | 401/403/404/422 致命；🔇 计数器曾在成功时也递增，重试额度被吃光后片段静默变空文本（已修） | 【实现】 | 16 §10.2、§10.3；01 §9.4 | — |
| ⓐ（chat 面） | 小米 MiMo | `mimo-v2.5-asr` | OpenAI SDK 打 `https://api.xiaomimimo.com/v1` 的 **`chat/completions`**；音频走 ① 族 `input_audio` 内容块；VAD 切片、每片 mp3 | `choices[0].message.content`，时间码来自切片 | ❌ 无 | 语言走 `extra_body.asr_options.language`（只认 zh／en／auto） | — | 【实现】 | 16 §10.2 | — |
| ⓐ（本地） | 本地服务 WhisperX ／ Parakeet ／ STT | — | OpenAI SDK 或自定义 `/api`；整文件 | WhisperX `diarized_json`；Parakeet、STT 直接要 `response_format: "srt"`（丢置信度与词级信息） | WhisperX 有 | — | — | 【实现】 | 16 §10.2 | — |
| 本地 | Faster-Whisper-XXL | — | — | — | — | — | 🔇 逐行正则吞掉行尾 `\n`，相邻字幕行被跳过——静默丢字幕（已修） | 【实现】 | 16 §10.3 | — |
| ⓑ | 阿里百炼 DashScope | `qwen3-asr-flash` | `POST {base}/services/aigc/multimodal-generation/generation`；头 `Authorization: Bearer`、`Content-Type: application/json`、`X-DashScope-SSE: disable`；默认 `https://dashscope.aliyuncs.com/api/v1`（专属域名可覆盖）；body：`input.messages[]` 可选 system `content:[{text:"术语…"}]`（无提示词整条不发）、user `content:[{audio:"data:audio/wav;base64,…"}]`；`parameters.result_format:"message"`、`asr_options:{language:"zh", enable_lid:true, enable_itn:true}`（自动检测不带 `language`；`enable_lid` 与 `language` 同发实测正常）；单次约 10 MB、3–5 分钟（文档两种说法） | **无句级时间戳**，时间码来自静音切片；可能存在的词级 `output.sentence.words[]`——同步接口会不会给**没有实测** | ❌ 不支持，不要下发【文档】 | 账号共享约 100 RPM【文档】；Retry-After 只认秒数（1–300 s），缺失 5/10/20/40/60 s 阶梯 | 400 + `ASR_RESPONSE_HAVE_NO_WORDS` = 没人声 → **成功、空文本**；413 片段太大；其他 400/422（语种、审核）非致命跳过这段；404 `Model not exist`（专属域名对不存在模型也回）致命 | 【实测 2026-09-13】三个模型识别同一段两句合成中文都正确 | 16 §1、§4、§4.2、§8 | 116、118 |
| ⓑ | 百炼 | `qwen-audio-3.0-asr-flash` | 同上端点／头；body：`input.messages[{role:user, content:[{type:"input_audio", input_audio:{data:"data:audio/wav;base64,…"}}]}]`；`parameters:{format:"wav", sample_rate:"16000"}` | 无句级；响应文本在 `output.text` 或 `output.choices[0].message.content`（字符串或 `[{text}]` 数组）两处之一 | 🔇 带 `diarization_enabled: true` **静默忽略**：200、有文本、没有 `speaker_id`【实测 2026-09-13】；**文档：支持；实测：忽略**；片段放长（2 分钟）也换不来编号 | 同上 | 同上；400/422 且体含 `DataInspectionFailed` = 这一片被审核拒 → 跳过这一片；空间专属地址 `https://{spaceid}.cn-beijing.maas.aliyuncs.com/api/v1` | 【实测 2026-09-13】 | 16 §4、§7、§10.2 | 115、118 |
| ⓑ | 百炼 | `fun-asr-flash-*` | 同 `qwen-audio-3.0-asr-flash`（`input_audio` 内容块） | 同上 | 🔇 `diarization_enabled` 静默忽略【实测 2026-09-13】；文档称支持 | 同上 | 同上 | 【实测 2026-09-13】 | 16 §4、§7 | 115 |
| ⓑ（SDK） | 百炼 | `qwen3-asr-flash`（原 Python 版） | DashScope SDK `MultiModalConversation.call`，`content: [{audio: <本地路径>}]`（SDK 替你上传本地文件，与 base64 形态等价）；VAD 切片 | `output.choices[0].message.content[].text` 拼接 | — | — | 原实现关了 TLS 校验、没有超时，任意 400/422 终止整个任务（已修） | 【实现】 | 16 §10.2、§10.3 | 118 |
| ⓒ | 百炼 | `qwen-audio-3.0-asr-flash-filetrans` | 五步：① `GET {base}/uploads?action=getPolicy&model=<model>` → `data.{upload_host, upload_dir, oss_access_key_id, policy, signature, x_oss_object_acl, x_oss_forbid_overwrite, max_file_size_mb}`（`model` 必须与提交一致；无 `data` = 该地址不支持临时上传；上传前按 `max_file_size_mb` 和时长拦截）；② 表单上传到 `upload_host`，**不带 `Authorization`**，字段顺序 `OSSAccessKeyId`、`policy`、`Signature`、`key`（`<upload_dir>/<时间戳>_<只保留 [A-Za-z0-9._-] 的文件名>`）、`x-oss-object-acl`、`x-oss-forbid-overwrite`、`success_action_status=200`，**`file` 必须最后**；200/204 成功，地址 `oss://<key>`（48h）；③ `POST {base}/services/audio/asr/transcription`，头 `X-DashScope-Async: enable` **和 `X-DashScope-OssResourceResolve: enable`**（少了后者不认 `oss://`）；body `{model, input:{file_urls:["oss://…"]}, parameters:{channel_id:[0], enable_words:true, diarization_enabled:true, language_hints:["en"]}}`；`output.task_id`；**提交不幂等**；④ `GET {base}/tasks/{id}`；⑤ GET 签名地址下载 JSON，**不带鉴权头**；时长上限 12 小时【文档】 | 句级 + 词级（**毫秒**，相对整个文件）：`transcripts[0].sentences[]` `{begin_time, end_time, text, speaker_id, words:[{begin_time, end_time, text, punctuation, speaker_id}]}`；`enable_words:true` 才有词级；末尾偶尔多一句只有标点的空句（至少含一个字母或数字才收） | ✅ 一男一女英文对话标成 0／1，整文件编号一致【实测 2026-09-13】；`speaker_id` 可能是数字或数字字符串，从 0 开始；词上缺失沿用句子的 | `language_hints:["en"]`；轮询 2 → 3 → 5 → 8 → 10 s 封顶 | `task_status ∈ PENDING/RUNNING/SUCCEEDED/FAILED/CANCELED/UNKNOWN`（与万相视频共用）；结果 `output.results[].transcription_url`（`subtask_status` 缺失按成功），兼容 `output.transcription_url`；取凭证／上传 403 = 凭证过期重取；提交 400 多半 `oss://` 过期丢 fileUrl 重传；轮询 404 = 只丢 taskId 重提交；FAILED 原因含 download/url/file/format → taskId、fileUrl 都丢；其他 FAILED 只丢 taskId、最多自动重来 1–2 轮；下载 403/404 = 签名过期丢 taskId 保留 fileUrl | 【实测 2026-09-13】官方地址跑通全部五步；❌ Dart `http` 包 `MultipartRequest` 传 OSS 被拒 `MalformedPOSTRequest`，手拼 multipart 立即成功【实测】（三处差异：boundary 含 `+` `.`、part 头全小写、文件段先 content-type 后 content-disposition；哪一处触发**没有定位**；旧：「boundary 含 `()+,?:=`」不准确，保留以解释旧代码） | 16 §1、§5、§7、§8、§9 | 119、120、121 |
| ⓒ | 百炼 | `qwen3-asr-flash-filetrans` | 同上五步，但 qwen3 族参数：`input.file_url: "oss://…"`（**单数、字符串**）、`parameters.language: "en"`；同样 `enable_words: true` | 同上 | ❌ 不支持【文档】 | — | 同上 | 📄 **只按文档实现、未实测** | 16 §5、§7 | — |
| ⓒ | 百炼 | `fun-asr`、`fun-asr-mtl`、`paraformer-v2` 等 | 同上 | 同上 | 📄 文档称支持，建议单声道、≤2 小时 | — | — | 📄【文档，未测】 | 16 §7 | — |
| 私有 HTTP | 火山引擎 豆包（大模型录音识别极速版） | `volc.bigasr.auc_turbo` | `POST https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash`；头 `X-Api-App-Key`、`X-Api-Access-Key`、`X-Api-Resource-Id: volc.bigasr.auc_turbo`、`X-Api-Request-Id: <uuid>`、`X-Api-Sequence: -1`；整文件 mp3 → base64 放 `audio.data` | `result.utterances[].start_time/end_time`（**毫秒**）、`text` | `additions.speaker`；请求开 `enable_speaker_info` | — | 🔇 **成败看响应头 `X-Api-Status-Code == 20000000`**，不看 HTTP 状态（缺头按失败）；`20000003` 静音、`45000001` 参数错、`45000002` 空音频、`45000151` 格式错、`55000031` 服务忙 | 【实现】 | 16 §10.2；06 §2 | 122 |
| 私有 SDK | Google Gemini | `gemini-3.5-transcribe` | `google-genai` SDK：Files API 上传后 `interactions.create`，`generation_config.transcription_config = {mode:{type:"verbatim", timestamp_granularities:["word"]}, language_codes:[…]}`；≤300 s 整段，更长用 silero 切 60–300 s、静音 2 s、不补静音 | 词级：`steps[].content[].annotations[]` 里 `type == "word_info"`；词时间是**带 `s` 后缀的字符串**（`"1.23s"`） | — | 多把 key 逗号分隔轮换 | 把 400/403/404/429/500 都当「不重试」，429 也不等；🔇 汇总段曾用相对时间和空 `text` 输出一条空字幕（已修）；502/503 曾被吞成 None（已修） | 【实现】 | 16 §10.2、§10.3 | — |
| 私有 SDK | Deepgram | — | SDK `listen.rest.v("1").transcribe_file`，超时 600 s；>50 MB 先转 mp3 | 分离时 `results.utterances[].start/end`（秒）、`transcript` | `speaker`；选项 `diarize`、`utt_split=<静音秒数>`、`smart_format`／`punctuate`／`paragraphs`／`utterances` | 中文结果要去空格、繁转简 | 缺密钥提示文案曾硬编码「Deepgram」 | 【实现】 | 16 §10.2、§10.3 | — |
| 私有 SDK | ElevenLabs | `scribe_v2`（指定语言）／`scribe_v1`（自动） | SDK `speech_to_text.convert`，`diarize: true`，整文件 | 词级 `words[]`：`type／text／start／end`（秒）；跳过 `type == "audio_event"` | `speaker_id`（`speaker_N`）；换人必断句，标点 +（停顿 ≥200 ms 或行长 ≥500 ms）断句 | — | — | 【实现】 | 16 §10.2 | — |
| 私有 SDK | CAMB AI | — | SDK 提交得 `task_id`，每 3 s 轮询，上限 600 s；整文件 | `transcript[]`：`start／end`（秒）、`text` | `speaker` | 🔇 语言是**整数 ID**，查不到默认 1（英语）——静默按英语识别 | — | 【实现】 | 16 §10.2 | — |
| ⓒ 型三步异步 | Gladia | — | `POST /v2/upload`（头 `x-gladia-key`）→ `POST /v2/pre-recorded` → 每 1 s 轮询 `GET /v2/pre-recorded/{id}` | `result.transcription.subtitles[0].subtitles`（直接要 SRT） | — | — | — | 【实现】 | 16 §10.2 | — |
| 自定义 API | 用户自建 | — | `POST {url}?sk={key}`——**密钥在查询串里**；multipart 字段名 `audio` | `{"code": 0, "data": "<SRT 字符串>"}` | — | — | 修复前把 URL 整体 `.lower()`，大小写敏感路径全坏；曾对服务端输出 `eval()` | 【实现】 | 16 §10.2 | — |

### 3.3 横切数值附表

照搬 16 §2、§4.1、§6、§9、§10.1。

| 项 | 值 | 出处 |
| --- | --- | --- |
| 统一形状 | `识别(音频路径, 语言, 取消令牌, 进度回调, 检查点?) -> [字幕条{startMs,endMs,text,speaker?,confidence?}]`；参数入队即定死；字幕存不带硬换行的干净文本；结果统一后过与服务无关的时间轴规整 | 16 §2、§6.2 |
| 输入音频统一 | 16 kHz、单声道、pcm_s16le wav：`ffmpeg -i in -vn -ac 1 -ar 16000 -c:a pcm_s16le out.wav`；约 1.9 MB/分钟，1 小时约 115 MB | 16 §2 |
| 语言代码 | 只取主标签 `zh-CN` → `zh`；自动检测**整个字段不发**，不发 `"auto"` | 16 §2 |
| 静音切片 | `ffmpeg -i audio.wav -af silencedetect=noise=-35dB:d=0.6 -f null -`，结果在 **stderr**（`silence_start`／`silence_end`／`silence_duration`；文件末尾可能只有 start）；补集为语音；<1 s 并入前一段（第一段并入后一段）；>25 s 按 `ceil(len/25s)` 等分 | 16 §4.1 |
| 切单片 | `ffmpeg -y -ss <start> -t <dur> -i audio.wav -af adelay=200:all=1,apad=pad_dur=0.200 -ac 1 -ar 16000 -c:a pcm_s16le clip.wav`；**前后补 200 ms 静音，不是邻段真实音频**（早期多截邻段 200 ms 导致半个词识别两次，2026-09-13 修复）；`fileStartMs = start − 200`；用 `-ss`+`-t` 不用 `-to` | 16 §4.1；坑 117 |
| 原 Python VAD | 默认 ten-vad、可选 silero；最短语音 1 s、单片硬上限 25 s、最短静音 600 ms、阈值 0.45；补静音注释写 200 ms **代码实际 400 ms** | 16 §10.1 |
| 词级 → 字幕块 | 词时间 = `offset + begin_time`（ⓑ offset = fileStartMs；ⓒ offset = 0）；词正文 = `text + punctuation`；断开条件：换说话人／上词标点句末 `[。！？.!?;；]`／块已超 10 s／超长度上限（含中日韩 40 字，否则 90 字符）；空格只在拉丁/数字相接时加；`end <= start` 时 `end = start + 1` | 16 §6.1 |
| 规整 | 先修重叠；<500 ms 且与上一条间隔 <200 ms 且同说话人并入；>10 s 按字数比例拆；单行上限（中日韩 15、其他 40）只在导出时用；无词级渠道一条最长 25 s、时间码误差约 1 s；空占位条不送翻译 | 16 §6.2 |
| 原 Python 重断句 `_resegment` | 单位秒；`[min, max + 1.5 s]` 内整段保留；切点：句末标点、停顿 ≥400 ms、逗号且 ≥200 ms、过半后 ≥100 ms，`max + 1.5 s` 强切；不加空格语言 zh/ja/th/yue/ko/km | 16 §10.1 |
| LLM 重断句 | 每 20 条 SRT 一批；输出包 `<SRT>…</SRT>`；剥 `<think>`；`finish_reason == "length"` 报错；条数 ≤ 原来一半整批丢弃（少三成也接受） | 16 §10.1 |
| 说话人编号 | 从 0 只是「第几个声音」，名字映射归上层；界面按首次出现顺序重编号；开了分离结果无编号不报错只提示 | 16 §7 |
| 检查点 | ⓑ 按片段 `(startMs, endMs)`，`{text?, pieces?, failures, skipped, lastError}`；续跑判据「记录过的每段都能在新切分里找到相同起止」，**不要求段数相等**（按段数比误判整份重跑，2026-09 修复）；ⓒ 存 `fileUrl` 与 `taskId` 三步续跑、音频懒抽取；等待 250 ms 小步睡眠检查取消 | 16 §9；坑 121 |
| 错误分类原则 | 按「哪一步」而不是按状态码：403 在识别步是鉴权致命，在 ⓒ 取凭证／上传／下载是过期回退一步；404 在轮询是任务不在 | 16 §8；坑 119 |
| 错误详情 | 只截响应体前 600 字符；密钥不进日志；响应体按 UTF-8 字节解码 | 16 §8 |
| 测分离 | 不能用两个合成中文女声（Tingting／Meijia）；要一男一女英文（macOS `say -v Samantha`／`-v Daniel`）；未安装嗓音 `say` 退出码 0 但生成**空文件** | 16 §7 |
| 原 Python 通用教训 | 重试次数／间隔每次重试时读设置；不就地修改共享常量；计数器不在成功时递增；未列举 API 错误重新抛出而非返回 None；提示文案里渠道名不硬编码 | 16 §10.3 |

---

## 4 尚未覆盖

来源明示信息不足或未实测的项（据此判错前先实测）：

**出图**

1. `z-image-turbo`（13 §4）：只在同步端点模型列表里出现，尺寸规则、参考图、计费、错误报法一概未写。
2. `qwen-image`／`-plus`／`-max` 初代五个固定尺寸：原文自带 ⚠，仅【文档 2026-09】，未实测。
3. `wan2.7-image-pro` 改图是否接受 `4K`：4K 文档只在文生图语境下出现。
4. wan `negative_prompt` 不支持时的报法（400 点名 ／ 静默忽略）：原文只说「不支持」。
5. Seedream 5.0 flash 是否支持流式：能力表未列；仅知 pro 不支持、lite／4.5／4.0 支持；flash 在套餐 key 上 404，按量未测。
6. Seedream 中转是否透传 SSE：原文明示「未知」。
7. Seedream 失败／被审核拦下的请求上游是否仍收输入费：【未验】——只能对账单。
8. Midjourney `base64Array` 垫图张数上限、计费单价：未写。
9. DashScope 出图的 `Throttling` 限流数值、RPM 上限：未写（ASR 侧写了约 100 RPM 且以控制台为准）。
10. `gpt-image-1` 的尺寸／质量档具体枚举与单价：原文只提 `size`／`quality` 回显与输入图 $8/M vs 文本 $5/M。
11. Seedream 4.5／4.0／5.0 flash 在按量 base 上的行为：只有文档能力表与套餐 404，按量 key 未实测（01 §9.3：手头只有套餐 key）。
12. images-api（OpenAI 官方）、gemini、imagen、chat-image、midjourney、minimax 各 route：证据等级为【实现／文档】，本库无独立实测数值（例外：Content-Type 与 part 数组两条 400【实测 2026-09-05】）。

**视频**

13. xAI 视频 720p／1080p 是否加价：【未验】。
14. OpenAI Sora、Google Veo：14 §2 只有端点、状态词、结果位置一行，无 body 字段、参考图、时长／分辨率、计费、保留期、取消，且未标注实测。
15. 火山方舟 Seedance 协议形状：本库未覆盖，仅有套餐 key 404 记录（按量 key 未测）。
16. 千问 wan3.0 视频失败态与取消分支：实测未走到；千问无取消端点（表中 `—`）。
17. MiniMax v2 未实测项：纯文生视频 `ratio` 替换、帧与参考素材互斥、`reference_image` role、取消 DELETE、`768P`。
18. 中继 openai-videos（`/v1/videos`）协议的 body／状态词：仅【实现】口径。

**语音识别**

19. ⓐ OpenAI 兼容 ASR：本库只有实现，没有实测、没有离线测试；硅基流动 SenseVoiceSmall 时间码形态未写。
20. ⓑ 同步接口是否给 `output.sentence.words[]` 词级信息：未实测，代码只允许它不存在。
21. ⓑ 单次上限：文档「约 10 MB、3–5 分钟」两种说法并存，未实测边界。
22. `qwen3-asr-flash-filetrans`：只按文档实现未实测。
23. ⓒ `fun-asr`、`fun-asr-mtl`、`paraformer-v2` 说话人分离：【文档，未测】。
24. Dart `http` `MultipartRequest` 被 OSS 拒的具体触发点：三处差异中哪一处未定位。
25. 16 §10.2 所有渠道（豆包、MiMo、Gemini transcribe、Deepgram、ElevenLabs、CAMB、Gladia、302.AI、GLM-ASR）：证据等级仅【实现】，本库未独立复核报文。
26. 流式／实时 ASR（WebSocket）：15 篇明示本库未覆盖。

---

## 附录 本表引用的坑

只列与出图／视频／ASR／媒体计费相关的坑（11 篇表 A 类别为 出图／视频／ASR／计费 且对象是媒体面）；chat 面的计费坑（3、4、18、62、77、108、145–197 等）不在本表。

| 坑号 | 一句话现象 | 平台 | 面 | 本表位置 |
| --- | --- | --- | --- | --- |
| 2 | Gemini 中继发 snake_case 图片字段，图片静默不可见 | 中继／New API ③ 兼容层 | 🖼 chat-image | §1.2 |
| 6 | HTTP 200 + 体内错误（MiniMax `base_resp.status_code`），过期密钥读成空回复 | MiniMax | 🖼 | §1.2 minimax |
| 56 | 短时效签名 URL 直接入库，几小时后图全部 404（DashScope 24h；多数中继更短） | DashScope／中继 | 🖼 | §1.4 第 5 条 |
| 57 | 「Unsupported parameter」prose 命中降级正则，二次计费重生成 | 通用 | 🖼 | §1.4 第 4 条 |
| 58 | DashScope 错误在顶层 `{code,message}`，`DataInspectionFailed` 掉进 prose 正则 | DashScope | 🖼 | §1.2 dashscope |
| 59 | DashScope 尺寸写 `宽*高`，`split("x")` 静默失败永远落回 sizes[0] | DashScope | 🖼 | §1.2 dashscope |
| 60 | 异步出图任务挂死无从排查；「停止」要等下次轮询 | 通用 | 🖼 异步／🎬 | §1.3、§2 |
| 78 | 代码解释器画的图链接约 12 小时过期 | DashScope | ①②（出图产物） | 13 §6 |
| 79 | Seedream 出图右下角带「AI 生成」水印（`watermark` 默认 true） | 火山方舟 | 🖼 ark | §1.2 |
| 80 | 套餐渠道保存后地址被「恢复」成按量 base，之后每次 401 | 火山方舟 | 🖼／全部 | §1.3 ark |
| 81 | 套餐 key 下模型「不存在」（404 UnsupportedModel），`GET /models` 也 404 | 火山方舟套餐 | 🖼 | §1.2、§1.3 |
| 82 | 组图／图层请求画到一半被客户端判超时，钱照扣图没收到 | 火山方舟 | 🖼 | §1.3 ark |
| 83 | 按 token 计价给 Seedream 算出离谱费用（`output_tokens`=像素/256） | 火山方舟 | 🖼 计费 | §1.4 第 7 条 |
| 84 | 组图里一张被审核拦下，整次判失败，其余已计费的图全丢 | 火山方舟 | 🖼 | §1.2 ark |
| 85 | 流式出图第一张没画完就判「连接空闲超时」（SSE 头等 ≈27 s） | 火山方舟 | 🖼 流式 | §1.2 ark 流式 |
| 86 | `stream:true` 回 400，解析器等 SSE 报莫名解析错 | 通用 | 🖼 流式 | §1.2 ark 流式 |
| 87 | 组图流里 `partial_failed` 事件带 `error` 被当请求级错误 | 火山方舟 | 🖼 流式 | §1.2 ark 流式 |
| 88 | 拆图层的名字／框错位一格（跳过下载失败项） | Seedream 图层 | 🖼 | §1.4 第 11 条 |
| 90 | MiniMax 出图「成功」但零张；`success_count` 是字符串 `"0"` | MiniMax | 🖼 | §1.2 minimax |
| 91 | MiniMax「改图」返回不相干的新图（`subject_reference` 是主体参考） | MiniMax | 🖼 | §1.2 minimax |
| 92 | 中继经 chat 出图，一张图存成三个文件或一张没存（裸 base64／裸链接） | 中继 | 🖼 chat-image | §1.2、§1.4 第 6 条 |
| 93 | OpenAI 兼容改图接口对单张 400 多张正常（或反之）：`image` vs `image[]` | 中继／dall-e-2 | 🖼 images-api | §1.2 |
| 101 | wan2.7 出图每次 400 `Field required: input.messages`（二手文档镜像错误信封） | DashScope | 🖼 | §1.2 wan2.7-image-pro |
| 102 | 千问／万相出图贵一倍、图 2048²（省略 `size` 落 2K 档） | DashScope | 🖼 计费 | §1.2、§1.3 |
| 103 | 换模型／重试出图 400 尺寸格式或范围不对（任务参数比模型活得久） | DashScope | 🖼 | §1.4 第 9 条 |
| 104 | 选官方推荐 16:9 显示成「自定义比例」（2688×1536 = 1.75:1） | DashScope | 🖼 UI | §1.3 dashscope |
| 110 | 出图模型经中转 chat 路由一律 400 `images[0] must be an http/https URL` | 中转 | 🖼 chat-image | §1.2 |
| 113 | MiniMax 视频「成功」出片计费，完全没用首尾帧（平铺 `url`） | MiniMax | 🎬 | §2 |
| 115 | 开了说话人分离，字幕一个编号都没有（同步接口静默忽略 `diarization_enabled`） | 百炼 | 🎤 ⓑ | §3.2 |
| 116 | 整段只出一条字幕（同步接口无句级时间戳；`gpt-4o-*-transcribe` 无 `segments`） | 百炼；OpenAI | 🎤 | §3.2 |
| 117 | 相邻字幕重复半个词（切片多截邻段 200 ms） | 通用 | 🎤 | §3.3 切单片 |
| 118 | 一段背景音乐让整个识别失败（400 `ASR_RESPONSE_HAVE_NO_WORDS`；审核 400/422 `DataInspectionFailed`） | 百炼 | 🎤 ⓑ | §3.2 |
| 119 | filetrans 续跑反复报鉴权失败／找不到（403/404 当全局致命） | 百炼 | 🎤 ⓒ | §3.1、§3.2 |
| 120 | Dart 上传百炼 OSS 回 `MalformedPOSTRequest` | 百炼 OSS | 🎤 ⓒ | §3.2 |
| 121 | 识别中途限流停下，续跑从头开始重新计费（检查点要求段数相等） | 通用 | 🎤 计费 | §3.3 检查点 |
| 122 | 火山豆包识别「成功」却一个字没有（成败在 `X-Api-Status-Code` 头，HTTP 恒 200） | 火山豆包 ASR | 🎤 | §3.2 |
| 123 | 不发 `quality` 的 xAI 出图按 Medium 计，本地按 Low 估，账单高三分之一 | xAI | 🖼 计费 | §1.2、§1.3 xai |
| 124 | `quality: auto` 让模型定档，账单不可预算 | xAI | 🖼 计费 | §1.3 xai |
| 125 | 初代 `grok-imagine-image` 默默收 `quality`，`1.5k` 却 400 | xAI | 🖼 | §1.2 |
| 126 | 上游同名字段改写记账键（`input_image_count`／`reported_cost_usd` 原样铺进 metadata）；Veo 轮询把 operation body 整个当内部信封 | 通用（中转、Veo） | 🖼🎬 计费 | §1.4 第 7 条、§2 |
| 127 | 上游报价只在收尾块，流被放弃就退回表算 | xAI／ark 流式 | 🖼 流式计费 | §1.2 ark 流式 |
| 128 | xAI 参考图上限文档 3 张，实测 5 张 200 并计费 | xAI | 🖼 计费／文档不一致 | §1.2 |
| 129 | 视频按秒标价，参考图另收 +$0.01/张，报价只在终态回包 | xAI | 🎬 计费 | §2 |
| 130 | 透明底立绘「加背景」照常 200，背景画进了人物里（`background:"transparent"` 只保证结果背景透明；客户端不应按输入透明 PNG 自动开） | 火山方舟 | 🖼 语义 | §1.2 透明背景行 |
| 131 | 改图带满参考图，审批后才 400「cannot exceed 10」（源图没算进上限） | 火山方舟 | 🖼 | §1.2 ark 通用行 |
| 132 | 透明编辑对「带透明通道」PNG 报 400「at least one transparent pixel」 | 火山方舟 | 🖼 | §1.2 透明背景行 |
