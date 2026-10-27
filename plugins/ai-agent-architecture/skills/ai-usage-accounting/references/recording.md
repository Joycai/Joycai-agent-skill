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

1. 提交被接受后持久化供应商/账号/任务 id、实际模型、任务类型、请求规格、整份适用价格规则版本、币种、输入素材数量与时长来源。提交成功不证明已收费；预估项与最终项分开保存。
2. 素材在请求体组装完成后计数；输入图片与输入视频秒数分别保存。没有视频输入可据请求体记 0；有视频但读不到时长则 unknown。协议计量规则见 [视频 API](../../ai-media-api-integration/references/video-generation.md)，不能只返回裸任务 id。
3. 终态规范化得到输入视频计费秒数、输出计费秒数、输入图片数及服务端规格。按提交时的规则快照重新匹配**输入和输出**单价；终态只补齐有证据的字段，缺字段不抹掉已知输入。请求数量只能作估算，不能假装上游确认。
4. 计费时长优先采用供应商的计费 usage；媒体文件容器时长另存为产物元数据，不据此改账。保留小数秒与厂商舍入规则；不得自行取整。total_seconds 不作为第三笔收费，折算 token 也不另收。
5. 同任务、同结算版本幂等落库：输入/输出费用项、最终规格、可信报价及其覆盖范围、状态在一个事务或等价原子事件中更新；更新失败保存待重试。重复轮询/回调不新增费用；旧版本事件不覆盖较新结算。
6. 同币种、同范围完整可信总价覆盖该范围估算，保留原估算供核对。xAI 终态报价字段与换算只在媒体适配层处理；报价为 0 必须保留。任意上游同名字段不能直接覆盖内部可信键。
7. 失败、取消、审核拦截按具体供应商证据确认费用、冲销或保持待结算。停止轮询、下载失败、任务记录过期都不能单独作为免费证据。任务成功但缺费用证据时仍可交付产物，同时显示 estimated / incomplete。
8. 再生成、Context-IR 与后续生成分别保留任务和费用范围，按任务类型选规则；同一个 model id 不意味着同一种计费方式。重新计费的原素材绑定新任务，不能因素材 URL 相同被跨任务去重。base_video 是否收费不得仅据请求中有视频而推断。

异步调整后使受影响日期/分组的汇总检查点失效或重算；修改当前价格不能重写历史。结算失败不遮蔽产物，恢复时查询原任务，不能为补账重新提交生成。

## 协议要发布什么

每个协议把 vendor 字段翻成中性键（[data-model](data-model.md)），记账**只认中性键、不认任何 vendor 字段**：

| 协议类型 | 必发 | 可发 |
| --- | --- | --- |
| 聊天 | 规范化的输入/缓存/输出计数与未知状态；原始字段见 [API usage](../../llm-api-integration/references/errors-probing-observability.md) | 平台声明信任时的 `reported_cost_usd` |
| images | 计费策略需要的张数或规范化模态 token；带参考图时保留实际张数，usage 缺失保持 unknown | `output_size/quality`、同范围可信报价 |
| video 提交 | `operation: submit`、持久任务 id、实际发送的素材计数及未知状态 | 输入视频时长估算及来源 |
| video 轮询 | 终态与已回报的输入/输出计量、规格；缺失保持 unknown | 同范围可信报价、币种与来源 |

vendor 自己的用量块（方舟按像素的「output_tokens」）**嵌在子键下**（`ark_usage`），不铺到顶层——铺了，按 token 的组会算出假钱。

## 网关报价的提取边界

字段、请求头和流式事件位置以 [API 网关报价观测](../../llm-api-integration/references/errors-probing-observability.md#gateway-cost-observations) 为唯一正文。协议层提取并标记来源；本层按 [核算规则](pricing-rules.md) 判断信任、完整性与金额优先级。

## 保留键：只有协议自己的换算能写

`input_image_count` 与 `reported_cost_usd` 被记账对**所有 vendor 一视同仁**地读，前者提供输入张数，后者仅在同范围完整可信时替换估算。新增输入视频量、模态桶、币种与范围也属于内部契约，必须由适配层校验产生；不可任意铺入上游同名字段。
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

MiniMax H3：视频 token 是用量折算，不与秒数/图片重复收费；Context-IR 单独按 tokens 核算。型号、任务类型与原始字段映射见 [FACT-MINIMAX-VIDEO-004](../../ai-media-api-integration/references/video-generation.md#minimax-h3-v2)。
