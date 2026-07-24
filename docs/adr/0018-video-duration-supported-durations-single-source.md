---
status: accepted
---

# Duração de vídeo: per-model supported_durations como única fonte de verdade; valor original repassado; se não resolver, fail loud

O mapeamento em buckets dentro do backend (transformar 6 em 8 em silêncio) e o fallback implícito `or [4,6,8]` são a causa-raiz do incidente «escolheu 6s, virava 8s, e o peer rejeitava como ilegal». Decidimos que cada modelo de vídeo declare um `supported_durations` discreto não vazio; três pontos de consumo (prompt de roteiro / seletor do frontend / body do request de vídeo) consomem a mesma origem; cada backend remove mapeamento e normalização de duration, repassa o valor original no body; fora da faixa o peer devolve 400; se o resolver receber conjunto vazio, lança `ValueError` e **todos** os fallbacks implícitos saem — melhor fail loud guiando o usuário a corrigir na página de config do que adulterar em silêncio a escolha do usuário/LLM ou mascarar defeito de config.

## Consequences

- A camada de schema não introduz tipo de intervalo contínuo; o meio-termo é list expandida por completo + frontend detecta continuidade.
- Custom provider, se faltar default, pré-preenche com tabela heurística por model_id (miss → default conservador); a migração Alembic de backfill copia o snapshot de presets inline em vez de importar módulo, para manter determinismo de migrações históricas.
- Uma exceção limitada: Vidu, porque a API lista conjuntos de duração legal muito diferentes por endpoint, mantém correção ao mais próximo no nível do endpoint `_coerce_duration` + warning — dimensão diferente da única fonte de verdade no nível do model.
