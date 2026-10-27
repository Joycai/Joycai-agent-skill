# 算钱

> 适用范围：本篇保留原项目的参考实现与故障记录。接口名、固定字段、阈值、UI 和未实现能力不是通用要求；采用前按 [skill 入口](../SKILL.md) 的约束与目标项目需求裁剪。


一份 `cost(row)` 供显示、汇总、导出与检查点共用；先选核算路径，再汇总同币种、互不重叠的费用项。

```text
cost(row):
  if trusted_complete_total_for_same_scope(row):
      return reported_cost                         # 0 有效，不与估算相加
  if row.accounting_schema_version uses components:
      return sum_known_components_with_completeness_status(row.components)
  switch row.billing_mode:                         # 兼容旧列，不再叠加 components
    token:   input_tokens * input_price / 1e6
           + cache_tokens * (cache_price ?? input_price) / 1e6
           + output_tokens * output_price / 1e6
    request: request_count * request_price + input_units * input_unit_price
    spec:    output_units * output_unit_price + input_units * input_unit_price
```

旧 token 三桶仅适用于输入同价的情形。多模态 token 或视频输入费用必须走费用项扩展，不能静默丢回旧公式。`snapshot_cost(row)` 忽略报价后走同一逻辑，保留估算状态和缺失项。

## 视频：输出秒数、输入秒数、图片分别计价

```text
estimate = output_billable_seconds * output_rate(output_spec)
         + input_video_billable_seconds * input_video_rate(output_spec)
         + max(0, input_images - free_images_per_request) * input_image_rate
```

这里只对已知数量与命中价格计算；未知时返回不完整状态。音频等免费项保留用量与明确零价，不把缺价当免费。输入/输出秒数不能相加后统一乘价，也不能再给 total_seconds 收一次费。匹配维度、价格快照与费用项见 [数据模型](data-model.md)。

厂商规则唯一正文为 [视频 API](../../ai-media-api-integration/references/video-generation.md) 的 FACT-MINIMAX-VIDEO-004 与 FACT-XAI-VIDEO-006：H3 的输入视频按输出分辨率选价；Max 输入/输出单价不同；再生成是新任务，原素材重新计费；Context-IR 按 token 另计。普通视频回报的折算 token 不与秒数费相加。

## 分模态 token：文本输入、图片输入、图片输出

```text
cost = (text_uncached * text_input_price + text_cached * text_cache_price
      + image_uncached * image_input_price + image_cached * image_cache_price
      + image_output * image_output_price) / 1e6
```

- 适配层先确定每个明细是否包含缓存，再从对应模态总量扣除已知缓存量；不能总输入扣一次、分桶又扣一次。计数不守恒或出现负数时标记异常，不用 clamp 掩盖。
- `input_tokens`、`total_tokens` 与模态明细是包含关系，不能都计费。未知模态不能全按文本价；只有实际模型契约证明单一输出模态时才可将输出总量作为图像输出量。
- GPT-Image 2/2.5 的输入图按 token，不按张补费；尺寸/质量对应的单图价格仅可作输出估算，不能代替完整请求费用。字段、缓存适用范围和官方价格见 [GPT Image 计量](../../ai-media-api-integration/references/image-generation.md#gpt-image-token-accounting)。
- 缓存命中未回报时不能推定未命中，更不能伪造模态缓存量。可提供明确标注的“按非缓存价估算”，实际优惠需账单证据；不要冒充已核对金额。
- Responses 主模型与图像工具各用自己的模型、用量范围和价格快照；确认二者无覆盖后求和。主模型总缓存字段不代表图像工具缓存。
- 流式 partial 图、最终图和最终汇总必须去重；仅在确认最终输出用量未含 partial 费用时补独立项，否则会重复收费。取消时保留已知用量，缺终态标不完整。

## 规范化用量与核算边界

原始字段的包含关系、缓存桶、思考和工具 token 口径统一见 [API usage 正文](../../llm-api-integration/references/errors-probing-observability.md)。核算层只接收规范化计数及其来源，不维护第二份厂商字段表。

- 明确各桶是否重叠以及适用单价；缓存读、写、文本输入、图像输入或工具费用不同价时单独表达，不能声称一个输入价可精确覆盖全部。
- 模型 token 之外的按次/按条工具费用需要独立费用项或可信上游总价；信息不足时标记成本不完整，不用 0 补齐。
- 参考项目把部分维度合并是产品取舍；需要估算时显示估算口径与缺失项。价格本身不在本文硬编码。

## 档位匹配

```
match(rates, spec):
  tier = tier_of(spec.size, rates)            # 像素尺寸落在表里哪个 NK 档，见下
  best = null; best_exact = false
  for rate in rates (按表顺序):
    exact = true
    if rate.size    != null && rate.size    != spec.size:
        if tier == null || rate.size != tier: continue
        exact = false                          # 靠档位匹配上的
    if rate.quality != null && rate.quality != spec.quality: continue
    if rate.seconds != null && rate.seconds != spec.seconds: continue
    better = best == null
          || rate.specificity >  best.specificity
          || (rate.specificity == best.specificity && exact && !best_exact)
    if better: best = rate; best_exact = exact
  return best     # null = 未覆盖：单价未知，matched = false，成本不完整
```

规则一句话：**空条件匹配一切（包括没有值的维度），填得最多的行赢，同样多先写的赢，同样多时精确尺寸赢档位尺寸。**
用户不需要排序，也不需要写兜底行——`1080p + high` 自然压过 `1080p` 压过全空。

### 按面积归档 `tier_of`

自由尺寸端点（qwen-image、wan、Seedream）**回显像素**（`1696x960`）却**按档计费**（1K / 2K）。表写档、请求带像素时：
`NK` 档代表边长 `N·1024` 的正方形面积；像素尺寸取**对数尺度上面积最近**的档，**只在表里真有的档之间比**。
所以 wan 的 1K 档推荐尺寸 1696×960（1.63 MP）落 1K（1.05 MP）而不是 2K（4.19 MP）；有 `1.5K` 行的表按该家的分法切。
不写每家的边界表。

### 归一化（两边都过）

| 输入 | 输出 |
| --- | --- |
| `1k` / `1.5K` | `1K` / `1.5K`（K 大写，小数保留） |
| `768P` | `768p`（p 小写） |
| `1024*1024` / `1024×1024` / ` 1024 X 1024 ` | `1024x1024`（四种拼法都认：`x X * ×`，容忍空白） |
| quality | 小写、去空白 |
| seconds | 数字、数字字符串、`8s` → 8；保留合法小数；此处规格条件 ≤ 0 或非数 → 空，计费用量的真实 0 必须保留 |
| `''` `auto` `not_set` `adaptive` | **空**（不带规格） |

## 单位怎么数

| `output_unit` | `output_units` | 什么时候定 |
| --- | --- | --- |
| image | 按供应商定义的计费图片张数 | 响应/账单证据到达时；未交付不自动证明输入免费 |
| second | **请求的**秒数（`spec.seconds`） | 提交时；完成后按上游报的计费时长**结算**（[recording](recording.md)） |
| clip | 1 | 提交时 |

## 输入图一侧

```
sent    = max(0, input_image_count)                       # 协议发布的张数
charges = input_unit_price > 0                            # 单位不参与：张 / 秒 / 条都收
charged = billing_confirmed ? max(0, sent − max(0, free_units)) : unknown
row.input_images = sent; row.input_units = charged; row.input_unit_price = charges ? price : 0
  # 提交估算可用 sent；billing_confirmed 由供应商计费证据决定，不以产物是否交付代替
```

- **单位不参与**（2026-09-22 起）：原先只有单位为「张」的组收，理由是「没有视频协议发布张数」；xAI `grok-imagine-video-1.5`
  实测首帧 / 参考图 $0.01/张（按秒标价之外另收；当时标价页未写，当前价格见视频 API 正文）后推翻——视频协议提交时发布张数（[recording](recording.md)），按秒 / 按条照收。
- **按次模式也收**：按次行的 `spec` 只有输入三列（`inputs_only`），`cost = requests × request_price + input_units × input_unit_price`。

- **未交付不等于免费**：失败、审核拦截、取消及输入处理费分别按供应商规则确认；证据不足保留待结算，不能将某平台失败免费外推。
- 免费张数的范围来自供应商规则；每请求、每任务与账期额度不能混用。本文公式仅适用于每请求/任务免费额度。
- 张数在**组完请求体之后**数：按上限截断后再丢掉读不出的附件，截断后的长度会为没发出去的图收钱。
- 上游回报的张数优先（方舟 `usage.input_images`）；回报的 **0 要明发**——流式合并时后一块不写的键不会覆盖前一块。
- 实测：xAI 出图每张 $0.01、线性、无免费、`n>1` 时**按请求收一次不乘张数**；xAI 视频（1.5）每张同价（文生 $0.08 → +1 首帧 $0.09 → +2 参考图 $0.10）。

## 上游报价

有的供应商在回包里直接写这次扣了多少（xAI images：`usage.cost_in_usd_ticks`，**1 tick = $10⁻¹⁰**，含输入图）；有的网关
也写（OrcaRouter，四个协议面各一种字段，见 [recording](recording.md)）。
- 协议翻成美元发布为 `reported_cost_usd`；换算只写一处。
- **同范围完整可信总价替换估算，不叠加**；报价覆盖的请求、费用项与币种必须明确。部分报价只替换对应费用项，缺项保持不完整。
- **空 ≠ 0**：没报是 NULL；上游说 0 就是 0。负数、非有限数 → 当没报。
- 档位快照**照写**在同一行：用量页把「上游报价」与「档位估算」对照，不等就是表该改的信号（`auto` 质量由模型定档，不等是常态）。
- 同范围完整可信报价已覆盖的部分不计「未覆盖」；部分报价不能隐藏其它费用项的缺口。
- 中转协议**默认不翻**：中转有自己的价。接受的边界：把直连 vendor 指到原样转发 `usage` 的中转 → 报的是供应商收中转的价。

### 信任边界：按平台声明，不按字段

同范围完整报价替换估算，所以**收不收是信任问题，不是解析问题**。一个 OpenRouter 形态的中转在 Chat Completions 上本来就回
`usage.cost`——字段名说明不了它是不是这台服务器实际扣的钱。

```
trusted_platform(request):
  p = request.platform_label                        # 作者选的「这是谁」
  return declares_reported_cost(p)                  # 平台表：测过「报的 = 实扣」才写
     and platform_of_address(request.base_url) == p # 地址也得指向它
     ? p : none

reported_cost_of(platform, family, usage):
  if platform == none: return null                  # 不发请求头、不读字段
  v = FIELD[family](usage)                          # 各协议面一种字段，换算只写这一处
  return finite(v) && v >= 0 ? v : null
```

- **声明要实测**：拿回包里的数对照该平台自己的账单接口（OrcaRouter：`GET /v1/generation` 的 `total_cost`）。相等才写进平台表；
  差一个计价单位以内（那台网关按 1/500,000 美元取整）可接受，写进文档。
- **标签 + 地址两道门**：别处（能力表、界面）信作者选的平台标签是对的；只有定账这一处还要地址相符——作者可以先选平台再改地址，
  标签不跟着变。被标错的中转既收不到「请报价」的请求头，回的数也不收。
- **不做组上的「信任上游报价」开关**：要界面、要迁移，而这类网关的用户多半根本没建组，开关无处可开；平台声明零配置即生效。

### 几次请求记成一行：全报才加

agent 的多轮、一个被上游拆成几段的回合（Anthropic `pause_turn`）、分段摘要——同模型、同价格版本与币种的 token 可相加；不同模型/档位保留各自费用项。报价汇总必须覆盖所有独立范围，不能重复计入父级总价与子项：

```
add_reported(acc, next):          # acc: 还没有 = undefined；有一次没报 = null
  if acc == null or next == null: return null
  return acc == undefined ? next : acc + next
row.reported_cost = acc ?? null   # 零次 = 没报，不是 0
```

半截的和会把没报的那几次当免费——报价压过整张表，那几次的 token 就白用了。`null` 让整行回落到计费组，按全部 token 算。
回退也可能缺价格或用量；这种情况标记成本不完整，不把 $0 当成完整总价。

### 显示的钱与记的钱同一口径

草稿卡片、会话累计这类「这次花了多少」的数字也要接报价，并走同一个 `cost()`——否则没配组的模型卡片上 $0、账上有钱。
报价参数在写入口与显示函数上都**必填、没有默认值**（没有就明写 null）：漏传不报错，只会静默按表算。
