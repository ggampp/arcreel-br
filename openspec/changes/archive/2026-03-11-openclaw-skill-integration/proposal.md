## Why

OpenClaw é uma das plataformas de AI Agent open source mais quentes de 2026 (247k+ stars no GitHub) e suporta extensão de capacidades via AgentSkill. Integrar o ArcReel com OpenClaw Skill permite que o usuário, por conversa em linguagem natural, chame criação de projeto, geração de roteiro, storyboard, vídeo etc., reduzindo a barreira de uso e ampliando canais de aquisição.

## What Changes

- Novo modo de autenticação por API Key: além do OAuth2 existente, adicionar `Authorization: Bearer <API_KEY>`, reutilizando os endpoints de API atuais
- Novo gerenciamento de API Key: página no frontend para gerar tokens; backend com interfaces CRUD
- Novo endpoint síncrono de conversa com o Agent: a API de assistente atual é stream SSE; é preciso um interface request-response síncrona para o OpenClaw
- Escrever o arquivo de definição AgentSkill do OpenClaw (`skill.md`), no formato de referência Zopia, descrevendo ferramentas e modos de chamada

## Capabilities

### New Capabilities

- `api-key-auth`: geração, gerenciamento e autenticação Bearer Token de API Key, como modo complementar ao sistema de autenticação existente
- `sync-agent-chat`: endpoint síncrono de conversa com o Agent, encapsulando o assistente SSE em modo request-response
- `openclaw-skill-def`: arquivo de definição de Skill no padrão OpenClaw AgentSkill, descrevendo o fluxo de trabalho e as APIs disponíveis

### Modified Capabilities

(não é necessário alterar as definições de requisitos das capabilities existentes; apenas compatibilizar o novo modo API Key na camada do middleware de autenticação)

## Impact

- **Camada de autenticação**: `get_current_user` em `server/routers/auth.py` precisa aceitar autenticação por API Key
- **Banco de dados**: novo modelo ORM `ApiKey` e migration
- **Rotas de backend**: novas rotas de gerenciamento de API Key e de conversa síncrona com o Agent
- **Frontend**: nova página de gerenciamento de API Key (área de configurações)
- **Raiz do projeto**: novo arquivo de definição `skill.md` para o OpenClaw ler
