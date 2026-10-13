# 参考图工作室

一个插件，四个 skill，共用工作区内的可信参考索引。

## 安装与调用

添加本仓库的 marketplace 后安装：

```bash
claude plugin install reference-image-studio@joycai-agent-skill
```

显式调用：

```text
/reference-image-studio:reference-image-workspace
/reference-image-studio:reference-image-repair
/reference-image-studio:reference-image-generate
/reference-image-studio:reference-image-cosplay
```

| Skill | 用途 |
| --- | --- |
| `reference-image-workspace` | 初始化工作区，更新参考图片、文字描述和可信设定 |
| `reference-image-repair` | 提出具体修改计划，经用户确认或调整后修复成图 |
| `reference-image-generate` | 根据可信设定与样本，将文字描述或草图生成新图片 |
| `reference-image-cosplay` | 先审查并确认材质、结构与展示方案，再生成真实 cosplay 服装人台图 |

使用示例：

- 使用 reference-image-workspace 初始化当前工作区，用于参考驱动的图片创作。
- 使用 reference-image-workspace，将这些图片和文字说明更新到参考索引。
- 使用 reference-image-repair，先指出这张成图需要改哪些地方，等我确认后再修。
- 使用 reference-image-generate，根据仓库设定画一张角色在雨中奔跑的图片。
- 使用 reference-image-generate，保留这张草图的构图和动作，按仓库标准完成图片。
- 使用 reference-image-cosplay，根据这些角色原画和饰品特写，先提出真实材质及人台展示方案，确认后生成正侧背与细节图。
- 使用 reference-image-cosplay，在完整造型之外补充移除外裙的内层连体衣展示；也可以仅生成内层服装图。

Cosplay 展示默认包含全套服装、假发与配饰的正侧背视图及必要特写；内层展示为可选项。先审查参考并给出结构、材质、缺失依据与出图清单，用户补充和确认后再生成。角色原设定与本次真实化方案分开记录，缺少背面或隐藏结构时不将推断当作事实。

插件提供工作流程与初始化脚本，实际出图使用所在环境已有的图像能力。没有捆绑角色素材、供应商账户或密钥。生成图不会自动成为可信样本。

## 工作区初始化

需要 Python 3，无第三方 Python 依赖。在本仓库根目录运行：

```bash
python3 plugins/reference-image-studio/skills/reference-image-workspace/scripts/init_workspace.py /path/to/workspace
```

脚本创建 `references/`、`inputs/`、`edits/`、`generations/`、`design_notes/`，并仅写入缺少的规则和索引文件。已有项目 `AGENTS.md` 时，参考规则另存为 `REFERENCE_WORKSPACE.md`，由 skill 阅读后合并或链接；脚本不会自动修改原项目规则。重复运行保留已有内容。

初始化不是生成或修复的必要前置条件。用户本次提供的明确设定和参考也可直接使用；纯文字依据足够时无需补交图片。独立修复任务默认先确认修改清单；已授权范围内的纠偏无需重复确认。生成和修复均保留原件，输出按批次另存。

## 插件结构

```text
.claude-plugin/plugin.json
skills/
├── reference-image-workspace/   # 入口、初始化脚本与模板
├── reference-image-repair/      # 分析、计划、修复与核对
├── reference-image-generate/    # 文字或草图生成与核对
└── reference-image-cosplay/     # 角色服装真实化、人台展示与分层核对
```

按本仓库的 Claude marketplace 格式打包，四个 skill 一起安装，保留相互引用。各 skill 的 `agents/openai.yaml` 是附带的界面元数据，不代表提供了独立的 Codex 插件安装包。

验证清单：在仓库根目录运行 `claude plugin validate .` 和 `claude plugin validate plugins/reference-image-studio`。
