## ADDED Requirements

### Requirement: Extração de ativos deve suportar modo de análise do livro inteiro

O subagent `analyze-assets` SHALL suportar analisar o romance completo e extrair de uma vez todos os personagens / cenas / props.

#### Scenario: Analisar o romance inteiro
- **WHEN** o subagent é despachado sem escopo de análise especificado
- **THEN** o subagent lê todos os textos em `projects/{project_name}/source/`, extrai todos os personagens / cenas / props e grava em project.json

#### Scenario: Analisar intervalo de capítulos especificado
- **WHEN** o subagent é despachado com escopo especificado (ex.: "capítulos 1–3" ou "um arquivo")
- **THEN** o subagent analisa apenas o texto nesse intervalo e extrai personagens / cenas / props dessa parte

### Requirement: Extração de ativos deve suportar modo de acréscimo incremental

Quando project.json já tem personagens / cenas / props, o subagent SHALL comparar com os dados existentes e apenas acrescentar ativos novos descobertos, sem sobrescrever definições existentes.

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

### Requirement: Cenas e props extraídos por tipo de ativo

Ambientes / objetos extraídos SHALL ser classificados como cena (scene) ou prop, gravados nas coleções correspondentes de project.json.

#### Scenario: Ambientes extraídos como ativo scene
- **WHEN** o objeto é um ambiente/cena (ex.: "fundo do bambuzal", "salão da estalagem")
- **THEN** é gravado na coleção scenes, com descrição de estrutura espacial e atmosfera de luz

#### Scenario: Objetos extraídos como ativo prop
- **WHEN** o objeto é um item/prop (ex.: "pingente de jade", "carta")
- **THEN** é gravado na coleção props, com descrição de referência de tamanho, material e detalhes de aparência

### Requirement: Resultados da extração devem passar validação de dados

Após gravar em project.json, o subagent SHALL chamar validação de dados para garantir integridade.

#### Scenario: Chamar validate_project
- **WHEN** o subagent termina a gravação de personagens / cenas / props
- **THEN** o subagent chama `validate_project(project_name)` para validar estrutura e integridade de referências de project.json

#### Scenario: Corrigir em caso de falha na validação
- **WHEN** validate_project retorna falha
- **THEN** o subagent corrige os dados com base nos erros e revalida até passar

### Requirement: Subagent deve retornar resumo estruturado

O resultado retornado por `analyze-assets` ao agente principal SHALL ser um resumo estruturado enxuto, sem o texto original do romance.

#### Scenario: Retornar resumo de personagens
- **WHEN** o subagent conclui a extração de personagens
- **THEN** o retorno inclui: quantidade de personagens novos, lista de nomes e descrição de uma frase por personagem

#### Scenario: Retornar resumo de cenas e props
- **WHEN** o subagent conclui a extração de cenas / props
- **THEN** o retorno inclui: quantidade de cenas novas, quantidade de props novos e listas de nomes de cada um
