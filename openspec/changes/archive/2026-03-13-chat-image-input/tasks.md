## 1. Camada de API do backend

- [x] 1.1 Em `server/routers/assistant.py`, adicionar o modelo Pydantic `ImageAttachment` (`data: str`, `media_type: str`)
- [x] 1.2 Em `SendMessageRequest`, adicionar `images: list[ImageAttachment] = Field(default_factory=list, max_length=5)`
- [x] 1.3 Na rota `send_message`, repassar `req.images` para `service.send_message()`

## 2. Camada Service do backend

- [x] 2.1 Na assinatura de `send_message` em `server/agent_runtime/service.py`, adicionar o parâmetro `images` (padrão `None`)
- [x] 2.2 Implementar o async generator `_build_multimodal_prompt(text, images)`, construindo o dict de mensagem do SDK com blocos text + image
- [x] 2.3 Com imagens, chamar `_build_multimodal_prompt` e obter o async generator; sem imagens, continuar passando str

## 3. Camada SessionManager do backend

- [x] 3.1 Na assinatura de `send_message` em `session_manager.py`, trocar `content: str` por `prompt: str | AsyncIterable[dict]` e adicionar o parâmetro `echo_text: str | None = None`
- [x] 3.2 A lógica de echo passa a usar `echo_text or (prompt if isinstance(prompt, str) else "")` como texto do balão
- [x] 3.3 `_build_user_echo_message` passa a aceitar lista de content blocks (incluindo blocos de imagem), para o balão imediato também exibir imagens

## 4. Camada de normalização do backend

- [x] 4.1 Em `normalize_block` de `server/agent_runtime/turn_schema.py`, adicionar explicitamente o ramo `elif block_type == "image": pass`, indicando passagem intencional do image block

## 5. Tipos do frontend

- [x] 5.1 Em `ContentBlock` type union de `frontend/src/types/assistant.ts`, adicionar `"image"`
- [x] 5.2 Na interface `ContentBlock`, adicionar o campo `source?: { type: "base64"; media_type: string; data: string }`

## 6. Renderização no frontend

- [x] 6.1 Em `ContentBlockRenderer.tsx`, adicionar o ramo `case "image"`, renderizando `<img src="data:..." className="max-w-full max-h-64 rounded-lg mt-1" />`

## 7. Hook do frontend

- [x] 7.1 Na assinatura de `sendMessage` em `useAssistantSession`, adicionar o parâmetro `images?: AttachedImage[]`
- [x] 7.2 Montar o corpo da requisição: mapear `images` para o array `{ data: dataUrl.split(",")[1], media_type: mimeType }`

## 8. UI do AgentCopilot no frontend

- [x] 8.1 Definir a interface `AttachedImage` (`id`, `dataUrl`, `mimeType`) e o state `attachedImages`
- [x] 8.2 Implementar `handlePaste`: ler itens `image/*` de `ClipboardEvent`, converter para base64 e adicionar à lista de anexos
- [x] 8.3 Implementar `handleDrop` + `handleDragOver`: ler imagens de `DataTransfer.files`, com destaque visual no arraste
- [x] 8.4 Implementar `handleFileSelect`: onChange de `<input type="file" multiple accept="image/*">` oculto
- [x] 8.5 Adicionar o botão 📎 ao lado do campo de entrada (dispara o file input); ligar `onPaste`, `onDrop`, `onDragOver` à área de entrada
- [x] 8.6 Implementar a barra de miniaturas: com `attachedImages` não vazio, renderizar miniaturas 64×64 acima do textarea + botão × de remoção no canto superior direito
- [x] 8.7 Com mais de 5 imagens, desabilitar o botão de anexo; com arquivo > 5MB, mostrar erro e recusar a adição
- [x] 8.8 `handleSend` chama `sendMessage(text, attachedImages)` e, após o envio, executa `setAttachedImages([])`

## 9. Ampliação de imagem (Lightbox)

- [x] 9.1 Criar o componente `ImageLightbox.tsx`: máscara em tela cheia com a imagem original; clique na máscara ou Esc fecha
- [x] 9.2 Em `case "image"` de `ContentBlockRenderer.tsx`, a imagem ganha `cursor-pointer` e o clique abre o lightbox
- [x] 9.3 Nas miniaturas de anexo de `AgentCopilot.tsx`, o clique abre o mesmo lightbox (componente compartilhado)
