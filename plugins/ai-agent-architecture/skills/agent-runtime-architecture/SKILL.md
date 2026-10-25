---
name: agent-runtime-architecture
description: >-
  Design, implement, or review agent runtimes: tool-loop lifecycle, cancellation and recovery, execution permissions, approval queues, delegation, context compaction, and session persistence. Use for stuck approvals, missing subagent results, or broken session state. Endpoint wire formats belong to llm-api-integration.
metadata:
  version: "1.1.0"
  updated: "2026-10-25"
---

# Agent Runtime Architecture

面向工具循环、执行权限、子代理、任务工作区、上下文压缩和会话恢复。协议报文归 [LLM API 接入](../llm-api-integration/SKILL.md)。

## 按任务读

| 任务 | 资料 |
| --- | --- |
| 循环终止、preset、事件、工具按需加载 | [运行时](references/agent-runtime.md) |
| 注册表、权限、审批、写入与备份 | [工具执行与写安全](references/tool-registry-and-write-safety.md) |
| 子代理委派、能力选择与结果交付 | [子代理](references/subagent.md) |
| 工作区、压缩、持久化、引用注入与恢复 | [上下文管理](references/context-management.md) |
| 故障排查 | [故障索引](references/pitfalls.md) |
| 从零建设与依赖顺序 | [参考实现路线图](references/roadmap.md) |

## 核心约束

- 执行权限在工具执行边界校验；UI 的按钮状态不能代替授权。审批应绑定运行、目标及版本，应用前重新检查目标是否仍匹配。
- 每次运行结束或取消都要处理其未决审批与工具结果，不清理其他运行的队列。在发送下一轮前修复协议不完整的历史；无法修复时重建上下文并保留审计信息。
- 文件操作遵守目标项目的访问边界；如选择写前备份策略，备份失败就阻止该次写入。
- 原样保存协议要求的跨轮载体。由适配层判断平台、协议、模型和会话兼容性；runtime 不统一按 modelId 删除。
- 临时提示有明确生命周期，不意外成为后续常驻指令；可以使用请求局部消息，也可在参考实现中发出后移除。
- 子代理的权限、取消与产物必须显式定义；并发、递归和代理间通信按产品需求设计，不因参考项目未实现就一律禁止。

## 推荐方案与实现边界

参考资料源自 simple-ai-writer（Tauri / React / TypeScript）。preset 驱动策略、统一注册表、任务笔记和消息配对修复是可选设计；接口名、阶段号、阈值和摘要长度是参考实现，不是所有 Agent 的约束。优先沿用目标项目已有的可靠机制。

按用户范围实现或审查相关模块，并检查取消、失败、恢复路径。报告实际运行的验证命令和结果；需要回归保护时补充测试，已有测试或手工验证不要求另造测试文件。不要为一个局部修复强制先建设完整协议层。
