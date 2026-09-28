# 20 · 平台表（平台 × 面 × 地址鉴权 × 目录 × 手脚 × 计费）

本表回答：「这个平台（含渠道／线路／套餐变体）有哪些面、地址与鉴权怎么写、目录可不可信、它会对请求做什么手脚、计费与 usage 怎么报」。主键 = 平台（渠道 / 线路 / 套餐变体各占一行，写作「New API · Kiro 渠道」「OrcaRouter · ② 默认线路」「火山方舟 · 套餐」「智谱 · Coding Plan」）。本表是结论表，报文细节与原因在 0x／1x 篇里，用「详见」列的指针链接过去；坑号指 `11-pitfalls.md`。

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

「面」的编号：① OpenAI Chat Completions ／ ② OpenAI Responses ／ ③ Gemini generateContent ／ ④ Anthropic Messages ／ Ⓓ DashScope 私有 ／ 🖼 出图 ／ 🎬 视频 ／ 🎤 ASR。证据记法沿用原文：【实测 YYYY-MM-DD】【文档 YYYY-MM】【中继源码】【实现】；⏳待复核 = 日期距 2026-09-28 超过半年。

维护：新增 / 修正按 `30-knowledge-ingestion.md` 的流程；本表每行必须带证据与指针，没有证据的格子写 `—`。被推翻的旧结论在同一格里写「旧：… → 新：…（YYYY-MM-DD 推翻）」，不删。

## 目录

- [§1 平台类型速览](#1-平台类型速览)
- [§2 主表](#2-主表)
- [§3 各平台展开](#3-各平台展开)
  - [3.1 官方直连](#31-官方直连) · [3.2 云部署变体](#32-云部署变体) · [3.3 聚合网关 OrcaRouter / OpenRouter](#33-聚合网关) · [3.4 自建中转 New API 类](#34-自建中转-new-api-类) · [3.5 本地运行时与 ASR 专营](#35-本地运行时与-asr-专营)
- [§4 本表尚未覆盖的平台](#4-本表尚未覆盖的平台)

---

## 1 平台类型速览

| 类型 | 典型判据（怎么从回包认出它） | 通用对策 | 详见 |
| --- | --- | --- | --- |
| 官方直连（OpenAI／Anthropic／Gemini／xAI／DeepSeek／百炼／MiniMax／火山方舟／智谱） | 地址锁定或厂商 host；回包带官方专有字段：① `system_fingerprint`+`usage.*_details`、② `resp_…` id+`billing`／`tool_usage`、③ `responseId`／`modelVersion`、④ `msg_01…` id+长 base64 `signature`+`usage.cache_creation`；非法参数回官方原文 400；漏出上游响应头（`anthropic-ratelimit-*`、`openai-processing-ms`、`x-goog-*`） | official 契约：地址锁定、`/models` 缺失算错误、能力乐观；缺口会响，静默项是厂商自身特性（智谱 `json_schema` 无视、百炼 `enable_search` 无痕）按 15 篇索引逐篇核 | 01 §3、§9.5 透传证据清单；15 |
| 云部署变体（Azure OpenAI／Vertex／Bedrock） | 同 body 换鉴权与 URL；Vertex 回包带 `createTime`、`usageMetadata.trafficType:"ON_DEMAND"`；Bedrock 消息 id `msg_bdrk_`、任何 Anthropic 服务端工具 400、URL 图片 400；Azure `finish_reason:"content_filter"` 代替错误码 | 按官方族接，鉴权／URL 作 L2 数据；Bedrock Converse（camelCase、SigV4）是第五种 body，要么写第五个 adapter 要么明确不接；正向 ≠ 官方，服务端工具按平台点名；中转站里叫 `[Azure]` 的不等于 Azure OpenAI | 01 §2、§9.2 第 4 条；06 §2 |
| 聚合网关（OrcaRouter／OpenRouter） | 一把 key 四面同主机、模型 id 带厂商前缀、目录带 `supported_endpoint_types`；请求被重新序列化（非法枚举 200）；回包按面「原样」或「OpenRouter 形态」（`gen-…` id、`provider`、`native_finish_reason`、`usage.cost`／`is_byok`、`reasoning_details[]`）；402 `insufficient_user_quota` 先于模型解析；只有自有响应头 `x-orca-*` | 按面用透传证据判后端，原样的面记官方事实、「发 X 会不会 400」只记网关注记；花费字段按面各读各的，③④ 带 `X-OrcaRouter-Include-Cost: true`；不调计数端点；错误分类靠 HTTP 状态 + 关键字不靠 `error.type`；不按 `supported_endpoint_types` 开线路 | 01 §9.5；06 §1、§2、§5 |
| 自建中转（New API 类，按渠道） | 无可识别 host；渠道／档位写在模型 id 前缀 `[kiro]` `[CC量]` `[Plus]`；503 `No available channel for model … under group …`；错误信封 `type:"<nil>"`、路径 `***`；`usage.billing_usage.source`、`usage.attribution`；④ 发 `output_config.effort:"bogus"`（② 发 `reasoning.effort:"bogus"`）200 = 反代、400 官方原文 = 正向 | 能力主键是（平台, 面, 渠道, 模型）；同台至少测两个渠道分「转换层／渠道」；② 恒发 `instructions` + 终止事件回显比对；图片一律内联 base64；兼容 ④ 线路默认不发 `cache_control`；目录 `supported_endpoint_types` 不开线路；站主缩写不进代码、上游由作者声明 | 01 §9.2；06 §4.1、§5、§8 |
| 本地运行时（Ollama／LM Studio／llama.cpp） | URL 指向本机（`:11434`）；空 Bearer 被拒；超窗返回 200 不报错；`/api/show`／`/props`／`/models.max_context_length` 有免费元数据 | 无 key 时整个 `Authorization` 头省略；发送前 `contextSize` 估算拦截（`ContextSizeError`）；`num_ctx` 与 `model_info` 两键取小的；JSON cue 接在最后一条 user 末尾不另起消息 | 01 §6；02 §5–6；06 §6、§9.3 |

通用闸门（所有类型）：欠费中转对**任何**真实请求回完整协议形状的 402 JSON、先于模型名解析——探测任一步都报不可达，不报鉴权失败【实测 2026-09-05】（坑 112；06 §5）。

---

## 2 主表

列说明：面（逐个列出可用面，不可用的写 ❌ 并给状态码）｜base 与鉴权｜目录（`/models` 形态、可信度）｜对请求的手脚（重序列化 / 注入 / 改写 / 丢字段）｜计费与 usage 报法｜证据｜详见｜坑。一格超过约 120 字时只写结论，细节在 §3。

| 平台／变体 | 面 | base 与鉴权 | 目录 | 对请求的手脚 | 计费与 usage 报法 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI 官方 | ① ✅；② ✅（o1-pro／codex 系／computer-use 只有 ②，走 ① 失败）；③④Ⓓ —；🖼 Images API 📄；🎬 Sora 📄；🎤 `/audio/transcriptions` 📄 | `https://api.openai.com/v1`，`Authorization: Bearer`（无 key 整个头省略）；② adapter 自拼 `/responses`；① 未知顶层字段直接 400、② 忽略（02 §7.1）| `GET /models` → `{data:[{id}]}`；② 族目录同 ① | 无中转改写；② `text.format` 省略 `strict` 自动升 `strict:true`（回显 `true`）、工具定义省略 `strict` 也自动 strict；GPT-5.x 以空 `final_answer` 收尾；`json_object` 缺 "JSON" 报错／无限空白流 | ① `prompt_tokens`／`completion_tokens`／`prompt_tokens_details.cached_tokens`；② `input_tokens_details.cached_tokens`／`cache_write_tokens`；`tool_usage.web_search.num_requests` 按次；一次搜索 45.7K 输入、112 s 是经 New API（第十个样本）测得，官方直连未测 | 【文档】；【实测 2026-09 经中转】；web_search 实测日期未标 ⏳待复核 | 01 §3.1、§8.1；02 §7；04 §5；05 §5、§7；06 §1；15 OpenAI 行 | 14、64、68、71、109、116 |
| Anthropic 官方 | ④ ✅；①②③Ⓓ🖼🎬🎤 — | 地址锁定，根地址不带 `/v1`（与 OpenAI 相反）；`x-api-key`（官方只 default 模式）+ `anthropic-version`；`max_tokens` 必填无服务端默认；未知顶层字段 400（`extraBody` 故意不 spread） | `GET /models` → `{data:[{id, display_name}]}`；per-model 端点给 `max_input_tokens`／`max_tokens` | 无改写；不回传 thinking 块→思考静默消失；`display` 默认 omitted；`stop_reason:"refusal"` 必 throw；`pause_turn` 续跑；`output_config.format` 拒绝报文至今无样本；Opus 5.5／Fable 5.1 拒 `thinking: disabled` 400 | 三桶不重叠相加：`input_tokens`+`cache_read_input_tokens`+`cache_creation_input_tokens`；`output_tokens_details.thinking_tokens`；`server_tool_use.web_search_requests`；`web_search` $10/1000 次 | 【文档】；Claude 5 经 OrcaRouter【实测 2026-09-26】；思考回退【实测 2026-09-28】 | 01 §2、§6；02 §1、§2.1、§5；03 §2–5；04 §2；05 §5–6；06 §1；15 Anthropic 行 | 1、4、16、17、18、179–184 |
| Google Gemini 官方（AI Studio） | ③ ✅（同一 wire 也出图）；🖼 Imagen `:predict` 📄；🎬 Veo 📄；①②④Ⓓ🎤 — | 地址锁定；`x-goog-api-key`；Interactions 与 generateContent 同构 | `GET /models` → `{models:[{name:"models/x", displayName}]}`；per-model 给 `inputTokenLimit`／`outputTokenLimit`（探测可省） | 图片字段 snake_case／camelCase 两种都收；有旧型号 🔇 无视 `responseMimeType`；`defer_loading` 整个被拒（第三方报告 ⚠）；「关闭」只是 `LOW`；三层错误（`promptFeedback`／拦截类 `finishReason`／请求缺陷） | `promptTokenCount`+`candidatesTokenCount`+`thoughtsTokenCount`（思考不在 candidates）+`toolUsePromptTokenCount`（在 prompt 之外）；流式只末块带计数 | 【文档】；3.8 Flash 事实经 OrcaRouter（Vertex）【实测 2026-09-26】不照搬 AI Studio | 01 §8.1、§9.5；02 §2.2、§3.2；03 §2–5；05 §5；06 §1–2、§6；15 Gemini 行 | 2、7、18、69、191、195 |
| xAI (Grok) 官方 | ② ✅ 推荐；① 📄 Deprecated（legacy）；④ `/v1/messages` 📄 完全弃用；🖼 Grok Imagine 2.0／初代 ✅；🎬 Grok Imagine 1.5 ✅；③Ⓓ🎤 — | `https://api.x.ai/v1`，Bearer；预设 `apiStandard: "openai_responses_compat"` | ⚠ `/models` 形态原文未说 | 推理模型发 `frequency_penalty` 200 未报错（文档说报错）；`reasoning.effort` ❌ 拒 `none`（4.5／4.6）、全系拒 `max` 400；`tool_search`／`defer_loading` ❌ 403（仅 alpha）；图片总像素 <512 ❌ 400；① `video_url` ❌ 400 `Empty content block` | ② 流 `response.completed` 带 usage + `[DONE]`；`server_side_tool_usage_details` 按次；🖼 `usage.cost_in_usd_ticks`（1 tick = $10⁻¹⁰）报实扣；🎬 $0.08/s、首帧与参考图各 +$0.01/张、done 回包报 ticks | 【实测 2026-09】；出图／视频计费【实测 2026-09-22】；视频输入【实测 2026-09-28】；【文档】 | 01 §9.1；03 §7.1、§7.3；05 §5、§7；13 §4.2、§7；14 §2、§3 第 8 条；15 xAI 行 | 66、67、123–129、206 |
| DeepSeek 官方 | ① ✅；`video_url` ❌ 422 `unknown variant video_url`（deepseek-flash）；其余 — | —（来源未写 base／鉴权） | — | `reasoning_effort:"none"` 关不掉，要 `thinking:{type:"disabled"}`；思维链回传义务分场景，两个方向都 ❌ 400；不支持 `json_schema`；`json_object` 缺 "JSON" 报错 | 顶层 `prompt_cache_hit_tokens`／`prompt_cache_miss_tokens`，无 `prompt_tokens_details.cached_tokens`，`prompt_tokens` 已含命中（只读标准拼写 = 命中按全价记） | 【文档 2026-08】；视频输入【实测 2026-09-28】；缓存字段【Joycai 2026-09-14 修复】 | 02 §1 表后；03 §2、§5；04 §1–2；06 §1；15 DeepSeek 行 | 206 |
| 阿里百炼（千问 DashScope） | ① `/compatible-mode/v1` ✅；Ⓓ `/api/v1/services/aigc/text-generation/…` 📄；④ `/apps/anthropic/v1/messages` 📄（模型子集）；② ✅（文档说不支持 PDF）；🖼 同步+异步 ✅；🎬 仅异步 ✅；🎤 同步 multimodal-generation／`-filetrans` 异步 ✅ | 一把 key 六条 wire，Bearer；路径从 base 推导（剥 `/compatible-mode/v1` 拼 `/api/v1` 或 `/apps/anthropic/v1`），只认路径不认 host（intl 域名同） | ⚠ 原文未说 | 协议可用性按模型分；`json_object` 缺 "json" ❌ 400；thinking 开时 `tool_choice` 只 `auto／none`；① `enable_search` 🔇 无痕、`enable_code_interpreter` 部分模型 🔇／qwen3.8 ❌ 400；② 单独 `web_extractor`／关思考 `code_interpreter` 200 后 `response.failed`；同步 ASR 🔇 忽略 `diarization_enabled`；细节见 §3 | 标准 ① usage；`usage.x_tools.code_interpreter.count`（限时免费）；搜索按次价比 Anthropic 低三个数量级、`web_search_image` 是搜索 6–12 倍；出图签名 URL 24h 过期、代码解释器图 12h 过期 | 【实测 2026-09-28 视频输入】【实测 2026-09-19 出图】【实测 2026-09-17 服务端工具】【实测 2026-09-13 ASR】【实测 2026-08-29 视频】【文档 2026-09】 | 01 §8.1、§8.4；03 §3、§7；04 §2、§4、§5.1；05 §5；06 §2；13 §4；14 §2；16 §4–9；15 百炼行 | 9、10、13、56–59、70、74–78、101–104、115–121、206–208 |
| MiniMax（国内站） | ① ✅、④ ✅（模型 id 完全一致，分两行）；🖼 `image-01` ✅；🎬 `/v2/video_generation` ✅（异步任务）；②③Ⓓ🎤 — | 剥 `/v1` 或 `/anthropic/v1` → 拼 `/v2/…`（视频面）；鉴权 — | ⚠ | 错误在 HTTP 200 体内 `base_resp.status_code`（1004／1008／1002，0 成功）；`tool_choice` 只 `auto／none`；④ 关思考发温度 🔇 不理会、开思考带温度 200；④ 停在 `*_tool_result` 报 `end_turn` 且拒收自发块 ❌ 400；`<think>` 内联；细节见 §3 | ⚠；续跑每腿全新计费；🖼 `success_count` 是字符串 `"0"` 也算「成功」 | 【实测 2026-09-28 ④ 温度（MiniMax-M3）】；【实测 2026-08 ①／④ 续跑】；【实测 2026-08-29 视频】；【文档 2026-08】 | 01 §8.1、§8.3–8.4；03 §3.4、§6；04 §2、§4；05 §6；06 §2；13 §4.2；14 §2；15 MiniMax 行 | 6、11、90、91、113、199、201、202 |
| 火山方舟 · 按量付费 base | ① `{base}/chat/completions` 📄（对话面未实测，能力记 `unknown`）；②④ ⚠ 未验；🖼 `{base}/images/generations`（`ark` route）📄（按量 key 未实测，实测均在套餐 base，见套餐行）；Files API `/api/v3/files` ⚠（只观察到套餐 key 打它 401，文档说对按量 key 开放）；🎬 Seedance 需按量 key（body 未覆盖） | `https://ark.cn-beijing.volces.com/api/v3`，Bearer；按量 key；套餐 key 打此 base ❌ 401 | 静态目录带日期 id（`doubao-seedream-5-0-260128`）；⚠ `/models` 形态未说 | 对话面未测；🖼 `watermark` 默认 true、`stream:true` 首块 ≈27 s、组图单张审核拦下在 `data[]` 单项 `{error}`；`background:"transparent"` 只保证结果背景透明、客户端不应按输入透明 PNG 自动开（坑 130） | 🖼 `usage.input_images`、首张免费、失败免费；`output_tokens` = 像素/256 只是参考不是 token 计费 | 【文档】；出图实测均在套餐 base【实测 2026-09-18】【实测 2026-09-23】，按量 key 未实测 | 01 §9.3；13 §4.1、§7、§8；14 §2；15 火山方舟行 | 79–85、87、88、130–132 |
| 火山方舟 · 订阅套餐 base（Agent／Coding Plan） | ① `/api/plan/v3/chat/completions` ✅；② `/api/plan/v3/responses` ✅（`/api/plan/responses` ❌ 404）；④ base `/api/plan` 的 `/v1/messages` ✅；🖼 同 base（5.0 pro／lite）✅；Files API ❌ 404（三种路径）；🎬 Seedance ❌ 404；③Ⓓ🎤 — | `https://ark.cn-beijing.volces.com/api/plan/v3`，Bearer；④ `x-api-key` 与 Bearer 都收；与按量同 channel type，变体按 endpoint 去尾斜杠回读 | ① `GET /api/plan/v3/models` ❌ 404 非 JSON；④ `/v1/models` 对有效 key ❌ 401；退回静态目录并再发最小补全定论（错 key 401、造的 id 404 `UnsupportedModel`） | 套餐按模型裁剪且挑拼写（Seed 1.6 系／无 lite 拼法／4.5／4.0／5.0 flash 全 ❌ 404 `UnsupportedModel`）；④ 温度 `0` 🔇 当没发；④ 签名不校验 🔇；① 2.1 `encrypted_content` 不回传；json_schema 按模型守不守；① 无服务端搜索；细节见 §3 | `max_tokens` 上限按模型 ❌ 400 报上限（2.0-mini 131,072、2.1-turbo 262,144）；上下文 256k；② `usage.tool_usage_details.web_search.doubao`；④ `usage.server_tool_use.web_search_requests`；① 收 `video_url`，`fps` 不改账单（未定论） | 【实测 2026-09-18】39 条全过；Files API／flash／透明背景【实测 2026-09-23】；④ 温度与视频输入【实测 2026-09-28】 | 01 §9.3；02 §1 表后；03 §3.2、§3.4、§5；04 §2；05 §5；06 §5；15 火山方舟行 | 80、81、114、130–137、198、201、206、208 |
| 智谱 BigModel · 按量标准端点 | ① `/chat/completions` ✅（收 `video_url`、忽略 `fps`：更早样本，型号与日期未标 ⚠ ⏳待复核）；Ⓓ 独立 `/web_search`、`/reader` REST ✅；🎤 `glm-asr`【实现】；②③④ —（走 Coding Plan 行）；🖼🎬 — | `https://open.bigmodel.cn/api/paas/v4`，Bearer；错 key ❌ 401 `令牌已过期或验证不正确` | `/models` OpenAI 形 `{object:"list", data:[{id,…}]}`，连接测试直接可用 ✅ | `json_schema` 🔇 200 无视；`tool_choice` `required`／具名 🔇 不强制（4.7／4.6／4.5 思考开时具名 ❌ 400 `1210`）；`reasoning_effort:"none"` 🔇 被丢或照想、档位折档；`web_search` 意图跳过仍说「根据联网搜索结果」🔇；非 5.3-flash(x) 收 `image_url` ❌ 400；未知顶层字段一律放过；细节见 §3 | `max_tokens` 上界 ❌ 400 生成前拒不计费（5.x／4.6／4.7 131,072；4.5-air 98,304）；对话内 `web_search` 结果按 token 灌入（`search_pro` ≈24k、`search_std` ≈6.7k）；独立端点无 usage、按次 | 【实测 2026-09-19】11 个对话模型 | 01 §9.4；03 §3.1；04 §2、§4；05 §5；06 §2；16 §10.2；15 智谱行 | 94–100、206 |
| 智谱 BigModel · Coding Plan 编程端点 | ① `/api/coding/paas/v4` ✅；④ `/api/anthropic` ✅；② `/api/v1` ✅（三者只测到「按量 key 200」，完整实测未覆盖 ⚠） | 同 host、同一把按量 key 全通；**路径决定扣余额还是扣套餐** | ② `/api/v1/models` 不是 OpenAI 形：Codex CLI 目录 `{models:[{slug, context_window, supported_reasoning_levels, input_modalities, …}]}` 只列 3 个；④ `/v1/models` Anthropic 形 | 选错路径不失败只换一笔钱；套餐条款只许「指定工具」使用，违规限流乃至封号→必须分行，不挂进按量行线路菜单 | 扣套餐（同 key 不同前缀不同计费） | 【实测 2026-09-19 + 文档】 | 01 §9.4；15 智谱行、尚未覆盖节 | — |
| Kimi（Moonshot） | ① ✅（仅一条实测）；其余 — | — | — | `json_object` 不查 "json" 字样 | — | 【实测 2026-09-19】（与智谱同批；日期按同批推断 ⚠） | 04 §2；15 尚未覆盖节 | — |
| Azure OpenAI（部署变体） | ①② 部署变体 📄；`api-version` 细节未覆盖 | `api-key` 头；URL `/openai/deployments/{d}/...?api-version=`，模型标识不同——要做是另一族不是 compat 选项 | — | `finish_reason: "content_filter"` 代替错误码，几乎不带文本，必须 throw；**中转站里叫 `[Azure]` 的 ≠ Azure OpenAI**（2026-09-24 那个是带护栏的网关） | ⚠ | 【文档】 | 01 §2；02 §5；06 §2；15 行 | 7、159（辨识） |
| Vertex AI（Gemini／Claude 部署变体） | ③ ✅（经 OrcaRouter ③ 线路实测，回包 Vertex 原样）；Claude 部署变体 📄 | 经 OrcaRouter 时 Bearer；直连鉴权 — | — | 回包带 `createTime`、`usageMetadata.trafficType:"ON_DEMAND"`；`thinkingLevel:"MINIMAL"` ❌ 400 `Thinking level MINIMAL is not supported`；缺签名 HTTP ❌ 400；枚举由上游校验 | `trafficType`；`googleSearch` 按查询条数约 $0.014/条；`toolUsePromptTokenCount` 在 prompt 之外 | 【实测 2026-09-26 经 OrcaRouter】；【文档】 | 01 §2、§9.5；03 §2；05 §5；06 §1 | 170–173、178、190 |
| AWS Bedrock（Claude 正向部署） | ④ ✅（经 New API AWSb 渠道实测）；Bedrock Converse 第五种 body（camelCase、SigV4）未接；Anthropic 服务端工具 ❌ 400 | 经 New API 时同 New API；直连 SigV4 — | — | 消息 id `msg_bdrk_` 前缀；参数校验与官方同文 ❌ 400；`web_search`／`web_fetch`／`code_execution` 各 ❌ 400 整条请求；URL 图片 ❌ 400；缺口会响不静默 | `cache_control` ✅ 真缓存；「Say OK.」10 token | 【实测 2026-09-23】经 New API AWSb 渠道 | 01 §2、§9.2 第 4 条；05 §5；15 行 | —（渠道层坑见 AWSb 行） |
| OrcaRouter（网关共性） | ①②③④ 四面同一主机（各线路见下五行）；PDF 四面都读；🖼🎬🎤 — | `api.orcarouter.ai`，一把 key `Authorization: Bearer`（`x-api-key`／`x-goog-api-key` 只在各自路径承诺）；模型 id 带厂商前缀（`anthropic/claude-sonnet-5`） | `GET /v1/models` Bearer → OpenAI 形（203 条，带 `supported_endpoint_types`、`context_length`、`max_completion_tokens`）；`x-api-key` → Anthropic 形；`/v1beta/models` → Gemini 形；`supported_endpoint_types` 是建议不是限制 | 四面请求都被重新序列化（未知字段／非法枚举常 200）；错误信封改写成 OpenAI 形（④ `type:"<nil>"`、路径 `***`）；响应头只有 `x-orca-request-id`／`x-orca-version`／`x-orca-route`，不漏上游头；余额零 ❌ 402 `insufficient_user_quota` 先于模型解析；细节见 §3 | 唯一声明「报的数 = 实扣」的平台；按 1/500,000 美元取整；与 `GET /v1/generation?id=` 的 `total_cost` 对账（④③ 相等，①② 差不到一个计价单位；账单另有 New API 式 `quota` = 美元 × 500,000）；花费字段按面不同（见各线路） | 【实测 2026-09-03】【实测 2026-09-26】【文档】 | 01 §9.5；06 §1、§2、§5、§8；15 OrcaRouter 行 | 166、174–177、185、186、196 |
| OrcaRouter · ① 线路 | ① ✅（任何模型都能调的翻译层）；`video_url`：Gemini 🔇 200 静默丢（输入 token 25→25）、GPT ❌ 400 | `/v1/chat/completions`，Bearer | 同共性 | 🔀 回包 OpenRouter 形态（`gen-…` id、`provider`、`native_finish_reason`、`reasoning_details[]`）；GPT 上游再走 Responses；Gemini 不返回思维链只报 `reasoning_tokens`；`web_search_options` 200 无 `annotations`；无 parameters 的 `googleSearch` 等函数名 🔀 换成 Gemini 原生工具；细节见 §3 | 末块 `usage.cost`（`include_usage`；流式没有 `cost_usd`，非流式两个都有）、`is_byok`、`cost_details.upstream_inference_cost`；不需请求头 | 【文档 + 实测 2026-09-03／09-26】；视频输入【实测 2026-09-28】 | 01 §9.5；02 §1 表后；05 §5；06 §1 | 185、205、206 |
| OrcaRouter · ② 默认线路 | ② ✅ | `/v1/responses`，Bearer | `gpt-6-luna`／`-sol` 只声明 `openai`，打 `/v1/responses` 照样 200 | 🔀 OpenRouter 形态：`gen-…` id、伪造 `msg_tmp_…`／`fc_tmp_…`、`summary:"auto"` 回显 `"detailed"`、`store` 恒 `false`；`minimal` 🔀 改 `low`；`effort:"bogus"` 回网关 `upstream_rejected_request`；回灌义务测不出（篡改／丢 reasoning item 全 200）；细节见 §3 | `response.completed.response.usage.cost`（不需请求头） | 【实测 2026-09-26】 | 01 §9.5；03 §7.1；04 §2；06 §1 | 175 |
| OrcaRouter · ② 原样线路 | ② ✅（`store:true` 或 `include` 含 `web_search_call.action.sources` 触发） | 同上 | 同上 | OpenAI 原样：`resp_…` id、`billing`、`tool_usage`、`moderation`、`prompt_cache_retention:"24h"`、默认 `store:true`；`tools:[{type:"web_search"}]`、`include:["reasoning.encrypted_content"]`、`text.verbosity` 都不触发分流；strict `text.format` 守住；`web_search` 真跑；细节见 §3 | ❌ 没有任何花费字段（`X-OrcaRouter-Include-Cost` 头对 ② 无效）；`usage.input_tokens_details.cache_write_tokens`（一次 `web_search` 4,388） | 【实测 2026-09-26】 | 01 §9.5；04 §2；05 §5；06 §1 | 175、186 |
| OrcaRouter · ③ 线路（Vertex） | ③ ✅（Vertex AI，不是 AI Studio）；`:countTokens` 🔀 被当 `generateContent` 执行并计费（$0.0028） | `/v1beta/models/{model}:generateContent`／`:streamGenerateContent`，Bearer（`x-goog-api-key` 只在此路径承诺）；id 里斜杠原样进路径不编码 | `GET /v1beta/models` Gemini 形 | 回包 Vertex 原样（`responseId`、`modelVersion`、`thoughtSignature`、`createTime`、`trafficType:"ON_DEMAND"`）；请求重序列化但枚举由上游校验（`thinkingLevel:"BOGUS"` Vertex 原文 400）；`MINIMAL` ❌ 400；`thinkingBudget:0` 🔇 照想；流末 `{text:""}` 回灌 ❌ 400；错误 `***` 遮路径；细节见 §3 | 带 `X-OrcaRouter-Include-Cost: true` 才有末块 `usageMetadata.costUsd`，不带头没有；与账单相等；`googleSearch` 约 $0.014/条；PDF 一页按图 520 token；16×16 图 1,098 token | 【实测 2026-09-26】；思考回退／视频【实测 2026-09-28】 | 01 §9.5；02 §2.2；03 §2、§5；04 §2；05 §3、§5；06 §1–2 | 170–173、176–178、186、190–195、197、203、204 |
| OrcaRouter · ④ 线路 | ④ ✅（Anthropic 原样）；`/v1/messages/count_tokens` ❌ 301 到官网首页 | `/v1/messages`，Bearer（`x-api-key` 只在此路径承诺） | `x-api-key` 打 `/v1/models` 回 Anthropic 形（无 `supported_endpoint_types`） | 回包 Anthropic 原样（`msg_011C…` id、base64 `signature`、`usage.cache_creation`、`service_tier`、`inference_geo`）；请求重序列化：顶层 `foo:1`、`thinking.type:"bogus"`、`output_config.effort:"bogus"` 全 200（官方 400）；整块丢 thinking block 200；错误信封 `type:"<nil>"`；细节见 §3 | 流式带 `X-OrcaRouter-Include-Cost: true` 才有 `message_delta.usage.cost_usd`（`message_start` 快照没有）；与账单相等；`web_search_20250305` 无 beta 头、服务端自动写缓存 2,834；一请求合计 $0.051；PDF Sonnet 5 记缓存写 1,630 | 【实测 2026-09-26】；思考回退【实测 2026-09-28】；402【实测 2026-09-03】 | 01 §9.5；03 §2、§3、§5；04 §2；05 §3、§5；06 §1–2 | 4、174、176、177、179、182、186、197、203、204 |
| OpenRouter | ① ✅ 📄；其余 — | host `openrouter.ai`；鉴权 — | `/models` 带 `context_length` | SSE 体内 `data:{"error":...}` routinely（审核／上游故障／余额耗尽）；「OpenRouter 形态」指纹（`gen-…`、`provider`、`native_finish_reason`、`reasoning_details[]`）是在 OrcaRouter 上看到的，不是对 OpenRouter 本身的实测 ⚠ | ① 回 `usage.cost`／`is_byok`／`cost_details`（平台未受信前不收） | 【文档】；指纹经 OrcaRouter【实测 2026-09-26】 | 06 §1、§2、§6；01 §9.5；15 OpenRouter 行 | 6、185 |
| New API 类中转站（平台层／转换层，总览） | ①②③④ 形状都有（按渠道）；Claude ① 是 ①→④ 转换、GPT ① 是 ①→② 转换；`/mj/*` Midjourney | 自建、无可识别 host；不手选平台落 `custom`；Bearer；渠道／档位写在模型 id 前缀（`[Plus]gpt-5.6-terra`，不加剥前缀规则） | `GET /v1/models` 的 `supported_endpoint_types` 不可信（声明 anthropic／gemini 却不许）；没线路／假模型同一 ❌ 503 `No available channel for model … under group …`；欠费 ❌ 402 | 转换层（四渠道一致）：Claude ① `response_format` 🔇 丢、`reasoning_effort:"max"`／`"none"` = 不想；GPT ① 翻成 ②、`web_search_options` 🔇；③ 面只认 camelCase；URL 图片中转站自己下载 ❌ 500 `count_token_failed`；同一非法参数四上游四种报法；接收侧畸形；细节见 §3 | 中转站估算 usage：总数可用、缓存分段不可信（`cache_control` 只写不读）；`usage.attribution.request_fields.instructions.input_tokens` 读注入量 | 【实测 2026-09-23】【实测 2026-09-24】【中继源码】 | 01 §9.2；02 §2.2、§3.2；03 §3.3、§4；04 §2、§5.1；05 §3、§5；06 §1、§2、§4.1、§5；15 New API 行 | 2、8、15、61–65、105–112、140、142、147、150、152–158、164、166–169、183 |
| New API · Kiro 渠道（Claude） | ① `/v1/chat/completions` ✅（翻成 Messages）；④ `/v1/messages` ✅；② `/v1/responses` ❌ 500 `convert_request_failed`「not implemented」；③ `/v1beta` ❌ 500 同；`count_tokens` ❌ 404 `Invalid URL`；`/v1/files` ❌ 401 | 同一台 New API；④ `x-api-key` 与 Bearer 都收；不带 `anthropic-version` 也 200；前缀 `[kiro]` `[kiro1]`…`[kiro3]` `[kiro-200k]` `[特价kiro量]` | `/v1/models` 的 `supported_endpoint_types` 一律 `null`；渠道只在 id 前缀；回显去掉前缀；不存在模型 ❌ 503 `model_not_found` | 反代（`effort:"bogus"` 200）：`max_tokens` 🔇；思考只 low 有效；两族 JSON 旋钮 🔇；强制 `tool_choice` 只非流式生效；单挂 `web_search` 🔀 整条劫持；`web_fetch`／`code_execution` 🔇 丢且模型假装执行；PDF／URL 图片 🔇 丢；不注入系统提示；细节见 §3 | `usage.billing_usage.source:"claude_messages"`；`cache_control` 只写不读、缓存段是拼的（同前缀两次都报 `cache_creation_input_tokens:7360`）；「Say OK.」7 token + 拼的缓存段；流式 `prompt_tokens` 301 vs 非流式 102 | 【实测 2026-09-23】（curl ≈200 次 + `live.relay-kiro.test.ts` 31 条全过） | 01 §9.2「Kiro 渠道的 Claude」「五个渠道」；03 §3.3；04 §2、§4；05 §5；06 §1、§8 | 65、138–147 |
| New API · CC 渠道（Claude） | ①④ ✅ | 同一台、同一把 key；前缀 `[CC量]`（推测 Claude Code 通道，未证实） | 同 Kiro（渠道写在 id） | 反代（无校验一律 200）：思考 ✅ 但 opus-5 thinking 文本恒空；`max_tokens` ✅；强制 `tool_choice` 带思考 3/8、4/8 时好时坏；`output_config.format` opus-4-6 🔇、opus-5 ✅；PDF ✅；URL 图片 🔇 丢；`web_search` ✅／`web_fetch` ✅／`code_execution` 🔇 丢；细节见 §3 | `cache_control` ✅ 真缓存（第二次 `cache_read` = 前缀）；「Say OK.」9–10 token | 【实测 2026-09-23】curl（无 live adapter 文件） | 01 §9.2「五个渠道」；04 §2、§4；05 §5；06 §1 | 147、149、150、152、153 |
| New API · anti 渠道（Claude） | ①④ ✅ | 同上；前缀 `[anti量]`（推测 Antigravity，未证实） | 同上 | 反代：不思考（`-thinking` 变体也不）；`max_tokens` ④ ✅、① 🔇；强制 `tool_choice` 0/0；两族 JSON 旋钮 🔇；PDF、纯文本 document 🔇 丢；URL 图片 ❌ 500；`web_search`／`web_fetch`／`code_execution` 🔇 全丢，模型凭记忆答 | 没有任何缓存字段、两次都全价；「Say OK.」39 token（约 30 token 注入） | 【实测 2026-09-23】curl | 01 §9.2「五个渠道」；03 §3.3；04 §2、§4；05 §5；06 §1 | 147、148、150、151、152 |
| New API · AWSb 渠道（Claude，Bedrock 正向） | ①④ ✅ | 同上；前缀 `[正向AWSb量]`；消息 id `msg_bdrk_` | 同上；`[AWSb]gpt-5.6-sol` 目录有但 ❌ 503 `No available channel` | 正向：`effort:"bogus"` ❌ 400 官方原文；思考真分档；`max_tokens` ✅；强制 ✅/✅；`output_config.format` ✅（① `response_format` 仍 🔇——转换层）；PDF ✅ citations ✅；URL 图片 ❌ 400；`web_search`／`web_fetch`／`code_execution`／① `web_search_options` ❌ 400 整条请求 | `cache_control` ✅ 真缓存；「Say OK.」10 token | 【实测 2026-09-23】curl；GPT 503【实测 2026-09-24】 | 01 §9.2 第 4 条、「五个渠道」；04 §2；05 §5；06 §1、§8 | 147、150、152、166 |
| New API · 官key 渠道 | ⚠（①④ 两个端点当天全 ❌ 502 `Upstream request failed`，没测到）；GPT-5.6-sol ❌ 503 `No available channel` | 同上；前缀 `[官key量]`／`[官key]` | 同上；目录里有 ≠ 有线路 | ⚠ 没测到；画像 official 无格子，选它只表示「已分类」 | ⚠ | 【实测 2026-09-23】502；【实测 2026-09-24】503 | 01 §9.2「五个渠道」、「上游做成作者声明的数据」第 2 条；06 §5 | 166 |
| New API · `[特价Pro]` 档（GPT，ChatGPT 账号池／Codex） | ② ✅；① ✅（翻成 ②）；④ ❌「This group does not allow Anthropic Messages requests」；`image_generation` ❌ 403；`code_interpreter`／`file_search` ❌ 流式 `response.failed`；`web_search` ✅ | 同一台同一把 key；画像 codex | 声明 `supported_endpoint_types` 含 `anthropic`／`gemini` 却不许——不可信 | 不带 `instructions` 注入时有时无（同档 0／11／296／4.4K／17K）；① 带 system 仍注入 4,397；`effort:"none"` 🔀 回显 `medium`；乱写 effort → 流式 `response.failed`；`temperature:0.5` 🔀 回显 `1.0`；`max_output_tokens`／`max_completion_tokens` 🔇；json_schema ✅（两面）；细节见 §3 | `usage.attribution.request_fields.instructions.input_tokens` 是注入读数；前缀缓存 `cached_tokens` 9,984；`web_search` 输入 8.5–14K、6–10 s | 【实测 2026-09-24】（curl ≈560 次 + `live.openai-responses.test.ts` 45 条过 41） | 01 §9.2「同一个 GPT」；03 §7.4；04 §5.1；05 §5；06 §1、§2、§4.1、§5、§8 | 61、62、65、161、162、164–167、169 |
| New API · `[Plus]` 档（GPT，账号池） | ②① ✅；④ ❌ 同上；`image_generation` ❌ 403；`code_interpreter`／`file_search` ❌ 502；`web_search` ✅ | 同上；画像 codex | 不可信（同上） | 不带 `instructions` 注入 4,389（`attribution…instructions.input_tokens: 4380`）；① 带 system 3/3 注入 4,395；乱写 effort ❌ 502 `Upstream request failed`；`none` 🔀 `medium`；`temperature:0.5` 🔀 `1.0`；`max_output_tokens` 🔇；json_schema ✅（省略／显式 strict 都收）；细节见 §3 | 同 `[特价Pro]` | 【实测 2026-09-24】 | 01 §9.2「同一个 GPT」；04 §5.1；05 §5；06 §2 | 61、62、65、161、162、164、165、169 |
| New API · `[Pro]` 档（GPT，账号池） | ②① ✅；④ ❌ 同上；`image_generation` ❌ 403；`code_interpreter`／`file_search` ❌ 400 `Unsupported tool type`；`web_search` ✅ | 同上；画像 codex | 不可信 | `text.format` json_schema 🔇 整个丢（省略／显式 `strict:true` 都丢，回显 `{type:"text"}`）；旧：第八个样本「显式 `strict:true` 才丢」→ 新：不论写不写都丢（2026-09-24 扩展）；① `response_format` 🔇 丢 4/4；乱写 effort ❌ 400 官方原文；`none` 🔀 `medium`；`temperature:0.5` 🔀 `1.0`；`max_output_tokens` 🔇；细节见 §3 | 同 `[特价Pro]` | 【实测 2026-09-24】；旧【实测 2026-09 第八个样本】 | 01 §9.2「同一个 GPT」「上游画像扩到 GPT」；04 §5.1；06 §2、§8 | 63、160、161、162、164、165 |
| New API · `[Azure]` 档（GPT，带护栏的网关，非 Azure OpenAI） | ②① ✅；④ ❌；`gpt-5.6-sol` ❌ 503 无线路（用 `-terra` 顶替）；`image_generation` ✅ 83 s；`code_interpreter`／`file_search` ❌ 500；`web_search` 🔇 静默丢 | 同上；画像 azure（正向） | 不可信；无 `attribution` 字段 | 带 `instructions`（含空串）🔀 追加约 1.2K 护栏并可能拒创作（6 拒 2，200 无 `refusal`）；`none` 🔀 `medium`（① 真关）；乱写 effort ❌ 500；`temperature:0.5` ❌ 500；`store:true` ❌ 500；① 具名 `tool_choice` ❌ 500；`web_search` 🔇；URL 图片 ❌ 500 `count_token_failed`；`max_output_tokens` ✅；细节见 §3 | 每请求 +1.2K 输入（多半命中缓存）；`cached_tokens` 11,576；① `max_completion_tokens:16` → `finish_reason: length` 但 `completion_tokens` 128 | 【实测 2026-09-24】 | 01 §9.2「同一个 GPT」「上游画像扩到 GPT」；02 §7.1；04 §5.1；05 §5；06 §1、§2、§4.1、§5 | 159、161、162、163、164、166、167、169 |
| New API 中转站（另一台）· `[Pro]`／`[Plus]` 档（GPT-5.4／5.5／5.6，第八、第十个样本） | ① ✅、② ✅（① 翻成 ②：响应 id `resp_…`、流里 `reasoning_content`） | ⚠ base 未给（自建）；Bearer；档位前缀 id | 档位前缀使按 id 前缀查表认不出——不加剥前缀规则，让作者手动声明 | 不发 `instructions` 注入 Codex 系统提示 4.4K–9K（Chat 面同样）；sol 发 `max` 🔀 回显 `none` 且 0 推理 token（2026-09-24 另一台未复现）；terra `none` 🔀 `medium`；`temperature:0.5` 🔀 `1.0`；其中一台 `max_output_tokens` 🔇；一档多上游，回显字段时有时无；细节见 §3 | 注入直接体现为输入 token 4.4K–9K | 【实测 2026-09】+【中继源码】 | 01 §9.2 第 1–4 条；04 §5.1；05 §5；06 §4.1 | 61–65、107、108 |
| 未具名中转（Claude 后端，Joycai 线上流量） | ① | — | — | `arguments` 背靠背拼接多对象 `{}{"id":1}`；调用 id 空串 `""`、同批共用 → 下一轮重复 `tool_call_id` ❌ 400，此后每轮 400；空参数执行不报错 🔇 | — | 【实测 2026-08-08】【实测 2026-08】 | 02 §3.2；05 §3 | 105、106 |
| Midjourney（midjourney-proxy／New API `/mj/*`） | 🖼 独立异步出图协议（`/mj/submit`）；其余 — | ⚠ | ⚠ | ⚠ | ⚠ | 【实现，日期未标】 ⏳待复核 | 13 §2、§4.2；15 行 | — |
| Ollama（本地） | ① 兼容 ✅；`/api/show` 元数据；其余 — | 本机 `:11434`；无 key 时整个 `Authorization` 头省略（空 Bearer 被拒）；Windows 打包版 ❌ 403（覆盖 `Origin` 头修复） | ① 形 `/models`；`/api/show` 的 `model_info` 与 `parameters` 常差 30 倍，小的才算数（`num_ctx` 默认 2048/4096） | 🔇 超窗从头部静默丢弃（先丢 system）返回 200；`num_ctx` 静默截断；JSON cue 另起 user 消息报 chat 模板错误 | ⚠（兼容层 `stream_options.include_usage` 可能没实现，usage 全 0 当「没报」） | 【实测，日期未标】 ⏳待复核 | 01 §6；02 §5、§6；06 §1、§6、§9.3；15 Ollama 行 | 5、8、211 |
| LM Studio／llama.cpp（本地） | ① 兼容 ✅；其余 — | 本机；空 Bearer 被拒（同 Ollama） | LM Studio `/models` 带 `max_context_length`；llama.cpp `/props`；`max_model_len` 置 high | 两条连续 user 消息在严格交替 chat 模板上 ❌ 报错；超窗静默截断同本地栈 🔇 | ⚠ | 【实测，日期未标】 ⏳待复核 | 01 §6；06 §6、§9.3 | 5、211 |
| Groq／硅基流动（仅 ASR） | 🎤 ⓐ OpenAI 兼容转写【实现】；chat 面未覆盖 | 地址在 16 §3；硅基流动 SenseVoice 语种 | — | ⚠ | ⚠ | 【实现】 | 16 §3；15 行 | — |
| 火山引擎 openspeech（豆包录音识别极速版，与方舟 base 无关） | 🎤 私有 HTTP `openspeech.bytedance.com` | 独立鉴权头 `X-Api-App-Key`／`X-Api-Access-Key`／`X-Api-Resource-Id` | — | 🔇 成败在响应头 `X-Api-Status-Code == 20000000`，HTTP 恒 200，缺头按失败 | ⚠ | 【实现 2026-09，原 pyVideoTrans】 | 16 §10.2；23 §3.2 | 122 |
| ASR 专营：Deepgram、ElevenLabs、CAMB AI、Gladia、小米 MiMo、302.AI | 🎤 各自 SDK／私有协议 | — | — | ⚠ | ⚠ | 【实现 2026-09，原 pyVideoTrans】 | 16 §10.2；15 行 | — |

---

## 3 各平台展开

### 3.1 官方直连

### OpenAI 官方

- 面与路径：① `/v1/chat/completions`；② `/v1/responses`（adapter 自己拼）；o1-pro／codex 系／computer-use 只有 ②，走 ① 会失败（截至 2026-08）【文档 2026-08】；🖼 Images API（13 §2、§4.2「images-api」）；🎬 Sora（14 §2）；🎤 `/audio/transcriptions`（whisper／gpt-4o-transcribe／diarize，16 §3、§10.2；`gpt-4o-*-transcribe` 无 `segments`，坑 116）。
- 分辨后端指纹：① `system_fingerprint`、OpenAI 形 `usage.*_details`；② `resp_…` id、`reasoning.encrypted_content` 可回灌、`output_text` 带 `annotations`、`billing`／`tool_usage`。
- 已知行为：② `text.format` json_schema 省略 `strict` 自动升 `strict:true`（回显 `true`）；工具定义省略 `strict` 端点自动 strict，非 strict schema 被改写契约（坑 64）→ 工具定义显式 `strict:false`；`json_object` 缺 "json" 400／无限空白流（坑 14）；GPT-5.x 空文本 `status:"completed"` message 收尾是合法输出（坑 109）；GPT-5.4+ 原生工具按需加载（`defer_loading`、`tool_search`、`namespace`、`additional_tools`），下一轮不回传 `tool_search_output` → 工具静默消失（坑 68）；`web_search` 的 `open_page`／`find_in_page` 无 queries（坑 71）；`code_interpreter` 要 `container`（不是 DashScope 那个工具）。
- 计费：一次搜索回答 45.7K 输入、112 s，首个事件可晚到 54 s（流看门狗首块等待要高于此）——经 New API 第十个样本测得，官方直连未测（OQ-027、OQ-053）；`text.verbosity: low/medium/high` 生效。
- 注意：经中转站的 GPT-5.6 事实按上游分（账号池／网关）见 New API 各档行；GPT-6 经 OrcaRouter 事实见 OrcaRouter 各线路行。是否收 ① `video_url` 未量（§4）。

### Anthropic 官方

- 面：④ `/v1/messages`；base 约定与 OpenAI 相反（根地址 vs 自带版本段，坑 16）；鉴权 `x-api-key` 与 `Bearer` 两套约定、各有网关只认一种（坑 17）——compat 端点 default/bearer/both 三模式，官方只 default。
- 已知行为（全部 ④ 官方口径）：不回传 thinking／redacted_thinking 块（含 signature、顺序不动）思考静默消失（坑 1）；`display` 默认 omitted、Sonnet 5／Opus 5.5 不发 `thinking` 也在想（坑 4）→ 恒发 `display:"summarized"`；Opus 5.5／Fable 5.1 拒收 `thinking: disabled` 400 `requires adaptive thinking`（坑 184）；「关闭」只是最低 effort（坑 203）；④ 无 JSON mode 参数（发 `response_format` 硬 400），只有 `output_config.format` 严格档（Claude 4.5 起）与 `off`，无 `json_object` 中间档（坑 180）；schema 不支持数值界／长度／pattern／递归（坑 182）；`output_config.format` 与 `output_config.effort` 同一对象合并不覆盖（坑 181）；`stop_reason:"refusal"` 必 throw；`pause_turn` → verbatim 续跑（`encrypted_content` 一字不改，`MAX_PAUSE_CONTINUATIONS = 4`）；`web_search_20250305` 不需要 beta 头、`max_uses` 是唯一刹车；`defer_loading` 与 `cache_control` 同现 400。
- 计费：三桶不重叠、直接读 `input_tokens` 长 prompt 命中缓存时少报一个数量级（坑 18）；`message_delta` 只报 output 不清零 input；没发 `cache_control` 也有 `cache_creation_input_tokens`（`web_search` 结果服务端自动写缓存，一次 2,834，坑 179）。
- 注意：Claude 5 系的原样回包事实全部是经 OrcaRouter ④ 线路测得（03 §3、§5；04 §2；05 §3、§5），标「经 OrcaRouter」；部署变体 Vertex／Bedrock 见 3.2。

### Google Gemini 官方（AI Studio）

- 面：③ `generateContent`／`streamGenerateContent`（`alt=sse`）；同一 wire 也出图（`responseModalities`）；Imagen `:predict`、Veo（`predictLongRunning`／`operations`）只有【文档】。
- 已知行为：`responseMimeType` 有旧型号静默无视→mimeType + cue 双发；`responseJsonSchema`（标准 JSON Schema）与旧 `responseSchema`（OpenAPI 方言）互斥只发一个；每 chunk 是完整对象不是 delta；旧型号 `functionCall` 无 id（适配器自造），Gemini 3.8 起带 `id`；并行调用 `thoughtSignature` 只挂第一个 part；`defer_loading` 整个被拒（第三方报告，坑 69）；Gemini 2.x 与函数工具同发内置工具的问题未测（有意接受的风险）。
- 计费：output = `candidatesTokenCount` + `thoughtsTokenCount`；input = `promptTokenCount` + `toolUsePromptTokenCount`（坑 191）；代码 part 随历史回传占上下文、估算要计入（坑 195）；`googleSearch` 按查询条数约 $0.014/条（经 Vertex 实测，坑 190）。
- 注意：3.8 Flash 的档位／工具轮／PDF 520 token/页等事实是 Vertex 后端（经 OrcaRouter），不直接照搬 AI Studio；参考实现在官方 google 上只「未实测、照发」`googleSearch`。

### xAI (Grok) 官方

- 面：② 推荐；① Deprecated 仍作 legacy（`grok-4.3` 上 `video_url` 400 `Empty content block`，坑 206）；④ `/v1/messages` 完全弃用；🖼 `grok-imagine-image-2.0`（`quality` low/medium、`resolution` 1k/1.5k/2k）／初代 `grok-imagine-image`（默默收 `quality`，`1.5k` 400，坑 125）；🎬 `grok-imagine-video-1.5`。
- 已知行为：Grok 4.5／4.6 `reasoning.effort` 拒 `none`，4.3／4.5／4.6 全拒 `max` 400（坑 66）；加密推理须发 `include:["reasoning.encrypted_content"]` 才有 `encrypted_content`，缺了第二轮照样 200；`frequency_penalty` 在推理模型上实测 200（文档说报错，按实测记）；`tool_search`／`defer_loading` 规格有、实测 403（仅 alpha）；图片总像素 <512 拒（16×16 拒、32×32 过，宽高各 ≥8，坑 67）；`web_search_call` 有 `open_page`／`find_in_page`，一次搜索 6,851 输入。
- 计费：流里 `response.completed` 带 usage + `[DONE]` 收尾（文档没写终止事件）；🖼 `usage.cost_in_usd_ticks` 含输入图、不发 `quality` 按 Medium 计（坑 123）、`auto` 不可预算（坑 124）、报价只在收尾块（坑 127）、参考图文档 3 张实测 5 张 200 并计费（坑 128）；🎬 $0.08/s、首帧与参考图各 +$0.01/张、报价只在轮询 done 回包、`video.duration` 报实际秒数（坑 129）。

### DeepSeek 官方

- 面：① 只有一张脸；`deepseek-flash` 发 `video_url` 422 点名可接受的片段类型（坑 206）。
- 已知行为：`reasoning_effort:"none"` 关不掉，要 `thinking:{type:"disabled"}`；思维链回传义务分场景、两个方向都 400（与 Anthropic 静默剥离相反）；不支持 `json_schema`，`json_object` 需 "JSON" 字样；DeepSeek V4 的错误文案点名参数，「按 400 学降级」用得上。
- 计费：顶层 `prompt_cache_hit_tokens`／`prompt_cache_miss_tokens`，`prompt_tokens` 已含命中——命中要补进标准拼写，否则每次命中按全价记【Joycai 2026-09-14 修复】。
- 另：`deepseek-v4` 托管在百炼时 ② 面代码解释器放行（见百炼行）。

### 阿里百炼（千问 DashScope）

- 六条 wire（同一把 key）：① `/compatible-mode/v1`；Ⓓ `/api/v1/services/aigc/text-generation/…`（Qwen-Audio 仅此面）；④ `/apps/anthropic/v1/messages`（模型子集，具体未给）；② DashScope Responses（文档无 `text` 字段，报错还是忽略未验；文档说不支持 PDF，能力表有意保留待实测）；🖼 同步（`qwen-image` 仅同步）+ 异步（提交路径不同、不是 header 切换；`wan2.7-image` 二者皆可）；🎬 仅异步（`wan3.0`）；🎤 同步 multimodal-generation／`-filetrans` 异步（上传经 OSS `getPolicy`）。
- 路径推导：剥 `/compatible-mode/v1` 再拼，只认路径不认 host，幂等。
- 服务端工具（① 顶层字段）：`enable_search:true` 无来源、无角标、无痕（坑 10）；`search_options:{search_strategy:"agent_max"}` 与 `tools` 同发一律 400 `Agent mode does not support tools…`（坑 74）、`qwen3.8-flash` 400 `does not support the "agent" search strategy`；`enable_code_interpreter:true` 非流式 400、带函数工具 400、`qwen-max`／`qwen3-max-preview` 静默忽略（坑 75）、qwen3.8 全系 400、`qwen3-max` 思考关闭照常跑（与文档不符）；② `tools:[{type:"web_search"}]` ✅、`web_extractor` 仅当 `web_search` 同在（单独 → 200 后 `response.failed`，坑 70）、`web_search_image`／`image_search` 可单独（`arguments`／`output` 都是 JSON 字符串）、`code_interpreter` 按模型 id 放行（思考关闭 → `response.failed` `Normal mode does not support Code interpreter.`，坑 76）。
- 思考：同一端点两代模型字段与默认不同——商业款永远不思考、强度在老款静默无效（坑 9）；`switch` 方言 `enable_thinking`。
- tool_choice：thinking 开启时只接受 `auto／none`【文档】→ 只在本次真发 `enable_thinking:true` 时降 `auto`。
- 结构化：`json_object` 全线可用、缺 "json" 400 `'messages' must contain the word 'json'`；`json_schema` 只最新两三代商业款。
- 多模态：`qwen3-vl-plus` 收 `video_url`、`fps` 生效（1,241→641）；夹具 320×240 纯色 400 `Invalid video file`（坑 207）。
- 出图：错误在顶层 `{code,message}`（`DataInspectionFailed` 掉进 prose 正则，坑 58）；尺寸 `宽*高`（坑 59）；统一信封 `{model,input:{messages},parameters}`（坑 101）；省略 `size` 落 2K 档贵一倍（坑 102）；签名 URL 24h（坑 56）。
- ASR：同步接口静默忽略 `diarization_enabled`（坑 115）、无句级时间戳（坑 116）；400 `ASR_RESPONSE_HAVE_NO_WORDS` 按空文本成功（坑 118）；filetrans 403/404 按步骤分类（坑 119）；OSS 上传 `MalformedPOSTRequest`（坑 120）。
- 计费：`usage.x_tools.code_interpreter.count`；代码解释器限时免费但多轮推理 token 增（qwen3.8-flash 一问约 1.1k）；Files API 对套餐开放（与火山对比时提及）。

### MiniMax（国内站）

- 两张 chat 脸模型 id 完全一致（无模型耦合 → 分两行，视频槽位两行各一份）；视频面路径：剥 `/v1` 或 `/anthropic/v1` → 拼 `/v2/video_generation`。
- 已知行为：`base_resp.status_code` 在 HTTP 200 体内（1004／1008／1002），只认 `error` 会把过期密钥读成正常空回复（坑 6）；`tool_choice` 枚举只 `auto／none`，强制档不存在 → 无条件预判降 `auto`；`json_object` 不查 "json" 字样；④ 停在 `*_tool_result` 报 `end_turn`（无 `pause_turn`），回灌自己发出的块 400 `invalid params, tool result's tool id(...) not found` → transcript 纯文本续跑（坑 11）；空 assistant 消息 400；`<think>` 内联（跨 chunk 分片，坑 15）；④ 关思考发温度收下不理会、开思考带温度 200 而非 400、类目 `minimax` 不发温度（坑 199、201）；MiniMax-M3 不发温度就 19–20/20 答同一水果（缺省已收敛，坑 202）。
- 出图 `image-01`：「成功」但零张、`success_count` 是字符串 `"0"`（坑 90）；`subject_reference` 是主体参考不是编辑（坑 91）。
- 视频：首尾帧要嵌套 `{"type":"image_url","image_url":{"url"},"role":"first_frame"}`，平铺 `url` 被当没附图照样计费（坑 113）。

### 火山方舟 · 按量付费 base（`/api/v3`）

- 只有套餐 key 在手，对话面至今未实测——能力格记 `unknown`，不抄套餐的；是否收 ① `video_url` 未量；按量 key 上传文件能否被套餐 key 引用【未验】；② 不写 `sources` 是否落到按次「联网内容插件」【未验】。
- 出图（Seedream，`ark` route，路径 = Images API `{base}/images/generations`、body 不同）：`doubao-seedream-5.0-flash` 只在按量；Seedream 4.5／4.0 只在按量；`watermark` 默认 true → 恒明发（坑 79）；组图请求超时按张数放宽（坑 82）；`output_tokens` = 像素/256（坑 83）；单张审核拦下 `data[]` 单项 `{error}`（坑 84）；流式首块 ≈27 s（坑 85）、`partial_failed` 事件（坑 87）；拆图层（坑 88）；`background:"transparent"` 只保证结果背景透明、客户端不应按输入透明 PNG 自动开（坑 130）；改图输入图上限含源图 10（坑 131）；透明编辑对带透明通道 PNG 400 `at least one transparent pixel`（坑 132）。计费：`usage.input_images`、首张免费、失败免费（13 §7）。
- Files API `/api/v3/files` 只对按量 key 开放；Seedance 视频需按量 key、body 未覆盖。
- Endpoint ID `ep-…` 从 id 看不出哪一代，分类失败是正常，让作者点单。

### 火山方舟 · 订阅套餐 base（`/api/plan/v3`，Agent／Coding Plan）

- 三面路径：① `/api/plan/v3/chat/completions`；② `/api/plan/v3/responses`（探测路径少 `/v3` 打 `/api/plan/responses` 404 被判「没有 Responses」，坑 135）；④ base `/api/plan` 下 `/v1/messages`，`x-api-key` 与 Bearer 都收。
- 变体回读：与按量同 channel type，只按 type 找变体会把套餐读成按量、编辑器「恢复」成必 401 的 base（坑 80）→ 类型匹配后比 endpoint 去尾斜杠。
- 目录：① `/models` 404 非 JSON、④ `/v1/models` 对有效 key 401（坑 136）→ `/models` 404/401/403 都再发最小补全定论；退回静态目录，收两种拼写（`5-0` 与 `5.0` 同一代、六位日期不是次版本、lite 三种拼写）；非法 `size` 零成本探测（400 = 支持，404 = 不支持，坑 81）。
- 模型裁剪：对话只 `doubao-seed-2.0-pro`（别名 `ark-code-latest`）、2.0-lite／2.0-mini／2.1-turbo；Seed 1.6 系 404 `UnsupportedModel`；出图 5.0 pro／lite 四种拼法收，flash 三种拼法 404。
- 思考：① 用 `reasoning_effort`（挂千问的 `enable_thinking:false` 被忽略照样计费，坑 114）；豆包 2.1 `reasoning_content` 只是摘要、原文在 `encrypted_content` 不回传多轮越做越差（坑 133）；④ 2.1 带签名但不校验，丢／改坏照样 200（坑 137）。
- 温度：④ 关思考时听温度，`0` 等于没发（`0.01` 才收敛）、开思考带温度 200 不收敛（坑 198、201）；① 面 `0` 生效。
- 结构化：① `json_schema` + `strict:true` 2.1-turbo 2/2 守、不带 `strict` 1/2 越过；2.0-lite ①② 都不守 200；2.0-mini ① 守、② 多字段（坑 134）→ 只放 2.1 系前缀。
- 服务端工具：② `{type:"web_search"}` 三款都跑、不写 `sources:["doubao"]` 也记 `doubao`；④ `web_search_20250305` + `max_uses` 真跑，结果 `url` 为空串；① 无（厂商页只列 ②④）。
- 多模态：读图 ① `image_url`（data URL）、④ `image` 块；PDF ①②④ 都读；`file_url` 三面都通（推翻旧写法「`file_url` 仅 ② 只可能在按量 base 上用」）；`file_id` ①② 假 id 404 `ResourceNotFound`、④ `source.type:"file"` 400；① 收 `video_url`、`fps` 在 4 秒片段上不改账单（两种拼法都无效，未定论，坑 208）。
- 无 Files API：`/api/plan/v3/files`、`/api/plan/files`、`/api/plan/v1/files` 列表／上传／检索／删除全 404；Seedance 404。
- 上限：上下文 256k；`max_tokens` 2.0-mini 两族 ≤ 131,072、2.1-turbo 收 262,144，超了 400 报上限。
- 条款：文本模型「不可用于 API 调用，在非 AI 工具中使用……可能被识别为滥用」。

### 智谱 BigModel · 按量标准端点（`/api/paas/v4`）

- 11 个对话模型实测（glm-4.5／4.5-air／4.6／4.7／5／5-turbo／5.1／5.2／5.3／5.3-flash／5.3-flashx）【实测 2026-09-19】。
- 思考按代三种：4.x／5.0／5.1 只开关（`reasoning_effort` 丢弃）、5.2 只 high/max 折档、5.3 low/high/max 且关不掉（坑 94、95）；关思考发 `thinking:{type:"disabled"}`；按族默认在 11 款上全错，必须按模型 id 预填。
- tool_choice 砍档第三种变体：文档「默认且仅支持 `auto`」；`required`／具名 200 不强制（坑 97）；4.7／4.6／4.5 思考开时具名 400 `1210 API 调用参数有误`（文案不提 tool_choice，「从 400 学降级」失效，坑 96）；4.5-air 真强制；`none` 5.3-flash 无视 → 平台级无条件 forced 降 `auto`。
- 结构化：`json_object` 无 "json" 字样照常出合法 JSON；`response_format:{type:"json_schema"}` 200 静默无视（回 ```json 代码块，坑 98）。
- 服务端工具：对话内 `tools[]` 项 `{type:"web_search", web_search:{enable:true, search_engine, search_intent?, search_result?, count?}}`，结果在顶层 `web_search[]`；默认意图识别、不搜却说搜了（坑 100）→ `search_intent:false`；`count` 无效；独立端点 `POST /web_search`（`search_query`、`search_engine`、`search_intent` 必填；`count` 四引擎都无视：std ~10、pro/sogou 恒 50、quark 10；`search_recency_filter` 三引擎无视）与 `POST /reader`（`return_format:"text"` 有损；目标 404 与主机不存在都 500 `1234 网络错误…请稍后重试`）。
- 错误：信封 `{"error":{"code":"1210","message":"…"}}`（业务码字符串、HTTP 状态另给）；`finish_reason` `sensitive`／`network_error` 必 throw、`model_context_window_exceeded` 按截断（坑 99）；「该模型始终思考，不支持关闭思考」覆盖 5.3 代所有非法思考参数；`temperature参数非法：限制数值范围[0,1]`；`max_tokens参数非法：限制数值范围[1,98304]`；未知顶层字段一律放过。
- 多模态：只有 5.3-flash／flashx 读图，其余 `image_url` 400；收 `video_url`、忽略 `fps`（更早的样本，型号与日期未标 ⚠ ⏳待复核，OQ-052）。
- 上限：`max_tokens` 上界 5.x／4.6／4.7 131,072、4.5-air 98,304、glm-4.5 实测 131,072（文档 96K）；上下文 5.3／5.3-flash(x)／5.2 1M、5-turbo 204,800、5.1／5／4.7／4.6 200K、4.5 系 128K。
- 🎤 `glm-asr`：限流码（16 §10.2）【实现】。

### 智谱 BigModel · Coding Plan 编程端点

- 同 host、同一把按量 key 全通：① `/api/coding/paas/v4`、④ `/api/anthropic`、② `/api/v1`；路径决定扣余额还是扣套餐，选错不失败只换一笔钱 → 必须分行，不挂进按量行线路菜单。
- 目录：② `/api/v1/models` 是 Codex CLI 目录形（`slug`、`context_window`、`supported_reasoning_levels`、`input_modalities`），只列 3 个（哪三个未给）；④ `/v1/models` Anthropic 形。
- 完整实测未覆盖（15 篇「尚未覆盖」）。

### Kimi（Moonshot）

- 输入里唯一事实：① `json_object` 不查 "json" 字样（与智谱同批实测）。其余按 §4「未知、需核实」。

### 3.2 云部署变体

### Azure OpenAI

- 同 body、换鉴权（`api-key` 头）与 URL（`/openai/deployments/{d}/...?api-version=`），模型标识不同，一个头救不了——要做是另一族不是 compat 选项；`api-version` 细节未覆盖。
- `finish_reason: "content_filter"` 代替错误码（多家网关同），几乎不带文本，必须 throw（坑 7）。
- 辨识：New API 里 `[Azure]` 档是带护栏的网关（回显 `instructions` 里有「System integrity addendum」），不是 Azure OpenAI；OrcaRouter ② 默认线路上 terra 的 reasoning `format` 是 `azure-openai-responses-v1`（上游 Azure）。

### Vertex AI

- 经 OrcaRouter ③ 线路看到的是 Vertex 原样：`createTime`、`usageMetadata.trafficType:"ON_DEMAND"`、`responseId`、`modelVersion`、`thoughtSignature`。
- 网关重序列化后仍由 Vertex 校验枚举：`thinkingLevel:"BOGUS"` 回 Vertex 原文 400；`MINIMAL` 400 `Thinking level MINIMAL is not supported`（3.8 Flash；3.1 Pro 亦无，坑 170）→「关闭」映射 `LOW`。
- 缺签名：HTTP 400 `Function call is missing a thought_signature in functionCall parts`（不是 200 + `MISSING_THOUGHT_SIGNATURE`，坑 173）；流末 `{text:""}` 回灌 400 `required oneof field 'data' must have one initialized field`（是 Vertex 本身还是网关把空串丢成 `{}` 未定，坑 172）。
- 图片字段 snake_case／camelCase 两种都收（对比 New API ③ 面只认 camelCase）。
- Claude 部署变体只有【文档】。

### AWS Bedrock（Claude 正向）

- 经 New API AWSb 渠道测得：消息 id `msg_bdrk_`；参数／签名校验与官方同文 400；思考真分档；`output_config.format` ✅；PDF ✅ citations ✅；URL 图片 400；任何 Anthropic 服务端工具（`web_search`／`web_fetch`／`code_execution`）400 `Input tag 'web_search_20250305' … does not match`——整条请求失败 → 正向渠道也要点名。
- Bedrock Converse（camelCase、SigV4）是第五种独立 body——接它是新族，body 未覆盖（§4）。

### 3.3 聚合网关

### OrcaRouter（网关共性）

- 一把 key、一份目录、四面同一主机：① `/v1/chat/completions`、② `/v1/responses`、③ `/v1beta/models/{model}:generateContent`／`:streamGenerateContent`、④ `/v1/messages`；一族一行，Bearer。
- 目录：`GET /v1/models` Bearer 回 OpenAI 形（203 条）、`x-api-key` 回 Anthropic 形、`/v1beta/models` 回 Gemini 形；标定值从目录抄：GPT-6 astra／luna／sol 与 GPT-5.6-terra 1,050,000 / 128,000，Claude Fable 5.1／Opus 5.5／Sonnet 5 1,000,000 / 128,000，Gemini 3.8 Flash 1,048,576 / 65,536；八个 `input_modalities` 都含 `file`；只对测过的路径算实测，经 ① 翻译层的 PDF 只算推断。
- `supported_endpoint_types` 两方向证据：OrcaRouter 声明了没有却能打（`gpt-6-luna`／`-sol` 只声明 `openai`，② 200），New API 声明了却不许——不能当线路开关（坑 166）。
- 请求侧不是透传：解析成它认识的结构再重新序列化，未知字段与非法枚举常 200；06 §8 第 10 条「非法参数分类法」在此失灵（④ 乱写 200 却是 Anthropic 原样，坑 174）→ 按面用透传证据判后端；「发 X 会不会 400」只记网关注记。
- 错误信封全改写成 OpenAI 形，带 New API 指纹（④ `type:"<nil>"`、③ `type:"invalid_argument"`），路径 `***.***.content.0` 被遮；上游 5xx 改 `api_error` + `The upstream provider is temporarily unavailable`；文档说的 `claude_error`／`gemini_error` 一次没出现（坑 177）。
- 响应头只有 `x-orca-request-id`、`x-orca-version`、`x-orca-route: model=…; fallback=0`（文档没写），不漏任何上游头。
- 402 `insufficient_user_quota` 先于模型解析（【实测 2026-09-03】）；免费档具体模型／限制未给。
- 计费：唯一被声明为「报的数 = 实扣」的平台（06 §1 第四种口径），四个适配器带 `X-OrcaRouter-Include-Cost: true`；与 `GET /v1/generation?id=` `total_cost` 对过（④③ 相等，①② 差不到一个计价单位，按 1/500,000 美元取整；账单另有 New API 式 `quota` = 美元 × 500,000）；「贴受信网关标签却指向别的中转」用两道门（平台声明 + 请求地址推出的平台一致，坑 185）。
- 不做：不调计数端点、不按错误信封 `type` 判类（写注释不加分支）；起步模型钉线路要配守卫 `pinnableRoute`（坑 196）。

### OrcaRouter · ① 线路

- 翻译层（OpenRouter 形态）：`id:"gen-…"`、`provider:"OpenAI"`、`native_finish_reason`、`reasoning_details[]`（密文尾部解出 `endpoint_slug`）；GPT 上游再走 Responses——`reasoning_effort` + `tools` 同发 200 不能证伪「官方 ① 上 5.4+ 不能 effort + tools」。
- 跨族：Claude 思维链在 `reasoning_content`；Gemini 不返回思维链只报 `reasoning_tokens`；`response_format` strict `json_schema` 守住 enum（gpt-6-luna）。
- 服务端工具：`web_search_options` 200 但没有 `annotations`；发一个没有 parameters 的函数工具名 `googleSearch`／`urlContext`／`codeExecution` → 网关换成 Gemini 原生内置工具（网关约定）【文档 2026-09】。
- 视频输入：Gemini 发 `video_url` 200 静默丢弃、输入 token 25→25（坑 205）；GPT 400（坑 206）；PDF `file` 部件 ✅ 但读不读由网关翻译定，标定只算推断。
- 计费：末块 `usage.cost`（`cost_usd ?? cost`），流式没有 `cost_usd`；`is_byok`、`cost_details.upstream_inference_cost`；不需请求头。

### OrcaRouter · ② 默认线路

- 同一 OpenRouter 形态层：`gen-…` id、伪造 `msg_tmp_…`／`fc_tmp_…` item id、`summary:"auto"` 回显 `"detailed"`、`store` 恒 `false`；terra 的 reasoning `format` 是 `azure-openai-responses-v1`（上游 Azure）。
- 改写：`reasoning.effort` `minimal` → `low`（03 §7.1）；`"bogus"` 回网关自己的 `upstream_rejected_request`，原文被吞。
- 回灌义务测不出：`store:false` 下只回 id 的 reasoning item、篡改 `encrypted_content`、丢 reasoning item 全 200——网关多半改写了 `input`；官方规则不据此改口。
- 流：`reasoning` item 一次 added/done，只有 `encrypted_content`、`summary: []`，没有 `reasoning_summary_text.delta`（非流时 summary 有文本；Luna 是唯一流出可读推理摘要的线路）；并行 `function_call` 依次不交错；strict `text.format` 守住矛盾 enum；`input_file` PDF ✅。
- 计费：`response.completed.response.usage.cost`，不需请求头。

### OrcaRouter · ② 原样线路

- 触发：`store:true`，或 `include` 含 `web_search_call.action.sources`；`tools:[{type:"web_search"}]`、`include:["reasoning.encrypted_content"]`、`text.verbosity` 都不触发（坑 175）→ 不按 id 前缀或花费字段推断条目类型。
- 回包 OpenAI 原样：`resp_…` id、`billing`、`tool_usage`、`moderation`、`prompt_cache_retention:"24h"`、默认 `store:true`；`web_search_call` `in_progress`／`searching`／`completed` 齐全、`url_citation`。
- 没有任何花费字段，`X-OrcaRouter-Include-Cost` 头对 ② 无效 → 按表算；`usage.input_tokens_details.cache_write_tokens`（不是中转私有键，一次 `web_search` 4,388）。
- 其余能力（结构化、工具、思考回灌）在此线路未测。

### OrcaRouter · ③ 线路（Vertex）

- id 里斜杠原样进路径：`/v1beta/models/google/gemini-3.8-flash:generateContent`，不编码；不带 `alt=sse` 的 `:streamGenerateContent` 也回 SSE（官方是 JSON 数组）。
- 回包 Vertex 原样（见 3.2 Vertex）；请求重序列化：`generationConfig.fooBar` 200，枚举上游校验；`thinkingBudget:0` 想关、账单照样几百思考 token（可能网关把 0 丢了，坑 171）→ Gemini 3 只发 `thinkingLevel`；不设档位 ≈ 关闭，回退要 off + 提示（坑 203、204）。
- 工具轮：`functionCall` 带 `id`（`call_1626125`）；流末 `{text:""}` 回灌 400（坑 172）；缺签名 HTTP 400（坑 173）；`googleSearch`／`urlContext`／`codeExecution` 三项真跑、与函数工具／`mode:"ANY"`／`responseJsonSchema` 同发 200；代码 part 原样回灌 200。
- `:countTokens` 被当 `generateContent` 执行并计费 $0.0028（坑 176）。
- 错误信封改写：`{"error":{"message","type":"invalid_argument","param":"","code":400}}`，路径与 URL `***`。
- 计费：末块 `usageMetadata.costUsd` 需 `X-OrcaRouter-Include-Cost: true`（坑 186）；`googleSearch` 约 $0.014/条（一题 6 条 $0.084；改口自「一次 $0.028」，坑 178、190）；`toolUsePromptTokenCount` 在 prompt 之外（20+65+77=162）；PDF `inlineData`+`application/pdf` 一页按图计 520 token（坑 197）；16×16 图 1,098 token。

### OrcaRouter · ④ 线路

- 回包 Anthropic 原样（`msg_011C…`、不透明 base64 `signature`、`usage.cache_creation` 分项、`service_tier`、`inference_geo`、`stop_details`、`context_management`）——Claude 5 系事实以此为据记进 03–06。
- 请求重序列化：顶层 `foo:1`、`thinking.type:"bogus"`、`output_config.effort:"bogus"`、`output_config.foo` 全 200（官方 400）；同一 schema 官方 400 经此 200（坑 182）；整块丢 thinking block 200（与官方「缺失 → 静默降级」一致，是印证）；改签名 400。
- `/v1/messages/count_tokens` 301 到官网首页（坑 176）；`tool_use` 多 `caller:{"type":"direct"}`（去掉回灌也 200）；`output_config.format` 五个型号守 enum、与思考／工具／强制工具／流式同用。
- 计费：流式 `message_delta.usage.cost_usd` 需 `X-OrcaRouter-Include-Cost: true`，`message_start` 快照里没有（坑 186）；`web_search_20250305` 无 beta 头、`usage.server_tool_use:{web_search_requests:1, web_fetch_requests:0}`、没发 `cache_control` 也记 2,834 `cache_creation_input_tokens`（坑 179）、一请求合计 $0.051；`usage.output_tokens_details.thinking_tokens`（22 = 21+1）；PDF Sonnet 5 未打断点也记缓存写 1,630（Opus 5.5 无，坑 197）。

### OpenRouter

- 本库只有【文档】：① 面；`/models` 带 `context_length`；SSE 体内 `data:{"error":...}` routinely（坑 6）；① 回 `usage.cost` 等（平台未受信前不收，坑 185）。
- 所有「OpenRouter 形态」指纹都是在 OrcaRouter ①／② 默认线路上看到的，不是对 OpenRouter 本身的实测。

### 3.4 自建中转 New API 类

### New API 类中转站（平台层／转换层）

- 无可识别 host，不手选平台时落 `custom`；两台样本只靠编号区分（第八 vs 第十／十五／十六／十七）。
- 转换层缺口（同台四渠道一致，按平台 × 面裁决，不进渠道画像）：Claude ① `response_format`（`json_object`／strict `json_schema`）被丢、`reasoning_effort:"max"`／`"none"` = 不想（坑 140、142；「扩到整台」【未实现】，参考实现只点名 Kiro）；GPT ① 四档响应 id 都是 `resp_…`、流里 `reasoning_content`、`web_search_options` 四档静默忽略（坑 164）、顶层 `verbosity` 无效。
- ③ 面只认 camelCase：snake_case 图片字段与系统提示被无视（坑 2、111）。
- 接收侧畸形：`arguments` 多对象拼接（坑 105）、空串调用 id（坑 106）、同 delta `reasoning_content:""` 盖住 `reasoning`（坑 107）、usage 末块 `choices:[]`（坑 108）、`content` 数组形；经 chat 出图一张图存成三个文件或没存（坑 92）、出图模型经 chat 路由 400 `images[0] must be an http/https URL`（坑 110）、改图 `image` vs `image[]`（坑 93）。
- URL 图片：中转站计 token 前自己下载，拒爬主机 500 `count_token_failed`／400／流内 `error` + 空答（坑 167）→ 图片一律内联 base64。
- 探测：`supported_endpoint_types` 不开线路；503 `No available channel for model … under group …` 报成「这档没线路」不报模型名错误；402 报不可达（坑 112、166）。
- 上游数据化：渠道前缀是站主起的名字，上游产品名（kiro、bedrock）可推断，站主缩写（CC／anti／AWSb／官key）永不推断、只进作者的表（坑 152）；解析顺序 手选（含 `"none"`）> 前缀表 > 产品名推断；每个问能力处经同一 `capabilityModelOf`（坑 153–158、168）。
- 计费：中转站估算 usage 总数可用、缓存分段不可信；`usage.attribution.request_fields.instructions.input_tokens` 是注入读数（发 10 报 4,380）；无此字段时用「Say OK.」对照输入 token。
- 代码侧通用对策只有两条：② adapter 恒发 `instructions`（网关上游按 `instructionsField` 裁决改发 developer 消息）、终止响应回显比对（坑 61）；没有按中转站名的分支；不加剥档位前缀规则。

### New API · Kiro 渠道（Claude）

- 前缀 `[kiro]` `[kiro1]`…`[kiro3]` `[kiro-200k]` `[特价kiro量]`；后端非 Anthropic API；两款模型（opus-4-6／opus-5）每条一致、usage 逐字相同；Sonnet 按推断收进名单（有意例外）。
- 只开 ① 与 ④：`/v1/responses`、`/v1beta` 回 500 `convert_request_failed`「not implemented」；① 先翻成 Messages 再发（`usage.billing_usage.source:"claude_messages"`）；`/v1/messages/count_tokens` 404 `Invalid URL`；`/v1/files` 401；不带 `anthropic-version` 也 200；`x-api-key` 与 Bearer 都收。
- 目录：`supported_endpoint_types` 一律 `null`；回显去掉档位前缀；不存在的模型 503 `model_not_found`「No available channel for model … under group default」（不是 404）。
- 反代特征：`effort:"bogus"` 一律 200；无参数／签名校验；缺口几乎全 200 不报错。
- 静默行为逐条：`max_tokens`（① 还有 `max_completion_tokens`）无视、`stop_reason` 永不 `max_tokens`（坑 65）；思考只 low 有效、`display` 无视、`budget_tokens ≥ max_tokens` 也 200（坑 141）；`output_config.format`（GA）／`output_format` + beta 头都 200 忽略、① `response_format` 忽略（坑 142）；强制 `tool_choice` 只在非流式转换路径实现——流式 `{type:"any"}`／`{type:"tool"}` 无视（32 次 1 次），非流式关思考 16/16、开思考 `tool` 0/8、`any` 6/8，复测带思考 0 次、不带思考流式 5 次 3 次（时好时坏，坑 138）→ 点名 id 上 forced 一律 `auto`；单挂 `web_search_20250305`／`_20260209`（流式与否）整条劫持：第一条 user 原文当搜索词、0.8–2 s 返回模板「I'll search for "…"」+ `server_tool_use` + `web_search_tool_result`，模型没跑；+ 函数工具 + 流式 → 真搜；+ 函数工具 + 非流式 → 丢（坑 139）；`web_fetch_20250910`／`code_execution_20250825`／乱造 type → 200 丢弃且模型假装执行（`<h1>Example Domain</h1>`、没跑的 Python，坑 144）；① `web_search_options` 转成 ④ `web_search` 后同样劫持；PDF（④ `document`／① `file`）与 URL 图片丢、base64 图 ✅（坑 143）；不注入系统提示（不带 system 输入 ~70 token）。
- 劫持指纹：两款模型逐字相同、`output_tokens` 固定 644/568/478、`encrypted_content` 是明文摘要、`page_age` null。
- 计费：`cache_control` 只写不读——同一 7.4k 前缀连发两次都报 `cache_creation_input_tokens:7360`、`cache_read` 永远几十，打断点比不打更贵（坑 145）；不带 `cache_control` 也固定报几十 `cache_read_input_tokens`；`message_delta` 报 `cache_creation:{ephemeral_5m_input_tokens:265}`；同一请求流式 `prompt_tokens` 301、非流式 102；「Say OK.」输入 7 + 拼的缓存段。
- 「只在本轮带函数工具时发 `web_search`」的按请求判定【未实现】。

### New API · CC 渠道（Claude）

- 前缀 `[CC量]`，推测 Claude Code 通道，未证实；证据等级 curl 实测（无 live adapter 文件）。
- ④：思考 ✅ 但 opus-5 thinking 文本恒为空（按思考计费面板永远空白，坑 149）；`effort` 分不开；无参数／签名校验一律 200；`max_tokens` ✅；强制 `tool_choice` 不带思考非流式／流式全调用、带 adaptive 思考非流式 3/8、流式 4/8 时好时坏 → 不判不发；`output_config.format` opus-4-6 无视（散文）、opus-5 执行（各 2/2，点名细到模型）；PDF ✅；纯文本 `document`+`citations` 读到但无 citations；URL 图片丢；`web_search` 单挂 ✅ 真搜（要求搜才搜，改写句子请求不触发不劫持）、+ 函数工具流式 ✅；`web_fetch_20250910` ✅ 有 `server_tool_use` 块；`code_execution_20250825` 丢、没有块。
- ①：`response_format` 丢（转换层）；`web_search_options` ✅ 答案引了搜索结果；PDF ✓。
- 计费：缓存是真的（第二次 `cache_read` = 前缀）；「Say OK.」9–10 token。

### New API · anti 渠道（Claude）

- 前缀 `[anti量]`，推测 Antigravity，未证实；curl 实测。
- ④：不思考（`-thinking` 变体也不，坑 148）；无校验一律 200；`max_tokens` ④ 生效；强制 `tool_choice` 两条路径都不实现（0/0，第五种变体）→ 降 `auto`；`output_config.format` 无视；PDF 丢、纯文本 document 也丢；URL 图片 500；`web_search` 单挂丢（凭记忆答「As of my latest information (July 2025)…」）、+ 函数工具流式丢、`web_fetch` 丢、`code_execution` 丢。
- ①：`response_format` 丢；强制非流式 5 次 1 次、流式 0；`web_search_options` 无效；`max_tokens` ① 无视（同渠道两面转换不同，坑 151）。
- 计费：没有任何缓存字段、两次都全价；「Say OK.」不带 system 报 39（别的渠道 9–10）——渠道自己注入约 30 token 提示（坑 151）。

### New API · AWSb 渠道（Claude，Bedrock 正向）

- 前缀 `[正向AWSb量]`；消息 id `msg_bdrk_`；curl 实测。正向：`effort:"bogus"` 400 官方原文、校验签名——但正向 ≠ 官方。
- ④：思考 ✅ 真分档；`max_tokens` ✅；强制 `tool_choice` ✅/✅；`output_config.format` ✅；PDF ✅ 有 citations；URL 图片 400；`web_search_20250305` 单挂／+ 函数工具／`web_fetch`／`code_execution` 全部 400 `Input tag 'web_search_20250305' … does not match`（整条请求失败）；`cache_control` ✅。
- ①：`response_format` 照丢（④ 面执行 schema、① 丢——同渠道同模型结构化随面不同，坑 150）；强制 ✅；`web_search_options` 400；PDF ✓。
- 目录里 `[AWSb]gpt-5.6-sol` 503 `No available channel`（GPT 在此档无线路，坑 166）。

### New API · 官key 渠道

- 前缀 `[官key量]`；当天 ①④ 两个端点全部 502 `Upstream request failed`，没测到；画像 official 无任何格子，选它只表示「已分类」。
- `[官key]gpt-5.6-sol` 目录有但 503「No available channel」——是「当时没线路」，是否长期如此未知。

### New API · `[特价Pro]` 档（GPT）

- ChatGPT 账号池／Codex 后端，画像 codex；与 `[Plus]`／`[Pro]`／`[Azure]` 同台同 key（第十七个样本）。
- 目录声明 `supported_endpoint_types` 含 `anthropic`／`gemini`，打 `/v1/messages` 回「This group does not allow Anthropic Messages requests」——目录不可信。
- ②：带 `instructions` 「Say OK.」19 token 不注入；不带则时有时无（0 或 +11）；同一档注入量 0／11／296／4.4K／17K 五种，延迟 3 s 到超时——一档之内不是一个账号（坑 165）；`reasoning.effort` 真分档（low 295–428 / xhigh 583–588 `reasoning_tokens`）；`none` 关不掉（回显 `medium`，坑 161）；乱写 effort → 流式 `response.failed`（`upstream_error`）；`reasoning.mode:"pro"` 回显 `standard`；`temperature:0.5` 200 回显 `1.0`（坑 162）；`max_output_tokens:16` 无视、`status:completed`（坑 65）；`text.format` json_schema 省略／显式 strict 都 ✅、`json_object` ✅；`text.verbosity` 生效；`web_search` 真搜（1 次 `web_search_call` + `url_citation`，6–10 s，输入 8.5–14K）；`code_interpreter`／`file_search` 流式 `response.failed`；`image_generation` 403 `Image generation is not enabled for this group`；`store:true` 200；`input_image`（data/http）、`input_file` PDF（`file_data`／`file_url`）✅；URL 图片拒爬主机流里 `error` 事件后接空答（200）。
- ①：带 system 仍注入 4,397（多数请求）；`reasoning_effort:"none"` 关不掉；`max_completion_tokens:16` 无视；`response_format` strict ✅；具名 `tool_choice` ✅；`web_search_options` 静默忽略；`reasoning_effort:"bogus"` → 流里「Upstream service temporarily unavailable」；顶层 `verbosity` 无效。
- 计费：`usage.attribution.request_fields.instructions.input_tokens` 读注入量（作者没发却记 4,380）；前缀缓存 `cached_tokens` 9,984（同一 10K 前缀）。
- 画像 codex：② `instructionsField` ✓ 恒发（不发则注入 4.4K）、`temperature` ✗（回显 1）、`textVerbosity` ✓、`web_search` ✓、`pdfInput` ✓、强制工具 ✓；① 温度不写格子。

### New API · `[Plus]` 档（GPT）

- 账号池 codex。②：不带 `instructions` 注入 4,389（`attribution.request_fields.instructions.input_tokens: 4380`）；乱写 effort → 502 `Upstream request failed`；`code_interpreter`／`file_search` 502；`image_generation` 403；json_schema 省略／显式 strict 都 ✅（第八个样本那条「显式 strict 丢」在 Plus 上未复现）；`json_object` ✅；`temperature:0.5` 回显 `1.0`；`store:true` 200；`web_search` ✅；其余同 `[特价Pro]`。
- ①：带 system 3/3 注入 4,395；`response_format` strict ✅；具名 200；`web_search_options` 忽略；`reasoning_effort:"bogus"` 502。

### New API · `[Pro]` 档（GPT）

- 账号池 codex——校验与官方同源（乱写 effort 400 `Invalid value: 'bogus'. Supported values are: 'none', 'minimal', …`）却是唯一丢结构化输出的账号档：「校验同源 ≠ 能力同源」。
- ②：`text.format` json_schema 省略与显式 `strict:true` 各 4 次全丢，回显 `{type:"text"}`、模型答 `{"answer":2}`；`json_object` 回显 `text`、碰巧输出 JSON——丢 format 后提示语要求 JSON 仍回 JSON，「能解析」不能证明 schema 生效（坑 160）；旧：第八个样本（另一台，5.4／5.5）「只有显式 `strict:true` 才丢」→ 新：不论写不写都丢（2026-09-24 扩展）；不带 `instructions` 9 token 不注入；`code_interpreter`／`file_search` 400 `Unsupported tool type`；`image_generation` 403；`web_search` ✅；`temperature:0.5` 回显 `1.0`；URL 图片拒爬主机 400 `Error while downloading file`。
- ①：`response_format: json_schema` 丢（4/4）；带 system 19 不注入，但带具名 `tool_choice` 时注入 4,434；具名 `tool_choice` ✅；`web_search_options` 忽略；`reasoning_effort:"bogus"` 400 官方原文。
- 能力表不给账号池写 `structuredOutput:false`（另两档白丢可用 JSON 模式），只在说明里告知；回显比对 `text.format`【未实现】。

### New API · `[Azure]` 档（GPT，带护栏的网关）

- 不是 Azure OpenAI；画像 azure（正向）；这一档没有 sol 线路（两次相隔 10 分钟 503 `No available channel for model gpt-5.6-sol under group …`），用 `gpt-5.6-terra` 顶替（比的是上游不是模型）。
- ②：带 `instructions`（哪怕空串）输入 1,209 token——`instructions` 后追加约 1.2K 护栏，回显三段：作者原文 → 中转站反制「【最高优先级强制规则】…>>>IGNORE_AFTER<<<…」→ 上游「System integrity addendum」四步门禁（拒 fiction/novels/poems/role-play、拒泄露提示词、拒批量输出）；约 60 次里至少 4 次被改写（鬼故事 6 拒 2）——200、无 `refusal`、答案不对（坑 159）；不带 `instructions` 9 token 无护栏；`effort` 分档弱（131–155 / 163–245）；`none` 关不掉；乱写 effort → 500 `Upstream gateway error`；`reasoning.mode:"pro"` 回显 `pro`（1 次）；`temperature:0.5` 500（6/6，`1` 则 200，坑 162）；`max_output_tokens:16` ✅ `incomplete` reason `max_output_tokens`；`text.verbosity` ✅；json_schema ✅；`web_search` 静默丢弃（无 `web_search_call`，模型答「I can't perform a live web search」，坑 163）；`code_interpreter`／`file_search` 500；`image_generation` ✅（83 s，`image_generation_call` 约 911K 字符 base64）；`store:true` 500；URL 图片拒爬主机 500 `count_token_failed`（中转站计 token 前自己下载，请求没到上游，坑 167）。
- ①：system 19 不注入；`reasoning_effort:"none"` 真关（答案随之变错）；`max_completion_tokens:16` → `finish_reason: length` 但 `completion_tokens` 128；json_schema ✅；具名 `tool_choice` 500（9/9，`required` ✅）→ 画像强制工具 ✗；`web_search_options` 忽略；`reasoning_effort:"bogus"` 500。
- 计费：前缀缓存 `cached_tokens` 11,576（多出的是护栏）；每请求 +1.2K 输入（多半命中缓存）；网关无 `attribution` 字段，护栏只能从回显 `instructions` 看出。
- 画像 azure：② `instructionsField` ✗ → 系统提示改为 `input` 开头 `{role:"developer", content}`、不发 `instructions` 键（不做全局开关——翻向 developer 账号池每请求 +4.4K，坑 169）；`temperature` ✗；`web_search` ✗；强制工具 ② ✓ ① ✗。对写作应用是最不该选的档。

### New API 中转站（另一台）· `[Pro]`／`[Plus]` 档（第八、第十个样本）

- base 未给；GPT-5.x 档位（5.4／5.5 第八个样本；5.6 sol／terra 第十个样本）。
- 四种静默行为（01 §9.2 第 1–4 条）：不发 `instructions`（system）注入 Codex 系统提示 4.4K–9K 输入 token，Chat 面同样注入（坑 62）；改写 effort／temperature：sol 发 `max` 回显 `none` 且 0 推理 token（2026-09-24 另一台四上游未复现，按「当时当档」理解）、terra 发 `none` 两次都回显 `medium` 且照样推理（全部复现）、`temperature:0.5` 回显 `1.0`（坑 61）；其中一台无视 `max_output_tokens`，截断状态永远不出现（坑 65）；一个档位背后多个上游，同一请求响应形状时有时无回显字段。
- 第八个样本：GPT-5.4／5.5 显式 `strict:true` 才丢 `text.format`（旧结论，被 2026-09-24 同台 `[Pro]` 扩展，坑 63）。第十个样本：搜索 112 s（比第十七个样本慢一个量级）；改写随时间与上游出现又消失，比对要常开。


### 未具名中转（Claude 后端，Joycai 线上流量）

- ① 面：`arguments` 先吐空对象占位再给真参数 `{}{"id":1}`（按括号深度切、左到右合并，坑 105）；调用 id 是空串 `""`、同批两调用共用 → 下一轮重复 `tool_call_id` 400、整段会话此后每轮 400（空串按缺失处理、按序号补 id，坑 106）。

### Midjourney（midjourney-proxy／New API `/mj/*`）

- 独立异步出图协议（`/mj/submit`）；只有【实现】口径，地址／目录／计费全 ⚠；详见 13 §2、§4.2「midjourney」。

### 3.5 本地运行时与 ASR 专营

### Ollama

- 鉴权：无 key 时整个 `Authorization` 头省略（收到空 Bearer 会拒）；Windows 打包版 403 靠 http 层覆盖 `Origin` 头修复（按「URL 指向本机」判断，Ollama 不做成枚举值）。
- 超窗从头部静默截断 prompt、200 + system 指令没了（坑 5）→ 发送前 `ContextSizeError` 估算拦截 + 探测 truncation check（快测 8k）+ 读实际 `num_ctx`。
- `/api/show`：`model_info` 与 `parameters` 常差 30 倍，小的才算数；`num_ctx` 默认 2048/4096 静默截断。
- JSON cue 追加成单独 user 消息 → chat 模板错误（坑 211）→ cue 接在最后一条 user 消息末尾。
- 兼容层 `stream_options.include_usage` 可能没实现、usage 全 0（坑 8）。

### LM Studio／llama.cpp

- LM Studio `/models` 带 `max_context_length`；llama.cpp `/props`；`max_model_len` 置 high（探测 finding confidence high）。
- 两条连续 user 消息在严格交替 chat 模板上报错（坑 211）；超窗静默截断同 Ollama（坑 5）。

### Groq／硅基流动（仅 ASR）

- ⓐ OpenAI 兼容转写（multipart），地址与硅基流动 SenseVoice 语种在 16 §3；【实现】口径，OpenAI 兼容 ASR 无实测；chat 面未覆盖（§4）。

### 火山引擎 openspeech（豆包录音识别极速版）

- 与火山方舟 `ark` base 无关：host `openspeech.bytedance.com`、独立鉴权头；成败在 `X-Api-Status-Code` 头、HTTP 恒 200、缺头按失败（坑 122）【实现】。

### ASR 专营：Deepgram、ElevenLabs、CAMB AI、Gladia、小米 MiMo、302.AI

- 各自 SDK／私有协议，16 §10.2 渠道速查表；【实现 2026-09，原 pyVideoTrans】；流式／实时 ASR（WebSocket）本库没有。

---

## 4 本表尚未覆盖的平台

以下平台在 `15-vendor-index.md`「本库尚未覆盖」列出（或本表只有零星一条事实），一律按「未知、需核实；先按 01 §2 判族，再用该族底座的全部检查项去审；厂商特有的不从相邻厂商类推；核实后按 SKILL.md「维护知识库」写回并补进本表」处理。

- Kimi／Moonshot：未知、需核实；先按 01 §2 判族（本表 Kimi 行仅一条 `json_object` 事实）。
- 智谱 GLM 的图像／视频模型：未知、需核实；先按 01 §2 判族。
- 智谱 Coding Plan 编程端点的完整实测：未知、需核实；先按 01 §2 判族（本表只有「按量 key 200、扣套餐」）。
- Mistral：未知、需核实；先按 01 §2 判族。
- Cohere：未知、需核实；先按 01 §2 判族。
- Groq 的 chat 面：未知、需核实；先按 01 §2 判族（本表只有 ASR 面）。
- 硅基流动的 chat 面：未知、需核实；先按 01 §2 判族（本表只有 ASR 面）。
- Together：未知、需核实；先按 01 §2 判族。
- Fireworks：未知、需核实；先按 01 §2 判族。
- Bedrock Converse 的 body：未知、需核实；先按 01 §2 判族（第五种 body，要么写第五个 adapter 要么明确不接）。
- OpenAI 兼容 ASR 的实测（16 §3 全是文档与实现口径）：未知、需核实；先按 01 §2 判族。
- 流式／实时 ASR（WebSocket，本库没有）：未知、需核实；先按 01 §2 判族。
- Azure 的 `api-version` 细节：未知、需核实；先按 01 §2 判族。
- Seedance 视频（火山方舟套餐不含，实测 404，需按量 key；body 形状未覆盖）：未知、需核实；先按 01 §2 判族。
- OpenAI 官方收不收 ① `video_url`（02 §1 表后，未量）：未知、需核实；先按 01 §2 判族。
- 火山方舟按量付费收不收 ① `video_url`（未量；按量对话面整体未实测）：未知、需核实；先按 01 §2 判族。
