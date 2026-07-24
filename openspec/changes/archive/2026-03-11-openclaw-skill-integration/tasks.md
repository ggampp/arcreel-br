## 1. Camada de banco — modelo ApiKey e migration

- [x] 1.1 Criar o modelo ORM `lib/db/models/api_key.py` (id, name, key_hash, key_prefix, created_at, expires_at, last_used_at)
- [x] 1.2 Registrar o novo modelo em `lib/db/models/__init__.py`
- [x] 1.3 Gerar a migration Alembic e executar `alembic upgrade head`
- [x] 1.4 Criar `lib/db/repositories/api_key_repository.py` (CRUD + consulta por hash + atualização de last_used_at)

## 2. Remodelar a camada de autenticação — bifurcação API Key

- [x] 2.1 Alterar `_verify_and_get_payload` em `server/auth.py` para decidir o caminho API Key ou JWT pelo prefixo `arc-`
- [x] 2.2 Implementar a lógica de validação de API Key (hash SHA-256 → consultar o banco → checar expiração → retornar payload)
- [x] 2.3 Adicionar cache em memória LRU dos resultados de consulta de API Key (TTL 5 minutos)
- [x] 2.4 Escrever testes unitários da bifurcação de autenticação (API Key sucesso/expirada/inexistente; JWT não afetado)

## 3. Rotas de gerenciamento de API Key

- [x] 3.1 Criar `server/routers/api_keys.py` (POST criar, GET listar, DELETE excluir)
- [x] 3.2 Implementar a lógica de geração de API Key (`arc-` + 32 caracteres aleatórios, armazenamento com hash, retornar a key completa na criação)
- [x] 3.3 Registrar as rotas em `server/app.py`
- [x] 3.4 Limpar o cache ao excluir a key
- [x] 3.5 Escrever testes de integração dos endpoints de gerenciamento de API Key

## 4. Endpoint síncrono de conversa com o Agent

- [x] 4.1 Criar o endpoint `POST /api/v1/agent/chat` (criar ou reutilizar sessão → enviar mensagem → coletar a resposta completa)
- [x] 4.2 Integrar com AssistantService por dentro, coletando o stream de eventos SSE até concluir
- [x] 4.3 Implementar tratamento de timeout de 120 s; em timeout retornar resposta parcial + status: "timeout"
- [x] 4.4 Escrever testes do endpoint síncrono de conversa

## 5. Arquivo de definição da Skill e renderização dinâmica

- [x] 5.1 Criar `public/skill.md.template`, escrever a definição da Skill ArcReel no formato de referência Zopia, com placeholder `{{BASE_URL}}` nas API URLs
- [x] 5.2 Criar a rota `GET /skill.md` (sem autenticação), inferir a base URL a partir de Host/scheme da requisição, substituir o placeholder e retornar
- [x] 5.3 Validar que `GET /skill.md` retorna a URL dinâmica correta em diferentes endereços de deploy

## 6. Frontend — página de gerenciamento de API Key

- [x] 6.1 Adicionar o componente da tab "API Keys" na página de configurações
- [x] 6.2 Implementar a listagem de API Keys (nome, prefixo, criação, expiração, último uso)
- [x] 6.3 Implementar criação de API Key (modal mostra a key completa e avisa que é visível só desta vez)
- [x] 6.4 Implementar exclusão de API Key (modal de confirmação)

## 7. Frontend — modal de guia OpenClaw

- [x] 7.1 Adicionar o botão 🦞 OpenClaw na barra superior do hall de projetos
- [x] 7.2 Implementar o componente Modal de guia: área do prompt (copiável, com URL dinâmica de skill.md), instruções em 4 passos, botão "Obter token de API"
- [x] 7.3 A URL no prompt se adapta dinamicamente ao endereço atual de acesso (`window.location.origin`)
- [x] 7.4 O botão "Obter token de API" navega para a página de gerenciamento de API Keys
