# Joycai-agent-skill

Joycai 自用的 Claude 插件市场（marketplace）。架构相关的五个 skill 合在 `ai-agent-architecture` 插件中，按任务选用；`dev-workflow` 和 `reference-image-studio` 是独立插件。

## 添加市场

Claude Code / Claude 桌面端的 `/plugin` 面板，或命令行：

```bash
# 本地目录
claude plugin marketplace add /Users/caizhengxu/github/Joycai-agent-skill
# 或推到 GitHub 后
claude plugin marketplace add Joycai/Joycai-agent-skill
```

## 安装插件

```bash
claude plugin install ai-agent-architecture@joycai-agent-skill
claude plugin install dev-workflow@joycai-agent-skill
claude plugin install reference-image-studio@joycai-agent-skill
```

会话内 `/plugin marketplace add …`、`/plugin install …` 同理。本地目录添加的市场，改完文件后 `/reload-plugins` 或重开会话即生效。

## 插件列表

| 插件 | skill | 用途 |
| --- | --- | --- |
| `ai-agent-architecture` | `llm-api-integration` | 聊天 API 协议、能力事实、接入审查与排错 |
| `ai-agent-architecture` | `ai-media-api-integration` | 图片、视频、ASR API 的上传、异步任务与产物处理 |
| `ai-agent-architecture` | `agent-runtime-architecture` | Agent 工具循环、执行权限、子代理、上下文与会话 |
| `ai-agent-architecture` | `llm-provider-config` | 供应商、凭据、线路与模型配置及迁移 |
| `ai-agent-architecture` | `ai-usage-accounting` | 用量记录、价格快照、成本核算与结算 |
| `dev-workflow` | `dev-workflow` | 标准化的需求实现 / bug 修复流程（定位 → 设计 → 计划 → 分片提交 → review → PR） |
| `reference-image-studio` | `reference-image-workspace` | 初始化参考创作工作区与 Dashboard，维护图片、文字设定、可信来源与适用范围 |
| `reference-image-studio` | `reference-image-dashboard` | 浏览可信参考、任务逐次输入输出与 prompt、保留结果，缩略图筛选与并排对比 |
| `reference-image-studio` | `reference-image-repair` | 依据可信参考分析成图，默认确认具体修改计划后执行修复 |
| `reference-image-studio` | `reference-image-generate` | 依据可信设定与样本，将文字或草图生成新图片 |
| `reference-image-studio` | `reference-image-cosplay` | 审查角色参考并确认结构与材质，生成真实服装人台三视图、特写及可选内层展示 |
| `reference-image-studio` | `reference-image-cosplay-photo` | 按服装设计图或角色原画生成真人 cosplay 照片，可选模特面部参考、场景与天气材质 |

参考图插件的调用方式与工作区初始化说明见 [reference-image-studio](plugins/reference-image-studio/README.md)。

## 目录约定

```
.claude-plugin/marketplace.json     市场清单（name / owner / plugins[]）
plugins/<plugin>/
  .claude-plugin/plugin.json        插件清单（name 必须与市场条目一致）
  skills/<skill>/SKILL.md           skill 入口
  skills/<skill>/references/        按需加载的资料
```

给已有插件新增 skill：放进该插件的 `skills/<skill>/`，写 `SKILL.md`，按需添加 `references/`。只有新增独立插件时，才新建插件目录与 `plugin.json`，并在 `marketplace.json` 的 `plugins` 数组加一项（`source` 用相对市场根的路径，不能含 `..`）。

插件版本在市场清单与插件清单中保持一致；各 skill 的 `metadata.version` 独立记录内容版本，纯目录迁移不改变 skill 版本。

校验：`claude plugin validate .`，以及对每个 `plugins/<plugin>` 运行 `claude plugin validate plugins/<plugin>`。

## 从旧版迁移

`ai-agent-architecture` 4.0.0 包含五个 skill：新增媒体 API 接入，重命名聊天接入、供应商配置与成本核算入口。插件安装名保持不变，旧 skill 调用名需更新，见 [插件迁移说明](plugins/ai-agent-architecture/README.md#从-3x-迁移) 与 [文件迁移清单](plugins/ai-agent-architecture/MIGRATION.md)。

若从 3.0.0 之前升级，原先独立安装的 `agent-runtime-architecture`、`channel-route-model`、`llm-billing-model` 插件应卸载，避免重复加载。`dev-workflow` 保持独立，调用仍为 `/dev-workflow:dev-workflow`。
