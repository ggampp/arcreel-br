---
status: accepted
---

# Proteção de arquivos do Agent em duas camadas: sandbox de kernel na árvore de subprocessos Bash; ferramentas de arquivo embutidas no PreToolUse hook

O sandbox de kernel (`SandboxSettings.filesystem.denyRead/denyWrite`) só restringe a ferramenta Bash e todos os subprocessos derivados dela; Read/Write/Edit/Glob/Grep embutidos do SDK não passam pelo Bash e executam direto no processo principal — o sandbox de kernel não os cobre. Decidimos completar a segunda camada nas ferramentas de arquivo embutidas com PreToolUse hook de aplicação (`_is_path_allowed`: arquivos sensíveis, leitura/escrita cross-projeto, extensões de código, cwd fora dos limites), as duas camadas cobrindo as mesmas regras de caminho. O ponto de interceptação **deve** ser PreToolUse hook, não `can_use_tool`: na cadeia de permissões do SDK, Read/Glob/Grep são liberados primeiro pela regra allow e nunca chegam a `can_use_tool`.

## Consequences

- Reviews de mudanças que tocam acesso a arquivo do agent precisam confirmar separadamente: o caminho Bash é interceptável (profile do sandbox)? o caminho das ferramentas embutidas é interceptável (hook)? Qualquer camada sozinha tem bypass.
- `docs/adr/0003` é a aplicação concreta dessas duas camadas na «escrita de JSON de projeto» (denyWrite e `_check_write_access` são as duas camadas da mesma origem).
