# 01 · 数据模型

四个实体、一个值对象、一组中性键。字段名用蛇形写，只是约定。

## 计费组 FeeGroup（`fee_groups`）

| 字段 | 类型 | 归属模式 | 说明 |
| --- | --- | --- | --- |
| `name` | text | — | 用户起的名，如「Gemini Pro」「xAI Imagine 2.0」 |
| `billing_mode` | `token` \| `request` \| `spec` | — | 未知值按 `request` 读（历史上的默认解释） |
| `input_price` | real | token | 每百万输入 token |
| `cache_input_price` | real **可空** | token | 每百万缓存命中 token；**空 = 同 `input_price`**，`0` = 真免费 |
| `output_price` | real | token | 每百万输出 token |
| `request_price` | real | request | 每次请求 |
| `output_unit` | `image` \| `second` \| `clip` | spec | 一次请求数什么：出的张数 / 请求的秒数 / 一条 |
| `output_rates` | JSON 数组 | spec | 档位表，见下 |
| `input_unit_price` | real，默认 0 | spec · request | 每张参考图；0 = 不收输入费（多数组） |
| `input_free_units` | int，默认 0 | spec | 每次请求免费张数（Seedream 5.0 pro「首张免费」） |
| `sort_order` | int | — | 用户拖拽的顺序，有自己的写入口（见 `04`） |

**三种模式共用一行、字段全保留。** 切模式不清空别的模式的价，切回来还在。

派生规则（只在一处定义，所有摘要与解析器共用）：
- `charges_input_images = mode ∈ {spec, request} && input_unit_price > 0`——单位不参与（2026-09-22 起；此前只有单位为「张」的组收，
  被 xAI 视频实测推翻：首帧 / 参考图 $0.01/张另收）。按 token 不收：它的图在 token 里。
  只有按张的组收输入费：没有视频面回报它收到的参考图，按秒 / 按条的组即使填了值也不收。
- `other_specs_at_zero = mode == spec && 没有全空条件的行`。

### 档位行 SpecRate

```
{ size?: text, quality?: text, seconds?: int, price: real }
```

- 三个条件**都可选**；空条件匹配一切；三个都空 = 兜底行（「其他规格」）。
- `specificity = 填了几个条件`（0–3），是匹配的平局裁决。
- 条件**存进去之前先归一化**（见 `02`），匹配时是纯相等。
- 同一张表里两行条件完全相同 = 配置错误，编辑器拒绝保存；只有一行没填价也拒绝。
- 编码成 JSON 文本存在一列里；空、空白、坏 JSON 都读成**空表**（组按 0 计、用量页标「未覆盖」），不抛。

## 模型 ↔ 组

- `models.fee_group_id`（可空）。删组时把引用置空，不删模型。
- `channels.default_fee_group_id`（可空）：该渠道下新建 / 发现的模型预填的组。
- 请求时把组的字段**解析进请求配置**（一个扁平的 `config`：`billing_mode`、三个 token 价、`request_price`、
  `output_unit`、`output_rates`、`input_unit_price`、`input_free_units`）；记账只看这个 config，不再回头查库。

## 规格 OutputSpec（值对象）

```
{ size?: text, quality?: text, seconds?: int }     全空 = 没有规格
```

读取优先级（每个维度独立）：**上游回显 > 请求参数**。

| 维度 | 上游回显键（中性） | 请求参数键（应用自己的词汇） |
| --- | --- | --- |
| size | `output_size` | `imageSize` → `resolution` |
| quality | `output_quality` | `quality` → `videoQuality` |
| seconds | `output_seconds` | `seconds` |

「让上游决定」的取值（`''`、`auto`、`not_set`、`adaptive`）读成**空**：它们不带规格，只有空条件的行能匹配。
标签：`1080p · high · 8s`，缺的维度不写。

## 用量行 UsageRow（`token_usage`）

一行 = 一次计费的请求（视频 = 一次提交）。分五组列：

| 组 | 列 | 说明 |
| --- | --- | --- |
| 身份 | `task_id`, `model_id`, `model_pk`, `timestamp` | `task_id` 是标签 + 时间戳（`req_…` / `subagent:…`）或视频作业 id（`video:<op>`，可跨重启找回）；`model_pk` 指向模型行，模型删了仍能按名显示 |
| 计数 | `input_tokens`, `cache_tokens`, `output_tokens`, `request_count` | **输入与缓存不重叠**，二者之和 = 全部 prompt token |
| token 价快照 | `input_price`, `cache_price`（可空）, `output_price` | 记录**解析后**的价：组没填缓存价时这里写输入价；空只出现在老行上 |
| 按次快照 | `request_price` | |
| 规格快照（七列） | `output_units`, `output_unit_price`, `output_unit`, `output_spec`(JSON), `input_images`, `input_units`, `input_unit_price` | 见下 |
| 上游报价 | `reported_cost`（可空） | 供应商自己报的这次金额，含输入图；空 = 没报 |
| 模式 | `billing_mode` | 当时组的模式；决定读哪组列 |

规格快照的七列：
- `output_units` 数了多少（张 / 秒 / 1）；`output_unit_price` 命中行的单价；`output_unit` 单位名。
- `output_spec` = `{size?, quality?, seconds?, matched: bool}`——**规格 + 有没有命中**，用量页据此数「未覆盖」。
- `input_images` **实际发出**的参考图张数（给界面看）；`input_units` **计费**张数（免费的已扣）；`input_unit_price` 单价。
  张数与计费张数分开存：「发 1 张免 1 张」与「没发」计费都是 0，只有前者该显示。
- 「七列全空或全 0」读成没有规格快照（旧行、其它模式的行）。

## 检查点 UsageCheckpoint（`usage_checkpoints`）

范围超过阈值（如 500 行）时按天写一条：总输入 / 缓存 / 输出 token、请求数、总成本、按组成本（JSON，键是组 id）。
统计从最近的检查点起累加；**检查点也只能从行的 `cost()` 算出来**，不是另一套算式。

## 协议发布的中性 metadata 键

协议把 vendor 字段翻成应用词汇，记账只认这些键：

| 键 | 谁发 | 含义 |
| --- | --- | --- |
| `prompt_tokens` / `input_tokens` / `promptTokenCount` | 各族 | 三种拼法都读；缓存明细在 `prompt_tokens_details.cached_tokens` / `cachedContentTokenCount` / `cache_read_input_tokens` |
| `completion_tokens` / `output_tokens` / `candidatesTokenCount` (+ `thoughtsTokenCount`) | 各族 | 见 `02` 的思考 token 陷阱 |
| `output_size` / `output_quality` / `output_seconds` | 有回显的 images / video 协议 | 上游实际服务的规格 |
| `input_image_count` | 每个带参考图的 images 协议 | 实际放进请求体的张数，或上游回报的张数 |
| `reported_cost_usd` | 上游报金额的协议（xAI images），及平台声明信任的网关（OrcaRouter 四个协议面） | 这次请求的实扣金额（美元）；几次请求合一行时全报才加（`02`） |
| `image_count`、`operation` | images / video | 出图张数；`submit` 标记提交行 |
| `ark_usage` / `dashscope_usage` | 方舟 / 百炼 | vendor 自己的用量块**嵌在子键下**，不铺到顶层——它们的「token」不是 token 价格能乘的东西 |

后两个键（`input_image_count`、`reported_cost_usd`）是**保留键**：原样铺上游 map 时必须剔掉（`03`）。
