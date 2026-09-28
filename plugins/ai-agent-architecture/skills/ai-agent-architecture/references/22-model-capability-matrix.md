# 22 模型 × 平台 × 面 能力矩阵（对话模型）

本表回答：**这个模型在这个平台的这个面上，思考／结构化输出／函数工具／服务端工具／多模态输入／上限与采样各是什么行为，哪里会静默失败**。主键 = （模型家族／型号，平台·渠道·线路，面）。典型用例：「DeepSeek 在百炼支持 code_interpreter 而官方不支持」「同一个 Claude 在 New API 四个渠道四种答案」这类差异要一眼能看出。

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

面的编号：① OpenAI Chat Completions ／ ② OpenAI Responses ／ ③ Gemini generateContent ／ ④ Anthropic Messages ／ Ⓓ DashScope 私有 ／ 🖼 出图 ／ 🎬 视频 ／ 🎤 ASR。

维护：新增 / 修正按 `30-knowledge-ingestion.md` 的流程；本表每行必须带证据与指针，没有证据的格子写 `—`。证据记法沿用各篇：【实测 YYYY-MM-DD】【文档 YYYY-MM】【中继源码】【实现】⚠；被推翻的旧结论写「旧：… → 新：…」不删。

## 目录

- [§1 怎么查](#1-怎么查)
- [§2 总览表](#2-总览表)
- [§3 GPT](#3-gpt)
- [§4 Claude](#4-claude)
- [§5 Gemini](#5-gemini)
- [§6 Grok](#6-grok)
- [§7 DeepSeek](#7-deepseek)
- [§8 Qwen（千问）](#8-qwen千问)
- [§9 GLM（智谱）](#9-glm智谱)
- [§10 豆包 Seed（火山方舟）](#10-豆包-seed火山方舟)
- [§11 MiniMax](#11-minimax)
- [§12 本地模型](#12-本地模型)
- [§13 其他（Kimi、OpenRouter）](#13-其他kimiopenrouter)
- [§14 服务端工具 × 平台 × 模型 专表](#14-服务端工具--平台--模型-专表)

## 1 怎么查

三步：

1. **先定模型家族节**（§3–§13）。中转站上的 id 带档位前缀（`[Plus]gpt-5.6-terra`、`[特价kiro量]claude-opus-5`），按去前缀后的家族找；渠道前缀本身是主键的一部分（01 §9.2 第 1 条）。
2. **看该节「家族固有特性（跨平台一致）」**：思考控制方言与代次差异、`<think>` 内联、回传义务、结构化档位。这些在任何平台都成立；只在一个平台测过的特性不在这里，而在平台行里标「仅测于 X」。
3. **在该节「按平台 × 面」表里找 (平台·渠道·线路, 面) 那一行**。同一渠道多个型号行为一致合并成一行（型号列写「opus-4-6 ／ opus-5」），不一致分行。**找不到的行 = 未测**，按 15 篇「未知、需核实」处理：不从相邻平台类推，不从「这是 Claude」推出（05 §5、01 §9.2）。

看完行再看该节末「随平台变化的特性」小结——同一模型在不同平台的对比句，是用户最常问的问题。服务端工具逐个工具、逐个平台的行为在 §14 专表。

## 2 总览表

| 模型家族 | 已测过的 平台·面 组合 | 最典型的随平台变化的特性 | 证据（汇总） |
| --- | --- | --- | --- |
| GPT | OpenAI 官方 ①②（多为 📄）；New API `[特价Pro]`②①、`[Plus]`②①、`[Pro]`②①、`[Azure]`②①、`[官key]`／`[AWSb]`（503）；New API 另一台 `[Pro]`／`[Plus]` ②（第八、第十个样本）；OrcaRouter ①、② 默认线路、② 原样线路 | `web_search`：账号池真搜、`[Azure]` 网关静默丢、OrcaRouter 真跑；`instructions`：账号池不发就注入 4.4K、网关发了挂 1.2K 护栏；`text.format`：`[Pro]` 整个丢、其余执行；`effort:"none"`：② 四上游都改 `medium`，① 只在网关真关；`temperature`：账号池回显 1.0、网关 500 | 【实测 2026-09-24】【实测 2026-09-26】【文档】 |
| Claude | Anthropic 官方 ④（📄 + 经 OrcaRouter 原样实测 Sonnet 5／Opus 5.5／Fable 5.1／Sonnet 4.6／Opus 4.5）；OrcaRouter ①；New API · Kiro ④①、CC ④①、anti ④①、AWSb ④①、官key（502）；某中转 ①（畸形样本） | 思考是否存在／有文本（anti 不想、CC opus-5 空文本、Kiro 只两态）；签名是否校验（官方／AWSb 400，Kiro／CC 200）；`output_config.format` ④ 按渠道甚至按型号、① 整台 New API 都丢；PDF／URL 图是否送达；服务端工具：劫持／真做／丢／400 四种；`max_tokens` Kiro 无视、anti ① 无视 ④ 生效 | 【实测 2026-09-23】【实测 2026-09-26】【实测 2026-09-28】【文档】 |
| Gemini | Google AI Studio ③（📄）；OrcaRouter ③（Vertex 原样）、①；New API ③ 面 | 图片键 snake_case：官方两种都收、New API 只 camelCase；`video_url` 经 OrcaRouter ① 层静默丢；`:countTokens` 经 OrcaRouter 当生成计费；报价需 `X-OrcaRouter-Include-Cost` 头 | 【实测 2026-09-05】【实测 2026-09-26】【实测 2026-09-28】【文档】 |
| Grok | xAI 官方 ②、①（legacy） | 只测官方：② 拒 `none`、拒 `max`；① `video_url` 400；`tool_search` 403 | 【实测 2026-09】【实测 2026-09-28】 |
| DeepSeek | DeepSeek 官方 ①（📄 + `video_url` 实测）；DashScope 托管 ② | 服务端工具：官方无；DashScope ② 面 `code_interpreter` 放行 `deepseek-v4` | 【文档 2026-08】【实测 2026-09-17】【实测 2026-09-28】 |
| Qwen | DashScope 百炼 ①、②、④（⚠）、Ⓓ（Qwen-Audio ⚠） | 同一端点两代思考控制不同；`code_interpreter` ① 面按型号「跑／静默忽略／400」、② 面到 3.8 都跑；`agent_max` 3.8-flash 400、3-max／3.5-plus 收 | 【实测 2026-09-17】【实测 2026-09-28】【文档】 |
| GLM | 智谱按量 ①；智谱 Coding Plan ④（glm-4.7）、①②④（⚠）；百炼／火山（平台执行搜索） | 联网搜索：自家端点靠对话内 `tools[]` + `search_intent:false`，在百炼／火山由平台执行；④ 面 glm-4.7 默认不想、① 面默认想 | 【实测 2026-09-19】 |
| 豆包 Seed | 火山方舟 · 套餐 ①②④；火山方舟 · 按量（对话面未测） | `json_schema` 按型号守不守（2.1-turbo 守、2.0-lite 不守、2.0-mini ② 多字段）；④ 2.0 系无 `signature`、2.1 有；服务端搜索 ②④ 有、① 无；套餐 vs 按量 key 不通用 | 【实测 2026-09-18】【实测 2026-09-23】【实测 2026-09-28】 |
| MiniMax | MiniMax 国内站 ④、① | ④ 面思考默认关且真关，① 面总在想且 `<think>` 内联；两面温度都不听 | 【实测 2026-08】【实测 2026-09-28】 |
| 本地模型 | Ollama ①；LM Studio／llama.cpp ① | 超窗静默从头部截断（Ollama `num_ctx`）；LM Studio 严格交替模板 | 【实测，日期未标】⚠ ⏳待复核【参考实现】 |
| 其他 | Kimi ①；OpenRouter ①（仅指纹经 OrcaRouter）；欠费中转（402） | — | 【实测 2026-09-19】⚠【文档】【实测 2026-09-03】 |

## 3 GPT

### 家族固有特性（跨平台一致）

- ② 思考控制 `reasoning:{effort, summary:"auto"}`，端点枚举七档 `none／minimal／low／medium／high／xhigh／max`；默认按型号不同：5.4 `none`、5.5／5.6 `medium`；5.4 上限 `xhigh`（`max` → 400 且报文列出合法值），5.5／5.6 收 `max`；`reasoning.context` 默认 `all_turns`。【实测，responses.md，日期未标】⚠ ⏳待复核 详见 03 §7.1、02 §7.3。
- ② 回传义务：整组 `output_item.done` 条目原样放回 `input`；**回传缺失不报错**（5.4／5.5／5.6 原样／删 reasoning／删 encrypted_content／只回裸 function_call 四种都 200 且答对），代价只在质量。【实测】详见 02 §7.3、03 §7.3。
- ② 工具结果交付后以 `phase:"final_answer"`、文本空、`status:"completed"` 的 message 条目收尾——是正常结束不是空回复。【实测 2026-09-15】坑 109。
- ② 工具定义省略 `strict` 端点自动升 strict（可选字段变全必填否则 400）→ 显式 `strict:false`；`text.format` json_schema 省略 `strict` 官方自动升 `true`（回显可见）。【文档】【实测】坑 64，详见 04 §5.1、02 §7.1。
- `json_object` 上下文须含 "JSON" 字面量否则报错／无限空白流。【文档】坑 14，详见 04 §2。
- `text.verbosity: low／medium／high` 生效（同题回答变短）——GPT-5.x，仅 ② 面；① 顶层 `verbosity` 在四个上游都无效。【实测 2026-09-24，New API 四上游】详见 04 §5.2。
- 服务端工具事件 `web_search_call` 的 `action.type` 有 `search`／`open_page`／`find_in_page`，后两种无 queries／sources。【实测】坑 71，详见 05 §5。
- GPT-5.4+ 原生工具按需加载（`defer_loading`、`tool_search`、`namespace`、`additional_tools`），下一轮必须回传 `tool_search_output`，缺了加载过的工具静默消失。【文档 2026-09】坑 68，详见 05 §7。
- o1-pro／codex 系／computer-use 是 Responses-only，走 ① 失败。【文档 2026-08】详见 01 §8.1。
- 文本 delta 旁带 `obfuscation` 填充；`[DONE]` 不属于 ② 但要容忍。【实测】详见 02 §7.2。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GPT（通用） | OpenAI 官方 | ① | 📄 顶层 `reasoning_effort`；未知顶层字段直接 400 | — | 📄 `json_object` 需含 "JSON"；`json_schema` strict 收 | 📄 `auto／none／required／具名` 全档 | 📄 `web_search_options` 形状存在；`enable_search` 等未知顶层参数 400 | ① `video_url` 未量 ⚠ | — | `json_object` 缺 "JSON" 无限空白流 | 【文档】 | 03 §2、04 §2、05 §5 | 14 |
| GPT（通用） | OpenAI 官方 | ② | 📄 `reasoning:{effort,summary}` 七档；默认按型号 | `store:false` 下 reasoning 条目附 `encrypted_content`；不发 `include` 是否丢加密推理未经官方 key 验证 ⚠ | ✅ `text.format` 省略 `strict` 自动升 `true`（回显）；`json_object` 缺 "json" 400；`text.verbosity` ✅ | 扁平具名 `{type:"function",name}`；工具须显式 `strict:false` | web_search 📄 形状；数值只有经 New API（第十个样本）的一次搜索 45.7K 输入、112 s、首事件可晚到 54 s（`open_page／find_in_page`）；code_interpreter 要 `container`；file_search／image_generation 📄 | 📄 `input_image`（data／http）、`input_file`（file_data／file_url） | `incomplete_details.reason: max_output_tokens` → 截断 | 空文本 `status:"completed"` message 收尾被误判空回复 | 【文档】【实测，日期未标】⚠ ⏳待复核 | 02 §7、03 §7.1、04 §5、05 §5 | 64、71、109 |
| GPT-5.4+ | OpenAI 官方 | ② | 同上 | 回传名单须含 `tool_search_output`／`additional_tools` | — | 📄 `defer_loading`、`tool_search`、`namespace`、`additional_tools`；工具表前缀不动、缓存不破 | — | — | — | 回传缺失 → 加载过的工具下一轮 🔇 静默消失 | 【文档 2026-09】 | 05 §7 | 68 |
| o1-pro ／ codex 系 ／ computer-use | OpenAI 官方 | ② only | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | 走 ① 会失败（Responses-only，截至 2026-08） | 【文档 2026-08】 | 01 §8.1 | — |
| GPT-5.4 | 经中转站（未具名） | ② | 默认 `none`；上限 `xhigh`；`max` ❌ 400 列合法值 | 回传缺失四种都 200 且答对 | — | — | — | — | — | — | 【实测，responses.md，日期未标】⚠ ⏳待复核 | 03 §7.1、02 §7.3 | — |
| GPT-5.5 ／ GPT-5.6 | 经中转站（未具名） | ② | 默认 `medium`；收 `max`；5.6 默认 `reasoning.context: all_turns` | 回传缺失四种都 200；工具结果后空文本 `completed` message 收尾 | — | — | — | — | — | 空回复守卫误判 | 【实测 2026-09-15】 | 02 §7.2、§7.3、03 §7.1 | 109 |
| gpt-5.6-sol | New API · `[特价Pro]`（ChatGPT 账号池，画像 codex） | ② | ✅ 真分档（low／xhigh `reasoning_tokens` 295–428／583–588）；`none` 🔇 回显 `medium` 照想；`max` ✅；乱写 ❌ 流式 `response.failed`（`upstream_error`）；`reasoning.mode:"pro"` 回显 `standard` | `store:false` 自带 `encrypted_content`；四种回传缺失 200 | ✅ json_schema（省略／显式 `strict` 都执行）；`json_object` ✅；`text.verbosity` ✅ | ✅ `auto`／具名／`required` | web_search ✅ 真搜 6–10 s（输入 8.5–14K）；code_interpreter ❌ 流式 `response.failed`；file_search ❌ 同；image_generation ❌ 403 `Image generation is not enabled for this group` | `input_image`（data／http）✅；`input_file` PDF（`file_data`／`file_url`）✅；拒爬主机 URL 图 → 流内 `error` 后接空答（200） | `max_output_tokens:16` 🔇 无视（`status:completed`）；`temperature:0.5` 🔇 回显 `1.0`；`store:true` 200 | 不带 `instructions` 注入 0／11／296／4.4K／17K 不固定（读 `usage.attribution.request_fields.instructions.input_tokens`）；effort／温度改写；上限无视回显抓不到 | 【实测 2026-09-24】（curl ≈560 次 + live 45 条过 41） | 01 §9.2「同一个 GPT」、03 §7.4、04 §5.1、05 §5、06 §1、§4.1 | 61、62、65、161、162、165、167 |
| gpt-5.6-sol | New API · `[特价Pro]` | ① | low／high／xhigh／max 都想；`none` 🔇 关不掉；乱写 → 流内「Upstream service temporarily unavailable」 | `reasoning_content` 摘要式短文本 25–107 字符（① 翻成 ② 再发） | ✅ `response_format: json_schema`（strict） | 具名 ✅ | `web_search_options` 🔇 静默忽略（①→② 翻译不转此字段） | ⚠ | `max_completion_tokens:16` 🔇 无视；温度无回显 | 带 system 仍注入 4,397（多数请求）；顶层 `verbosity` 无效 | 【实测 2026-09-24】 | 01 §9.2、03 §7.4、04 §5.1、05 §5 | 164、165 |
| gpt-5.6-sol | New API · `[Plus]`（账号池，codex） | ② | 同 `[特价Pro]` ②；乱写 ❌ 502 `Upstream request failed` | 同上 | ✅ json_schema 省略／显式 strict 都执行；`json_object` ✅（第八个样本「显式 strict 丢」在 Plus 未复现） | ✅ | web_search ✅；code_interpreter／file_search ❌ 502；image_generation ❌ 403 | ✅ | `max_output_tokens` 🔇；`temperature:0.5` 🔇 回显 `1.0`；`store:true` 200 | 不带 `instructions` 注入 4,389（`attribution…input_tokens: 4380`） | 【实测 2026-09-24】 | 01 §9.2、04 §5.1、05 §5、06 §2 | 62、65、161、162 |
| gpt-5.6-sol | New API · `[Plus]` | ① | `none` 🔇 关不掉；乱写 ❌ 502 | 同 `[特价Pro]` ① | ✅ json_schema | 具名 ✅ | `web_search_options` 🔇 忽略 | ⚠ | `max_completion_tokens` 🔇 | 带 system 3／3 注入 4,395 | 【实测 2026-09-24】 | 01 §9.2、04 §5.1 | 164、165 |
| gpt-5.6-sol | New API · `[Pro]`（账号池，codex） | ② | 同 `[特价Pro]` ②；乱写 ❌ **400 官方原文** `Invalid value: 'bogus'. Supported values are: 'none', 'minimal', …` | 同上 | ❌🔇 **整个丢 `text.format`**：省略与显式 `strict:true` 各 4 次全丢，回显 `{type:"text"}`，答 `{"answer":2}`；`json_object` 回显 `text`。旧：显式 `strict:true` 才丢（第八个样本）→ 新：不论写不写都丢（2026-09-24） | ✅ | web_search ✅；code_interpreter／file_search ❌ 400 `Unsupported tool type`；image_generation ❌ 403 | ✅；拒爬主机 URL 图 ❌ 400 `Error while downloading file` | `max_output_tokens` 🔇；`temperature:0.5` 🔇 回显 `1.0` | 校验与官方同文却是唯一丢结构化输出的档（校验同源 ≠ 能力同源）；丢 format 后仍回合法 JSON（提示语要求），能解析不证明 schema 生效；不带 `instructions` 9 token 不注入 | 【实测 2026-09-24】 | 01 §9.2「上游画像扩到 GPT」、04 §5.1、06 §2、§8 | 63、160 |
| gpt-5.6-sol | New API · `[Pro]` | ① | `none` 🔇 关不掉；乱写 ❌ 400 官方原文 | 同 `[特价Pro]` ① | ❌🔇 `response_format: json_schema` 丢（4／4） | 具名 ✅，但带具名时注入 4,434 | `web_search_options` 🔇 忽略 | ⚠ | `max_completion_tokens` 🔇 | 带 system 19 token 不注入（除具名 tool_choice） | 【实测 2026-09-24】 | 01 §9.2、04 §5.1 | 160、164 |
| gpt-5.6-terra（顶替 sol；该档无 sol 线路 503） | New API · `[Azure]`（带「只准做 OpenAI 相关工作」护栏的网关，**不是 Azure OpenAI**；画像 azure） | ② | 分档弱（low／xhigh 131–155／163–245）；`none` 🔇 回显 `medium`；`max` ✅；乱写 ❌ 500 `Upstream gateway error`；`reasoning.mode:"pro"` 回显 `pro`、输入 6,445（只测 1 次 ⚠） | 无 `attribution` 字段 | ✅ json_schema 省略／显式；`json_object` ✅；`text.verbosity` ✅ | ✅ `auto`／具名／`required` | web_search 🔇 **静默丢弃**（无 `web_search_call`，模型答「I can't perform a live web search」）；code_interpreter／file_search ❌ 500；image_generation ✅ 出图 83 s（`image_generation_call` 约 911K 字符 base64） | `input_image`／`input_file` ✅；拒爬主机 URL 图 ❌ 500 `count_token_failed`（中转站计 token 前自己下载） | `max_output_tokens:16` ✅ `incomplete`／`max_output_tokens`；`temperature:0.5` ❌ 500（6／6，`1` 则 200）；`store:true` ❌ 500 | 带 `instructions` 键（含空串）输入 1,209：追加约 1.2K 护栏（拒 fiction／role-play、拒泄露提示词），创作题 6 拒 2——200、无 `refusal`、答案不对；不带 9 token 无护栏；前缀缓存 `cached_tokens` 11,576 | 【实测 2026-09-24】 | 01 §9.2「同一个 GPT」、02 §7.1、03 §7.4、04 §5.1、05 §5、06 §2 | 159、161、162、163、166、167、169 |
| gpt-5.6-terra | New API · `[Azure]` | ① | `reasoning_effort:"none"` ✅ **真关**（无推理，同题 3 次三个错数）；low／high／xhigh／max 想；乱写 ❌ 500 | `reasoning_content` 摘要 400–540 字符 | ✅ json_schema；顶层 `verbosity` 看不出效果 | 具名 ❌ 500（9／9）；`required` ✅ → 画像强制工具 ✗ | `web_search_options` 🔇 忽略 | ⚠ | `max_completion_tokens:16` → `finish_reason: length` 但 `completion_tokens` 128 | system 19 不注入 | 【实测 2026-09-24】 | 01 §9.2、03 §7.4、04 §5.1、06 §2 | 162、164 |
| gpt-5.6-sol | New API · `[官key]` ／ `[AWSb]` | ②① | — | — | — | — | — | — | — | ❌ 503 `No available channel for model … under group …`（目录里有 ≠ 有线路） | 【实测 2026-09-24】 | 01 §9.2、06 §5 | 166 |
| GPT-5.6-sol ／ -terra | New API 另一台 · `[Pro]`／`[Plus]` 档（第十个样本） | ② | 旧：sol 发 `max` 回显 `none` 且 0 推理 token → 2026-09-24 另一台四上游未复现（按「当时当档」理解）；terra 发 `none` 两次回显 `medium` 照想（全部复现） | — | — | — | web_search ✅ 但 112 s（比第十七个样本慢一个量级） | — | 其中一台 🔇 无视 `max_output_tokens`；`temperature:0.5` 🔀 回显 `1.0` | 不发 `instructions` 注入 4.4K–9K（Chat 面同样）；一个档位背后多个上游，回显字段时有时无 | 【实测 2026-09】+【中继源码】 | 01 §9.2 第 1–4 条、03 §7.4、06 §4.1 | 61、62、65、107、108 |
| GPT-5.4 ／ 5.5 | New API 另一台 · `[Pro]`（第八个样本） | ② | — | — | 旧：显式 `strict:true` 才丢 `text.format` → 新：2026-09-24 同台 `[Pro]` 不论写不写都丢 | — | — | — | — | — | 【实测 2026-09】 | 01 §9.2「同一个 GPT」第 6 条、04 §5.1 | 63 |
| GPT 家族（作用域 `/gpt/`，含 5.4／5.5／5.6） | New API · codex 画像（参考实现落格） | ① | — | — | — | 强制工具 ✓ | — | `pdfInput` ✓ | ① 温度不写格子（发 0.5 都 200、无回显） | — | 【实现 2026-09-24】 | 01 §9.2「上游画像扩到 GPT」 | 168 |
| 同上 | New API · codex 画像 | ② | — | — | `textVerbosity` ✓ | 强制工具 ✓ | `web_search` ✓ | `pdfInput` ✓ | `temperature` ✗（回显 1） | `instructionsField` ✓（恒发，不发则注入 4.4K） | 【实现 2026-09-24】 | 01 §9.2 | 168、169 |
| 同上 | New API · azure 画像 | ① | — | — | `structuredOutput` ✓ · `jsonSchema` ✓ | 强制工具 ✗（`required` 也发 `auto`） | — | `pdfInput` ✓ | — | — | 【实现 2026-09-24】 | 01 §9.2 | 168 |
| 同上 | New API · azure 画像 | ② | — | — | `structuredOutput` ✓ · `jsonSchema` ✓ · `textVerbosity` ✓ | 强制工具 ✓ | `web_search` ✗ | `pdfInput` ✓ | `temperature` ✗（非 1 就 500） | `instructionsField` ✗ → 系统提示作 `input` 开头 `{role:"developer"}`，不发 `instructions` 键 | 【实现 2026-09-24】 | 01 §9.2 | 159、168、169 |
| GPT-6 luna ／ sol ／ astra；GPT-5.6-terra；gpt-5-mini | OrcaRouter · ① 线路（OpenRouter 形态翻译层） | ① | `reasoning_effort` + `tools` 同发 200、并行调用正常（上游走 ②，不能证伪「官方 ① 上 5.4+ 不能 effort + tools」） | 思维链只以 `reasoning_details[]` 密文／`reasoning` 摘要出现 | ✅ `response_format` strict `json_schema` 守住 enum（luna） | 并行 ✅ | `web_search_options` 🔇 200 但没有 `annotations` | `video_url` ❌ 400 `The upstream provider rejected this request`（gpt-5-mini） | 目录 1,050,000／128,000；末块 `usage.cost` | 回包 `gen-…` id、`provider`、`native_finish_reason`（翻译层指纹）；视频 400 会响 | 【实测 2026-09-26】；视频【实测 2026-09-28】 | 01 §9.5、04 §2、02 §1、06 §1 | 185、206 |
| GPT-6 luna ／ sol ／ astra | OrcaRouter · ② 默认线路（OpenRouter 形态） | ② | `none`–`max` 六档 200；`minimal` 🔀 改写成 `low`（翻译层还是上游 ⚠）；`effort:"bogus"` ❌ 网关自己的 `upstream_rejected_request`（原文被吞） | 流：reasoning item 只有 `encrypted_content`、`summary: []`、无 `reasoning_summary_text.delta`（非流时 luna 有摘要文本）；`summary:"auto"` 回显 `"detailed"`；回灌义务测不出（`store:false` 只回 id 的 reasoning item、篡改密文、丢 item 全 200） | ✅ strict `text.format` 守住 enum；顶住矛盾 enum | 并行 `function_call` 依次不交错；伪造 `msg_tmp_…`／`fc_tmp_…` item id | web_search ✅ 真跑（`in_progress`／`searching`／`completed` 齐全、`url_citation`）；`action.sources` 需 `include:["web_search_call.action.sources"]`（但该 include 触发分流到原样线路） | `input_file` PDF ✅ | 目录 1,050,000／128,000；`response.completed.response.usage.cost`（不需请求头）；`store` 恒 `false` | `minimal` 静默改写；`gen-…` id | 【实测 2026-09-26】 | 01 §9.5、03 §7.1、04 §2、05 §5、06 §1 | 175、185 |
| GPT-5.6-terra | OrcaRouter · ② 默认线路 | ② | reasoning `format` 是 `azure-openai-responses-v1`（上游 Azure） | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | 1,050,000／128,000 | — | 【实测 2026-09-26】 | 01 §9.5 | — |
| GPT-6（同上） | OrcaRouter · ② 原样线路（`store:true` 或 `include` 含 `web_search_call.action.sources`） | ② | `include:["reasoning.encrypted_content"]`、`text.verbosity`、`tools:[{type:"web_search"}]` 都不触发分流 | OpenAI 原样：`resp_…` id、`billing`、`tool_usage`、`moderation`、`prompt_cache_retention:"24h"` | ⚠ | ⚠ | web_search ✅（同上，原样事件） | ⚠ | **没有任何花费字段**（`X-OrcaRouter-Include-Cost` 对 ② 无效）；`usage.input_tokens_details.cache_write_tokens`（一次 web_search 4,388） | 同一端点两套后端按 `store`／`include` 分流 | 【实测 2026-09-26】 | 01 §9.5、06 §1 | 175、186 |

### 随平台变化的特性

- **联网**：同一 `gpt-5.6-sol` 在 New API 三个账号池档 `web_search` 真搜 6–10 s，在 `[Azure]` 网关 200 静默丢（模型老实说搜不了）；OrcaRouter 两条 ② 线路都真跑；① 面 `web_search_options` 在 New API 四上游全部静默忽略、在 OrcaRouter 200 无 `annotations`——GPT 联网只能走 ②。【实测 2026-09-24】【实测 2026-09-26】
- **系统提示**：账号池不发 `instructions` 注入 4.4K–17K token，网关发了 `instructions` 键就挂 1.2K 护栏并可能拒创作——同一台同一 id 两类上游方向相反，`instructionsField` 按上游裁决。【实测 2026-09-24】坑 62、159、169
- **结构化**：`text.format` 在 `[特价Pro]`／`[Plus]`／`[Azure]`／OrcaRouter 执行，唯独 `[Pro]` 整个丢（省略 `strict` 也救不了）；① `response_format` 同样只在 `[Pro]` 丢。【实测 2026-09-24】坑 160
- **关思考**：② `effort:"none"` 在 New API 四上游都被改写成 `medium`；① `reasoning_effort:"none"` 只在 `[Azure]` 网关真关；xAI 拒 `none`、DeepSeek 另一字段——同一个「关」四种命运。【实测 2026-09-24】坑 161
- **温度与上限**：账号池 `temperature:0.5` 回显 `1.0`、`max_output_tokens` 无视；网关 `temperature≠1` 整条 500、`max_output_tokens` 执行；OrcaRouter ② 默认线路 `minimal` 被改成 `low`。【实测 2026-09-24】【实测 2026-09-26】坑 65、162
- **URL 图片**：拒爬主机上的 http 图片四档四种失败（流内 error+空答／400／500 `count_token_failed`）；PDF 与 data 图片在 GPT 上游全部读到（丢文档是 Claude 翻译层的事）。【实测 2026-09-24】坑 167

## 4 Claude

### 家族固有特性（跨平台一致）

- 思考方言按代：4.6+ `adaptive`（`{"thinking":{"type":"adaptive","display":"summarized"}}`），≤4.5 `extended`（`{"type":"enabled","budget_tokens":N,"display":"summarized"}`，budget 钳 `[1024, min(16384, maxTokens/2)]`，`budget_tokens ≥ max_tokens` 官方 400）；`display` 当前代默认 `"omitted"`——thinking 块文本空但**全额计费**。【文档／参考实现】坑 4，详见 03 §3。
- Claude 5 系（Opus 5.5／Fable 5.1）拒收 `thinking:{type:"disabled"}` → 400 `requires adaptive thinking; omit thinking or use thinking.type=adaptive and output_config.effort`；Sonnet 5 不发 `thinking` 也在思考（adaptive 默认）；「关闭」= adaptive + `effort:"low"`，只是最低档（`offSpelling:"lowest"`），要真省得 off + 一句提示。【实测 2026-09-26】【实测 2026-09-28】经 OrcaRouter 原样，坑 184、203、204，详见 03 §2、§2.1。
- 只发 `output_config.effort` 不发 `thinking` → 不想（官方 4.6 与 Kiro 一致）。【文档】【实测 2026-09-23】详见 03 §3、§3.3。
- 回传义务：`_thinkingBlocks` 有序整块原样回传（含 `signature`、`redacted_thinking`），只挂在带 tool_calls 的 assistant 上；**不回传 = 静默降级**（API 不报错，直接关掉这轮思考）；改动／重排／部分丢弃 → 400；换模型不剥 → 别的模型静默忽略且照 input 计费。【文档】【实测 2026-09-26】坑 1、3、137，详见 03 §5。签名**是否校验**随平台（见下）。
- 思考开着官方只收 `temperature:1`（别的 400）——文档口径，未在 Sonnet 5／Opus 5.5 单独实测 ⚠；在想就不发温度。【文档】详见 03 §3.4。
- 结构化只有严格档 `output_config.format:{type:"json_schema",schema}`（与 `output_config.effort` 同一对象合并，平铺互盖 = 坑 181），无 `json_object` 中间档，`response_format` 硬 400；官方支持表从 Claude 4.5 起；schema 限制：`additionalProperties:false` 必须、不支持 `minimum／maximum／pattern／minLength／maxLength`、`minItems` 只 0／1、不支持递归与外部 `$ref`；官方拒绝报文至今无样本 ⚠。旧：④ 只有 cue → 新：2026-09-26 更正。【文档】【实测 2026-09-26】坑 180–182，详见 04 §2。
- 工具：`{name, description, input_schema}`；tool_choice `{type:"any"}`／`{type:"tool",name}`；只在声明了本地工具时发；空参数调用不流 `input_json_delta`（`""` → `"{}"`）；`tool_use` 块带 `caller:{"type":"direct"}`；4.5+ `defer_loading`（至少一个非延迟工具，与 `cache_control` 同现 400）。【文档】【实测 2026-09-26】详见 05 §2、§3、§7。
- 服务端工具 wire：`tools[]` 版本化条目 `web_search_20250305`（不需 beta 头）／`web_search_20260209`／`web_fetch_20250910`／`code_execution_20250825` + `max_uses`（唯一刹车，$10／1000 次）；`server_tool_use` → `*_tool_result` → citations；`stop_reason:"pause_turn"` verbatim 续跑。【文档】【实测 2026-09-26】详见 05 §5、§6。
- usage 三桶不重叠相加；`output_tokens_details.thinking_tokens` 是 `output_tokens` 子集；服务端自动写缓存（`web_search` 2,834、PDF 1,630）不能当「我方打了断点」判据。【实测 2026-09-26】坑 18、179、197，详见 06 §1。
- `max_tokens` 必填无服务端默认；官方未知顶层键 400；`stop_reason:"refusal"` 必须 throw。【文档】详见 02 §1、06 §2。
- New API 平台层 ①→④ 转换（四渠道一致，归转换层不归渠道）：① `reasoning_effort:"max"`／`"none"`／乱写 = 不想（`max` 与 `none` 同效）；`response_format` 被丢；`reasoning_tokens` 恒 0（思考算进 `completion_tokens`）。【实测 2026-09-23】坑 140、142、147，详见 01 §9.2、03 §3.3、04 §2。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude 4.6+（家族） | Anthropic 官方 | ④ | 📄 `adaptive`；`display` 默认 `omitted` 全额计费；只发 effort 不发 thinking → 不想；思考开只收 `temperature:1` | 📄 `thinking_delta`（仅 display summarized）；不回传 🔇 静默关思考；改签名 400 | 📄 `output_config.format` json_schema（4.5 起）；无 json_object；`response_format` 400 | 📄 `any`／`tool`；`defer_loading` 4.5+ | 📄 `web_search_20250305`+`max_uses`；`web_fetch_20250910`；`code_execution_20250825`；`pause_turn` | 📄 image base64／url；document base64／url；纯文本 document + `citations.enabled` | `max_tokens` 必填；未知顶层键 400 | display 默认 omitted 付全额费拿不到字；丢块静默；换模型不剥静默计费 | 【文档】【参考实现】 | 03 §3、§5、04 §2、05 §2、§5–7、02 §1 | 1、3、4、180–182 |
| Claude ≤4.5（家族） | Anthropic 官方 | ④ | 📄 `extended`：`enabled + budget_tokens`，budget 钳 `[1024, min(16384, maxTokens/2)]`，`budget ≥ max_tokens` 400 | 同 ④ 载体 | 📄 4.5 起 `output_config.format`（旧写法 `output_format` + beta 头） | 同上 | 同上 | 同上 | 同上 | 同上 | 【文档／参考实现】 | 03 §3、§3.3 | 1、4 |
| Claude Sonnet 5 | Anthropic 官方 · 经 OrcaRouter ④ 线路（回包原样） | ④ | 不发 `thinking` 也想（141 token）、块文本空只有签名；显式 `display:"summarized"` 才有文本；`effort` low–max 都收，`low` 常 0 思考 token；`enabled + budget_tokens` 也 200 照想；回退实测（输出 token 中位数）不设 6,962／高 6,825／关(=低) 2,270／高+提示 1,090／关+提示 1,396，关闭省约 2／3；网关上 `thinking.type:"bogus"`／`effort:"bogus"` 200（重新序列化） | 流：`content_block_start` 带 `signature:""` → `thinking_delta` → 末尾 `signature_delta`；原样回灌 200；改 `signature` ❌ 400 ``Invalid `signature` in `thinking` block``；改 thinking 文本留原签名 200；整块丢 200 🔇 静默降级 | ✅ `output_config.format` 回纯 JSON 无围栏、守住 enum（去掉 enum 答 `yellow`）；与 effort 共用 `output_config`；与思考／工具／强制／流式同用 | 强制 `any`／指名（含 adaptive）✅ 出 `tool_use`；`caller:{"type":"direct"}`（去掉回灌也 200） | `web_search_20250305` ✅ 不需 beta 头：`server_tool_use` → `web_search_tool_result`（10 条各带 `encrypted_content`）→ 带 `citations` 的 text；`usage.server_tool_use:{web_search_requests:1, web_fetch_requests:0}` | PDF `document` ✅；没带 `cache_control` 记 1,630（PDF）／2,834（web_search）`cache_creation_input_tokens` | 目录 1,000,000／128,000；`thinking_tokens` 子集（22 = 21+1）；一次 web_search 请求 $0.051；`message_delta.usage.cost_usd` 需 `X-OrcaRouter-Include-Cost: true` 头；`/v1/messages/count_tokens` 301 | 不发 thinking 也付费；丢块静默；`cache_creation` 非断点判据；错误信封 `type:"<nil>"`、路径 `***`；402 先于模型解析 | 【实测 2026-09-26】【实测 2026-09-28】；402【实测 2026-09-03】 | 03 §2.1、§3、§4、§5；04 §2；05 §3、§5；06 §1、§2、§5；02 §1 | 4、174、176、177、179、186、197、203、204 |
| Claude Opus 5.5 | Anthropic 官方 · 经 OrcaRouter ④ | ④ | `thinking:{type:"disabled"}` ❌ 400 `requires adaptive thinking; omit thinking or use thinking.type=adaptive and output_config.effort`；不发 `thinking` 也想 | 同 Sonnet 5（adaptive） | ✅ 守住 enum；思考摘要明说「yellow 不在 enum 里」；与 `budget_tokens` 思考同用 thinking 块在前 JSON 在后 | 强制与 schema 不冲突 | — | PDF `document` ✅；那次**没有**缓存写入 token（与 Sonnet 5 差异原因 ⚠） | 目录 1,000,000／128,000 | `disabled` 会响；其余同 Sonnet 5 | 【实测 2026-09-26】 | 03 §2、§3；04 §2；02 §1 | 184、197 |
| Claude Fable 5.1 | Anthropic 官方 · 经 OrcaRouter ④ | ④ | `disabled` ❌ 400（同 Opus 5.5 文案）；那一题没思考 | — | ✅ 守住 enum | — | — | — | 目录 1,000,000／128,000 | — | 【实测 2026-09-26】 | 03 §2、§3；04 §2 | 184 |
| Claude Sonnet 4.6 ／ Opus 4.5（`thinking: disabled`） | Anthropic 官方 · 经 OrcaRouter ④ | ④ | `disabled` 收（这两款可关） | — | ✅ `output_config.format` 守住 enum；与工具同用第一轮 `tool_use`、回灌后第二轮合 schema JSON；流式走普通 `text_delta` | 强制与 schema 不冲突 | — | — | — | 名单要列两种拼法（`claude-opus-4-5`／`claude-opus-4.5`） | 【实测 2026-09-26 补测】 | 04 §2 | 183 |
| Claude（同上五款） | OrcaRouter · ① 线路（翻译层） | ① | 思维链在 `reasoning_content` | — | ⚠ | ⚠ | ⚠ | PDF `file` 部件 ✅ 读到（网关替上游翻译，标定表只算推断） | 目录 1,000,000／128,000；末块 `usage.cost` | — | 【实测 2026-09-26】 | 01 §9.5、02 §1 | — |
| claude-opus-4-6 ／ claude-opus-5（两款每条一致，usage 逐字相同） | New API · Kiro 渠道（前缀 `[kiro]`…`[特价kiro量]`；后端 Kiro 非 Anthropic API） | ④ | `adaptive`／`enabled+budget`／`disabled` 三种都照办；`display` summarized／omitted 🔇 无效（永远全文）；`effort` 只有 `low` 有效（low ≈ 750，medium／high／max ≈ 1,050 分不出）；`bogus` 🔇 200；只发 effort 不发 thinking → 不想；`budget_tokens ≥ max_tokens` 200；思考时 `temperature:0.3` 200 | 块带 `signature`（300–380 字符）；`thinking_delta`／`signature_delta`；工具轮回传 ✅；**签名不校验**：原样／篡改末尾／删掉都 200 🔇 | 🔇 `output_config.format`（GA）与 `output_format` + beta 头都 200 都无视（答 `2`、外包 markdown）→ cue-only | 强制只在**非流式**转换路径生效：流式 `any`／`tool` 🔇 无视（32 次 1 次）；非流式带思考首轮 `tool` 0／8、`any` 6／8，复测 0；不带思考流式时好时坏（16 次 1 次 → 5 次 3 次） | web_search 单挂 🔀 **整条劫持**（首条 user 原文当搜索词、0.8–2 s 模板回复、模型没跑）；+ 函数工具流式 ✅ 真搜；+ 函数工具非流式 🔇 丢；web_fetch 🔇 丢且假装抓；code_execution 🔇 丢且假装跑；乱造 type 200 丢 | base64 图 ✅；URL 图 🔇 丢；PDF `document` base64／url 🔇 丢（模型答「没看到文档」，33 s）；纯文本 `document`+`citations` 读到但无 `citations` 字段 | `max_tokens` 🔇 无视，`stop_reason` 永不 `max_tokens`；不带 `anthropic-version` 也 200 | 不注入（「Say OK.」7 token）；`cache_control` 只写不读（同前缀两次都报 `cache_creation` 7,360，打断点更贵）；usage 估算，流式 301 vs 非流式 102 | 【实测 2026-09-23】（curl ≈200 次 + `live.relay-kiro.test.ts` 31 条） | 01 §9.2；03 §3.3；04 §2、§4；05 §5；06 §1、§8 | 65、137、138–145 |
| 同上 | New API · Kiro 渠道 | ① | `reasoning_effort` low／medium／high 想 → `delta.reasoning_content`；`max`／`none`／乱写 🔇 不想（转换层，整台）；顶层 `thinking:{…}` 🔇 忽略 | `reasoning_content` 有文本；`completion_tokens_details.reasoning_tokens` 恒 0（不能当「没想」判据） | 🔇 `response_format` `json_object`／strict `json_schema` 丢（转换层）：回 json 代码块围栏、键名自拟 | 流式 `required`／具名 🔇 无视（4 次 0 次，模型复述「你要我调用 get_weather」不调）；非流式生效 | `web_search_options` → 转成 ④ `web_search` 后同样 🔀 劫持 | PDF `file` 🔇 丢；http `image_url` 🔇 丢；data URL ✅ | `max_tokens`／`max_completion_tokens` 🔇 无视 | ① 面 cue 是条件追加 → 实现以为原生约束在位不补 cue | 【实测 2026-09-23】 | 01 §9.2；03 §3.3；04 §2、§4；05 §5 | 138–140、142、143 |
| Claude Sonnet（Kiro 渠道） | New API · Kiro 渠道 | ①④ | ⚠ 没测，按推断收进名单（缺口在翻译层，有意例外） | ⚠ 同 opus 推断 | ⚠ | ⚠ | ⚠ | ⚠ | — | — | ⚠ 推断【实测 2026-09-23 仅 opus】 | 01 §9.2 第 5 条 | — |
| claude-opus-4-6 | New API · CC 渠道（`[CC量]`，推测 Claude Code 通道，未证实） | ④ | 思考 ✅ 有文本；`display:"omitted"` ✅（块在文本空）；`effort` low／max 分不开（745–1,804 vs 768–1,929）；`bogus`／思考时 `temperature:0.3` 🔇 200 | 篡改 `signature` 200 🔇 不校验；`budget_tokens ≥ max_tokens` 200；回传 ✅ | 🔇 `output_config.format` 无视（散文） | 不带思考 ✅ 全调用；带 adaptive 非流式 3／8、流式 4／8 时好时坏（不判不发） | web_search 单挂 ✅ 真搜（要求搜才搜，改写句子不触发不劫持）；+ 函数工具流式 ✅；web_fetch ✅ 有 `server_tool_use` 块；code_execution 🔇 丢无块 | PDF ✅；纯文本 `document` 读到无 citations；URL 图 🔇 丢；base64 ✅ | `max_tokens` ✅ | 缓存真（第二次 `cache_read` = 前缀）；「Say OK.」9–10 token | 【实测 2026-09-23】curl（无 live 文件） | 01 §9.2；03 §3.3；04 §2、§4；05 §5；06 §1 | 137、147、150 |
| claude-opus-5 | New API · CC 渠道 | ④ | 思考 ✅ 但 **thinking 文本恒为空**（带 `display:"summarized"`、难题 765 输出 token 也空）；其余同 opus-4-6 | 同 opus-4-6 | ✅ `output_config.format` **执行**（2／2）——同渠道两款不同 | 同 opus-4-6 | 同 opus-4-6 | 同 opus-4-6 | `max_tokens` ✅ | 按思考计费却无思考文本可显示 🔇 | 【实测 2026-09-23】 | 01 §9.2 第 5 条；03 §3.3；04 §2 | 149、150 |
| claude-opus-4-6 ／ -5 | New API · CC 渠道 | ① | `max`／`none` 🔇 不想（转换层） | `reasoning_content` | 🔇 `response_format` 丢（转换层） | 同 ④ 形 | `web_search_options` ✅ 答案引了搜索结果 | PDF ✓（画像 `pdfInput` ✓） | — | — | 【实测 2026-09-23】 | 01 §9.2；04 §2；05 §5 | 140、142 |
| claude-opus-4-6 ／ -5（含 `-thinking` 变体） | New API · anti 渠道（`[anti量]`，推测 Antigravity，未证实） | ④ | ❌🔇 **任何思考参数都不想**（`-thinking` 变体也不）；乱写 effort／温度 200 | 没有 thinking 块；`budget_tokens ≥ max_tokens` 200；未测回传 | 🔇 `output_config.format` 无视 | 强制两条路径都不实现：不带思考 0／0、带思考 0 → 降 `auto` | web_search 单挂 🔇 丢（凭记忆答「As of my latest information (July 2025)…」）；+ 函数工具 🔇 丢；web_fetch 🔇；code_execution 🔇 | PDF 🔇 丢，纯文本 `document` 也丢；URL 图 ❌ 500 `failed to decode base64 data`；base64 ✅ | `max_tokens` ④ ✅ | 约 30 token 注入（「Say OK.」输入 39）；没有任何缓存字段、两次全价；UI 档位全是摆设 | 【实测 2026-09-23】curl | 01 §9.2；03 §3.3；04 §2、§4；05 §5；06 §1 | 148、151 |
| 同上 | New API · anti 渠道 | ① | 🔇 不想 | — | 🔇 `response_format` 丢 | 非流式 5 次 1 次、流式 0 | `web_search_options` 🔇 无效 | PDF ✗ | `max_tokens` ① 🔇 **无视**（同渠道两面转换不同） | — | 【实测 2026-09-23】 | 01 §9.2；04 §4；05 §5 | 151 |
| claude-opus-4-6 ／ -5 | New API · AWSb 渠道（`[正向AWSb量]`，AWS Bedrock 正向；消息 id `msg_bdrk_`；= Bedrock 部署变体） | ④ | 思考 ✅ **真分档**：low 6／207，max 1,037–1,156 输出 token；`display:"omitted"` ✅；乱写 effort／思考时 `temperature:0.3` ❌ 400 与官方同文（`Input should be 'low', 'medium', 'high' or 'max'`）；`budget_tokens ≥ max_tokens` 200（正向也不校验） | 篡改 `signature` ❌ 400 `Invalid signature in thinking block`（校验）；回传 ✅ | ✅ `output_config.format` 执行 | 强制 ✅／✅（不带思考／带 adaptive 全调用） | web_search／web_fetch／code_execution ❌ **各 400 整条请求** `Input tag 'web_search_20250305' … does not match`（Bedrock 不提供任何 Anthropic 服务端工具） | PDF ✅（要 30 s）**返回 `citations`**（四渠道唯一）；URL 图 ❌ 400 `URL sources are not supported`；base64 ✅ | `max_tokens` ✅ | 缓存真；「Say OK.」10 token；正向缺口会响，唯一「按 400 学降级」生效的渠道 | 【实测 2026-09-23】curl | 01 §9.2 第 4 条；03 §3.3；04 §2、§4；05 §5；06 §1 | 147、150 |
| 同上 | New API · AWSb 渠道 | ① | `max`／`none` 🔇 不想（转换层） | — | 🔇 `response_format` **照丢**（④ 面执行 schema、① 丢——同渠道同模型随面不同） | 强制 ✅ | `web_search_options` ❌ 400 | PDF ✓ | — | — | 【实测 2026-09-23】 | 01 §9.2；04 §2 | 150 |
| claude-opus-4-6 ／ -5 | New API · 官key 渠道（`[官key量]`） | ④① | ⚠ 未测 | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | ❌ 当天两个端点全 502 `Upstream request failed`；画像 official 无格子 | 【实测 2026-09-23】（502） | 01 §9.2「五个渠道」 | — |
| Claude（经中转，后端 Claude） | 某中转（Joycai 线上流量，未具名） | ① | — | — | — | 畸形：`arguments` 背靠背多对象 `{}{"id":1}`（先吐空对象再给真参数）；调用 id 空串 `""`，同批共用 → 下一轮重复 `tool_call_id` 400、此后每轮 400 | — | — | — | 工具以空参数执行不报错 🔇 | 【实测 2026-08-08】【实测 2026-08】 | 05 §3；02 §3.2 | 105、106 |
| Claude opus-4.5（点号 id `anthropic/claude-opus-4.5`） | 任意中转（id 拼法为点号） | ④ | — | — | 结构化名单只写连字符 id 时点号 id 🔇 静默不命中 → 名单列两种拼法 | — | — | — | — | 静默不命中 | 【实现】 | 04 §2 | 183 |

### 随平台变化的特性

- **思考有没有、有没有文本**：官方／OrcaRouter／AWSb／CC opus-4-6／Kiro 有文本；CC opus-5 按思考计费但文本恒空；anti 渠道任何参数都不想（`-thinking` 变体也不）；Kiro `effort` 只两态（`low` 真变浅，其余等价），AWSb 真分档。【实测 2026-09-23】坑 141、148、149
- **签名校不校验**：官方（经 OrcaRouter 原样）与 AWSb 改签名 400；Kiro／CC 篡改、删签名都 200——回传出错在反代上不响，只能看日志存下的块。【实测 2026-09-23】【实测 2026-09-26】坑 137
- **结构化 `output_config.format`**：官方五款守 enum、AWSb 执行、CC 按型号（opus-5 执行、opus-4-6 无视）、Kiro／anti 无视；① 面 `response_format` 在整台 New API 四渠道都丢（转换层），连 ④ 面执行 schema 的 AWSb 也丢。【实测 2026-09-23】【实测 2026-09-26】坑 142、150
- **服务端工具四种答案**：Kiro 劫持（单挂）／真搜（+函数工具流式）／假装执行；CC 真搜真抓、code_execution 丢；anti 全丢凭记忆答；AWSb 整条 400；官方经 OrcaRouter 真搜且不需 beta 头。【实测 2026-09-23】【实测 2026-09-26】坑 139、144
- **PDF／URL 图片**：AWSb 读 PDF 且唯一返回 `citations`、URL 图 400；CC 读 PDF、URL 图丢；Kiro 与 anti PDF 丢（anti 连纯文本 document 也丢）、URL 图 Kiro 丢 anti 500；OrcaRouter 四面都读 PDF；全台可移植的只有 base64 图。【实测 2026-09-23】【实测 2026-09-26】坑 143
- **`max_tokens` 与计费**：Kiro 无视且 `cache_control` 只写不读；anti ① 无视 ④ 生效、无缓存字段、每请求注入 ~30 token；CC／AWSb 生效且缓存真。【实测 2026-09-23】坑 145、151
- **「发 X 会不会 400」**：官方对未知顶层键、`thinking.type:"bogus"`、非法 schema 关键字 400；经 OrcaRouter 全部 200（网关重新序列化）、回包却是 Anthropic 原样——乱写 200 不能判成反代。【实测 2026-09-26】坑 174、182

## 5 Gemini

### 家族固有特性（跨平台一致）

- 思考控制 `generationConfig.thinkingConfig.thinkingLevel: LOW／MEDIUM／HIGH`（全大写；小写 `thinking_level` 属 Interactions API）；发 level 必带 `includeThoughts: true`（否则付钱看不见思考）；`thinkingBudget`（2.5 代 `extended` 方言）与 `thinkingLevel` 只发一代。【文档】【参考实现】详见 03 §2、§3。
- `MINIMAL` 不是每个型号都有，缺时 400 非降级（3.8 Flash 实测、3.1 Pro 文档）且文档明说 minimal ≠ 关闭；「关闭」映射到 `LOW`。旧：2026-09-26 前 off → `MINIMAL` → 新：`LOW`。【实测 2026-09-26】【文档】坑 170，详见 03 §2。
- 回传义务：`_geminiModelParts` 整组原始 parts 原样回灌（含 thought parts 与 `thoughtSignature`）；不回传 → 200 + `finishReason: MISSING_THOUGHT_SIGNATURE`（旧型号）或 HTTP 400 `Function call is missing a thought_signature in functionCall parts`（3.8 Flash）——两种都要认成「我方丢了签名」；并行调用签名只在第一个 `functionCall` part，流式落在末块 `{text:"", thoughtSignature}`。【参考实现】【实测 2026-09-26】坑 173，详见 03 §5、05 §3。
- 流：每个 chunk 是完整响应对象非 delta；`functionCall` 一次给全、args 是对象；旧型号无 id（适配器自造）、3.8 Flash 起带 `id`；`functionResponse` 靠函数名匹配。【文档】【实测 2026-09-26】详见 02 §2.2、§3.2。
- usage：`thoughtsTokenCount` 在 `candidatesTokenCount` 之外（output 相加）；`toolUsePromptTokenCount` 在 `promptTokenCount` 之外（input 相加）；【文档】每 chunk 带计数、【实测 2026-09-26】Vertex 流式只末块带——取最后见到的值。坑 18、191，详见 06 §1。
- 结构化：`responseMimeType:"application/json"` + cue 双发（有旧型号静默无视 mimeType）；`responseJsonSchema`（标准 JSON Schema）或旧 `responseSchema`（OpenAPI 方言）互斥只发一个。【实测／经验】详见 04 §2。
- 内置工具是 `tools[]` 里与 `functionDeclarations` 并列的独立项 `{googleSearch:{}}`／`{urlContext:{}}`／`{codeExecution:{}}`；无 `max_uses` 等价物；`googleSearch` 按查询条数计费（约 $0.014／条，条数模型定）；「搜没搜」只认 `webSearchQueries`；代码 part 随历史回传占上下文。【实测 2026-09-26 仅 Vertex 经 OrcaRouter】坑 178、190、194、195，详见 05 §5。
- `defer_loading` 字段整个被拒（第三方报告 ⚠）。坑 69，详见 05 §7。
- 三层错误：`promptFeedback.blockReason`、拦截类 `finishReason`（SAFETY 等）、请求缺陷（`MISSING_THOUGHT_SIGNATURE`／`UNEXPECTED_TOOL_CALL`／…）。【文档】详见 06 §2。
- 请求键 Google 官方两种拼写都收；New API ③ 面只认 camelCase（平台差异，见表）。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.8 Flash（`google/gemini-3.8-flash`） | OrcaRouter · ③ 线路（**Vertex AI 原样**，不是 AI Studio） | ③ | `thinkingLevel` LOW／MEDIUM／HIGH ✅ 单调（`thoughtsTokenCount` 193／641／1,348，不发 685）；`MINIMAL` ❌ 400 `Thinking level MINIMAL is not supported for this model.`；`thinkingLevel:"BOGUS"` ❌ Vertex 原文 400；`thinkingBudget: 0` 🔇 照想 312 token（网关重序列化把 0 当空值 ⚠）；回退实测不设 1,980／高 4,973／关(=低) 1,977／高+提示 1,830（3／5 对）／关+提示 1,300（5／5）——不设与关闭分不开 | 思考摘要一个整段 `{text, thought:true}` part（流式不逐字）；`thoughtSignature` 挂正文 text part、流式末块 `{text:"", thoughtSignature}`；`functionCall` 缺签名 ❌ HTTP 400 `Function call is missing a thought_signature…`；流末光秃秃 `{text:""}` 回灌 ❌ 400 `required oneof field 'data' must have one initialized field`（网关还是 Vertex ⚠） | ✅ `responseJsonSchema` 守住回 `red`；旧 `responseSchema` 也守；strict 风格 200；与 `googleSearch` + `responseMimeType` 同发 200 | `functionCall` 带 `id`（`call_1626125`）；`functionResponse` 带不带 id 都 200；`mode:"ANY"` 与内置工具同发 200（先搜再调函数）；并行只第一个 part 带签名 | googleSearch ✅ 真搜（`groundingMetadata`；`uri` 是 `vertexaisearch` 跳转、`title` 是域名）；codeExecution ✅（`executableCode` → `codeExecutionResult`，代码 part 回灌 200）；urlContext ✅（`urlContextMetadata` 首块、末块 `groundingChunks` 真实 uri、无 `webSearchQueries`）；三者与函数工具同发 200 | `inlineData` 与 `inline_data` 都看得见图；16×16 PNG 记 1,098 prompt token；PDF `inlineData`+`application/pdf` ✅ 一页按图像计 520 token | 目录 1,048,576／65,536；usage 只末块带计数；`toolUsePromptTokenCount` 另计（20+65+77=162）；`trafficType:"ON_DEMAND"`；搜索约 $0.014／条（一题 6 条 $0.084；旧：一次 $0.028 按请求）；末块 `usageMetadata.costUsd` 需 `X-OrcaRouter-Include-Cost: true` | `thinkingBudget:0` 不关；`:countTokens` 被当 `generateContent` 执行并计费（$0.0028）；错误信封改写成 OpenAI 形 `type:"invalid_argument"`、路径 `***`；不带 `alt=sse` 也回 SSE | 【实测 2026-09-26】【实测 2026-09-28】 | 03 §2、§2.1、§4、§5；02 §1、§2.2、§3.2；04 §2；05 §3、§5；06 §1、§2 | 170–173、176、177、178、186、190–195、197、203、204 |
| Gemini 3.8 Flash | OrcaRouter · ① 线路（翻译层） | ① | 不返回思维链、只报 `reasoning_tokens` | — | ⚠ | 发无 `parameters` 的 function 工具名 `googleSearch`／`urlContext`／`codeExecution` → 网关换成原生内置工具（网关约定）📄 | 同左 📄 | `video_url` 🔇 **200 但静默丢弃**：三次答错、输入 token 25 → 25 不变（Gemini 本身读视频，丢在 ① 翻译层，回答照示例格式瞎编）；PDF 经 ① 只算推断 | 目录同上 | 视频静默丢（最坏一种） | 【实测 2026-09-26】【实测 2026-09-28】；保留函数名【文档 2026-09】 | 01 §9.5；02 §1；05 §5 | 205 |
| Gemini 3.1 Pro | Google 官方 | ③ | 📄 档位只有 `low／medium／high`（无 minimal） | — | — | — | — | — | — | — | 【文档】 | 03 §2 | 170 |
| Gemini 2.5（家族） | Google 官方 | ③ | 📄 方言 `extended` 同形（固定 `thinkingBudget`） | — | — | — | — | — | — | — | 【参考实现】 | 03 §3 | — |
| Gemini 2.x | Google AI Studio | ③ | — | — | — | — | 与函数工具同发内置工具的问题 ⚠ 未测（有意接受的风险）；`googleSearch` 官方「未实测、照发」 | — | — | ⚠ | 【未测】 | 05 §5 | — |
| Gemini 旧型号（3.8 Flash 之前，泛指） | Google 官方 | ③ | — | `functionCall` 无 id、`functionResponse` 靠函数名匹配（同名并行调用结果对应不可表达）；丢 `thoughtSignature` → 200 + `finishReason: MISSING_THOUGHT_SIGNATURE` | 有模型 🔇 静默无视 `responseMimeType`（故 cue 双发；型号与日期未给 ⚠） | 适配器自造 `gtc_${Date.now()}_${n}` | — | — | `inputTokenLimit`／`outputTokenLimit` per-model 端点直接给 | 缺签名不是 400；mimeType 无视 | 【参考实现】【实测／经验，日期未标】⚠ ⏳待复核 | 02 §1、§2.2、§3.2；03 §5；04 §2；06 §6 | 173 |
| Gemini（任意型号） | New API 中转站 · Gemini 面（③ 形状中转） | ③ | — | — | — | — | — | 只认 camelCase：snake_case 请求 🔇 200 照回，**图片和系统提示静默丢弃** | — | snake_case 静默丢 | 【实测 2026-09-05】 | 02 §2.2 | 2、111 |

### 随平台变化的特性

- **请求键拼写**：Google 官方 `inlineData`／`inline_data` 两种都收（Vertex 经 OrcaRouter 也都收）；New API ③ 面只认 camelCase，snake_case 200 但图片与系统提示静默丢。【实测 2026-09-05】【实测 2026-09-26】坑 2、111
- **视频输入**：Gemini 本身读视频，经 OrcaRouter ① 翻译层 200 静默丢弃（输入 token 不变）；③ 线路未测视频。【实测 2026-09-28】坑 205
- **缺签名报法**：旧型号 200 + `MISSING_THOUGHT_SIGNATURE`；3.8 Flash（Vertex 经 OrcaRouter）HTTP 400——两代型号形态不同。坑 173
- **网关特有**：`:countTokens` 被当生成计费、`{text:""}` 空 part 回灌 400、`thinkingBudget:0` 关不掉、报价需 `X-OrcaRouter-Include-Cost` 头——只对 OrcaRouter 成立，不照搬给 AI Studio。【实测 2026-09-26】坑 171、172、176、186

## 6 Grok

### 家族固有特性（跨平台一致，仅测于 xAI 官方）

- ② `reasoning.effort` 默认 `high`；4.5／4.6 **拒 `none`**（400，本来关不掉思考）；4.3／4.5／4.6 全部拒 `max`（400）；未知顶层键忽略；流里有 `response.completed` + `[DONE]` 收尾。【实测 2026-09】坑 66，详见 03 §7.1、02 §7.2、01 §9.1。
- 加密推理须发 `include:["reasoning.encrypted_content"]` 才有 `encrypted_content`；缺了第二轮照样 200 且答对（缺的只是推理延续）。【实测 2026-09】详见 03 §7.3。
- 图片输入总像素 ≥512（16×16 拒、32×32 过），宽高各 ≥8。【实测 2026-09】坑 67。
- 推理模型上发 `frequency_penalty` 实测 200 未报错（文档说会报错）——文档：报错；实测：200。【实测 2026-09】详见 01 §9.1。
- `tool_search`／`defer_loading` ❌ 403（仅 alpha 用户）。【实测】坑 —，详见 05 §7。
- ④ `/v1/messages` 官方标完全弃用；① 官方标 Deprecated（仍作 legacy）。【文档】详见 01 §9.1。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| grok-4.5 ／ 4.6 | xAI 官方 `https://api.x.ai/v1` | ② | 默认 `high`；`none` ❌ 400（关不掉）；`max` ❌ 400 | `include:["reasoning.encrypted_content"]` 必发才有密文；不带回传第二轮 200 | ⚠ | ⚠ | web_search ✅（`web_search_call` `open_page`／`find_in_page`，一次 6,851 输入；`server_side_tool_usage_details` 按次）；`tool_search`／`defer_loading` ❌ 403 | 图片 ≥512 像素总数 | `frequency_penalty` 200（文档说报错） | 「关闭」芯片必然 400（UI 要写明） | 【实测 2026-09】【实测，日期未标】⚠ ⏳待复核 | 01 §9.1；03 §7.1、§7.3；05 §5、§7；06 §1 | 66、67 |
| grok-4.3 | xAI 官方 | ②；①（legacy） | ② `max` ❌ 400 | — | ⚠ | ⚠ | 同上 | ① `video_url` ❌ 400 `Empty content block`（片段被当空块） | ⚠ | 视频 400 会响 | 【实测 2026-09】；视频【实测 2026-09-28】 | 01 §9.1；02 §1 | 206 |

### 随平台变化的特性

- 只在 xAI 官方测过，无跨平台对比；Grok Imagine 出图／视频（2.0 `quality`／`resolution`、`cost_in_usd_ticks`；1.5 视频 $0.08/s）不在本表（🖼🎬 见 13、14 篇）。坑 123–129

## 7 DeepSeek

### 家族固有特性（跨平台一致）

- ① 档位表**没有 `none`**：`reasoning_effort:"none"` 🔇 被无视照想照计费；只有顶层 `thinking:{type:"disabled"}` 关得掉（Joycai 2026-09-05 按文档修复，**未实测** ⚠）；`medium` 折进 `high`。【文档 2026-08】详见 03 §2、§5。
- 回传义务分场景**两个方向都 400**：有工具调用的轮次 `reasoning_content` 必须回传（官方原文「若您的代码中未正确回传 reasoning_content，API 会返回 400」）；无工具轮次不要携带（400 `reasoning_content is not allowed in the input messages`；新版部分改为忽略但不可依赖）。【文档 2026-08】坑 1（对比），详见 03 §5。
- 结构化：`json_object` 需 "JSON" 字样（同 OpenAI）；**不支持 `json_schema`**。【文档】详见 04 §2。
- usage 顶层 `prompt_cache_hit_tokens`／`prompt_cache_miss_tokens`，无标准 `cached_tokens`，`prompt_tokens` 已含命中（只读标准拼写 = 命中按全价记）。【文档；Joycai 2026-09-14 修复】详见 06 §1。
- V4：按错误文案里的参数名识别「强制被拒」的学习机制用得上。【文档】详见 04 §4。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek 推理系（`deepseek-flash` 实测视频） | DeepSeek 官方 | ① | `none` 🔇 无视；`thinking:{type:"disabled"}` 📄 关（未实测 ⚠）；`medium` 折 `high` | `reasoning_content`；有工具轮不回传 ❌ 400，无工具轮携带 ❌ 400 | 📄 `json_object`（需 "JSON"）；`json_schema` 不支持 | 📄 V4 错误文案点名参数 | 无（官方无服务端工具字段） | `video_url` ❌ 422 `unknown variant video_url, expected one of text, image_url, file` | `prompt_cache_hit_tokens`／`miss_tokens` 顶层 | `none` 无症状；缓存命中按标准拼写读会全价记 | 【文档 2026-08】；视频【实测 2026-09-28】 | 03 §2、§5；04 §2；06 §1；02 §1 | 206 |
| `deepseek-v4`（DashScope 托管） | 阿里百炼 DashScope | ② | ⚠ | ⚠ | ⚠ | ⚠ | `code_interpreter` ✅ ② 面按模型 id 放行 | ⚠ | ⚠ | — | 【实测 2026-09-17】 | 05 §5 | — |

### 随平台变化的特性

- **服务端工具**：DeepSeek 官方无任何服务端工具；同一家族的 `deepseek-v4` 托管在百炼时 ② 面 `code_interpreter` 放行——「能不能联网／跑代码」是 (平台, 面) 属性不是模型属性。【实测 2026-09-17】
- 官方 ① `video_url` 422 会响；其余平台未测。【实测 2026-09-28】坑 206

## 8 Qwen（千问）

### 家族固有特性（跨平台一致，仅测于 DashScope 百炼）

- 同一端点两代思考控制不同：Qwen3-Max／Qwen3-Plus 等商业款**默认关**，`switch` 方言 `enable_thinking: bool` 顶层（停发 `reasoning_effort`）；Qwen3.5+ **默认开**；Qwen3.7+ 直接接受标准 `reasoning_effort`（与 `thinking_budget` 互斥）；部分开源模型思考模式强制 `stream: true`。【文档／参考实现】坑 9，详见 03 §3 `switch`。
- 思考开启时 `tool_choice` 只接受 `auto／none`【文档】→ 只在本次真发 `enable_thinking:true` 时降 `auto`。详见 04 §4。
- 结构化：`json_object` 全线可用；缺 "json" 字样 ❌ 400 `'messages' must contain the word 'json'`；`json_schema` 只最新两三代商业款。【文档】详见 04 §2。
- ① 私有顶层 `enable_search: true`（无痕：不返回来源、不支持角标、无 `max_uses`）、`search_options:{search_strategy:"agent_max"}`、`enable_code_interpreter: true`；`agent_max`／`enable_code_interpreter` 与 `tools` 同发 ❌ 400 `Agent mode does not support tools…`；`enable_code_interpreter` 非流式 ❌ 400。【实测 2026-09-17】坑 10、74，详见 05 §5。
- ② 面 `tools:[{type:"web_search"}]`、`web_extractor`（仅当 `web_search` 同在）、`web_search_image`／`image_search`（可单独，按次价 6–12 倍）、`code_interpreter`（思考关闭 → 200 后 `response.failed`）；Responses 面无 `encrypted_content`，回传明文 `summary`；文档有 `reasoning_text.delta`；文档无 `text` 字段（报错还是忽略未验 ⚠）。【文档】【实测 2026-09-17】坑 70、76，详见 03 §7.2、§7.3、05 §5、04 §5.1。
- 视频 `video_url` + 片段旁 `fps`（私有扩展，发起者）；`vl_high_resolution_images` 私有。【文档】详见 02 §1。
- 一把 key 三张 chat 脸：① `/compatible-mode/v1`、Ⓓ `/api/v1/services/aigc/text-generation/…`、④ `/apps/anthropic/v1/messages`（只服务模型子集）；协议可用性按模型分。【文档 2026-09】详见 01 §8.1。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3-Max ／ Qwen3-Plus 等商业款 | 阿里百炼 DashScope compatible-mode | ① | 📄 默认关；`enable_thinking: bool` 顶层（`switch`），停发 `reasoning_effort`；`thinking_budget` 不接 | ① `reasoning_content` | 📄 `json_object` ✅（缺 "json" 400）；`json_schema` 只最新两三代 | 思考开时 `tool_choice` 只 `auto／none` 📄 → forced 降 `auto` | 见 Qwen（通用）① 行 | 图片 ① 标准 | — | 不发开关就永不思考 🔇 | 【文档／参考实现】 | 03 §3；04 §2、§4 | 9 |
| Qwen3.5+ ／ Qwen3.7+ | 阿里百炼 DashScope compatible-mode | ① | 📄 默认开；3.7+ 收标准 `reasoning_effort`（与 budget 互斥）；部分开源版思考模式强制 `stream:true` | 同上 | 同上 | 同上 | 同上 | — | — | 强度在老款静默无效 🔇 | 【文档】 | 03 §3 | 9 |
| Qwen（通用） | 阿里百炼 DashScope compatible-mode | ① | 同上两行 | 同上 | `json_object` ✅；缺 "json" ❌ 400 | 同上 | `enable_search:true` ✅ 但无痕（无来源无角标）；`agent_max` 与 `tools` 同发 ❌ 400 `Agent mode does not support tools…`；`web_search_image`／`image_search` 猜的字段 🔇 静默忽略；`enable_code_interpreter` 非流式 ❌ 400 `Non-streaming mode does not support Code interpreter.`、带函数工具 ❌ 400、思考关闭照常跑（与文档不符）、无痕（prompt_tokens ~30 → 700–1600） | `video_url` ✅（见 qwen3-vl-plus）；PDF 仅 qwen3.8-max | 按次价比 Anthropic 低三个数量级；无上限字段 | 搜索无痕；辅助请求继承服务端工具静默多花钱 | 【文档】+【实测 2026-09-17】 | 04 §2、§4；05 §5 | 10、74、77 |
| Qwen（通用） | 阿里百炼 DashScope | ② | ⚠ | 文档 `reasoning_text.delta`；无 `encrypted_content`，回传明文 `summary` 📄 | 文档无 `text` 字段（报错／忽略未验 ⚠） | — | `web_search` ✅；`web_extractor` 仅当 `web_search` 同在（单独 → 200 后首事件 `response.failed`）；`web_search_image`／`image_search` ✅ 可单独；`code_interpreter` ✅ 按模型 id（非流式可以、带函数工具可以、思考关闭 ❌ 200 后 `response.failed` `Normal mode does not support Code interpreter…`）；过程可见 | 文档说不支持 PDF（能力表无 `false` 格，待实测 ⚠） | `usage.x_tools.code_interpreter.count`；代码解释器限时免费但多轮推理 token 增 | `response.failed` 在 HTTP 200 里；画图链接（签名 OSS）约 12 小时过期、正文不带 | 【文档】【实测 2026-09-17】第六个样本 | 03 §7.2、§7.3；04 §5.1；05 §5；01 §9.2 | 70、76、78 |
| `qwen3-vl-plus` | 阿里百炼 DashScope | ① | — | — | — | — | — | `video_url` ✅ 200 答对；输入 token 34 → 1,241（带片段）→ 641（带 `fps: 1`）：**`fps` 生效**；对片段挑剔：320×240／10 fps 纯色 ❌ 400 `Invalid video file`，加噪或 640×480 就收 | — | 夹具太小误判「不读视频」 | 【实测 2026-09-28】第十九个样本 | 02 §1；15 百炼行 | 206–208 |
| `qwen3.8-max` | 阿里百炼 DashScope | ① | — | — | — | — | — | PDF `{type:"file", file:{file_data, filename}}` 镜像 ① 形状，**仅此款** | — | — | 【文中陈述】⚠ | 02 §1 | — |
| `qwen3.8-flash` ／ qwen3.8 全系 | 阿里百炼 DashScope | ① | — | — | — | — | `agent_max` ❌ 400 `does not support the "agent" search strategy`（不降级重试）；`enable_code_interpreter` ❌ 400（3.8 全系 ① 面不支持） | — | — | — | 【实测 2026-09-17】 | 05 §5 | 75 |
| `qwen3.8-flash` ／ qwen3.8 全系 | 阿里百炼 DashScope | ② | — | — | — | — | `code_interpreter` ✅（② 面支持到 3.8） | — | 一问约 1.1k token（不开约 30） | — | 【实测 2026-09-17】 | 05 §5 | 78 |
| `qwen3-max`（及日期版） | 阿里百炼 DashScope | ① | — | — | — | — | `agent_max` ✅ 收；不带策略的 `enable_search` 🔇 **根本没搜**（输入 29 token，凭记忆答）；`enable_code_interpreter` ✅（思考关闭也行，与文档不符） | — | — | `enable_search` 不搜无症状 | 【实测 2026-09-17】 | 05 §5 | 10 |
| `qwen3.5-plus` | 阿里百炼 DashScope | ① | — | — | — | — | `agent_max` ✅ 收 | — | — | — | 【实测 2026-09-17】 | 05 §5 | — |
| `qwen-max` ／ `qwen3-max-preview` | 阿里百炼 DashScope | ① | — | — | — | — | `enable_code_interpreter` 🔇 **静默忽略**（不报错、prompt 不变、答案没算过） | — | — | 静默忽略 | 【实测 2026-09-17】 | 05 §5 | 75 |
| qwen3.5–3.7 plus／max／flash、部分开源版 | 阿里百炼 DashScope | ①／② | — | — | — | — | 代码解释器实测正则表放行（锚定，防 `qwen3.5-omni-plus`、`qwen3-vl-plus` 误中；下一代不预放行） | — | — | — | 【实测 2026-09-17】 | 05 §5 | 75 |
| Anthropic 面模型子集（具体哪些未给） | 阿里百炼 `/apps/anthropic/v1/messages` | ④ | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | 只服务模型子集 | 【文档】 | 01 §8.1 | — |
| Qwen-Audio | 阿里百炼 DashScope | Ⓓ 私有面 | — | — | — | — | — | 仅私有面可用 | ⚠ | — | 【文档】 | 01 §8.1 | — |
| Qwen（同步 ASR：qwen-audio-3.0-asr-flash 等） | 阿里百炼 | 🎤 | — | — | — | — | — | 同步接口 🔇 静默忽略 `diarization_enabled`；无句级时间戳 | — | 分离只走 `-filetrans` | 【实测】 | 16 §4.1、§7 | 115、116 |

### 随平台变化的特性

- 千问只在百炼一个平台测过，「随平台变化」体现为**同一端点随面与型号变化**：`code_interpreter` ① 面按型号「跑（qwen3-max）／静默忽略（qwen-max、qwen3-max-preview）／400（qwen3.8 全系）」，② 面到 3.8 都跑；`agent_max` 3.8-flash 400、3-max／3.5-plus 收；`enable_search` 不带策略在 qwen3-max 根本没搜。【实测 2026-09-17】坑 10、75
- 思考控制按代：商业款默认关要 `enable_thinking`，3.5+ 默认开，3.7+ 收 `reasoning_effort`——参数按模型 id 预填，不能靠族默认。坑 9
- 对比火山方舟：把千问的 `enable_thinking:false` 挂到豆包被静默忽略照想照计费（坑 114）；方舟 ① `none` 关得掉、千问要开关。

## 9 GLM（智谱）

### 家族固有特性（跨平台一致，仅测于智谱自家端点）

- 思考控制按代三种（① 面，全部默认开）：**5.3 代**（5.3／5.3-flash／5.3-flashx）不能关（`disabled` 400），`reasoning_effort` 只收 `low／high／max` 真分档（~30／50／~120 推理 token），其余值含 `none`／`medium` 400、文案一律「不支持关闭思考」不指向值；**5.2** 关 `thinking:{type:"disabled"}`，七值都收但 `low／medium` 折 high、`xhigh` 折 max（实有两档），`none` 🔇 关不掉（文档说放弃思考——文档与实测冲突）；**4.5／4.5-air／4.6／4.7／5／5-turbo／5.1** 关 `thinking:{type:"disabled"}`，`reasoning_effort` 任何值（含乱写）200 🔇 静默丢弃，`high` + `disabled` 同发不报错（豆包 400）。按族默认 `reasoning_effort` 在 11 款上全错，必须按模型 id 预填。【实测 2026-09-19，11 款】坑 94、95，详见 03 §3.1。
- `thinking.clear_thinking` 默认 `true`（丢历史轮 `reasoning_content`），`false` = 保留式思考、跨轮原样回传全部历史推理；厂商推荐 5.3-flash 用 `clear_thinking:false`；工具轮回传接受（交错思考，文档要求回传）；缺 `type` 只发 `{clear_thinking:false}` 自家端点 200（经千问转发在非 GLM 模型上 400）。【实测 2026-09-19】详见 03 §3.1。
- `usage.completion_tokens_details.reasoning_tokens` 4.5-air 从不给；glm-5／4.6／4.5 关思考时缺席（不是 0）。【实测 2026-09-19】详见 03 §3.1。
- 结构化：`json_object` 无 "json" 字样照常出合法 JSON；`response_format:{type:"json_schema"}` 🔇 200 静默无视（回 ```json 代码块、不合 schema）。【实测 2026-09-19】坑 98，详见 04 §2。
- tool_choice 砍档第三种变体：文档「默认且仅支持 `auto`」；实测按代不同（见表）→ 平台级无条件 forced 降 `auto`（400 文案 `1210 API 调用参数有误` 不提 tool_choice，「从 400 学降级」失效）。【实测 2026-09-19】坑 96、97，详见 04 §4。
- 对话内联网 `tools[]` 项 `{type:"web_search", web_search:{enable:true, search_engine, search_intent?, …}}`，结果在响应顶层 `web_search[]`；默认意图识别，意图不够不搜而模型照答「根据联网搜索结果……」→ 必须 `search_intent:false`；`count` 无效（`search_pro` 一次灌 50 条 ≈24k token、`search_std` ≈6.7k）。【实测 2026-09-19】坑 100，详见 05 §5。
- 错误：信封 `{"error":{"code":"1210","message":"…"}}` 业务码字符串；`finish_reason: "sensitive"`（同 content_filter）、`network_error`（流式中途失败不回错误码，必须 throw）、`model_context_window_exceeded`（按截断）；未知顶层字段一律放过；`temperature` 非法 → `temperature参数非法：限制数值范围[0,1]`。【实测 2026-09-19】【文档 2026-09】坑 99，详见 06 §2。
- 多模态：只有 5.3-flash／flashx 读图，其余文本模型收 `image_url` 直接 400；收 `video_url`、忽略 `fps`（更早样本，日期未标 ⚠）。【实测 2026-09-19】【实测，日期未标】 ⏳待复核详见 01 §9.4、02 §1。
- `max_tokens` 上界 400 生成前拒、不计费、报出范围（`max_tokens参数非法：限制数值范围[1,98304]`）：5.x 与 4.6／4.7 131,072；4.5-air 98,304；glm-4.5 实测 131,072（文档写 96K）。上下文：5.3／5.3-flash(x)／5.2 1M；5-turbo 204,800；5.1／5／4.7／4.6 200K；4.5 系列 128K。【实测 2026-09-19】详见 01 §9.4。
- 服务端工具归平台：独立端点 `/web_search`、`/reader`（应用执行，不受模型约束，见 §14）；在百炼／火山由平台执行搜索。【实测 2026-09-19】详见 05 §5。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glm-5.3 ／ 5.3-flash ／ 5.3-flashx | 智谱 BigModel · 按量 `/api/paas/v4` | ① | 默认开；**不能关**（`disabled` ❌ 400）；`reasoning_effort` 只收 `low／high／max` ✅ 真分档（~30／50／~120）；`none`／`medium`／乱写 ❌ 400「不支持关闭思考」（文案不指向值，连关思考的图片请求也这句） | `reasoning_content` 流出；工具轮回传接受；`clear_thinking` 默认 true | `json_object` ✅（不查 "json"）；`json_schema` 🔇 静默无视 | `required` 200 🔇 不强制、具名 200 🔇 不强制、`none` 🔇 5.3-flash 照调工具 → forced 降 `auto` | 对话内 `tools[]` `web_search` ✅（需 `search_intent:false`；结果顶层 `web_search[]`） | 5.3-flash／flashx 读图 ✅（5.3 文本款 `image_url` ❌ 400）；`video_url` 见下「GLM（型号未标）」行 | 上下文 1M；`max_tokens` ≤131,072（400 报范围） | json_schema 无视；`none` 无视；不搜却说搜了 | 【实测 2026-09-19】 | 01 §9.4；03 §3.1；04 §2、§4；05 §5；06 §2 | 94、95、97、98、100 |
| glm-5.2 | 智谱 BigModel · 按量 | ① | 默认开；关 `thinking:{type:"disabled"}` ✅；`reasoning_effort` 七值都收（乱写 400）：`low／medium` 折 high、`xhigh` 折 max（实有两档，`max` 多想 ~35%）；`none` 🔇 关不掉（与 `low` 一样多；文档：放弃思考，实测：照想） | 同上 | 同上 | 同 5.x（`required`／具名 200 不强制） | 同上 | `image_url` ❌ 400；`video_url` — | 上下文 1M；`max_tokens` ≤131,072 | `none` 关不掉 | 【实测 2026-09-19】 | 03 §3.1；04 §2、§4 | 94、95 |
| glm-5 ／ 5-turbo ／ 5.1 | 智谱 BigModel · 按量 | ① | 默认开；关 `thinking:{type:"disabled"}` ✅；`reasoning_effort` 任何值 🔇 200 静默丢弃；`high`+`disabled` 同发不报错；glm-5 非法 effort → 「API 调用参数有误，请检查文档」不点名 | glm-5 关思考时 `reasoning_tokens` 缺席（不是 0） | 同上 | `required` 200 🔇 不强制、具名 200 🔇 不强制 | 同上 | `image_url` ❌ 400；`video_url` — | 上下文 5-turbo 204,800、5.1／5 200K；`max_tokens` ≤131,072 | 档位是假控件 | 【实测 2026-09-19】 | 03 §3.1；04 §4 | 94、95、97 |
| glm-4.7 ／ 4.6 ／ 4.5 | 智谱 BigModel · 按量 | ① | 同上行（开关型，档位丢弃） | 4.6／4.5 关思考时 `reasoning_tokens` 缺席 | 同上 | `required` 200 🔇 不强制；具名：思考开时 ❌ 400 `1210 API 调用参数有误`（不提 tool_choice）、关时 200 🔇 不强制；`none` ✅ 生效 | 同上 | `image_url` ❌ 400；`video_url` — | 上下文 4.7／4.6 200K、4.5 128K；`max_tokens` 4.6／4.7 ≤131,072、glm-4.5 实测 131,072（文档 96K） | 具名 400 文案笼统，学降级失效 | 【实测 2026-09-19】 | 03 §3.1；04 §4；01 §9.4 | 94–97 |
| glm-4.5-air | 智谱 BigModel · 按量 | ① | 同上行 | `reasoning_tokens` 从不给 | 同上 | `required` ✅ **真强制**、具名 ✅ 真强制、`none` ✅——平台级降 `auto` 后失去其唯一真强制档（回退链兜住） | 同上 | `image_url` ❌ 400 | 上下文 128K；`max_tokens` ≤98,304 | — | 【实测 2026-09-19】 | 03 §3.1；04 §4 | 95 |
| GLM（型号未标） | 智谱 BigModel · 按量 | ① | — | — | — | — | — | 收 `video_url`、`fps` 🔇 忽略（更早的样本，型号未记） | — | `fps` 静默无效 | 【实测，日期未标】 ⏳待复核⚠ ⏳待复核 | 02 §1 表后 | 206、208 |
| glm-4.7 | 智谱 · Coding Plan `/api/anthropic` | ④ | 默认**不**思考（只回 text 块）——与 ① 面默认思考相反 | — | — | — | — | — | — | 默认值按「模型 × 面」问 | 【实测 2026-09-19】 | 03 §3.1；01 §9.4 | — |
| 11 款（同上） | 智谱 · Coding Plan ① `/api/coding/paas/v4`、④ `/api/anthropic`、② `/api/v1` | ①④② | ⚠（完整实测未覆盖） | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | ② `/api/v1/models` 是 Codex CLI 目录形（只列 3 个）；④ `/v1/models` Anthropic 形 | 同一把按量 key 200 但**扣套餐**；路径决定扣哪笔钱；套餐条款只许指定工具 | 【实测 2026-09-19 + 文档】 | 01 §9.4 | — |
| GLM（托管） | 千问百炼 ／ 火山方舟 | 视平台 | — | — | — | — | 由平台执行搜索（能不能联网是 (平台, 协议族) 属性，不能从模型 id 推） | — | — | — | 【实测 2026-09-19】 | 05 §5 | — |

### 随平台变化的特性

- **联网**：智谱自家端点靠对话内 `tools[]` `web_search`（且要 `search_intent:false`）或独立 `/web_search` 端点；同一 GLM 托管在百炼／火山时由平台执行搜索。【实测 2026-09-19】
- **默认思考**：glm-4.7 在 ① 面默认想、在 Coding Plan ④ 面默认不想。【实测 2026-09-19】
- **计费路径**：同一把 key 打 `/api/paas/v4` 扣余额、打 `/api/coding/paas/v4`／`/api/anthropic`／`/api/v1` 扣套餐，选错不失败只换一笔钱——必须分行。【实测 2026-09-19】

## 10 豆包 Seed（火山方舟）

### 家族固有特性（跨平台一致，仅测于火山方舟 · 套餐 base）

- ① 思考控制：默认开；`reasoning_effort` 收 `none／minimal／low／medium／high／xhigh／max`（乱写 400 并列出参数名）+ 顶层 `thinking:{type:"enabled"／"disabled"}`（`auto` ❌ 400 InvalidParameter）；`none`／`minimal`／`disabled` **真关**（0 推理 token）；`high` + `disabled` 同发 ❌ 400 `Invalid combination of reasoning_effort and thinking type`（关只发开关不带强度）；`enable_thinking:false`（千问拼法）🔇 静默忽略照想。【实测 2026-09-18】坑 114，详见 03 §3.2。
- ② 思考：默认开；关 `reasoning:{effort:"none"}`（三款都 0）；也认顶层 `thinking:{type:"disabled"}`；七档全收；`reasoning_tokens` 在 `usage.output_tokens_details`。【实测 2026-09-18】【实测 2026-09-23】详见 03 §3.2。
- ④ 思考：默认开；关 `thinking:{type:"disabled"}` 真关（`switch` 方言 ④ 拼法）；`adaptive`、`enabled + budget_tokens` 都收；`output_config.effort` 不报错（效果未比 ⚠）；什么都不发 = 在想。【实测 2026-09-18】【文档 2026-09】详见 03 §3.2。
- 取回／回传：① `delta.reasoning_content`（2.1 系、seed-evolving、2.0-lite-260428 起**只是摘要**）+ `delta.encrypted_content`（原文密文，整串落在某一 delta 上与摘要同帧）；回传须两者一起、`encrypted_content` 优先；只回摘要不报错但「推理效果下降」🔇（静默降级第四种载体）；② 整条 `reasoning` item 原样回传；④ thinking 块（签名按代，见表）；回传出错不响（篡改／删签名都 200）。【实测 2026-09-23】坑 133、137，详见 03 §3.2、§5。
- 强制 `tool_choice`（`required`／具名／④ `{type:"tool"}`）思考开时 200 但**推理 token 为 0**（🔇 静默跳过思考，与 MiniMax 拒绝相反）。【实测 2026-09-18】详见 03 §3.2、04 §4。
- 结构化：① `json_schema` 要发 `strict:true` 键（不带时 2.1-turbo 也越过）；守不守按型号（见表）。【实测 2026-09-23】坑 134，详见 04 §2。
- 多模态：读图 ① `image_url`（data URL）、④ `image` 块；PDF ①②④ 都读，`file_url` 三面都通（② `input_file.file_url`、① `{type:"file",file:{file_url}}`、④ `document`+`source:{type:"url"}`）——旧：「`file_url` 仅 ② 且只在按量 base」→ 新：三面都通（2026-09-23）；`file_id` ①② 假 id 404 `ResourceNotFound`、④ `source.type:"file"` 400；① 扁平 `{type:"file", file_data}` 400 `missing messages.content.file`；① 收 `video_url`（`fps` 在 4 秒片段上不改账单，未定论 ⚠）。【实测 2026-09-18】【实测 2026-09-23】【实测 2026-09-28】坑 206、208，详见 02 §1、01 §9.3。
- ④ 关思考时听温度：`0` = 等于没发（🔇 当未设）、`0.01`／`0.1`／`0.3` 收敛；开思考带温度 200 不收敛（官方 400）；① 面 `0` 生效。类目 `doubao-switch` 声明 `temperatureWhenOff:{zeroIsUnset:true}`。【实测 2026-09-28，2.0-mini 每档 20 次】坑 198、201，详见 03 §3.4。
- 服务端搜索：② `{type:"web_search"}`（文档要 `sources:["doubao"]`）、④ `web_search_20250305` + `max_uses` 真跑；① **无**（厂商页只列 Responses 与 Messages）。【实测 2026-09-18】详见 05 §5。
- 平台形态：套餐 base `/api/plan/v3`（① `/chat/completions`、② `/responses`、④ `/api/plan` + `/v1/messages`）与按量 base `/api/v3` 不通用（套餐 key 打按量 401）；套餐无 Files API；`GET /api/plan/v3/models` 404、④ `/v1/models` 对有效 key 401；套餐按模型裁剪且挑拼写（Seed 1.6 系 404 `UnsupportedModel`）；上下文 256k。【实测 2026-09-18】【实测 2026-09-23】坑 80、81、135、136，详见 01 §9.3。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| doubao-seed-2.0-pro（别名 `ark-code-latest`） | 火山方舟 · 套餐 `/api/plan/v3` | ① | 默认想（60–67 reasoning token）；`none`／`minimal` ✅ 真关 0；`low／medium／high／max／xhigh` 60–145 真分档；`thinking:{type:"disabled"}` 0；`enabled` 66；`auto` ❌ 400；`disabled`+`high` ❌ 400；`enabled`+`none` 0（effort 说了算）；`enable_thinking:false` 🔇 照想 | 回包 `reasoning_content` + `encrypted_content`；Joycai 不读不回传多轮未报错（静默降级） | ⚠ | ⚠ | ⚠ | ⚠ | ⚠ | 别家开关被静默无视 | 【实测 2026-09-18】 | 03 §3.2；01 §9.3 | 114 |
| doubao-seed-2.1-turbo | 火山方舟 · 套餐 | ① | 默认开（「用一句话说你好」想 590 token）；关 `disabled` 或 `none`／`minimal` ✅；七档收、乱写 400 列参数名；`medium` 真有一档（平凡题档位差被噪声淹没）；`high`+`disabled` ❌ 400；强制 tool_choice 思考开时 200 但推理 token 0 🔇 | `reasoning_content` **只是摘要** + `encrypted_content` 密文同帧（`{"delta":{"reasoning_content":"\n","encrypted_content":"djEN…"}}`）；两者一起回、密文优先；只回摘要 🔇 效果下降；换渠道能否解密、篡改密文报不报错未测 ⚠ | ✅ `json_schema` + `strict:true` 2／2 守住；不带 `strict` 🔇 1／2 越过 | 强制 200 但跳过思考 | ① 无服务端搜索 | PDF `file:{file_data, filename}` ✅；`file:{file_url}` ✅；`file:{file_id}` 假 id 404；扁平 `{type:"file", file_data}` ❌ 400；`video_url` ✅ | 上下文 256k；`max_tokens` 收 262,144；`reasoning_tokens` 在末尾 `choices:[]` chunk | 只回摘要静默降级；强制工具跳过思考 | 【实测 2026-09-18】【实测 2026-09-23】 | 03 §3.2；04 §2；02 §1；01 §9.3 | 133、134、137 |
| doubao-seed-2.0-lite | 火山方舟 · 套餐 | ① | 同 2.1-turbo ① 行 | 2.0-lite-260428 起 `reasoning_content` 只是摘要 | 🔇 strict **不守**（答真实值 + 多出字段）200 | 同上 | ① 无 | 同上 | 上下文 256k | 200 不守 schema | 【实测 2026-09-23】 | 04 §2；03 §3.2 | 134 |
| doubao-seed-2.0-mini | 火山方舟 · 套餐 | ① | 同 2.1-turbo ① 行 | 同上 | ✅ strict 守住 | 同上 | ① 无 | `video_url` ✅ 200 答对，输入 59 → 2,795 → 2,795（带 `fps:1`）：收，`fps` 不改这段账单（两种拼法、1 与 0.2 都同；4 秒片段可能在最少帧数之下 ⚠） | `max_tokens` 两族 ≤131,072（超了 400 报上限）；温度 `0`／`0.1`／`0.3` 收敛（17–19／20）、`1` 分散（9／20） | — | 【实测 2026-09-18】【实测 2026-09-23】【实测 2026-09-28】 | 03 §3.2、§3.4；04 §2；02 §1 | 134、208 |
| doubao-seed-2.1-turbo | 火山方舟 · 套餐 `/api/plan/v3/responses` | ② | 默认开；关 `reasoning:{effort:"none"}` ✅ 0 推理；也认 `thinking:{type:"disabled"}`；七档全收；标准 ② 写法原样可用 | 整条 `reasoning` item 原样回传（含 `encrypted_content`） | ✅ `text.format`（不带 strict）2／2 守住 | ⚠ | `{type:"web_search"}` ✅ 跑出 `web_search_call`；套餐不写 `sources` 也记 `usage.tool_usage_details.web_search.doubao` | `input_file.file_url` ✅、`file_id` 假 id 404；`input_image` ✅ | `reasoning_tokens` 在 `usage.output_tokens_details`（已含在 output） | 打 `/api/plan/responses` 是 404（路径少 `/v3`） | 【实测 2026-09-18】【实测 2026-09-23】 | 03 §3.2；04 §2；05 §5；01 §9.3 | 135 |
| doubao-seed-2.0-lite | 火山方舟 · 套餐 | ② | 同上 | 同上 | 🔇 `text.format` **不守** 200 | ⚠ | `web_search` ✅ 跑 | 同上 | — | 200 不守 schema | 【实测 2026-09-23】 | 04 §2；05 §5 | 134 |
| doubao-seed-2.0-mini | 火山方舟 · 套餐 | ② | 同上 | 同上 | 值守住、🔇 多出字段 | ⚠ | `web_search` ✅ 跑 | 同上 | — | 多出字段 | 【实测 2026-09-23】 | 04 §2；05 §5 | 134 |
| doubao-seed-2.0-lite ／ 2.0-mini | 火山方舟 · 套餐 `/api/plan` + `/v1/messages`（`x-api-key` 与 Bearer 都收） | ④ | 默认开；关 `thinking:{type:"disabled"}` ✅ 真关；`adaptive`／`enabled+budget_tokens` 都收；`output_config.effort` 不报错（效果未比 ⚠）；什么都不发 = 在想；强制 `{type:"tool"}` 200 但推理 token 0 🔇 | thinking 块 **没有 `signature`**（流式非流式都没有；原样回传照样 200） | ⚠ | 强制跳过思考 | `web_search_20250305` + `max_uses` ✅ 真跑：`server_tool_use` + `web_search_tool_result`（带 `encrypted_content`、**`url` 为空串**）；`usage.server_tool_use.web_search_requests` | `image` 块 ✅；`document` base64／`source:{type:"url"}` ✅；`source.type:"file"` ❌ 400（支持 `base64／text／url／content`） | 关思考 + `0` 🔇 等于没发（9–13／20）；`0.01`／`0.1`／`0.3` 收敛（17–20／20）；开思考 + `0.3` 200 推理照常、`0.01` 不收敛（10–13／20）；`/v1/models` 对有效 key ❌ 401 | `0` 温度当未设；开思考带温度不响 | 【实测 2026-09-18】【实测 2026-09-23】【实测 2026-09-28，2.0-mini 每档 20 次】 | 03 §3.2、§3.4；05 §5；06 §5；01 §9.3 | 136、198、201 |
| doubao-seed-2.1-turbo | 火山方舟 · 套餐 | ④ | 同上行 | thinking 块**带 `signature`**（非流式在块上、流式 `signature_delta`，`dj…` 开头与 ① `encrypted_content` 前缀相同，推测同一密文 ⚠）；工具轮回传原样／篡改末尾／删掉 **三种都 200** 🔇（不校验）；删签名是否让推理变差未验 ⚠ | ⚠ | 同上 | 同上 ✅ | 同上 | 同上 | 签名不校验 | 【实测 2026-09-23】 | 03 §3.2、§5 | 137 |
| doubao-seed-1-6-250615 ／ doubao-seed-1.6 ／ doubao-seed-code（Seed 1.6 系） | 火山方舟 · 套餐 | ① | — | — | — | — | — | — | `max_tokens` 照收 | ❌ 404 `UnsupportedModel`（「does not support the agent plan feature」） | 【实测 2026-09-18】【实测 2026-09-23】 | 01 §9.3；03 §3.2 | 81 |
| 豆包（对话） | 火山方舟 · 按量 `/api/v3` | ① | ⚠ 对话面至今未实测（手头只有套餐 key）——能力格记 `unknown`，不抄套餐 | ⚠ | ⚠ | ⚠ | ⚠ | `video_url` 没量到（大概率同样收，按规矩要样本 ⚠） | ⚠ | 按量 key 上传文件能否被套餐 key 引用未验 ⚠ | 【未测 2026-09-28】【文档】 | 01 §9.3；02 §1 | — |
| 豆包（对话） | 火山方舟 · 按量 | ②／④ | ⚠ | ⚠ | ⚠ | ⚠ | 未知【未验】；② 不写 `sources` 是否落到按次「联网内容插件」未验 ⚠ | ⚠ | ⚠ | — | 【未验】 | 05 §5 | — |

### 随平台变化的特性

- 豆包只在火山方舟**套餐 base** 测过，按量 base 对话面全部 `unknown`——「随平台变化」目前体现为**套餐 vs 按量**：key 不通用（套餐 key 打按量 401、按量 key 上传的文件套餐能否引用未验）、模型目录按套餐裁剪（Seed 1.6 系 404）、套餐无 Files API 与 Seedance。【实测 2026-09-18】【实测 2026-09-23】坑 80、81
- **同一端点随面**：服务端搜索 ② 与 ④ 有、① 无；`json_schema` 2.0-lite ①② 都不守、2.1-turbo ①② 都守、2.0-mini ① 守 ② 多字段；④ 2.0 系无 `signature`、2.1-turbo 有但不校验；温度 ① 面 `0` 生效、④ 面 `0` 当未设。【实测 2026-09-23】【实测 2026-09-28】坑 134、137、198
- **对比同为 ① 兼容的千问**：方舟 `reasoning_effort:"none"` 真关、千问要 `enable_thinking`；把千问方言挂到方舟「关」不报错只是失效。坑 114
- **对比官方 Claude（④）**：方舟 `disabled` 真关（Claude 5 拒收）、篡改签名 200（官方 400）、开思考带温度 200（官方 400）。【实测 2026-09-23】【实测 2026-09-28】坑 137、201

## 11 MiniMax

### 家族固有特性（跨平台一致，仅测于 MiniMax 国内站）

- ① 面**总在想**且不分离思维链：`<think>…</think>\n\n正文` 塞进 `delta.content` → 需 `<think>` 兜底切分器（只认响应开头、跨 chunk `danglingPrefix`、流末未闭合按 reasoning flush）；切出的只展示不回传。【实测 2026-09-28】【参考实现】坑 15，详见 03 §3.4、§6。
- ④ 面 `switch` 方言：只有 `thinking:{type:"adaptive"／"disabled"}`，无 `display`、无 `output_config`；思考**默认关**、真关。【实测 2026-09-28】详见 03 §3。
- 温度：**收下、不理会**（关思考 `0.01`／`0`／不发／`1` 分不开；开思考 + `0.3` 200 而非 400）；类目 `minimax` 不声明 `temperatureWhenOff`。【实测 2026-09-28，每档 20 次】坑 199、201，详见 03 §3.4。
- tool_choice 枚举只剩 `auto／none`，强制档不存在 → 无条件预判降 `auto`；思考开时拒绝强制工具。【实测 2026-08】详见 04 §4。
- 结构化：`json_object` 不查 "json" 字样。【实测 2026-08】详见 04 §2。
- 错误信封 `base_resp.status_code`（1004 鉴权失败／1008 余额不足／1002 限流，0 成功）——只认 `error` 会把过期密钥读成空回复；空 assistant 消息也 400。【实测 2026-08】坑 6，详见 06 §2。
- ④ 兼容端点服务端工具：停在 `*_tool_result` 块上报 `end_turn`（无 `pause_turn`）；**拒收自己发出的块** ❌ 400 `invalid params, tool result's tool id(...) not found` → transcript 纯文本续跑。【实测 2026-08】坑 11，详见 05 §6。
- ①／④ 两张 chat 脸模型 id 完全一致（分两行）。【文档 2026-08】详见 01 §8.1。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MiniMax-M3 | MiniMax 国内站 `/anthropic/v1/messages` | ④ | `thinking:{type:"adaptive"／"disabled"}`；默认关；真关；无 `display`／`output_config`；思考开时拒绝强制工具（降 `auto`） | — | ⚠ | 强制降 `auto` | 见 MiniMax（通用）④ 行 | ⚠ | 关思考 + `0.3` 200 没想；`0.01` 🔇 不收敛（10–11／20，与不发、`1` 分不开）；`0` 同样；开思考 + `0.3` 200（官方 400）、`0.01` 不收敛 → 温度收下不理会 | 温度静默不理；开思考带温度不响 | 【实测 2026-09-28，每档 20 次】 | 03 §3、§3.4；04 §4；15 MiniMax 行 | 199、201、202 |
| MiniMax-M3 | MiniMax 国内站 `/v1` | ① | ① 面总在想；`<think>…</think>` 混进 `delta.content` | 切出的 reasoning 只展示不回传 | — | — | — | ⚠ | 看不出温度；不发温度就 19–20／20 答同一种水果（缺省已收敛，那道题说明不了温度） | `<think>` 混进正文 | 【实测 2026-09-28】（温度）；【参考实现】（think 标签） | 03 §3.4、§6；06 §8 第 13 条 | 15、202 |
| MiniMax chat（通用，`switch` 方言端点） | MiniMax | ① | `<think>` 内联 | 同上 | `json_object` ✅ 不查 "json" | 枚举只 `auto／none`，强制档不存在 → 无条件降 `auto` | — | ⚠ | 空 assistant 消息 ❌ 400（需兜底文案） | `base_resp.status_code` 体内错误（1004／1008／1002）🔇 只认 `error` 读成空回复 | 【实测 2026-08】【文档 2026-08】 | 04 §2、§4；06 §2；01 §8.1 | 6、15 |
| MiniMax（通用） | MiniMax ④ 兼容端点 | ④ | 同 M3 ④ | — | — | — | 停在 `*_tool_result` 报 `end_turn`（无 `pause_turn`）；回灌自己发出的块 ❌ 400 `invalid params, tool result's tool id(...) not found` → transcript 纯文本续跑（丢 citation，每次续跑全新计费） | ⚠ | — | 响应侧实现了、请求侧没抄 | 【实测 2026-08】 | 05 §6 | 11 |

### 随平台变化的特性

- MiniMax 只在自家国内站测过；「随平台变化」体现为**同一 id 随面变化**：④ 面思考默认关且真关，① 面总在想且 `<think>` 内联；两面温度都不听。【实测 2026-09-28】坑 15、199
- **对比火山方舟 ④**（同样 `switch` 拼法）：方舟关思考时听温度（`0` 除外），MiniMax 不听——拼法相同差在听不听，故挂在思考类目而非平台格。坑 200
- **对比 Anthropic 官方 ④**：MiniMax 兼容端点无 `pause_turn`、拒收自己发出的 `*_tool_result` 块；官方 verbatim 续跑。坑 11

## 12 本地模型

### 家族固有特性（跨平台一致）

- 超窗**静默从头部丢弃**（先丢的正是 system），返回 200——只能事前 `contextSize` 估算拦截（`ContextSizeError` 带 estimated／contextSize）。【实测，日期未标】⚠ ⏳待复核 坑 5，详见 01 §6。
- 空 `Authorization: Bearer` 被拒 → 无 key 时省略整个头；Windows 打包版 403 → http 层覆盖 `Origin` 头。【参考实现】详见 02 §5、§6。
- 严格交替 chat 模板上两条连续 user 消息报错（JSON cue 要接在最后一条 user 末尾）。【参考实现】坑 211，详见 06 §9.3。

### 按平台 × 面

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 本地模型（任意） | Ollama `:11434` | ① 兼容 | — | — | — | — | — | — | `/api/show` 的 `model_info` 与 `parameters` 常差 30 倍，小的才算数（`num_ctx` 默认 2048／4096）；truncation 快测 8k | 超窗 🔇 从头部静默截断返回 200（先丢 system）；空 Bearer 被拒 | 【实测，日期未标】⚠ ⏳待复核 | 01 §6；02 §5、§6；06 §6 | 5 |
| 本地模型（任意） | LM Studio ／ llama.cpp | ① 兼容 | — | — | — | 两条连续 user 消息在严格交替模板上 ❌ 报错 | — | — | LM Studio `/models` `max_context_length`；llama.cpp `/props`；`max_model_len` 置 high | 超窗同上 🔇 | 【参考实现】【实测，日期未标】⚠ ⏳待复核 | 06 §6、§9.3；02 §5 | 5、211 |

### 随平台变化的特性

- Ollama 与 LM Studio／llama.cpp 差在**上限探测来源**（`/api/show` 两键 vs `max_context_length`／`/props`）与**模板严格度**（LM Studio 严格交替）；超窗静默截断是两者共性。坑 5、211

## 13 其他（Kimi、OpenRouter）

| 型号 | 平台·渠道·线路 | 面 | 思考控制 | 思考取回／回传 | 结构化输出 | 工具／tool_choice | 服务端工具 | 多模态输入 | 上限与采样 | 静默失败要点 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi | Kimi（Moonshot） | ① | — | — | `json_object` ✅ 不查 "json" 字样 | — | — | — | — | — | 【实测 2026-09-19】⚠（与智谱同批，日期为推断） | 04 §2 | — |
| 任意模型 | OpenRouter | ① | — | — | — | — | — | — | `/models` 带 `context_length`；① 回 `usage.cost`（未信任前不收） | SSE 体内 `data:{"error":…}` routinely（审核、上游故障、余额耗尽）；**指纹**（`gen-…`、`provider`、`native_finish_reason`、`reasoning_details[]`）是在 OrcaRouter 上看到的，不是对 OpenRouter 本身的实测 ⚠ | 【文档；指纹经 OrcaRouter 实测 2026-09-26】 | 06 §1、§2、§6；15 OpenRouter 行 | 185 |
| 任意模型 | 欠费中转（通用）／ OrcaRouter 余额为零 | 任意 | — | — | — | — | — | — | — | ❌ 402 `insufficient_user_quota` 对任何真实请求都回、完整协议形状 JSON、先于模型名解析——不是「连通」也不是鉴权失败 | 【实测 2026-09-05】【实测 2026-09-03】 | 06 §5 | 112 |

## 14 服务端工具 × 平台 × 模型 专表

### web_search

| 工具 | 模型 | 平台·渠道 | 面 | 行为 | 计费 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| web_search（`web_search_20250305`） | Claude | Anthropic 官方（「8 次」那次的平台与日期未标；Claude 5 实测全经 OrcaRouter，见下行） | ④ | 📄 `tools[]` 版本化条目 + `max_uses`；`server_tool_use` → `web_search_tool_result` → citations；`pause_turn` verbatim 续跑 | 官方 $10／1000 次 + 结果按 input token；一题实测 8 次搜索（平台、日期未标） | 【文档】+【实测，日期未标】 ⏳待复核⚠ ⏳待复核 | 05 §5、§6 | — |
| web_search（`web_search_20250305`） | Sonnet 5 | OrcaRouter · ④（Anthropic 原样） | ④ | ✅ 真搜，**不需要 beta 头**；10 条结果各带 `encrypted_content`；`citations` `web_search_result_location`；`usage.server_tool_use:{web_search_requests:1, web_fetch_requests:0}` | 一请求合计 $0.051；没发 `cache_control` 也记 2,834 `cache_creation_input_tokens` | 【实测 2026-09-26】 | 05 §5；06 §1 | 179 |
| web_search（`_20250305`／`_20260209`） | claude-opus-4-6 ／ opus-5 | New API · Kiro 渠道 | ④ | 单挂无函数工具（流式／非流式）🔀 **劫持**：用第一条 user 消息原文搜、模板回复「I'll search for "…"」、模型没跑（0.8–2 s）；+ 函数工具流式 ✅ 真搜（模型自拟词，结果带 `title`／`url`／`page_age`）；+ 函数工具非流式 🔇 丢 | `output_tokens` 固定 644／568／478（劫持指纹） | 【实测 2026-09-23】第十五个样本 | 05 §5 | 139 |
| web_search_options | Claude | New API · Kiro 渠道 | ① | 转成 ④ `web_search` 后 🔀 同样劫持 | — | 【实测 2026-09-23】 | 05 §5 | 139 |
| web_search | Claude | New API · CC 渠道 | ④ | ✅ 单挂真搜（要求搜才搜；改写句子不触发不劫持；`server_tool_use` + 结果块）；+ 函数工具流式 ✅ | `usage.server_tool_use.web_search_requests:1` | 【实测 2026-09-23】第十六个样本 | 05 §5 | — |
| web_search_options | Claude | New API · CC 渠道 | ① | ✅ 答案引了搜索结果 | — | 【实测 2026-09-23】 | 05 §5 | — |
| web_search | Claude | New API · anti 渠道 | ④ | 🔇 单挂丢（凭记忆答「As of my latest information (July 2025)…」）；+ 函数工具流式 🔇 丢 | — | 【实测 2026-09-23】 | 05 §5 | — |
| web_search_options | Claude | New API · anti 渠道 | ① | 🔇 无效 | — | 【实测 2026-09-23】 | 05 §5 | — |
| web_search（+ ① web_search_options） | Claude | New API · AWSb 渠道（Bedrock 正向） | ④／① | ❌ 400 `Input tag 'web_search_20250305' … does not match`——整条请求失败，不只丢工具 | — | 【实测 2026-09-23】 | 05 §5 | — |
| web_search | `gpt-6-luna` | OpenAI 官方 · 经 OrcaRouter ② 两条线路 | ② | ✅ 真搜：`web_search_call` `in_progress`／`searching`／`completed` 齐全、`url_citation`；`action.sources` 需 `include:["web_search_call.action.sources"]` | 原样线路 `usage.input_tokens_details.cache_write_tokens` 4,388 | 【实测 2026-09-26】 | 05 §5；06 §1 | — |
| web_search | GPT | 经 New API（第十个样本，另一台） | ② | ✅ 一次搜索回答 45.7K 输入、112 s；首个事件可晚到 54 s（流看门狗首块等待需高于此）；官方直连未测（OQ-027） | `tool_usage.web_search.num_requests` 按次 + 输入 token | 【实测，日期未标】 ⏳待复核⚠ ⏳待复核 | 05 §5 | 71 |
| web_search | `gpt-5.6-sol` | New API · `[特价Pro]`／`[Plus]`／`[Pro]`（账号池） | ② | ✅ 真搜：1 次 `web_search_call` + `url_citation`，6–10 s | 输入 8.5–14K（搜回网页按输入计） | 【实测 2026-09-24】第十七个样本 | 05 §5 | — |
| web_search | `gpt-5.6-sol` | New API · `[Azure]`（网关） | ② | ❌🔇 **静默丢弃**：无 `web_search_call`，模型答「I can't perform a live web search」 | — | 【实测 2026-09-24】 | 05 §5 | 163 |
| web_search（第十个样本） | GPT sol | New API 另一台 | ② | ✅ 但 112 s（比第十七个样本慢一个量级） | — | 【实测 2026-09】第十个样本 | 05 §5 | — |
| web_search_options | `gpt-5.6-sol` | New API · 四个上游全部 | ① | 🔇 静默忽略（模型答不出只有联网才知道的事）；①→② 翻译层不转此字段 → GPT 联网只能走 ② | — | 【实测 2026-09-24】 | 05 §5 | 164 |
| web_search_options | GPT-6 | OrcaRouter · ① | ① | 🔇 200 但没有 `annotations` | — | 【实测 2026-09-26】 | 01 §9.5 | — |
| web_search（`open_page`／`find_in_page`） | Grok | xAI 官方 | ② | ✅ `web_search_call` `action.type:"open_page"`／`"find_in_page"` → `{url}`+`pattern`，无 queries／sources | 一次 6,851 输入；`server_side_tool_usage_details` 按次 | 【实测，日期未标】⚠ ⏳待复核 | 05 §5 | 71 |
| web_search（`enable_search:true`） | Qwen | 千问 DashScope | ① compat | ✅ 顶层字段；**无痕**：不返回来源、不支持角标；`qwen3-max` 不带策略 🔇 根本没搜（输入 29 token） | 按次价比 Anthropic 低三个数量级；无上限字段 | 【文档】+【实测 2026-09-17】 | 05 §5 | 10 |
| web_search | Qwen | 千问 DashScope | ② compat | ✅ `tools:[{type:"web_search"}]` | 按次 | 【实测 2026-09-17】第六个样本 | 05 §5 | — |
| web_search_image（以文搜图）／ image_search（以图搜图） | Qwen | 千问 DashScope | ② compat | ✅ 可单独；`*_call` 的 `arguments` 与 `output` 都是 JSON 字符串（`"[]"` = 没搜到） | 按次价是搜索的 6–12 倍（单独开关） | 【实测 2026-09-17】 | 05 §5 | — |
| web_search_image ／ image_search | Qwen | 千问 DashScope | ① compat | ❌🔇 猜的字段被静默忽略 | — | 【实测 2026-09-17】 | 05 §5 | — |
| web_search（`{type:"web_search"}`） | doubao-seed-2.1-turbo ／ 2.0-lite ／ 2.0-mini | 火山方舟 · 套餐 | ② | ✅ 三款都跑出 `web_search_call`；套餐不写 `sources:["doubao"]` 也记在 `doubao` 源下；按量 key 不写可能落到按次「联网内容插件」【未验】⚠ | `usage.tool_usage_details.web_search.doubao` | 【实测 2026-09-18】 | 05 §5 | — |
| web_search（`web_search_20250305` + `max_uses`） | 豆包 | 火山方舟 · 套餐 | ④ | ✅ 真跑：`server_tool_use` + `web_search_tool_result`（带 `encrypted_content`、`url` 为空串） | `usage.server_tool_use.web_search_requests` | 【实测 2026-09-18】 | 05 §5 | — |
| web_search | 豆包 | 火山方舟 · 套餐 | ① | **无**（厂商页只列 Responses 与 Messages） | — | 【实测 2026-09-18】 | 05 §5 | — |
| web_search | 豆包 | 火山方舟 · 按量 | ②／④ | 未知【未验】 | — | — | 05 §5 | — |
| web_search（对话内 `tools[]` 项） | GLM | 智谱 BigModel 自家端点 | ① | ✅ `{type:"web_search", web_search:{enable:true, search_engine, search_intent?, search_result?, count?}}`；结果在响应顶层 `web_search[]`；默认意图识别，意图不够 🔇 不搜、模型照答「根据联网搜索结果……」→ 必须 `search_intent:false`；`count` 无效（`search_pro` 50 条 ≈24k token、`search_std` ≈6.7k） | 按 token 灌入 | 【实测 2026-09-19】 | 05 §5 | 100 |
| 平台搜索 | GLM | 千问百炼 ／ 火山方舟 | 视平台 | 由平台执行搜索（(平台, 协议族) 属性） | — | 【实测 2026-09-19】 | 05 §5 | — |
| googleSearch | Gemini 3.8 Flash | OrcaRouter · ③（Vertex 原样） | ③ | ✅ 真搜；`tools[]` 独立项 `{googleSearch:{}}`；末块 `groundingMetadata{webSearchQueries[], groundingChunks[{web:{uri,title,domain}}], searchEntryPoint, groundingSupports}`；`uri` 是 `vertexaisearch` 跳转（能用多久 ⚠）、`title` 是域名；「搜没搜」只认 `webSearchQueries`；无 `max_uses`；与函数工具／`mode:"ANY"`／`responseJsonSchema` 同发 200 | 按查询条数约 $0.014／条（一题 6 条 $0.084）；旧：一次 $0.028 按请求 → 新：按条 | 【实测 2026-09-26】 | 05 §5；06 §1 | 178、190、192–194 |
| googleSearch | Gemini | Google AI Studio 官方 ／ 其他中转 | ③ | 📄 协议自带，「未实测、照发」；Gemini 2.x 在 AI Studio 与函数工具同发问题未测 ⚠ | — | 【未测】 | 05 §5 | — |
| googleSearch ／ urlContext ／ codeExecution（保留函数名） | Gemini | OrcaRouter · ① | ① | 📄 发无 `parameters` 的 function 工具名，网关换成原生内置工具（网关约定，非 Gemini 的） | — | 【文档 2026-09】 | 05 §5 | — |

### web_fetch · url_context · reader · web_extractor

| 工具 | 模型 | 平台·渠道 | 面 | 行为 | 计费 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| web_fetch（`web_fetch_20250910`） | Claude | New API · Kiro 渠道 | ④ | 🔇 200 静默丢弃，模型**假装抓了**（给 `<h1>Example Domain</h1>`） | — | 【实测 2026-09-23】 | 05 §5 | 144 |
| web_fetch | Claude | New API · CC 渠道 | ④ | ✅ 有 `server_tool_use` 块 | — | 【实测 2026-09-23】 | 05 §5 | — |
| web_fetch | Claude | New API · anti 渠道 | ④ | 🔇 丢 | — | 【实测 2026-09-23】 | 05 §5 | — |
| web_fetch | Claude | New API · AWSb 渠道 | ④ | ❌ 400 整条请求 | — | 【实测 2026-09-23】 | 05 §5 | — |
| web_fetch（`web_fetch_20250910`） | Claude | Anthropic 官方 | ④ | 📄 版本化条目；`usage.server_tool_use.web_fetch_requests` | 📄 | 【文档】 | 05 §5 | — |
| web_extractor（`search_options:{search_strategy:"agent_max"}`） | Qwen | 千问 DashScope | ① compat | `qwen3.8-flash` ❌ 400 `does not support the "agent" search strategy`；`qwen3-max`／`qwen3.5-plus` ✅ 收；与 `tools` 同发 ❌ 400 `Agent mode does not support tools…` → 本轮带函数工具只发 `enable_search` | 抓回正文按输入 token | 【实测 2026-09-17】 | 05 §5 | 74 |
| web_extractor | Qwen | 千问 DashScope | ② compat | 仅当 `web_search` 同在 ✅；单独 → ❌ HTTP 200 后首事件 `response.failed`；`web_extractor_call`：`urls[]`+`goal` → `output`（按 goal 提炼正文，非原始 HTML） | 按输入 token | 【实测 2026-09-17】 | 05 §5 | 70 |
| urlContext | Gemini 3.8 Flash | OrcaRouter · ③（Vertex 原样） | ③ | ✅ 首块 `urlContextMetadata.urlMetadata[{retrievedUrl, urlRetrievalStatus}]`；末块 `groundingChunks` 真实 uri + 页面标题、**无 `webSearchQueries`**（只开读网页却被当「搜过」= 坑 194）；app 层依附 `web_search` | 读回正文记 `toolUsePromptTokenCount`（在 prompt 之外） | 【实测 2026-09-26】 | 05 §5；06 §1 | 191、194 |
| `/reader`（应用执行独立端点） | 任意 | 智谱 BigModel | 私有 REST | body `{url, return_format?, retain_images?, …}` → `{model:"web-reader", reader_result:{title, description, url, content, metadata}}`；默认 markdown 完整；`return_format:"text"` 有损（门户首页只剩 108 字页脚）；`retain_images:false`／`with_links_summary` 无效果；目标 404 与主机不存在都 ❌ 500 `1234 网络错误…请稍后重试`（分不出死链与平台故障） | 无 usage | 【实测 2026-09-19】 | 05 §5 | — |
| `/web_search`（应用执行独立端点） | 任意（不受模型约束） | 智谱 BigModel | 私有 REST | body `{search_query, search_engine, search_intent}` 必填 → `{search_intent[], search_result[]}`；`search_intent` 默认 false、true 时闲聊 0 条 `SEARCH_NONE`；`count` 四引擎无视（std ~10、pro／sogou 恒 50、quark 10）；`search_domain_filter` 只 `search_pro`／`search_pro_sogou` 生效；`search_recency_filter` 三引擎无视；超 70 字照搜 | 无 usage、按次计费 | 【实测 2026-09-19】 | 05 §5 | — |

### code_interpreter · code_execution · codeExecution

| 工具 | 模型 | 平台·渠道 | 面 | 行为 | 计费 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code_execution（`code_execution_20250825`） | Claude | New API · Kiro 渠道 | ④ | 🔇 200 静默丢弃，模型**假装跑了**（一段没执行的 Python 和「输出」）；乱造 `type` 同样 200 丢 | — | 【实测 2026-09-23】 | 05 §5 | 144 |
| code_execution | Claude | New API · CC 渠道 | ④ | 🔇 丢，没有块 | — | 【实测 2026-09-23】 | 05 §5 | — |
| code_execution | Claude | New API · anti 渠道 | ④ | 🔇 丢 | — | 【实测 2026-09-23】 | 05 §5 | — |
| code_execution | Claude | New API · AWSb 渠道 | ④ | ❌ 400 整条请求 | — | 【实测 2026-09-23】 | 05 §5 | — |
| code_interpreter（OpenAI 自家） | GPT | OpenAI 官方 | ② | 📄 要 `container`，不是 DashScope 那个工具；app 层 `code_interpreter` id 对官方线过滤掉 | — | 【文档】 | 05 §5 | — |
| code_interpreter | `gpt-5.6-sol` | New API · `[特价Pro]` | ② | ❌ 流式 `response.failed`（整条请求挂） | — | 【实测 2026-09-24】 | 05 §5；06 §2 | — |
| code_interpreter | `gpt-5.6-sol` | New API · `[Plus]` | ② | ❌ 502 | — | 【实测 2026-09-24】 | 05 §5 | — |
| code_interpreter | `gpt-5.6-sol` | New API · `[Pro]` | ② | ❌ 400 `Unsupported tool type` | — | 【实测 2026-09-24】 | 05 §5 | — |
| code_interpreter | `gpt-5.6-sol` | New API · `[Azure]` | ② | ❌ 500 | — | 【实测 2026-09-24】 | 05 §5 | — |
| code_interpreter（`enable_code_interpreter:true`） | qwen3-max（含日期版）等实测名单 | 千问 DashScope | ① compat | 按模型 id 放行；非流式 ❌ 400 `Non-streaming mode does not support Code interpreter.`；带函数工具 ❌ 400（agent mode）；思考关闭照常跑（与文档不符）；与搜索同开可以；无痕（prompt_tokens ~30 → 700–1600）；qwen-max ／ qwen3-max-preview 🔇 静默忽略；qwen3.8 全系 ❌ 400 | — | 【实测 2026-09-17】 | 05 §5 | 75、77 |
| code_interpreter（`tools:[{type:"code_interpreter"}]`） | qwen3-max、qwen3.5–3.8 plus／max／flash、部分开源版、deepseek-v4 | 千问 DashScope | ② compat | ✅ 按模型 id 放行；非流式可以；带函数工具可以（先调函数、下一轮跑代码）；思考关闭（`reasoning.effort:"none"`）→ ❌ 200 后 `response.failed` `Normal mode does not support Code interpreter…` → 本轮不发；`output_item.added` 带完整 `code`，三个进度事件，`done` 补 `outputs:[{type:"logs",logs}]`（剥围栏）；Python 异常仍 `status:"completed"`、traceback 在 logs；画图以 markdown 图片写在 logs、签名 OSS 约 12 小时过期、正文不带 | `usage.x_tools.code_interpreter.count`；限时免费；qwen3.8-flash 一问约 1.1k token（不开约 30） | 【实测 2026-09-17】 | 05 §5 | 76、78 |
| codeExecution | Gemini 3.8 Flash | OrcaRouter · ③（Vertex 原样） | ③ | ✅ 独立块 `executableCode{language, code, id}`（带签名）→ `codeExecutionResult{outcome:"OUTCOME_OK", output, id}` → 文本；不回 `functionResponse`；代码 part 原样回灌 200（后续轮无 `codeExecution`／无工具也 200）；`inlineData` 图表随 model parts 回传；代码 part 回传占上下文（估算要计入） | 回填输出记 `usageMetadata.toolUsePromptTokenCount`（在 prompt 之外） | 【实测 2026-09-26】 | 05 §5；06 §1 | 191、195 |

### file_search

| 工具 | 模型 | 平台·渠道 | 面 | 行为 | 计费 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| file_search | `gpt-5.6-sol` | New API · `[特价Pro]`／`[Plus]`／`[Pro]`／`[Azure]` | ② | ❌ 与 code_interpreter 同：流式 `response.failed` ／ 502 ／ 400 `Unsupported tool type` ／ 500 | — | 【实测 2026-09-24】 | 05 §5 | — |
| file_search | GPT | OpenAI 官方 | ② | 📄 `{type:"file_search"}` 形状存在；只放行官方线 | — | 【文档】 | 05 §5 | — |

### image_generation

| 工具 | 模型 | 平台·渠道 | 面 | 行为 | 计费 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| image_generation | `gpt-5.6-sol` | New API · `[特价Pro]`／`[Plus]`／`[Pro]` | ② | ❌ 403 `Image generation is not enabled for this group` | — | 【实测 2026-09-24】 | 05 §5 | — |
| image_generation | `gpt-5.6-sol` | New API · `[Azure]` | ② | ✅ 出图：83 s，`image_generation_call` 带约 911K 字符 base64 | — | 【实测 2026-09-24】 | 05 §5 | — |
| image_generation | GPT | OpenAI 官方 | ② | 📄 `{type:"image_generation"}` 形状存在；`image_generation_call`（base64） | — | 【文档】 | 05 §5 | — |

### 其他（工具按需加载、续跑、事件形状）

| 工具 | 模型 | 平台·渠道 | 面 | 行为 | 计费 | 证据 | 详见 | 坑 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tool_search ／ defer_loading ／ namespace ／ additional_tools（工具按需加载） | GPT-5.4+ | OpenAI 官方 | ② | 📄 原生实现，工具表前缀不动、缓存不破；下一轮 `input` 必须回传 `tool_search_output`／`additional_tools`，缺了加载过的工具 🔇 静默消失 | — | 【文档 2026-09】 | 05 §7 | 68 |
| tool_search ／ defer_loading | Grok | xAI 官方 | ② | 规格有，❌ 实测 403（仅 alpha 用户） | — | 【实测】 | 05 §7 | — |
| defer_loading ／ tool_search_tool_regex_* ／ _bm25_* | Claude 4.5+ | Anthropic 官方 | ④ | 📄 至少一个非延迟工具否则 400；`defer_loading` 与 `cache_control` 同现 400；`tool_result` 里可回 `tool_reference`；延迟工具搜到前完全不可见 | — | 【文档】 | 05 §7 | — |
| defer_loading | Gemini | Google 官方 | ③ | ❌ 字段整个被拒（第三方报告 ⚠） | — | 【第三方报告】⚠ | 05 §7 | 69 |
| 服务端工具（含 `*_tool_result`）verbatim 续跑 | MiniMax | MiniMax ④ 兼容 | ④ | 停在 `*_tool_result` 报 `end_turn`（无 `pause_turn`）；回灌自己发出的块 ❌ 400 `invalid params, tool result's tool id(...) not found` → transcript 纯文本续跑（丢 citation） | 每次续跑全新计费 | 【实测 2026-08】 | 05 §6 | 11 |
| `pause_turn` verbatim 续跑 | Claude | Anthropic 官方 | ④ | 📄 `stop_reason:"pause_turn"` → `encrypted_content` 一字不改原样续跑（重建块 = 400）；`MAX_PAUSE_CONTINUATIONS = 4` | 每腿全新计费重发整个 turn | 【文档】【实现】 | 05 §6 | — |
| 结构化任务 ／ 辅助请求（摘要、翻译、图片描述） | 任意 | 任意（DashScope 起） | ①② | 继承模型行的服务端工具 🔇 静默多花钱（代码解释器光说明约 800 输入 token／请求还多轮推理）→ 每个非对话调用点显式覆盖为空 | 多花钱 | 【实测 2026-09-17】 | 04 §3；05 §5 | 77 |
