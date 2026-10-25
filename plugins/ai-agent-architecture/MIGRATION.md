# 4.0.0 迁移清单

插件安装名保持 `ai-agent-architecture`。旧 skill 入口不作为别名保留，调用方需更新名称。

| 原路径（插件内） | 新路径 |
| --- | --- |
| `skills/agent-runtime-architecture/SKILL.md` | [skills/agent-runtime-architecture/SKILL.md](skills/agent-runtime-architecture/SKILL.md) |
| `skills/agent-runtime-architecture/references/07-agent-runtime.md` | [skills/agent-runtime-architecture/references/agent-runtime.md](skills/agent-runtime-architecture/references/agent-runtime.md) |
| `skills/agent-runtime-architecture/references/08-tool-registry-and-write-safety.md` | [skills/agent-runtime-architecture/references/tool-registry-and-write-safety.md](skills/agent-runtime-architecture/references/tool-registry-and-write-safety.md) |
| `skills/agent-runtime-architecture/references/09-subagent.md` | [skills/agent-runtime-architecture/references/subagent.md](skills/agent-runtime-architecture/references/subagent.md) |
| `skills/agent-runtime-architecture/references/10-context-management.md` | [skills/agent-runtime-architecture/references/context-management.md](skills/agent-runtime-architecture/references/context-management.md) |
| `skills/agent-runtime-architecture/references/11-pitfalls.md` | [skills/agent-runtime-architecture/references/pitfalls.md](skills/agent-runtime-architecture/references/pitfalls.md) |
| `skills/agent-runtime-architecture/references/12-roadmap.md` | [skills/agent-runtime-architecture/references/roadmap.md](skills/agent-runtime-architecture/references/roadmap.md) |
| `skills/ai-agent-architecture/SKILL.md` | [skills/llm-api-integration/SKILL.md](skills/llm-api-integration/SKILL.md) |
| `skills/ai-agent-architecture/references/00-audit-playbook.md` | [skills/llm-api-integration/references/audit-playbook.md](skills/llm-api-integration/references/audit-playbook.md) |
| `skills/ai-agent-architecture/references/01-provider-layering.md` | [skills/llm-api-integration/references/provider-layering.md](skills/llm-api-integration/references/provider-layering.md) |
| `skills/ai-agent-architecture/references/02-protocol-differences.md` | [skills/llm-api-integration/references/protocol-differences.md](skills/llm-api-integration/references/protocol-differences.md) |
| `skills/ai-agent-architecture/references/03-reasoning.md` | [skills/llm-api-integration/references/reasoning.md](skills/llm-api-integration/references/reasoning.md) |
| `skills/ai-agent-architecture/references/04-structured-output.md` | [skills/llm-api-integration/references/structured-output.md](skills/llm-api-integration/references/structured-output.md) |
| `skills/ai-agent-architecture/references/05-tools-and-server-tools.md` | [skills/llm-api-integration/references/tools-and-server-tools.md](skills/llm-api-integration/references/tools-and-server-tools.md) |
| `skills/ai-agent-architecture/references/06-errors-probing-observability.md` | [skills/llm-api-integration/references/errors-probing-observability.md](skills/llm-api-integration/references/errors-probing-observability.md) |
| `skills/ai-agent-architecture/references/11-pitfalls.md` | [skills/llm-api-integration/references/pitfalls.md](skills/llm-api-integration/references/pitfalls.md) |
| `skills/ai-agent-architecture/references/12-migration-roadmap.md` | [skills/llm-api-integration/references/migration-roadmap.md](skills/llm-api-integration/references/migration-roadmap.md) |
| `skills/ai-agent-architecture/references/13-image-generation.md` | [skills/ai-media-api-integration/references/image-generation.md](skills/ai-media-api-integration/references/image-generation.md) |
| `skills/ai-agent-architecture/references/14-video-generation.md` | [skills/ai-media-api-integration/references/video-generation.md](skills/ai-media-api-integration/references/video-generation.md) |
| `skills/ai-agent-architecture/references/16-speech-recognition.md` | [skills/ai-media-api-integration/references/speech-recognition.md](skills/ai-media-api-integration/references/speech-recognition.md) |
| `skills/ai-agent-architecture/references/20-platform-matrix.md` | [skills/llm-api-integration/references/platform-matrix.md](skills/llm-api-integration/references/platform-matrix.md) |
| `skills/ai-agent-architecture/references/22-model-capability-matrix.md` | [skills/llm-api-integration/references/model-capability-matrix.md](skills/llm-api-integration/references/model-capability-matrix.md) |
| `skills/ai-agent-architecture/references/23-media-matrix.md` | [skills/ai-media-api-integration/references/media-matrix.md](skills/ai-media-api-integration/references/media-matrix.md) |
| `skills/ai-agent-architecture/references/30-knowledge-ingestion.md` | [skills/llm-api-integration/references/knowledge-ingestion.md](skills/llm-api-integration/references/knowledge-ingestion.md) |
| `skills/ai-agent-architecture/references/31-open-questions.md` | [skills/llm-api-integration/references/open-questions.md](skills/llm-api-integration/references/open-questions.md) |
| `skills/ai-agent-architecture/references/CHANGELOG.md` | [skills/llm-api-integration/references/CHANGELOG.md](skills/llm-api-integration/references/CHANGELOG.md) |
| `skills/channel-route-model/SKILL.md` | [skills/llm-provider-config/SKILL.md](skills/llm-provider-config/SKILL.md) |
| `skills/channel-route-model/references/01-data-model.md` | [skills/llm-provider-config/references/data-model.md](skills/llm-provider-config/references/data-model.md) |
| `skills/channel-route-model/references/02-storage-and-migration.md` | [skills/llm-provider-config/references/storage-and-migration.md](skills/llm-provider-config/references/storage-and-migration.md) |
| `skills/channel-route-model/references/03-route-switching.md` | [skills/llm-provider-config/references/route-switching.md](skills/llm-provider-config/references/route-switching.md) |
| `skills/channel-route-model/references/04-merge.md` | [skills/llm-provider-config/references/merge.md](skills/llm-provider-config/references/merge.md) |
| `skills/channel-route-model/references/05-ui.md` | [skills/llm-provider-config/references/ui.md](skills/llm-provider-config/references/ui.md) |
| `skills/channel-route-model/references/06-pitfalls.md` | [skills/llm-provider-config/references/pitfalls.md](skills/llm-provider-config/references/pitfalls.md) |
| `skills/llm-billing-model/SKILL.md` | [skills/ai-usage-accounting/SKILL.md](skills/ai-usage-accounting/SKILL.md) |
| `skills/llm-billing-model/references/01-data-model.md` | [skills/ai-usage-accounting/references/data-model.md](skills/ai-usage-accounting/references/data-model.md) |
| `skills/llm-billing-model/references/02-pricing-rules.md` | [skills/ai-usage-accounting/references/pricing-rules.md](skills/ai-usage-accounting/references/pricing-rules.md) |
| `skills/llm-billing-model/references/03-recording.md` | [skills/ai-usage-accounting/references/recording.md](skills/ai-usage-accounting/references/recording.md) |
| `skills/llm-billing-model/references/04-storage-and-migration.md` | [skills/ai-usage-accounting/references/storage-and-migration.md](skills/ai-usage-accounting/references/storage-and-migration.md) |
| `skills/llm-billing-model/references/05-ui.md` | [skills/ai-usage-accounting/references/ui.md](skills/ai-usage-accounting/references/ui.md) |
| `skills/llm-billing-model/references/06-pitfalls.md` | [skills/ai-usage-accounting/references/pitfalls.md](skills/ai-usage-accounting/references/pitfalls.md) |
