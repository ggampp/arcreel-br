## ADDED Requirements

### Requirement: Geração de API Key
O sistema SHALL fornecer uma interface de criação de API Key, gerando chaves no formato `arc-` + 32 caracteres aleatórios, retornando a chave completa (visível apenas na criação), e armazenando no banco apenas o hash SHA-256.

#### Scenario: Criar API Key com sucesso
- **WHEN** um usuário autenticado chama `POST /api/v1/api-keys` fornecendo o parâmetro `name`
- **THEN** o sistema retorna uma resposta contendo `key` completo, `name`, `key_prefix`, `created_at`, `expires_at`, com status 201

#### Scenario: Nome duplicado na criação
- **WHEN** um usuário autenticado cria uma API Key com o mesmo nome de uma chave existente
- **THEN** o sistema retorna erro 409

### Requirement: Listagem de API Keys
O sistema SHALL fornecer uma interface de listagem de API Keys, retornando metadados de todas as chaves (sem a chave completa).

#### Scenario: Consultar lista de API Keys
- **WHEN** um usuário autenticado chama `GET /api/v1/api-keys`
- **THEN** o sistema retorna `id`, `name`, `key_prefix`, `created_at`, `expires_at`, `last_used_at` de todas as chaves

### Requirement: Exclusão (revogação) de API Key
O sistema SHALL fornecer uma interface de exclusão de API Key, invalidando imediatamente a chave.

#### Scenario: Excluir API Key com sucesso
- **WHEN** um usuário autenticado chama `DELETE /api/v1/api-keys/{key_id}`
- **THEN** o sistema remove o registro da chave; requisições subsequentes com essa chave retornam 401

#### Scenario: Excluir key inexistente
- **WHEN** um usuário autenticado tenta excluir um `key_id` inexistente
- **THEN** o sistema retorna 404

### Requirement: Bifurcação de autenticação Bearer Token
O sistema SHALL, em `_verify_and_get_payload`, determinar o modo de autenticação pelo prefixo do token: tokens com prefixo `arc-` seguem o caminho de validação de API Key; caso contrário, seguem o caminho de validação JWT.

#### Scenario: Autenticação por API Key bem-sucedida
- **WHEN** a requisição carrega `Authorization: Bearer arc-xxxxx` e a chave existe no banco e não está expirada
- **THEN** o sistema retorna o payload `{"sub": "apikey:<key_name>", "via": "apikey"}` e atualiza `last_used_at`

#### Scenario: API Key expirada
- **WHEN** a requisição carrega uma API Key com formato válido, mas já passou de `expires_at`
- **THEN** o sistema retorna 401

#### Scenario: API Key inexistente
- **WHEN** a requisição carrega um token com prefixo `arc-`, mas o hash não corresponde a nenhum registro no banco
- **THEN** o sistema retorna 401

#### Scenario: Autenticação JWT não é afetada
- **WHEN** a requisição carrega um Bearer token que não começa com `arc-`
- **THEN** o sistema processa pelo fluxo original de validação JWT

### Requirement: Cache de API Key
O sistema SHALL usar cache em memória (LRU, TTL 5 minutos) para resultados de consulta de API Key, reduzindo consultas ao banco.

#### Scenario: Cache hit
- **WHEN** a mesma API Key é usada em múltiplas requisições dentro de 5 minutos
- **THEN** apenas a primeira dispara consulta ao banco; as seguintes leem do cache

#### Scenario: Cache invalidado após exclusão da Key
- **WHEN** uma API Key é excluída
- **THEN** a entrada de cache dessa chave SHALL ser limpa imediatamente
