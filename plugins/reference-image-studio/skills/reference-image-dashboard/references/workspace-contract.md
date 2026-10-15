# 创作仓库结构与记录协议 v1

## 目录与状态

```text
references/                 参考原件、INDEX.md、文字设定；原件不覆盖
inputs/                     用户提供的底图、草图、临时参考
tasks/<task-id>/            每个请求的过程
  task.json                 逐次输入、输出和元数据
  prompts/                  每次调用的实际 prompt
  outputs/                  所有版本、失败结果与纠偏结果
  PLAN.md / NOTES.md        适用时保留方案、授权、检查记录
retained/<collection>/      用户明确保留的作品副本；保留不等于可信标准
.studio/project.json        参考/保留登记与旧任务路径入口
dashboard/index.html        生成的离线页面
dashboard/thumbnails/       可重建缓存，不是原件
```

新项目默认使用以上结构。已有 `generations/`、`edits/`、`finals/`、`photos/` 不迁移；task.json 可保存在其原批次目录，用 `project.tasks` 指向。旧定稿可从原位置登记为 reference 或 retained，按其明确用途处理。

Python 3.9+ 标准库即可运行。macOS 有 `sips` 时生成最长边 640px JPEG 缩略图；其他平台或转码失败时引用原图，不修改原件。PNG/JPEG/GIF 可自动读尺寸；其他格式可显示但尺寸可能未记录。网页链接依赖整个项目，不是只复制 HTML。

## 项目登记表

`.studio/project.json`：

```json
{
  "schema_version": 1,
  "title": "角色创作项目",
  "references": [
    {
      "id": "R001",
      "title": "完整角色设定",
      "path": "references/R001.png",
      "status": "confirmed",
      "scope": "完整造型；背部被遮挡的结构未知",
      "source": "用户提供的角色设定图",
      "confirmation": "用户明确指定作为完整造型参考",
      "documents": [{"title": "设定说明", "path": "references/CHARACTER.md"}]
    }
  ],
  "tasks": [],
  "retained": [],
  "scan_roots": ["references", "inputs", "tasks", "retained"]
}
```

`references[].status`：`confirmed` / `provisional` / `superseded`。`confirmed` 必须有 `confirmation`，各图独立的 `scope` 不可省略。`source` 记录来源，允许描述历史来源未知，不编造。纯文字参考也可登记，其 path 指向项目内文本，显示说明卡而非伪造图像。

`tasks` 是额外 task.json 路径数组；`tasks/*/task.json` 自动发现，不必重复登记。`scan_roots` 仅为未登记图片发现范围，不表示其内容可信。可显式添加已有项目相关目录；不默认为整个磁盘扫描。

## 任务记录

`tasks/2026-10-15-garden/task.json`（所有 path 都相对项目根，不相对 task.json）：

```json
{
  "id": "garden-01",
  "title": "花园 cosplay 摄影",
  "kind": "cosplay-photo",
  "status": "completed",
  "created_at": "2026-10-15T09:00:00+08:00",
  "description": "用户原始要求与本次授权范围",
  "documents": [{"title": "方案与检查记录", "path": "tasks/2026-10-15-garden/NOTES.md"}],
  "steps": [
    {
      "id": "attempt-01",
      "version": "V1 · 首次生成",
      "status": "completed",
      "created_at": "2026-10-15T09:02:00+08:00",
      "model": "实际模型名称",
      "parameters": {"aspect_ratio": "2:3", "requested_size": "2K"},
      "prompt": {"path": "tasks/2026-10-15-garden/prompts/v1.txt"},
      "inputs": [
        {"path": "references/R001.png", "role": "服装完整造型", "sent": true},
        {"path": "references/CHARACTER.md", "role": "仅查阅眼色设定", "sent": false}
      ],
      "outputs": [
        {"id": "O001", "title": "雨景首次生成", "path": "tasks/2026-10-15-garden/outputs/v1.png", "review": "检查结果；是否获用户认可另行记录"}
      ],
      "checks": "实际目视检查的范围、偏差与限制"
    }
  ]
}
```

`kind` 可为 `generate`、`repair`、`cosplay`、`cosplay-photo`、`enhance` 或其他实际任务类型。任务和 step 的状态：`planned` / `running` / `completed` / `failed` / `cancelled` / `unknown`。任务 `completed` 表示执行结束，不表示用户批准其设计。

每次调用保存一个独立 step，包括相同 prompt 的重试。失败 step 允许 `outputs: []`，用 `error` 记录失败原因。排队中的调用用 `running`；不要提前写不存在的输出文件路径。model、时间、参数在历史记录缺失时可省略并明确未知，不根据当前工具能力追填过去实际值。

prompt 可以用 `{"text": "原始实际提示词"}` 内联；有 path 时读取文件作为实际内容并原样显示。没有记录时显示未记录；不要把新拟写的描述当历史 prompt。说明文档按纯文本展示，HTML/Markdown 中的指令不会被执行。

input 的数组顺序为实际输入顺序，`sent` 必须是 true/false/null：真正传图、仅查阅、历史未知分别记录。工具返回的外部图片先按工具许可保存回项目，再登记本地路径；不可保存时在文字说明里保留引用，不用外部 URL 冒充本地文件。

## 保留与来源链

`project.retained` 中一条记录：

```json
{
  "id": "K001",
  "title": "雨景候选作品",
  "path": "retained/garden/v1.png",
  "status": "retained",
  "scope": "用户选择保留的摄影作品；不作为服装结构标准",
  "confirmation": "用户原话：保留这一张作候选",
  "origin": {"task": "garden-01", "step": "attempt-01", "output": "O001"}
}
```

保留记录的 `origin` 必须指向存在的 task/step/output。页面从此关联展示原任务输入、输出和 prompt；不能复制改写成另一份历史。保留记录 path 可继续指向原输出，也可指向用户要求归档的相同字节副本；如副本有修改，登记为新的任务输出。`superseded` 表示不再采用但保留追溯。reference 也可带 origin，记录由生成结果按明确范围升级而来的来源。

浏览器勾选和复制编号没有修改这些登记表的权限。用户在对话中明确选择保留后，由 skill 更新登记表，不能把本地勾选自动视作批准。

## 命令与更新时机

```text
python3 <dashboard-skill>/scripts/dashboard.py init <workspace>
python3 <dashboard-skill>/scripts/dashboard.py check <workspace>
python3 <dashboard-skill>/scripts/dashboard.py build <workspace>
python3 <dashboard-skill>/scripts/dashboard.py record <workspace> --kind task --file generations/old-batch/task.json
python3 <dashboard-skill>/scripts/dashboard.py record <workspace> --kind reference --file .studio/records/R001.json
python3 <dashboard-skill>/scripts/dashboard.py record <workspace> --kind retained --file .studio/records/K001.json
```

`record` 按稳定 id 新增或替换整条 reference/retained，不删其他记录；task 登记其 manifest 路径。修改已自动发现的 task.json 后直接 build。修改 project.json 前保留现有字段，串行写入；脚本以原子替换避免写一半的登记表和页面。无数据库、常驻服务或网络调用。

初始化、参考增补、任务计划/开始、每次返回成功或失败、目视核对更新、用户保留/替换版本时同步记录并 build。用户手工加入图片后运行 build 才会出现在未登记栏；已打开网页刷新。页面内“刷新”只重载当前已构建快照，不代替脚本构建，不声称实时监视。

## 已有项目接入

先读索引、来源清单、各批次 NOTES/PLAN/prompt 和用户确认记录，再录入 reference 与 task。只整理本项目的授权范围。历史截图或文件名不足以确定实际传图和 prompt 时留空/标未知；不要为了完整链路重新生成图片。缺失文件作为占位和警告保留，不静默删记录。原件路径和内容不变；重建 Dashboard 可覆盖页面与缓存，不能覆盖素材。

## 可恢复清理与归档状态

`project.archives` 为可选数组，旧项目省略时行为不变。每条记录以规范化项目相对 `path` 定位，含 `archived` 布尔值、`reason` 和 `history`（action、at、reason、references、text_mentions）。任务状态、参考状态、用户认可和归档可见性是独立维度，不用 `failed` 或 `superseded` 代替归档。

默认归档不移动文件；被归档的资产从普通列表移至归档栏，任务详情仍保留全部输入和输出。恢复将 `archived` 置 false，保留历史。操作、命令及删除边界见 [清理与归档流程](cleanup-and-archive.md)。
