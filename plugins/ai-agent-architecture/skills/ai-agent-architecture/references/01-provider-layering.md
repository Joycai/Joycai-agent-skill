# 01 · 分层模型与统一抽象

> 本篇解决的问题：同时对接 OpenAI Chat Completions、OpenAI Responses、Google Gemini、Anthropic Messages 四个协议族，以及大量第三方"兼容"中继（New API、MiniMax、DeepSeek、千问 DashScope、OpenRouter、Ollama、LM Studio…）时，代码应当如何分层，才能做到「加一家新供应商 = 加一行数据，不是加一个文件」。
> 不读会踩的坑：为每家供应商建一个 Provider 子类，第三方之间 99% 相同的代码被复制 N 份；消息形状按 standard 原值分支，每个新 `_compat` 值都静默掉进 OpenAI 分支；传输配置在十几个调用点手工摊平，漏一处不是编译错误而是某个界面静默行为不一致。

出处：simple-ai-writer `src/lib/ai/`（`types.ts`、`index.ts`、`conn.ts`），设计文档 `docs/api/provider-layering.md`。

本篇目录：
- §1 四层模型：L1 / L2 / L3 + 探测维
- §2 协议族的判定标准
- §3 ApiStandard = 协议族 × official/compat（§3.1 案例：② Responses 为什么是第四族）
- §4 内部 lingua franca：OpenAI Chat Completions 形状
- §5 统一流事件：StreamChunk 变体联合
- §6 统一入口 streamCompletion 与 StreamOptions
- §7 config→request 的收口：连接参数单点摊平
- §8 多面供应商：surface × 协议菜单，与模型级协议选择（§8.1 事实 · §8.2 surface 与协议菜单 · §8.3 通道级选面 vs 模型级点单 · §8.4 路径推导 · §8.5 退化情形）
- §9 供应商数据行样例（§9.1 xAI · §9.2 New API 中转站的四种静默行为；渠道写在模型 id 里：Kiro 渠道的 Claude、同一模型五个渠道的对照、按 id 只点名的能力裁决（已被取代）、上游做成作者声明的数据与怎么测、同一个 GPT 的账号池与网关两类上游（网关的 `instructions` 护栏）、`instructionsField` 按上游裁决 · §9.3 火山方舟按量/套餐两个 base · §9.4 智谱：一把 key 走遍所有路径、路径决定计费 · §9.5 OrcaRouter：一台网关四个面三种后端、回包原样与请求重新序列化、透传证据清单、花费字段与请求头、目录标定表与钉线路的起步模型、PDF 四面、③ 是 Vertex 不是 AI Studio）

---

## 1. 四层模型：L1 / L2 / L3 + 探测维

任何参数、任何差异，都应当先被归入下面四层之一，再决定放在哪：

```
L1  协议族      wire format 本身（body 长什么样）      服务商定义，一族一个 adapter
L2  端点        baseUrl / 鉴权方式 / 族方言参数        作者配置的一行（Provider 表）
L3  模型        能力、档位、上下文/输出上限、价格       端点下的一行（Model 表）
────────────────────────────────────────────────
探测维          真实行为的实测结果（带时间戳）          机器写入，不是配置
```

### 三条铁律

1. **只有 L1 允许"每族一份代码"。** 运行时永远只有"每个协议族一个 adapter"；"某一家供应商"（DeepSeek、Ollama…）是一张**预设数据表**，不是子类。禁止 `DeepSeekProvider extends OpenAIProvider` 这种形态——第三方之间 99% 相同，继承会把 99% 复制 N 份，而那 1% 的差异（一个 header、一个字段）一行配置就能表达。**加一家新供应商 = 加一行数据，不是加一个文件。**
2. **枚举值是稀缺的。** 只有"body 形状不同"才配拥有一个 `ApiStandard` 值。鉴权不同、默认值不同、私有字段不同，全用 L2 数据字段表达。
3. **新参数归属判断法**（按顺序问）：决定 body 形状？→ L1；换 key/baseUrl 会变？→ L2；同端点换模型会变？→ L3；作者答不上来只能实测？→ 探测维。同时命中 L2/L3 的放 L3（细粒度层永远能表达粗的）。

**探测维有两半，过期规则相反**（2026-09-28 定）：作者点的探测（上下文 / 输出上限）写进作者看得见的字段，不过期、重新探测时覆盖，作者填的值优先于它；
端点自己的 400 教会的上限（强制工具、结构化档位）不在作者的字段里，带时间、会过期（参考值 7 天），作者改了那项声明或重新探测即作废，其余时候压住作者的声明。
存储、终止性与作废规则见第 6 篇 §9。

## 2. 协议族的判定标准

规则是一句话：**"能不能只改 URL 与鉴权头就跑通？能，就不是新族。"**

按这个标准，业内收敛成四族：

1. **OpenAI Chat Completions** —— 事实标准 + 全行业兼容层；
2. **OpenAI Responses** —— 与 ① 同厂却是独立一族（`input` vs `messages`、扁平 vs 嵌套工具定义、类型化事件 vs delta 拼接、服务端状态）；
3. **Google GenAI generateContent**；
4. **Anthropic Messages**。

Azure OpenAI、Vertex、Bedrock 上的 Claude 只是**部署变体**（同 body，换鉴权与 URL），不是新族。Bedrock Converse 实际是第五种独立 body（camelCase、SigV4）——接它就是接一个新族，不要伪装成 compat 选项；如果不打算写第五个 adapter，就明确不接。

## 3. ApiStandard = 协议族 × official/compat

每个协议族拆成 official 与 compat 两个枚举值，`familyOf()` 把它们折回族：

```text
ApiStandard    = openai | openai_compat
               | openai_responses | openai_responses_compat     # ② 族，2026-09 加入
               | gemini | gemini_compat
               | anthropic | anthropic_compat
ProtocolFamily = openai | responses | gemini | anthropic

familyOf(standard) -> ProtocolFamily
  查表折回族；表里没有的值（库里的旧值）落回 openai，不抛错
```

`_compat` 不是装饰，两种契约实质不同：

| | official 契约 | compat 契约 |
| --- | --- | --- |
| 地址 | 锁定（存空串，域名变更是代码改动不是数据迁移） | 自填（要归一化） |
| 鉴权 | 锁定 | 可选（下拉，见第 2 篇鉴权矩阵） |
| `/models` | 缺失视为错误 | 缺失降级探测（见第 6 篇） |
| 能力默认值 | 乐观 | 保守 |

**分发规则（红线）**：凡是问"消息长什么样"的地方，必须按 `familyOf(standard)`（折回后的族）分支，而不是按 standard 原值——否则每个新增的 `_compat` 值都会静默掉进 default（OpenAI）分支。只有 official/compat 契约差异（地址校验、鉴权选项、探测策略）才允许直接看 standard。

### 3.1 案例：② Responses 为什么是第四族而不是 `useResponses` 开关

出处：simple-ai-writer `src/lib/ai/responses.ts`，决策记录 `docs/api/qianwen-compat-plan.md` §4.3。

Responses 与 ① 同厂、同 base（官方 `https://api.openai.com/v1`，adapter 自己拼 `/responses`）、同 `Authorization: Bearer`、`/models` 探测复用 ① 族——**但"只改 URL 就跑通"不成立**：

- body：`instructions` + `input` 条目 vs `messages`；
- 流：类型化事件 vs `choices[].delta`；
- 工具形状：扁平 + 自动 strict vs 嵌套；
- 回传义务：整组 output 条目 vs assistant 消息。

反例：在 ① 族 adapter 里加 `useResponses` 布尔，等于把四处分支塞进一个文件、并让每个按族分支的调用点读不到这个差异。落地做法：

- `ApiStandard` 加 `openai_responses` / `openai_responses_compat` 成对两值，`ProtocolFamily` 加 `"responses"`，统一入口多一个 `case "responses"`。
- **加族 = 逐个过 `familyOf` 调用点**（参考实现 12 处：模型/供应商抽屉、两个探测器、出图、入口、jsonMode、modelSummary、reasoning、serverTools、types、urls）。漏过的调用点会静默落进 default（① 族）分支。
- `authMode` 在此族无意义（只有 Bearer），`authModesFor` 只给 `default`。

## 4. 内部 lingua franca：OpenAI Chat Completions 形状

内部消息表示应当统一选一种形状，推荐 OpenAI chat.completions：`system/user/assistant/tool` 角色、`tool_calls`、`tool_call_id`、`image_url` data-URL 多模态 part。Gemini/Anthropic 适配器各自做**单向转换**（`convertToGeminiContents` / `convertToAnthropicMessages`），转换只发生在 adapter 内部、发出前的最后一刻。

跨协议无法用 OpenAI 形状表达的东西（思维链回传物、Gemini 的 thoughtSignature 等），用 **`_` 前缀私有字段**随消息携带，adapter 上线前按前缀统一剥除：

```text
消息（三种之一）：
  { role: system|user|assistant, content: 文本 或 ContentPart[] }
  { role: assistant, content: null, tool_calls: [...],
    _geminiModelParts?  Gemini 原始 parts（含 thoughtSignature），原样
    _reasoning?         { field, text }  ① 系思维链：字段原名 + 全文，工具轮回传用
    _thinkingBlocks?    { modelId, blocks }  Anthropic thinking blocks，原样
    _responseItems?     { modelId, items }   ② Responses 整组 output 条目，原样 }
  { role: tool, tool_call_id, content: 文本 }

ContentPart = { type: text, text } | { type: image_url, image_url: { url: "data:<mime>;base64,<data>" } }
```

**剥除按前缀，不按名单。** 发出前：删掉所有以 `_` 开头的键；若有 `_reasoning`，再把
`_reasoning.text` 以 `_reasoning.field` 的**原名**写回（例如 `reasoning_content`）。参考实现的注释原话是：
每个需要回传的协议都会往这里加一个字段，名字白名单会静默地把下一个放行到 wire 上。

陷阱：如果剥除逻辑是一张字段名白名单，下一个协议加的 `_` 字段会被静默放行到 wire 上——多数端点对未知顶层键直接 400。前缀约定使"新增一个载体字段"零成本地安全。

## 5. 统一流事件：StreamChunk 变体联合

调用方只见一种 chunk 流。判别一律用 **key 判别**（`"text" in chunk` 式），因此**新增变体对旧消费者天然是 no-op**——这是加 `reasoning`/`serverTool` 变体不破坏任何调用点的机制，也是这个联合可以持续生长的前提。

```text
流事件（按「带哪个键」判别，六种之一）：
  { text }          正文——唯一会进用户内容的变体
  { reasoning }     思维链片段——绝不能混进正文，所以独立一种
  { serverTool }    端点自己跑的工具（纯上报，无需回传）
  { turnResumed: { leg, final } }   一次调用变成多次 HTTP 请求的可观测信号
  { done, inputTokens, outputTokens,
    truncated?      finish_reason=length / MAX_TOKENS / max_tokens 归一化后的布尔
    stopReason?     端点原话，只做诊断，永不作分支条件
    cachedTokens?   inputTokens 的子集（已归一化，见 06 §1）
    wireRewrites?   [{ field: reasoning.effort|temperature, sent, echoed }]  回显≠发出（06 §4.1） }
  { toolCalls, _geminiModelParts?, _reasoning?, _thinkingBlocks?, _responseItems? }
                    工具轮：整轮回传载体随 toolCalls 一起交付
```

设计准则：

- **正文与思维链必须是不同变体。** 混流的后果是思考散文进入用户稿子（见第 3 篇）。
- **`stopReason` 只做诊断，永不作为分支条件**——它是端点原话，各家拼写不同且随时增补；需要分支的语义（截断）单独归一化成 `truncated` 布尔。
- `done` chunk 携带归一化后的 usage（口径见第 6 篇）。

## 6. 统一入口 streamCompletion 与 StreamOptions

所有调用最终收敛到一个入口，在这里完成横切关注点（prefix 合并、上下文预检、日志接线），然后按族分发。按顺序做五件事（参考实现里这就是入口函数的全部内容）：

1. 把模型级前缀 prompt 合进首条 system（**返回新列表**，不改传入的）。
2. 开一条 API 日志记录。
3. 若声明了上下文窗口：估算 消息 + 工具定义 的 token，超窗即在发送前抛「上下文超限」错误。
4. 给日志装「请求体」「流事件」两个钩子——**串联**调用方已有的同名钩子，不覆盖（06 §4.2）。
5. 按 `familyOf(standard)` 分发到四个族适配器之一，默认落 ① 族。

统一入口的请求参数（节选）：`baseUrl / apiKey / standard / authMode / modelId / messages / onChunk / signal / tools / serverTools / toolChoice / extraBody / safetySettings / prefix / contextSize / maxOutput / reasoningEffort / thinkingDialect / _onRequestBody`。

其中几个字段的语义必须写进规范，因为它们在各族上行为不同：

- **`extraBody`** —— per-request escape hatch，优先级高于配置（OpenAI 路径最后 spread）；Gemini 路径也收（JSON 模式用它塞 `generationConfig`）；**Anthropic 路径故意不 spread**——它携带的是 OpenAI 形状字段（如 `response_format`），Messages API 对未知顶层字段直接 400。规则：escape hatch 的形状属于某一族时，其他族的适配器应当拒绝 spread 而不是"透传以示通用"。
- **`maxOutput`** —— 只有 Anthropic 路径真的发出去（`max_tokens` 必填、无服务端默认）；OpenAI/Gemini 路径上只作上下文预算的规划输入。
- **`contextSize`** —— 发送前用估算器拦截超窗请求，抛 `ContextSizeError`（携带 estimated/contextSize 两个数字供 UI 展示）。理由：ollama 这类本地栈会**静默从头部丢弃**超出部分（先丢的正是 system 指令），返回 200 装没事——事后无法发现，只能事前拦。
- **`prefix`** —— 模型级前缀 prompt，`applyPrefix` 合并进首条 system。**必须不可变、返回新数组**——agent 循环跨轮复用同一 history 数组，原地修改会把 prefix 重复叠加。

## 7. config→request 的收口：连接参数单点摊平

背景教训（来自参考实现）：约 9 个传输字段全部可选，曾在 16 个调用点手工摊平、8 个参数类型重复声明——漏一处**不是编译错误，是某个界面静默行为不一致**（可选字段的遗漏类型系统查不出来）。

收口方案（参考实现叫 `conn` 模块）：

```text
连接 = { 供应商行, 模型行, 密钥 }
连接参数 ConnOptions = 请求参数里「来自配置」的那一半：
  baseUrl, apiKey, standard, authMode?, safetySettings?, modelId, prefix?,
  contextSize?, maxOutput?, reasoningEffort?, thinkingDialect?, serverTools?
connOptions(连接)        -> ConnOptions      逐字段摊平，全项目只此一处
pickConnOptions(参数)    -> ConnOptions      反向收窄
resolveConn(模型表, 供应商表, modelId) -> 连接 | 未选模型 | 模型已删 | 供应商已删
```

规则：

- 任何携带供应商接线的参数结构都**包含** ConnOptions；调用点统一由 `connOptions(连接)` 展开再补 messages 等调用参数。
- **新增一个 L2/L3 传输字段 = 改 `ConnOptions` + `connOptions()` + `pickConnOptions()` 三处，且在同一文件。**"加字段 = 改一处（文件）"是这个模式的全部意义。
- 两份手写字段表（摊平与收窄）的分歧由**往返单测**盯住——类型系统查不出可选字段的遗漏。
- `resolveConn` 的三种失败（未选模型 / 模型已删 / 供应商已删）保持可区分，UI 才能给出正确的修复指引。
- 陷阱：`connOptions` 刻意**不给空 baseUrl 填默认值**。空串意为"用该协议自己的默认"，只有 URL 模块知道那是哪个；在 conn 层填 `api.openai.com` 会把 Gemini 供应商指过去——参考实现历史上真发生过这个 bug。
- 收口时机：调用点 ≥3 个时就该收口，别等到 16 个。

## 8. 多面供应商：surface × 协议菜单，与模型级协议选择

> 2026-08 增补，来源：阿里百炼（千问平台）与 MiniMax 官方文档全量核对 +
> Joycai Image AI Toolkits 的 vendor–protocol–model 路由重构。
> 解决的问题：**「一家供应商 = 一个协议族」的绑定撑不住了**。

### 8.1 事实：一家供应商可以在同一个 surface 上有多条协议，且与模型耦合

- **阿里百炼**一把 key 六条 wire：chat 有 OpenAI 兼容（`/compatible-mode/v1`）、
  DashScope 私有（`/api/v1/services/aigc/text-generation/…`）、Anthropic 兼容
  （`/apps/anthropic/v1/messages`）三张脸；生图分同步/异步（**提交路径不同**，
  不是加 header 切换）；视频只有异步任务。且协议可用性**按模型分**：
  Qwen-Audio 仅私有面、Anthropic 面只服务模型子集、qwen-image 仅同步、
  wan2.7-image 同步异步皆可（用户选）、wan3.0 视频仅异步。
- **OpenAI 官方**已有 Responses-only 模型（o1-pro / codex 系 /
  computer-use，截至 2026-08）——同一家的 chat surface 有两条结构不兼容的
  wire，走哪条由模型决定。Google 的 Interactions 与 generateContent 同构。
- **MiniMax** 的反例同样重要：①/④ 两张 chat 脸的**模型 id 完全一致**
  （无模型耦合），视频则是独立的私有任务面（`/v2/video_generation`）。

### 8.2 概念：surface 与协议菜单

- **Surface（调用面）**：chat / imageGen / videoJob / discovery。四个就够——
  三家官方的全部生成面都装得下；Responses/Interactions 是 chat 槽位的候选
  协议，不是新 surface。**同一个 wire format 可以服务两个 surface**
  （Gemini generateContent 既是 chat 也是出图），所以协议目录是
  Surface × WireProtocol 二维的。
- **L2 的声明从「一个协议族」升级为「per surface 的菜单 + 默认值」**：

```text
供应商的 surface 声明：
  chat:  默认 WireProtocol + 菜单里的其它选项
  image: 默认 WireProtocol（可空）+ 其它选项
  video: 默认 WireProtocol（空 = 这家没有该 surface）
```

- **L3 增加一个可选的「协议点单」字段**（用户配置，存库）：
  解析顺序 = 模型点单（且在菜单内）→ L2 该 surface 默认 → 按模型分类推导。
  点单不在菜单内（如供应商行改了类型）→ 静默回退 auto + WARN，不炸——
  点单是**偏好**不是路由事实，失效的偏好可以安全忽略。
  注意它**不是可推导数据的副本**（那种列是 bug 面，禁止落库），而是与
  「思考开关」同性质的用户选择，无处可推导。

### 8.3 裁决标准：通道级选面 vs 模型级点单

一家多协议有两种表达，标准一句话：**协议与模型有耦合才点单，没有就分行**。

| 手段 | 适用 | 例 |
| --- | --- | --- |
| **分成多个 L2 行**（UI 上做成一行 + 变体分段控件） | 各面**模型集合一致**，差异只是路径/auth/方言 | MiniMax ①/④、Google native/兼容面、New API 三格式 |
| **一个 L2 行 + 菜单 + 模型点单** | 协议可用性按模型分、或同一模型多条路可选 | 百炼全家、wan2.7 同步/异步、OpenAI Responses-only 模型 |

两者可并用：MiniMax 的 chat 保持双行，但视频槽位声明在**两行上各一份**
（无论用户配的是哪张 chat 脸，视频模型都可用）——视频面是供应商的 surface，
不是某张 chat 脸的附属。

### 8.4 路径推导：一个 base 服务多条 wire

模型点单要成立，前提是一个 L2 行（一个 baseUrl、一把 key）能到达所有面。
做法：**协议自己从 base 推导路径，只认路径、不认 host**（intl 域名同样成立），
且推导幂等（输入已是目标形状 / 裸 host / 带尾斜杠都得到同一结果）：

- 百炼：剥 `/compatible-mode/v1` → 拼 `/api/v1`（私有面）或
  `/apps/anthropic/v1`（④ 面）；
- MiniMax：剥 `/v1` 或 `/anthropic/v1` → 拼 `/v2/…`（视频面）。

反面（存后缀进配置）只在「分行」手段里用——变体切换重写 endpoint 是
通道级选面的实现，别和推导混用在同一家的同一个面里。

### 8.5 退化情形零开销

单协议供应商（Anthropic 官方、各中继、本地运行时）= 单项菜单：不出现任何
选择 UI、auto 即全部行为。通用化不向简单情形收税——这是这套设计能默认开启
而不是藏在高级选项里的原因。

## 9. 供应商数据行样例：xAI（Grok）、New API 中转站、火山方舟、智谱与 OrcaRouter（2026-09）

> 来源：simple-ai-writer `docs/api/landscape.md` §7 第七、八、十、十一、十五、十六、十七、十八个样本（均为实测）。
> 用意：示范「加一家 = 加一行数据 + 一段厂商注记」，以及哪些行为只能写进注记、不能写进代码分支。

### 9.1 xAI：一行预设，零 adapter 改动

- **数据行**：`{ name: "xAI (Grok)", apiStandard: "openai_responses_compat", baseUrl: "https://api.x.ai/v1" }`，Bearer。
  xAI 自己把 Responses 标为推荐接口，Chat Completions 标 **Deprecated**（仍作 legacy 提供），
  Anthropic SDK 兼容面（`/v1/messages`）标完全弃用——所以预设选 ② 族。
- **实测差异（写进注记，不进分支）**：
  - effort：grok-4.5 / 4.6 **拒 `none`**（关不掉思考），`max` 在 4.3/4.5/4.6 全部 400——菜单与默认值见第 3 篇 §7.1。
  - 图片最小 **512 像素总数**（16×16 被拒；32×32 通过），宽高各 ≥8。测试夹具的小图会撞上。
  - 加密推理：须发 `include:["reasoning.encrypted_content"]` 才有 `encrypted_content`，缺了第二轮照样 200 且答对，见第 3 篇 §7.3。
  - 流里**有** `response.completed`（带 usage）+ `[DONE]` 收尾（文档没写终止事件，实测有）。
  - 推理模型上发 `frequency_penalty` 实测 200 未报错（文档说会报错）——文档与实测不符按实测记。
  - `tool_search` / `defer_loading` 实测 403（仅 alpha 用户），见第 5 篇 §7。

### 9.2 New API 中转站：只能写进注记的四种静默行为

两台 New API（`[Pro]` / `[Plus]` 档）上 GPT-5.x 的实测，全部是"不报错、只改账单或质量"：

1. **不发 `instructions`（system）就注入 Codex 系统提示**：一次 4.4K–9K 输入 token，**Chat 面同样注入**。
   规则：对这类端点永远显式发 system（② 族 adapter 恒发 `instructions`，哪怕空串）。
   > **补充（【实测 2026-09-24】，第十七个样本）**：② 带 `instructions` 在三个 ChatGPT 账号档上都不注入，这条规则仍成立；
   > 但 **① 面带 system 消息也挡不住**——`[特价Pro]` 带 system 多数请求仍报 4,397、`[Plus]` 3/3 注入 4,395，`[Pro]` 只在带具名 `tool_choice` 时注入（4,434）。
   > 要稳定避开注入，GPT 走 ② 并发 `instructions`。**例外**：网关类上游见到 `instructions` 键就加护栏，那里要反过来不发（下文「同一个 GPT，两类上游」）。
2. **改写 effort / temperature**（GPT-5.6）：sol 发 `max` 回显 `none` 且 0 推理 token；terra 发 `none` 两次都回显 `medium` 且照样推理；
   `temperature:0.5` 回显 `1.0`。对策是回显比对（第 6 篇 §4.1），不是重试。
   > **部分未复现（【实测 2026-09-24】，第十七个样本，另一台主机）**：sol 发 `max` 四个上游都原样回显 `max` 且有推理——「`max` 回显 `none`」**没再出现**，按「当时当档」理解；
   > `none` 回显 `medium` 照样推理在四个上游（含 sol）全部复现；`temperature:0.5` 在账号池上复现（回显 `1.0`），网关上则整条 500（下文）。
3. **无视 `max_output_tokens`**（其中一台）：截断状态永远不会出现。【实测 2026-09-24】第十七个样本三个账号档都无视（① `max_completion_tokens` 同），网关执行。
4. **一个档位背后多个上游**：同一请求的响应形状时有时无回显字段——每次落到哪个上游，请求侧无法决定。
   【实测 2026-09-24】`[特价Pro]` 同一类请求的注入量有 0 / 11 / 296 / 4.4K / 17K 五种，延迟从 3 s 到超时——一档之内也不是一个账号。

另：档位前缀模型 id（`[Plus]gpt-5.6-terra`）让按 id 前缀查表的逻辑认不出——不要为此加剥前缀规则
（会吞掉别家中继的别名），让作者手动声明。

#### 同一台中转站，渠道写在模型 id 里：Kiro 渠道的 Claude（2026-09-23）

来源：simple-ai-writer `docs/api/landscape.md` §7 第十五个样本（先 curl 约 200 次，再用 `live.relay-kiro.test.ts` 驱动真实 adapter，31 条全过）、
`docs/api/capability-gating-plan.md` §8.10、`src/lib/ai/capabilities.ts` 的 `KIRO_CLAUDE`。

- **形状**【实测 2026-09-23】：一台 New API 中转站的目录里，Claude 挂在多个渠道下，渠道**只体现在模型 id 的档位前缀里**
  （`[kiro]` `[kiro1]`…`[kiro3]` `[kiro-200k]` `[特价kiro量]claude-opus-5`），`/v1/models` 里 `supported_endpoint_types` 一律 `null`。
  Kiro 是 AWS 的 IDE 产品，后端不是 Anthropic API，中转站在两者之间翻译。只开 ① `/v1/chat/completions` 与 ④ `/v1/messages`；
  `/v1/responses`、`/v1beta` 回 500 `convert_request_failed`「not implemented」。① 面是先翻成 Messages 再发的
  （响应里 `usage.billing_usage.source: "claude_messages"`），所以 ④ 的缺口 ① 全有，外加 ① 自己的几条。
- **缺口几乎全是 200、不报错**：`max_tokens`（① 还有 `max_completion_tokens`）无视，`stop_reason` 永远不会是 `max_tokens`（同坑 65）；
  思考档位一半失效（03 §3.3）；两族的 JSON 旋钮都被无视（04 §2）；强制 `tool_choice` 只在非流式路径生效（04 §4）；
  单独挂的 `web_search` 被中转站劫持（05 §5）；PDF 与 URL 图片被丢（02 §1 表后）；`cache_control` 只写不读、usage 的缓存段是拼的（06 §1）。
- **两款 Opus（`claude-opus-4-6` / `-opus-5`）在每一条上都一样**，同一请求的 usage 逐字相同——从请求侧分不出背后是不是两个模型。
- 零碎：不带 `anthropic-version` 也 200，`x-api-key` 与 `Authorization: Bearer` 都收；不存在的模型回 503 `model_not_found`
  「No available channel for model … under group default」（New API 的报法，不是 404）；模型回显去掉档位前缀；
  `/v1/messages/count_tokens` 404 `Invalid URL`；`/v1/files` 401；不注入系统提示（与上面第 1 条不同，不带 system 的请求输入只报 70 token 上下）。

#### 同一个模型，五个渠道五种阉割法（2026-09-23）

来源：simple-ai-writer `docs/api/landscape.md` §7 第十六个样本（同一把 key、同一台中转站、同一套 curl 用例，约 350 次请求，① ④ 两族）、
`docs/issues/relay-claude-channel-gating.md`。

【实测 2026-09-23】同一台 New API 上，同一个 `claude-opus-4-6` / `-opus-5` 挂在几个渠道下，渠道只写在 id 前缀里：

| 前缀 | 背后 | 类别 |
| --- | --- | --- |
| `[特价kiro量]` | Kiro（AWS 的 IDE），上一小节 | 反代 |
| `[CC量]` | 推测是 Claude Code 通道（未证实） | 反代 |
| `[anti量]` | 推测是 Antigravity（未证实） | 反代 |
| `[正向AWSb量]` | AWS Bedrock（消息 id 以 `msg_bdrk_` 开头） | 正向 |
| `[官key量]` | 官方 key | 正向；当天两个端点全部 502 `Upstream request failed`，**没测到** |

④ 面，同一个 `claude-opus-4-6`（CC 另测了 opus-5）：

| 特性 | Kiro | CC | anti | AWSb |
| --- | --- | --- | --- | --- |
| 思考 | ✅ | ✅；**opus-5 的 thinking 文本恒为空** | ❌ **不想**（`-thinking` 变体也不） | ✅ |
| `effort` 分档 | 只有 low 有效 | 分不开 | — | ✅ 真分档 |
| 参数 / 签名校验 | 无，一律 200 | 无 | 无 | ✅ 与官方同文的 400 |
| `max_tokens` | 无视 | ✅ | ✅ | ✅ |
| 强制 `tool_choice`：不带 / 带思考 | 流式时好时坏 / 0 | ✅ / 时好时坏（3/8、4/8） | 0 / 0 | ✅ / ✅ |
| `output_config.format` | 无视 | opus-4-6 无视、opus-5 执行 | 无视 | ✅ |
| PDF / 纯文本 `document` + `citations` | 丢 / 读到、无 citations | ✅ / 读到、无 citations | 丢 / **丢** | ✅ / ✅ 有 citations |
| URL 图片（base64 四个渠道都行） | 丢 | 丢 | 500 | 400 |
| `web_search` / `web_fetch` / `code_execution` | 劫持 / 假装 / 假装 | 真搜 / 真抓 / 丢 | 丢 / 丢 / 丢 | 400 / 400 / 400 |
| `cache_control` | 只写不读 | ✅ | 没有缓存字段 | ✅ |
| 「Say OK.」的输入 token | 7 + 拼的缓存段 | 9–10 | **39**（约 30 token 注入） | 10 |

① 面（New API 先转成 ④ 再发）：④ 的渠道差异在这里重演，**外加转换层自己的两条，四个渠道完全一样**——
`response_format`（`json_object` / strict `json_schema`）被丢（AWSb 在 ④ 面执行 schema，① 面照丢），`reasoning_effort:"max"` / `"none"` = 不想。
另：anti 的 `max_tokens` ① 面无视、④ 面生效——同一渠道两个面的转换也不是同一套。

写给做实现的人：

1. **中转站上能力的主键是（平台, 面, 渠道, 模型），不是（平台, 模型）。**去掉前缀后是同一个 id，能力却从「最接近官方」（CC）到「连思考都没有」（anti）。
2. **先分清转换层与渠道。**只测一个渠道时，转换层的缺口会被记成渠道特性：第十五个样本把 ① `max` = 不想、`response_format` 被丢记成 Kiro 特有，
   测到第二个渠道才发现是整台 New API 的 ①→④ 转换。规则：同一台至少测两个渠道，都一样的归转换层（按平台 × 面裁决），不一样的归渠道。
3. **反代与正向能零成本分辨**：④ 发 `output_config.effort:"bogus"`——正向回官方原文的 400（`Input should be 'low', 'medium', 'high' or 'max'`），
   反代一律 200。正向还校验签名、带特征消息 id 前缀。**反代的缺口全静默；正向的缺口会响**（Bedrock 没有服务端工具 → 400）。
4. **正向也不等于官方**：Bedrock 不提供任何 Anthropic 服务端工具，不收 URL 图片。会响，但一个把中转站当「可能支持」而发 `web_search` 的应用，
   在这个渠道上**每个请求都 400**，不只是丢工具——所以正向渠道也要点名。
5. **同一渠道两款模型也可能不同**：CC 上结构化输出只有 opus-5 执行，思考文本只有 opus-4-6 有。
6. **渠道前缀是站主起的名字。**`kiro` 来自上游产品名，换一台中转站大概率还这么叫；`CC` / `anti` / `AWSb` 是这一台的缩写，写进正则就是为一台中转站硬编码。

> **同日被取代**（留痕，审查旧项目时用得上）：下面这套「只写 `refuses` 的模型格」当天就被下文「上游做成作者声明的数据」取代——
> `KIRO_CLAUDE` 迁成「按 id 推断出 Kiro 上游」，五格结果逐格不变，原因码由 `model` 变成 `upstream`。只点名的思路本身仍对，
> 缺的是「点名谁」不能靠站主起的缩写。

**能力按「平台 × 模型 id」裁决，而且只点名**（参考实现的决定，理由见 `capability-gating-plan.md` §8.10）：

1. 中转站自建、没有可识别的主机，同一台背后挂着许多渠道，行为随渠道变——所以**不写成平台画像**（会连累同一台上的所有模型），
   也不能按 host 判。上游是谁，只有模型 id 里看得出来。
2. 在中转站平台上加一个**只写 `refuses` 的模型格**：`{ refuses: [/^(?=.*kiro)(?=.*claude)/] }`（id 同时含 `kiro` 与 `claude`，
   按渠道 × 家族写，不按具体型号）。名单里的 id 判「不发」；**名单外的 id 与空 id 照常走平台 / 协议规则，跟这个格子不存在一样**。
   参考实现挂在 `newapi` 与 `custom` 两个平台上——New API 中转站不手选平台时落在 `custom`，渠道又都写在 id 里。
3. 为什么不用「`runs` 白名单 + 名单外 = 未实测」那种模型格：放到中转站上，会把同一台上**别的所有模型**拉成「未实测」，
   它们既没测过、也不该被一个渠道连累。
4. 为什么不靠运行时学习：这些缺口都不报错，按 400 学降级的机制（强制工具的错误学习、JSON mode 的备忘）一条都学不到。
5. Sonnet 没测，按推断一并收进名单：缺口在中转站的翻译层、不在模型（两款 Opus 每项一致）。这是「`refuses` 只收实测」的有意例外，
   例外的理由要写下来。别的渠道（`[anti]` 等）当时没测，不在名单里；后来测了（上一小节），名单仍只收 Kiro，理由见第 7 条。
6. **查表的每个调用点都要带上模型 id**：参考实现为此一起改了强制工具（① 与 ④ 两个适配器，④ 以前根本不查这一格）、
   `anthropicServerTools`、`readsPdf`、`resolveStructuredOutput` 几处不带 id 的查询。漏一处就是「矩阵说不发、适配器照发」——
   用「矩阵 vs 适配器实发 body」的一致性测试抓，测试的模型 id 里要有一个被点名的。

7. **代码里的渠道名单只收上游产品名认得出的渠道**（kiro、bedrock 类），站主自定的缩写不进代码【参考实现的决定 2026-09-23，
   `issues/relay-claude-channel-gating.md`】。转换层那两条（① 面 JSON 模式、`max`）应落成「`newapi` 平台 ① 面、按 `claude` 点名」，
   但目前只有一台 New API 的样本，没落。更一般的做法【已实现 2026-09-23，见下文「上游做成作者声明的数据」】：**把渠道做成作者声明的数据**——在中转站的模型行（或一份渠道配置）上
   选「这个 id 走哪种渠道画像」（反代 · Kiro 类 / 反代 · CC 类 / 正向 · Bedrock / 正向 · 官方…），画像就是一组能力格；
   id 正则只当默认建议。与 03 §3「思考代次由作者声明、不从 id 猜」同一原则：id 是作者输入的自由文本，渠道是事实，事实由作者声明。

点名后的结果：

| 线路 | 能力 | 改后 | 为什么 |
| --- | --- | --- | --- |
| ① | `pdfInput` | 不发 | `file` 片段被丢，PDF 子代理不会选中这个模型 |
| ① | `forcedToolChoice` | 发 `auto` | 流式下强制被无视；结构化任务先试工具调用，没调用就退 JSON（04 §3） |
| ① | `structuredOutput`（`jsonSchema` 随之） | JSON 模式降到 `off`，只发 cue | `response_format` 被无视 |
| ④ | `forcedToolChoice` | 发 `{type:"auto"}` | 同上 |
| ④ | `web_search` | 不发 | 不带函数工具的请求会被劫持成一页搜索结果；代价是 agent 场景里本来能用的真搜索也关了（05 §5） |

与 03 §3「思考代次不从 id 猜」不矛盾：那里是**正向推断**（从 id 猜该发什么字段），这里是**实测过的渠道被点名拒绝**——
名单只会让「不发」更早发生；漏点名的后果是回到平台默认，不会凭 id 发出任何新字段。

#### 上游做成作者声明的数据（2026-09-23 实现）

来源：simple-ai-writer PR #687（功能）、#688（合并与提示的修正，五轮 review 收敛）；`docs/api/capability-gating-plan.md` §8.11、
`src/lib/ai/relayUpstream.ts`、`capabilities.ts` 的 `UPSTREAM_CAPABILITIES`。**用词**：参考实现的界面里「渠道」指 provider 行（一把 key + 一个平台），
中转站背后的后端叫「**上游**」；本节以前的小节沿用了旧说法，「渠道」即这里的「上游」。

**形状：「这个模型背后是谁」是独立的一轴，事实由作者的数据给，能力由代码里的内置画像给。**

1. **解析顺序**（只在中转站平台 `newapi` / `custom` 上有意义，别的平台一律「无」）：
   模型手选（含「不按上游」`"none"`）→ 渠道上的「前缀 → 上游」表（取**最长**的匹配前缀，**不分大小写**、去首尾空白，只在 id 开头匹配）
   → id 里的**上游产品名**（`kiro`、`bedrock`，任意位置、不分大小写）→ 无。
   - 表优先于推断：站主可能把 `[特价kiro量]` 映射到别的上游，作者的表比产品名可信。
   - `"none"` 是一个**解析结果**，不是空缺：选了它就不再按 id 推断。存储里「没选」与「选了 none」必须分得开（坑 158）。
   - 站主的缩写（`CC` `anti` `AWSb` `官key`）**永不推断**——只能进作者的表。渠道抽屉列出本渠道模型里还没配的 `[…]` 前缀（按出现次数排，
     大小写不同的并成一条、取多数写法）供一键加行。
2. **画像**：kiro / cc / anti / bedrock / official 五种，内置、**不可编辑**（作者填的格子没有实测依据，矩阵却会标「实测」）。
   每格只写 `true` / `false`、只写样本里测过的；作用域只有 id 含 `claude` 的模型。official 没有格子（当天 502 没测到），选它只表示「这个前缀分过类」。
   （2026-09-24 起另有 GPT 的两种：codex / azure，作用域 id 含 `gpt` 的模型，见下文「上游画像扩到 GPT」。两组互不越界：Claude 模型选了 codex 等于没有上游，反之亦然。）

   | 上游 | ① Chat | ④ Anthropic |
   | --- | --- | --- |
   | kiro | `pdfInput` ✗ · 强制工具 ✗ · `structuredOutput` ✗（实为转换层，见下） | 强制工具 ✗ · `web_search` ✗（劫持） |
   | cc | `pdfInput` ✓ | `pdfInput` ✓ · `web_search` ✓（强制工具**不写**：带思考 3/8、4/8，判 ✗ 会丢掉能调用的那部分） |
   | anti | `pdfInput` ✗ · 强制工具 ✗ | 强制工具 ✗ · `web_search` ✗（丢，模型凭记忆答） |
   | bedrock | `pdfInput` ✓ · 强制工具 ✓ | `pdfInput` ✓ · 强制工具 ✓ · `web_search` ✗（**400 整条请求**） |
   | official | — | — |

   画像表达不了的事实（anti 不思考、Kiro 无视输出上限、CC opus-5 思考文本为空）只在模型抽屉里**告知**，不改发送——它们属于思考类目 / 模型行。
3. **裁决次序**：模型类型 → `requires` → 思考 → **上游格** → 平台格 → 协议族规则。上游格排在平台格前面，因为它更细。
   原因码 `upstream`，可用性矩阵里这类格子带「上游」小标，文案点名上游（「中转站上游「Kiro」实测会丢掉 PDF」），不说「平台不支持」。
4. **每个问能力的地方都走同一个解析**。参考实现里的问法有：请求适配器、矩阵、模型摘要、JSON 模式裁决、PDF 子代理资格 `readsPdf`、搜索子代理资格 `serverToolsSent`、子代理页提示、模型抽屉。
   - `connOptions()` 恒给出一个上游或 `"none"`：适配器不会再按 id 推断盖过作者的表。
   - 只有手搭请求（live 探测、端点探测）缺省时才按 id 推断，行为与只点名时代相同。
   - 漏一处就是「资格说能、请求不发」或反过来（坑 153、154）。
5. **迁移与唯一的新行为**：旧的 Kiro 正则迁成「推断出 Kiro」，结果逐格不变（测试锁住）。推断 `bedrock` 是新的：
   id 同时含 `bedrock` 与 `claude` 的模型，④ 面不再发 `web_search`（原来发了整条 400），同时多了 ④ PDF。
6. **合并两行渠道**（同一台中转站的两条协议被建成了两行，后来合并成一行）时，上游的优先级从高到低：
   1. 保留行的手选；
   2. 同 id 折叠时，被吸收行的手选——专为这个 id 做的，比保留行表里的一行前缀细；
   3. 本行前缀表给出的上游——并表说法不同时（同一前缀两种映射，或对方更长的前缀抢走了匹配），钉成手选；
   4. 其余跟随并表。
   **只从 id 推断出的上游不是谁的设置**：既不能盖过手选，也不能被钉成手选（坑 155、156）。两张前缀表取并集，同一前缀以保留行为准。
7. **提示与资格用同一个裁决，不另写一套**（坑 157）：
   - PDF 子代理的提示分四种：没勾 PDF / 上游丢 / 当前线路传不了 / 渠道上另有能传的线路（点名那条）。
   - 「能传」直接问 `readsPdf`，所以未实测的线路按能力表缺省算能传——提示与请求说同一句话。
   - 反例：千问文档说 DashScope Responses 不支持 PDF，但表里没有 `false` 格（`false` 只留给实测过的否定），提示在 Chat 线路排后时会点名 Responses——
     这是有意保留、写进文档的出入，等实测。

**没做的，与理由**：
- New API 的 ①→④ 转换层（① `response_format` 被丢、`reasoning_effort:"max"` = 不想，四个上游一样）属于**平台**，
  不进上游画像；只有一台 New API 的样本，没落成平台格。唯一例外：Kiro 画像保留 ① `structuredOutput: false`，那是旧规则就判的，注释写明真实归属。
- 没把上游做成合成平台（`relay-kiro`）：平台是渠道级的，上游是模型级的，`PlatformId` 会按上游数翻倍。
- 没只在模型行上选：同一上游的模型多时要逐个选；模型行上的选择保留为覆盖。

**怎么测的（测试内容）**

*实测（花钱，产出记在 `landscape.md` §7）*：
- 第十五个样本：只测了 Kiro。先 curl 约 200 次探形状，再用 `live.relay-kiro.test.ts` 经 `streamCompletion` 驱动真实 adapter，31 条全过。
  这些用例钉住的是**被 200 藏起来的失败**：PDF 被丢、`max_tokens` 无视、① `max` = 不想。哪天某条变红，说明中转站变了——重测，并同步画像的 kiro 一格。
- 第十六个样本：同一把 key、同一台中转站、同一套 curl 用例，约 350 次请求，覆盖 CC / anti / AWSb 的 ① ④ 两族。
  **只有 curl，没有 live adapter 文件**：cc / anti / bedrock 三份画像的证据等级是 curl 实测，不是经应用自己请求体的实测。补 live 文件时按上游参数化同一套用例。
- 用例的设计让模型猜不出答案：
  - 秘密词 PDF（「The secret word is PELICAN 7342」）；纯色 64×64 图；
  - 与 prompt 冲突的 schema；
  - 「Say OK.」对照各上游的输入 token，用来看注入；
  - ④ `effort:"bogus"` 零成本分正向 / 反代；
  - 流式 / 非流式、单挂服务端工具 / 与函数工具同发，各测一遍（06 §8 第 7–10 条）。

*离线（常规套件，不花钱）*：
- **一致性测试**（`capabilityConsistency.test.ts`）：对每个（平台 × 线路 × 能力 × 模型 id × 上游）组合，比「矩阵说发不发」与
  「适配器实发的 body 有没有这个字段」——拦截 `fetch` 抓 body，比较带与不带该能力时 body 是否不同；模型摘要同样比一遍。
  上游用例：同一个 `[x]claude-opus-4-6` 分别手选五种上游，外加一个 **id 含 kiro 却选了 `"none"`** 的（验证 `none` 真的关掉推断）。
  用例 id 里要有被点名的，否则「矩阵说不发、适配器照发」测不出来。
- **解析单测**（`relayUpstream.test.ts`）：
  - 顺序：手选 → 表 → 推断 → 无；表压过推断；`none` 是结果不是空缺；非中转站平台上一律无；
  - 最长前缀、大小写与首尾空白、只匹配开头、空前缀不匹配；
  - 五个站主缩写**永不推断**；存储读回时坏行丢弃、同前缀（不分大小写）只留第一条。
- **读取方单测**（`relayReaders.test.ts`）：`readsPdf`、`serverToolsSent` 跟着渠道的表走、手选压过表、`none` 恢复平台默认；
  `upstreamDropping` 只在「上游」确实是拒绝原因时点名（④ 面 anti 的 PDF 是协议规则拒的，不算上游）；`pdfRouteFor` 在四线路 New API 上给 Kiro 模型的答案与当前线路无关。
- **合并单测**（`channelMerge.test.ts`）：
  - 两表取并集；表冲突时钉住合并前的答案；没有上游的跟随并表、不冻成 `none`；
  - 被吸收行手选（含 `none`）压过推断与保留行的表；保留行手选仍最优先；
  - 推断出的上游在并表不同意时不被写成手选。
- **提示文本单测**（`subagent.test.ts`）：委派拦截四种说法各一例，外加「未声明」。
- **矩阵文档由表生成**（`UPDATE_CAPABILITY_MATRIX=1` 重写 `capability-matrix.md`，含「按上游」一节），测试比对生成结果与仓库里的文件，表改了文档不改就红。
- **导入导出往返**（`configTransfer*`）：前缀表与模型手选都要进备份，`Required<>` 夹具逼着新字段不漏。

*review 教给的*：功能 PR 三轮整体 review、修正 PR 五轮 review 找出来的问题**几乎全在「同一个事实被第二处代码重新推了一遍」**。
例子：合并时把推断当设置、手搭 options 绕过解析、提示自己判断线路。结构性的对策是：
- 问能力只经一个函数（`capabilityModelOf`）；
- 写入手选只经一个函数（`settle`）；
- 提示的「换到哪」也问同一个裁决（`readsPdf`）。

#### 同一个 GPT，两类上游：ChatGPT 账号池与带护栏的网关（2026-09-24）

来源：simple-ai-writer `docs/api/landscape.md` §7 第十七个样本（与第十、十五、十六个样本同一台 New API、同一把 key；并发 curl 约 560 次，
② `/v1/responses` 与 ① `/v1/chat/completions` 各一套，默认流式，随机性大的项补跑 3–4 次；再用 `live.openai-responses.test.ts` 驱动真实 ② 适配器四档各一轮，
45 条过 41 条，4 条失败都在下表里）。

【实测 2026-09-24】同一个 `gpt-5.6-sol` 挂在四个前缀下：

| 前缀 | 背后（按可观测特征推断） | 类别 |
| --- | --- | --- |
| `[特价Pro]` / `[Plus]` / `[Pro]` | ChatGPT 账号池（Codex 后端）：不发 `instructions` 会被注入 Codex / 「coding assistant」提示，`usage` 带 `attribution`；`[Pro]` 的参数校验与官方同文 | 账号池（反代） |
| `[Azure]` | 名字叫 Azure，**实际是一个带「只准做 OpenAI 相关工作」护栏的网关**，不是 Azure OpenAI 本身。这一档没有 sol 的线路（两次相隔 10 分钟都 503 `No available channel for model gpt-5.6-sol under group …`），用同档 `gpt-5.6-terra` 顶替——**这一列比的是上游，不是模型** | 网关（正向） |

目录也不可信：`GET /v1/models` 对三个账号档声明 `supported_endpoint_types` 含 `anthropic` / `gemini`，这把 key 打 `/v1/messages` 却回
`This group does not allow Anthropic Messages requests`（06 §5）。`[官key]` / `[AWSb]` 下的 sol 同样 503「No available channel」——目录里有 ≠ 有线路。

**② Responses 面**（`[Azure]` 列是 terra）：

| 特性 | 三个账号档 | `[Azure]` 网关 |
| --- | --- | --- |
| 带 `instructions` 的「Say OK.」输入 token | 19，不注入 | **1,209**：网关在 `instructions` 后追加约 1.2K token 护栏，回显的 `instructions` 字段里看得见 |
| 不带 `instructions` | `[Plus]` **4,389**（注入，`attribution.request_fields.instructions.input_tokens: 4380`）；`[特价Pro]` 时有时无（0 或 +11）；`[Pro]` 9 | 9，不注入，护栏也不加 |
| `reasoning.effort` 真分档（同题 `reasoning_tokens` low / xhigh） | ✅ 分得开（如 295–428 / 583–588） | 弱（131–155 / 163–245） |
| `effort:"none"` | **关不掉**：回显 `medium`、照样推理 | 同左 |
| 乱写 `effort` | `[Pro]` 400 官方原文；`[Plus]` 502；`[特价Pro]` 流式 `response.failed` | 500 `Upstream gateway error` |
| `reasoning.mode:"pro"` | 回显 `standard` | 回显 `pro`（只测 1 次） |
| `temperature:0.5` | 200，回显 `1.0`（静默改写） | **500**（6/6；`temperature:1` 则 200） |
| `max_output_tokens:16` | ❌ 无视 | ✅ `incomplete`，reason `max_output_tokens` |
| `text.verbosity` low / high | ✅ 生效 | ✅ |
| `text.format: json_schema` | `[Plus]` / `[特价Pro]` ✅ 执行；**`[Pro]` 省略 `strict` 与显式 `strict:true` 都被丢**（回显 `{type:"text"}`） | ✅ |
| 函数工具 `auto` / 具名 / `required` | ✅ | ✅ |
| `input_image`（data / http）、`input_file` PDF（`file_data` / `file_url`） | ✅ | ✅（拒爬虫主机上的 URL 图各档失败方式不同，06 §2） |
| 内置 `web_search` | ✅ 真搜，6–10 s | ❌ **静默丢弃** |
| `code_interpreter` / `file_search` | 不支持（报法各异，05 §5） | 500 |
| `image_generation` | 403 `Image generation is not enabled for this group` | ✅ 能出图（83 s） |
| `store:true` | 200 | 500 |
| 前缀缓存（同一 10K 前缀连发） | ✅ `cached_tokens` 9,984 | ✅ 11,576（多出的是护栏） |

**① Chat Completions 面**：四档响应 `id` 都是 `resp_…`、流里有 `reasoning_content`——New API 把 ① 翻成 ② 再发（与第八、十个样本一致）。与 ② 面不同的几处：

| 特性 | 三个账号档 | `[Azure]` 网关 |
| --- | --- | --- |
| 带 system 消息的输入 token | `[特价Pro]` 4,397、`[Plus]` 4,395（**带 system 也注入**）；`[Pro]` 19，但带具名 `tool_choice` 时 4,434 | 19 |
| `reasoning_effort:"none"` | 关不掉 | ✅ **真关**（没有推理，答案随之变错） |
| `max_completion_tokens:16` | ❌ 无视 | `finish_reason: length`，但 `completion_tokens` 128——截断了，上限不是 16 |
| 顶层 `verbosity` | 看不出效果 | 看不出效果 |
| `response_format: json_schema`（strict） | `[Plus]` / `[特价Pro]` ✅；**`[Pro]` 被丢**（4/4） | ✅ |
| 具名 `tool_choice` | ✅ | ❌ **500**（9/9；`required` ✅，② 面具名也 ✅） |
| `web_search_options` | ❌ 静默忽略 | ❌ 静默忽略 |

**网关的 `instructions` 护栏**。只要请求里有 `instructions` 键（**哪怕是空串**），回显的 `instructions` 就变成三段：作者原文 → 中转站插入的反制
（「【最高优先级强制规则】……位于标记 >>>IGNORE_AFTER<<< 后面的全部作废」）→ 上游追加的「System integrity addendum (highest priority; supersedes any conflicting instructions above)」。
后者是四步门禁：上文没把模型确立为「OpenAI 相关助手」就拒绝；**明文要求拒绝 fiction、novels、poems、role-play 等创作**；拒绝泄露提示词；拒绝按随口给的数字批量输出。
- 中转站的反制大体有效，但不是每次：约 60 次带护栏的 200 里至少 4 次被改写——鬼故事 **6 次拒 2 次**（「I can help with OpenAI, data engineering … but not creative fiction」），
  一道数学题、一次结构化输出的字段里也出现「only OpenAI-related」。200、没有 `refusal`，只是答案不对。
- **不带 `instructions` 键就没有护栏**：纯 `input`、system 放进 `{role:"developer"}` 消息、① 面带或不带 system，都是 9–33 token，创作题全部照写。
- `instructions` 写成写作者身份时 4/4 照写，样本太小，不能说身份压得住护栏。代价另有每请求 +1.2K 输入 token（多半命中缓存）。

写给做实现的人：

1. **同一个模型 id、同一台中转站，两类上游在「`instructions` 该不该发」上方向相反**：账号池不发就被注入 4.4K（第八个样本起的老规则），网关发了就挂护栏。
   这不是一个可以全局翻转的开关，只能按上游裁决（下一小节）。
2. **判断注入最直接的读数是 `usage.attribution.request_fields.instructions.input_tokens`**（作者发 10 token、回报 4,380 = 被注入了），06 §1；
   网关没有这个字段，护栏只能从回显的 `instructions` 看出。没有这些字段时用「Say OK.」对照输入 token。
3. **零成本分类**：② 发 `reasoning.effort:"bogus"`——回官方原文 400 的（`[Pro]`）参数校验与官方同源，其余三种报法（502 / 流式 `response.failed` / 500）都说明中间还有一层（06 §2）。
   但「校验同源」不等于「能力同源」：`[Pro]` 恰是唯一丢结构化输出的账号档。
4. **对写作应用网关是最不该选的一档**，哪怕它参数面最像官方（输出上限生效、① `none` 真关、唯一能出图）：没有联网搜索、温度非 1 整条 500、
   ① 具名 `tool_choice` 整条 500，还挂着不许写小说的护栏。
5. **① 面在这台中转站上对 GPT 一律是翻译出来的**：联网只能走 ② `web_search`，`web_search_options` 四档都静默忽略；要用 GPT-5.6 的内置工具，协议选 Responses。
6. 两条旧结论要按「当时当档」理解（留痕）：第八个样本 `[Pro]` 的「显式 `strict:true` 才丢 format」——这次不论写不写都丢（04 §5.1）；第十个样本 sol 的「发 `max` 回显 `none`」——这次四档都正常（上文第 2 条）。

#### 上游画像扩到 GPT：`instructionsField` 按上游裁决（2026-09-24 实现）

来源：simple-ai-writer `docs/api/capability-gating-plan.md` §8.12、`src/lib/ai/capabilities.ts` 的 `UPSTREAM_CAPABILITIES`（codex / azure 两格的注释写着依据）、`responses.ts`。

【实现 2026-09-24】在「上游做成作者声明的数据」的框架上加两种上游，作者在渠道的前缀表里把 `[Plus]` / `[Pro]` / `[特价Pro]` 配成 codex、`[Azure]` 配成 azure：

| 上游 | ① Chat | ② Responses |
| --- | --- | --- |
| codex（ChatGPT 账号池，反代） | `pdfInput` ✓ · 强制工具 ✓ | `pdfInput` ✓ · 强制工具 ✓ · `textVerbosity` ✓ · `web_search` ✓ · `temperature` ✗（回显 1，被无视）· **`instructionsField` ✓** |
| azure（网关，正向） | `pdfInput` ✓ · **强制工具 ✗**（具名 500；格子分不开具名与 `required`，所以 `required` 也发 `auto`）· `structuredOutput` ✓ · `jsonSchema` ✓ | `pdfInput` ✓ · 强制工具 ✓ · `textVerbosity` ✓ · `structuredOutput` ✓ · `jsonSchema` ✓ · `web_search` ✗ · `temperature` ✗（非 1 就 500）· **`instructionsField` ✗** |

- **新能力 `instructionsField`**（只属 ② 族，协议自带，缺省 yes）。判 `false` 时适配器把系统提示作为 `input` 开头的 `{role:"developer", content}` 消息，
  **不发 `instructions` 键**（02 §7.1 规则 2 的例外）；实测这样护栏不出现，创作题照写。codex 格显式写 `true`：两种写法都测过，不发就注入 4.4K。
  - 为什么不做成全局开关：翻向 developer，账号池每请求多 4.4K；翻回 instructions，网关拒写小说。
  - 为什么不做成上游上的特判字段（`systemAs:"developer"`）：绕过能力表，矩阵与一致性测试都看不见它；「这条线收不收 `instructions`」以后也可能出现在别的平台。
  - 为什么不只在说明里告知：对写作应用这是唯一会直接拒答的一条，而避开的办法已实测、代价为零。
- **作用域写 `/gpt/`，不只 5.6**：差距在中转站与上游之间，不在型号；第八、十个样本（另一台、5.4 / 5.5）一致。与 Kiro 按推断收 Sonnet 同一条理由。
- **不按 id 推断**：GPT 的 id 里没有上游产品名；「azure」这个词也不能推断——这里的 `[Azure]` 是带护栏的网关，不是 Azure OpenAI。
- **`[Pro]` 丢结构化输出不进格子，只进模型抽屉的上游说明**：三档同是账号池，同一种上游测出两种结果。写 `false` 会让另两档白丢实测可用的 JSON 模式；
  拆出 `codex-pro` 是给一台中转站的档位起名（另一台的 `[Pro]` 只在显式 `strict` 时丢）。`[Pro]` 上丢了 format，提示语仍要求 JSON，实测照样回 JSON，只是不受 schema 约束。
- **画像表达不了的只进说明、不改发送**：账号池无视输出上限、`effort:none` 关不掉、不能出图也不能跑代码；网关能出图（Responses 路径本来不发 `image_generation`）。
  ① 面温度不写格子：两类上游发 `0.5` 都 200、没有回显，是否生效分不出。
- **查表缺口一并补上**（坑 168）：`responses.ts` 的温度（以前根本不查表）、verbosity，`modelSummary.ts` 与模型抽屉的温度、verbosity 以前都不带上游。
  表里一写 `temperature: false`，矩阵说不发、请求照发、抽屉摘要照列。现在都经 `capabilityModelOf`；一致性测试的上游夹具由上游清单生成，同时带 Claude 与 GPT 的 id，新上游当天就被覆盖。

### 9.3 字节跳动 · 火山方舟（豆包 / Seedream）：两个 base 是同一行的两个变体

> 来源：Joycai Image AI Toolkits 接入 Seedream（2026-09-18，官方文档 + 套餐 key 实测）。
> 出图协议本身见第 13 篇 §4.1。

- **数据行**：一家、一把 key、一个 host（`ark.cn-beijing.volces.com`），Bearer。chat 是 ① 族
  （`{base}/chat/completions`），出图是同 base 下的 `/images/generations`（第 13 篇的 `ark` route），
  声明为该行 image surface 的菜单——**不新增协议族**：它的 auth、发现、错误信封都是 OpenAI 形。
- **两个 base、两种 key，互不通用**：按量付费 `…/api/v3`，订阅套餐（Agent / Coding Plan）
  `…/api/plan/v3`，路径后缀完全相同。套餐 key 打 `/api/v3` 得 401。按 §8.3 的裁决标准这是
  「分行」（差异只在 base，模型集合按套餐裁剪），UI 上做成**一行 + 两个变体**，且**两个变体
  同一个 channel type**——由此出现一个新不变量：
  - **变体必须按地址回读**。只按 type 找变体，套餐渠道会被读成按量变体，编辑器随即提议把地址
    「恢复」成它的 key 必定 401 的 base。回读 = 类型匹配后再比 endpoint（去尾斜杠），都不中才
    落回首个变体。
  - 变体卡的副标题不能只印协议族（两张一样），兄弟变体同族时印路径。
- **套餐没有模型列表**：`GET /api/plan/v3/models` → 404，非 JSON body。发现逻辑遇 404 退回
  L2 行自带的静态目录（按量带日期 id + 套餐别名），不当连接失败。
- **套餐按模型裁剪、且挑拼写**：只服务 5.0 pro / 5.0 lite；`doubao-seedream-5.0-pro`、
  `doubao-seedream-5.0-lite`（套餐文档写法）与带日期的 `…-5-0-pro-260628`、
  `…-5-0-lite-260128` 都收，**不带 `lite` 的** `doubao-seedream-5-0-260128`（按量文档里 lite 的
  正式 id）与 4.5 / 4.0 回 `404 UnsupportedModel`；**5.0 flash 三种拼法也 404**，只在按量 base
  【实测 2026-09-23】——按量平台的静态目录才列它。模型分类因此要认「`5-0` 与 `5.0` 同一代、六位
  日期不是次版本、lite 有三种拼写」。
- **套餐 base 也服务对话**（同路径 `/chat/completions`）：可用 `doubao-seed-2.0-pro`、别名 `ark-code-latest`，其余 Seed 1.6 系回
  `404 UnsupportedModel`；思考控制就是 ① 的 `reasoning_effort`，不要给它声明别家的方言（第 3 篇 §3.2，实测 2026-09-18）。
- **套餐的对话是三族三个面**（simple-ai-writer，`doubao-seed-2.0-lite` / `-mini` / `2.1-turbo`，39 条实测全过【实测 2026-09-18】）：
  ① `…/api/plan/v3/chat/completions`、② `…/api/plan/v3/responses`、④ `…/api/plan`（Anthropic 形，`/v1/messages`）。
  数据行上是**同一行的三个 route**，不是三行。几处容易看错的：
  - ② 在 `/api/plan/v3/responses`；**探测打在少了 `/v3` 的 `/api/plan/responses` 上是 404**，据此会把整个 ② 面漏掉（坑 135）。
  - 发现：① `/api/plan/v3/models` 404；④ `/v1/models` 对**有效** key 回 **401**——连接测试据此会报「key 无效」。
    `/models` 回 404 / 401 / 403 时都再发一次最小补全，由补全端点定论（错 key 在那里也是 401，造的模型 id 回 404 `UnsupportedModel`）（坑 136）。
  - ④ 面 `x-api-key` 与 `Authorization: Bearer` 都收。
  - `max_tokens` 上限**按模型**：2.0-mini 两族都 ≤ 131,072（超了 400 并报上限），2.1-turbo 收 262,144；上下文 256k（套餐概览页）。
  - 读图：① `image_url`（data URL）、④ `image` 块都读得出；读 PDF：①②④ 三族都读得出（形状见第 2 篇 §1 表的补注）。
  - **套餐没有 Files API**【实测 2026-09-23，对照厂商「文件输入(Files API)」页复测】：`/api/plan/v3/files`、`/api/plan/files`、
    `/api/plan/v1/files` 的列表 / multipart 上传 / 检索 / 删除全 404（路由不存在）；同一把 key 打按量 `/api/v3/files` 是 **401**
    （套餐 key 过不了按量鉴权）。与百炼不同，Files API 只对按量 key 开放。
    - 套餐对话端点**认 `file_id` 字段**：①（`{type:"file",file:{file_id}}`）②（`input_file.file_id`）给假 id 回 404 `ResourceNotFound`，
      不是 400；只是套餐侧没有上传入口。按量 key 上传的文件能否被套餐 key 引用【未验】。④ 的 `source.type:"file"` 是 400
      （支持值 `base64 / text / url / content`）。
    - **`file_url` 三面都通**：② `input_file.file_url`、① `{type:"file",file:{file_url}}`、④ `document` + `source:{type:"url"}` 都读得出公网 PDF。
      厂商写 `file_url`「仅 ②」，① 实测也收。本条旧写法「`file_url`（仅 ②）只可能在按量 base 上用」被这次复测推翻。
      只对文件已在公网上的场景有用；本地文件仍只有 base64 内联。
  - 条款：套餐概览页写明文本模型「不可用于 API 调用，在非 AI 工具中使用……可能被识别为滥用」——AI 工具类应用属于其列，
    但应在渠道 UI 上照实写出。
  - **按量 base 的对话面至今未实测**（手头只有套餐 key）：数据行按文档与套餐实测「假设」，能力格子应记 `unknown` 而不是抄套餐的。
- **Endpoint ID（`ep-…`，推理接入点）可以替代 model id**，从 id 上看不出是哪一代：分类失败是
  正常情况，让作者点单（声明它是出图模型 + 选 `ark` route），点单后落到协议兜底参数表。
- **中转站例外**：认得出的 Seedream id 挂在 ① 族中转上时，默认 route 也是 `ark`（菜单首项，
  Images API / chat 出图仍可点单）。理由：`ark` 的路径就是 Images API 的
  `{base}/images/generations`，在中转 host 上有意义——「中转不提供厂商私有协议」防的是
  **从 endpoint 推导出的私有路径**，这里没有推导，只是 body 形状不同。

### 9.4 智谱 BigModel 开放平台（GLM）：一把 key 走遍所有路径，路径决定计费

> 来源：simple-ai-writer `docs/api/landscape.md` §7 第十四个样本、`docs/api/zhipu-plan.md`（2026-09-19，按量 key 实测全部 11 个对话模型）。

- **数据行**：host `open.bigmodel.cn`，Bearer；① 族标准端点 `…/api/paas/v4`（`/chat/completions`、`/models`）。
  `/models` 是 OpenAI 形（`{object:"list", data:[{id,…}]}`），连接测试直接可用。【实测 2026-09-19】
- **四个前缀，一把 key 全通**：① `/api/paas/v4`（标准）、① `/api/coding/paas/v4`、④ `/api/anthropic`、② `/api/v1`。
  后三个是 GLM Coding Plan 的「编程端点」，按量 key 打上去同样 200。**与火山方舟（§9.3，两种 key 在对方路径上 401）
  正相反：这里是路径决定扣余额还是扣套餐**，选错不会失败、只会换一笔钱；套餐条款又只许「指定工具」使用，违规限流乃至封号。
  按 §8.3 裁决应「分行」，而且**不能把编程端点挂进按量行的线路菜单**——作者切一条线路就在不知情时换了计费与条款。
  【实测 2026-09-19 + 文档】
- **② 面的 `/api/v1/models` 不是 OpenAI 形**：是 Codex CLI 的模型目录（`{models:[{slug, context_window,
  supported_reasoning_levels, input_modalities, …}]}`），只列 3 个模型。④ 面 `/v1/models` 是 Anthropic 形。
- **模型集合**：11 个对话 id（glm-4.5 / 4.5-air / 4.6 / 4.7 / 5 / 5-turbo / 5.1 / 5.2 / 5.3 / 5.3-flash / 5.3-flashx）。
  **思考控制按代分三种**（第 3 篇 §3.1），**只有 5.3-flash / flashx 读图**，其余文本模型收到 `image_url` 直接 400。
  这是「协议族默认的思考参数在一家之内就不对」的样本：按族取默认值（① 族 = `reasoning_effort`）在 11 款上全错，
  所以参数必须**按模型 id 预填**（一张平台级校准表），不能只靠族默认 + 作者手选。
- **max_tokens 上界**（400 生成前拒、不计费，报出范围）：5.x 与 4.6 / 4.7 为 131,072，4.5-air 为 98,304，**glm-4.5 实测
  也是 131,072**（文档写 96K）。上下文：5.3 / 5.3-flash(x) / 5.2 1M，5-turbo 204,800，5.1 / 5 / 4.7 / 4.6 200K，4.5 系列 128K。

### 9.5 OrcaRouter：一台网关、四个面、三种后端——回包原样 ≠ 请求透传（2026-09-26）

> 来源：simple-ai-writer `docs/api/landscape.md` §7 第七个样本（2026-09-03，探测与免费档）、第十八个样本（2026-09-26，付费 key，
> 约 120 次 curl + 真实四族适配器 28 条 live 用例）、`docs/api/orcarouter-probe-plan.md` §3、§7。模型：GPT-6（luna / sol / astra）、
> GPT-5.6-terra、Claude Sonnet 5 / Opus 5.5 / Fable 5.1、Gemini 3.8 Flash。
> 这一节是**方法论的样本**：一台网关的各个面背后可以是不同的后端，同一个面的请求侧与响应侧也可以不对称。厂商事实（Claude 5 的默认思考、
> Gemini 3.8 的档位与工具轮、各族 usage）已写进 03–06 对应小节，这里只记网关本身和「怎么判断一条观察算不算官方」。

- **数据行**：host `api.orcarouter.ai`，一把 key、一份目录，四个面同在一台主机——① `/v1/chat/completions`、② `/v1/responses`、
  ③ `/v1beta/models/{model}:generateContent` / `:streamGenerateContent`、④ `/v1/messages`。四个都是已有的族，不配新族（§2），一族一行。
  鉴权统一 `Authorization: Bearer`（`x-api-key` / `x-goog-api-key` 只在各自的路径上承诺）。模型 id 带厂商前缀（`anthropic/claude-sonnet-5`、
  `google/gemini-3.8-flash`），③ 的 id 里的斜杠**原样进路径**（`/v1beta/models/google/gemini-3.8-flash:generateContent`），不编码。【文档 + 实测 2026-09-03 / 09-26】
- **目录**：`GET /v1/models` 按鉴权头回不同形态——Bearer 回 OpenAI 形（每条带 `supported_endpoint_types`），`x-api-key` 回 Anthropic 形（没有该字段）；
  `GET /v1beta/models` 回 Gemini 形。**`supported_endpoint_types` 是建议不是限制**：`gpt-6-luna` / `-sol` 只声明 `openai`，打 `/v1/responses` 照样 200
  【实测 2026-09-26】。与 New API 那台的方向相反（声明了却不许，06 §5）——两个方向都说明它不能当线路开关。

**按面看，背后是三种东西**【实测 2026-09-26】：

| 面 | 回包里的证据 | 结论 |
| --- | --- | --- |
| ④ | `msg_011C…` id、不透明 base64 `signature`、`usage.cache_creation` 分项、`service_tier`、`inference_geo`、`stop_details`、`context_management` | **Anthropic 原样**（只多一个 `usage.cost_usd`，且要带请求头才有，见下「花费字段」） |
| ③ | `responseId`、`modelVersion`、`thoughtSignature`，以及 Vertex 专有的 **`createTime`、`usageMetadata.trafficType:"ON_DEMAND"`** | **Vertex AI 原样**（只多一个 `usageMetadata.costUsd`，同样要带头） |
| ①（GPT） | `id:"gen-…"`、`provider:"OpenAI"`、`native_finish_reason`、`usage.cost` / `is_byok` / `cost_details.upstream_inference_cost`、`reasoning_details[]`（密文尾部解出 `endpoint_slug`） | **OpenRouter 形态的翻译层**，GPT 的上游再走 Responses |
| ② 默认 | `id:"gen-…"`、伪造的 `msg_tmp_…` / `fc_tmp_…` item id、`summary:"auto"` 回显 `"detailed"`、`store` 恒 `false`、`usage.cost` | 同一层 OpenRouter 形态（terra 的 reasoning `format` 是 `azure-openai-responses-v1`，上游是 Azure） |
| ② 带 `store:true`，或 `include` 含 `web_search_call.action.sources` | `resp_…` id、`billing`、`tool_usage`、`moderation`、`prompt_cache_retention:"24h"`、默认 `store:true`；**没有任何花费字段** | **OpenAI 原样**。同一端点按请求字段分流到两套后端；`tools:[{type:"web_search"}]`、`include:["reasoning.encrypted_content"]`、`text.verbosity` 都**不**触发分流 |

**请求侧不是透传**【实测 2026-09-26】：网关把 body 解析成它认识的结构再重新序列化。④ 顶层多一个 `foo:1`、`thinking.type:"bogus"`、
`output_config.effort:"bogus"`、`output_config.foo` 全部 200（官方对多余字段 400）；③ `generationConfig.fooBar` 也 200，但**枚举值由上游校验**
（`thinkingLevel:"BOGUS"` 回 Vertex 原文 400）；② 默认线路 `reasoning.effort:"bogus"` 回网关自己的 `upstream_rejected_request`，原文被吞。
② 的回灌义务在两条线路上都测不出（`store:false` 下只回 id 的 reasoning item、篡改的 `encrypted_content`、丢掉 reasoning item 全 200）——网关多半在转发前改写了 `input`。

**所以记录时一分为二**：
- **回包形状、字段、事件序列、计费数字**——在判定为「原样」的面上可以当官方事实记（写进 03–06 对应小节，标「经 OrcaRouter」）。
- **「发 X 会不会 400」**——只对这台网关成立。官方规则不据此改口（例：② 回灌义务，03 §7.3。反例：④ 整块丢掉 thinking block 得 200，恰与官方「缺失 → 静默降级」一致，是印证而非改口，03 §5）。
- 06 §8 第 10 条的「非法参数分类法」在这类网关上会失灵：④ 乱写 effort 200，按那条会被判成反代，回包证据却是 Anthropic 原样——
  那条测的是请求侧校验，不是后端是谁。

**透传证据清单**（判定一个面的回包是不是上游原样；plan §3 + 第十八个样本）：

| 族 | 原样的迹象 | 被翻译 / 伪造的迹象 |
| --- | --- | --- |
| ④ | `id` 为 `msg_01…`；`thinking.signature` 是长的不透明 base64；`usage` 带 `cache_creation` 分项、`service_tier`、`inference_geo` | `signature` 等于 message id；`usage` 只有两个数 |
| ③ | `responseId`、`modelVersion`；`thoughtSignature` 出现且回灌生效；`createTime` / `trafficType`（= Vertex） | `parts: []` 而 `thoughtsTokenCount` 为 0 |
| ② | `resp_…` id；`reasoning.encrypted_content` 可回灌；`output_text` 带 `annotations`；`billing` / `tool_usage` | `gen-…` id、`msg_tmp_` / `fc_tmp_` item id、`summary` 被改写、`usage.cost`；事件序列缺官方必有事件 |
| ① | `system_fingerprint`；OpenAI 形的 `usage.*_details` | `gen-…` id、`provider`、`native_finish_reason`、`usage.cost` / `is_byok`、`reasoning_details[]`（OpenRouter 指纹） |

另：响应头里漏出的上游头（`anthropic-ratelimit-*`、`request-id`、`openai-processing-ms`、`x-goog-*`）是强证据。OrcaRouter 一个都不漏，
只有自己的 `x-orca-request-id`、**`x-orca-route: model=…; fallback=0`**（文档没写）、`x-orca-version`。

**① 与 ② 默认线路上能测到什么、测不到什么**【实测 2026-09-26】：
- ① GPT：`reasoning_effort` + `tools` 同发 200、并行调用正常——但上游走 Responses，**不能用来证伪「官方 ① 上 5.4+ 不能 effort + tools」**。
  思维链只以 `reasoning_details` 密文 / `reasoning` 摘要出现；`web_search_options` 200 但没有 `annotations`。
- ① 跨族：Claude 的思维链在 `reasoning_content`；Gemini 不返回思维链、只报 `reasoning_tokens`。
- ② 默认线路的流：`reasoning` item 一次 `added` / `done`，只有 `encrypted_content`、`summary: []`，**没有** `reasoning_summary_text.delta`
  （非流时 `summary` 有文本）；两个并行 `function_call` 依次（不交错）。`reasoning.effort` 的 `minimal` 被改写成 `low`（03 §7.1）。

**网关自己的零碎**【实测 2026-09-26】：
- **花费字段按面不同，而且 ④③ 要请求头才报**（流式再补测，【实测 2026-09-26】，landscape.md §7 第十八个样本「再补测」A）：

  | 线路 | 不带头 | 带 `X-OrcaRouter-Include-Cost: true` |
  | --- | --- | --- |
  | ④ Messages 流 | **没有** | `message_delta.usage.cost_usd`（`message_start` 的 usage 快照里**没有**） |
  | ③ `streamGenerateContent` | **没有** | 末块 `usageMetadata.costUsd` |
  | ① Chat 流（`include_usage`） | 末块 `usage.cost`（流式**没有** `cost_usd`；非流式两个都有） | 同左 |
  | ② 默认线路 | `response.completed.response.usage.cost` | 同左 |
  | ② 原样线路（`store:true`） | **没有** | 没有（头对 ② 无效） |

  与网关账单 `GET /v1/generation?id=` 的 `total_cost` 对过：④③ 相等，① ② 差不到一个计价单位（网关按 1/500,000 美元取整；账单另有 New API 的
  `quota` = 美元 × 500,000）。**改口留痕**：此前（非流式）写的「④③ 只多一个花费字段」没交代请求头——应用只发流式时，不带头就一分钱也读不到。
  读法与信任边界按 06 §1「第四种口径」：有报价且平台受信就用，没有就按表算——同一端点两条线路，一条有一条没有。
- **计数端点不能用**：③ `:countTokens` 被当成 `generateContent` **执行并计费**（回一段关于「数 token」的作文，$0.0028）；④ `/v1/messages/count_tokens`
  301 到官网首页。
- 不带 `alt=sse` 的 `:streamGenerateContent` 也回 SSE（官方是 JSON 数组）。
- **错误信封全被改写成 OpenAI 形**，带 New API 的指纹（④ `type:"<nil>"`），路径被 `***` 遮住——文档说的 `claude_error` / `gemini_error` 没出现。详见 06 §2。
- 余额为零时任何真实模型的任何一面先回 402 `insufficient_user_quota`，先于模型解析【实测 2026-09-03】，见 06 §5。

**把它当内置渠道调好：目录、起步模型、PDF、内置工具**（【实测 2026-09-26】再补测 B–D；【实现】simple-ai-writer `platforms.ts` / `routes.ts`，
决定与理由见其 `docs/api/orcarouter-probe-plan.md` §8）：

- **标定表从目录抄**：`GET /v1/models`（Bearer，203 条）每条带 `context_length`、`max_completion_tokens`、`architecture.input_modalities`——
  GPT-6 astra / luna / sol 与 GPT-5.6-terra 是 1,050,000 / 128,000，Claude Fable 5.1 / Opus 5.5 / Sonnet 5 是 1,000,000 / 128,000，
  Gemini 3.8 Flash 是 1,048,576 / 65,536；八个的 `input_modalities` 都含 `file`。这是免费的数值来源（06 §6 Step 0），抄进平台级标定表，
  作者手动加这些 id 时预填；**没实测的路径**（Claude / Gemini 经 ① 送 PDF：网关在 ① 上替上游翻译请求，读不读得到由它定）预填只能算推断。
- **起步模型按线路钉好**：付费起步行各钉在最能体现它的面——GPT-6 Luna 钉 ②（唯一流出可读推理摘要的线路）、Sonnet 5 钉 ④、Gemini 3.8 Flash 钉 ③。
  钉线路要配一道守卫：作者**保存前**删掉了被钉的线路，起步行就不钉、跟主线路走（纯函数 `pinnableRoute(route, endpoints)`：线路还在才钉）。
  事后编辑渠道再删线路，钉在上面的模型由解析层明确报 routeNotFound（会响），参考实现有意没做自动回退。
- **PDF 四面都读得到**（一份自造单页 PDF 问里面的口令）：① `file` 部件、② `input_file`、④ `document`（Sonnet 5、Opus 5.5）、
  ③ `inlineData` + `application/pdf`。计费细节见 02 §1 表后。
- **③ 背后是 Vertex，不是 AI Studio**：在这条线上测开的格（PDF、内置工具）不照搬给官方 google 平台；参考实现在官方 google 上只按规则
  「未实测、照发」`googleSearch`（协议自带），PDF 格不动。内置工具的形状与计费见 05 §5「③ Gemini 的内置工具」。
- **上游报价进账**：只有这个平台被声明为「报的数 = 实扣」（与 `GET /v1/generation` 对过账），四个适配器带上那个头；信任边界与合并规则见 06 §1「第四种口径」。
- **不做的事写在平台条目旁**：不调计数端点、不按错误信封的 `type` 判类。今天全仓库没有一处这样做，所以只写注释、不加运行时分支——
  注释的价值在于下一个想加「先 count 一下」的人会先看到它。

写给做实现的人：

1. 一族一行，Bearer；③④ 两行的价值在于拿到上游原样的回包（原生思考、签名、缓存分项、内置工具），① 行是任何模型都能调的翻译层。
2. 探一个新网关，**先按面判后端**（上面的清单），再决定哪些观察写进协议事实、哪些只写进这一行的注记。
3. 这台网关逼出的两处适配器修正都是通用的：Gemini「关闭」映射到所有型号都收的最低档（03 §2），回灌 Gemini parts 前剔除空的 `{text:""}`（05 §3）。
4. 网关报钱是好事，但**收不收是信任问题**：平台级声明（测过报价 = 实扣）+ 请求地址也指向它，两道门都过才用（06 §1）；④③ 记得带请求头。

---

## 本篇检查清单

- [ ] 运行时 adapter 数量 = 协议族数量，没有任何"每供应商一个类/文件"的形态。
- [ ] 每个候选新参数都用"归属判断法"过了一遍（body 形状→L1；换端点变→L2；换模型变→L3；只能实测→探测维）。
- [ ] 探测维分主动 / 被动两半：主动探测值进作者字段、不过期；从 400 学到的上限不进配置、会过期、作者改声明或重新探测即作废（06 §9.5）。
- [ ] `ApiStandard` 只在 body 形状不同时增加值；official/compat 成对出现。
- [ ] 全部消息形状分支按折回后的族判断，找不到按 standard 原值判断消息形状的代码。
- [ ] `familyOf` 对未知/旧枚举值有防御性兜底（不抛错，落回默认族）。
- [ ] 内部消息统一为一种 lingua franca 形状；跨协议私有数据全部用 `_` 前缀字段承载。
- [ ] adapter 发出 wire 消息前按 `_` **前缀**（而非名单）剥除私有字段。
- [ ] `StreamChunk` 用 key 判别；新增变体后，跑一遍旧消费者确认是 no-op。
- [ ] `stopReason` 没有出现在任何 `if`/`switch` 条件里（只展示/记日志）。
- [ ] 存在唯一入口 `streamCompletion`，prefix 合并、上下文预检、日志接线都在入口做，不散落在调用方。
- [ ] `applyPrefix` 等消息变换函数是纯函数，不修改传入数组。
- [ ] 配置 → 请求参数只在一处摊平；所有携带供应商接线的参数结构都包含这份连接参数；有摊平/收窄的往返单测。
- [ ] `connOptions` 不给空 baseUrl 填任何默认值。
- [ ] 多面供应商：L2 声明的是 per-surface 菜单而非单一协议族；surface 布尔
      开关（`usesXxxNativeSurfaces` 式）没有随供应商增多而平方增长。
- [ ] 模型级协议点单：解析顺序（点单→菜单默认→分类推导）单点实现；点单失效
      回退 auto + WARN；单项菜单不渲染任何选择 UI。
- [ ] 多 wire 共用一个 base 的路径推导幂等、只认路径不认 host，有纯函数测试。
- [ ] ② Responses 是独立族（`openai_responses` / `_compat` + `ProtocolFamily "responses"`），不是 ① 族里的布尔开关；加族时逐个过了全部 `familyOf` 调用点。
- [ ] 统一入口给自己装的钩子（`_onRequestBody` 等）**串联**调用方的同名钩子，不覆盖。
- [ ] 同一 channel type 挂多个变体（火山方舟按量/套餐）时，变体按 endpoint 回读，编辑器不会把地址「恢复」到别的变体。
- [ ] 中转站的静默行为（注入 system、改写 effort/temperature、无视 `max_output_tokens`、多上游）记在厂商注记里，代码侧只有「恒发 instructions」「回显比对」两条通用对策，没有按中转站名分支。
- [ ] 「这条线收不收 `instructions`」是能力表里的一格（按上游裁决），不是全局开关：账号池上游恒发（挡注入），带护栏的网关上游把 system 改成开头的 `developer` 消息；GPT 的上游由作者声明，不从 id（包括「azure」字样）推断。
- [ ] 中转站上按渠道挑出的模型（渠道只在 id 里看得出），用**只点名**的 id 名单裁决：名单外的 id 照常走平台规则，没有被连累成「未实测」；查能力表的每个调用点都带模型 id，有矩阵 vs 实发 body 的一致性测试。
- [ ] 一把 key 能打多个前缀、由路径决定计费的平台（智谱 BigModel），不同计费的前缀分在不同的行里，没有挂进同一行的线路菜单。
- [ ] 经网关的实测先按面判定后端（§9.5 透传证据清单）：回包原样的面，形状与计费记成官方事实；「发 X 会不会 400」只记成这台网关的注记——网关会重新序列化请求，未知字段与非法枚举常被静默丢掉。
- [ ] 同一端点可能按请求字段分流到两套后端（OrcaRouter ② 的 `store` / `include`）：不按 id 前缀或花费字段的有无推断条目类型与能力。
- [ ] 起步模型钉线路时有「线路还在才钉」的守卫；从网关目录抄来的标定值只对测过的路径算实测，经翻译层的路径标成推断。
