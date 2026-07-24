## 1. Desenvolvimento de scripts novos

- [x] 1.1 Criar o script `add_characters_clues.py`: encapsular `ProjectManager.add_characters_batch()` + `add_clues_batch()` + `validate_project()`, recebendo dados de personagens/pistas em JSON por argumento de linha de comando ou stdin
- [x] 1.2 Criar o script `normalize_drama_script.py`: com o modelo `gemini-3.1-pro-preview`, ler o romance em source/, gerar roteiro normalizado em Markdown (`step1_normalized_script.md`) e orçamento de planos (`step2_shot_budget.md`); o formato de saída deve ser compatível com `ScriptGenerator.build_drama_prompt()`
- [x] 1.3 Em `permissions.allow` de `settings.json`, adicionar permissão Bash dos dois novos scripts
- [x] 1.4 Validar a compatibilidade de `generate-script` com os dois content_mode (narration lê step1_segments.md, drama lê step1_normalized_script.md) e corrigir problemas encontrados

## 2. Criação de subagents focados

- [x] 2.1 Fornecer a description do agent `analyze-characters-clues` para o usuário criar via `/agents` (extração global de personagens/pistas, analisa o romance inteiro, grava em project.json via Bash com add_characters_clues.py, retorna resumo estruturado)
- [x] 2.2 Fornecer a description do agent `split-narration-segments` para o usuário criar via `/agents` (divisão de segmentos no modo narração, ~4 s/segmento pelo ritmo de leitura, marca segment_break, salva arquivos intermediários em drafts/, retorna resumo)
- [x] 2.3 Fornecer a description do agent `normalize-drama-script` para o usuário criar via `/agents` (na primeira geração chama normalize_drama_script.py com Gemini 3.1 Pro; edições posteriores o agent edita o Markdown diretamente; retorna resumo)
- [x] 2.4 Fornecer a description do agent `create-episode-script` para o usuário criar via `/agents` (pré-carrega a skill generate-script, chama generate_script.py para gerar JSON, valida a saída, retorna resumo)
- [x] 2.5 Após o usuário criar os 4 agents, revisar os arquivos gerados para garantir que frontmatter e system prompt atendem aos requisitos

## 3. Reescrita da skill de orquestração

- [x] 3.1 Reescrever `manga-workflow/SKILL.md`: lógica de detecção de estado (ler project.json + inspecionar o sistema de arquivos em drafts/scripts/characters/storyboards/videos)
- [x] 3.2 Definir a árvore de decisão de etapas em manga-workflow: faltam personagens → dispatch analyze-characters-clues; faltam drafts → dispatch split-narration-segments ou normalize-drama-script (conforme content_mode); faltam scripts → dispatch create-episode-script; faltam ativos → dispatch subagent de geração de ativos
- [x] 3.3 Definir o protocolo de confirmação entre etapas em manga-workflow: após o retorno de cada subagent, mostrar resumo, obter confirmação via AskUserQuestion, suportar refazer/pular/continuar
- [x] 3.4 Definir as regras de passagem de contexto em manga-workflow: quais parâmetros cada dispatch de subagent recebe (nome do projeto, número do episódio, content_mode, caminhos de arquivo)

## 4. Adaptação do subagent de geração de ativos

- [x] 4.1 Definir o modo de dispatch do subagent de geração de ativos: criar template de agent dedicado ou usar subagent general-purpose + prompt de tarefa concreto
- [x] 4.2 Incluir em manga-workflow a lógica de dispatch das etapas de geração de ativos (generate-characters, generate-clues, generate-storyboard, generate-video)

## 5. Limpeza dos agents antigos e atualização de documentação

- [x] 5.1 Remover `agent_runtime_profile/.claude/agents/novel-to-narration-script.md`
- [x] 5.2 Remover `agent_runtime_profile/.claude/agents/novel-to-storyboard-script.md`
- [x] 5.3 Atualizar `agent_runtime_profile/CLAUDE.md`: substituir a descrição do fluxo (dos dois agents grandes para a arquitetura skill de orquestração + subagents focados)
- [x] 5.4 Atualizar `agent_runtime_profile/CLAUDE.md`: adicionar a explicação do princípio de fronteira skill/agent
- [x] 5.5 Atualizar `agent_runtime_profile/.claude/settings.json`: confirmar que as permissões de ferramentas dos novos subagents estão corretas

## 6. Reforço do prompt do agente principal

- [x] 6.1 Atualizar `_PERSONA_PROMPT` em `server/agent_runtime/session_manager.py`: consciência de orquestração — entender as etapas do fluxo e saber quando despachar qual subagent
- [x] 6.2 Avaliar se `_build_append_prompt()` precisa injetar o estado da etapa atual do fluxo (otimização opcional)

## 7. Testes de integração e verificação

- [x] 7.1 Validação ponta a ponta: projeto novo percorrendo o fluxo completo de manga-workflow (extração de personagens → pré-processamento → geração de JSON)
- [x] 7.2 Validar entrada flexível: projeto com personagens já existentes entra direto no pré-processamento de episódio
- [x] 7.3 Validar modo incremental: no segundo episódio, comportamento de acréscimo da extração de personagens/pistas
- [x] 7.4 Validar modo narration com split-narration-segments e modo drama com normalize-drama-script (incluindo chamada ao script Gemini)
- [x] 7.5 Validar que o formato de saída de normalize_drama_script.py é consumido corretamente por generate_script.py
