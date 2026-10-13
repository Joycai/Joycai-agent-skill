# 02 · 算钱

一份 `cost(row)`，分成几个「部分」求和；每种模式只有自己的部分非零。界面按部分上色，汇总按部分加。

```
parts = { input, cache, output, request, spec, spec_input, reported }

cost(row):
  if row.reported_cost != null:                       # 上游报价压过一切
      return parts(reported = row.reported_cost)      # 其余六项 0
  switch row.billing_mode:
    token:   input  = input_tokens  * input_price  / 1e6
             cache  = cache_tokens  * (cache_price ?? input_price) / 1e6
             output = output_tokens * output_price / 1e6
    request: request = request_count * request_price
    spec:    spec       = output_units * output_unit_price
             spec_input = input_units  * input_unit_price
  total = sum(parts)
```

`snapshot_cost(row)` = 去掉报价再算一遍——用量页写「档位估算」用它，算式仍只有一份。

## token 口径的三个陷阱（协议事实，2026）

1. **缓存计数：子集 vs 不重叠。** Chat Completions / Responses / Google 的 `cached_tokens` 是 prompt 的**子集**；
   Anthropic 的 `input_tokens` 只是**未命中**的余量，缓存读、缓存写各自单列。行上存的是**不重叠**的两个数：
   `input = prompt − cached`，`cache = cached`。Anthropic 协议先把三桶之和当 `prompt_tokens` 发布，记账再减。
   缓存**写入**比基础价贵，没有第四个价就归入全价桶（高估的那一侧才安全）。
2. **思考 token：已含 vs 未含。** ①②④ 的输出已含思考；Google 的 `candidatesTokenCount` **不含**，思考在
   `thoughtsTokenCount`——输出 = 二者之和，否则「想 5k 答 500」记成 500。
3. **图像 token。** 按 token 计费的出图模型（gpt-image、Gemini image）把图算进 `input_tokens` / `output_tokens`；
   图像输入单价（$8/M）与文本（$5/M）不同而组只有一个输入价——差额小，接受。
4. **服务端工具的 token：另算 vs 已含。** Google 的内置工具（读网页、代码执行、搜索结果回填）记在
   `toolUsePromptTokenCount`，它**在 `promptTokenCount` 之外**——实测 prompt 20 + candidates 65 + toolUse 77 = total 162。
   输入 = 二者之和（与思考 token 进输出同理），否则开了代码执行的请求少记一截输入。
5. **按次收费的服务端工具，token 表根本表达不了。** Google 搜索按**查询条数**收（经一台网关实测约 $0.014 一条），
   一次回答搜几条由模型定、协议没有上限字段可发——一次实测一个问题搜了 6 条（$0.084），token 部分只是零头。
   按 token 的组对这类请求**必然大幅低估**；只有上游报价能记对。没有报价的平台，至少在开关旁写明「按条计费、会少算」。

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
  return best     # null = 未覆盖：单价 0，output_spec.matched = false
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
| seconds | 数字、数字字符串、`8s` → 8；≤ 0 或非数 → 空 |
| `''` `auto` `not_set` `adaptive` | **空**（不带规格） |

## 单位怎么数

| `output_unit` | `output_units` | 什么时候定 |
| --- | --- | --- |
| image | 响应实际携带的图片张数 | 响应到达时；0 张 = 请求失败 = 输出 0、输入也不收 |
| second | **请求的**秒数（`spec.seconds`） | 提交时；完成后按上游报的实际时长**结算**（`03`） |
| clip | 1 | 提交时 |

## 输入图一侧

```
sent    = max(0, input_image_count)                       # 协议发布的张数
charges = input_unit_price > 0                            # 单位不参与：张 / 秒 / 条都收
charged = charges && delivered ? max(0, sent − max(0, free_units)) : 0
row.input_images = sent; row.input_units = charged; row.input_unit_price = charges ? price : 0
  # spec：delivered = output_units > 0；request：一律 delivered（按次 = 按成功请求），只写输入三列、输出四列留空
```

- **单位不参与**（2026-09-22 起）：原先只有单位为「张」的组收，理由是「没有视频协议发布张数」；xAI `grok-imagine-video-1.5`
  实测首帧 / 参考图 $0.01/张（按秒标价之外另收、标价页不写）后推翻——视频协议提交时发布张数（`03`），按秒 / 按条照收。
- **按次模式也收**：按次行的 `spec` 只有输入三列（`inputs_only`），`cost = requests × request_price + input_units × input_unit_price`。

- **一张没交付就不收输入费**：方舟明说失败免费；别的路由上「没出图」同样不是事件。
- 免费张数**按每次请求**（首张免费 = 每次请求的第一张）。上游若按账期免——记多了，接受（见 `06`）。
- 张数在**组完请求体之后**数：按上限截断后再丢掉读不出的附件，截断后的长度会为没发出去的图收钱。
- 上游回报的张数优先（方舟 `usage.input_images`）；回报的 **0 要明发**——流式合并时后一块不写的键不会覆盖前一块。
- 实测：xAI 出图每张 $0.01、线性、无免费、`n>1` 时**按请求收一次不乘张数**；xAI 视频（1.5）每张同价（文生 $0.08 → +1 首帧 $0.09 → +2 参考图 $0.10）。

## 上游报价

有的供应商在回包里直接写这次扣了多少（xAI images：`usage.cost_in_usd_ticks`，**1 tick = $10⁻¹⁰**，含输入图）；有的网关
也写（OrcaRouter，四个协议面各一种字段，见 `03`）。
- 协议翻成美元发布为 `reported_cost_usd`；换算只写一处。
- **有它就不再算**——压过三种模式的全部算式（它含输入侧，所以不是叠加）；按 token 的默认组（$0）挂着出图模型时也由此记对。
- **空 ≠ 0**：没报是 NULL；上游说 0 就是 0。负数、非有限数 → 当没报。
- 档位快照**照写**在同一行：用量页把「上游报价」与「档位估算」对照，不等就是表该改的信号（`auto` 质量由模型定档，不等是常态）。
- 有报价的行**不算「未覆盖」**：缺口已被报价填上，让用户去补表是让他修不存在的问题。
- 中转协议**默认不翻**：中转有自己的价。接受的边界：把直连 vendor 指到原样转发 `usage` 的中转 → 报的是供应商收中转的价。

### 信任边界：按平台声明，不按字段

报价压过整张表，所以**收不收是信任问题，不是解析问题**。一个 OpenRouter 形态的中转在 Chat Completions 上本来就回
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

agent 的多轮、一个被上游拆成几段的回合（Anthropic `pause_turn`）、分段摘要——几次请求的 token 相加记一行。报价**不能**照样相加：

```
add_reported(acc, next):          # acc: 还没有 = undefined；有一次没报 = null
  if acc == null or next == null: return null
  return acc == undefined ? next : acc + next
row.reported_cost = acc ?? null   # 零次 = 没报，不是 0
```

半截的和会把没报的那几次当免费——报价压过整张表，那几次的 token 就白用了。`null` 让整行回落到计费组，按全部 token 算。
代价：没绑组的模型这一行记 $0（和任何没报价的行一样），接受。

### 显示的钱与记的钱同一口径

草稿卡片、会话累计这类「这次花了多少」的数字也要接报价，并走同一个 `cost()`——否则没配组的模型卡片上 $0、账上有钱。
报价参数在写入口与显示函数上都**必填、没有默认值**（没有就明写 null）：漏传不报错，只会静默按表算。
