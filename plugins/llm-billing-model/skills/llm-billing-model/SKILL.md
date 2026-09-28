---
name: llm-billing-model
description: >-
  Language-agnostic design standard for metering and billing LLM / image /
  video API usage in an app that lets users configure their own prices:
  fee groups in three billing modes (per token with cache rate, per request,
  per output spec — a rate table over size × quality × seconds with an input-
  image side), how a request's spec is read and matched (blank condition
  matches anything, most specific row wins, resolution tiers by area), what
  a usage row snapshots so history never re-prices, provider-reported cost
  overriding the table, bill-on-submit + settle for video jobs, the neutral
  metadata keys protocols publish, reserved-key hygiene against relays, the
  usage page's rules and the fee-group editor. Use when designing, in any
  stack, cost tracking for AI APIs: "计费组", "资费", "按规格计费", "档位表",
  "输入图计费", "上游报价", "用量统计", "token 成本", "cache 计价",
  "usage tracking", "fee groups", "pricing tiers", "spec billing",
  "cost per image", "reported cost", "usage dashboard".
metadata:
  version: "1.0.0"
  updated: "2026-09-28"
---

# LLM 计费模型（Fee Groups × Usage Rows）

一份**架构与设计**标准，与语言、框架、存储引擎无关：讲用户自配价格的 AI 用量计费怎么建模、一次请求怎么算钱、
用量行该快照什么、上游报的价怎么压过本地表、界面怎么把它说清楚。提炼自一个桌面创作应用在十余家平台
（OpenAI / Gemini / Anthropic / xAI / 火山方舟 / 百炼 / MiniMax / Midjourney / OrcaRouter，直连与中转）上的实测与四轮重构；
文中的平台与价格是**证据**，不是要求。协议本身的字段拼法只在需要时点到（`references/03`）。

## 一句话结论

> **计费组**回答「这类模型按什么算钱」；**用量行**回答「这一次到底花了多少」——并且把当时的价格**抄在自己身上**；
> **上游报价**回答「供应商说扣了多少」，有它就不再算。
> 把价格只存在模型上、算钱时回头查当前价、把「没报」和「报了 0」混成一个数，就会出现：改一次价历史全变、
> 视频按提交时猜的时长收钱、中转随便起个字段名就能定账。

## 目标形状

```
计费组 FeeGroup           用户配置，一组价格，三种模式之一
   ├─ token   输入价 · 缓存价（可空 = 同输入价）· 输出价     单位：每百万 token
   ├─ request 每次请求价
   └─ spec    单位（张 / 秒 / 条）× 档位表[尺寸? · 质量? · 时长? → 单价] + 输入图（单价 · 每次免费张数）
模型 Model ── fee_group_id ──▶ 计费组          渠道有 default_fee_group_id 给新模型
用量行 UsageRow            一次计费请求：计数 + 当时价格的快照 + 规格快照 + 上游报价(可空)
检查点 Checkpoint          大范围统计的日汇总缓存
```

## 工作流

1. **先判断要哪几种模式。** 只接聊天模型 → `token` 一种够用；有按张计价的图像端点 → 加 `request`；
   同一模型价格随尺寸 / 质量 / 时长变 → 再加 `spec`。三种模式共用一张组表、一张用量行表，**字段全保留、按模式读**。
2. **按任务读 references：**

| 任务涉及… | 读 |
| --- | --- |
| 计费组、模型 ↔ 组、用量行、检查点的字段与归属；规格三元组；中性 metadata 键 | `references/01-data-model.md` |
| 三种模式的算式；档位匹配（空条件、最具体、按面积归档）；输入图一侧；上游报价的优先级与信任边界、多次请求合一行；token 口径陷阱 | `references/02-pricing-rules.md` |
| 什么时候记、谁来记、流式与中止、视频「提交即计费 + 结算」、协议该发布什么、保留键防伪造、网关报价（带头才报、流里在哪一块） | `references/03-recording.md` |
| 列的可空与默认、错类型格、局部更新、迁移只加不改、备份版本、检查点 | `references/04-storage-and-migration.md` |
| 计费组编辑器与摘要；用量页（汇总卡、分组条、明细行、展开网格、未覆盖提示、上游报价对照） | `references/05-ui.md` |
| 评审 / 上线前自查 / 排查「记错钱但不报错」 | `references/06-pitfalls.md` |

3. **动手前把五个决定写进设计文档，附理由：**
   - 支持的模式集合与每种的单位（张 / 秒 / 条各自怎么数）。
   - 规格从哪里读：请求参数的键名、上游回显的键名、谁压过谁。
   - 用量行快照哪些列（原则：**读时算钱只用行上的数**）。
   - 哪些上游回报的量可以压过本地（张数、时长、金额），从哪个协议、以什么中性键进来；报金额的，**信任哪些平台、凭什么实测**。
   - 币种：一律一种显示币种，还是每组带币种（后者今天没做，见 `06`）。

## 九条不变量

1. **用量行自带价格。** 每一行抄下计费时的单价 / 数量 / 规格；改组、删组、换组，历史一分不动。
2. **算钱只有一份代码，且只读行上的数。** 汇总、分组条、明细、检查点、导出都调同一个 `cost(row)`。
3. **「没有」与「零」分得开。** 缓存价可空（= 同输入价）、上游报价可空（= 没报）、用量块可缺（= 记 0 并警告）；
   永远不用 `0` 表示「未配置 / 未回报」。
4. **规格两边都归一化后再比。** 请求值、回显值、手填的档位条件走同一个归一化；**空条件匹配一切，填得最多的行赢**。
5. **上游说的压过本地猜的。** 回显尺寸 > 请求尺寸；回报张数 > 本地数的张数；回报金额 > 整张表；结算时长 > 提交时长。
6. **只有协议自己的换算能写保留键，报价只信声明过的平台。** 上游 `usage` 原样铺进 metadata 前剔掉 `reported_cost_usd` /
   `input_image_count`；中转默认不翻报价（中转的价在用户的表里）——**例外只按平台声明**：实测过「回包报的 = 账单扣的」
   的网关才翻，且请求地址也得指向它（标签可以贴给任何主机）。几次请求记一行时，**每次都报了才相加，缺一次整行回落到表**。
7. **记账在一切之前、且永不抛错。** 上游已经生成并收费的东西先记；取消、内容拦截、写库失败都排在后面。
8. **提交即计费，结算只改输出（加一列报价）。** 视频提交时按请求参数记一行（id 可跨重启找回，带送出的张数），完成时只重写输出四列；
   上游在终态才报的钱只写 `reported_cost` 一列。
9. **每处「静默记错」都要有一条测试。** 记错钱不会报错：匹配错档、少一列、把 NULL 读成 0——各钉一条。
