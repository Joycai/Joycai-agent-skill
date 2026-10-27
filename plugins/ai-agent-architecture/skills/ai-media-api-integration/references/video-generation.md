# 视频生成管线（异步任务协议：千问万相 / MiniMax / xAI / Sora / Veo）

> 阅读边界：带日期的厂商行为只适用于所记录组合；类名、路由表、存储格式与 UI 属于参考实现。付费验证与失败重试遵循 [媒体接入入口](../SKILL.md)，不将历史“零成本”描述当作当前保证。


> 本篇解决的问题：在多协议 AI 层里接入视频生成。
> 本篇覆盖的是「提交拿 task_id → 轮询 → 结果 URL」的异步任务协议，但五家的
> 提交 body、状态词表、结果位置、保留期、取消语义各不相同。
> 不读会踩的坑：失败任务装在 HTTP 200 里被通用错误检查放行，轮询循环把
> FAILED 当 PENDING 转到天荒地老；结果直链过期后入库，图库/画廊静默腐烂；
> 过期 task_id 被当成瞬时错误无限重试；「取消」只取消了本地轮询，上游照跑
> 照计费；必填参数无服务端默认，靠"不发字段用默认"的习惯直接 400。
>
> 2026-08 增补，来源：千问平台（阿里百炼）与 MiniMax 官方文档全量核对。
> 与[image-generation](image-generation.md)共享异步轮询循环的设计点（总 deadline、可中断 sleep、瞬时失败
> 限次、task_id 先行入日志），此处不重复，只写视频独有部分。

---

## 1. 统一形状：submit / poll 两个入口，调用方只见归一化结果

视频任务天然跨请求（提交与轮询之间隔着分钟级时间，可能跨进程存活），所以
不能学出图藏在一个同步函数里——task_id 必须暴露给调用方持久化：

```text
提交(连接, 请求)   -> task id（不透明字符串，调用方负责持久化）
轮询(连接, task id) -> 状态；每次轮询调一次
  状态 = { done: false, status? }   status 仅展示，永不作分支条件
       | { done: true, videoUrl }
  失败一律以错误抛出，不进返回值

请求 = { prompt,
         media?: [{ role: first_frame|last_frame|reference_image|reference_video|reference_audio,
                    url: data URL 或公网 URL }]      适配器转成各家拼写
         resolution?, duration?, ratio?, audio?, extraBody? }
```

- **首帧/尾帧/参考素材统一用 role 标注**，不做 `firstFrameImage` 这类独立
  字段——千问（`input.media[].type`）与 MiniMax（`content[].role`）都已收敛
  到这个形状，独立字段反而要在 adapter 里拆回去。
- **失败以抛错送达，不进 `done` 变体**——轮询方对失败唯一正确的反应是停止
  并上报，把它做成返回值就会有调用方漏检。

## 2. 五家事实速查

| | 千问 wan3.0 | MiniMax v2 (H3) | xAI | OpenAI Sora | Google Veo |
| --- | --- | --- | --- | --- | --- |
| 提交 | `POST /api/v1/services/aigc/video-generation/video-synthesis` + `X-DashScope-Async: enable` | `POST /v2/video_generation` | `POST /v1/videos/generations`（JSON） | `POST /v1/videos`（**multipart**） | `:predictLongRunning` |
| 轮询 | `GET /api/v1/tasks/{id}`（图片任务共用） | `GET /v2/query/video_generation/{id}` | `GET /v1/videos/{request_id}` | `GET /v1/videos/{id}` + `/content` 下载 | operations `GET` |
| 状态词表 | `PENDING/RUNNING/SUCCEEDED/FAILED/CANCELED/UNKNOWN` | `queued/running/succeeded/failed/cancelled` | `pending/done/expired/failed` | `queued/in_progress/completed/failed` | `{done: bool}` |
| 结果位置 | `output.video_url`（顶层扁平） | `task.content.url`（直链，v1 的 file_id→retrieve 二段式已废除） | `video.url`；`video.duration` 报实际秒数；done 回包带 `usage.cost_in_usd_ticks` | `/content` 端点流式下载 | operation response 内 URI |
| 保留期 | task_id 24h | **任务记录 7 天** | — | — | — |
| 取消 | — | `DELETE /v2/video_generation/{id}`，**仅 `queued` 可取消**（免扣费），succeeded/failed 变删除记录，running 不可操作 | — | — | — |

千问 wan3.0 提交 body：`input.prompt`（≤2 万字符，可用「图1」指代素材）+
`input.media[]{type, url}`；`parameters`：`resolution`（480P/720P/1080P，
默认 1080P）、`ratio`（adaptive/16:9/…）、`duration`（2–30s，`-1` 智能）、
**`audio` 默认 true**、`prompt_extend` 默认 true。usage 报秒数/fps/分辨率，
无 token（字段 `video_count`(=1) / `duration` / `fps` / `SR` / `ratio`）。**创建 → 轮询 → 取结果**
【实测 2026-08-29，Joycai 用户账号】跑通；失败态与取消分支未走到。

火山方舟 Seedance：订阅套餐 base 上 `/contents/generations/tasks` 对 `doubao-seedance-1-0-pro-250528`、`-1.0-pro`、`-2.0`、
`-1-0-lite-t2v-250428` 全回 `404 UnsupportedModel`【实测 2026-09-18】——要按量 key，协议形状本库未覆盖。

MiniMax H3 当前契约与实测见 [§2.1](#minimax-h3-v2)（FACT-MINIMAX-VIDEO-001–005）；不要把 H3 的参数范围套用到整个家族。

**xAI `grok-imagine-video-1.5` 实测**（2026-09-22，`POST /v1/videos/generations` → `GET /v1/videos/{request_id}`，三条 1 s · 480p，来源 Joycai）：
- 提交回包只有 `{"request_id"}`；轮询 pending 是 **HTTP 202** + `{status: pending, progress}`，done 是 200 +
  `{status: done, video: {url, duration, respect_moderation}, model, usage: {cost_in_usd_ticks}, progress: 100}`——
  **报价只在终态回包里**，提交时没有；`video.duration` 报实际渲染秒数（可用于结算）。OpenAPI：`VideoResponse.usage` 是
  `MediaUsage`（`cost_in_usd_ticks` 必有，token 字段视频一律省略）；`video.url` 为空且 `respect_moderation: false` = 被审核拦下。
- **参考图另收钱，标价页没写**（页面只写 $0.080/s）：文生 800 000 000 = $0.08；首帧 `image` 900 000 000 = +$0.01；
  `reference_images` 两张 1 000 000 000 = +$0.02——**$0.01/张、线性**，与出图面同价。`duration: 1` 按 1 s 计，没有最低计费秒数。
  720p / 1080p 是否加价：【未验】。初代 `grok-imagine-video`（$0.050/s）已下线（2026-09-22），不再追。
- `GET /v1/video-generation-models` 只列 id / 模态 / 别名，**没有 `pricing`**（出图面的同名端点有）；1.5 的 `input_modalities` 是
  text / image / audio（`reference_audios`），初代是 text / image / video（`/videos/edits`、`/videos/extensions`）。

<a id="minimax-h3-v2"></a>
### 2.1 MiniMax H3 v2：模型、素材与任务类型

**FACT-MINIMAX-VIDEO-001–004** 为【文档 2026-10-27】；实测见 005。官方来源：[使用指南](https://platform.minimax.cn/docs/guides/video-generation.md)、[创建](https://platform.minimaxi.com/docs/api-reference/video-generation-v2-create.md)、[查询](https://platform.minimaxi.com/docs/api-reference/video-generation-v2-query.md)、[列表](https://platform.minimaxi.com/docs/api-reference/video-generation-v2-list.md)、[取消/删除](https://platform.minimaxi.com/docs/api-reference/video-generation-v2-delete.md)、[Context-IR](https://platform.minimaxi.com/docs/api-reference/video-generation-v2-h3-context-ir.md)、[再生成](https://platform.minimaxi.com/docs/api-reference/video-generation-v2-regeneration.md)、[定价](https://platform.minimaxi.com/docs/pricing/overview.md)。指南列 H3 / Max；创建页另列 Highspeed / Lite。账户可用性以实测为准。

**FACT-MINIMAX-VIDEO-001 — 创建契约。** 官方文档 base 为 `https://api.minimax.cn`，使用 `Authorization: Bearer <API_KEY>` 和 JSON；`POST /v2/video_generation` 返回 `task_id`。v2 直接返回视频 URL，不走 v1 的 file_id → retrieve；错误处理见 003。

| model | resolution | duration（整数秒） | 证据 |
| --- | --- | --- | --- |
| `MiniMax-H3` | `768P`、`2K` | 4–15 | 📄 创建页；历史 2K 首尾帧实测见下 |
| `MiniMax-H3-Highspeed` | `768P` | 4–15 | 📄 未实测 |
| `MiniMax-H3-Lite` | `480P`、`768P` | 4–15 | 📄 未实测 |
| `MiniMax-H3-Max` | `480P`、`768P` | 5–15 | 📄 未实测；不支持 4 秒 |

- schema 必填 `model/content/resolution/duration`。Lite/Max 的 resolution 描述同时写“默认 768P”，与 required 列表不一致：客户端显式发送，勿依赖省略（OQ-041）。
- `content` 必须有非空 `{"type":"text","text":"…"}`，单项最多 7000 字符。媒体使用嵌套 `{"type":"image_url","image_url":{"url":"…"},"role":"first_frame"}`；`video_url/audio_url` 同形，不能平铺 `url`。
- 图片 role：`first_frame/last_frame/reference_image`；仅一张图片不填 role 默认首帧。文档组合列表支持单尾帧，但 role 说明又要求尾帧与首帧成对；单尾帧保留文档冲突，不标为已验证支持。
- 首尾帧模式与参考模式互斥：出现任一 `reference_image/reference_video/reference_audio` 就不能混入 `first_frame/last_frame`。发送前校验。
- `ratio`：`adaptive/21:9/16:9/4:3/1:1/3:4/9:16`。纯文本必填具体比例，不能 adaptive；首尾帧模式恒按图片自适应，其他合法值会被忽略；参考模式可省略为 adaptive，但 **Lite 参考模式必须显式指定具体比例**。
- Max 独有 `extra.prompt_expansion_mode`：`disabled/balanced/quality`，默认 balanced，不能拼成 balance；`extra` 不接受未声明字段。`aigc_watermark` 默认 false；这些字段本轮未测。

最小首尾帧请求示例（素材 URL 为占位符；调用会创建付费任务）：

```json
{
  "model": "MiniMax-H3",
  "content": [
    {"type": "text", "text": "固定镜头，人物轻轻转身，从首帧自然过渡到尾帧。"},
    {"type": "image_url", "image_url": {"url": "https://your-cdn.example/first.jpg"}, "role": "first_frame"},
    {"type": "image_url", "image_url": {"url": "https://your-cdn.example/last.jpg"}, "role": "last_frame"}
  ],
  "resolution": "768P",
  "duration": 4,
  "ratio": "adaptive"
}
```

**FACT-MINIMAX-VIDEO-002 — 输入边界。** 支持公网 URL、`mm_file://{file_id}`、对应 MIME 的 base64 data URI；文件上传未测。请求体 ≤64 MB，base64 增大约 33%，本地文件路径不能直接作为 URL 发给服务端。

| 素材 | 数量与时长 | 尺寸、格式、大小 |
| --- | --- | --- |
| 图片 | 首帧/尾帧各 ≤1；参考图 ≤9 | 宽高各 256–5760 px，宽/高 0.4–2.5；JPG/JPEG/PNG/WEBP/HEIC/HEIF；单文件 ≤30 MB |
| 参考视频 | ≤3 段，每段 2–15 s，合计 ≤15 s | 同上尺寸与比例；23.976–60 fps；MP4/MOV，H.264/H.265，内部音频 AAC/MP3；单文件 ≤50 MB |
| 参考音频 | ≤3 段，每段 2–15 s，合计 ≤15 s | WAV/MP3；单文件 ≤15 MB |

混合素材总数 ≤12（指南）；音视频的时长总上限分别校验。

**FACT-MINIMAX-VIDEO-003 — 共用任务生命周期与新任务。** 查询 `GET /v2/query/video_generation/{task_id}`，列表 `GET /v2/query/video_generation`，最近 7 天可查；列表支持 `page_num/page_size` 及 `filter.status/task_ids/model/task_type`。每约 10 秒轮询，客户端另设总 deadline；超时保留 task_id，恢复时查询而不是重新提交。

- `queued/running` 非终态；`succeeded/failed/cancelled` 终态。HTTP 请求错误使用真实 400/401/402/422/429/500 等状态与 `error`，任务失败还可能在 HTTP 200 的 `task.error.code/message` 中。两层都必须检查。
- 成功后按 `task_type/modality` 解析：generation、regeneration → `task.content.url`；h3_context_ir → `task.content.prompt`。后者没有视频 URL 不代表失败。
- 视频 URL 有时效，立即下载校验；文档称过期可重新查询获取，仍受任务 7 天窗口约束，不能把任务保留期当直链有效期。
- `DELETE /v2/video_generation/{id}`：queued → `action=cancelled`（无扣费，文档）；succeeded/failed → `action=deleted`；running/cancelled 返回错误。取消和删除不同，不能无条件重试 DELETE；也不能把本地停止轮询显示成上游取消。
- `callback_url` 验证需在 3 秒内原样返回 challenge，状态回调与查询响应同形；未做 webhook 实测。
- **Context-IR**：`POST /v2/h3_context_ir`，目前 model 为 `MiniMax-H3`，必填 `model/content/duration`（4–15 整数秒）；ratio 按纯文本/首尾帧/参考模式分别处理，返回 task_id；仅生成增强提示词，不自动创建视频。将结果用于后续生成是另一次请求与费用，须保留实际使用的最终 prompt。
- **再生成**：`POST /v2/video_regeneration`，model=`MiniMax-H3`、resolution=`2K`；两种输入必须且只能选一种：① `source_task_id`（需白名单、当前账号、成功且 7 天内的生成任务）；② `content` 原样保留源 768P 视频生成时全部输入（包括 IR 后最终 prompt），追加唯一 `type=video_url/role=base_video`。不是任意视频通用超分。
- base_video 模式源片必须有音轨、24 fps、宽高均为 32 的倍数、面积 589824–1032192 px、总帧数 107–362 且以 17 帧递增。再生成 text 上限 40000 字符，与创建上限不同。

**FACT-MINIMAX-VIDEO-004 — 用量不等于额外计费项。** 查询中的 `usage.total_seconds=input_seconds+output_seconds`；`input_image_count` 包含首帧、尾帧、参考图；`input_audio_seconds` 为音频时长取和四舍五入。视频的 token 字段是素材/视频用量折算，**不能把同一视频的秒数费用与折算 token 费用重复相加**。Context-IR 才按实际输入/输出 tokens 单独计费。原始 usage 完整保存，价格匹配 task_type、model、resolution 与时间快照。

价格快照（人民币，2026-10-27，使用前复核）：

| 生成模型/档位 | 输出元/秒 | 输入视频元/秒 | 超额图片元/张 | 每任务免费图片 |
| --- | --- | --- | --- | --- |
| H3 768P / 2K | 0.50 / 0.80 | 0.50 / 0.80 | 0.20 | 5 |
| Highspeed 768P | 0.40 | 0.40 | 0.20 | 5 |
| Lite 480P / 768P | 0.16 / 0.26 | 0.16 / 0.26 | 0.13 | 5 |
| Max 480P / 768P | 0.33 / 0.50 | 0.37 / 0.97 | 0.50 | 2 |

音频输入免费；图片只对 `max(0, input_image_count - 免费张数)` 计费。Context-IR 输入/输出为 ¥5.80/¥23.00 每百万 tokens。再生成输出/输入视频 ¥0.30/秒、超额图 ¥0.15/张（前5张免费），原任务输入素材重新计费，费用在原生成之外；不要仅据“升到2K”推断总价或 base_video 的结算方式。Hailuo 视频资源包当前不适用于 H3；标价和推算均不是账单实扣证明。

**历史实测范围**（2026-08-29，`api.minimaxi.com`，MiniMax-H3，来源 Joycai；原始日志位置待补）：首尾帧创建→轮询→下载 2K 跑通；平铺媒体 url 被收下却忽略图片（坑113）；带媒体 ratio=adaptive 接受，text 必须存在；旧矩阵记录缺 resolution/duration 返回 400，仍限当时 H3 组合。旧计费推断已移入[结论历史](../../llm-api-integration/references/conclusion-history.md#minimax-h3-billing-history)。

**FACT-MINIMAX-VIDEO-005 — 本轮首尾帧成功样本。**【实测 2026-10-27，官方 `api.minimax.cn`，MiniMax-H3，生成提交 1 次、成功 1 次】将用户提供的两张 1696×2528 JPEG 作为嵌套 data URI 的 first_frame/last_frame，与非空文本、`duration:4/resolution:"768P"/ratio:"adaptive"` 一起提交：HTTP 200 返回 task_id；轮询经过 running → succeeded，最后无认证头下载 MP4。脱敏请求、终态原始字段、图片/视频哈希和官方页面哈希见 [实测证据](minimax-h3-evidence.json)。

- `task.usage`：`total_seconds:4/input_seconds:0/output_seconds:4/input_image_count:2`；同时返回 `total_tokens:156236/prompt_tokens:26040/completion_tokens:130196`。计费解释见 004。
- 返回 `task.resolution:"768P"/duration:4/ratio:"adaptive"`。本样本 ratio 没有回显数值比例，不能仅从该字段获得真实尺寸；需读取视频元数据。
- 下载 1,362,782 bytes，Content-Type=`video/mp4`，ftyp 检查通过；ffprobe：H.264、768×1152、24 fps、107 帧，AAC 音轨，容器时长 **4.458333 s**。API 时长与媒体播放时长不是同一量；计费保存原始 output_seconds，不擅自用容器时长改账。
- 抽查首帧/中间帧/尾帧：首尾人物姿态对应两张输入，中间出现转身过渡。仅三个采样帧，不能保证整段动作一致性或音频质量。
- 按当日标价估算 **¥2.00**（4×0.50，2 张图在免费5张内）；**实际扣费未核实**。未测其他型号、参考模式、取消、webhook、Context-IR 与再生成；待核实项见 OQ-041。

## 3. 横切不变量（每家都适用，漏一条就是一类静默失败）

1. **失败装在 HTTP 200 里。** `task_status: FAILED` + 错误码嵌在 body
   （千问在 `output.code/message`，MiniMax 在 `task.error`）。HTTP 成功不能替代任务状态检查。先处理 HTTP 错误，再检查任务状态；保留结构化 code，避免丢失审核等失败原因。
2. **状态词表逐家归一化，未知状态当"仍在跑"处理有上限。** 词表各不相同且
   随时增补；未知值先当 in-progress 容忍，但要受总 deadline 罩住——否则
   一个新终态（如千问的 `UNKNOWN`、xAI 的 `expired`）会让轮询永不停止。
   已知终态（CANCELED/expired/UNKNOWN）必须显式列入"抛错"分支。
3. **过期 task_id ≠ 失败任务。** MiniMax 7 天清记录、千问 task_id 24h——
   过期后查到的是"查无此任务"，必须报成独立的明确错误（「任务已过期」），
   落进重试循环或报成 FAILED 都是误导。
4. **结果 URL 当场下载。** 直链一律短时效（千问明文 24h，MiniMax 只说
   "有时效"）；下载 GET 通常**不带** API 认证头（OSS/CDN 签名在 URL 里，
   多带无益甚至有害；Sora 的 `/content` 是例外——它是 API 端点，要带）。
   下载校验 content-type + magic bytes，规则同[image-generation](image-generation.md) §6。
5. **取消要分两层语义。** 本地放弃轮询 ≠ 上游停止计费。有取消端点的
   （MiniMax）作为可选能力接上：用户取消时先试上游取消（仅排队态有效），
   失败时明确告知上游仍可能继续执行，再停止本地轮询；没有取消端点的家，UI 文案别承诺"已取消"。
6. **计费相关的默认值显式下发。** `audio: true`（千问）、`n: 4`（wan 图片，
   见 [image-generation](image-generation.md)）这类服务端默认直接乘在账单上——不吃默认，全部显式发。
7. **必填参数由模型能力表声明。** MiniMax H3 缺 resolution/duration 的 400 为历史观测；当前各型号按 §2.1 校验并显式发送，adapter 不猜测服务端默认。
8. **usage 多种计量并存时先辨明是否独立收费**，只相加独立计费项；MiniMax H3 视频 token 是折算展示，不与秒数重复收费（FACT-MINIMAX-VIDEO-004）。例外是**上游直接报钱**的面（[image-generation](image-generation.md) §7 的 `cost_in_usd_ticks`）：报价含全部（含参考图），替换不叠加。
   xAI 视频面也报它，但**只在 done 的轮询回包里**【实测 2026-09-22】——提交时按请求的秒数先记一行，终态再用报价改写；
   只改写秒数的结算会把参考图那 $0.01/张 漏掉（坑 129）。

## 4. 与中继的关系

中继（New API 等）把百家视频收敛到 OpenAI 式 `/v1/videos`（sora、
grok-imagine、wan2.5、kling、hailuo…同一张脸）。**同一个模型 id 在官方与
中继上走不同协议**——这正是[provider-layering](../../llm-api-integration/references/provider-layering.md) §8 的「协议选择按 L2 菜单解析」：官方
供应商行的 video 槽位指向私有协议，中继行指向 openai-videos，模型 id 不变。
按 model-id 硬编码路由的实现会在其中一边坏掉。

---

## 本篇检查清单

- [ ] submit/poll 分离，task_id 暴露给调用方持久化；失败以抛错送达。
- [ ] 首帧/尾帧/参考素材用 role 标注的统一形状，adapter 内转各家拼写。
- [ ] 分别检查 HTTP 错误和任务失败，保留结构化 code。
- [ ] 每家状态词表显式归一化；未知状态容忍但受总 deadline 罩住；已知终态
      （含 CANCELED/expired/UNKNOWN 类）全部在抛错分支里。
- [ ] 「任务已过期/查无此任务」是独立错误，不重试、不报成 FAILED。
- [ ] 结果 URL 当场下载；认证头按端点性质（签名直链不带，API 端点带）。
- [ ] 取消分两层：可选的上游取消（仅排队态）+ 本地放弃；文案不超售。
- [ ] 计费相关默认值全部显式下发；必填无默认参数有 L3 声明的缺省。
- [ ] 同一模型 id 在官方/中继两侧路由不同，经 L2 菜单解析，无 model-id 硬编码。
