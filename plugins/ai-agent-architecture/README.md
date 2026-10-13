# ai-agent-architecture

一个插件，四个按任务选用的 skill。安装一次即可使用 LLM 接入、agent 运行时、接入配置与计费设计的知识和规范。

| 任务 | skill / 显式调用 |
| --- | --- |
| 查模型能力、审查 API 接入、接入新厂商、排查协议问题、记录实测结果 | `/ai-agent-architecture:ai-agent-architecture` |
| 搭建 agent、工具循环、审批与写安全、子代理、上下文压缩与会话持久化 | `/ai-agent-architecture:agent-runtime-architecture` |
| 设计渠道 → 线路 → 模型配置、多协议切换、迁移与合并供应商、设置 UI | `/ai-agent-architecture:channel-route-model` |
| 设计 token / 按次 / 按规格计费、用量快照、上游报价、视频结算与用量 UI | `/ai-agent-architecture:llm-billing-model` |

每个 skill 保留独立的 `SKILL.md`、触发描述与按需加载的 `references/`；按任务读取相应入口。开发流程由独立的 `dev-workflow` 插件提供。

目录：

```text
skills/
├── ai-agent-architecture/
├── agent-runtime-architecture/
├── channel-route-model/
└── llm-billing-model/
```

其中 LLM 接入知识库的资料组织：

```
skills/ai-agent-architecture/
├── SKILL.md                 入口：三个坐标轴、四种用法、五层文件地图、证据记法、六条原则
└── references/
    流程   00-audit-playbook.md · 12-migration-roadmap.md · 30-knowledge-ingestion.md
    结论表 20-platform-matrix.md（平台，含各家正文索引）· 22-model-capability-matrix.md（模型 × 平台 × 面，核心）
           23-media-matrix.md（出图 / 视频 / ASR）· 31-open-questions.md（待核实）
    正文   01 架构分层 · 02 协议差异（含四族总对照表）· 03 思考 · 04 结构化 · 05 工具与服务端工具
           06 错误 / usage / 探测 · 13 出图 · 14 视频 · 16 语音识别
    反查   11-pitfalls.md（现象 → 对策 → 指针）
    日志   CHANGELOG.md
```
