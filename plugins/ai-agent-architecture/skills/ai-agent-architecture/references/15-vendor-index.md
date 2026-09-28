# 15 · 厂商索引：每家的事实散在哪里

这是一张目录，本身不写事实。审查或接入某一家时，先在这里找到它，再把列出的小节全部读一遍。
一家的事实通常分散在五六篇里：协议差异一篇、思考一篇、错误一篇、出图一篇……只读一篇，就会漏掉另外几个维度。

**先看结论表再看正文**：每家的结论已汇成矩阵——平台本身（面、地址、目录、手脚、计费）在 `20-platform-matrix.md`，模型 × 平台 × 面的能力在 `22-model-capability-matrix.md`，出图 / 视频 / ASR 在 `23-media-matrix.md`；没测过的组合在 `31-open-questions.md`。本表的「事实所在」列指向正文小节，用来看原因与报文。新增一家时本表、20 §2 / §3、22 各家族节都要加行（流程见 `30-knowledge-ingestion.md` §3）。

「证据」一列用 SKILL.md 定义的记法，是那几节里标注的最近来源。没标日期的，按「文档口径、日期未知」对待。

## 协议族（与厂商无关的底座）

| 族 | 端点形状与差异 | 思考 | 结构化 | 工具 | 错误 / usage | 坑 |
| --- | --- | --- | --- | --- | --- | --- |
| ① Chat Completions | 02 §1、§3、§4、§5；视频片段 `video_url` 是厂商扩展、按平台放行（02 §1 表后） | 03 §2、§4–6 | 04 §2–4 | 05 §1–3 | 06 §1–2、§9（按 400 学降级） | A、B、AA、AB 组 |
| ② Responses | 02 §7（请求骨架 / 事件 / 回传；`instructions` 与 developer 消息按上游裁决）；01 §3.1 为什么独立成族 | 03 §7 | 04 §5 | 05 §1、§5「② Responses 族」、§7 | 06 §1（`attribution`）、§4.1 回显比对 | G、V 组 |
| ③ Gemini generateContent | 02 §1、§2.2、§3.2 | 03 §2–5（§2.1「关闭」只是 `LOW`） | 04 §2 | 05 §1–2 | 06 §2（三层错误） | A、B、Z 组 |
| ④ Anthropic Messages | 02 §1、§2.1、§3.2、§5 | 03 §2–5（§2.1「关闭」只是最低 effort；§3.4 开关型方言关思考时的温度） | 04 §2（JSON mode 只有 cue；schema 模式 `output_config.format`） | 05 §1–6（续跑循环） | 06 §1（三桶 usage） | A、B、Z 组 |

## 厂商与平台

| 厂商 / 平台 | 协议与面 | 事实所在 | 证据 |
| --- | --- | --- | --- |
| **OpenAI 官方** | ①、② 两张 chat 脸（部分模型只有 ②）；Images API；Sora 视频；`/audio/transcriptions` 转写 | 01 §8.1（Responses-only 模型）；02 §7（含 GPT-5.x 空 `final_answer` 收尾）；03 §7；04 §5；05 §5、§7；13 §2、§4.2「images-api」；14 §2；16 §3、§10.2（whisper / gpt-4o-transcribe / diarize）；坑 109。**经中转站的 GPT-5.6 按上游（ChatGPT 账号池 / 网关）的对照**见 New API 行：01 §9.2「同一个 GPT，两类上游」、03 §7.4、04 §5.1、05 §5「中转站上的 GPT」、06 §1 / §2 / §4.1；坑 159–169。**GPT-6（luna / sol / astra）经 OrcaRouter**：03 §7.1（`minimal` 被改写成 `low`）、04 §2（strict schema 顶住矛盾 enum）、05 §5（`web_search` 事件、`cache_write_tokens`）、06 §1；① ② 默认线路是 OpenRouter 形态翻译层，只有 ② 带 `store:true` 的线路是原样（01 §9.5） | 【实测 2026-09 经中转 + 文档；上游对照实测 2026-09-24；GPT-6 经 OrcaRouter 实测 2026-09-26】 |
| **Anthropic 官方** | ④；部署变体 Vertex / Bedrock | 02 §1、§2.1、§5；03 §3、§5；05 §5–7；06 §1；01 §2（Bedrock Converse 是另一族）；坑 1。**Claude 5 系（Sonnet 5 / Opus 5.5 / Fable 5.1）经 OrcaRouter 的原样回包**：03 §3（不发 `thinking` 也思考、`display` 默认 omitted）、§4（流形）、§5（改签名 400）；04 §2（`output_config.format` schema 模式：五个型号实测守 enum、与思考 / 工具 / 强制工具 / 流式同用、只有严格档、关键字限制、与 effort 合并）；03 §2（Opus 5.5 / Fable 5.1 拒收 `disabled`）；05 §3（`tool_use.caller`）、§5（`web_search_20250305` 无 beta 头、自动缓存）；06 §1（`thinking_tokens`、`server_tool_use`）；02 §1 表后（PDF：Sonnet 5 未打断点也记缓存写入）；03 §2.1（Sonnet 5 的「关闭」= effort low，省约三分之二，off + 提示最省）；坑 4、179、180–184、197、203、204 | 【文档；Claude 5 经 OrcaRouter 实测 2026-09-26；思考回退 2026-09-28】 |
| **Google Gemini** | ③ chat（同一 wire 也出图）；Imagen `:predict`；Veo 视频 | 02 §2.2、§3.2；03 §2–5；06 §2；13 §2、§4.2「imagen」；14 §2。**Gemini 3.8 Flash（Vertex 后端，经 OrcaRouter）**：03 §2（`MINIMAL` 400、「关闭」→ `LOW`、`thinkingBudget:0` 关不掉、各档思考量）、§4、§5（缺签名 HTTP 400、签名位置）；02 §2.2（`functionCall.id`、两种图片拼写、16×16 = 1,098 token）；04 §2（`responseJsonSchema` / `responseSchema` 都守 enum）；05 §3（流末空 part 回灌 400）、§5「③ Gemini 的内置工具」（`tools[]` 独立项、与函数工具 / `ANY` / `responseJsonSchema` 同发都 200、回报位置、搜索按条约 $0.014、代码 part 回灌、日志 id 前缀）；06 §1（`trafficType`、`toolUsePromptTokenCount` 在 prompt 之外、检索费）；02 §1 表后（PDF 一页按图计 520 token；经 OrcaRouter ① 发 `video_url` 被静默丢弃）；03 §2.1（不设档位 ≈ 「关闭」，回退要 off + 提示）；坑 2、170–173、176、178、190–195、197、203–205。经 OrcaRouter 测的是 Vertex，不直接照搬给 AI Studio（01 §9.5） | 【文档；3.8 Flash 经 OrcaRouter 实测 2026-09-26；思考回退 / 视频 2026-09-28】 |
| **xAI Grok** | ②（官方推荐；① 已标弃用）；Grok Imagine 出图（2.0：`quality` low/medium、`resolution` 1k/1.5k/2k、`usage.cost_in_usd_ticks` 报实扣；初代平价）/ 视频（1.5：$0.08/s，首帧与参考图各 +$0.01/张，done 回包报 ticks，`video.duration` 报实际秒数） | 01 §9.1；03 §7.1、§7.3；05 §5「② Responses 族」、§7（tool search 403）；13 §4.2「xai-images」（质量 / 分辨率 / 定价端点 / 参考图上限纠错）、§7（报价、输入图按张）；06 §1（第四种口径）；14 §2「xAI 实测」、§3.8；02 §1 表后（① 不收 `video_url`：400 `Empty content block`，`grok-4.3`）；坑 66–67、123–129、206 | 【实测 2026-09-22 出图质量与计费、视频 1.5 计费；视频输入 2026-09-28；其余 2026-09】 |
| **DeepSeek** | ① | 03 §2（`none` 关不掉，要 `thinking:{type:"disabled"}`）、§5（回传义务分场景，两个方向都会 400）；04 §1–2；06 §1（缓存命中字段 `prompt_cache_hit_tokens`）；02 §1 表后（不收 `video_url`：422 点名可接受的片段类型，`deepseek-flash`）；坑 206 | 【文档 2026-08；视频输入实测 2026-09-28】 |
| **阿里百炼 / 千问 DashScope** | chat 三张脸（① 兼容 / 私有三段式 / ④）；出图同步 + 异步；视频异步；服务端工具；语音识别两张脸（同步 multimodal-generation / `-filetrans` 异步） | 01 §8.1、§8.4；03 §3、§7；04 §4（tool_choice 砍档）、§5.1；05 §5「代码解释器」；13 §4（含「自由尺寸的规则」）；14 §2（wan3 视频链路实测）；16 §4–§9；02 §1 表后（视频输入 `video_url` 的对照端点：`qwen3-vl-plus` 收、`fps` 生效；夹具太小 400 `Invalid video file`）；坑 9、10、13、56–59、70、74–78、101–104、115–121、206–208 | 【实测 2026-09-28 视频输入；实测 2026-09-19 出图信封与自由尺寸；实测 2026-09-17 服务端工具；实测 2026-09-13 ASR 两条路；实测 2026-08-29 视频；文档 2026-09】 |
| **MiniMax** | chat ① / ④ 两张脸（模型 id 相同）；`image-01` 出图；v2 视频任务；`<think>` 内联 | 01 §8.1、§8.3–8.4；03 §3、§6；05 §6；06 §2（`base_resp`）；13 §4.2「minimax」；14 §2（含 v2 视频实测）；03 §3.4（④ 关思考发温度：收下、不理会；开思考带温度 200 而非 400；类目 `minimax` 不发）；坑 6、11、90、91、113、199、201、202 | 【实测 2026-09-28 ④ 温度（MiniMax-M3，国内站）；实测 2026-08-29 视频全链路；其余文档 2026-08】 |
| **字节跳动火山方舟（豆包 / Seedream）** | ① ② ④ 对话（套餐三面；按量未测）；Seedream 出图（`ark` route，含流式、拆图层、透明背景；5.0 flash 只在按量）；按量 / 套餐两个 base；另有 openspeech 的录音识别极速版（独立鉴权头） | 01 §9.3（含套餐三面、套餐无 Files API、`file_url` 三面通）；02 §1（PDF 形状、`file_url` / `file_id`）；03 §3.2（三面思考控制、思考摘要与加密原文、④ 2.1 的签名）、§4、§5；04 §2（按模型守不守 schema）；05 §5（套餐 ②④ 联网搜索）；06 §5（④ `/models` 401）；13 §4.1（含「流式出图」「拆图层的实测形状」）、§7（`usage.input_images`、首张免费、失败免费）、§8；14 §2（Seedance 套餐 404）；16 §10.2（ASR，【实现】）；03 §3.4（Coding Plan ④ 关思考时听温度、`0` 等于没发、开思考带温度 200 而不收敛）；02 §1 表后（Coding Plan ① 收 `video_url`、读对画面，`fps` 在 4 秒片段上不改账单；按量未测）；坑 79–85、87、114、122、130–137、198–201、206、208 | 【实测 2026-09-18】；透明背景 / flash / 参数 400 / Files API 复测【实测 2026-09-23】；④ 温度与视频输入【实测 2026-09-28】 |
| **智谱 BigModel（GLM）** | ① chat 标准端点；同一把 key 另通 Coding Plan 的 ① / ② / ④ 编程端点（路径决定计费）；独立的网络搜索 / 网页阅读端点；`glm-asr` 转写 | 01 §9.4；03 §3.1；04 §2（`json_schema` 静默无视）、§4（砍档第三种变体）；05 §5「服务端工具归平台」；06 §2（`sensitive` / `network_error`、笼统文案）；16 §10.2（GLM-ASR 限流码，【实现】）；02 §1 表后（收 `video_url`、忽略 `fps`）；坑 94–100 | 【实测 2026-09-19，11 个对话模型】 |
| **New API 类中转站** | ①、②、③、④ 形状都有（按渠道；Kiro 渠道的 Claude 只开 ① ④，② ③ 回 500 `convert_request_failed`）；`/mj/*` Midjourney | 01 §9.2（四种静默行为；Kiro 渠道与「按模型 id 只点名」的能力裁决；同一模型 Kiro / CC / anti / Bedrock 四个渠道的对照；「上游做成作者声明的数据」：解析顺序、内置画像、合并优先级、提示与资格同一裁决、实测与离线测试怎么做；「同一个 GPT，两类上游」：ChatGPT 账号池（`[特价Pro]` / `[Plus]` / `[Pro]`）与带 `instructions` 护栏的网关（`[Azure]`）逐项对照、注入量随账号变；「上游画像扩到 GPT」：codex / azure 两格、`instructionsField` 按上游裁决）；02 §7.1 规则 2（网关上 system 改发 developer 消息）；04 §5.1（显式 `strict` 丢 format——2026-09-24 被扩展：`[Pro]` 不论写不写都丢；四上游对照）；06 §4.1；13 §4.2「经 chat 出图的中继」、§6；14 §4；02 §1 表后（PDF / URL 图片静默丢弃，随渠道）、§2.2（③ 面只认 camelCase）、§3.2（`content` 数组、usage 末块）；03 §3.3（① `max` = 不想是转换层的；④ 思考随渠道：Kiro effort 只有 low 生效、`display` 无视，anti 不想，CC opus-5 空文本，Bedrock 真分档）、§4（空 `reasoning_content`）、§7.4（GPT：账号池真分档、`none` 关不掉，① `none` 只在网关生效）；04 §2（两族 JSON 旋钮被无视；① 面整台被丢、④ 面随渠道）、§4「第四种变体」（强制 `tool_choice` 只在非流式生效；anti 两条路径都不生效）；05 §3（拼接参数、空串 id）、§5「中转站自己做服务端工具」（`web_search` 劫持 / 真搜 / 丢弃，`web_fetch` / `code_execution` 假装执行；同台四个渠道四种答案）、§5「中转站上的 GPT」（账号池真搜、网关静默丢，① `web_search_options` 处处忽略，代码解释器 / 文件搜索 / 出图的报法）；06 §1「中转站估算的 usage」（`cache_control` 只写不读）与 `attribution`（注入量读数）、§2（同一非法参数四上游四种报法、中转站自己下载 URL 图片 500 `count_token_failed`）、§4.1（GPT 上游的改写；输出上限回显抓不到）、§5（402；目录的 `supported_endpoint_types` 不可信、503「No available channel」）、§8 第 7–11 条（流式 / 非流式各测、至少测两个渠道、非法参数分反代 / 正向、注入量多跑几次）；坑 61–65、105–112、138–169 | 【实测 2026-09 + 中继源码；Kiro 渠道与五渠道对照实测 2026-09-23；上游画像实现 2026-09-23；GPT 四上游实测与 codex / azure 画像实现 2026-09-24】 |
| **OrcaRouter**（`api.orcarouter.ai`） | ① ② ③ ④ 四面同一主机、一把 key、一份目录（模型 id 带厂商前缀）；④ 回包 Anthropic 原样、③ Vertex AI 原样，① 与 ② 默认线路是 OpenRouter 形态翻译层，② 带 `store:true` / 搜索来源 `include` 时换到 OpenAI 原样；**四面请求都被重新序列化** | 01 §9.5（数据行、按面判后端、透传证据清单、两套 ② 后端、`x-orca-route` 头、计数端点被当生成执行、目录的 `supported_endpoint_types` 只是建议；**花费字段按面不同、④③ 要 `X-OrcaRouter-Include-Cost: true` 才报**（④ 在 `message_delta`、③ 在末块，① 流式只有 `usage.cost`，② 原样线路不报，与 `GET /v1/generation` 对账相等）；目录 `context_length` / `max_completion_tokens` / `input_modalities` 抄成标定表、起步模型按线路钉好 + 删线路的守卫、PDF 四面都读、③ 是 Vertex 不是 AI Studio）；06 §1（网关报钱按面不同；上游报价进账的信任边界与合并规则）、§2（错误信封改写：③ `***` 遮路径、④ `type:"<nil>"`）、§5（402 余额闸、`supported_endpoint_types` 反方向）、§8 第 7、10、12 条；02 §1 表后（PDF 四面、计费；① 不收 `video_url`：Gemini **200 静默丢弃**、输入 token 不变，GPT 400）；05 §5「③ Gemini 的内置工具」；03 §2.1（经它测的思考回退）；经它测得的厂商事实见 Anthropic / Gemini / OpenAI 三行；坑 170–179、185–197、203–206 | 【实测 2026-09-03 探测与免费档；付费四面实测 2026-09-26；流式花费 / PDF / Gemini 内置工具再补测 2026-09-26；思考回退 / 视频输入 2026-09-28】 |
| **OpenRouter** | ① | 06 §2（SSE 体内 error 常见）、§6（`/models` 带 `context_length`）。**OpenRouter 形态的回包指纹**（`gen-…` id、`provider`、`native_finish_reason`、`usage.cost` / `is_byok` / `cost_details`、`reasoning_details[]`；② 上伪造的 `msg_tmp_` / `fc_tmp_` item id、`summary` 回显 `detailed`）见 01 §9.5——是在 OrcaRouter 的 ① ② 默认线路上看到的，不是对 OpenRouter 本身的实测 | 【文档；指纹经 OrcaRouter 实测 2026-09-26】 |
| **Ollama / LM Studio**（本地） | ① | 02 §5（空 Bearer 被拒）、§6（Windows 打包版 403）；01 §6（超窗静默丢头部）；06 §6；坑 5 | 【实测，日期未标】 |
| **Azure OpenAI / Vertex / Bedrock** | 部署变体 | 01 §2；02 §5；06 §2（Azure 用 `content_filter` 代替错误码）。注意：中转站里叫 `[Azure]` 的上游不等于 Azure OpenAI——2026-09-24 那个是带护栏的网关（01 §9.2、坑 159） | 【文档】 |
| **Midjourney（midjourney-proxy / New API `/mj/*`）** | 独立的异步出图协议 | 13 §2、§4.2「midjourney」 | 【实现，日期未标】 |
| **Groq / 硅基流动（仅语音识别）** | ⓐ OpenAI 兼容转写 | 16 §3（地址、SenseVoice 语种） | 【实现】 |
| **ASR 专营：Deepgram、ElevenLabs、CAMB AI、Gladia、小米 MiMo、302.AI** | 各自 SDK / 私有协议 | 16 §10.2 | 【实现 2026-09，原 pyVideoTrans】 |

## 本库尚未覆盖（审查时按「未知、需核实」处理）

Kimi / Moonshot、智谱 GLM 的图像 / 视频模型与 Coding Plan 编程端点的完整实测、Mistral、Cohere、Groq 与硅基流动的 chat 面、Together、Fireworks、Bedrock Converse 的 body、
OpenAI 兼容 ASR 的实测（16 §3 全是文档与实现口径）、流式 / 实时 ASR（WebSocket，本库没有）、
Azure 的 `api-version` 细节、Seedance 视频（火山方舟套餐不含，实测 404，需按量 key；body 形状未覆盖）、
OpenAI 官方与火山方舟按量付费收不收 ① `video_url`（02 §1 表后，未量）。

遇到它们：
- 先按 01 §2 判定协议族，再用该族底座的全部检查项去审。
- 厂商特有的东西一律当「未知」，不要从相邻厂商类推。
- 核实后按 `30-knowledge-ingestion.md` 写回本库，并补进上面的表、20 §2 与 22 对应家族节。完整的待核实清单（含优先级与测法）在 `31-open-questions.md`。
