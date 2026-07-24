## Context

O ArcReel usa autenticação OAuth2 Bearer JWT; todos os endpoints de API são validados pela dependência `get_current_user`. O frontend obtém o JWT em `/auth/token` e as requisições seguintes carregam `Authorization: Bearer <jwt>`.

Plataformas externas como OpenClaw precisam de API Keys de longa duração para chamar a API do ArcReel, em vez de JWT de curta duração. Além disso, a conversa do assistente atual é stream SSE; Agents externos precisam de interface síncrona request-response.

## Goals / Non-Goals

**Goals:**
- Adicionar modo de autenticação por API Key ao sistema existente, coexistindo com JWT
- Reutilizar os endpoints de API atuais, sem criar uma camada separada de "API pública"
- Fornecer endpoint síncrono de conversa com o Agent para chamadas externas
- Escrever skill.md no padrão OpenClaw AgentSkill

**Non-Goals:**
- Não implementar multi-usuário / multi-tenant (manter modo single-user)
- Não implementar rate limit de chamadas de API (iteração futura)
- Não implementar controle de escopo de permissões por API Key (todas as keys têm permissão completa)
- Não refatorar caminhos ou formatos de parâmetros dos endpoints existentes

## Decisions

### 1. Formato e armazenamento da API Key

**Decisão**: prefixo `arc-` + 32 caracteres aleatórios; o banco só guarda o hash SHA-256.

Formato: `arc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (36 caracteres)

**Justificativa**: o prefixo facilita o reconhecimento pelo usuário e serve de critério de bifurcação na autenticação; o hash garante que um vazamento do banco não exponha a key original. Referência ao padrão Zopia `zopia-xxxxxxxxxxxx`.

### 2. Forma de remodelar a camada de autenticação

**Decisão**: alterar `_verify_and_get_payload` em `server/auth.py`, decidindo o modo de autenticação pelo prefixo `arc-`.

Fluxo:
1. Extrair o Bearer token
2. Verificar se o token começa com `arc-`
3. **Sim → caminho API Key**: calcular hash SHA-256 → consultar o banco → em sucesso retornar `{"sub": "apikey:<key_name>", "via": "apikey"}`
4. **Não → caminho JWT**: decodificar e validar JWT → em sucesso retornar o payload
5. Qualquer caminho falhando → retornar 401

**Justificativa**: a decisão por prefixo é determinística e evita tentativas desnecessárias de decode JWT. Mudança mínima; todos os endpoints existentes ganham suporte a API Key automaticamente.

**Alternativas**: middleware de autenticação separado (mais mudanças); prefixo de rota independente (viola o princípio de reutilização).

### 3. Endpoint síncrono de conversa com o Agent

**Decisão**: novo endpoint `POST /api/v1/agent/chat`; por dentro cria sessão temporária → envia mensagem → coleta o stream SSE até concluir → retorna a resposta completa.

Corpo da requisição:
```json
{
  "project_name": "my-project",
  "message": "Me ajude a escrever um roteiro de suspense",
  "session_id": null  // opcional; se informado, reutiliza a sessão
}
```

Corpo da resposta:
```json
{
  "session_id": "xxx",
  "reply": "Certo, vou te ajudar...",
  "status": "completed"
}
```

**Justificativa**: referência ao design `/api/v1/agent/chat` do Zopia; Agents externos como OpenClaw não suportam SSE e precisam de interface síncrona. Reutiliza AssistantService por dentro.

### 4. Local do gerenciamento de API Key

**Decisão**: backend com `server/routers/api_keys.py` novo; frontend com tab "API Keys" na página de configurações.

Modelo de banco `ApiKey`:
- `id`: chave primária
- `name`: nome definido pelo usuário
- `key_hash`: hash SHA-256
- `key_prefix`: primeiros 8 caracteres (`arc-xxxx`) para exibição na lista
- `created_at`: horário de criação
- `expires_at`: horário de expiração (opcional, padrão 30 dias)
- `last_used_at`: último uso

**Justificativa**: alinhado ao ORM existente; reutiliza SQLAlchemy async + migration Alembic.

### 5. Serviço dinâmico de skill.md

**Decisão**: skill.md fica como template em `public/skill.md.template`, com placeholder `{{BASE_URL}}` nas API URLs. A rota FastAPI `GET /skill.md` renderiza dinamicamente: infere a base URL real a partir do header `Host` e do scheme, substitui o placeholder e retorna.

**Justificativa**: o projeto é self-hosted; domínio/porta de cada usuário é diferente; as API URLs em skill.md precisam se adaptar. Arquivo estático não resolve.

**Alternativas**: o usuário preenche a base URL manualmente (mais atrito); geração no frontend (OpenClaw precisa obter direto do servidor).

### 6. Modal de guia de uso do OpenClaw no frontend

**Decisão**: botão 🦞 OpenClaw na barra superior do hall de projetos; o clique abre um Modal de instruções com:
- Prompt (copiável): `Aprenda https://<domain>/skill.md e siga a skill; crie vídeos livremente`
- Passos de uso (4)
- Botão "Obter token de API" (navega para o gerenciamento de API Keys)

A URL no prompt do modal também é substituída dinamicamente pelo endereço atual de acesso.

**Justificativa**: referência ao guia do Zopia; reduz o custo de compreensão para o usuário.

## Risks / Trade-offs

- **[Performance]** Cada requisição com API Key consulta o banco → cache em memória (LRU, TTL 5 minutos) para reduzir a carga
- **[Segurança]** API Key de longa duração → expiração padrão de 30 dias + revogação manual
- **[Compatibilidade]** O endpoint síncrono de conversa pode dar timeout → timeout de resposta razoável (120 s); em timeout retornar resposta parcial
- **[Single-user]** API Key não distingue usuários → aceitável no modo single-user atual; multi-usuário exigiria extensão
