# Joycai-agent-skill

Joycai 自用的 Claude 插件市场（marketplace）。每个 skill 一个插件，装哪个用哪个。

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
```

会话内 `/plugin marketplace add …`、`/plugin install …` 同理。本地目录添加的市场，改完文件后 `/reload-plugins` 或重开会话即生效。

## 插件列表

| 插件 | skill | 用途 |
| --- | --- | --- |
| `ai-agent-architecture` | `ai-agent-architecture` | 平台 × 协议 × 模型 的 LLM 端点事实矩阵、供应商分层架构、知识吸收协议 |

## 目录约定

```
.claude-plugin/marketplace.json     市场清单（name / owner / plugins[]）
plugins/<plugin>/
  .claude-plugin/plugin.json        插件清单（name 必须与市场条目一致）
  skills/<skill>/SKILL.md           skill 入口
  skills/<skill>/references/        按需加载的资料
```

新增一个 skill：在 `plugins/` 下新建插件目录，写 `plugin.json`，把 skill 放进 `skills/`，然后在 `marketplace.json` 的 `plugins` 数组加一项（`source` 用相对市场根的路径，不能含 `..`）。校验：`claude plugin validate .`。
