## ADDED Requirements

### Requirement: Endpoint síncrono de conversa com o Agent
O sistema SHALL fornecer o endpoint síncrono `POST /api/v1/agent/chat`, recebendo a mensagem do usuário e retornando a resposta completa do Agent.

#### Scenario: Conversa em nova sessão
- **WHEN** um usuário autenticado chama `POST /api/v1/agent/chat` com `project_name` e `message`, sem `session_id`
- **THEN** o sistema cria uma nova sessão, executa a conversa com o Agent e retorna `session_id`, `reply` (texto completo) e `status: "completed"`

#### Scenario: Reutilizar sessão existente
- **WHEN** um usuário autenticado chama o endpoint com um `session_id` válido
- **THEN** o sistema continua a conversa no contexto dessa sessão e retorna a resposta

#### Scenario: Projeto inexistente
- **WHEN** o `project_name` fornecido não corresponde a um projeto existente
- **THEN** o sistema retorna 404

#### Scenario: Timeout da resposta
- **WHEN** o processamento do Agent ultrapassa 120 segundos
- **THEN** o sistema retorna a resposta parcial já coletada, com `status` igual a `"timeout"`

### Requirement: Formato do conteúdo da conversa
A resposta SHALL conter a resposta em texto puro gerada pelo Agent, sem detalhes internos de chamadas de ferramentas, apenas o conteúdo voltado ao usuário.

#### Scenario: Resposta após o Agent usar ferramentas
- **WHEN** o Agent chama ferramentas por dentro (ex.: gerar roteiro) e produz uma resposta em texto
- **THEN** o campo `reply` da resposta contém apenas o texto voltado ao usuário, sem expor detalhes de chamada de ferramentas
