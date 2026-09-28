# ai-agent-architecture

一个 skill：`ai-agent-architecture`。平台无关的 LLM 接入知识库——已验证的「平台 × 协议 × 模型」事实矩阵、供应商分层架构经验、以及新知识的吸收与修正协议。

安装后触发词：`/ai-agent-architecture:ai-agent-architecture`，或直接问「X 模型在 Y 平台支持不支持 Z」「审查模型接入」「接入新厂商」「这个中转站为什么…」。

目录：

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
