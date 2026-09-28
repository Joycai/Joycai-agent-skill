# 03 · 什么时候记、谁来记

## 唯一写入口

三条到达路径（同步请求、流式、长任务提交）都进同一个 `record_usage(model, config, metadata, options, image_count, row_id?)`：

```
record_usage:
  spec   = price_spec(config, options, metadata, image_count)   # 纯函数：读规格、匹配、数输入图
  prompt = metadata[promptTokenCount ?? prompt_tokens ?? input_tokens]      # 三种拼法
  cache  = clamp(cached_of(metadata), 0, prompt)
  output = output_tokens_of(metadata)                            # Google 加 thoughts
  row    = { ...counts, input = prompt − cache, cache,
             input_price = config.input_price, cache_price = config.effective_cache_price, output_price,
             request_price, billing_mode = config.billing_mode,
             ...spec?.columns, reported_cost = reported_cost_of(metadata) }
  sink(row)                                                       # 写库；测试用 override 换掉
```

`price_spec` 是**纯函数**（不碰库），三条路径各一条测试就能钉住。

## 四条时序规则

1. **先记账，再做别的。** 上游已生成并收费：记账排在「取消检查」「内容拦截抛错」「写进会话」之前。
   中途被取消的流：已到的部分照记，然后再抛取消；内容拦截：先记后抛。
2. **永不抛错。** 记账失败（库锁、坏表）记 WARN 并吞掉——不能把已交付的图变成失败任务，不能丢掉刚拿到的视频作业 id。
3. **按 token 的渠道没回 usage：记 0 并警告一次**（每次调用一次，不是每段续跑一次）。本地栈与不少代理不回 usage；
   「没回」不能读成「0 token」——所以 `prompt_tokens_of` 返回**空**让调用方回退，只有记账把空当 0。
4. **按规格的组带图就记**，哪怕没有 usage 块：中转经聊天面出图常常一个 usage 都不回，图是计费依据。

## 流式

- 块的 metadata **合并，后写的赢**；后一块没写的键不会抹掉前一块的——所以「回报的 0」要明发。
- **每个图片块都带** `input_image_count` 与 `reported_cost_usd`（凡是自己造图片块的地方：单发转流、方舟 SSE、Midjourney）：
  流在出图之后、收尾块之前被放弃时，提前退出的记账只看到图片块。
- 流被放弃：用已合并的 metadata 记一行（图已交付、已收费）。

## 视频：提交即计费，结算只改输出

- 提交被接受即记一行（`operation: submit`，token 0）：没有别的时刻能记它——视频不走同步 / 流式路径。
  行 id = `video:<作业名>`，**持久**，重启后续轮询的进程也能找回。
- 按规格的组：提交时按**请求的**分辨率 / 时长匹配；失败的作业照样记（与按次一致）。
- **提交返回的不是裸 id**：`submit → {request_id, input_images}`，张数在组完请求体之后数（读不到的附件、互斥被丢的参考图不算：
  xAI 首帧计 1 或 `reference_images` 长度；Sora 数 multipart 文件；百炼数 `input.media[]`；MiniMax 数互斥之后剩下的；
  Veo 数 `image` + `lastFrame` + `referenceImages`）。票据带着它，提交行的 metadata 写 `input_image_count`——输入费对视频生效。
  **新加一个视频协议不报张数 = 该协议上的视频输入费静默记 0。**
- 完成时上游报了实际时长（百炼 `usage.duration`、MiniMax `usage.output_seconds`、xAI `video.duration`）→ **结算**：用提交时同一份
  options 只换时长重新匹配（按时长分档的行可能变），**只重写输出四列**（数量、单价、单位、规格快照）；输入三列不碰——结算只知道秒数。
- 完成时上游报了钱（xAI `usage.cost_in_usd_ticks`，**只在终态轮询里**，提交与 pending 都没有）→ 协议经同一个换算发布在 done 信封的
  `reported_cost_usd` 下；结算的第二段在**任何模式**下只写 `reported_cost` 一列——提交行的档位估算从此被压过，快照仍在。
- done 信封上的 `reported_cost_usd` 与实际时长只能由协议自己的换算写入。一个**把上游 body 原样当内部信封返回**的轮询（Veo 的
  operation JSON 就是这样穿透的）必须在返回前 `remove` 掉这两个键，否则挂在中转上的该面塞一个同名字段就压掉整张表（`06`）。
- 两段各自尽力而为、互不阻塞：结算失败记 WARN，视频不受影响。
- 提交前本地就能判定的错误（缺参考图）不计费、不重试。

## 协议要发布什么

每个协议把 vendor 字段翻成中性键（`01`），记账**只认中性键、不认任何 vendor 字段**：

| 协议类型 | 必发 | 可发 |
| --- | --- | --- |
| 聊天 | 三种拼法之一的 token 计数 + 缓存明细（Google 另加 `toolUsePromptTokenCount`，见 `02`） | 平台声明信任时的 `reported_cost_usd` |
| images | `image_count`；**带参考图的必发 `input_image_count`**（否则该协议上的输入费静默记 0） | `output_size/quality`（回显）、`reported_cost_usd` |
| video 提交 | `operation: submit` | — |
| video 轮询 | 完成时的渲染秒数 | — |

vendor 自己的用量块（方舟按像素的「output_tokens」）**嵌在子键下**（`ark_usage`），不铺到顶层——铺了，按 token 的组会算出假钱。

## 网关报价：带头才报、流里在哪一块

一台网关在四个协议面上报价的方式可能各不相同（OrcaRouter，2026-09-26 实测，流式，按应用真实会发的请求）：

| 协议面 | 不带请求头 | 带 `X-OrcaRouter-Include-Cost: true` |
| --- | --- | --- |
| Anthropic Messages | 没有 | `message_delta.usage.cost_usd`；**`message_start` 里没有**——开场快照的数是半截的，不能读 |
| Google `streamGenerateContent` | 没有 | 末块 `usageMetadata.costUsd` |
| Chat Completions（`include_usage`） | 末块 `usage.cost`（没有 `cost_usd`） | 同左 |
| Responses 默认线路 | `response.completed.response.usage.cost` | 同左 |
| Responses 原样线路（`store: true` / include 搜索来源） | 没有 | 没有 |

- 「请报价」的请求头也由信任判断发出：没声明的平台一个头都不加（`02`「信任边界」）。
- 非流式的观察**不能**代替流式：非流式时 Chat 两个字段都有、流式只有一个；应用只发流式就只测流式。
- 流式里取**最后一个**带报价的块；一段内只以收尾那块的数为准（对应 Anthropic：`message_delta` 直接赋值，不保留旧值）。
- 同一台网关上，某条线路（这里是 Responses 原样线路）一分不报：确认应用发的请求走不到它，写进文档；走得到就按「没报」回落。

## 保留键：只有协议自己的换算能写

`input_image_count` 与 `reported_cost_usd` 被记账对**所有 vendor 一视同仁**地读，前者定输入费、后者压过整张表。
所以：

- **凡是把上游 `usage`（或任何上游 map）原样铺进 metadata 的地方都走一个 `upstream_usage(raw)`**：cast + 剔掉两个保留键。
  不走它 = 中转或供应商起个同名字段就能定账。聊天四族 + images 三家 + 流式面，每处一条伪造用例钉住。
- 只有 `reported_cost_from_ticks`（xAI）、`sent_input_images(sent, reported:)`（数出来 / 方舟回报）能产生这两个键，
  且它们**在铺之后**再展开（后写的赢）。
- **不只是 spread**：凡是把上游 body **整个当内部信封返回**的路径（异步作业的轮询最常见，Veo 的 `veoPollResult` 就是）——那里没有铺，
  保留键随整个 body 穿透——返回前 `remove` 掉两个保留键，或自造信封；同样每处一条伪造用例。
- 中转协议（走 OpenAI Images 形状的中转）不翻报价：**中转的价在用户填的表里。** 例外只有平台表里声明过、且地址对得上的网关（`02`）。
- 新增一个协议时的自查：它铺了上游 map 吗 → 走 `upstream_usage`；它带参考图吗 → 发 `input_image_count`；
  它自己造图片块吗 → 每块带两个键；它把上游 body 当信封原样返回吗 → 返回前剔保留键。
