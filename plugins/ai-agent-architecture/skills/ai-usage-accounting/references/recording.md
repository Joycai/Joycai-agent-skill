# 什么时候记、谁来记

> 适用范围：本篇保留原项目的参考实现与故障记录。接口名、固定字段、阈值、UI 和未实现能力不是通用要求；采用前按 [skill 入口](../SKILL.md) 的约束与目标项目需求裁剪。


## 参考实现：单一写入口

三条到达路径（同步请求、流式、长任务提交）都进同一个 `record_usage(model, config, metadata, options, image_count, row_id?)`：

```
record_usage:
  spec   = price_spec(config, options, metadata, image_count)   # 纯函数：读规格、匹配、数输入图
  prompt = normalized_usage.total_input_tokens                  # 适配层已处理厂商口径
  cache  = normalized_usage.cached_input_tokens                  # 规范化契约保证不重叠
  output = normalized_usage.total_output_tokens                 # 缺失保持 unknown
  row    = { ...counts, input = subtract_if_known(prompt, cache), cache,
             input_price = config.input_price, cache_price = config.effective_cache_price, output_price,
             request_price, billing_mode = config.billing_mode,
             ...spec?.columns, reported_cost = reported_cost_of(metadata) }
  sink(row)                                                       # 写库；测试用 override 换掉
```

`price_spec` 是**纯函数**（不碰库），三条路径各一条测试就能钉住。

## 四条时序规则

1. **先记账，再做别的。** 上游已生成并收费：记账排在「取消检查」「内容拦截抛错」「写进会话」之前。
   中途被取消的流：已到的部分照记，然后再抛取消；内容拦截：先记后抛。
2. **失败隔离且可恢复。** 不用记账异常覆盖已经取得的结果或视频任务 id；保留可重试事件，记录持久化失败状态与日志。按请求/任务 id 幂等写入，重试与结算去重。无法持久保存事件时明确报告记录缺失，不能只 WARN 后假装成功。
3. **按 token 的渠道没回 usage：标记 unknown 并警告一次**（每次调用一次，不是每段续跑一次）。本地栈与不少代理不回 usage；
   「没回」不能读成「0 token」——所以 `prompt_tokens_of` 返回**空**让调用方回退，旧实现以 0 占位；新实现使用可空计数或独立 usage_status，展示与汇总不能将未知当作实际零消耗。
4. **按规格的组带图就记**，哪怕没有 usage 块：中转经聊天面出图常常一个 usage 都不回，图是计费依据。

## 流式

- 块的 metadata **合并，后写的赢**；后一块没写的键不会抹掉前一块的——所以「回报的 0」要明发。
- **每个图片块都带** `input_image_count` 与 `reported_cost_usd`（凡是自己造图片块的地方：单发转流、方舟 SSE、Midjourney）：
  流在出图之后、收尾块之前被放弃时，提前退出的记账只看到图片块。
- 流被放弃：用已合并的 metadata 记一行（图已交付、已收费）。

## 视频：提交记录与实际结算分开

- 提交被接受后记录任务、原始规格、价格快照与 estimated 状态；提交成功本身不能证明已收费。
  行 id = `video:<作业名>`，**持久**，重启后续轮询的进程也能找回。
- 提交时按请求规格估算；完成、失败、取消时按供应商规则与账单证据确认、调整或冲销。保留估算与最终值及来源，不能默认失败也收费。
- **提交返回的不是裸 id**：`submit → {request_id, input_images}`，张数在组完请求体之后数（读不到的附件、互斥被丢的参考图不算：
  xAI 首帧计 1 或 `reference_images` 长度；Sora 数 multipart 文件；百炼数 `input.media[]`；MiniMax 数互斥之后剩下的；
  Veo 数 `image` + `lastFrame` + `referenceImages`）。票据带着它，提交行的 metadata 写 `input_image_count`——输入费对视频生效。
  **新加一个视频协议不报张数 = 该协议上的视频输入费静默记 0。**
- 完成时上游报了实际时长（百炼 `usage.duration`、MiniMax `usage.output_seconds`、xAI `video.duration`）→ **结算**：用提交时同一份
  options 只换时长重新匹配（按时长分档的行可能变），参考实现更新输出四列（数量、单价、单位、规格快照）；仅当此次结算只改变时长时保留输入侧快照；如有输入费调整证据，另行记录调整。
- 完成时上游报了钱（xAI `usage.cost_in_usd_ticks`，**只在终态轮询里**，提交与 pending 都没有）→ 协议经同一个换算发布在 done 信封的
  `reported_cost_usd` 下；结算的第二段在**任何模式**下只写 `reported_cost` 一列——提交行的档位估算从此被压过，快照仍在。
- done 信封上的 `reported_cost_usd` 与实际时长只能由协议自己的换算写入。一个**把上游 body 原样当内部信封返回**的轮询（Veo 的
  operation JSON 就是这样穿透的）必须在返回前 `remove` 掉这两个键，否则挂在中转上的该面塞一个同名字段就压掉整张表（[pitfalls](pitfalls.md)）。
- 结算失败不遮蔽视频产物，但保留待重试状态；使用任务 id 和结算版本防止重复记费。原实现“只改输出四列”的更新形状只是示例，输入费变化或冲销时也必须按证据更新。
- 提交前本地就能判定的错误（缺参考图）不计费、不重试。

## 协议要发布什么

每个协议把 vendor 字段翻成中性键（[data-model](data-model.md)），记账**只认中性键、不认任何 vendor 字段**：

| 协议类型 | 必发 | 可发 |
| --- | --- | --- |
| 聊天 | 规范化的输入/缓存/输出计数与未知状态；原始字段见 [API usage](../../llm-api-integration/references/errors-probing-observability.md) | 平台声明信任时的 `reported_cost_usd` |
| images | `image_count`；**带参考图的必发 `input_image_count`**（否则该协议上的输入费静默记 0） | `output_size/quality`（回显）、`reported_cost_usd` |
| video 提交 | `operation: submit` | — |
| video 轮询 | 完成时的渲染秒数 | — |

vendor 自己的用量块（方舟按像素的「output_tokens」）**嵌在子键下**（`ark_usage`），不铺到顶层——铺了，按 token 的组会算出假钱。

## 网关报价的提取边界

字段、请求头和流式事件位置以 [API 网关报价观测](../../llm-api-integration/references/errors-probing-observability.md#gateway-cost-observations) 为唯一正文。协议层提取并标记来源；本层按 [核算规则](pricing-rules.md) 判断信任、完整性与金额优先级。

## 保留键：只有协议自己的换算能写

`input_image_count` 与 `reported_cost_usd` 被记账对**所有 vendor 一视同仁**地读，前者定输入费、后者压过整张表。
所以：

- **凡是把上游 `usage`（或任何上游 map）原样铺进 metadata 的地方都走一个 `upstream_usage(raw)`**：cast + 剔掉两个保留键。
  不走它 = 中转或供应商起个同名字段就能定账。聊天四族 + images 三家 + 流式面，每处一条伪造用例钉住。
- 只有 `reported_cost_from_ticks`（xAI）、`sent_input_images(sent, reported:)`（数出来 / 方舟回报）能产生这两个键，
  且它们**在铺之后**再展开（后写的赢）。
- **不只是 spread**：凡是把上游 body **整个当内部信封返回**的路径（异步作业的轮询最常见，Veo 的 `veoPollResult` 就是）——那里没有铺，
  保留键随整个 body 穿透——返回前 `remove` 掉两个保留键，或自造信封；同样每处一条伪造用例。
- 中转协议（走 OpenAI Images 形状的中转）不翻报价：**中转的价在用户填的表里。** 例外只有平台表里声明过、且地址对得上的网关（[pricing-rules](pricing-rules.md)）。
- 新增一个协议时的自查：它铺了上游 map 吗 → 走 `upstream_usage`；它带参考图吗 → 发 `input_image_count`；
  它自己造图片块吗 → 每块带两个键；它把上游 body 当信封原样返回吗 → 返回前剔保留键。
