## Why

O diálogo de conversa hoje só aceita entrada de texto puro; o usuário não consegue passar imagens diretamente ao AI Agent para análise (imagens de referência, capturas de tela, rascunhos de storyboard etc.). Para o Agent auxiliar a criação com base em conteúdo visual, o diálogo precisa suportar entrada de imagens.

## What Changes

- Nova função de anexo de imagens na área de entrada do diálogo: upload por clique, arrastar e soltar, colar (Ctrl+V)
- A área de entrada exibe miniatura das imagens pendentes de envio, com remoção individual
- No envio, as imagens vão junto com o texto para o backend, que repassa ao Agent (forma concreta de transmissão a confirmar no brainstorm)
- A API de backend é estendida para mensagens que carregam dados de imagem

## Capabilities

### New Capabilities

- `chat-image-attachment`: anexos de imagem no diálogo — coleta, pré-visualização e remoção no frontend; no envio, merge com o texto; o backend recebe e repassa ao Agent

### Modified Capabilities

- `sync-agent-chat`: a interface de envio de mensagem precisa aceitar dados de imagem anexados (formato concreto a definir)

## Impact

- **Frontend**: interação da área de entrada em `AgentCopilot.tsx`, assinatura de `sendMessage` no hook `useAssistantSession`
- **API de backend**: `server/routers/assistant.py` — `SendMessageRequest` ganha campo de imagens
- **Serviços de backend**: `server/agent_runtime/service.py`, `session_manager.py` — lógica de construção da mensagem
- **Dependências**: File API nativa do navegador; solução no lado do Claude SDK a avaliar
