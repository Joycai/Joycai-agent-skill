---
name: channel-route-model
description: >-
  Language-agnostic architecture standard for LLM access config in three
  layers — channel (one credential on one platform) → route (one protocol
  family at an address) → model (independent per-route parameters plus an
  active route) — with a shipped platform profile table. Use when designing,
  in any stack, how users configure LLM providers and models: one key
  speaking several protocols (Chat Completions, Responses, Anthropic,
  Gemini), per-model protocol switching, the same model differing per
  platform, which settings (thinking, max output, temperature, structured
  output, server tools) belong to model vs route, vendor-private fields
  leaking onto "compatible" endpoints, migrating legacy provider records
  without changing any request, merging duplicate providers sharing one key,
  backup versioning, or the settings UI. Triggers: "供应商与模型",
  "渠道", "线路", "一个 key 多个协议", "模型切换协议", "按模型选协议",
  "多面供应商", "合并供应商", "provider schema", "multi-protocol provider",
  "per-route params".
metadata:
  version: "1.0.0"
  updated: "2026-09-28"
---

# 渠道 × 线路 × 模型（Channel × Route × Model）

一份**架构与设计**标准，与编程语言、框架、存储引擎无关：讲 LLM 接入配置怎么分层、每个字段归谁、旧数据怎么迁、合并怎么做、界面怎么把它说清楚。
提炼自一个桌面写作应用在十余家平台、四个协议族上的实测与重构；文中的平台与模型名是**证据**，不是要求。
协议本身的差异（消息格式、流式解析、思考字段的具体拼法）不在范围内。

## 一句话结论

> **协议**回答「消息长什么样」；**平台**回答「这台服务器在这个协议上额外认哪些字段」；**凭据**回答「这是谁的账」。
> 把三件事绑进一条 `供应商 = 地址 + 协议 + 凭据` 记录，就会出现：同一凭据存多份、同一模型建多次、换协议要重填全部参数、
> 以及把某一家的私有字段发给所有「兼容」端点。

## 目标形状

```
平台画像  Platform Profile   随软件发布的只读数据        「平台 X 在 Responses 面上认代码解释器」
   │ 被引用（platform id）
渠道      Channel            用户配置，一条 = 一份凭据    身份 = 凭据
   └─ 线路 Route ×N          每个协议族至多一条           身份 = 渠道 + 协议族；携带地址
模型      Model              挂在渠道下                   身份 = 稳定 id，切线路永不改变
   ├─ 当前线路 activeRoute
   └─ 线路参数 RouteProfile ×N   每条线路一份独立参数
```

## 工作流

1. **先判断需不需要。** 每家平台只用一个协议 → 一条供应商记录就够。出现以下任一条再上这套：
   同一凭据能打多个协议族；同一模型要在协议间切换；同一模型在不同平台或协议上能力不同；一个「兼容」协议上有某家的私有字段。
   单线路渠道必须**零额外负担**：不出现任何线路 UI，行为与旧模型完全一致。
2. **按任务读 references：**

| 任务涉及… | 读 |
| --- | --- |
| 实体划分、渠道为何以凭据为身份、字段归模型还是归线路、平台画像 | `references/01-data-model.md` |
| 存储形态取舍、让大量调用方无需改动的「扁平视图」、迁移不改变任何请求、旧版本共存、备份与同步的版本演进 | `references/02-storage-and-migration.md` |
| 模型切线路、参数独立不复制、授权声明 vs 线路可用性、线路消失、改主线路 | `references/03-route-switching.md` |
| 合并同一凭据的多个旧供应商：检测、计划、执行顺序、引用改写 | `references/04-merge.md` |
| 设置界面的信息架构与视觉语法 | `references/05-ui.md` |
| 评审 / 上线前自查 / 排查静默错误 | `references/06-pitfalls.md` |

3. **动手前把四个决定写进设计文档，附理由：**
   - 线路集合：支持哪几个协议族。
   - 字段归属表：对模型的每个字段问「同一渠道同一模型，换协议会变吗？」，**有实测证据才下沉到线路**。
   - 迁移策略：读时迁移还是一次性迁移；旧字段保不保留。
   - 合并：只能由用户确认，永不自动。

## 七条不变量

1. **模型 id 永不因切线路或改线路参数而改变。** 唯一让 id 消失的操作是合并，且它的全部引用在同一步里改写。
2. **凭据属于渠道，线路不带凭据。** 两份凭据 = 两个渠道。
3. **没配过的线路什么都不发。** 新增或切到一条线路时，随协议变化的参数一律从空白开始，不从别的线路复制。
4. **平台私有能力由 (平台, 协议族, 模型) 查画像决定能否发出。** 用户的开关是授权；发不出时保留授权、不发送、并在界面说明。
5. **协议适配层只按协议族分。** 平台差异只以数据（画像）进入，不出现按平台的适配器分支或子类。
6. **对外暴露的「扁平视图」永远是当前线路的。** 渠道的地址与协议 = 主线路的；模型的参数 = 当前线路的；其余线路的数据旁挂保存。
7. **迁移只做不可能出错的事。** 请求逐字节不变；不自动合并；推断不出平台就归入「自定义」——只有协议标准部分，没有任何私有扩展。
