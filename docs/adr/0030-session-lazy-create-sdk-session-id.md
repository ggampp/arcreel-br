---
status: accepted
---

# Sessão se cria no envio; identidade externa unificada em sdk_session_id

Pré-criar linha de sessão exige gerar ID por conta própria e depois manter um mapa quando o SDK devolve session_id, e produz linhas órfãs «criadas e nunca falaram». Decidimos não pré-criar: sessão nova sobe o actor em estado temporário em memória e envia a primeira mensagem; só quando a mensagem init do SDK devolve session_id a linha de sessão grava no DB, e a key em memória troca do ID temporário para o real (key swap); daí em diante consulta/atualização/restauração usam sempre `sdk_session_id` (UNIQUE) como única identidade externa.

## Consequences

- Antes do retorno do SDK init da primeira mensagem, a sessão não é endereçável (não está na lista, não se assina/restaura por ID).
- Key swap é caminho sensível: qualquer código que procure sessão por ID na janela «já enviou, init ainda não voltou» precisa considerar a fase de ID temporário.
