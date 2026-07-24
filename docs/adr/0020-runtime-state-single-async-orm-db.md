---
status: accepted
---

# Estado de runtime unificado em um único banco ORM assíncrono

Originalmente 3 bancos SQLite síncronos independentes (fila de tarefas / uso de API / sessões Agent) não podiam mudar para PostgreSQL com um único `DATABASE_URL`, não havia FK/transação cross-DB, e o driver síncrono bloqueava o event loop nas rotas async do FastAPI. Decidimos hard-cut para um único banco assíncrono SQLAlchemy, com um `DATABASE_URL` decidindo SQLite (dev) ou PostgreSQL (prod), migração única, sem manter o caminho antigo de SQL escrito à mão — hard-cut evita estado intermediário de double-write e ganha semântica de transação unificada + banco comutável.

## Consequences

- Migração irreversível; uma vez que todos os Repository/Worker estão async e dependem da semântica de transação de banco único, voltar a multi-DB ou driver síncrono exige reescrever a camada inteira de acesso a dados.
- Fronteira de armazenamento em camadas claras: estado de runtime no DB; dados de projeto (project.json / roteiro / arquivos de mídia) continuam no filesystem.
