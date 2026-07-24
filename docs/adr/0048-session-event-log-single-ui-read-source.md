---
status: accepted
---

# Log de eventos de sessão: única fonte de leitura da timeline da UI; responsabilidades separadas do transcript do SDK

Se a verdade da UI da conversa do agent se espalha por várias origens (transcript do SDK, buffer em memória, preview de stream) e as origens não compartilham identidade de mensagem, a consistência só se costura com heurísticas de comparação de conteúdo — perda/duplicação de mensagem e inconsistência de render vazam sem parar nos cantos. Decidimos adicionar o **log de eventos de sessão** (tabela independente persistida com seq monotônico por sessão) como única fonte de leitura da timeline da UI:

- Entradas se **tipificam no ponto de escrita** — reconhecimento semântico de notificação de task, interrupt, chamada de skill, afiliação de subagent etc. só ocorre em um lugar ao entrar no log e se persiste; entrada de skill só registra nome e parâmetros de entrada; o texto injetado por completo não entra no log.
- **Mensagem do usuário: o servidor grava no log e aloca identidade antes de ecoar**; o POST devolve a entrada autoritativa; o frontend não renderiza nenhuma mensagem sintetizada localmente; retry se apoia em chave de idempotência no lado do request.
- **SSE empurra stream de entry** (o campo `id` do evento SSE é o seq; no disconnect retoma pelo cursor); a montagem da estrutura de turn (fundir assistants consecutivos, backfill de tool_result, atualização in-place de task) é função pura da camada de projeção do frontend.
- **Preview de stream (draft) é estado em memória do servidor**, identidade = `message_id` da mensagem; ao completar a mensagem é substituído com precisão pela entrada do log com o mesmo `message_id`; não entra no log; crash = perde (consistente com a memória do agent).
- **Mensagens de subagent se registram por completo** como entradas com parent_tool_use_id; o frontend agrupa por parent em cards de subtarefa colapsáveis; a timeline principal só mostra o card.
- O log é **visão materializada** do transcript: se reconstrói replaying o transcript; sessões antigas geram na primeira visita (lazy); o meio de consertar drenagem é reconstruir, sem sync bidirecional.
- **A responsabilidade do transcript do SDK se limita ao SDK resume** (memória do agent); não se misturam entradas exclusivas da UI (seriam alimentadas de volta ao agent no resume).

## Explicitamente não adotamos

- **Convergir a lógica de dedupe sem unificar a identidade de mensagem**: o vazamento de fronteira da comparação de conteúdo não se elimina.
- **Usar o transcript direto como log da UI**: o timing de escrita é controlado pelo SDK; não se aloca identidade no aceite da mensagem do usuário; entradas exclusivas da UI poluem o resume; o subpath independente do subagent e a ordem temporal da UI não são isomorfos.
- **Trilho duplo com feature flag de protocolo antigo/novo**: o frontend teria de manter em paralelo duas lógicas de store.

## Consequences

- Novo tipo de evento de UI deve se tipificar no ponto de escrita; o lado de render e o de leitura não fazem cheiro semântico nem dedupe — o meio de consertar problema de consistência da UI é corrigir a lógica de tipificação no ponto de escrita ou reconstruir o log por replay.
- A coexistência da tabela de log de eventos e da tabela de transcript é double-write deliberado: a primeira é o read model da UI, a segunda é a memória do agent; o conteúdo se sobrepõe mas protocolo e ordem temporal não são isomorfos — fundir as tabelas volta ao acoplamento que este ADR elimina.
- O eager flush do transcript (`docs/adr/0029`) só serve a o SDK resume após crash não perder contexto; o snapshot de reconexão da UI fica a cargo do log de eventos.
