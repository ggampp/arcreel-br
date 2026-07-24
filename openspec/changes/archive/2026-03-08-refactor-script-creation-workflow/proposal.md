## Why

O sistema atual de criação de roteiro tem três problemas estruturais:

**1. Desalinhamento de escopo — tarefas globais presas no fluxo por episódio**

O design de personagens/pistas é, em essência, uma operação de **dimensão da obra inteira** (analisar o romance completo, montar um sistema de personagens reutilizável entre episódios), mas está embutido no fluxo de subagent per-episode (narration Step 2, drama Step 3). Consequências:
- No primeiro episódio registram-se personagens; nos seguintes "já existe, ignora" — efeito colateral implícito, não design global explícito
- O usuário não consegue fazer primeiro um planejamento completo de personagens/pistas e só depois criar o roteiro episódio a episódio
- Se o usuário quiser tratar só um capítulo, ainda é forçado a percorrer o fluxo inteiro

**2. Subagent com várias etapas de confirmação interativa — viola o padrão de uso de subagent**

O valor central do subagent é **proteger o espaço de contexto do agente principal**: descarregar para o subagent o processamento de muito material bruto (romance inteiro) e as chamadas de skill; o agente principal só recebe resultados enxutos. Porém os dois subagents atuais contêm 3–4 etapas com confirmação do usuário, o que leva a:
- O subagent ocupa o estado de execução por muito tempo; produtos intermediários (step1, step2…) se acumulam no context do subagent
- A confirmação via AskUserQuestion acontece dentro do subagent, mas a capacidade de revisão que o usuário precisa (ver arquivos do projeto, comparar mudanças) é mais natural no agente principal
- Se o contexto do subagent se aproximar do limite da janela ou houver erro, o fluxo multi-etapas precisa recomeçar do zero

Padrão correto: **cada subagent aceita uma tarefa focada, conclui de forma independente (podendo chamar skills/scripts por dentro) e retorna o resultado**. Confirmações e orquestração entre etapas ficam com o agente principal, entre subagents.

**3. Camada de orquestração ausente — divisão de responsabilidades entre skill e agent pouco razoável**

- `manga-workflow` deveria ser o hub de orquestração, mas é só um Markdown estático
- Os dois agents misturam orquestração (controle de etapas), raciocínio (análise de texto) e execução (chamar a skill generate-script)
- Não há princípio claro de fronteira skill/agent: o que deve ser subagent (precisa de raciocínio + proteger o context principal) e o que o agente principal deve chamar direto

## What Changes

Seguindo a filosofia subagent-driven-development — **um subagent, uma tarefa focada; o subagent pode chamar skills por dentro; o agente principal só orquestra e confirma com o usuário** — remodelar todo o sistema skill/agent.

### Princípios de camadas da arquitetura

```
Agente principal (camada de orquestração — extremamente leve)
  │  Mantém apenas: resumo do estado do projeto + histórico de conversa
  │  Responsabilidades: detecção de estado, decisão de fluxo, confirmação do usuário, dispatch de subagent
  │
  ├─ dispatch via Agent tool ──→  Subagent (camada de execução — tarefa focada)
  │                                 Mantém: material bruto necessário à tarefa (texto do romance etc.)
  │                                 Responsabilidades: raciocínio/análise + chamar skill/script
  │                                 │
  │                                 ├─ Skills pré-carregadas (via frontmatter `skills`)
  │                                 ├─ invoke Skill tool / Bash ──→  execução de script
  │                                 │    generate-script, generate-characters...
  │                                 │    operações determinísticas, chamar API / rodar ffmpeg
  │                                 │
  │                                 ├─ ⚠️ Não pode spawnar sub-subagent (restrição do SDK)
  │                                 │
  │                                 └─ Retorna resultado enxuto ao agente principal
  │
  └─ Recebe o resumo, mostra ao usuário, obtém confirmação
```

**Restrições-chave** (documentação oficial do Claude Code):
- Subagent **não pode** spawnar outro subagent — só o agente principal despacha subagents
- Skills podem ser **pré-carregadas** no subagent via campo `skills` (conteúdo injetado no context do subagent)
- Skills também podem rodar no subagent via mecanismo `context: fork`
- Skills são chamadas pelo subagent, não pelo agente principal — prompts/logs volumosos ficam no context do subagent; o principal só vê o resumo

### Mudanças centrais

- **Desmembrar os dois grandes agents em vários templates de subagent focados** (diretório `agents/`):
  - `analyze-characters-clues` — extração global de personagens/pistas (romance inteiro ou intervalo), grava em project.json via ProjectManager
  - `split-narration-segments` — divisão de segmentos no modo narração (per-episode), retorna arquivo intermediário step1
  - `normalize-drama-script` — normalização + orçamento de planos no modo drama (per-episode), retorna arquivos intermediários step1+step2
  - `create-episode-script` — geração unificada de roteiro JSON (per-episode), chama a skill generate-script por dentro, retorna o resultado
  - Cada template define **contrato claro de entrada/saída**: o que recebe, o que retorna, o que chama por dentro
  - **BREAKING**: remover `novel-to-narration-script.md` e `novel-to-storyboard-script.md`

- **Elevar manga-workflow a skill real de orquestração**:
  - Capacidade de detecção de estado (ler project.json + inspecionar o sistema de arquivos)
  - Transições de etapa e estratégia de dispatch claras
  - Após cada retorno de subagent, o agente principal revisa o resumo, mostra ao usuário, obtém confirmação e só então despacha de novo
  - Entradas flexíveis: só design global de personagens, só roteiro de um episódio, ou continuar de qualquer etapa
  - Etapas posteriores de geração de ativos (generate-characters/storyboard/video) também via dispatch de subagent, não chamada direta de skill pelo agente principal

- **Estabelecer o princípio de fronteira skill/agent**:
  - **Subagent (Task)** = tarefas que precisam de muito contexto ou raciocínio → proteger o context do agente principal
  - **Skill (chamada dentro do subagent)** = execução determinística de script → chamada de API, geração de arquivos
  - **Chamada direta pelo agente principal** = só operações leves (ler estado do projeto, operações simples de arquivo)

### Nova sequência do fluxo de trabalho

```
Agente principal (orquestração — extremamente leve)   Subagents (execução focada)
───────────────────────                               ─────────────────────

[Etapa 0] Detectar estado do projeto
├─ Ler resumo de project.json
├─ Julgar o que falta
└─ Decidir a etapa de entrada

[Etapa 1: Design global de personagens/pistas]
dispatch → ──────────────── → analyze-characters-clues
  Envia: romance + personagens já existentes   Analisa o romance inteiro
                                               Extrai tabela de personagens + pistas
                                               Grava em project.json via ProjectManager
                                               Retorna: resumo de personagens/pistas
← ────────────────────────── ←
Mostra o resumo, usuário confirma ✓

[Etapa 2: Pré-processamento de episódio]
dispatch → ──────────────── → split-narration-segments
  Envia: texto do episódio                      (ou normalize-drama-script)
  Envia: lista de nomes de personagens/pistas   Divisão/normalização + orçamento de planos
                                               Salva arquivos intermediários em drafts/
                                               Retorna: resumo de segmentos/cenas
← ────────────────────────── ←
Mostra o resumo, usuário confirma ✓

[Etapa 3: Geração de roteiro JSON]
dispatch → ──────────────── → create-episode-script
  Envia: número do episódio + parâmetros de modo  Chama generate-script por dentro
                                               Valida a saída
                                               Retorna: resumo do resultado
← ────────────────────────── ←
Mostra o resultado, usuário confirma ✓

[Etapa 4+: Geração de ativos]
dispatch → ──────────────── → subagent chama /generate-characters
dispatch → ──────────────── → subagent chama /generate-clues
dispatch → ──────────────── → subagent chama /generate-storyboard
dispatch → ──────────────── → subagent chama /generate-video
  Cada subagent chama a skill correspondente por dentro
  Retorna o resumo ao agente principal
```

### Decisões de design-chave

1. **Isolamento de contexto**: o texto do romance só entra no context do subagent; o agente principal nunca carrega o romance bruto. O subagent devolve resumos enxutos (tabelas, estatísticas, status), protegendo o espaço de contexto do principal.

2. **Desacoplar design global e criação por episódio**: a extração de personagens/pistas é etapa independente, executável sozinha. O usuário pode planejar personagens do livro inteiro primeiro e criar o roteiro episódio a episódio. Também há modo incremental — quando um episódio novo descobre personagens, eles são acrescentados.

3. **Chamadas de skill descem para o subagent**: skills de geração (generate-characters, generate-storyboard etc.) são chamadas pelo subagent, não pelo agente principal. O volume de prompt e logs de geração fica no context do subagent; o principal só recebe resumos como "geradas N imagens de design de personagem".

4. **Dois modos compartilham etapas globais**: extração de personagens/pistas e geração de JSON usam o mesmo template de subagent nos dois modos. Só o pré-processamento muda de template conforme o modo.

## Capabilities

### New Capabilities
- `workflow-orchestration`: mecanismo de skill de orquestração — manga-workflow elevado a skill com percepção de estado; define transição de etapas, estratégia de dispatch de subagent, protocolo de passagem de contexto (só o necessário), retomada após interrupção e pontos de entrada flexíveis
- `focused-subagent-tasks`: sistema de templates de tarefas de subagent focadas — desmembrar o agent multi-etapas original em templates de task prompt independentes; cada um define contrato de entrada/saída, lista de skills chamáveis por dentro e restrições de execução
- `global-character-clue-extraction`: extração global de personagens/pistas — independente do fluxo por episódio; suporta análise do livro inteiro e acréscimo incremental; grava dados via ProjectManager

### Modified Capabilities
(nenhum spec existente a modificar)

## Impact

- **Definições de Agent**: remover 2 agents grandes; adicionar 3–4 templates de task prompt focados (`agent_runtime_profile/.claude/agents/`)
- **Arquivos de Skill**: `manga-workflow/SKILL.md` reescrito de documento estático para skill de orquestração com detecção de estado e lógica de dispatch
- **Prompt do agente principal**: `_PERSONA_PROMPT` em `session_manager.py` ganha consciência de orquestração e compreensão das etapas do fluxo
- **CLAUDE.md do agent_runtime_profile**: atualizar documentação do fluxo e da fronteira skill/agent
- **Skills de geração existentes não afetadas**: `generate-script`, `generate-characters`, `generate-clues`, `generate-storyboard`, `generate-video`, `compose-video` permanecem iguais (só muda o chamador: de agente principal para subagent)
- **Serviços de backend não afetados**: em `server/agent_runtime/` subagents continuam sendo despachados via ferramenta Task
- **Frontend não afetado**
- **Modelo de dados inalterado**: estrutura de `project.json` permanece
