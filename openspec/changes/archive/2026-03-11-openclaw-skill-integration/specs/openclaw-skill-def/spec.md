## ADDED Requirements

### Requirement: Renderização dinâmica do arquivo de definição da Skill
O sistema SHALL fornecer o endpoint `GET /skill.md`, lendo o template `public/skill.md.template`, substituindo o placeholder `{{BASE_URL}}` pela base URL real do solicitante (inferida do header `Host` e do scheme) e retornando o conteúdo renderizado, sem autenticação.

#### Scenario: Acessar skill.md
- **WHEN** qualquer cliente solicita `GET /skill.md`
- **THEN** o sistema retorna o arquivo de definição da Skill renderizado, com todos os `{{BASE_URL}}` substituídos pelo endereço real do serviço (ex.: `https://my-arcreel.example.com`)

#### Scenario: Diferentes endereços de deploy
- **WHEN** o usuário faz self-host em `http://192.168.1.100:1241` e acessa `/skill.md`
- **THEN** as API URLs no arquivo retornado são `http://192.168.1.100:1241/api/v1/...`

### Requirement: Descrição do fluxo de trabalho da Skill
skill.md SHALL descrever o fluxo completo de uso: criar projeto → salvar configurações → múltiplas rodadas de conversa com o Agent → visualizar resultados.

#### Scenario: OpenClaw lê o fluxo de trabalho
- **WHEN** o Agent OpenClaw carrega skill.md
- **THEN** pode obter a sequência completa de chamadas de API e a documentação de parâmetros

### Requirement: Definição das ferramentas da Skill
skill.md SHALL definir as seguintes ferramentas centrais, com endpoints de API e formatos de requisição/resposta:
- Criar projeto (`POST /api/v1/projects`)
- Obter/atualizar configurações do projeto (`GET/PATCH /api/v1/projects/{name}`)
- Conversa com o Agent (`POST /api/v1/agent/chat`)
- Lista de projetos (`GET /api/v1/projects`)
- Detalhe do projeto (`GET /api/v1/projects/{name}`)

#### Scenario: Completude das definições de ferramenta
- **WHEN** o Agent OpenClaw interpreta as definições de ferramenta em skill.md
- **THEN** cada ferramenta SHALL incluir caminho do endpoint, método HTTP, descrição dos parâmetros de requisição e exemplo de formato de resposta

### Requirement: Instruções de autenticação
skill.md SHALL explicar o modo de autenticação: o usuário obtém a API Key (prefixo `arc-`) na página de configurações do ArcReel e a envia via `Authorization: Bearer <API_KEY>`.

#### Scenario: Usuário configura autenticação conforme as instruções
- **WHEN** o usuário segue as instruções de autenticação em skill.md
- **THEN** consegue chamar com sucesso todos os endpoints de API definidos pela Skill

### Requirement: Modal de guia de uso do OpenClaw
A barra superior da página do hall de projetos no frontend SHALL oferecer o botão 🦞 OpenClaw; o clique abre um Modal de instruções de uso.

#### Scenario: Abrir o modal de guia
- **WHEN** o usuário clica no botão 🦞 OpenClaw na barra superior
- **THEN** abre um Modal contendo: prompt copiável (com URL dinâmica de skill.md), instruções de uso em 4 passos e botão "Obter token de API"

#### Scenario: URL no prompt se adapta dinamicamente
- **WHEN** o usuário acessa em `http://localhost:1241` e abre o modal de guia
- **THEN** a URL no prompt é `http://localhost:1241/skill.md`

#### Scenario: Obter token de API
- **WHEN** o usuário clica no botão "Obter token de API"
- **THEN** navega para a página de gerenciamento de API Keys
