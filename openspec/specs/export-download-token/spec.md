## ADDED Requirements

### Requirement: Emitir download token
O sistema SHALL fornecer o endpoint `POST /api/v1/projects/{name}/export/token` para emitir um token de download de curta duração a usuários autenticados.

Esse token é um JWT (HS256); o payload SHALL conter:
- `sub`: nome de usuário atual
- `project`: nome do projeto solicitado
- `purpose`: valor fixo `"download"`
- `exp`: horário de emissão + 300 segundos (5 minutos)

O endpoint SHALL retornar JSON: `{ "download_token": "<jwt>", "expires_in": 300 }`.

#### Scenario: Usuário autenticado obtém download token com sucesso
- **WHEN** um usuário autenticado chama `POST /api/v1/projects/{name}/export/token` para um projeto existente
- **THEN** o sistema retorna 200, com corpo contendo a string `download_token` e `expires_in: 300`

#### Scenario: Usuário não autenticado solicita download token
- **WHEN** uma requisição sem Bearer JWT válido chama `POST /api/v1/projects/{name}/export/token`
- **THEN** o sistema retorna 401

#### Scenario: Solicitar download token de projeto inexistente
- **WHEN** um usuário autenticado chama `POST /api/v1/projects/{name}/export/token` para um projeto inexistente
- **THEN** o sistema retorna 404

### Requirement: Endpoint de exportação autentica via download token
O endpoint de exportação `GET /api/v1/projects/{name}/export` SHALL usar o query param `download_token` como único modo de autenticação (obrigatório), validado pelo próprio endpoint, sem depender do header `Authorization`.

Regras de validação (`verify_download_token`):
- o campo `purpose` do token MUST ser `"download"`
- o campo `project` do token MUST coincidir com `{name}` na URL
- o token MUST não estar expirado

#### Scenario: Exportar com download token válido
- **WHEN** a requisição carrega um `download_token` query param válido ao acessar o endpoint de exportação
- **THEN** o sistema retorna normalmente o arquivo ZIP, sem necessidade de Authorization header

#### Scenario: Exportar com download token expirado
- **WHEN** a requisição carrega um `download_token` query param já expirado
- **THEN** o sistema retorna 401, com detail "O link de download expirou; exporte novamente"

#### Scenario: Exportar com download token de outro projeto
- **WHEN** a requisição carrega um `download_token` (emitido para o projeto A) ao acessar o endpoint de exportação do projeto B
- **THEN** o sistema retorna 403, com detail "O download token não corresponde ao projeto de destino"

#### Scenario: Falta download token
- **WHEN** a requisição acessa o endpoint de exportação sem o query param `download_token`
- **THEN** o sistema retorna 422 (query param obrigatório ausente)
