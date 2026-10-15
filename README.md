# Joycai-agent-skill

Joycai 自用的 Claude 插件市场（marketplace）。架构相关的四个 skill 合在 `ai-agent-architecture` 插件中，按任务选用；`dev-workflow` 和 `reference-image-studio` 是独立插件。

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
| `ai-agent-architecture` | `ai-agent-architecture` | 平台 × 协议 × 模型 的 LLM 端点事实矩阵、供应商分层架构、知识吸收协议 |
| `ai-agent-architecture` | `agent-runtime-architecture` | agent 层架构：工具循环、审批与写安全、子代理、上下文压缩与会话持久化 |
| `ai-agent-architecture` | `channel-route-model` | LLM 接入配置三层架构：渠道 → 线路 → 模型 |
| `ai-agent-architecture` | `llm-billing-model` | LLM / 出图 / 视频 API 计量与计费设计标准 |
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

`ai-agent-architecture` 从 3.0.0 起包含四个架构 skill。已有用户更新市场后，将该插件更新到 3.0.0 或更高版本；原先单独安装的 `agent-runtime-architecture`、`channel-route-model`、`llm-billing-model` 插件请卸载，避免重复加载。`dev-workflow` 保持独立。

四个 skill 的名称不变，显式调用统一使用 `ai-agent-architecture` 插件前缀：

```text
/ai-agent-architecture:ai-agent-architecture
/ai-agent-architecture:agent-runtime-architecture
/ai-agent-architecture:channel-route-model
/ai-agent-architecture:llm-billing-model
```

开发工作流仍使用 `/dev-workflow:dev-workflow`。
