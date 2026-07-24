---
status: accepted
---

# Parâmetros puramente de nitidez (ex. resolução) sem config: «não enviar», não preencher default nosso

Manter tabelas nossas de resolução default hardcoded por modelo (`DEFAULT_VIDEO_RESOLUTION` etc.) é adivinhar o default de cada provider, espalhado e difícil de manter, e «não configurado» não se distingue de «escolheu explicitamente esta faixa». Decidimos apagar essas tabelas default nossas; resolução como parâmetro **puramente de nitidez** se resolve por project → legacy → default do modelo custom → None; None significa «não carregar esse parâmetro na chamada ao SDK», seguir o default do próprio SDK, não nosso fallback — devolvendo o direito de default ao SDK.

## Consequences

- Sem default global de resolução no nível de sistema (o default no nível de modelo de custom provider já cobre a semântica de camada de sistema).
- **Fronteira**: esta decisão só cobre backends em que «resolução e proporção são ortogonais e a resolução é omitível». Quando o tamanho **precisa carregar proporção** (ex. size do OpenAI Sora, size de imagem), o `aspect_size` de `docs/adr/0011` sempre calcula e envia — **nunca** omite com None; esse caminho é o oposto desta decisão e não conflita. A normalização dos nomes nativos de cada um (OpenAI size / Grok resolution / Gemini image_size) também já entrou no cálculo centralizado de `docs/adr/0011`; backends não mantêm mais tabelas estáticas de tradução.
