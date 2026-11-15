# Joycai-agent-skill

Joycai 自用的 **Codex / Claude 双平台插件市场**。三个插件共用 skills、脚本和参考资料，分别提供两端的市场与插件清单。当前都是 skills 插件，不附带 MCP 服务；图片生成、设计工具和子代理能力由使用它的宿主环境提供。

## Codex：安装

在支持插件的 Codex CLI 中添加市场，再按需安装（可先运行 `codex plugin --help` 检查本机支持）：

```bash
codex plugin marketplace add Joycai/Joycai-agent-skill
codex plugin add ai-agent-architecture@joycai-agent-skill
codex plugin add dev-workflow@joycai-agent-skill
codex plugin add reference-image-studio@joycai-agent-skill
```

本地开发时，先进入本仓库根目录，用本地来源替代上面的 GitHub 来源：

```bash
codex plugin marketplace add .
codex plugin marketplace list
```

桌面端可打开插件目录，选择 **Joycai Agent Skills** 市场，按需安装并启用。添加本地市场后重启桌面端，在新聊天中检查技能是否可选。若 CLI 没有 `plugin add` 子命令，使用桌面端安装，或升级支持插件管理的客户端。

Codex 的市场入口是 `.agents/plugins/marketplace.json`，插件入口是各插件的 `.codex-plugin/plugin.json`（官方仍支持的兼容格式）。原有 Claude 格式也能被部分 Codex 客户端识别；本仓库现在提供独立的 Codex 清单。同一个市场请选择 GitHub 或本地来源之一。

## Claude Code：安装

```bash
claude plugin marketplace add Joycai/Joycai-agent-skill
claude plugin install ai-agent-architecture@joycai-agent-skill
claude plugin install dev-workflow@joycai-agent-skill
claude plugin install reference-image-studio@joycai-agent-skill
```

本地开发时在仓库根目录运行 `claude plugin marketplace add .`，替代 GitHub 来源。也可在 Claude Code 会话中打开 `/plugin` 面板添加市场并安装；会话内命令为 `/plugin marketplace add …`、`/plugin install …`。Claude 桌面端的插件入口随产品模式而异，以上命令用于 Claude Code。

## 使用

- **Codex**：在技能选择器中选择目标技能，或明确说“使用 llm-api-integration 检查这个 API 接入”“使用 dev-workflow 实现这个需求”。选择器展示的完整名称以实际加载结果为准。
- **Claude Code**：使用 `/插件名:技能名`，例如 `/ai-agent-architecture:llm-api-integration`、`/dev-workflow:dev-workflow`、`/reference-image-studio:reference-image-workspace`。
- 两端都可以用自然语言描述任务，让宿主按 skill 描述选择。插件需要先安装、启用并在当前会话中加载。

`dev-workflow` 的新任务文件使用 `.agent-tasks/<slug>/`，旧的 `.claude/tasks/<slug>/` 任务继续原位恢复。Claude 的 sonnet / opus 建议不用于 Codex，Codex 默认继承当前模型。没有子代理时分阶段自行 review；没有设计工具时产出 UI 规格或本地原型。图片创作需宿主提供实际可用的图片生成 / 编辑工具，安装 skills 不会自动配置这些服务。

## 更新与本地调试

上述 GitHub 安装命令默认读取仓库默认分支，PR 合并后才能获取本次修改。合并前请用本地目录测试；Codex 也可用 `codex plugin marketplace add Joycai/Joycai-agent-skill --ref codex/dual-platform-plugins` 指定已推送的开发分支。

```bash
# Codex：刷新市场，再按需重新安装目标插件
codex plugin marketplace upgrade joycai-agent-skill
codex plugin add ai-agent-architecture@joycai-agent-skill

# Claude Code：刷新市场与目标插件
claude plugin marketplace update joycai-agent-skill
claude plugin update ai-agent-architecture@joycai-agent-skill
```

其余插件同理。Codex 使用安装缓存，改源码后应刷新 / 重新安装并新开聊天；桌面端必要时重启。Claude Code 更新后执行 `/reload-plugins` 或重开会话。本地直接调试单个 Claude 插件也可用 `claude --plugin-dir ./plugins/dev-workflow`。

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

## 目录与维护

```text
.claude-plugin/marketplace.json      Claude 市场清单（维护源）
.agents/plugins/marketplace.json     Codex 市场清单（生成）
plugins/<plugin>/
  .claude-plugin/plugin.json         插件元数据（维护源）
  .codex-plugin/plugin.json          Codex 插件清单（生成）
  skills/<skill>/SKILL.md            两端共用入口
  skills/<skill>/references/         按需加载的资料
scripts/sync-plugin-manifests.ps1    同步与检查双平台清单
```

新增 skill 放进对应插件的 `skills/<skill>/`。新增独立插件时，先添加 Claude 插件清单与市场条目，再生成 Codex 清单。Codex 市场的 `source.path` 相对仓库根目录，而非 `.agents/plugins/` 目录。不要手改生成的 JSON。

插件版本在 Claude 市场条目和插件清单中同步递增，再运行同步脚本；skill 的 `metadata.version` 仅在内容改变时递增。本次插件版本：架构 4.0.9、工作流 1.1.0、参考图 1.4.3。

需要 PowerShell 7（Windows / macOS / Linux 均可安装）：

```powershell
pwsh -File scripts/sync-plugin-manifests.ps1
pwsh -File scripts/sync-plugin-manifests.ps1 -Check
claude plugin validate .
claude plugin validate plugins/ai-agent-architecture
claude plugin validate plugins/dev-workflow
claude plugin validate plugins/reference-image-studio
```

架构资料的内部链接与结构检查：`python3 plugins/ai-agent-architecture/scripts/validate_structure.py`。清单检查不等于两端实际模型行为测试；安装后应在新会话中分别调用目标 skill 验证。

格式与安装依据：[OpenAI 插件打包文档](https://developers.openai.com/plugins/build/plugins)、[Claude Code 插件文档](https://code.claude.com/docs/en/plugins)。CLI 子命令以本机 `--help` 为准。

## 从旧版迁移

`ai-agent-architecture` 4.0.0 包含五个 skill：新增媒体 API 接入，重命名聊天接入、供应商配置与成本核算入口。插件安装名保持不变，旧 skill 调用名需更新，见 [插件迁移说明](plugins/ai-agent-architecture/README.md#从-3x-迁移) 与 [文件迁移清单](plugins/ai-agent-architecture/MIGRATION.md)。

若从 3.0.0 之前升级，原先独立安装的 `agent-runtime-architecture`、`channel-route-model`、`llm-billing-model` 插件应卸载，避免重复加载。`dev-workflow` 保持独立，调用仍为 `/dev-workflow:dev-workflow`。
