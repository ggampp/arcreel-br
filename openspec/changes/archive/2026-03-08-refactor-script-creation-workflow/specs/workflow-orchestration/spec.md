## ADDED Requirements

### Requirement: A skill de orquestração manga-workflow deve detectar o estado do projeto

Após carregar a skill manga-workflow, ela SHALL detectar automaticamente o estado do fluxo de trabalho do projeto atual, com base em project.json e no sistema de arquivos, para determinar a etapa atual.

#### Scenario: Projeto novo sem personagens e pistas
- **WHEN** characters e clues em project.json estão vazios
- **THEN** a skill de orquestração classifica a etapa atual como "design global de personagens/pistas" e orienta o agente principal a despachar o subagent `analyze-characters-clues`

#### Scenario: Já há personagens, mas sem arquivos intermediários em drafts
- **WHEN** characters em project.json não está vazio, mas o diretório `drafts/episode_{N}/` não existe ou está vazio
- **THEN** a skill de orquestração classifica a etapa como "pré-processamento de episódio" e orienta o agente principal a despachar o subagent de pré-processamento do modo correspondente

#### Scenario: Já há drafts, mas sem scripts
- **WHEN** os arquivos intermediários em `drafts/episode_{N}/` existem, mas `scripts/episode_{N}.json` não existe
- **THEN** a skill de orquestração classifica a etapa como "geração de roteiro JSON" e orienta o agente principal a despachar o subagent `create-episode-script`

#### Scenario: Já há scripts, mas faltam ativos
- **WHEN** `scripts/episode_{N}.json` existe, mas há ativos faltando em characters/ ou storyboards/ ou videos/
- **THEN** a skill de orquestração classifica a etapa como "geração de ativos" e orienta o agente principal a despachar o subagent de geração de ativos correspondente

### Requirement: A skill de orquestração deve definir protocolo de dispatch e confirmação entre etapas

Após o retorno do subagent de cada etapa, o agente principal SHALL exibir o resumo do resultado ao usuário e aguardar confirmação antes de avançar para a próxima etapa.

#### Scenario: Subagent retorna resultado da extração de personagens/pistas
- **WHEN** o subagent `analyze-characters-clues` conclui e retorna
- **THEN** o agente principal exibe o resumo de quantidades e nomes de personagens/pistas, obtém confirmação do usuário via AskUserQuestion e, após confirmar, avança para a próxima etapa

#### Scenario: Usuário rejeita o resultado do subagent
- **WHEN** o usuário não está satisfeito com o resultado de uma etapa
- **THEN** o agente principal pode re-despachar o mesmo subagent (com o feedback do usuário) ou permitir edição manual antes de continuar

#### Scenario: Usuário escolhe pular uma etapa
- **WHEN** o usuário declara explicitamente pular a etapa atual
- **THEN** o agente principal pula essa etapa e vai direto para a próxima

### Requirement: A skill de orquestração deve suportar pontos de entrada flexíveis

manga-workflow SHALL permitir iniciar a execução em qualquer etapa, sem forçar o início do zero.

#### Scenario: Usuário só quer design de personagens
- **WHEN** o usuário pede "analisar personagens do romance" sem precisar criar roteiro
- **THEN** o agente principal despacha apenas o subagent `analyze-characters-clues` e, ao concluir, não avança automaticamente para a próxima etapa

#### Scenario: Usuário já tem personagens e quer criar roteiro diretamente
- **WHEN** project.json já tem definições de personagens/pistas e o usuário pede para criar o roteiro de um episódio
- **THEN** a skill de orquestração pula a etapa de extração de personagens/pistas e entra diretamente no pré-processamento de episódio

#### Scenario: Usuário quer retomar o trabalho interrompido
- **WHEN** o usuário executa /manga-workflow e o projeto tem trabalho parcialmente concluído
- **THEN** a skill de orquestração localiza automaticamente a etapa em que parou via detecção de estado e continua a partir dali

### Requirement: A skill de orquestração deve repassar o contexto correto ao subagent

Ao despachar um subagent, o agente principal SHALL repassar apenas o contexto mínimo necessário à tarefa (caminhos de arquivo e parâmetros-chave), e não blocos grandes de conteúdo bruto.

#### Scenario: Despachar subagent de extração de personagens/pistas
- **WHEN** o agente principal despacha `analyze-characters-clues`
- **THEN** repassa nome do projeto, caminho do diretório source e lista de nomes de personagens/pistas já existentes; o subagent lê o romance sozinho

#### Scenario: Despachar subagent de pré-processamento de episódio
- **WHEN** o agente principal despacha o subagent de pré-processamento
- **THEN** repassa nome do projeto, número do episódio, content_mode e lista de nomes de personagens/pistas; o subagent lê o trecho correspondente do romance sozinho

### Requirement: Etapa de geração de ativos chama skill via subagent

Skills de geração (generate-characters, generate-clues, generate-storyboard, generate-video) SHALL ser chamadas via subagent, e não diretamente pelo agente principal.

#### Scenario: Gerar imagens de design de personagens
- **WHEN** a orquestração entra na etapa de design de personagens
- **THEN** o agente principal despacha um subagent; o subagent chama internamente o script generate_character.py via Bash e retorna o resumo do resultado

#### Scenario: Gerar storyboards em lote
- **WHEN** a orquestração entra na etapa de geração de storyboards
- **THEN** o agente principal despacha um subagent; o subagent chama internamente o script generate_storyboard.py, processa todos os storyboards pendentes e retorna o resumo de sucessos/falhas
