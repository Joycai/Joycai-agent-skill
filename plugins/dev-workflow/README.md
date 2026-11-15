# dev-workflow

支持 Codex 与 Claude，共用同一套 skills。[安装与使用说明](../../README.md)。Codex 可在技能选择器中选择技能，或明确说“使用 `<skill-name>`”；本文 `/插件名:技能名` 示例用于 Claude Code。

一个 skill：`dev-workflow`。标准化的需求实现 / bug 修复流程：子代理定位范围 → 设计文档 → 可用设计工具出 UI 稿 → 执行计划 → 分片提交 → 每次提交后子代理 review → 整体 review 循环 → 开 PR。

触发：`/dev-workflow:dev-workflow`，或「按工作流做」「实现这个需求」「修这个 bug」「走流程」。

新任务文档统一保存到 `.agent-tasks/<slug>/`；已有 `.claude/tasks/<slug>/` 任务继续原位恢复。Codex 默认继承当前模型；没有子代理或设计工具时按技能中的降级规则执行。

## 1.1.0 更新

增加 Codex 插件清单，适配模型选择、设计工具、任务目录与分支命名；保留 Claude 调用方式和旧任务恢复。插件与 skill 内容版本均为 1.1.0。
