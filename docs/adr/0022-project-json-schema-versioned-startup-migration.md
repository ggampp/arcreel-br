---
status: accepted
---

# project.json: schema versionado no nível do arquivo + migração idempotente nível a nível no startup

Não versionar e confiar em compatibilidade ad-hoc de campos antigos na leitura tem custo zero de migração, mas campos de forma antiga permanecem para sempre e os ramos no caminho de leitura se acumulam. Decidimos introduzir `schema_version` de topo em project.json + registry em `lib/project_migrations`; no startup varre cada projeto e roda migrators função pura nível a nível (backup antes da migração, escrita atômica de volta, migração em cascata do roteiro); falha de um projeto isola e não interrompe o startup — versionamento explícito em troca de convergência de forma de dados e reescrita única, melhor do que ramos de compatibilidade infinitos no caminho de leitura.

## Consequences

- Introduz complexidade de backup / escrita atômica / isolamento de falha / idempotência, e a migração reescreve o arquivo in-place de forma irreversível (ex.: v0→v1 quebra clue em scene/prop e apaga importance; v1→v2 normaliza provider).
- A mesma cadeia de migração não roda só no startup: o caminho de **importação** de arquivo de projeto também reutiliza `migrate_project_dir`, porque o runner de startup só cobre projetos já existentes no start; arquivos antigos importados depois do start precisam rodar a cadeia completa na entrada de importação.
