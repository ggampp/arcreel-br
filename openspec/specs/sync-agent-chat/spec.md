## Requirements

### Requirement: Endpoint síncrono de conversa com o Agent
O sistema SHALL fornecer o endpoint síncrono `POST /api/v1/agent/chat`, recebendo a mensagem do usuário (com anexos de imagem opcionais) e retornando a resposta completa do Agent.

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

#### Scenario: Enviar mensagem com anexos de imagem
- **WHEN** um usuário autenticado chama `POST /api/v1/assistant/sessions/{id}/messages` com corpo contendo `content` (texto) e `images` (até 5 objetos de imagem em base64)
- **THEN** o sistema combina texto e imagens em mensagem multimodal para o Agent, que pode perceber o conteúdo das imagens e responder
