---
status: proposed
---

# Tamanho de mídia: a proporção é decidida só por aspect_ratio e sempre tem prioridade; resolução só define nitidez

O tamanho de saída (largura×altura) de storyboard/vídeo antes vinha de tabelas estáticas «(faixa de resolução, proporção) → pixels» de cada backend, ou de «valor de resolução» passado direto como tamanho. O problema: **tamanho já carrega proporção** — bastava o valor de resolução carregar informação de proporção (valor errado em tabela hardcoded, ou valor custom do usuário como `1920x1080`) para sobrescrever o `aspect_ratio` do projeto e produzir imagem com proporção errada. Varredura camada a camada (8 backends de imagem + 8 de vídeo + valores de resolução custom) confirmou que não é bug pontual, e sim **defeito de mecanismo**:

- A tabela OpenAI de imagem `OPENAI_IMAGE_SIZE_MAP` atribuía 1K de `3:4`/`4:3` aos pixels da proporção vizinha 9:16/16:9 (direção certa, magnitude errada ±25~31%); o caminho I2I (`images.edit`) não passava size nenhum — a proporção vinha do default do upstream (o usuário mediu exatamente essa rota com proporção errada).
- O registry `resolutions` do DashScope qwen são valores de pixel **com** proporção (ex. `2688*1536` de 16:9); com projeto em 9:16, a lógica antiga `if explicit: return explicit` repassava o valor cru e a proporção se perdia.
- Tabelas de vídeo OpenAI/NewAPI incluem valores 4:7 estilo dall-e e 1080 não divisível, e valores desconhecidos/custom repassados crus podem ser ilegais.

Princípio de produto estabelecido: **`aspect_ratio` é a única fonte de verdade da proporção de saída e sempre tem prioridade; resolução (faixa preset ou valor custom) só decide a escala de nitidez, não a proporção; dentro das restrições de tamanho de cada backend, a proporção é a mais exata possível; se faltar resolução mas o tamanho for obrigatório para controlar a proporção, o fallback default é 720P. Produto com proporção errada é inutilizável.**

## Considered Options

- **Corrigir tabela estática de cada backend** — rejeitado: valores errados espalhados, nova proporção/backend ainda exige re-copiar tabela, e não resolve a causa-raiz «valor de resolução carrega proporção e sobrescreve aspect_ratio».
- **Mecanismo unificado de tamanho `lib/aspect_size.py`** — adotado. Proporção + lado curto calculam tamanho exato: tamanho legal = `(aw·round_to·t, ah·round_to·t)` (`aw:ah` é a razão reduzida), desvio de proporção zero por construção + divisível por `round_to`; cada backend aplica clamp pelas próprias restrições de pixel (`max_long_edge` / `max_total_pixels`). Resolução se normaliza unificada a «lado curto»: faixa por tabela, custom `WxH` pega `min` e descasca a proporção, `None` fallback 720.

## Consequences

- **① Valor custom de resolução descasca a proporção**: usuário preenche `1920x1080` (16:9) mas o projeto quer 9:16 — só se usa `min=1080` como lado curto; a proporção continua 9:16. O `ResolutionPicker` do frontend ainda permite input livre; a normalização é no backend (único ponto forçado).
- **② Mecanismo unificado substitui tabelas estáticas dos backends**: depreca `OPENAI_IMAGE_SIZE_MAP`, `_SIZE_BY_RATIO`/`_WAN_PIXELS_BY_BUDGET`/`_EDIT_SIZE_BY_RATIO` do DashScope; backends que aceitam pixels arbitrários (gpt-image-2, série fusão DashScope qwen-image-2.0 e modo pixel wan, qwen-edit-plus/max) ficam com desvio de proporção zero. I2I e T2I de imagem OpenAI passam size de forma simétrica.
- **③ Cobrança desacoplada do tamanho de saída**: o caminho principal de imagem OpenAI cobra por token (cobre a grande maioria); remove a anti-consulta `(resolution, aspect_ratio) → size` do fallback de cobrança. **Custo**: o fallback quando o SDK não devolve usage deixa de distinguir custo por tamanho (cai na faixa default `1024x1024`) — deliberadamente sem introduzir outra fonte de verdade de tamanho só para o fallback; o caminho principal não é afetado.
- **④ Faixas unificadas de lado curto (2K=1440, 4K=2160) mudam a saída existente de vários backends de pixel** (todas com proporção exata):
  - Imagem OpenAI 2K: 9:16 de ~`2048×3584` (4:7) → `1440×2560`, pixels ~metade, custo cai;
  - DashScope wan 4K: 9:16 de `3072×5376` (lado longo acima de 4K) → `2160×3840` (lado longo 3840 é 4K de verdade), pixels ~metade;
  - DashScope wan/qwen 2K: 9:16 de `1536×2688` (desvio 4:7) → `1440×2560` (exato, levemente menor);
  - DashScope wan 1K: 9:16 de `768×1344` → `1008×1792` (aumenta).
- **⑤ Alguns backends têm restrições inerentes inelimináveis — exceções legítimas**:
  - **Vídeo sora-2**: size é enum fixo de 4 faixas (`720x1280`/`1280x720`/`1024x1792`/`1792x1024`, confirmado pelo Literal `VideoSize` do SDK openai), **não aceita WxH arbitrário**. Logo o vídeo não passa por `aspect_size`; em vez disso **adere à faixa legal de proporção mais próxima**. Proporção exata 9:16/16:9 só existe na faixa 720; sem faixa exata mais alta, sora-2 com proporção exata tem teto de nitidez nível 720 (nitidez cede à proporção, conforme o princípio). Vídeo NewAPI é porta agregadora genérica width/height e passa por `aspect_size` (alinha a múltiplos de 8, obtém tamanhos padrão como `1920×1080`).
  - **ark Seedream 2K**: por piso de pixels totais (≥3,68M) mantém ~0,1% de desvio de proporção; mantém a tabela exata existente (migrar regrediria precisão).
  - **Série clássica DashScope qwen** (`qwen-image`/`-plus`/`-max`) só 5 faixas fixas, não aceita pixel arbitrário: presets não registrados, não recomendados oficialmente, fora da cobertura deste mecanismo.
- **Backends de string com proporção independente não precisam mudar lógica de tamanho**: Gemini/Grok/Vidu/ark/DashScope vídeo passam `aspect_ratio`/`ratio` como campo SDK independente, ortogonal a `resolution` (context7 confirma que em Veo `aspect_ratio` e `resolution` são campos independentes; Grok na mesma forma) — não embutem proporção no size em pixels, já sem bug de tamanho; só se acrescentam testes e comentários de guarda da independência de proporção.

Mesma família de «parâmetros de geração resolvidos na execução» que `docs/adr/0001` — tamanho também é derivado com precisão na camada de execução a partir de proporção+resolução, sem congelar de antemão.
