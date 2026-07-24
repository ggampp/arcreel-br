---
status: accepted
---

# Config de provider no frontend puxada no ponto de consumo, sem cache persistente de config mutável

O cache no nível de módulo de `provider-models.ts` (`_cache` embutido / `_customCache` custom) nunca invalidava — `invalidateProviderModelsCache` com zero chamadas — e é a causa-raiz de «nas settings do provider o modelo ganhou 10s, o seletor de duração nas settings do projeto ainda mostra o valor antigo»: o cache do frontend virou segunda fonte de verdade que drena, violando ADR 0018 (`supported_durations` per-model como única fonte de verdade) e ADR 0013 (fonte de verdade de capacidade no nível do modelo). Decidimos tornar os dois fetchers totalmente sem estado — cada chamada puxa direto `GET /custom-providers`, `GET /providers`; remove todo cache de módulo, promise in-flight e função invalidate — «consumo = puxar de novo» elimina pela estrutura a classe de stale, em vez de depender de o caller lembrar de invalidar.

## Consequences

- Entrar em settings / assistente de criação / canvas puxa a lista de providers uma vez a mais (JSON pequeno). Thundering herd não ocorre: cada consumidor chama uma vez no topo da página e desce por props; não há irmãos puxando o mesmo fetcher em paralelo, logo sem dedupe in-flight.
- Rejeitamos o plano de zustand store: o ganho de «consistência reativa na mesma tela» não se aplica na estrutura de rotas deste app (página de settings e página de projeto não são a mesma tela) — over-engineering; o momento de introduzir store é quando de fato existir hot path com N consumidores concorrentes.
- `config-status-store` tem fetch próprio + `refresh()` embutido (já chamado após mudança); só produz o ponto vermelho de config e `availableMediaTypes`, sem expor lista de modelos ao seletor de duração/capacidade — fora desta restrição.
- `default_duration` já gravado que estoura a faixa porque a duração do modelo encolheu é coberto pelo resolver do backend em fail-loud (ADR 0018); o aviso «valor salvo inválido» do picker no frontend é assunto separado, fora deste escopo.
