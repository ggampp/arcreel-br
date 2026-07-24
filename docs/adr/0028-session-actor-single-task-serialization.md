---
status: accepted
---

# SessionActor: um único asyncio task por sessão serializa todas as chamadas ClaudeSDKClient

ClaudeSDKClient não pode ser chamado com concorrência segura; por dentro roda em anyio, e chamar com lock entre tasks facilita deadlock e quebra as hipóteses da máquina de estados interna do SDK. Decidimos que cada sessão agent configure um actor task dedicado, monopolizando o ClaudeSDKClient daquela sessão: query/interrupt/disconnect todos vão pela command queue e executam em série no actor task; durante o recebimento streaming de mensagens, `asyncio.wait` entrelaça com a fila de comandos (interrupt não precisa esperar o fim do stream da rodada inteira); para fora, só se empurram mensagens via callback `on_message`. Rejeitamos «cada caller com seu lock» e «chamada concorrente direta».

## Consequences

- Qualquer operação nova no SDK deve entrar no actor pela command queue; não operar o client direto em task externo.
- O actor é o sujeito residente em memória da sessão; o ciclo de vida (expulsão/inspeção/restauração) é gerido pelo SessionManager (ver `docs/adr/0029`).
