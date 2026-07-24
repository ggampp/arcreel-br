## Context

O diálogo AgentCopilot hoje só aceita entrada de texto puro. A assinatura de `ClaudeSDKClient.query()` do Claude Agent SDK é `str | AsyncIterable[dict]`; o caminho AsyncIterable permite passar content multimodal completo (blocos de texto + imagem). O `send_message` do backend hoje só usa o caminho `str`; as camadas Service / SessionManager / Router não conhecem imagens.

## Goals / Non-Goals

**Goals:**
- O usuário pode anexar imagens no diálogo por colar (Ctrl+V), upload por clique ou arrastar e soltar
- As imagens são enviadas inline em base64 junto com a mensagem ao Agent
- Após o envio, o balão e o replay do histórico renderizam as imagens corretamente

**Non-Goals:**
- Referência por URL de imagem (exigiria fetch extra no backend; fora deste ciclo)
- Compressão ou conversão de formato de imagem no servidor
- Modal de pré-visualização em tela cheia de imagens (coberto depois pelo lightbox no frontend)

## Decisions

### Decisão 1: Forma de transmissão da imagem — Base64 inline no JSON

**Escolha**: base64 da imagem embutido em `SendMessageRequest.images[]`, em uma única requisição.

**Alternativa**: POST multipart primeiro para obter ID temporário e referenciar na mensagem.

**Motivo**: sem endpoint novo de upload; menor mudança no frontend e backend; requisição sem estado, sem gestão de ciclo de vida de arquivo temporário. Limite de 5 imagens × 5MB; body JSON no máximo ~33MB, aceitável.

---

### Decisão 2: Camada de integração com o SDK — encapsulamento no Service

**Escolha**: `AssistantService.send_message()` monta `content + images` em AsyncGenerator e passa ao SessionManager; o SessionManager só conhece `str | AsyncIterable[dict]`, sem entender a estrutura de imagem.

**Alternativa A**: serializar na camada Router (camada mais externa).  
**Alternativa B**: tratar dentro do SessionManager (camada mais interna).

**Motivo**: Service é a camada de lógica de negócio; Router faz validação de borda HTTP; SessionManager gerencia a comunicação com o SDK — divisão de responsabilidades clara. O Service centraliza a formatação do conteúdo, facilitando testes e extensões futuras.

---

### Decisão 3: Separar echo_text e sdk_prompt

**Escolha**: `SessionManager.send_message()` ganha o parâmetro `echo_text` para exibição no balão do usuário; o parâmetro `prompt` recebe o sdk_prompt (pode ser str ou AsyncGenerator).

**Motivo**: o balão do usuário só precisa da parte de texto; AsyncGenerator não pode ser consumido duas vezes e não serve ao mesmo tempo para o SDK e para a construção do echo. Separar evita acoplamento.

## Risks / Trade-offs

- **Volume do body JSON**: 5 imagens de 5MB em base64 ficam em cerca de 33MB. Validar tamanho no frontend (≤ 5MB/imagem) para evitar 413. Recomenda-se também configurar `max_body_size` no FastAPI do backend.  
  → Mitigação: interceptação no frontend + limite no backend.

- **Mensagem echo com base64 da imagem**: `_build_user_echo_message` guarda o base64 completo no message_buffer, elevando o uso de memória.  
  → Mitigação: o buffer já tem mecanismo de prune; mensagens echo são desduplicadas e limpas após confirmação no transcript.

- **normalize_block e passagem de image block**: `turn_schema.normalize_block` faz deepcopy de types desconhecidos e não perde dados; se no futuro houver whitelist de tipos, é preciso incluir `"image"` em sincronia.

## Migration Plan

Só adições, sem migração de dados. Deploy independente de frontend e backend permanece compatível:
- Frontend antigo não envia o campo `images` → backend trata `images` como lista vazia padrão e segue o caminho original
- Frontend novo envia `images` → precisa de backend novo; deploy sincronizado

## Open Questions

- Registrar explicitamente o type `"image"` em `normalize_block` (adicionar `elif block_type == "image": pass`) ou confiar no deepcopy atual? Recomenda-se registro explícito por legibilidade; não afeta a função.
