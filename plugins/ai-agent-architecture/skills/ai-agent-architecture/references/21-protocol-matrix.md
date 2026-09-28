# 21 · 协议表（协议族 × 功能维度）

本表回答：在某个协议族上，某个功能（system、多模态输入、流、思考、结构化、工具、服务端工具、usage、错误）的**字段长什么样、取回在哪、回传义务是什么、各族之间哪里不同**。主键 = 协议族 × 功能维度；平台 / 渠道 / 模型级的差异只在「详见」指过去，不在本表展开（那是 22、23 篇的事）。只写来源（02–06、13、14、16 篇）里有的事实。

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

维护：新增 / 修正按 `30-knowledge-ingestion.md` 的流程；本表每行必须带证据与指针，没有证据的格子写 `—`。证据记法：【实测 YYYY-MM-DD】【文档 YYYY-MM】【中继源码】【实现】（参考实现代码里已在真实端点上跑的形状）。面的编号：① OpenAI Chat Completions ／ ② OpenAI Responses ／ ③ Gemini generateContent ／ ④ Anthropic Messages ／ Ⓓ DashScope 私有 ／ 🖼 出图 ／ 🎬 视频 ／ 🎤 ASR。

目录：
- [§1 协议族清单](#1-协议族清单)
- [§2 对话四族功能对照表](#2-对话四族功能对照表)
- [§3 各功能维度展开](#3-各功能维度展开)
  - [3.1 端点、鉴权、baseURL、CORS](#31-端点鉴权baseurlcors) · [3.2 system 与消息结构](#32-system-与消息结构) · [3.3 多模态输入](#33-多模态输入) · [3.4 流式事件骨架、终止与 usage 位置](#34-流式事件骨架终止与-usage-位置)
  - [3.5 思考强度](#35-思考强度) · [3.6 思考取回](#36-思考取回) · [3.7 思考回传](#37-思考回传)
  - [3.8 JSON mode 与 schema](#38-json-mode-与-schema) · [3.9 工具定义与 tool_choice](#39-工具定义与-tool_choice) · [3.10 流式工具参数拼接与配对](#310-流式工具参数拼接与配对)
  - [3.11 服务端工具 wire 形状](#311-服务端工具-wire-形状) · [3.12 服务端工具续跑](#312-服务端工具续跑) · [3.13 工具按需加载](#313-工具按需加载)
  - [3.14 usage 与缓存](#314-usage-与缓存) · [3.15 错误信封与 200 里的失败](#315-错误信封与-200-里的失败) · [3.16 未知字段、max tokens、温度](#316-未知字段max-tokens温度)
- [§4 非对话协议的骨架](#4-非对话协议的骨架)
  - [4.1 出图 route](#41-出图-route请求响应统一化要点) · [4.2 视频 submit/poll](#42-视频-submitpoll-不变量) · [4.3 ASR 三种线格式](#43-asr-三种线格式)

---

## 1. 协议族清单

「判定标准」= 从一条 base + 一份报文怎么认出它属于哪一族；「谁在用」只列来源里出现过的平台。

| 族 | 判定标准 | 端点路径 | 鉴权头 | 谁在用 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ① OpenAI Chat Completions | 容器 `messages[]`，system 是 `role:"system"` 消息，工具调用在 `assistant.tool_calls[]` 且 `arguments` 是 JSON 字符串，流末 `data: [DONE]` | `POST {base}/chat/completions`；base 自带版本段（`…/v1`），**不补 `/v1`** | `Authorization: Bearer <key>`；无 key 时**整个头省略** | OpenAI 官方、DeepSeek、千问 compatible-mode、火山方舟（含 Coding Plan `…/api/plan/v3`）、智谱、MiniMax、Kimi、xAI、OpenRouter、New API、OrcaRouter、Ollama／LM Studio | 【实现】【实测 2026-09-23／24／28】 | 02 §1、§4、§5 | — |
| ② OpenAI Responses | 顶层 `instructions` + `input[]` 条目（`input_text`／`function_call`／`function_call_output`），流是类型化事件 `response.*`，终止 `response.completed` | `POST {base}/responses`（base 与 ① 同） | Bearer（与 ① 同） | OpenAI 官方、xAI、千问 Responses 面、火山方舟 ② 面、New API、OrcaRouter | 【实现】【实测 2026-09-15／24／26】 | 02 §7 | — |
| ③ Google GenAI generateContent | **模型名在 URL**，容器 `contents[]`，模型侧角色 `model`，system 在顶层 `systemInstruction`，请求键 camelCase，每个 SSE chunk 是完整响应对象 | `POST {base}/models/{id}:streamGenerateContent?alt=sse`；base 自带 `…/v1beta`，额外剥尾部 `/models` | `x-goog-api-key`（默认）；compat 可选 `bearer`／`both`；`?key=` 查询串**故意不实现**（进代理日志 = 泄漏） | Google AI Studio、Vertex（经 OrcaRouter）、New API Gemini 面 | 【实现】【实测 2026-09-05／26】 | 02 §1、§2.2、§5 | 111 |
| ④ Anthropic Messages | 顶层 `system` 字符串，`messages[]` 严格 user／assistant 交替，工具调用是 `tool_use` block，流是 `message_start → content_block_* → message_delta → message_stop`，`max_tokens` 必填 | `POST {root}/v1/messages`；base 是**根地址**，客户端补 `/v1/messages`（`anthropicRoot` 先剥 `/messages` 再剥 `/v1`） | `x-api-key` + `anthropic-version: 2023-06-01`（pinned）+ `anthropic-dangerous-direct-browser-access: true`；compat 可选 `bearer`／`both`（`ANTHROPIC_AUTH_TOKEN→Bearer` 是一等约定） | Anthropic 官方（经 OrcaRouter）、New API 四渠道（Kiro／CC／anti／AWSb）、火山方舟 ④ 面、智谱 `/api/anthropic`、MiniMax `/anthropic/v1/messages` | 【实现】【实测 2026-09-23／26】 | 02 §1、§4、§5、§6 | — |
| Ⓓ DashScope 私有扩展（挂在 ① compatible-mode 上） | ① 形状 + 顶层私有键：`enable_thinking`、`thinking_budget`、`enable_search`、`search_options`、`enable_code_interpreter`、`vl_high_resolution_images`、`video_url` 片段（发起者） | 千问 compatible-mode（① 面）；另有千问 Responses 面（②） | Bearer（与 ① 同） | 千问百炼；`enable_search` 等只放行 compat（api.openai.com 对未知顶层键 400） | 【文档】【实测 2026-09-17／28】 | 02 §1；03 §3；05 §5 | 10、74、77、78 |
| 附：火山方舟豆包私有扩展（① ② ④ 三面并存） | ① 面顶层 `thinking:{type}`、`reasoning_effort` 七档、`delta.encrypted_content`；④ 面 `thinking:{type:"disabled"}` 真关 | Coding Plan 套餐 base `…/api/plan/v3/chat/completions`（① 面）；② 面；④ 面 | Bearer（套餐 key） | 火山方舟 | 【实测 2026-09-18／23／28】 | 03 §3.2、§3.4 | 114、137 |
| 附：智谱私有 REST（应用执行的联网端点，非对话协议） | 同一把 key、同一前缀下的独立端点，body 不含 messages | `POST /web_search` body `{search_query, search_engine, search_intent}`；`POST /reader` body `{url, return_format?, …}` | Bearer | 智谱 BigModel | 【实测 2026-09-19】 | 05 §5「服务端工具归平台」 | — |
| 附：Bedrock 上的 Claude（经 New API AWSb 正向渠道，④ 形状；**不是** Bedrock Converse——Converse 是 camelCase + SigV4 的第五种 body，本库未接，见 01 §2） | 经 New API `/v1/messages` 暴露，④ 形状；区别只在校验会响：乱写 effort／思考时 `temperature:0.3`／篡改 `signature` 都 400 与官方同文 | New API `/v1/messages` → Bedrock 正向 | 由 New API 代管 | New API · AWSb 渠道 | 【实测 2026-09-23】 | 03 §3.3；02 §1 | — |
| 🖼 images-api | `POST /images/generations` JSON；编辑 `POST /images/edits` **multipart**，文件字段 1 张 `image`、多张 `image[]` | `{base}/images/generations`、`/images/edits` | Bearer | OpenAI（dall-e-2／3、gpt-image-1）；New API 式中继的 `/images/generations` **只认 Imagen** | 【实现】【实测 2026-09-05】 | 13 §2、§4.2、§6 | — |
| 🖼 chat 出图（chat-image） | 走 `POST /chat/completions`，模型被作者声明为出图模型（`isImageGenerator:true`）；纯文本消息也要发成单元素 part 数组 | `{base}/chat/completions` | Bearer | 中继（New API 等）上的 `nano-banana-pro`、中转 `gpt-image-1`、Gemini 出图、Flux | 【实测 2026-09-05】【实现】 | 13 §2、§6 | 110 |
| 🖼 gemini | `:generateContent` + `responseModalities:["TEXT","IMAGE"]` | `POST /models/{id}:generateContent` | `x-goog-api-key` | Google Gemini 出图模型 | 【实现】 | 13 §2、§7 | — |
| 🖼 imagen | `:predict`（**不是** `:generateContent`）；无编辑、无 usage | `POST /models/{id}:predict` | `x-goog-api-key` | Google Imagen | 【实现】 | 13 §2、§4.2、§7 | — |
| 🖼 dashscope 同步 | 原生 `/api/v1`（不走 compatible-mode）；body 两段式：顶层只有 `model` 与 `input`，旋钮全在 `parameters`；尺寸拼写 `宽*高` | `POST {原生base}/services/aigc/multimodal-generation/generation`（原生 base = 供应商行剥 `/compatible-mode/v1` 拼 `/api/v1`） | Bearer | 百炼 qwen-image／wan／z-image 家族 | 【实测 2026-09-19】【外部实测 2026-09-04】【文档 2026-08／09】 | 13 §3、§4 | 101、102 |
| 🖼 dashscope 异步 | 提交路径与同步不同、body 一致，头 `X-DashScope-Async: enable`；轮询 `GET /tasks/{id}` | `POST /services/aigc/image-generation/generation` → `GET /tasks/{id}` | Bearer | 百炼 wan2.7-image／-pro（both） | 【文档 2026-08】 | 13 §3、§4 异步任务流 | — |
| 🖼 ark（火山方舟 Seedream） | 与 OpenAI 同路径但 body 是超集且缺字段：无 `n`／`quality`，参考图走 JSON `image`，`watermark` 默认 true，档位 `1K`…`4K` 或 `WxH` 不可混用 | `POST {base}/images/generations`（按量／套餐两个 base） | Bearer | 火山方舟 Seedream 4.0／4.5／5.0 lite／pro／flash | 【文档 2026-09-18／22】【实测 2026-09-18／23】 | 13 §4.1 | 83、127、130 |
| 🖼 xai-images | `/images/generations`；编辑 `/images/edits` 是 **JSON**（不是 multipart）；清晰度 `resolution: 1k／1.5k／2k`（不是 `size`）；`usage` 只有 `cost_in_usd_ticks` | `/images/generations`、`/images/edits`；`GET /v1/image-generation-models/{id}` 回价目 | Bearer | xAI grok-imagine-image（2.0／初代／quality） | 【文档 2026-09】【实测 2026-09-21／22】 | 13 §4.2、§7 | 123、124、125 |
| 🖼 minimax | `POST /v1/image_generation`（挂在 `/v1` 下但**不是** Images API）；`data.image_urls[]` + `base_resp` | `/v1/image_generation` | Bearer | MiniMax image-01／image-01-live | 【实现／文档】 | 13 §2、§4.2、§7 | — |
| 🖼 midjourney | midjourney-proxy 的 `/mj/*`，异步 submit → fetch，参数改写成 `--ar/--v/--s/--c/--q` 拼进 prompt | `POST /mj/submit/imagine` → `GET /mj/task/{id}/fetch` | 代理自定 | midjourney-proxy／New API `/mj/*` | 【实现】 | 13 §2、§4.2 | — |
| 🎬 视频 · 千问 wan3.0 | submit/poll；提交带 `X-DashScope-Async: enable`；轮询端点与图片任务、ASR filetrans 共用 | `POST /api/v1/services/aigc/video-generation/video-synthesis` → `GET /api/v1/tasks/{id}` | Bearer | 百炼 | 【实测 2026-08-29】【文档 2026-08】 | 14 §2、§3 | — |
| 🎬 视频 · MiniMax v2 | submit/poll；`resolution` 与 `duration` **必填无默认**；创建响应只有 `{"task_id"}` | `POST /v2/video_generation` → `GET /v2/query/video_generation/{id}`（`api.minimaxi.com`） | Bearer | MiniMax-H3 | 【实测 2026-08-29】 | 14 §2、§3 | 113 |
| 🎬 视频 · xAI | submit/poll；pending 是 **HTTP 202**；报价只在 done 回包 `usage.cost_in_usd_ticks` | `POST /v1/videos/generations` → `GET /v1/videos/{request_id}` | Bearer | grok-imagine-video-1.5（初代已下线） | 【实测 2026-09-22】 | 14 §2、§3 第 8 条 | 129 |
| 🎬 视频 · OpenAI Sora | submit **multipart**；`/content` 是 API 端点下载**要带**认证头 | `POST /v1/videos` → `GET /v1/videos/{id}` + `/content` | Bearer | OpenAI | 📄【文档】⚠ 未标注实测 | 14 §2、§3 第 4 条 | — |
| 🎬 视频 · Google Veo | `:predictLongRunning` + operations `GET {done:bool}` | `:predictLongRunning` → operations `GET` | `x-goog-api-key` | Google | 📄【文档】⚠ | 14 §2 | — |
| 🎬 视频 · 中继 openai-videos | 中继把 sora／grok-imagine／wan2.5／kling／hailuo 收敛到 OpenAI 式 `/v1/videos`；**同一模型 id 在官方与中继走不同协议** | `/v1/videos` | Bearer | New API 等 | 【实现】 | 14 §4 | — |
| 🎤 ⓐ OpenAI 兼容转写 | multipart 文件字段 `file`，`response_format=verbose_json` 给 `segments[].start/end`（**秒**） | `POST {base}/audio/transcriptions` | Bearer；本地无密钥时不发 | OpenAI whisper-1／gpt-4o-transcribe、Groq、硅基流动、302.AI、智谱 glm-asr、本地 WhisperX | 【文档】【实现】（本库 ⓐ 无实测、无离线测试） | 16 §1、§3、§10.2 | — |
| 🎤 ⓑ 百炼同步识别 | base64 data URI 放 JSON body `input.messages[].content[{audio}]`；头 `X-DashScope-SSE: disable`；**无句级时间戳** | `POST {base}/services/aigc/multimodal-generation/generation`（默认 `https://dashscope.aliyuncs.com/api/v1`） | Bearer | 百炼 qwen3-asr-flash、qwen-audio-3.0-asr-flash、fun-asr-flash-* | 【实测 2026-09-13】 | 16 §1、§4 | — |
| 🎤 ⓒ 百炼录音文件转写（filetrans） | 模型名以 `-filetrans` 结尾；五步：取凭证 → OSS 表单上传（不带 Authorization）→ 异步提交 → 轮询 → 下载结果 JSON；句级 + 词级**毫秒** | `GET /uploads?action=getPolicy&model=…` → OSS → `POST /services/audio/asr/transcription`（头 `X-DashScope-Async: enable` + `X-DashScope-OssResourceResolve: enable`）→ `GET /tasks/{id}` | Bearer（上传与下载两步**不带**） | 百炼 qwen-audio-3.0-asr-flash-filetrans（实测）、qwen3-asr-flash-filetrans／fun-asr／paraformer-v2（文档） | 【实测 2026-09-13】 | 16 §1、§5 | — |
| 🎤 附：私有 SDK／HTTP | 豆包 `X-Api-*` 头 + 响应头 `X-Api-Status-Code == 20000000` 判成败；Gemini transcribe 走 `interactions.create`；Deepgram／ElevenLabs／CAMB／Gladia 各自 SDK | 各家私有 | 各家私有 | pyVideoTrans 渠道 | 【实现】（本库未独立复核报文） | 16 §10.2 | — |

---

## 2. 对话四族功能对照表

行 = 功能维度，列 = 四族。每格只放结论 + 关键字段名；报文片段、词表翻译、平台差异在 §3 对应小节。

| 功能维度 | ① Chat Completions | ② Responses | ③ Gemini | ④ Anthropic | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseURL 归一化 | ✅ base 自带 `/v1`，直接拼 path，**不补 `/v1`**（中继路由在 `/v1` 之下，补了就断） | ✅ 同 ① | ✅ base 自带 `/v1beta`；额外剥尾部 `/models` | ✅ base 是根地址；`anthropicRoot` 剥 `/messages`、`/v1` 再拼 `root + "/v1" + path`；旧 bug 只拼 `/messages` → 照第三方文档粘贴一律 404 | 【实现】 | 3.1；02 §4 | — |
| 鉴权头 | ✅ `Authorization: Bearer`；无 key 省略整个头；无 compat 模式；Azure `api-key` 不做 | ✅ Bearer（同 ①） | ✅ `x-goog-api-key`；compat `bearer`／`both`；`?key=` 不实现 | ✅ `x-api-key` + `anthropic-version: 2023-06-01` + `anthropic-dangerous-direct-browser-access: true`；compat `bearer`／`both`（`both` 官方端点拒双凭证） | 【实现】 | 3.1；02 §5 | — |
| CORS／浏览器直连 | ✅ 打包版原生 HTTP 无 preflight；本地 Ollama Windows 打包版 403 → http 层按「URL 指向本机」覆盖 `Origin` | — | — | ✅ `anthropic-dangerous-direct-browser-access` 打包版是 no-op，为 dev 浏览器环境而带；不带则官方拒绝浏览器 origin | 【实现】 | 3.1；02 §6 | — |
| system 放哪 | ✅ `messages[0].role="system"` | ✅ 顶层 `instructions`（全部 system hoist、`\n\n` join，**恒发哪怕空串**）；上游判不收时改为 `input` 开头 `{role:"developer"}` | ✅ 顶层 `systemInstruction:{parts:[{text}]}`（camelCase） | ✅ 顶层 `system` 字符串（多条 `\n\n` join；`ContentPart[]` 须拍平，否则 `[object Object]`）；消息数组内**无** system 角色 | 【实现】【实测 2026-09-24】 | 3.2；02 §1、§2.1、§7.1 | — |
| 消息角色与内容块 | ✅ 容器 `messages[]`；模型侧 `assistant`；`content` 字符串或 part 数组；允许连续同角色；tool 结果 `role:"tool"` + `tool_call_id` | ✅ 容器 `input[]`；user `{role, content:[{type:"input_text"}…]}`；调用 `{type:"function_call", call_id, name, arguments}`；结果 `{type:"function_call_output", call_id, output}` | ✅ 容器 `contents[]`；模型侧 **`model`**；`parts[].text`；结果是 `role:"user"` 的 `parts[].functionResponse` | ✅ 容器 `messages[]`；模型侧 `assistant`；**交替律**：首条 user、相邻交替，连续 tool 合成一条 user；工具轮 content 顺序 `[thinking…, tool_use…]` | 【实现】 | 3.2；02 §1、§2 | —（坑 21 在 agent-runtime-architecture skill） |
| 图片输入 | ✅ `{type:"image_url", image_url:{url: dataURL}}`（标准） | ✅ `{type:"input_image", image_url:"data:…", detail?}`（**`detail` 与 `image_url` 并列**；标准） | ✅ `{inlineData:{mimeType,data}}`（标准；Google 两种拼写都收，New API Gemini 面 snake_case 🔇 丢图） | ✅ `{type:"image", source:{type:"base64",media_type,data}}` 或 `source:{type:"url"}`（标准） | 【实现】【实测 2026-09-05／23／26】 | 3.3；02 §1、§2.2 | 111 |
| PDF 输入 | ✅ `{type:"file", file:{file_data: dataURL, filename}}`（**filename 必带**；标准）；方舟另收 `file:{file_url}`／`file:{file_id}` | ✅ `{type:"input_file", filename, file_data}` 或 `file_url`（标准） | ✅ 同 `inlineData` + `application/pdf`（标准；3.8 Flash 一页按图像计 520 token） | ✅ `{type:"document", source:{type:"base64",media_type,data}}` 或 `source.type:"url"`；纯文本 `document` + `citations.enabled`（标准） | 【实现】【实测 2026-09-18／23／26】 | 3.3；02 §1 | — |
| 视频输入 | ⚠ `{type:"video_url", video_url:{url: dataURL}}` **是厂商扩展不是族片段**（千问首创；`fps` 百炼在片段旁、方舟文档在 `video_url.fps`）；按平台放行 | — 来源未提及 | — 来源未提及（Gemini 本身读视频，经 OrcaRouter ① 翻译层 🔇 丢） | — 来源未提及 | 【实测 2026-09-28】 | 3.3；02 §1 | — |
| 音频输入 | ⚠ 仅 ASR 篇：小米 MiMo 走 ① 族 `input_audio` 内容块（【实现】）；02–06 篇未提及 | — | — | — | 【实现】 | 3.3；16 §10.2 | — |
| 流式事件骨架 | ✅ SSE 匿名 chunk，客户端拼 `delta`，`data: [DONE]` 收尾；`content` 可能是 part 数组 | ✅ 类型化事件 `response.created → output_item.added → *.delta → *.done → output_item.done → response.completed`；只读 `data:` 行；容忍 `[DONE]`；无视 `obfuscation` | ✅ SSE，**每 chunk 是完整响应对象**（parts 追加，不是 delta）；流末光秃秃 `{text:""}` | ✅ 类型化 `message_start → content_block_start → content_block_delta → content_block_stop → message_delta → message_stop`；只认 `data:` 行 | 【实现】【实测 2026-08-14／2026-09-26】 | 3.4；02 §3、§7.2 | 108 |
| 流式终止与 usage 位置 | ✅ `finish_reason: stop／length／tool_calls／content_filter`；usage **须开 `stream_options:{include_usage:true}`**，随末 chunk 到且 `choices:[]` | ✅ `response.completed{response.usage}`／`incomplete{incomplete_details.reason}`／`failed`／`error`；无终止事件的流照样 finish（usage 记 0） | ✅ `finishReason: STOP／MAX_TOKENS／SAFETY／RECITATION／MISSING_THOUGHT_SIGNATURE…`；【文档】每 chunk 带 `usageMetadata`；【实测】Vertex 只末块带 → 取最后见到的值 | ✅ `stop_reason: end_turn／tool_use／max_tokens／refusal／pause_turn`；usage 分两次：`message_start` 给 input，`message_delta` 给 output + stop_reason | 【实现】【实测 2026-09-26】 | 3.4；02 §1、§3.2、§7.2 | 108、109 |
| 思考强度字段与词表 | ✅ 顶层 `reasoning_effort`；六档 → off=`"none"`、low／medium／high 同名、max=`"max"`；**`"none"` 不是族级关闭**（DeepSeek 需 `thinking:{type:"disabled"}`） | ✅ 嵌套 `reasoning:{effort, summary:"auto"}`；端点七档 `none／minimal／low／medium／high／xhigh／max`，菜单取六档；off → `{effort:"none"}` 无 summary | ✅ `generationConfig.thinkingConfig.thinkingLevel: LOW／MEDIUM／HIGH`（**全大写**）+ 必带 `includeThoughts:true`；off → `"LOW"`（关不掉；旧 `MINIMAL` 3.8 Flash 400 已推翻）；AI Studio 直连档位值小写 `"low"` 也收、枚举外 `"lowest"` ❌ 400【实测 2026-09-28】（03 §2） | ✅ `thinking:{type:"adaptive"／"enabled"／"disabled", budget_tokens?, display?}` + `output_config.effort: low／medium／high／max`；off → `effort:"low"`（`disabled` 多款 400）。第三方 ④ 兼容层的默认值与 `disabled` 结局按平台 × 模型：收下真关（DeepSeek、百炼千问、智谱 4.6、MiniMax-M3）／拒绝会响（智谱 5.3 系 1210、百炼托管 M2.5／glm-5.3 点名 `enable_thinking`）／收下照想 🔇（MiniMax-M2.7、百炼 kimi-k2-thinking），见 03 §3.5 | 【实现】【实测 2026-09-26】【实测 2026-09-28】【文档 2026-08】 | 3.5；03 §2、§3、§3.5、§7.1 | 114、147、217、222 |
| 思考取回位置 | ✅ `delta.reasoning_content`／`delta.reasoning`（候选表按「有非空文本」取）+ `<think>` 兜底切分；方舟 2.1 起 `reasoning_content` 只是摘要、密文在 `delta.encrypted_content` | ✅ `response.reasoning_summary_text.delta`（`reasoning_text.delta` GPT-5.x 未出现、千问文档有）；`reasoning_tokens:0` 时无 reasoning 条目 | ✅ `part.thought === true` 的文本 part（3.8 Flash 一整段给出，流式不逐字）；`thoughtSignature` 挂在正文 text part 上 | ✅ `thinking_delta.thinking`（仅发了 `display:"summarized"` 才有）；流形 `content_block_start` 带 `signature:""` → `thinking_delta`×N → `signature_delta` | 【实测 2026-09-14／23／26】 | 3.6；03 §4、§7.2 | 107 |
| 思考回传载体与缺失后果 | ✅ `_reasoning:{field,text}` 原字段名回传（方舟旁加 `encrypted:{modelId,value}`）；只挂带 tool_calls 的 assistant；缺失：DeepSeek ❌ 400、方舟 🔇 降级、GLM 接受 | ✅ `_responseItems:{modelId,items}` 收自 `output_item.done` 整组放回 `input`；缺失**不报错**（四种都 200） | ✅ `_geminiModelParts` 整组原样（含 thought parts 与 `thoughtSignature`；剔除流末 `{text:""}`）；缺失：200 + `finishReason: MISSING_THOUGHT_SIGNATURE`，3.8 Flash ❌ 400 | ✅ `_thinkingBlocks:{modelId,blocks}` 有序原样（含 `redacted_thinking`）；缺失 🔇 静默关掉这轮思考；改 `signature` ❌ 400 | 【文档 2026-08】【实测 2026-09-23／26】 | 3.7；03 §5、§7.3；02 §7.3 | 137 |
| JSON mode 字段 | ✅ `response_format:{type:"json_object"}`；前置：上下文含 "JSON" 字样否则官方报错（千问 400），缺则**条件追加** cue | ✅ `text:{format:{type:"json_object"}}`；缺 "json" 同样 400 | ✅ `generationConfig.responseMimeType:"application/json"` + cue **总是双发**（有模型 🔇 无视） | ❌ **无 JSON mode 参数**（发 `response_format` 硬 400）；cue 是全部机制；档位只有 `json_schema`／`off` | 【文档】【实测 2026-09-19／26】 | 3.8；04 §2、§5.1 | — |
| JSON schema 字段与 strict | ✅ `response_format:{type:"json_schema", json_schema:{name, schema, strict:true}}`（**`strict` 要发**）；默认不用，按模型 id 表抬升 | ✅ `text:{format:{type:"json_schema", name, schema}}`（无 `json_schema` 包装层；**不发 `strict`**，官方自动升 true；New API `[Pro]` 档不论写不写都 🔇 丢 format——旧：显式 `strict:true` 才丢 → 新：2026-09-24 扩展，其余上游两种写法都执行，见 22 §3） | ✅ `generationConfig.responseJsonSchema`（标准 JSON Schema）或旧 `responseSchema`（OpenAPI 方言）**互斥只发一个** | ✅ `output_config:{format:{type:"json_schema", schema}}`（与 `effort` 同对象合并）；官方限制 `additionalProperties:false` 必须、不支持 `min/max*`、`pattern`、递归 `$ref` | 【实测 2026-09-23／24／26】 | 3.8；04 §2、§5.1 | — |
| 工具定义形状 | ✅ 嵌套 `{type:"function", function:{name, description, parameters}}` | ✅ 扁平 `{type:"function", name, description, parameters, strict:false}`（**`strict:false` 必须显式**） | ✅ `tools[0].functionDeclarations[{name, description, parameters}]` | ✅ `{name, description, input_schema}`（唯一改 schema 字段名） | 【实现】 | 3.9；05 §1；02 §7.1 | — |
| tool_choice 词表 | ✅ `"auto"／"none"／"required"／{type:"function", function:{name}}` | ✅ `"auto"／"none"／"required"／{type:"function", name}`（去 `function` 包装；只随函数工具发；无「思考中禁止强制」） | ✅ `toolConfig.functionCallingConfig.mode: AUTO／ANY／NONE`；具名 = `ANY` + `allowedFunctionNames:[name]` | ✅ `{type:"auto"／"any"／"tool"(+name)／"none"}`；**只在声明了本地工具时才发** | 【实现】 | 3.9；05 §2；02 §7.1 | — |
| 流式工具参数拼接 | ✅ 按 `delta.tool_calls[].index` 分组拼 `arguments` 字符串；**id 也可能分片**（`entry.id += partial.id`） | ✅ 按 `output_index` 分组；参数两次到达（delta + `function_call_arguments.done` 整串），**以整串为准** | ✅ `functionCall` 一次给全（已解析对象）；旧型号无 id 自造 `gtc_…`，3.8 Flash 起带 `id` | ✅ 按块索引拼 `input_json_delta.partial_json`；**空参数不流 delta，`""` → `"{}"`** | 【实现】【实测 2026-08-08／2026-09-26】 | 3.10；05 §3；02 §3.2 | 105、106 |
| 工具配对义务 | ✅ `tool_call_id` 配对；空串 id 按缺失处理（否则下一轮重复 id 400） | ✅ `call_id` 配对；`function_call_output` 回 `call_id` | ✅ 靠**函数名**匹配（旧型号）；带 id 时回 id 也收；同名并行调用对应关系在旧型号不可表达 | ✅ `tool_use_id` 配对；一轮所有 `tool_result` 须合在一条 user 里一起到达 | 【实现】【实测 2026-09-26】 | 3.10；05 §4；02 §2 | 106 |
| 服务端工具 wire 形状（web_search／code／fetch） | Ⓓ 顶层 `enable_search:true`、`search_options:{search_strategy:"agent_max"}`、`enable_code_interpreter:true`（只放行 compat）；OpenAI 形 `web_search_options`；**搜索无痕**无来源 | ✅ `tools:[{type:"web_search"}]`（OpenAI／xAI 同形）、千问 `web_extractor`／`web_search_image`／`image_search`／`code_interpreter`；事件 `web_search_call`、`code_interpreter_call` 等 | ✅ `tools[]` 独立项 `{googleSearch:{}}`／`{urlContext:{}}`／`{codeExecution:{}}` 与 `functionDeclarations` 并列；回报在 `groundingMetadata`、`executableCode`／`codeExecutionResult` | ✅ 版本化条目 `{type:"web_search_20250305", name:"web_search", max_uses:10}`（也见 `web_search_20260209`、`web_fetch_20250910`、`code_execution_20250825`）；响应 `server_tool_use → web_search_tool_result → citations` | 【实测 2026-09-17／18／26】 | 3.11；05 §5 | 10、192、193 |
| 服务端工具续跑 | — 来源未写 ① 官方续跑信号 | — 来源未写 | — 来源未写 | ✅ `stop_reason:"pause_turn"` → verbatim 续跑（`encrypted_content` 一字不改，重建块 400；`MAX_PAUSE_CONTINUATIONS = 4`）；兼容端（MiniMax）停在 `*_tool_result` 报 `end_turn` 且拒收自己的块 → transcript 纯文本续跑 | 【实测 2026-08】【实现】 | 3.12；05 §6 | — |
| 工具按需加载 | ❌ 无 | ✅ GPT-5.4+：`defer_loading:true`、`{type:"tool_search", execution:"server"／"client"}`、`{type:"namespace"}`、`{type:"additional_tools", role:"developer", tools}`；下一轮 `input` **必须**回 `tool_search_output`；xAI 规格有实测 403 | ❌ 请求带 `defer_loading` 整个被拒（第三方报告） | ✅ Claude 4.5+：`defer_loading`、`tool_search_tool_regex_*`／`_bm25_*`；至少一个非延迟工具否则 400；与 `cache_control` 同现 400 | 【文档 2026-09】【实测 xAI 403】 | 3.13；05 §7 | — |
| usage 字段与缓存字段 | ✅ `usage.prompt_tokens／completion_tokens`（含思考）、`prompt_tokens_details.cached_tokens`（input 子集）、`completion_tokens_details.reasoning_tokens`；DeepSeek 顶层 `prompt_cache_hit_tokens／miss` | ✅ `usage.input_tokens／output_tokens`、`input_tokens_details.cached_tokens`／`cache_write_tokens`、`output_tokens_details.reasoning_tokens`；`attribution.request_fields.instructions.input_tokens` | ✅ `usageMetadata.promptTokenCount／candidatesTokenCount／thoughtsTokenCount／toolUsePromptTokenCount／cachedContentTokenCount`；**思考不在 candidates 里**、toolUse 在 prompt 之外 | ✅ **三桶不重叠**：`input_tokens` + `cache_read_input_tokens` + `cache_creation_input_tokens`；`output_tokens_details.thinking_tokens`（子集）；`server_tool_use.{web_search_requests,…}` | 【实现】【实测 2026-09-26】【文档；修复 2026-09-14】 | 3.14；06 §1；02 §1 | 186 |
| 错误信封 | ✅ HTTP 4xx + body；智谱 `{"error":{"code":"1210","message"}}` 业务码是字符串；MiniMax `base_resp.status_code`（1004／1008／1002，0 成功）；SSE 体内 `data:{"error"}` | ✅ `response.failed`／`error` 事件／裸 `{error}`（无 `type`）；`response.incomplete.incomplete_details.reason` | ✅ 400 原文（Vertex）；OrcaRouter 改写成 `{"error":{"message","type":"invalid_argument","param":"","code":400}}`，路径 `***` | ✅ 400 带原文（``Invalid `signature` in `thinking` block``）；官方 `error.type`；OrcaRouter 改写成 `{"error":{"type":"<nil>",…},"type":"error"}`；第三方 ④ 兼容层各有信封：DeepSeek 422 反序列化文案、智谱 `{"type":"invalid_request_error","code":"1210","message":"[1210][…][<request id>]"}`、MiniMax `{"type":"invalid_request_error","message":"invalid params, … (2013)"}`、百炼透传上游 `<400> InternalError.Algo.InvalidParameter: … enable_thinking …`（点名别家协议字段）；MiniMax／DeepSeek 未知模型名不报错静默改映射（06 §2） | 【实测 2026-09-19／24／26／28】 | 3.15；06 §2；03 §3.5 | 112、219、221 |
| HTTP 200 里的失败形态 | 🔇 静默丢弃；`finish_reason: content_filter`／智谱 `sensitive`／`network_error`／`model_context_window_exceeded`；空 `content` + `stop` 与坏中转无法区分 | 🔇 流里 `response.failed`（千问 `Normal mode does not support Code interpreter…`）；`status:"completed"` 的空 message 条目是**正常结束** | 🔇 `promptFeedback.blockReason`；`finishReason ∈ {SAFETY, PROHIBITED_CONTENT, BLOCKLIST, RECITATION, SPII, IMAGE_SAFETY}`；`GEMINI_REQUEST_FAULTS`（`MISSING_THOUGHT_SIGNATURE`、`UNEXPECTED_TOOL_CALL`、`TOO_MANY_TOOL_CALLS`、`MALFORMED_RESPONSE`） | 🔇 `stop_reason:"refusal"`（必须 throw）；丢 thinking 块静默关思考；翻译层中转丢 PDF／URL 图片 | 【实测 2026-09-15／23】【文档 2026-09】 | 3.15；06 §2；02 §7.2 | 109 |
| 未知顶层字段的态度 | ❌ 官方端点直接拒绝（`enable_search` 等 400）；智谱一律放过；方舟 🔇 忽略 `enable_thinking` | ✅ 官方与 xAI 忽略（仍按最小公倍数发送） | — 来源未写官方口径；New API Gemini 面 🔇 无视未知键（snake_case 丢图） | ❌ 官方**未知键 400**；第三方 ④ 兼容层顶层未知字段**四家都 200 放过**，`thinking.type:"bogus"` 四家四种：MiniMax 🔇 200 且开思考、DeepSeek ❌ 422 点名枚举、智谱 ❌ 1210、百炼 ❌ 400 `Request body format invalid`（03 §3.5） | 【实测 2026-09-18／19／28】【实现】 | 3.16；03 §2、§3.5；02 §1 表后、§7.1 | 114、217、220 |
| max tokens 字段 | ✅ `max_tokens` → `max_completion_tokens`（选填；被拒自动换拼写重试一次） | ✅ `max_output_tokens`（账号池上游 🔇 无视且回显抓不到） | ✅ `generationConfig.maxOutputTokens`（选填） | ✅ `max_tokens` **必填、无服务端默认**；`budget_tokens` 必须 < `max_tokens` | 【实现】【实测 2026-09-24】 | 3.16；02 §1；06 §5 | 65 |
| 温度与思考的关系 | — 来源未写族级约束（方舟 ① 面 `0／0.1／0.3` 都收敛） | ⚠ 官方口径未写；中转站账号池 `temperature:0.5` 🔀 回显 `1.0`，网关 500 | — 来源未写 | 📄 官方思考开着只收 `temperature:1`（别的 400）→ **在想就不发温度**；`switch` 类目关思考时按类目声明（方舟听、`0` 等于没发；MiniMax 不听） | 【文档】【实测 2026-09-24／28】 | 3.16；03 §3.4；06 §2 | — |

---

## 3. 各功能维度展开

### 3.1 端点、鉴权、baseURL、CORS

**baseURL 归一化不对称**（【实现】`urls.ts`）：

| 族 | 作者可能粘贴的 base | 归一化 | 拼出的端点 |
| --- | --- | --- | --- |
| ① ② | `https://relay/openai`、`https://api.openai.com/v1` | 不补 `/v1`（中继合法路由在 `/v1` 之下） | `{base}/chat/completions`、`{base}/responses` |
| ③ | `…/v1beta`、`…/v1beta/models`（粘了模型列表 URL） | 剥尾部 `/models` | `{base}/models/{id}:streamGenerateContent?alt=sse` |
| ④ | 根、根+`/v1`、完整 `…/v1/messages` | `anthropicRoot`：先剥 `/messages` 再剥 `/v1` | `root + "/v1" + path` |

官方端点 base 存空串，适配器 `baseUrl || DEFAULT_*` 兜底；官方/compat 拆分的旧行迁移在**读取时**幂等做。

**鉴权矩阵**（【实现】02 §5）：

```text
AuthMode = default | bearer | both
可选鉴权模式：anthropic_compat、gemini_compat → [default, bearer, both]；其余 standard → 只有 [default]
```

| 族 | 默认 | compat 可选 | 不做的 |
| --- | --- | --- | --- |
| ① ② | `Authorization: Bearer`；无 key 时整个头省略（Ollama／LM Studio 收到空 Bearer 会拒） | 无 | Azure `api-key`：URL `/openai/deployments/{d}/...?api-version=` 与模型标识都不同，要做是另一族 |
| ③ | `x-goog-api-key` | `bearer`／`both` | `?key=` 查询串（key 进代理日志／报错信息） |
| ④ | `x-api-key` + `anthropic-version: 2023-06-01`（pinned，wire 形状按它版本化）+ `anthropic-dangerous-direct-browser-access: true` | `bearer`／`both`（`both` 只在 compat：api.anthropic.com 拒双凭证） | — |

- ④ 的 `ANTHROPIC_API_KEY→x-api-key` 与 `ANTHROPIC_AUTH_TOKEN→Bearer` 是两套一等约定，大量网关只认 Bearer，读错头 = 401。`default` 存 NULL，读取时按 standard 校验残留值。
- CORS：打包版（Tauri 原生 HTTP）无 preflight，`anthropic-dangerous-direct-browser-access` 是 no-op，为 dev 浏览器环境保留；本地 Ollama Windows 打包版 403 → http 层覆盖 `Origin`，按「URL 指向本机」判断，不做 provider 枚举。

详见：02 §4、§5、§6。

### 3.2 system 与消息结构

| 维度 | ① | ② | ③ | ④ |
| --- | --- | --- | --- | --- |
| system | `messages[0].role="system"` | 顶层 `instructions`（恒发，含空串）；能力表 `instructionsField` 判不收 → `input[0] = {role:"developer", content}` 且不发 `instructions` 键 | 顶层 `systemInstruction:{parts:[{text}]}` | 顶层 `system` 字符串；`ContentPart[]` 用 `textOf` 拍平 |
| 模型侧角色 | `assistant` | assistant 条目 `{type:"message"}`／`function_call`／`reasoning` | **`model`** | `assistant` |
| 连续同角色 | 允许 | — | — | ❌ 交替律：丢开头 assistant、合并同角色、连续 tool 合成一条 user |
| 工具结果 | `{role:"tool", tool_call_id, content}` | `{type:"function_call_output", call_id, output}` | `role:"user"` 的 `parts[].functionResponse` | `role:"user"` 的 `{type:"tool_result", tool_use_id}` block |

② 请求骨架（【实现】02 §7.1）：

```jsonc
POST {base}/responses          // base 与 ① 同，Bearer
{
  "model": "…",
  "instructions": "…",         // 全部 system 消息 hoist 并 "\n\n" join；恒发，哪怕空串
  "input": [ /* items */ ],
  "tools": [{ "type": "function", "name", "description", "parameters", "strict": false }],
  "tool_choice": "auto" | "none" | "required" | { "type": "function", "name": "f" },
  "reasoning": { "effort": "medium", "summary": "auto" },
  "text": { "format": {…}, "verbosity": "low" },
  "store": false,
  "stream": true
}
```

- ② `store:false` 恒发（零数据保留组织不发被拒；也是 reasoning 条目附 `encrypted_content` 的前提）。`instructions` 缺失 → 中转站 🔀 注入 4.4K–9K token 系统提示；有的网关上游见到 `instructions` 键就追加 ~1.2K 护栏——两种上游在同一台、同一个模型 id 上并存，按上游裁决非全局翻转【实测 2026-09-24】。
- ④ 转换器四件必做：丢头部 assistant、合并同角色、连续 tool 合成单条 user、system hoist；工具轮 assistant content 顺序 `[...thinkingBlocks, ...tool_use blocks]`（顺序即 400 红线）。`labelAuthorText`：合并进带 `tool_result` 的 user 消息的作者文本前加【…】标签（坑 21）。`tool_use.name` 三级兜底 `tc.function.name || toolCallIdToName.get(tc.id) || "unknown_function"`。
- ③ `assistant → model`；请求键一律 camelCase（`inlineData`／`mimeType`／`systemInstruction`）：Google 两种都收，New API Gemini 面 snake_case **200 照回但图片与系统提示静默丢弃**【实测 2026-09-05；坑 111】。

详见：02 §2.1、§2.2、§7.1。

### 3.3 多模态输入

| 输入 | ① | ② | ③ | ④ |
| --- | --- | --- | --- | --- |
| 图片 | `{type:"image_url", image_url:{url: dataURL}}` | `{type:"input_image", image_url:"data:…", detail?}`（`detail` 与 `image_url` 并列） | `{inlineData:{mimeType, data}}` | `{type:"image", source:{type:"base64", media_type, data}}`／`source:{type:"url"}` |
| PDF | `{type:"file", file:{file_data: dataURL, filename}}`（base64 形态 filename 必带） | `{type:"input_file", filename, file_data}`／`file_url` | `{inlineData:{mimeType:"application/pdf", data}}` | `{type:"document", source:{type:"base64", media_type, data}}`／`source.type:"url"`；纯文本 `document` + `citations.enabled` |
| 视频 | ⚠ 厂商扩展 `{type:"video_url", video_url:{url: dataURL}}`；`fps` 百炼写片段旁、方舟文档写 `video_url.fps` | — | — | — |
| 音频 | ⚠ 仅 ASR 篇：MiMo `input_audio` 内容块（【实现】） | — | — | — |

- **形状被接受 ≠ 内容送到了模型**。翻译层中转（New API · Kiro 渠道 Claude，【实测 2026-09-23】）：④ `document` base64／url、① `file` PDF 都 200 但 🔇 丢（模型答「没看到文档」，33 s vs 3 s）；④ 图片 `source.type:"url"` 与 ① http `image_url` 也丢；只有 base64／data URL 图片送得到；纯文本 `document` + `citations.enabled` 读到但无 `citations` 字段。同台 CC／AWSb PDF 读到（AWSb 30 s 且唯一回 `citations`）；anti 连纯文本 document 也没读到；URL 图片 anti ❌ 500 `failed to decode base64 data`、AWSb ❌ 400 `URL sources are not supported`。**整台可移植的只有内联 base64 图片**。
- 同台 GPT-5.6（【实测 2026-09-24】）：② `input_file` 的 `file_data`／`file_url`、① `file`、data／http 图片全部读到——丢文档是 Claude 翻译层的事。http 图片放拒爬虫主机时：网关 ❌ 500 `count_token_failed`（中转站计 token 前自己下载）、`[Pro]` ❌ 400 `Error while downloading file`、`[特价Pro]` 流里 `error` 后接空答（200）。
- 回包原样网关（OrcaRouter，【实测 2026-09-26】）：① `file`、② `input_file`、④ `document`、③ `inlineData` + `application/pdf` 四面都读到；③ 一页 PDF **按图像计 520 token**；③ 16×16 PNG 记 1,098 prompt token；④ Sonnet 5 没带 `cache_control` 却记 1,630 缓存写入 token（Opus 5.5 没有，原因未明 ⚠）。
- 方舟 ① PDF 三形态【实测 2026-09-18／23】：`file:{file_data, filename}` 可读；扁平 `{type:"file", file_data}` ❌ 400 `missing messages.content.file`；`file:{file_url}`（公网 URL，厂商写仅 ②）与 `file:{file_id}` 都收。DashScope `file` 形状镜像仅 qwen3.8-max。
- `video_url` 六端点【实测 2026-09-28】（4 秒先红后蓝片段，输入 token 不带 → 带 → 带 `fps:1`）：百炼 `qwen3-vl-plus` ✅ 34 → 1,241 → 641（`fps` 生效）；方舟 `doubao-seed-2.0-mini` ✅ 59 → 2,795 → 2,795（`fps` 不改这段账单，4 秒片段可能在最少帧数之下 ⚠）；DeepSeek `deepseek-flash` ❌ 422 `unknown variant video_url, expected one of text, image_url, file`；xAI `grok-4.3` ❌ 400 `Empty content block`；OrcaRouter ① `google/gemini-3.8-flash` 🔇 200 答错、25 → 25；OrcaRouter ① `openai/gpt-5-mini` ❌ 400 `The upstream provider rejected this request`。智谱收 `video_url`、🔇 忽略 `fps`（更早的样本，型号与日期未标 ⚠ ⏳待复核）（日期未标）。百炼对片段挑剔：320×240／10 fps ❌ 400 `Invalid video file`。做法：视频输入做成**平台格**，不按族放行。
- 测法：用模型猜不出的内容（PDF「The secret word is PELICAN 7342」、纯色图、先红后蓝视频）看三件事：HTTP 状态、答没答对、输入 token 带／不带片段之差。

详见：02 §1、§2.2；06 §2。

### 3.4 流式事件骨架、终止与 usage 位置

共用 SSE 读法骨架（【实现】02 §3.1）：

```
res.body.getReader() + TextDecoder({stream: true})
→ 按 "\n" split
→ 最后一个不完整行留到下次 read（行缓冲）
→ 流结束后再 flush 一次 buffer 尾巴
```

| 维度 | ① | ② | ③ | ④ |
| --- | --- | --- | --- | --- |
| chunk 形态 | 匿名 chunk，`choices[].delta` 拼接；`content` 字符串**或** part 数组 `[{"type":"text","text":"…"}]`（兼容层镜像）【实测 2026-08-14】 | 类型化事件；只读 `data:` 行；文本 delta 旁带 `obfuscation` 随机填充（只读 `delta`；`include_obfuscation:false` 无效） | **每 chunk 是完整响应对象**，parts 直接追加（按 delta 拼会重复） | 类型化事件；`content_block_start` 浅拷贝整块留存（含不认识的类型） |
| 收尾 | `data: [DONE]` | `response.completed`／`incomplete`／`failed`／`error`；`[DONE]` 不属此协议但要容忍（xAI 会发）；可能无终止事件 | 光秃秃 `{text:""}` part；流式 `thoughtSignature` 落在最后一块 `{text:"", thoughtSignature}` | `message_stop` |
| 结束原因 | `finish_reason: stop／length／tool_calls／content_filter` | `incomplete_details.reason`: `max_output_tokens` → truncated、`content_filter` → throw | `finishReason: STOP／MAX_TOKENS／SAFETY／RECITATION／MISSING_THOUGHT_SIGNATURE…` | `stop_reason: end_turn／tool_use／max_tokens／refusal／pause_turn`（在 `message_delta`） |
| usage 位置 | 须发 `stream_options:{include_usage:true}`；随末 chunk 到，末块 `"choices": []`——`choices?[0]` 挡不住空列表，抛越界被 catch 吞 → usage 静默丢（坑 108） | `response.completed.response.usage`；无终止事件时 usage 记 0、stopReason 缺失 | `usageMetadata`：【文档】每 chunk 都带；【实测 2026-09-26】Vertex 只最后一块带 → 取最后见到的值不累加 | `message_start` 给 input，`message_delta` 给 output；`message_delta` 不能清零 input（`input` 缺失时沿用 `prev.inputTokens`） |
| 思考计数 | `usage.completion_tokens_details.reasoning_tokens`（末块） | `usage.output_tokens_details.reasoning_tokens` | `usageMetadata.thoughtsTokenCount` | `usage.output_tokens_details.thinking_tokens`（`output_tokens` 子集） |

② 事件序列（【实现】02 §7.2）：

```
response.created → response.in_progress
→ output_item.added {item:{type:"reasoning"|"message"|"function_call"|"web_search_call"…}}
→ reasoning_summary_text.delta ×N / output_text.delta ×N / function_call_arguments.delta ×N
→ function_call_arguments.done {arguments}     // 完整串
→ output_item.done {item: 完整条目，含 encrypted_content}
→ response.completed {response:{usage, reasoning, temperature, …}}
  | response.incomplete {response.incomplete_details.reason} | response.failed | error
```

- ② `status:"completed"` 的空 message 条目是正常结束：工具结果交付后 GPT-5.x 以 `phase:"final_answer"`、文本空、`status:"completed"` 的 message 条目收尾【实测 2026-09-15；坑 109】。**① 没有这个判据**（空 `content` + `finish_reason:stop` 与坏中转无法区分），不照搬。
- ② 终止响应**回显请求字段**（`reasoning.effort`、`temperature`、`text.format`、`instructions`、`max_output_tokens`）→ 回显比对（06 §4.1）；`max_output_tokens` 被无视时回显抓不到（坑 65）。① 无回显字段。
- ④ 事件：`content_block_delta` 细分 `text_delta`／`input_json_delta`／`thinking_delta`／`signature_delta`；`event:` 行无 payload。

详见：02 §3、§7.2；06 §1、§4.1。

### 3.5 思考强度

配置层自有六档（【实现】03 §2）：

```text
ReasoningEffort = default | off | low | medium | high | max
```

`default` = 一个字段都不发（② 各模型默认不同：5.4 `none`、5.5／5.6 `medium`、Grok 4.5／4.6 `high`）。翻译表：

| 本项目档位 | ① `reasoning_effort` | ② `reasoning:{effort, summary}` | ③ `generationConfig.thinkingConfig.thinkingLevel` | ④ `output_config.effort`（+ `thinking`） |
| --- | --- | --- | --- | --- |
| off | `"none"` | `{effort:"none"}`（无 summary） | `"LOW"`（关不掉；**2026-09-26 前写 `MINIMAL`**，3.8 Flash ❌ 400 `Thinking level MINIMAL is not supported for this model.`，已推翻） | `"low"`（`disabled` 被 Opus 5.5／Fable 5.1 ❌ 400 `requires adaptive thinking; omit thinking or use thinking.type=adaptive and output_config.effort`） |
| low／medium／high | 同名 | `{effort:<同名>, summary:"auto"}` | `LOW／MEDIUM／HIGH`（**全大写**；小写 `thinking_level` 属于 Interactions API） | 同名 |
| max | `"max"` | `{effort:"max", summary:"auto"}` | `"HIGH"`（枚举到头） | `"max"` |

方言 `ThinkingDialect = adaptive | extended | switch | none`（作者声明的 L3 字段，不探测；缺省：anthropic 族猜 `adaptive`，其余 `none`），各族发出的片段：

| 方言 | ④ 发出 | ① 发出 |
| --- | --- | --- |
| `adaptive`（Claude 4.6+） | `{"thinking":{"type":"adaptive","display":"summarized"}}`（`display` **必须显式**：默认 `"omitted"` 文本空但全额计费） | `{"reasoning_effort": …}` |
| `extended`（Claude ≤4.5；Gemini 2.5 同形） | `{"thinking":{"type":"enabled","budget_tokens":N,"display":"summarized"}}`；budget 钳 `Math.max(1024, Math.min(16384, maxTokens/2))` | `{"reasoning_effort": …}` |
| `switch` | 关：`{"thinking":{"type":"disabled"}}`；其余：`{"thinking":{"type":"adaptive"}}`（无 display、无 `output_config`；MiniMax、方舟 ④） | `{"enable_thinking": effort ≠ off}` 且**停发** `reasoning_effort`（千问 DashScope） |
| `none`／未声明 | 不发 `thinking` | `{"reasoning_effort": …}`，与未引入方言时逐字节相同 |

各族要点：
- ①：`"none"` 不是族级关闭。DeepSeek 档位表无 `none`（发了 🔇 无视照想照计费），只有顶层 `thinking:{type:"disabled"}` 关得掉【文档 2026-08；2026-09-05 按文档修复未实测 ⚠】，medium 折进 high；GLM 三代三样（5.3 不能关、只收 `low/high/max`；5.2 `none` 关不掉；4.x／5／5.1 无档位 🔇 丢弃）【实测 2026-09-19】；方舟 `none`／`minimal` 真关、七档真分档、`thinking:{type:"auto"}` ❌ 400 InvalidParameter、`disabled` + `high` ❌ 400 `Invalid combination of reasoning_effort and thinking type`、`enable_thinking:false` 🔇 忽略（坑 114）【实测 2026-09-18】；New API ①→④ 转换层上 Claude 的 `max`／`none` 都 🔇 不想（坑 147）【实测 2026-09-23】。
- ②：端点七档 `none／minimal／low／medium／high／xhigh／max`，菜单取六档（去 `minimal`）；非 off 必带 `summary:"auto"`（不发无摘要事件；`auto` 回显 `detailed`）；菜单不按型号裁剪，越界交给端点 400（GPT-5.4 `max` ❌ 400 列合法值；Grok 4.5／4.6 ❌ 拒 `none`、拒 `max`）；`reasoning.mode:"pro"`、`reasoning.context` 不接；中转站账号池 `effort:"none"` 🔀 回显 `medium` 照样推理【实测 2026-09-24】；`gpt-6-luna` 经 OrcaRouter `minimal` 🔀 改写成 `low`【实测 2026-09-26】。
- ③：发 level **强制搭配 `includeThoughts: true`**（不开 = 付钱买看不见的思考）；`thinkingBudget` 与 `thinkingLevel` 只发一代；`thinkingBudget: 0` 经 OrcaRouter 🔇 照样思考（312 token；网关重新序列化可能丢 0 ⚠）；3.8 Flash `thoughtsTokenCount` LOW 193／MEDIUM 641／HIGH 1,348【实测 2026-09-26】；【文档】3.1 Pro 只有 `low/medium/high`，minimal ≠ 关闭（*does not guarantee that thinking is off*）。
- ④：`output_config.effort` 管**整个回复**不只思考；不发 `thinking` 也在思考（adaptive 是默认，Sonnet 5 一题 141 思考 token）；`thinking:{type:"enabled", budget_tokens}` 在 Sonnet 5 也 200 照样思考；`budget_tokens ≥ max_tokens` 官方 400，中转四渠道都 200【实测 2026-09-23／26】。第三方 ④ 兼容层「省略 = 用默认」的默认按平台 × 模型：DeepSeek ④ 默认想、MiniMax-M3 ④ 默认不想、百炼千问想而 qwen-turbo 不想、智谱 4.7 不想而 5.3 关不掉；`disabled` 三种结局（真关／拒绝会响／收下照想 🔇）与判据「文本或签名至少一个非空」见 03 §3.5、§4.1【实测 2026-09-28】。
- ③ 档位值在 AI Studio 直连不分大小写（`"low"`／`"LOW"` 都 200），枚举外 `"lowest"` 400 带 `generation_config.thinking_config.thinking_level` 路径【实测 2026-09-28】（03 §2）。
- `offSpelling: "disable" | "lowest"`：③ off=LOW、④ off=adaptive+low 线上没有真关；「要它少想」的回退在 lowest 类目上既发 off 又带提示【实测 2026-09-28】。

详见：03 §2、§2.1、§3、§3.1–3.3、§7.1、§7.4。

### 3.6 思考取回

| 族 | 读哪里 | 形态 |
| --- | --- | --- |
| ① | `delta.reasoning_content`／`delta.reasoning`（候选表 `REASONING_CONTENT_FIELDS` 按序试）+ 内联 `<think>` 兜底切分 | **按「有非空文本」取不按「字段存在」取**（有中继同时发 `reasoning_content:""` 与非空 `reasoning`【实测 2026-09-14；坑 107】）；非字符串值忽略不强转（有端点旁发结构化 `reasoning_details` 数组） |
| ①（方舟 2.1 起） | `delta.reasoning_content` 是**摘要**；原文密文在 `delta.encrypted_content` | 密文整串落在某一个 delta 上，与一段摘要同帧；只留存不显示 |
| ② | `response.reasoning_summary_text.delta`、`response.reasoning_text.delta`（后者 GPT-5.x 从未出现，千问 Responses 文档有） | `reasoning_tokens: 0` 时即使发了 summary 也无 reasoning 条目——同一请求一次有一次没有，不是 bug |
| ③ | `part.thought === true` 的文本 part | 3.8 Flash：思考摘要是**一个**整段 `{text, thought:true}` part，流式也不逐字；`thoughtSignature` 挂在正文 text part 上【实测 2026-09-26】 |
| ④ | `thinking_delta.thinking` 事件（仅请求发了 `display:"summarized"` 才有） | 流形：`content_block_start` 的 thinking 块带 `signature:""` → `thinking_delta` 连续 → 末尾一条 `signature_delta`（只累积不展示）【实测 2026-09-26，Sonnet 5】 |

方舟 ① 密文帧（【实测 2026-09-23，2.1-turbo】）：

```json
{"choices":[{"delta":{"reasoning_content":"\n","encrypted_content":"djEN…"}}]}
```

- `<think>` 切分器：只认响应开头（允许前导空白）、跨 chunk 用 `danglingPrefix`（`<thi` + `nk>` 分片是常态）、流末未闭合按 reasoning flush；切出的 reasoning 只展示不回传（MiniMax ① 面把 `<think>…</think>\n\n正文` 塞进 `delta.content`）。
- 产出统一 `{reasoning}` chunk，与 `{text}` 不同变体，绝不混进正文流。
- 中转站翻译层可能无视 `display`：Kiro 渠道 ④ `summarized`／`omitted` 都永远返回全文；CC 渠道 opus-5 thinking 块文本恒空（按思考计费无文本）；anti 任何思考参数都无 thinking 块；① 面 `reasoning_tokens` 恒 0（思考算在 `completion_tokens`）——**`reasoning_tokens` 为 0 不能当「没想」判据**【实测 2026-09-23】。

详见：03 §4、§6、§3.3、§7.2。

### 3.7 思考回传

心法：跨轮要回传的东西必须整块留存原物，不能归一化后重建。三个载体都**只挂在带 tool_calls 的 assistant 消息上**。

| 族 | 载体 | 回传形状 | 不回传的后果 | 改动的后果 |
| --- | --- | --- | --- | --- |
| ① DeepSeek 系 | `_reasoning: {field, text}` | 收到什么字段名就用什么名字回（`reasoning_content`） | ❌ **400**（官方原文「若您的代码中未正确回传 reasoning_content，API 会返回 400」）；反向：无工具轮**携带**也 400 `reasoning_content is not allowed in the input messages` | — |
| ① 火山方舟（2.1 起） | `_reasoning` + `encrypted: {modelId, value}` | `reasoning_content` 与 `encrypted_content` 一起回，`encrypted_content` 优先；摘要空时只写密文 | 🔇 只回摘要不报错，厂商原话「推理效果下降」 | 篡改密文报不报错未验 ⚠；换渠道能否解密未测 ⚠ |
| ① 智谱 GLM | `_reasoning` | `reasoning_content` 回传接受（交错思考）；`thinking.clear_thinking:false` = 保留式思考、跨轮原样回传全部历史推理 | 接受 | — |
| ② | `_responseItems: {modelId, items}` | `output_item.done` 的 item（reasoning／function_call／message）整组原样放回 `input`，**替代**裸 `function_call`；服务端工具条目不回传；换模型退回裸 function_call | 不报错：原样／删 reasoning／删 `encrypted_content`／只回裸 function_call 四种都 200 且答对（GPT-5.4／5.5／5.6、Grok）；代价只在质量（5.6 `reasoning.context: all_turns`） | — |
| ③ | `_geminiModelParts: unknown[]` | 整组原始 parts 原样（含 thought parts 与 `thoughtSignature`）；**例外：流末光秃秃 `{text:""}` 剔除**（回灌 ❌ 400 `required oneof field 'data' must have one initialized field`） | 旧型号：200 + `finishReason: MISSING_THOUGHT_SIGNATURE`；3.8 Flash：❌ 400 `Function call is missing a thought_signature in functionCall parts` | 签名位置：正文 text part、并行调用**第一个** `functionCall` part、流式末块 |
| ④ | `_thinkingBlocks: {modelId, blocks}` | 有序块数组原样（`redacted_thinking` 只有不透明 `data` 也要回；过滤条件是「思考类块」）；换模型整组丢弃（别的模型 🔇 忽略且照 input 计费） | 🔇 **静默降级**：API 不报错，直接关掉这轮思考（唯一验证：看响应里还有没有 thinking block） | 改 `signature` ❌ 400 ``Invalid `signature` in `thinking` block``；改 thinking 文本留原签名 200（经网关请求侧结论）【实测 2026-09-26】 |

- ② `encrypted_content` 来源三家不同：OpenAI `store:false` 自带；xAI **必须** `include:["reasoning.encrypted_content"]`（不带回传第二轮照样 200，缺的只是推理延续）；千问 Responses 面无 `encrypted_content`，回传明文 `summary`。官方端点不发 `include` 是否丢加密推理未经官方 key 验证 ⚠。
- ④ 签名校验按渠道：官方／AWSb 篡改 → 400（AWSb 原文 `Invalid signature in thinking block`）；Kiro／CC／方舟 ④ 原样、篡改末尾、删掉 `signature` 三种都 200（坑 137）——**回传出错不响，验证只能看 API 日志存下的块**。方舟 ④ 2.0 系 thinking 块无 `signature`，2.1-turbo 带（`dj…` 开头，与 ① `encrypted_content` 前缀相同，推测同一密文 ⚠）。
- 三个 `_` 载体并存是刻意选择，不泛化承载；泛化的是**剥除**（`_` 前缀丢弃）。

详见：03 §5、§3.2、§3.3、§7.3；02 §7.3；05 §3。

### 3.8 JSON mode 与 schema

四族形状（【实现】04 §2、§5.1）：

| 族 | JSON mode | schema 严格档 | cue（「只输出 JSON」一句） |
| --- | --- | --- | --- |
| ① | `{"response_format":{"type":"json_object"}}` | `{"response_format":{"type":"json_schema","json_schema":{"name","schema","strict":true}}}` | 仅当上下文没有 "JSON" 字样时条件追加（官方／DeepSeek 报错，千问 ❌ 400 `'messages' must contain the word 'json'`） |
| ② | `{"text":{"format":{"type":"json_object"}}}` | `{"text":{"format":{"type":"json_schema","name":"…","schema":{…}}}}`（无 `json_schema` 包装层；**不发 `strict`**） | 同 ① |
| ③ | `{"generationConfig":{"responseMimeType":"application/json"}}` | `generationConfig.responseJsonSchema`（标准 JSON Schema）或旧 `responseSchema`（OpenAPI 方言、大写类型），互斥只发一个 | **总是**双发（有模型 🔇 无视 mimeType） |
| ④ | 无（发 `response_format` ❌ 硬 400；适配器不 spread `extraBody`） | `output_config: { format: { type: "json_schema", schema } }`（与 `output_config.effort` 同一对象合并）；旧写法 `output_format` + beta 头 | 不发 schema 时总是（cue 是全部机制）；发 schema 时不发 |

②：

```jsonc
// json_schema 档（按模型 id 表自动抬升，与 ① 族共用同一批模型）；schema 已按 strict 规则整理
{ "text": { "format": { "type": "json_schema", "name": "…", "schema": { … } } } }
// json_object 档；上下文缺 "json" 字样时追加 cue（与 ① 同一前置条件）
{ "text": { "format": { "type": "json_object" } } }
```

- strict 预处理（strictify）：可选字段改 `type:["string","null"]` 并列入 `required`、`additionalProperties:false`、全字段 required；① ② 都收下 200。① `strict` 键要发（不带时 doubao-seed-2.1-turbo 也越过）；② 刻意省略（官方自动升 `strict:true` 回显 `true`；New API `[Pro]` 档省略与显式 `strict:true` 都 🔇 整个丢 `format`、回显 `{type:"text"}`——省略救不了这一档，其余上游两种写法都执行）【实测 2026-09-24】。
- ④ 官方 schema 限制：`additionalProperties:false` 必须；不支持 `minimum`／`maximum`／`multipleOf`／`minLength`／`maxLength`／`pattern`；`minItems` 只收 0／1；不支持递归与外部 `$ref`；`oneOf` 写成 `anyOf`。经网关发非法关键字都 200——官方拒绝报文至今无样本 ⚠。支持表从 Claude 4.5 起；与 adaptive／`budget_tokens` 思考同用 thinking block 在前 JSON 在后；与工具、强制 `tool_choice` 同用不冲突；流式走普通 `text_delta`【实测 2026-09-26】。④ 只有 `json_schema`／`off` 两档，没有 `json_object` 中间档。
- 默认不用 `json_schema`（DeepSeek 不支持、千问只最新两三代商业款；智谱 `json_schema` 🔇 200 无视）；按模型 id 表抬升。验证只能用「schema 与 prompt 冲突」的用例（enum 锁死 `7`、只有 red／green／blue 却要 `yellow`），能解析不证明 schema 生效。
- ② `text.verbosity: low／medium／high`（L3 模型字段，GPT-5.x 生效）与 `text.format` 合并成 `{"text":{"format":{…},"verbosity":"low"}}`，放在 extraBody **之后**；① 顶层 `verbosity` 四上游都无效。千问 Responses 面文档无 `text` 字段（报错还是忽略未验 ⚠）。
- 结构化任务两级链：首选强制 pseudo-tool（schema 即 `parameters`）→ 失败退回 JSON mode + cue；回退判定正则要求能力词与「不支持」措辞同现。

详见：04 §1、§2、§3、§5.1、§5.2。

### 3.9 工具定义与 tool_choice

内部统一形状（【实现】05 §1）：

```jsonc
{ "type": "function", "function": { "name": "…", "description": "…", "parameters": { /* JSON Schema */ } } }
```

| 维度 | ① | ② | ③ | ④ |
| --- | --- | --- | --- | --- |
| 定义 | 同上（嵌套） | `{ type:"function", name, description, parameters, strict: false }`（去 `function` 包装；**`strict:false` 显式**，省略 → 官方自动升 strict → 可选字段 schema 变「全必填否则 400」） | `{"tools":[{"functionDeclarations":[{name, description, parameters}]}]}` | `{ name, description, input_schema }` |
| `auto` | `"auto"` | `"auto"` | `mode:"AUTO"` | `{type:"auto"}` |
| `none` | `"none"` | `"none"` | `mode:"NONE"` | `{type:"none"}` |
| required | `"required"` | `"required"` | `toolConfig.functionCallingConfig.mode:"ANY"` | `{type:"any"}` |
| 具名 | `{type:"function", function:{name}}` | `{type:"function", name}` | `mode:"ANY"` + `allowedFunctionNames:[name]` | `{type:"tool", name}` |
| 发送条件 | — | 只在声明了函数工具时发；不做「思考中禁止强制」预判 | — | **只在声明了本地工具时才发**（只有 server tools 时发 `{type:"auto"}` = 对端点内部决策发表意见） |

- 砍档方言与降级：MiniMax `switch` 枚举只剩 `auto／none` → forced 无条件预判降 `auto`；千问【文档】思考开启时 `tool_choice` 只接受 `auto／none` → 只在本次真发 `enable_thinking:true` 时降；智谱文档「仅支持 `auto`」、实测 `required`／具名 200 不强制、4.7 具名思考开时 ❌ 400 `1210 API 调用参数有误`（不点名参数）→ 平台级降 `auto`；4.5-air `required` 真强制【实测 2026-09-19】；方舟强制时 200 但推理 token 0（🔇 跳过思考，不需降级）【实测 2026-09-18】。
- forced 被接受 ≠ 生效：Kiro 渠道 ① `required`／具名与 ④ `any`／`tool` 流式 🔇 无视、非流式生效；anti 两条路径都不实现；CC 带思考时好时坏；AWSb 全生效【实测 2026-09-23】；New API `[Azure]` ① 具名 ❌ 500（9/9）【实测 2026-09-24】。
- ④ `tool_use` 块多 `caller:{"type":"direct"}`（原样存；去掉回灌经网关也 200）。

详见：05 §1、§2；04 §4；02 §7.1。

### 3.10 流式工具参数拼接与配对

| 族 | 拼接方式 | 配对 | 畸形样本 |
| --- | --- | --- | --- |
| ① | 按 `delta.tool_calls[].index` 分片拼 `arguments` 字符串；**分组键必须是 index 不是 id，id 自身也可能分片**（`entry.id += partial.id`）；`parseJsonArgs` 全员 try/catch 兜 `{}` | `tool_call_id` | 参数背靠背多对象 `{}{"id":1}`（按括号深度切、左到右合并，坑 105）；调用 id 是空串 `""`（按缺失处理，否则下一轮重复 `tool_call_id` 400、整段会话此后每轮 400，坑 106）【实测 2026-08-08／08】 |
| ② | 按 `output_index` 分组（部分中继 delta 缺 `item_id`）；参数 delta + `function_call_arguments.done`／`output_item.done` 整串，以整串为准；只发一种的端点也要能拼出 | `call_id` | — |
| ③ | 整个 `functionCall` 一次到齐（已解析对象）；旧型号无 id → 适配器自造 `gtc_${Date.now()}_${n}`；3.8 Flash 起带 `id`（`call_1626125`），`functionResponse` 带不带 id 都收【实测 2026-09-26】 | 旧型号靠函数名（id→name 表回填）；同名并行调用对应关系不可表达 | 并行调用只第一个 `functionCall` part 带 `thoughtSignature`（正常，不补） |
| ④ | 按块索引拼 `input_json_delta.partial_json`；**空参数调用不流任何 delta，`""` → `"{}"`**；流式第一条 `input_json_delta` 是空串 | `tool_use_id`；一轮所有 `tool_result` 合成一条 user 一起到达 | — |

配对是硬要求且违约不自愈：一次缺失永远留在历史每轮重发；适配器层兜底（孤儿 tool 消息合并、name 兜底链）。

详见：05 §3、§4；02 §2、§3.2。

### 3.11 服务端工具 wire 形状

app 层一个 id（`web_search`／`web_extractor`／`code_interpreter`）一种意思，拼法按族收口。

| 工具 | Ⓓ ① compat（千问） | ② | ③ | ④ |
| --- | --- | --- | --- | --- |
| web_search | 顶层 `enable_search: true`；`search_options:{search_strategy:"agent_max"}`（与 `tools` 同发 ❌ 400 `Agent mode does not support tools…`）；**无痕**：不返回来源、无角标、无 `ServerToolEvent`（坑 10） | `tools:[{type:"web_search"}]`（OpenAI／xAI；火山 ② 文档要 `sources:["doubao"]`）；事件 `web_search_call`：`action.type:"search"` → `action.queries[]`／`action.query`；`action.sources` 需 `include:["web_search_call.action.sources"]`；`open_page`／`find_in_page` → `{url}`+`pattern`；`url_citation` 注解 | `{googleSearch:{}}`；末块 `groundingMetadata{webSearchQueries[], groundingChunks[{web:{uri,title,domain}}], searchEntryPoint, groundingSupports}`（`uri` 是 `vertexaisearch` 跳转、`title` 是域名）；「搜没搜」只认 `webSearchQueries` | `{type:"web_search_20250305", name:"web_search", max_uses:10}`（不需要 beta 头）；`server_tool_use` → `web_search_tool_result`（10 条各带 `encrypted_content`）→ 带 `citations`（`web_search_result_location`）的 text；配对 `server_tool_use.id` ↔ `tool_use_id` |
| fetch／extractor | `search_options` agent 模式 | 千问 `{type:"web_extractor"}`（仅当 `web_search` 同在；单独 → 200 后 `response.failed`）：`web_extractor_call` `urls[]`+`goal` → `output` | `{urlContext:{}}`；首块 `urlContextMetadata.urlMetadata[{retrievedUrl, urlRetrievalStatus}]`；末块 `groundingChunks` 真实 uri，**无 `webSearchQueries`** | `web_fetch_20250910` |
| code | 顶层 `enable_code_interpreter: true`（非流式 ❌ 400 `Non-streaming mode does not support Code interpreter.`；带函数工具 400；无痕） | `{type:"code_interpreter"}`（千问名；OpenAI 同名要 `container`）：`output_item.added` 带完整 `code` → `response.code_interpreter_call.{in_progress,interpreting,completed}` → done 补 `outputs:[{type:"logs",logs}]`；思考关闭 → 200 后 `response.failed` `Normal mode does not support Code interpreter. Please set enable_thinking to true.` | `{codeExecution:{}}`；独立块 `executableCode{language, code, id}`（带签名）→ `codeExecutionResult{outcome:"OUTCOME_OK", output, id}`；代码 part 随 model 轮原样回灌 200 | `code_execution_20250825` |
| 其他 | `web_search_image`／`image_search` 猜的字段 🔇 忽略 | `{type:"web_search_image"}`／`{type:"image_search"}`（`arguments` 与 `output` 都是 JSON 字符串，`"[]"` = 没搜到）；`{type:"file_search"}`；`{type:"image_generation"}`（base64） | — | — |
| 刹车 | 无 `max_uses` 等价物（按次价低三个数量级） | 无 | 无 `max_uses` 等价物 | **`max_uses` 是唯一刹车**（官方 $10/1000 次 + 结果按 input token；一题 8 次搜索）；即使中继文档没列也照发 |
| 计数 | — | OpenAI `tool_usage.web_search.num_requests`；xAI `server_side_tool_usage_details`；千问 `usage.x_tools.code_interpreter.count`；火山 `usage.tool_usage_details.web_search.doubao` | `googleSearch` 按查询条数约 $0.014/条；`toolUsePromptTokenCount` | `usage.server_tool_use.{web_search_requests, web_fetch_requests}` |

④ 与 ③ 的原文片段：

```json
{ "type": "web_search_20250305", "name": "web_search", "max_uses": 10 }
```

```json
"tools": [
  { "functionDeclarations": [ … ] },
  { "googleSearch": {} }, { "urlContext": {} }, { "codeExecution": {} }
]
```

- 三原则：声明而非注册、无可执行（不给 `server_tool_use` 回 tool_result）、只读上报。收窄方向两族相反：④ 不收窄到 compat（官方真有）；① `enable_search` 只放行 compat（api.openai.com 对未知顶层参数 400）。
- 响应流防御读取：④ `server_tool_use` query 按 `input_json_delta` 分片或 start 块整给，两种都收；`web_search_tool_result.content` 正常是数组、出错是单个 error 对象，认不出 = 零结果不抛异常。事件 id 在整份日志唯一（请求级前缀 + 内容键；坑 192、193）。
- 平台差异（服务端工具是「平台 × 面 × 渠道 × 模型」属性，不从模型 id 推）：New API Kiro ④ `web_search` 单挂 🔀 劫持（第一条 user 原文当搜索词、模板回复、`output_tokens` 固定 644/568/478）、+ 函数工具流式 ✅ 真搜、非流式丢；`web_fetch`／`code_execution` 200 🔇 丢且模型假装执行；CC 单挂 ✅；anti 全部 🔇 丢；AWSb 全部 ❌ 400 `Input tag 'web_search_20250305' … does not match`（整条请求失败）【实测 2026-09-23】。GPT 四上游：账号池 `web_search` ✅、`[Azure]` 🔇 丢（模型答「I can't perform a live web search」）、`code_interpreter`／`file_search` 各 `response.failed`／502／400 `Unsupported tool type`／500、`image_generation` 403 或 `[Azure]` ✅【实测 2026-09-24】；① `web_search_options` 四上游全 🔇 忽略。火山 ① 面无服务端搜索；智谱 ① 对话内 `{type:"web_search", web_search:{enable:true, search_engine, search_intent?…}}` 结果在响应顶层 `web_search[]`，默认意图识别不搜却答「根据联网搜索结果……」→ 必须 `search_intent:false`【实测 2026-09-19】。

详见：05 §5；06 §1。

### 3.12 服务端工具续跑

| 信号 | 谁 | 续跑方式 |
| --- | --- | --- |
| `stop_reason: "pause_turn"` | 官方 ④ | **verbatim**：整组 content block 原样作为 assistant 消息追加回去（`encrypted_content` 一字不改；重建块 = 400） |
| 停在 `*_tool_result` 块上、报 `end_turn` | 某些兼容端点（MiniMax，【实测 2026-08】） | **transcript**：搜索结果渲染成纯文本，以「assistant 开场白 + user 结果文本」两条普通消息送回（交替律所致；空 assistant 消息也 400，需兜底文案） |

- MiniMax **拒收自己发出的块**：❌ 400 `invalid params, tool result's tool id(...) not found`（响应侧实现了、请求侧没抄）——协议规定的续跑方式恰是它唯一不收的形状。
- 判据 `spokeSinceSearch` 是文本流事实而非块记录；`MAX_PAUSE_CONTINUATIONS = 4`（触顶不是错误）；usage 跨腿求和；transcript 单条 600／整份 12,000 字符双层闸；无结果不续跑。
- ① ② ③ 的续跑信号来源未写。

详见：05 §6。

### 3.13 工具按需加载

| 维度 | 原生 | 延迟标记／搜索工具 | 应用自己插入定义 | 回传义务 |
| --- | --- | --- | --- | --- |
| ② OpenAI | ✅ GPT-5.4+【文档 2026-09】 | `defer_loading: true`；`{type:"tool_search", execution:"server"／"client"}`；`{type:"namespace", …}` | ✅ `{type:"additional_tools", role:"developer", tools}` 条目，不经模型 | 下一轮 `input` **必须**带 `tool_search_output`（及 `additional_tools`），否则加载过的工具 🔇 静默消失 |
| ② xAI | ⚠ 规格有，**实测 403**（仅 alpha 用户） | 同 OpenAI 形 | 未见 | 未写 |
| ③ | ❌ | 请求带 `defer_loading` 整个被拒（第三方报告 ⚠） | — | — |
| ④ | ✅ Claude 4.5+ | `defer_loading`；`tool_search_tool_regex_*`／`_bm25_*`；`tool_result` 里可回 `tool_reference`；至少一个非延迟工具否则 400；与 `cache_control` 同现 400 | ❌（需经一次 tool_result） | 历史保留 `tool_search_tool_result` 块即可 |
| ① | ❌ | — | — | — |

原生实现工具表前缀不动、缓存不破；自改 `tools` 从工具表那截起前缀缓存全作废。形状「未全部实测」（只有 xAI 403 是实测）⚠。

详见：05 §7。

### 3.14 usage 与缓存

内部口径：`inputTokens` 总输入 ／ `outputTokens` 总输出**含思考** ／ `cachedTokens` 是 input 子集；计费 `(input − cached) × 全价 + cached × 缓存价`。

| 族 | input | output | 缓存 | 思考 | 其他键 |
| --- | --- | --- | --- | --- | --- |
| ① | `usage.prompt_tokens` | `usage.completion_tokens`（已含思考） | `prompt_tokens_details.cached_tokens`（子集）；DeepSeek 顶层 `prompt_cache_hit_tokens`／`prompt_cache_miss_tokens`，无标准键，`prompt_tokens` 已含命中（只读标准拼写 = 每次命中按全价记【文档；2026-09-14 修复】） | `completion_tokens_details.reasoning_tokens`（末块 `choices:[]`；GLM 4.5-air 从不给、glm-5／4.6／4.5 关思考时缺席） | OrcaRouter／OpenRouter 形态 ① 末块 `usage.cost`（`cost_usd ?? cost`） |
| ② | `usage.input_tokens` | `usage.output_tokens` | `input_tokens_details.cached_tokens`（子集）；`input_tokens_details.cache_write_tokens`（OpenAI 原样线路也有，一次 `web_search` 4,388） | `output_tokens_details.reasoning_tokens` | `usage.attribution.request_fields.instructions.input_tokens`（账号池上游读注入量）、`attribution.items`；OrcaRouter ② 默认线路 `usage.cost`、原样线路无 |
| ③ | `usageMetadata.promptTokenCount` **+ `toolUsePromptTokenCount`**（在 prompt 之外；实测 20+65+77=162） | `candidatesTokenCount` **+ `thoughtsTokenCount`**（思考不在 candidates 里） | `cachedContentTokenCount`（子集） | `thoughtsTokenCount` | `trafficType:"ON_DEMAND"`（Vertex 专有）；OrcaRouter 末块 `usageMetadata.costUsd`（需 `X-OrcaRouter-Include-Cost: true`） |
| ④ | `input_tokens` + `cache_read_input_tokens` + `cache_creation_input_tokens`（**三桶不重叠**；直接读 `input_tokens` 少报一个数量级） | `output_tokens` | 两个 cache 桶；cache write 计价高于基础价归全价桶（宁可高估）；`message_delta` 里的 `cache_creation:{ephemeral_5m_input_tokens}`（中转估算形） | `output_tokens_details.thinking_tokens`（子集；Sonnet 5：22 = 21+1） | `usage.server_tool_use.{web_search_requests, web_fetch_requests}`；OrcaRouter `message_delta.usage.cost_usd`（需同一请求头） |

② 账号池上游的 usage 样本（【实测 2026-09-24】06 §1）：

```jsonc
"usage": {
  "input_tokens": 4389,
  "input_tokens_details": { "cached_tokens": 0, "cache_write_tokens": 0 },
  "attribution": {
    "items": { "<item id>": {…} },                          // 按输出条目计
    "request_fields": { "instructions": { "input_tokens": 4380 } }  // 作者没发 instructions，却记了 4,380
  }
}
```

- ④ 没发 `cache_control` 也有 `cache_creation_input_tokens`（`web_search` 结果服务端自动写缓存，一次 2,834；Sonnet 5 PDF 请求 1,630）——`cache_creation` 不能当「我方打了断点」判据。手打断点：9,848 token system 首次写 $0.0247（1.25× 输入价）、第二次读 $0.0020。
- 中转站估算的 usage：总数可用、缓存分段不可信（Kiro `cache_control` 只写不读：同一 7.4k 前缀连发两次都报 `cache_creation_input_tokens:7360`；同一请求流式 `prompt_tokens` 301、非流式 102）；anti 渠道没有任何缓存字段。
- 上游报价：④ `cost_usd` ／ ③ `costUsd` ／ ① `cost_usd ?? cost` ／ ② `cost` 换算只写一处；信任声明在平台上；「没报」≠ 0（NULL）。

详见：06 §1；02 §1；03 §3.1。

### 3.15 错误信封与 200 里的失败

| 族 | 错误信封 | 200 里的失败 |
| --- | --- | --- |
| ① | HTTP 4xx + body 文案（DeepSeek 422 `unknown variant video_url…`、xAI 400 `Empty content block`、千问 400 `Invalid video file`）；智谱 `{"error":{"code":"1210","message":"…"}}`（业务码字符串，HTTP 状态另给；错 key 401 `{"code":"401","message":"令牌已过期或验证不正确"}`；「该模型始终思考，不支持关闭思考」覆盖 5.3 代所有非法思考参数、「API 调用参数有误，请检查文档」不点名参数）；MiniMax `base_resp.status_code`（1004 鉴权失败／1008 余额不足／1002 限流，0 成功）；SSE 体内 `data: {"error":…}`（OpenRouter routinely）；方舟 `400 InvalidParameter`、`404 UnsupportedModel`；402 `{"error":{"code":"insufficient_user_quota",…}}` 先于模型解析（坑 112） | `finish_reason: content_filter`（Azure 及网关，几乎不带文本，必须 throw）；智谱 `sensitive`（同义）、`network_error`（流式中途失败不回错误码）、`model_context_window_exceeded`（按 `length` 截断）【文档 2026-09】；🔇 静默丢弃（PDF／URL 图片／视频）；空 `content` + `stop` 与坏中转无法区分；只认 `error` 会把过期密钥读成正常空回复 |
| ② | `response.failed`／`error` 事件／data 行裸 `{error}`（无 `type`）；`response.incomplete.incomplete_details.reason`；乱写 effort 按上游：`[Pro]` 400 官方原文 `Invalid value: 'bogus'. Supported values are: 'none', 'minimal', …`、`[Plus]` 502 `Upstream request failed`、`[特价Pro]` 200 + `response.failed`（`upstream_error`）、网关 500 `Upstream gateway error`；503 `No available channel for model … under group …` = 该档没线路 | 流里 `response.failed`（千问单独 `web_extractor`、思考关时 `code_interpreter`）必须当失败；流里 `error` 事件后接空答；🔀 回显改写（`temperature:0.5` 回显 `1.0`、`effort:"none"` 回显 `medium`）；`max_output_tokens` 被无视回显抓不到（坑 65）；`status:"completed"` 的空 message 条目是**正常结束**（坑 109） |
| ③ | 400 原文（Vertex）`Thinking level MINIMAL is not supported for this model.`、`Function call is missing a thought_signature in functionCall parts`、`required oneof field 'data' must have one initialized field`；OrcaRouter 改写成 `{"error":{"message","type":"invalid_argument","param":"","code":400}}`，路径与 URL 打成 `***` | 请求级 `promptFeedback.blockReason`；响应级 `finishReason ∈ {SAFETY, PROHIBITED_CONTENT, BLOCKLIST, RECITATION, SPII, IMAGE_SAFETY}`（可在半截文本后到）；`GEMINI_REQUEST_FAULTS`：`MISSING_THOUGHT_SIGNATURE`（我方丢签名，措辞要区分）、`UNEXPECTED_TOOL_CALL`、`TOO_MANY_TOOL_CALLS`、`MALFORMED_RESPONSE`；不认识的 finishReason 不能读成正常短回复；New API Gemini 面 snake_case 🔇 丢图与系统提示 |
| ④ | 400 带原文：``Invalid `signature` in `thinking` block``、`requires adaptive thinking; omit thinking or use thinking.type=adaptive and output_config.effort`、`Invalid signature in thinking block`（AWSb）、`Input tag 'web_search_20250305' … does not match`（AWSb）、`URL sources are not supported`（AWSb）；官方 `error.type`（`invalid_request_error` 等）；OrcaRouter 改写成 `{"error":{"type":"<nil>","message":"***.***.content.0: … (request id: …)"},"type":"error"}`（**`type` 是 Go 空值 `<nil>`**，New API 系指纹）；上游 5xx 改成 `api_error` + `The upstream provider is temporarily unavailable`；文档说的 `claude_error` 一次没出现；官方 `output_config.format` 拒绝报文无样本 ⚠；第三方 ④ 兼容层【实测 2026-09-28】：DeepSeek 422 ``Failed to deserialize the JSON body into the target type: thinking.type: unknown variant `bogus`, expected one of `adaptive`, `enabled`, `disabled` at line 1 column 142``、智谱 `[1210][该模型始终思考，不支持关闭思考；请使用 low、high 或 max。][<request id>]`、MiniMax `invalid params, param 'top_p' should be in (0,1] (2013)`、百炼 `Request body format invalid` 与透传的 `<400> InternalError.Algo.InvalidParameter: The value of the enable_thinking parameter is restricted to True.`（点名 ① 的字段名，坑 219）；MiniMax／DeepSeek 未知模型名不报错、静默改映射（坑 221；06 §2） | `stop_reason:"refusal"`（必须 throw）；丢 thinking 块 🔇 静默关思考；翻译层中转 🔇 丢 PDF／URL 图片、无视 `display`、`max_tokens` 被无视且 `stop_reason` 永远不是 `max_tokens`（Kiro）；服务端工具 🔀 劫持（Kiro）／🔇 丢且假装执行；反代对乱写 effort 一律 200 |

- 四种「看起来成功」的失败都处理：SSE 内 `data:{"error"}`、`base_resp.status_code`、内容拦截（throw 作废已流出文本）、请求缺陷（`GEMINI_REQUEST_FAULTS`）；「200 且没有任何内容」当可疑。
- 错误分类只靠 HTTP 状态 + 报文关键字，不靠 `error.type`／`param`／字段路径（`***`、`<nil>`）；按文案做降级前先看该家文案是否点名参数；「按 400 学降级」正则不匹配 502／500／流内 `response.failed`；只有正向渠道（AWSb／官方）会响，反代静默。
- 探测：① `GET /models` → `{data:[{id}]}`；② `GET /v1/models` 的 `supported_endpoint_types` 只是建议（New API 声明 `anthropic`／`gemini` 却拒、OrcaRouter 只声明 `openai` 却 200）；③ `GET /models` → `{models:[{name:"models/x", displayName}]}`，per-model 端点给 `inputTokenLimit`／`outputTokenLimit`，`:countTokens` 在 OrcaRouter 是一次计费的 `generateContent`；④ `GET /models` → `{data:[{id, display_name}]}`，per-model 给 `max_input_tokens`／`max_tokens`，火山套餐 ④ `/v1/models` 对有效 key 401（坑 136）。

详见：06 §2、§5；02 §1、§7.2；03 §5。

### 3.16 未知字段、max tokens、温度

| 维度 | ① | ② | ③ | ④ |
| --- | --- | --- | --- | --- |
| 未知顶层字段 | 官方端点直接拒绝（`enable_search`、`enable_thinking` 等 400）；方舟 🔇 忽略 `enable_thinking:false`（坑 114）；智谱一律放过；DashScope 私有键只放行 compat | 官方与 xAI 忽略；仍按最小公倍数发送 | 官方口径来源未写；New API Gemini 面无视未知键（snake_case 🔇） | 官方**未知键 400**；反代（Kiro／CC／anti）与重新序列化网关（OrcaRouter）对 `output_config.effort:"bogus"` 200；第三方 ④ 兼容层（DeepSeek／百炼／智谱／MiniMax）顶层未知字段与 ① 的 `reasoning_effort` 都 200 放过，`thinking.type:"bogus"` 四家四种（MiniMax 🔇 200 且开思考；DeepSeek ❌ 422；智谱 ❌ 1210；百炼 ❌ 400 `Request body format invalid`）【实测 2026-09-28】（03 §3.5） |
| max tokens | `max_tokens` → `max_completion_tokens`（选填；被拒自动换拼写重试一次）；errorProbe 发 `max_tokens=10,000,000` 读 4xx body 里的真实上限；智谱 `max_tokens参数非法：限制数值范围[1,98304]` | `max_output_tokens`；账号池上游 🔇 无视（设 16 照样写完、`status:completed`）；网关执行 | `generationConfig.maxOutputTokens`（选填） | `max_tokens` **必填、无服务端默认**；`budget_tokens` 必须 < `max_tokens`（官方 ≥ 时 400，中转四渠道与方舟 200）；Kiro 渠道 `max_tokens` 🔇 被无视 |
| 温度与思考 | 来源未写族级约束；方舟 ① 面 `0／0.1／0.3` 都收敛（17–19/20）、`1` 分散（9/20）；MiniMax-M3 ① 面总在想、看不出温度 | 账号池 `temperature:0.5` 🔀 回显 `1.0`；网关 ❌ 500（`temperature:1` 则 200）→ 该上游 ② `temperature` 判「不发」 | 来源未写 | 📄 官方思考开着只收 `temperature:1`（别的 400）→ **在想就不发温度**（对 adaptive／extended 恒成立，关了也在想）；`switch` 类目关思考时：方舟 ④ 听但 `0` 等于没发（`0.01` 收敛 19/20），MiniMax ④ 收下不理会；两家开思考 + `0.3` 都 200 不收敛（官方 400 在此不响）【实测 2026-09-28】；智谱 `temperature参数非法：限制数值范围[0,1]` |

- 温度事实挂在思考类目上（`minimax`／`doubao-switch`，只有后者声明 `temperatureWhenOff:{zeroIsUnset:true}`），不写成平台格；`0` 只加说明不改写成极小正数。
- ② `store:true`：账号池 200、网关 ❌ 500。

详见：03 §2、§3.4；02 §7.1；06 §2、§5、§6、§8。

---

## 4. 非对话协议的骨架

只写协议级：route 与线格式的骨架；逐模型的尺寸、参考图张数、价目留给 23 篇。

### 4.1 出图 route：请求／响应统一化要点

route 按端点分发、不按供应商（同供应商同协议按模型走不同端点，无法从 ApiStandard 推导）；出图入口是流式入口的兄弟：独立函数 `出图(连接, 请求) -> 结果`，`images` 非空即编辑。

| route | 请求骨架 | 编辑的表达 | 同步／异步／流式 | 响应位置 | URL 有效期 | usage／计费口径 | 错误报法 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| images-api | `POST /images/generations` JSON；`sizes` 声明为空 = 不带 `size`；回显 `size`／`quality` 是定了的规格 | `POST /images/edits` **multipart**：1 张 `image`、多张 `image[]`；每个 part 显式 `Content-Type`；**绝不手动设整体 `Content-Type`**（boundary 由运行时生成）；`mask` 仅此 route | 同步，一个 JSON body | `data[].b64_json`／`data[].url`；`b64_json` 不带 mime → magic bytes 嗅探；dall-e-3 逐项 `revised_prompt` | — | `input_tokens`／`output_tokens`（不是 chat 的 `prompt_/completion_`）；`input_tokens_details.image_tokens`；输入图 $8/M vs 文本 $5/M | `Unsupported parameter: 'x' is not supported with this model.` 带 `param:"x"`；中继对默认 `octet-stream` part ❌ 400【实测 2026-09-05】；中继 200 + HTML 错误页／200 + `{"error"}` 零张图要抛错 | 【实测 2026-09-05】【实现／文档】 | 13 §2、§4.2、§6 | — |
| chat（chat-image） | `POST /chat/completions` 多模态 user 消息；出图模型纯文本也发单元素 part 数组（字符串 `content` ❌ 400 `images[0] must be an http/https URL or image data URI`）；New API Gemini 出图参数只认 `extra_body.google.image_config`（snake_case） | 多模态消息附图 | 同步 | 中继各放各的全都要接：`content` 里 `![image](data:…)`／`![image](https://…)`；`message.images[].image_url.url`／`images[].b64_json`／`images[].url`；`message.image_b64_json`；整条回复是裸链接或裸 base64 | — | 按 chat usage | 宽高比发错位置 🔇 静默无效；走 ③ 原生形状中继不补 `responseModalities` 老模型只回文本；对象存储型中继给 https 链接只认 data URI 就零张图 | 【实测 2026-09-05】【实现】 | 13 §2、§4.2、§6 | 110 |
| gemini | `POST /models/{id}:generateContent` + `responseModalities:["TEXT","IMAGE"]` | 输入图就是额外 parts | 同步 | `candidates[].content.parts[].inlineData`；可附 text part | — | 输入图在 `input_tokens`（`input_tokens_details.image_tokens`） | — | 【实现】 | 13 §2、§7 | — |
| imagen | `POST /models/{id}:predict` | **无编辑**——用户附参考图要显式警告 | 同步 | `predictions[].bytesBase64Encoded`；**无 usage** | — | 按次；元数据至少放张数否则统计里整条消失 | — | 【实现】 | 13 §2、§4.2、§7 | — |
| dashscope 同步 | `POST {原生base}/services/aigc/multimodal-generation/generation`；body 顶层只有 `model`、`input`；`input.messages[].content` = `{image}`／`{text}` part 数组；旋钮全在 `parameters`（`n`、`size`、`negative_prompt`、`seed`、`watermark`、`prompt_extend`…），`extraBody` 并进 `parameters`；尺寸 `宽*高`（发前把 `1024x1024` 归一）、**永远显式发** | image part 收公网 URL 或 data URL；qwen 图在前文在后，wan 文在前图在后 | 仅同步（qwen 全系）；wan2.7 both；`asyncTask` 三态声明 | `output.choices[].message.content[].{image}`（qwen 只有 `image` 键，wan 多 `type:"image"`） | **24 小时**，拿到立刻下载 | qwen 按面积 `qima_output_1k`／`_2k`；wan 按张，usage 回显 `size` | 顶层 `{code, message}`（不是 `{error:{…}}`；任务失败嵌在 `output`）；`Throttling`／429 限流；HTTP 200 带 `code` = body 里送达的错误；`messages` 放顶层 ❌ 400 `InvalidParameter: Field required: input.messages`；qwen-image-3.0 收 `"1K"` ❌ 400 `Expected format: '<width>*<height>'` | 【实测 2026-09-19】【外部实测 2026-09-04】【文档 2026-08／09】 | 13 §3、§4 | 101、102 |
| dashscope 异步 | `POST /services/aigc/image-generation/generation` + 头 `X-DashScope-Async: enable`（路径不同、body 一致）→ `output.task_id` | 同同步 | 异步；`task_status: PENDING／RUNNING → SUCCEEDED／FAILED／CANCELED／UNKNOWN`（过期也 UNKNOWN）；轮询 ~3 s 起步十来次后 5 s，总 deadline 600 s | `GET /tasks/{id}` → `output.results[].url` | `task_id` 与结果 URL 均 24h | 同同步 | 打错路径报路径级 4xx；FAILED／CANCELED 嵌在 HTTP 200 的 `output` 里 | 【文档 2026-08】 | 13 §3、§4 异步任务流 | — |
| ark | `POST {base}/images/generations`；`model`／`prompt`／`size`／`response_format` 同名同义；**无 `n`／`quality`**；`watermark` 默认 true → 永远明发；档位（`1K`…`4K`）或 `WxH` 不可混用，`WxH` 约束总像素 | JSON `image` 字段（URL 或 `data:image/<fmt>;base64,…`，`<fmt>` 必须小写；单张或数组）；组图 `sequential_image_generation:"auto"` + `…_options.max_images`（默认 15）；参考图数 + 生成数 ≤ 15；选区写 prompt `<bbox>x1 y1 x2 y2</bbox>` | 仅同步（`stream:true` 例外：5.0 lite／4.5／4.0）；等全部图画完才返回；超时按张数放宽（5 分钟起每张 +40 s 封顶 15 分钟） | `data[]` 每项 `url` 或 `b64_json` + `size`；组图单项失败只有 `error{code,message}`；顶层 `error` 只在一张都没画出时；回显 `model` 非流式去日期、流式是请求拼写 | **24 小时** | `usage.generated_images`（账单口径）；`output_tokens` = Σ(宽×高)/256 仅供参考不进通用 token 键（坑 83）；`usage.input_images`；`usage.tool_usage.web_search` | OpenAI 形 `{"error":{"code","message","param","type"}}`；不支持参数出图前 400、`param` 点名「is not supported by the current model」；审核 code `InputTextSensitiveContentDetected`／`InputImageSensitiveContentDetected`／`OutputImageSensitiveContentDetected`；免费探测：非法 `size`（`"1x1"`）→ 支持的模型 `400 InvalidParameter`、不支持 `404 UnsupportedModel`；校验顺序不固定 | 【文档 2026-09-18／22】【实测 2026-09-18、2026-09-23】 | 13 §4.1 | 83、127、130 |
| ark 流式 | `stream:true`；SSE `event:` 与 `data.type` 同名：`image_generation.partial_succeeded`（`image_index` 从 0、`url`、`size`）／`partial_failed`（带 `error`）／`image_generation.completed`（`usage`）／`data: [DONE]`；响应头等第一张画完才回（≈27 s） | — | 流式 | 每张一个 `partial_succeeded`；`usage` 只在 `completed` | 24 小时 | 按已送达张数记账；每个图片块带 `input_image_count`／`reported_cost_usd`（坑 127） | 参数校验失败不走 SSE：照样 `400 application/json`；200 时 SSE 还是 JSON 看 body 首行 | 【实测 2026-09-18 5.0 lite】 | 13 §4.1 流式出图 | 127 |
| xai-images | `/images/generations`；`aspect_ratio` 收 `auto`；`resolution: 1k／1.5k／2k`（`size` 字段 ❌ 400）；`quality: low／medium／high／auto`（**不带 = medium**）；`response_format:"b64_json"`；`GET /v1/image-generation-models/{id}` 回 `image_price` + `pricing[{quality, resolution, price_per_image}]` | `/images/edits` **JSON**：1 张 `image:{url:<data URI>}`，2–3 张 `images:[{url}…]`（互斥），prompt 里 `<IMAGE_0>` 指代；文档参考图 3 张、实测 5 张 200 按 5 张收费（旧结论「最多 3 张」被推翻）【实测 2026-09-21】 | 同步 | OpenAI 形 `data[]`；`url`／`b64` 都空 = 被审核拦下 | — | `usage` 只有 `cost_in_usd_ticks`，**1 tick = $10⁻¹⁰**（400 000 000 = 1K·Low $0.04）；输入图 $0.01/张线性；报价含输入图、整单实扣、替换不叠加；回包没有输入张数 | `quality` 非枚举 ❌ 422 列枚举；2.0 发 `high` ❌ 400 `This model only supports the following quality value(s): low, medium, auto.`；初代 `1.5k` ❌ 400 `1.5K resolution is not supported for this model.`；初代 🔇 默默收下 `quality`（坑 125）；不带 `quality` 本地按表第一行 Low 估价低估三分之一（坑 123） | 【文档 2026-09】【实测 2026-09-21／22】 | 13 §4.2、§7 | 123、124、125 |
| minimax | `POST /v1/image_generation`；`aspect_ratio`（8 种）或 `width/height`（512–2048、8 的倍数，仅 image-01）；`n` 1–9；`aigc_watermark` 默认关 | **没有编辑**——只有 `subject_reference[{type:"character", image_file}]`；caps `edit:false` | 同步但慢（长任务） | `data.image_urls[]` + `base_resp`；逐图计数在 `metadata` | **24 小时** | 按次；不回 token，元数据至少放张数 | 两层：`base_resp.status_code≠0` 请求级（过期 key、余额、审核都 HTTP 200）；`status_code==0` 但 `metadata.success_count==0` 逐图失败；**`success_count`／`failed_count` 是字符串**（`"0"`／`"3"`） | 【实现／文档】 | 13 §2、§4.2、§7 | — |
| midjourney | `POST /mj/submit/imagine`；参数改写成 `--ar/--v/--s/--c/--q` 拼进 prompt（用户自己写的 flag 优先；`--v niji 6` → `--niji`） | `base64Array` 垫图（张数上限未写 ⚠） | 异步：submit → 轮询 3 s、总帽 10 分钟；每次进度推成一个文本 chunk | `GET /mj/task/{id}/fetch` → `{status, progress, imageUrl, failReason}`；提交回执 `code` 1 成功、22 排队中 | — | 按次；放弃永不重试 | task id 出现前不入日志 → 轮询死了无线索 | 【实现】 | 13 §2、§4.2 | — |

统一化要点（【实现】13 §5–§7）：
- URL 一律当场下载内联，一次重试；校验 content-type；mime 从 magic bytes 嗅探；识别 `url` 字段里的 `data:` 前缀。单交付物端点 200 但零张图 = 抛错；解析顺序：状态码 → 是否 JSON → 形状 → 错误信封。
- chat 出图：裸链接只对声明为出图模型下载；裸 base64 ≥64 字符且 magic bytes 是图片；同一张图可出现在 `content`、`images[0].b64_json`、`image_b64_json` 三处 → 按字节 SHA-256 去重。
- 编辑降级判定只认路由缺失（404／405／501）；结构化 code/param 只认指名模型的；`param:"x"` 丢字段即可修。
- 计费：per-image 与 token **相加**；上游直接报钱（`cost_in_usd_ticks`）**替换**不叠加；「没报」与「报了 0」分开（NULL vs 0）；计费相关默认值明发（xAI `quality`、wan `n`、ark `watermark`）；记账中性键 `input_image_count`／`reported_cost_usd` 是保留键（坑 126）。
- 尺寸校验器要能表达「面积区间」与「单边区间」两类规则，发前按目标模型校验，不合规换默认值而非转发吃 400。

详见：13 §2、§3、§4、§4.1、§4.2、§5、§6、§7。

### 4.2 视频 submit/poll 不变量

| 维度 | 千问 wan3.0 | MiniMax v2（H3） | xAI | OpenAI Sora | Google Veo |
| --- | --- | --- | --- | --- | --- |
| 提交 | `POST /api/v1/services/aigc/video-generation/video-synthesis` + `X-DashScope-Async: enable`；`input.prompt` + `input.media[]{type, url}`；`parameters`：`resolution`（480P／720P／1080P）、`ratio`、`duration`（2–30s，`-1` 智能）、**`audio` 默认 true**、`prompt_extend` 默认 true | `POST /v2/video_generation`；`content[]`（至少一个 text 项 ≤7000 字符；媒体项**嵌套** `{"type":"image_url","image_url":{"url":…},"role":"first_frame"}`）；**`resolution`（768P／2K）与 `duration`（4–15s）必填无默认**；创建响应只有 `{"task_id"}` | `POST /v1/videos/generations`（JSON）；回包只有 `{"request_id"}`；首帧 `image`、`reference_images`、`reference_audios` | `POST /v1/videos`（**multipart**） | `:predictLongRunning` |
| 轮询 | `GET /api/v1/tasks/{id}`（与图片任务、ASR filetrans 共用） | `GET /v2/query/video_generation/{id}` | `GET /v1/videos/{request_id}`；pending 是 **HTTP 202** + `{status, progress}`；done 200 | `GET /v1/videos/{id}` + `/content` | operations `GET` |
| 状态词表 | `PENDING／RUNNING／SUCCEEDED／FAILED／CANCELED／UNKNOWN` | `queued／running／succeeded／failed／cancelled` | `pending／done／expired／failed` | `queued／in_progress／completed／failed` | `{done: bool}` |
| 结果位置 | `output.video_url`（顶层扁平） | `task.content.url`（直链；v1 的 file_id→retrieve 二段式已废除） | `video.url`；`video.duration` 报实际秒数；`usage.cost_in_usd_ticks` 只在 done 回包 | `/content` 端点流式下载（API 端点，**要带**认证头） | operation response 内 URI |
| 失败位置 | `task_status: FAILED` 装在 HTTP 200，码在 `output.code/message` | `task.error` 在 HTTP 200 里；缺 resolution/duration → 400 | `video.url` 为空且 `respect_moderation: false` = 审核拦下；`expired` 是终态 | — | — |
| 保留期 | task_id **24h**；过期 = 查无此任务 | 任务记录 **7 天** | — | — | — |
| 取消 | 无端点 | `DELETE /v2/video_generation/{id}`，**仅 `queued` 可取消**（免扣费） | — | — | — |
| usage | 秒数／fps／分辨率无 token：`video_count`／`duration`／`fps`／`SR`／`ratio` | 秒数 + token 双口径（相加） | `cost_in_usd_ticks`（$0.080/s；首帧／参考图 $0.01/张线性） | ⚠ | ⚠ |
| 证据 | 【实测 2026-08-29】【文档 2026-08】 | 【实测 2026-08-29】 | 【实测 2026-09-22】 | 📄【文档】⚠ | 📄【文档】⚠ |

不变量（【实现】14 §1、§3）：
- submit 与 poll 两个入口分离，`task_id` 暴露给调用方持久化（提交与轮询隔分钟级可能跨进程）；轮询返回 `{done:false, status?}`（status 仅展示永不作分支）或 `{done:true, videoUrl}`；失败一律抛错不进返回值。
- 轮询面跳过通用错误信封检查，状态机自己报错并保留结构化 code（失败装在 HTTP 200 里）。
- 状态词表逐家归一化；未知状态当 in-progress 容忍但受总 deadline 罩；已知终态（CANCELED／expired／UNKNOWN）显式进抛错分支。
- 「任务已过期／查无此任务」是独立错误，不重试不报 FAILED。
- 结果 URL 当场下载；签名直链**不带** API 认证头，Sora `/content` **要带**；校验 content-type + magic bytes。
- 取消分两层：上游取消（MiniMax 仅 queued）失败静默降级为本地放弃；无取消端点的家 UI 别承诺「已取消」。
- 首帧／尾帧／参考素材统一 `media[].role`（`first_frame`／`last_frame`／`reference_image`／`reference_video`／`reference_audio`），adapter 转各家拼写。MiniMax 平铺 `"url"` 🔇 静默失败（解析器照收、任务成功、照样计费，当作没附图；坑 113）——「跑通」判据是出片遵守首尾帧，不是 HTTP 200。
- 同一模型 id 在官方与中继走不同协议（官方行 video 槽位 → 私有协议，中继行 → openai-videos），无 model-id 硬编码。
- 火山方舟 Seedance：套餐 base `/contents/generations/tasks` 四个 id 全 ❌ `404 UnsupportedModel`，协议形状本库未覆盖【实测 2026-09-18】。

详见：14 §1、§2、§3、§4。

### 4.3 ASR 三种线格式

| 维度 | ⓐ OpenAI 兼容转写 | ⓑ 百炼同步识别 | ⓒ 百炼录音文件转写（filetrans） |
| --- | --- | --- | --- |
| 端点 | `POST {base}/audio/transcriptions` | `POST {base}/services/aigc/multimodal-generation/generation`；头 `X-DashScope-SSE: disable` | `GET /uploads?action=getPolicy&model=…` → OSS 表单上传 → `POST /services/audio/asr/transcription`（`X-DashScope-Async: enable` + `X-DashScope-OssResourceResolve: enable`）→ `GET /tasks/{id}` → 下载结果 JSON |
| 音频怎么传 | multipart 字段 `file`、`model`、`response_format=verbose_json`、`timestamp_granularities[]=segment`、`language`（自动检测时不发）、`prompt` | base64 data URI 放 JSON：`input.messages[]` user `content:[{audio:"data:audio/wav;base64,…"}]`（qwen3-asr）或 `[{type:"input_audio", input_audio:{data}}]`（qwen-audio-3.0／fun-asr）；`parameters.result_format:"message"`、`asr_options:{language, enable_lid, enable_itn}` | 上传到临时 OSS 得 `oss://` 地址（**48 小时**）；提交 body `{model, input:{file_urls:["oss://…"]}, parameters:{channel_id:[0], enable_words:true, diarization_enabled:true, language_hints:["en"]}}`（qwen3 族 `input.file_url` 单数字符串、`parameters.language`）；**提交不幂等** |
| 单次上限 | OpenAI 25 MB【文档】 | 约 10 MB、3–5 分钟（文档两种说法）【文档】 | 凭证 `max_file_size_mb`；时长 12 小时【文档】 |
| 时间码来源 | `verbose_json` 给 `segments[].start/end`（**秒**，浮点，×1000 取整）；`gpt-4o-transcribe` 只有 `json`／`text` 不给 segments → 时间码来自切片；无 `segments` 时整段 `[0, duration]` | **无句级时间戳**，时间码只能来自「送去识别的那一片在哪」（静音切片，`fileStartMs = start − 200`）；词级 `output.sentence.words[]` 同步接口给不给未实测 ⚠ | 句级 + 词级（**毫秒**整数，相对整个文件）：`transcripts[0].sentences[]{begin_time, end_time, text, speaker_id, words:[{begin_time, end_time, text, punctuation, speaker_id}]}`；`enable_words:true` 才有词级 |
| 说话人 | 标准 whisper 无；`gpt-4o-transcribe-diarize` `response_format:"diarized_json"` 给 `segments[].speaker`【实现】 | 【文档】称支持、【实测 2026-09-13】`diarization_enabled:true` 🔇 静默忽略（200、有文本、无 `speaker_id`）；`qwen3-asr-flash` 不支持不要下发（文档与实测冲突，两个都记） | ✅ qwen-audio-3.0 族可用，一男一女英文标成 0／1，整文件编号一致【实测 2026-09-13】；`speaker_id` 可能是数字或数字字符串；qwen3-asr-flash-filetrans 不支持【文档】 |
| 成功／失败判据 | 401／403／404 致命；200 非 JSON 致命；429 按 Retry-After；5xx 同段 3 次后跳过 | 400 + `ASR_RESPONSE_HAVE_NO_WORDS` = 没人声 → **成功、空文本**；413 片段太大；其他 400／422（语种、审核 `DataInspectionFailed`）非致命跳过这段；404 `Model not exist` 致命；限流约 100 RPM，Retry-After 只认秒数 | `task_status ∈ PENDING／RUNNING／SUCCEEDED／FAILED／CANCELED／UNKNOWN`（与万相视频共用）；结果 `output.results[].transcription_url`；取凭证／上传 403 = 凭证过期重取；提交 400 多半 `oss://` 过期重传；轮询 404 = 任务不在重提交；下载 403／404 = 签名过期；下载 GET **不带鉴权头** |
| 代表 | OpenAI whisper-1、Groq、硅基流动、302.AI、智谱 glm-asr-2512（`error.code` 1302／1303／1214 是限流）、本地 WhisperX | `qwen3-asr-flash`、`qwen-audio-3.0-asr-flash`、`fun-asr-flash-*` | 模型名以 `-filetrans` 结尾 |
| 证据 | 【文档】【实现】（本库无实测） | 【实测 2026-09-13】 | 【实测 2026-09-13】（官方地址五步跑通；qwen3 族只按文档实现未实测） |

- 三种线格式 = 三个适配器；百炼 ⓑ／ⓒ 按模型名后缀分发（`endsWith('-filetrans')` → ⓒ），不按厂商。
- 选路：要说话人 → 只有 ⓒ；要准确时间码模型未指定 → ⓒ；用户点名同步模型又要时间码 → ⓑ + 静音切片并告知 ⓒ 替代；已用 OpenAI 兼容只要粗时间码 → ⓐ。
- 词级 → 字幕块：词时间 = `offset + begin_time`（ⓑ offset = fileStartMs；ⓒ offset = 0）；语言代码只取主标签（`zh-CN` → `zh`），自动检测整个字段不发。
- ⓒ 上传细节：字段顺序 `OSSAccessKeyId`、`policy`、`Signature`、`key`、`x-oss-object-acl`、`x-oss-forbid-overwrite`、`success_action_status=200`，**`file` 必须最后**；Dart `http` `MultipartRequest` 被 OSS 拒 `MalformedPOSTRequest`、手拼 multipart 成功（触发点未定位 ⚠）。
- ASR 错误分类按「哪一步」而不是按状态码（403 在识别步是鉴权致命，在 ⓒ 取凭证／上传／下载是过期回退一步）。
- 私有 SDK／HTTP 渠道（豆包 `X-Api-Status-Code == 20000000`、Gemini transcribe 词时间是带 `s` 后缀的字符串 `"1.23s"`、Deepgram `utterances[].start/end` 秒、ElevenLabs `words[]` 秒、CAMB 语言是整数 ID 查不到默认英语 🔇）证据等级仅【实现】，据此判错前先实测。

详见：16 §1、§3、§4、§5、§6、§7、§8、§9、§10.2。
