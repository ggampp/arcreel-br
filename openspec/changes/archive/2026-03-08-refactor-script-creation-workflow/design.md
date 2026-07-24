## Context

### Situação atual

O ArcReel usa o Claude Agent SDK em uma sessão de agente principal e despacha subagents via ferramenta Agent (antes Task) para tarefas concretas. Hoje há dois subagents grandes (`novel-to-narration-script`, `novel-to-storyboard-script`), cada um com 3–4 etapas e pontos de confirmação do usuário, e um documento de orquestração estático `manga-workflow`.

### Restrições do mecanismo de Subagent do Claude Code

Com base na [documentação oficial do Claude Code](https://code.claude.com/docs/en/sub-agents.md):

1. **Subagent não pode spawnar subagent**: delegação aninhada não é viável; fluxos multi-etapas só via dispatch em cadeia pelo agente principal
2. **Pré-carregamento de skill**: o campo `skills` no frontmatter do subagent injeta o conteúdo da skill no context do subagent; o subagent não herda as skills do agente principal
3. **Context independente do subagent**: o subagent só recebe o próprio system prompt + informações básicas de ambiente, não o system prompt completo do agente principal
4. **Subagent em background**: pode-se definir `background: true` para rodar em segundo plano, com auto-deny de permissões não pré-autorizadas
5. **Mecanismo de resume**: o subagent pode retomar pelo agent ID, preservando o histórico completo
6. **Auto-compaction**: o subagent suporta compactação automática, disparada por volta de 95% da capacidade

### Arquivos relacionados

| Arquivo | Papel |
|------|------|
| `agent_runtime_profile/.claude/agents/*.md` | Definições de subagent |
| `agent_runtime_profile/.claude/skills/*/SKILL.md` | Definições de skill |
| `agent_runtime_profile/.claude/settings.json` | Configuração de permissões e ferramentas |
| `agent_runtime_profile/CLAUDE.md` | Instruções de runtime do agente principal |
| `server/agent_runtime/session_manager.py` | Injeção de prompt do agente principal |

## Goals / Non-Goals

**Goals:**

1. Desmembrar os dois subagents multi-etapas em vários subagents de tarefa única focada; cada um faz uma coisa e retorna
2. Separar a extração de personagens/pistas do fluxo per-episode, tornando-a operação global
3. Elevar manga-workflow de documento estático a skill de orquestração com detecção de estado e lógica de dispatch
4. Estabelecer fronteira clara entre skill (execução de script) e subagent (raciocínio/análise)
5. Descer as chamadas de skills de geração para dentro de subagents, protegendo o espaço de contexto do agente principal

**Non-Goals:**

- Alterar a implementação das skills de geração generate-characters, generate-clues, generate-storyboard, generate-video, compose-video etc.
- Alterar código dos serviços de backend (`server/agent_runtime/` permanece)
- Alterar código do frontend
- Alterar a estrutura de dados de project.json
- Implementar um engine de fluxo de trabalho ou framework de máquina de estados novo (basta prompt da skill)

## Decisions

### Decision 1: Estratégia de desmembramento de subagents

**Escolha**: desmembrar os dois agents grandes em 3 subagents focados + reutilizar skills existentes

**Alternativas**:
- A) Manter os dois agents grandes, só mudar o fluxo interno → não resolve o desalinhamento de escopo
- B) Eliminar subagents e executar tudo com skill no agente principal → o romance bruto contamina o context do principal
- C) Um subagent por etapa original (5–6) → superdivisão; algumas etapas são leves demais para o custo de um subagent

**Justificativa**: 3 subagents correspondem a 3 etapas que realmente precisam de raciocínio (análise global de personagens, pré-processamento de episódio, validação/correção na geração de JSON). Operações de geração (generate-characters etc.) já têm skill/script independentes e podem ser chamadas via subagent.

**Lista dos novos subagents**:

| Subagent | Escopo | Entrada | Saída | Skills pré-carregadas |
|----------|--------|------|------|--------------|
| `analyze-characters-clues` | Global (romance inteiro) | Romance + personagens/pistas existentes | Tabela de personagens + pistas (grava em project.json) | — |
| `split-narration-segments` | Episódio (modo narration) | Texto do episódio + lista de personagens/pistas | `drafts/episode_{N}/step1_segments.md` | — |
| `normalize-drama-script` | Episódio (modo drama) | Texto do episódio + lista de personagens/pistas | `drafts/episode_{N}/step1_normalized_script.md` + `step2_shot_budget.md` | — |
| `create-episode-script` | Episódio | Número do episódio + content_mode | scripts/episode_N.json | `generate-script` |

**Modo de criação**: na implementação, o Claude fornece o texto de description de cada agent; o usuário cria interativamente com o comando `/agents`.

### Decision 2: Design da skill de orquestração

**Escolha**: reescrever `manga-workflow` como skill de orquestração com lógica de detecção de estado (só prompt, sem framework de código)

**Alternativas**:
- A) Escrever um framework de máquina de estados em Python → overengineering e desalinhado do modo prompt-based do Claude Agent SDK
- B) Dividir em várias skills independentes, o usuário chama na ordem → falta orquestração automática, pior UX
- C) Hardcodar a orquestração em session_manager.py → viola a separação entre agent_runtime_profile e server

**Justificativa**: a skill de orquestração é um conjunto de regras de decisão — checar estado, decidir o próximo passo, despachar o subagent certo. Isso se expressa bem com prompt estruturado, sem framework de código. Depois de carregar a skill manga-workflow, o agente principal age conforme a árvore de decisão da skill.

**Estrutura da skill de orquestração manga-workflow**:
```
1. Detecção de estado (ler project.json + checar o sistema de arquivos drafts/scripts)
2. Árvore de decisão de etapas:
   ├─ Faltam personagens/pistas → dispatch analyze-characters-clues
   ├─ Faltam drafts → dispatch preprocess-episode
   ├─ Faltam scripts → dispatch create-episode-script
   ├─ Faltam imagens de design → dispatch subagent chama generate-characters/clues
   ├─ Faltam storyboards → dispatch subagent chama generate-storyboard
   └─ Faltam vídeos → dispatch subagent chama generate-video
3. Após cada dispatch retornar: mostrar resumo → confirmação do usuário → próxima etapa
```

### Decision 3: Modo de chamada de skill — pré-carregamento vs chamada em runtime

**Escolha**: estratégia mista

- O subagent `create-episode-script` **pré-carrega** a skill `generate-script` via campo `skills` (a tarefa central do subagent é chamar essa skill)
- Na etapa de geração de ativos (generate-characters/storyboard/video), o agente principal despacha um subagent genérico que, em runtime, **chama via Bash** o script Python correspondente (essas skills são essencialmente wrappers de script)

**Alternativas**:
- Pré-carregar todas as skills → alguns subagents carregam conteúdo desnecessário e desperdiçam context
- Todas as skills só em runtime → para algumas skills as instruções são críticas ao comportamento do subagent e precisam de pré-carregamento

**Justificativa**: pré-carregamento serve quando "o comportamento do subagent é totalmente definido pela skill"; chamada em runtime serve quando "o subagent só precisa executar um comando de script".

### Decision 4: Momento de disparo da extração global de personagens/pistas

**Escolha**: primeira etapa explícita do fluxo de orquestração, e também chamável de forma independente

**Design**:
- Na orquestração de `manga-workflow`, se characters ou clues em project.json estiverem vazios, entrar automaticamente na etapa de extração global
- O usuário também pode chamar a qualquer momento (ex.: "analisar personagens do romance inteiro" → o agente principal despacha `analyze-characters-clues`)
- Modo incremental: se project.json já tem personagens, o subagent compara o romance com a lista existente e só acrescenta novos
- O usuário pode definir o escopo da análise (romance inteiro / alguns capítulos / a parte de um episódio)

**Alternativas**:
- Só disparar automaticamente na criação do primeiro episódio → volta ao modo de efeito colateral implícito
- Reanalisar a cada episódio → desperdício e risco de inconsistência

### Decision 5: Etapa de geração de ativos usa subagent?

**Escolha**: skills de geração de ativos (generate-characters/storyboard/video) chamadas via subagent

**Justificativa**:
- Essas skills geram muita saída (prompt de geração, logs de API, progresso)
- Descer para o subagent protege o context do agente principal
- O subagent pode tratar falhas, retries e resumo de resultados parciais, retornando só o resumo final
- Com `background: true` do subagent, parte da geração pode rodar em segundo plano

**Implementação**: criar um template genérico de subagent `asset-generator` para a etapa de geração de ativos, com parâmetro indicando qual script de skill chamar; ou o agente principal despacha um subagent general-purpose com a tarefa no prompt.

### Decision 6: Scriptar a gravação de personagens/pistas

**Escolha**: novo script `add_characters_clues.py` encapsulando `ProjectManager.add_characters_batch()` + `add_clues_batch()` + `validate_project()`

**Situação atual**:
- `ProjectManager` já tem `add_characters_batch()` e `add_clues_batch()`
- Mas não há script CLI independente — os dois agents grandes chamam esses métodos com blocos Python embutidos
- O subagent precisa chamar o script via Bash (não código embutido), logo é necessário um script executável

**Design**:
```bash
# Uso
python .claude/skills/manage-project/scripts/add_characters_clues.py {project_name} \
  --characters '{"Nome": {"description": "...", "voice_style": "..."}}' \
  --clues '{"Nome da pista": {"type": "prop", "description": "...", "importance": "major"}}'
```

- Entrada: nome do projeto + dados de personagens/pistas em JSON (argumentos de CLI ou stdin)
- Saída: grava em project.json + chama validate_project + imprime resumo de sucesso/falha
- **Liberar em settings.json**: adicionar em `permissions.allow` `Bash(python .claude/skills/manage-project/scripts/add_characters_clues.py *)`

### Decision 7: Pré-processamento no modo drama em dois passos — Gemini gera Markdown + script_generator gera JSON

**Escolha**: o subagent `normalize-drama-script` chama um novo script com `gemini-3.1-pro-preview` para gerar o roteiro normalizado em Markdown (step1); depois o subagent `create-episode-script` usa o `script_generator` existente para converter Markdown em JSON (step2)

**Fluxo em dois passos**:

```
Step 1 (subagent normalize-drama-script)
  ├─ Chama o novo script normalize_drama_script.py
  ├─ Script usa o modelo gemini-3.1-pro-preview
  ├─ Entrada: romance em source/
  ├─ Saída: drafts/episode_{N}/step1_normalized_script.md
  │         drafts/episode_{N}/step2_shot_budget.md
  └─ Edições posteriores: o subagent (Claude) edita o Markdown diretamente

Step 2 (subagent create-episode-script — implementação existente)
  ├─ Chama o generate_script.py existente
  ├─ script_generator lê step1_normalized_script.md
  ├─ Gera JSON com gemini-3-flash-preview
  └─ Saída: scripts/episode_{N}.json
```

**Situação atual**:
- `ScriptGenerator` já suporta o modo drama — `build_drama_prompt()` lê `step1_normalized_script.md` como entrada
- O roteiro normalizado (step1) hoje é escrito manualmente pelo agent (Claude) — lento e consome muito context
- O novo é só a automação Gemini do step1; o step2 reutiliza a implementação existente

**Design do novo script**:
- Local: `agent_runtime_profile/.claude/skills/generate-script/scripts/normalize_drama_script.py` (dentro de generate-script, pois faz parte do fluxo de geração de roteiro)
- Modelo: `gemini-3.1-pro-preview` (Pro é melhor em reescrita estruturada de textos longos)
- Formato de saída: Markdown (compatível com o `step1_normalized_script.md` existente, para o script_generator consumir sem atrito)
- **Liberar em settings.json**: adicionar `Bash(python .claude/skills/generate-script/scripts/normalize_drama_script.py *)`

**Alternativas**:
- Tudo gerado por Claude → lento, caro em context, ruim para romances longos
- Modelo flash → Pro tem melhor qualidade em compreensão e reescrita estruturada de textos longos

## Risks / Trade-offs

### [Risco] Custo de passagem de contexto do subagent
No dispatch, o prompt precisaria carregar muito conteúdo (romance etc.), consumindo o context do subagent.

→ **Mitigação**: o subagent lê arquivos, em vez de receber o conteúdo no prompt. O prompt só leva caminhos e parâmetros-chave; o subagent lê o que precisa.

### [Risco] Complexidade da skill de orquestração
manga-workflow precisa detectar vários estados e tratar vários pontos de entrada; um prompt puro pode ficar longo demais.

→ **Mitigação**: árvore de decisão clara e formatação Markdown; se o prompt ficar longo, dividir em skills auxiliares.

### [Risco] Mudança na capacidade de retomada
O subagent grande antigo tinha context contínuo e retomava naturalmente. Depois do desmembramento, a retomada depende da skill de orquestração redetectar o estado.

→ **Mitigação**: cada etapa, ao concluir, persiste no sistema de arquivos (project.json, drafts/, scripts/); a skill de orquestração retoma pelo estado do filesystem. Isso é, na prática, mais confiável que a recuperação interna do subagent — não depende do context do subagent sobreviver.

### [Trade-off] Mais subagents → mais chamadas de API
Antes 1 subagent fazia tudo; agora 3–4 em sequência, cada dispatch com custo.

→ **Aceitar**: o custo extra de API é controlável; o ganho é melhor isolamento arquitetural, flexibilidade e tolerância a falhas.

### [Trade-off] Carga de orquestração no agente principal
O agente principal precisa entender as etapas do fluxo, despachar o subagent certo e repassar contexto.

→ **Mitigação**: a skill de orquestração manga-workflow dá instruções claras; o agente principal só "age conforme a skill".
