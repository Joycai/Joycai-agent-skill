# 参考图工作室

一个插件，六个 skill，共用工作区内的可信参考索引。

## 安装与调用

添加本仓库的 marketplace 后安装：

```bash
claude plugin install reference-image-studio@joycai-agent-skill
```

显式调用：

```text
/reference-image-studio:reference-image-workspace
/reference-image-studio:reference-image-dashboard
/reference-image-studio:reference-image-repair
/reference-image-studio:reference-image-generate
/reference-image-studio:reference-image-cosplay
/reference-image-studio:reference-image-cosplay-photo
```

| Skill | 用途 |
| --- | --- |
| `reference-image-workspace` | 初始化标准目录与 Dashboard，更新参考图片、文字描述和可信设定 |
| `reference-image-dashboard` | 浏览可信参考、逐次任务输入/输出/prompt 与保留结果，缩略图筛选与并排对比 |
| `reference-image-repair` | 提出具体修改计划，经用户确认或调整后修复成图 |
| `reference-image-generate` | 根据可信设定与样本，将文字描述或草图生成新图片 |
| `reference-image-cosplay` | 先审查并确认材质、结构与展示方案，再生成真实 cosplay 服装人台图 |
| `reference-image-cosplay-photo` | 按服装设计图或角色原画生成真人 cosplay 照片，模特照片可选 |

使用示例：

- 使用 reference-image-workspace 初始化当前工作区，用于参考驱动的图片创作。
- 使用 reference-image-workspace，将这些图片和文字说明更新到参考索引。
- 使用 reference-image-repair，先指出这张成图需要改哪些地方，等我确认后再修。
- 使用 reference-image-generate，根据仓库设定画一张角色在雨中奔跑的图片。
- 使用 reference-image-generate，保留这张草图的构图和动作，按仓库标准完成图片。
- 使用 reference-image-cosplay，根据这些角色原画和饰品特写，先提出真实材质及人台展示方案，确认后生成正侧背与细节图。
- 使用 reference-image-cosplay，在完整造型之外补充移除外裙的内层连体衣展示；也可以仅生成内层服装图。
- 使用 reference-image-cosplay-photo，按服装 V1 和这组模特面部照片生成一张全身漫展照，配饰和假发保持一致。
- 使用 reference-image-cosplay-photo，没有服装设计图，直接按这张角色原画生成清晨花园中的真人 cosplay 摄影，不指定模特。

使用 reference-image-cosplay-photo，根据已确认的 cosplay 设计图生成漫展、棚拍或户外真人照片；可提供模特四宫格锁定面部，也可不指定模特。没有预先设计图时可直接从角色原画转译成照片，不强制先做人台图。支持按本次场景表现天气与材质，并核对工具实际输出尺寸；照片生成默认直接执行已明确的请求。

Cosplay 人台展示默认包含全套服装、假发与配饰的正侧背视图及必要特写；内层展示为可选项。先审查参考并给出结构、材质、缺失依据与出图清单，用户补充和确认后再生成。角色原设定与本次真实化方案分开记录，缺少背面或隐藏结构时不将推断当作事实。

插件提供工作流程与初始化脚本，实际出图使用所在环境已有的图像能力。没有捆绑角色素材、供应商账户或密钥。生成图不会自动成为可信样本。

## 工作区初始化

需要 Python 3.9+，无第三方 Python 依赖。在本仓库根目录运行：

```bash
python3 plugins/reference-image-studio/skills/reference-image-workspace/scripts/init_workspace.py /path/to/workspace
```

脚本创建 `references/`、`inputs/`、`tasks/`、`retained/`、`.studio/`、`dashboard/`，兼容保留 `edits/`、`generations/`、`design_notes/`。只写入缺少的规则、索引和项目登记表，构建可离线打开的 `dashboard/index.html`；页面和缩略图可重建。已有项目 `AGENTS.md` 时，参考规则另存为 `REFERENCE_WORKSPACE.md`，由 skill 阅读后合并或链接；脚本不会自动修改原项目规则。重复运行保留已有素材和登记表，并刷新 Dashboard 快照。

初始化不是生成或修复的必要前置条件。用户本次提供的明确设定和参考也可直接使用；纯文字依据足够时无需补交图片。独立修复任务默认先确认修改清单；已授权范围内的纠偏无需重复确认。生成和修复均保留原件，输出按批次另存。

## 插件结构

```text
.claude-plugin/plugin.json
skills/
├── reference-image-workspace/   # 入口、初始化脚本与模板
├── reference-image-dashboard/   # 仓库结构、逐次记录、离线浏览与对比
├── reference-image-repair/      # 分析、计划、修复与核对
├── reference-image-generate/    # 文字或草图生成与核对
├── reference-image-cosplay/     # 角色服装真实化、人台展示与分层核对
└── reference-image-cosplay-photo/ # 真人穿着摄影、可选面部参考与场景材质核对
```

按本仓库的 Claude marketplace 格式打包，六个 skill 一起安装，保留相互引用。各 skill 的 `agents/openai.yaml` 是附带的界面元数据，不代表提供了独立的 Codex 插件安装包。

验证清单：在仓库根目录运行 `claude plugin validate .` 和 `claude plugin validate plugins/reference-image-studio`。

## 项目 Dashboard

初始化即提供本地 Dashboard：可信参考及限定说明、每次任务的输入/职责/实际传图、模型参数、prompt、输出和检查，以及用户明确保留的结果与来源链。失败尝试保留记录；手工新增但未登记的图片单列，不自动成为标准。

页面支持搜索、模型筛选、原图放大、2–4 张并排对比和复制选择编号。网页勾选仅供挑选，正式保留或更新参考由用户在对话中确认后登记。所有素材留在项目内，无账户、网络服务或 CDN 依赖。

各创作 skill 在每次产出/失败后更新 task.json 并构建页面，已打开页面刷新即可查看。页面是快照，不实时监控磁盘。已有项目保持原目录，按记录协议接入；未知的历史 prompt 或输入如实留空。完整目录、JSON 和命令见 [记录协议](skills/reference-image-dashboard/references/workspace-contract.md)。

```bash
python3 plugins/reference-image-studio/skills/reference-image-dashboard/scripts/dashboard.py build /path/to/workspace
```

Dashboard 支持按自然语言要求清理版本：默认原位归档、检查任务与参考引用、自动更新页面，保留完整输入输出和 prompt 链路；可恢复，不释放磁盘空间。物理迁移或删除须用户明确指定。见 [清理与归档流程](skills/reference-image-dashboard/references/cleanup-and-archive.md)。
