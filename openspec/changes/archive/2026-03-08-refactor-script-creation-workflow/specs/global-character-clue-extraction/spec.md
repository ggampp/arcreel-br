## ADDED Requirements

### Requirement: Extração de personagens/pistas deve suportar modo de análise do livro inteiro

O subagent `analyze-characters-clues` SHALL suportar analisar o romance completo e extrair de uma vez todos os personagens e pistas.

#### Scenario: Analisar o romance inteiro
- **WHEN** o subagent é despachado sem escopo de análise especificado
- **THEN** o subagent lê todos os textos em `projects/{project_name}/source/`, extrai todos os personagens e pistas e grava em project.json

#### Scenario: Analisar intervalo de capítulos especificado
- **WHEN** o subagent é despachado com escopo especificado (ex.: "capítulos 1–3" ou "um arquivo")
- **THEN** o subagent analisa apenas o texto nesse intervalo e extrai personagens e pistas dessa parte

### Requirement: Extração de personagens/pistas deve suportar modo de acréscimo incremental

Quando project.json já tem personagens/pistas, o subagent SHALL comparar com os dados existentes e apenas acrescentar personagens e pistas novos descobertos, sem sobrescrever definições existentes.

#### Scenario: Acrescentar novos personagens com lista já existente
- **WHEN** project.json já tem 5 definições de personagem e o subagent descobre 3 novos
- **THEN** o subagent apenas acrescenta os 3 novos em project.json, preservando os 5 originais

#### Scenario: Descrições de personagens existentes não são sobrescritas
- **WHEN** um personagem em project.json já tem description ou character_sheet editados manualmente
- **THEN** o subagent não sobrescreve esses dados e apenas marca no resumo retornado "já existe, ignorado"

### Requirement: Resultado da extração de personagens deve seguir normas de geração de imagem

As descrições extraídas de personagens SHALL conter apenas informações visuais utilizáveis diretamente na geração de imagem.

#### Scenario: Descrição do personagem só com elementos visuais
- **WHEN** o subagent extrai informações do personagem
- **THEN** o campo description inclui pontos de aparência, roupa, marcos distintivos, palavras-chave de cor e estilo de referência, sem personalidade, relações ou enredo

#### Scenario: voice_style registrado separadamente
- **WHEN** o romance descreve voz/tom do personagem
- **THEN** o subagent registra a informação de voz em voice_style (referência para dublagem posterior), separada da descrição visual

### Requirement: Extração de pistas deve distinguir tipo e importância

As pistas extraídas SHALL marcar tipo (location/prop) e importância (major/minor).

#### Scenario: Pistas de ambiente marcadas como location
- **WHEN** a pista é um ambiente/cena (ex.: "fundo do bambuzal", "salão da estalagem")
- **THEN** o type da pista é "location", com descrição de estrutura espacial e atmosfera de luz

#### Scenario: Pistas de objeto marcadas como prop
- **WHEN** a pista é um item/prop (ex.: "pingente de jade", "carta")
- **THEN** o type da pista é "prop", com descrição de referência de tamanho, material e detalhes de aparência

#### Scenario: Pistas importantes marcadas como major
- **WHEN** a pista reaparece no enredo ou tem papel-chave
- **THEN** importance é "major" (depois gerará imagem de design)

#### Scenario: Pistas secundárias marcadas como minor
- **WHEN** a pista aparece só ocasionalmente ou é decoração de fundo
- **THEN** importance é "minor" (só mantém a descrição, sem gerar imagem de design)

### Requirement: Resultados da extração devem passar validação de dados

Após gravar em project.json, o subagent SHALL chamar validação de dados para garantir integridade.

#### Scenario: Chamar validate_project
- **WHEN** o subagent termina a gravação de personagens/pistas
- **THEN** o subagent chama `validate_project(project_name)` para validar estrutura e integridade de referências de project.json

#### Scenario: Corrigir em caso de falha na validação
- **WHEN** validate_project retorna falha
- **THEN** o subagent corrige os dados com base nos erros e revalida até passar

### Requirement: Subagent deve retornar resumo estruturado

O resultado retornado por `analyze-characters-clues` ao agente principal SHALL ser um resumo estruturado enxuto, sem o texto original do romance.

#### Scenario: Retornar resumo de personagens
- **WHEN** o subagent conclui a extração de personagens
- **THEN** o retorno inclui: quantidade de personagens novos, lista de nomes e descrição de uma frase por personagem

#### Scenario: Retornar resumo de pistas
- **WHEN** o subagent conclui a extração de pistas
- **THEN** o retorno inclui: quantidade de pistas novas, distribuição major/minor, lista de nomes e tipos das pistas
