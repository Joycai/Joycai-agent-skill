---
name: agent-runtime-architecture
description: >-
  Architecture standard for the agent layer on top of an LLM API: the tool
  loop and its termination rules, presets, event system, permission-tiered
  tool registry with approval flow and write safety (backup, plan gating),
  deferred tool loading, sub-agents / delegation with capability routing,
  task workspaces, context compaction and session persistence. Use when
  building or reviewing an agent — "搭一个 agent", "工具调用循环", "审批",
  "子代理", "委派", "上下文压缩", "长会话", "工具按需加载", "会话持久化" — or
  debugging a session that got permanently broken, a hung approval, or a
  sub-agent returning nothing. For wire-format / endpoint protocol facts
  use the ai-agent-architecture skill instead.
metadata:
  version: "1.0.0"
  updated: 2026-09-28
---

# Agent Runtime Architecture（Agent / 子代理体系搭建标准）

这是 agent 层的设计标准：怎样在一个多协议的模型调用层之上，搭 tool loop、工具注册与审批、子代理、任务工作区和上下文压缩。

**协议事实不在这里。** 各家端点的报文、思考回传、工具形状、服务端工具等事实，在 **ai-agent-architecture** skill（一个与语言无关的端点协议知识库）。本 skill 引用那边时写作「ai-agent-architecture 0N §x」。

出处：simple-ai-writer（Tauri + React，TypeScript）的生产实践。代码块里的接口用 TypeScript 记法表达；模式本身与语言无关。

## 按任务读

| 任务涉及… | 读 | 补充 |
| --- | --- | --- |
| agent tool loop、轮次控制、preset、事件系统、执行日志 | `references/07-agent-runtime.md` | 08 |
| 工具 schema 太占固定头部：工具按需加载的策略 | `references/07-agent-runtime.md` §4.6 | 各族协议事实见 ai-agent-architecture 05 §7 |
| 工具注册表、权限分级、审批、备份、审批队列、会话 store | `references/08-tool-registry-and-write-safety.md` | 07 |
| 子代理 / 委派、能力路由、整份 PDF 交给模型读 | `references/09-subagent.md` | 10 |
| 任务工作区、上下文压缩、会话持久化、@引用注入、检索去重 | `references/10-context-management.md` | 09 |
| 排查 agent 层的怪问题（坑 19–53） | `references/11-pitfalls.md` | — |
| 从零搭：阶段 4–9 路线图（依赖协议层的阶段 0–2） | `references/12-roadmap.md` | ai-agent-architecture 12 |

写完每个模块，都对照对应 reference 结尾的「本篇检查清单」逐条过一遍。

## 三条设计原则

1. **runtime 只负责循环，策略全放在数据（preset）里。** 权限在工具执行器里执行，不在 UI 里。能力用「通道在不在」表达：审批就是一个挂起的等待，放在队列里等 UI 来处理；同一个注册表放到缺了某条通道的界面上，会自动降级。
2. **协议完整性是生死不变量。** 每个 tool_call 都必须有配对的回复。中途 abort 也要先补上 `[not run]` 桩再抛错；history 就是会话本身，一次畸形就永久报废。四族拒绝缺失配对的事实见 ai-agent-architecture 05 §4。
3. **一次性提示「发出即撤」。** 请求发出后，把它从 history 里删掉；留着就会变成之后每一轮的常驻指令。

## 最容易漏、代价最大的点

1. tool_call 配对不变量，**包括 abort 路径上的补桩**。漏了，会话永久报废。
2. 每次运行的 finally 里清空这次运行的审批队列。漏了，悬挂的等待会永久卡死之后的运行。
3. 备份失败就等于写入失败：备份抛错时，写入根本不发生。
4. 审批 apply 时要重新定位目标文本。目标消失了、或者匹配到多处，都转成拒绝回给模型——审批卡片挂着的时候，用户可能一直在编辑。
5. 模型能控制的路径参数，一律做包含校验，并且**显式拒绝空前缀**。空的 projectPath 做前缀测试，会包含一切绝对路径。
6. 思考类回传载体原样整存，换模型时按 modelId 剥离。事实见 ai-agent-architecture 03 §5。
7. 一次性提示发出即撤（见上）。

## 关键接口速览（完整定义在 references 里）

```ts
interface TaskPreset {    // runtime 只做循环，策略全在这
  id: string; tools: readonly ToolId[]; maxRounds: number;
  finishPolicy: "force-text" | "allow-tool-end";
  scratchpad?: "off" | "offered" | "required";
  serverTools?: "final-round-off" | "off" | "always" | "no-web";  // no-web 由 routeTools 设（搜索子代理接管时）
}

interface RegisteredTool {
  definition: ToolDefinition;                  // OpenAI function schema
  access: "read" | "write-auto" | "write-approval";
  execute: (call: ToolCall, ctx: ToolContext) => Promise<ToolResult>;
}
// ToolContext 的审批 / 门控 / 工作区钩子全部可选——在缺这些通道的界面上，
// 工具自动报「此界面不支持」，同一个注册表处处可用。

// 子代理 = 一个 delegate 工具 + 嵌套调用同一个 runAgent（沙箱 ctx、共享取消信号）；
// 产出经 onOutputText 捕获（成文轮的文本不入 history！）→ 落盘为 note → 回「路径 + ≤800 字符摘要」。见 09 §2、§5.2。
```

## 交付物约定

- 按用户要求的范围交付：分层的源码目录（或按目标项目的惯例），每个模块附上对照检查清单自查后的说明。
- 声称「已验证 / 已测试」，就必须把可运行的测试文件一并交付；没有随附测试，就等于没做，宁可如实说明未测。
- 范围不确定时先小后大：先把协议层（ai-agent-architecture 12 的阶段 0–2）跑通一个流式调用，再逐阶段推进。
