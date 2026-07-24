---
status: accepted
---

# Transcript do SDK espelhado no DB próprio; eager flush por default; sessão idle expulsa da memória e se restaura sem perder histórico

O transcript jsonl nativo do SDK amarra ao filesystem local e não casa com a forma de deploy de «estado de runtime unificado no único async ORM DB» (`docs/adr/0020`) (multi-usuário/PostgreSQL). Decidimos implementar SessionStore custom que espelha o transcript entry a entry no DB (`agent_session_entries` + tabela de resumo de sessão), controlado por `ARCREEL_SDK_SESSION_STORE` (default `db`; `off` volta ao jsonl do SDK); hook de startup migra de uma vez o jsonl histórico local para o DB; o modo de flush default é eager — grava no banco item a item, em troca de o resume do SDK após crash não perder contexto. O transcript só serve ao resume do SDK; a fonte de leitura da timeline da UI é o log de eventos da sessão (ver `docs/adr/0048`).

## Consequences

- Sessões ociosas, após atraso (`agent_session_cleanup_delay_seconds`, default 300 s, com inspeção periódica de fallback), são expulsas da memória (fecha actor/subprocesso do SDK) para conter memória residente. Como o transcript já está no DB, a expulsão não perde histórico: no próximo acesso, rebuild do actor por sdk_session_id via SDK resume e a conversa continua.
- Eager flush tem write amplification; em store lento o SDK funde frames por conta própria. O modo `off` só serve a dev single-machine.
