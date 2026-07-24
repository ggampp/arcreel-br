## ADDED Requirements

### Requirement: Endpoint de exportação suporta parâmetro scope
O endpoint de exportação `GET /api/v1/projects/{name}/export` SHALL aceitar o query param `scope` com valor `full` ou `current`, padrão `full`.

- `scope=full`: empacota todos os arquivos do diretório do projeto (comportamento existente)
- `scope=current`: ignora arquivos históricos sob `versions/`, mantendo apenas um `versions/versions.json` recortado

#### Scenario: Scope padrão é full
- **WHEN** a requisição de exportação não carrega o parâmetro scope
- **THEN** o sistema empacota no modo `full`; o ZIP inclui todos os arquivos históricos sob `versions/`

#### Scenario: scope=full exporta todos os dados
- **WHEN** a requisição de exportação carrega `scope=full`
- **THEN** o ZIP inclui todos os arquivos do diretório do projeto (incluindo o conteúdo completo de `versions/`), igual ao comportamento existente

#### Scenario: scope=current ignora arquivos de versão histórica
- **WHEN** a requisição de exportação carrega `scope=current`
- **THEN** o ZIP não inclui nenhum arquivo sob `versions/storyboards/`, `versions/videos/`, `versions/characters/`, `versions/scenes/`, `versions/props/`, `versions/reference_videos/`

#### Scenario: Valor de scope inválido
- **WHEN** a requisição de exportação carrega `scope=invalid`
- **THEN** o sistema retorna 422, indicando que scope deve ser `full` ou `current`

### Requirement: Exportação só da versão atual preserva metadados de versão recortados
Quando `scope=current`, o ZIP SHALL incluir o arquivo `versions/versions.json`, com conteúdo recortado: o array `versions` de cada recurso mantém apenas o registro correspondente a `current_version`.

O `versions.json` recortado preserva os seguintes metadados:
- número de `current_version`
- `prompt` da versão atual (prompt de geração)
- `created_at` da versão atual
- número de `version` da versão atual

#### Scenario: versions.json recortado contém só o registro da versão atual
- **WHEN** o storyboard E1S01 do projeto tem 3 versões (current_version=3) e a exportação usa `scope=current`
- **THEN** em `versions/versions.json` no ZIP, o array `storyboards.E1S01.versions` contém apenas o registro da version 3, e `current_version` continua 3

#### Scenario: versions.json recortado preserva o prompt de geração
- **WHEN** a exportação usa `scope=current` e a versão atual tem metadados de prompt
- **THEN** no `versions/versions.json` recortado, o campo `prompt` do registro da versão atual é preservado

### Requirement: Manifesto de exportação marca o scope
O manifesto `arcreel-export.json` SHALL incluir o campo `scope` com valor `"full"` ou `"current"`, refletindo o escopo real da exportação.

#### Scenario: Manifesto de exportação full tem scope full
- **WHEN** a exportação usa `scope=full`
- **THEN** o campo `scope` em `arcreel-export.json` tem valor `"full"`

#### Scenario: Manifesto de exportação current tem scope current
- **WHEN** a exportação usa `scope=current`
- **THEN** o campo `scope` em `arcreel-export.json` tem valor `"current"`

### Requirement: Interação de exportação no frontend suporta seleção de escopo
O frontend SHALL, após o usuário clicar no botão de exportar, exibir um diálogo de seleção com duas opções:

- **Apenas versão atual** (recomendado): marcada como recomendada, indicando que não inclui histórico de versões e o volume é menor
- **Todos os dados**: indicando que inclui o histórico completo de versões

Após a escolha do usuário, o frontend SHALL, em sequência:
1. Chamar `POST /api/v1/projects/{name}/export/token` para obter o download token
2. Construir a URL de download: `/api/v1/projects/{name}/export?download_token=xxx&scope=yyy`
3. Disparar o download nativo do navegador via `window.open` ou tag `<a>`

#### Scenario: Usuário escolhe exportar apenas a versão atual
- **WHEN** o usuário clica em exportar e escolhe "Apenas versão atual"
- **THEN** o navegador inicia uma requisição nativa de download com `scope=current`, com progresso visível no gerenciador de downloads

#### Scenario: Usuário escolhe exportar todos os dados
- **WHEN** o usuário clica em exportar e escolhe "Todos os dados"
- **THEN** o navegador inicia uma requisição nativa de download com `scope=full`

#### Scenario: Usuário pode trocar de página durante a exportação
- **WHEN** o usuário dispara o download de exportação e navega para outra página
- **THEN** o download não é interrompido, pois o gerenciador nativo do navegador assume o controle

#### Scenario: Falha ao obter download token
- **WHEN** a requisição de obtenção do download token falha (erro de rede ou autenticação expirada)
- **THEN** o frontend exibe um toast de erro e não dispara o download
