---
status: accepted
---

# Edição open-source pré-embute modelo de dados multi-usuário e a costura `_scope_query`, sem implementar multi-tenant

Adicionar depois colunas FK NOT NULL + backfill de linhas históricas em tabelas já em uso custa muito mais do que pré-embutir com `server_default` desde o início, e bifurcaria o schema open-source/comercial. Decidimos, na edição open-source, já adicionar `user_id` (sempre `"default"`) a Task/ApiCall/ApiKey/AgentSession, criar a tabela users (admin default) e o ponto de reescrita no-op `_scope_query` na classe base do Repository; a edição comercial, via migration com campos extras + override de `_scope_query` na subclasse injetando filtro por user_id, implementa isolamento de visibilidade. Sem isolamento de diretório, fluxo de login, quota nem admin backend.

## Consequences

- A edição open-source carrega um lote de no-ops aparentemente inúteis e `"default"` constante — **leitores não devem apagar como código morto**.
- `claim_next` usa SQL nativo e `_scope_query` não intercepta — exceção conhecida que a edição comercial precisa override.
