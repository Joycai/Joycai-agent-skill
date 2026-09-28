---
name: ai-agent-architecture
description: >-
  Platform-agnostic knowledge base of verified LLM endpoint facts, keyed by
  (platform·channel × protocol face × model): thinking control, structured
  output, tools & server tools (web_search, code interpreter), multimodal
  input, limits, billing, silent failures — across OpenAI Chat/Responses,
  Anthropic, Gemini, DashScope 百炼, 火山方舟, 智谱 GLM, xAI, DeepSeek, MiniMax,
  relays (New API channels, OrcaRouter, OpenRouter), Ollama/LM Studio; plus
  image/video generation and ASR. Includes the provider-layering architecture
  ("add a vendor = add a data row") and the protocol for absorbing new facts
  and correcting old ones. Use whenever a task calls an LLM/image/video/ASR
  API: does model X support feature Y on platform Z, compare platforms, audit a
  project's model support, add a vendor/protocol/surface, debug silent
  failures, or record a test result. Triggers: 接入, 审查模型接入, 中转站,
  思考模型, 结构化输出, web_search, 服务端工具, 出图, 视频生成, 语音识别, ASR,
  流式解析, 供应商分层, 记录实测结果, 更新知识库, any vendor or model name.
metadata:
  version: "2.1.0"
  updated: "2026-09-28"
---

# LLM 接入知识库与架构指引

这里存的是**已验证的事实**：各平台、各协议、各模型的行为，以及三者组合时的差异；另有一套从事实里提炼出的「怎样组织支持才不会静默出错」的架构原则，和一套「新事实怎么进来、旧结论怎么改」的维护协议。

与编程语言、框架无关：报文用 JSON 写，内部结构用 schema 记法（`{ 字段?, … }`、`A | B`）。文中的函数名、文件名来自「出处」里的参考实现（simple-ai-writer、Joycai Image AI Toolkits、pyVideoTrans / subtitle_studio），只用来溯源。

agent 体系（tool loop、审批、子代理、上下文压缩）不在这里，在 **agent-runtime-architecture** skill；渠道 / 线路 / 模型三层配置的产品形态在 **channel-route-model** skill；计费在 **llm-billing-model** skill。

## 三个坐标轴

本库所有事实都挂在三个轴的交点上，查和写都先定坐标：

| 轴 | 含义 | 例 |
| --- | --- | --- |
| **平台**（含渠道 / 线路 / 套餐变体） | 谁在接请求。同一台中转站的不同渠道、同一网关的不同线路是不同平台 | OpenAI 官方、百炼、火山方舟 · 套餐、New API · Kiro 渠道、OrcaRouter · ② 默认线路、Ollama |
| **协议面** | 请求 body 的形状 | ① Chat Completions、② Responses、③ Gemini、④ Anthropic、Ⓓ DashScope 私有、🖼 出图 route、🎬 视频、🎤 ASR |
| **模型** | 家族与型号 | GPT-5.6-sol、Claude Opus 5.5、Gemini 3.8 Flash、DeepSeek、Qwen3-Max、GLM-5.3、豆包 Seed 2.1、MiniMax-M3 |

**同一个模型在不同平台的同一面上行为可以完全不同**（DeepSeek 在百炼 ② 面有 `code_interpreter`、官方没有；同一 Claude 在 New API 四个渠道四种答案）。所以能力的主键永远是 (平台·渠道, 面, 模型)，不是 (模型)。

## 四种用法

### 用法一：查「这个组合能不能用、怎么用」

按顺序读，通常两步就够：

1. `references/22-model-capability-matrix.md` —— 先看该模型家族的「固有特性」，再找 (平台, 面) 那一行；服务端工具逐个工具在 §14 专表。**找不到的行 = 未测**，按未知处理，不从相邻平台类推。
2. 行里的「详见」指向 02–06 的正文，那里有报文、原因和对策。
3. 平台层面的事（地址、鉴权、目录可不可信、会不会注入 / 改写、报价怎么读）看 `20-platform-matrix.md`；协议层面的字段形状看 `02-protocol-differences.md` §1 总对照表；出图 / 视频 / ASR 看 `23-media-matrix.md`。
4. 命中 `31-open-questions.md` 里的组合 → 回答「待核实」并给出测法。

### 用法二：审查一个项目

回答两个问题：它**支持得全不全**、**支持得对不对**。按 `references/00-audit-playbook.md` 走：盘点线格式字面量 → 填覆盖矩阵 → **先查静默失败** → 每条发现带证据等级 → 按模板出报告。判定时用 22 / 20 的结论格对照项目行为，用正文篇解释原因。

为什么先查静默失败：会报 400 的错用户迟早会撞见；静默的错只会表现为效果变差、账单变贵、数据慢慢坏掉，不拿事实去对照永远发现不了。本库最值钱的部分正在这里。

### 用法三：新增支持 / 设计架构

加一家厂商、一个协议族、一个出图 / 视频 / ASR 面，按 `references/12-migration-roadmap.md` 的配方走。第一步永远是查 20（§0 协议族、§3 各节「正文所在」行）/ 22 / 23：本库已有的事实直接用，缺的先实测再写。

架构层面（分层、多面供应商、中转站的渠道与上游、按 400 学降级）在 `01-provider-layering.md`；贯穿全库的六条原则见下。

### 用法四：写回新事实 / 修正旧结论

任何实测、审查发现、新读的文档，都按 `references/30-knowledge-ingestion.md` 写回：七字段齐全 → 决策树定位置 → 正文一处 + 矩阵格指针 → 推翻旧结论留痕不删 → 过 §8 自检清单 → `CHANGELOG.md` 加一行。口述与推断只进 31 待核实表。

## 文件地图：五层

每个文件只属于一层，每层只回答一类问题。找东西先定层，再定文件。

| 层 | 文件 | 回答什么 | 里面没有什么 |
| --- | --- | --- | --- |
| **流程** | `00-audit-playbook.md` 审查 · `12-migration-roadmap.md` 新增 · `30-knowledge-ingestion.md` 写回 | 按什么步骤做 | 不复述事实 |
| **结论表** | `20-platform-matrix.md` 平台 · `22-model-capability-matrix.md` 模型 × 平台 × 面 · `23-media-matrix.md` 出图 / 视频 / ASR · `31-open-questions.md` 待核实 | 能不能、哪里静默、证据日期、正文在哪 | 每格只写记号 + 关键值 + 证据 + 指针，原因与报文在正文 |
| **正文** | `01` 架构分层 · `02` 协议差异 · `03` 思考 · `04` 结构化 · `05` 工具与服务端工具 · `06` 错误 / usage / 探测 · `13` 出图 · `14` 视频 · `16` 语音识别 | 报文、数值、原因、后果、对策——事实的唯一正文 | 不按厂商重复；厂商差异是同一小节里的对照表 |
| **反查** | `11-pitfalls.md` | 现象 → 一句对策 → 指针（坑 1–18、54–223；19–53 在 agent skill） | 原因在正文 |
| **日志** | `CHANGELOG.md` | 改动史 | — |

按问题定文件：

| 要查的 | 读 |
| --- | --- |
| 某模型在某平台某面上的思考 / 结构化 / 工具 / 服务端工具 / 多模态 / 上限；服务端工具按工具查（§14） | 22 |
| 某平台的面、地址鉴权、目录可信度、后端指纹、对请求的手脚、计费报法；某一家的正文散在哪（§3 各节「正文所在」行）；协议族底座在哪（§0） | 20 |
| 出图 / 视频 / ASR 的 route × 平台 × 模型 | 23 |
| 没测过的组合、证据不够的结论、超期待复核 | 31 |
| 四族 × 功能维度的字段形状总对照（§1）；非对话面与私有扩展的判定与端点（§1.1）；消息转换、流式解析、地址、鉴权 | 02 |
| 思考：强度、取回、回传、`<think>`、「关闭」只是最低档、关思考时的温度、第三方 ④ 面默认值与 `disabled` 三种结局（§3.5）、判想没想（§4.1） | 03 |
| 结构化输出：每族 JSON mode、强制工具回退链、`text.format` / `verbosity` | 04 |
| 工具定义、tool_choice、流式拼接、配对、服务端工具、`pause_turn` 续跑、按需加载 | 05 |
| usage 口径、上游报价、HTTP 200 里的失败、重试、日志与回显比对、探测、付费实测纪律、按 400 学降级 | 06 |
| 分层架构：加一家 = 加一行数据、多面厂商、中转站的渠道与上游做成数据、透传证据、规范化 id | 01 |
| 出图 / 视频 / ASR 管线正文 | 13 / 14 / 16 |
| 看起来成功其实失败的怪现象 | 11 |

## 证据记法

一条事实靠不靠得住，看它从哪来、什么时候核实的。正文与矩阵统一用：

| 记法 | 含义 | 审查时怎么用 |
| --- | --- | --- |
| 【实测 YYYY-MM-DD】 | 真发过请求、看过响应（矩阵里另标样本量） | 可以直接据此判错 |
| 【文档 YYYY-MM】 | 官方文档或 API 参考页的口径 | 项目行为不一致时写「待核实」，并给出验证方法 |
| 【中继源码】 | 读中转站源码得出 | 只对那一类中转站成立 |
| 【实现】 | 某项目的代码这样写并在真实服务上用过，本库没独立复核报文 | 当线索用；判错前先实测 |
| ⚠ / 【未验】 | 推断，或文档含糊 | 不据此判错 |

矩阵格子另用结论记号：✅ 实测生效 ／ ❌ 拒绝且会响（带状态码）／ 🔇 **静默失败**（200 不生效、被丢、被改写）／ 🔀 被中转站改写或劫持 ／ 📄 仅文档 ／ — 未测。

另外三条规则：
- 事实超过半年没有复核的，一律按「待核实」对待（矩阵里标 ⏳，列在 31 §4）。
- 文档与实测冲突时，以实测为准，并把两者都记下来。
- 经翻译层网关看到的官方行为，只有回包原样的面才能记成官方事实，且标「经 X」（01 §9.5）。

## 贯穿全库的六条原则

具体事实会过时，这六条比任何一条事实都耐用。审查「结构对不对」时拿它们当标尺：

1. **每个协议族一个适配器，厂商是数据行，不是子类。** 只有 body 形状不同才配一个新协议族。一家可以有多张脸，这也是数据：每个面一份「菜单 + 默认值」（01 §1、§8）。中转站上同一个模型 id 背后可能是几个后端渠道，能力随渠道变——渠道也是作者声明的数据，不是从 id 上猜的（01 §9.2）。
2. **发送取最小公倍数，接收取最大宽容。** 主动发出的每个字段都可能被某个中转站 400；接收侧要防得住任何没见过的形状。
3. **凡跨轮回传的，原样整存。** thinking block、thoughtSignature、`encrypted_content`、reasoning 字段名都属此类；「理解后归一化再重建」恰好会丢掉校验要用的那部分。载体带上 modelId，换模型时整组剥离（03 §5）。
4. **先问：出错时会不会响？** 会响的，靠错误驱动降级就够了。不会响的（静默降级、静默截断、静默忽略）必须主动验证：对照日志、探测、找间接判据。HTTP 200 不等于成功（06 §2）。
5. **能力能声明就声明，只有数值才实测，出图永不探测。** 出图的每次探测都是一次真实计费（06 §7、13 §3）。
6. **协议完整性是硬约束。** 每个 tool_call 都必须有配对的结果消息；四族都拒绝缺失，一次畸形就会让整段会话永久作废（05 §4）。

## 维护知识库（摘要，全文见 30 篇）

- **事实只有一处正文，其余是指针**：模型 / 协议级正文在 02–06 / 13 / 14 / 16，平台级正文在 20 §3；22 / 23 与 20 §2 只写结论 + 指针。改事实 = 改正文一处 + 同步所有结论格。
- **放对地方**按 30 §3 决策树：待核实 → 31；媒体 → 13/14/16 + 23；平台本身（地址、目录、手脚、计费报法）→ 20 §3 就是正文，§2 是结论；模型 × 平台行为 → 03/04/05/02 正文 + 22 结论格；协议通用 → 02–06（总对照在 02 §1）；现象型静默失败 → 11（编号只增不重排）；架构经验 → 01 / 12。
- **写法**：主键 (平台·渠道, 面, 模型)、发了什么、看到什么、记号、不这样会怎样、证据 + 日期 + 样本量、出处——七项缺一不是事实是线索。给实际报文与字段名，不写「支持 X」。
- **改结论留痕**：旧句保留，写「旧 → 新（日期，被哪次实测推翻）」。唯一允许删行的是 31。
- 写回前 grep 主键，更新原条目不另起重复；过 30 §8 自检清单；`CHANGELOG.md` 加一行。
