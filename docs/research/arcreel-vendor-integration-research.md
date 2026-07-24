# Relatório de pesquisa de integração de três fornecedores no ArcReel (Alibaba BaiLian / Kling / MiniMax)

**Data da pesquisa**: 2026-05-29  
**Uso**: material de entrada para PRD e documentos de design posteriores; avaliar os três como fornecedores preset do ArcReel (texto / imagem / vídeo)  
**Moeda**: preços do site da China continental em RMB como referência; diferenças do site internacional já anotadas  
**Sobre preços**: os preços de cada um flutuam com promoções; os deste relatório são referência de seleção, com distinção entre fontes oficiais e de terceiros; antes do go-live, validar no console oficial de cada um

**Declaração de fontes e confiabilidade**:
- Alibaba BaiLian: lista de modelos conferida item a item com a [página oficial "catálogo de modelos"](https://help.aliyun.com/zh/model-studio/models) (atualização da página 2026-05-21); IDs de modelo segundo a página oficial.
- MiniMax: lista de modelos conferida com a [página oficial "lançamentos de modelos"](https://platform.minimaxi.com/docs/release-notes/models) na timeline de releases; julgamento de flagship correto.
- Kling: lista de modelos e preços conferidos em primeira mão com a documentação oficial Kling ([modelos de vídeo](https://klingai.com/document-api/apiReference/model/videoModels) / [modelos de imagem](https://klingai.com/document-api/apiReference/model/imageModels)) e a [página oficial de preços](https://klingai.com/dev/pricing); IDs de modelo, matriz de capacidades e preço unitário em créditos (vídeo 1 crédito=¥1, imagem 1 crédito=¥0.025) segundo o oficial.
- Preços unitários exatos "por imagem" de `qwen-image-2.0` / `wan2.7-image` da Alibaba e faixas detalhadas atrás do login wall ainda precisam de confirmação no console; itens marcados "conferir no console" não foram confirmados em primeira mão.

---

## 0. Escopo e posicionamento da pesquisa

Este relatório é uma compilação de material de **natureza de pesquisa**, cobrindo capacidades, protocolos de API e preços oficiais dos **modelos premium mais recentes** dos três fornecedores, com foco nas necessidades reais do fluxo romance chinês → vídeo do ArcReel (roteiro → design de personagem/cena → storyboard → vídeo → composição).

**Fora do escopo** (decisões de fase PRD / documento de design): ordem de integração, divisão de fases, regras de circuit-breaker/degradação de custo, design de classes de backend, schema de banco.

Princípio de filtro de modelos: só incluir os modelos premium mais recentes adequados à integração ArcReel; versões antigas superadas só são marcadas "substituído" onde necessário, sem aprofundar.

---

## 1. Conclusão primeiro: lista de modelos recomendados para avaliação

| Fornecedor | Modalidade | Modelo | ID do modelo | Preço oficial | Protocolo |
|---|---|---|---|---|---|
| Alibaba BaiLian | text | Qwen-Plus (equilíbrio de produção) | `qwen-plus` | Escalonado 0-128K: ¥0.8 in / ¥2 out (por milhão de tokens) | Compatível OpenAI ✅ |
| Alibaba BaiLian | text | Qwen3.6-Plus (Plus vision-language mais recente) | `qwen3.6-plus` | ¥2 in / ¥12 out; cache hit ¥0.2 | Compatível OpenAI ✅ |
| Alibaba BaiLian | text | Qwen3-Max (flagship estável) | `qwen3-max` | Escalonado 0-32K: ¥2.5 in / ¥10 out | Compatível OpenAI ✅ |
| Alibaba BaiLian | text | Qwen3.7-Max (flagship mais recente, agentic) | `qwen3.7-max` | ¥12 in / ¥36 out (256K-1M); 50% off limitado até ¥6/¥18 (até 2026-06-22) | Compatível OpenAI ✅ |
| Alibaba BaiLian | image | Qwen-Image-2.0-Pro (recomendado oficial, mangá/storyboard/texto) | `qwen-image-2.0-pro` / `qwen-image-2.0` (versão acelerada) | Por imagem (conferir no console) | DashScope síncrono |
| Alibaba BaiLian | image | Wanxiang 2.7 imagem (realismo de retrato/grupo) | `wan2.7-image` / `-image-pro` | Por imagem (conferir no console; falha não cobra) | DashScope síncrono/assíncrono |
| Alibaba BaiLian | video | HappyHorse 1.0 first-frame-to-video | `happyhorse-1.0-i2v` | 720P ¥0.9/s, 1080P ¥1.6/s | DashScope assíncrono |
| Alibaba BaiLian | video | HappyHorse 1.0 reference-to-video (R2V) | `happyhorse-1.0-r2v` | 720P ¥0.9/s, 1080P ¥1.6/s | DashScope assíncrono |
| Alibaba BaiLian | video | HappyHorse 1.0 text-to-video | `happyhorse-1.0-t2v` | 720P ¥0.9/s, 1080P ¥1.6/s | DashScope assíncrono |
| Alibaba BaiLian | video | Wanxiang 2.7 image-to-video (first/last frame/extend/áudio) | `wan2.7-i2v-2026-04-25` | Por segundo e faixa de resolução (conferir no console) | DashScope assíncrono |
| Kling | image | Kling Omni Image O1 (consistência multi-ref de personagem, IP/mangá/série) | `kling-image-o1` (1-10 imgs ref) / `kling-v3-omni` (4K+grupo) | ¥0.2/img (1K-2K); v3-omni 4K ¥0.4 | JWT + assíncrono |
| Kling | video | Kling v3 / v3-omni (flagship, multi-shot+4K+controle de sujeito) | `kling-v3` / `kling-v3-omni` | std ¥0.6/s, pro ¥0.8/s, 4K ¥3/s (sem áudio, preço cheio) | JWT + assíncrono |
| Kling | video | Kling v2-6 (único com controle de voz humana no vídeo) | `kling-v2-6` | pro com áudio ¥1.0/s, sem áudio ¥0.8/s | JWT + assíncrono |
| Kling | video | Kling 2.5 Turbo (cavalinho de custo-benefício) | `kling-v2-5-turbo` | std sem áudio ¥0.6/s, pro com áudio ¥1.0/s | JWT + assíncrono |
| MiniMax | text | MiniMax-M2.7 (flagship) | `MiniMax-M2.7` | ¥2.1 in / ¥8.4 out; cache read ¥0.42 | Dual-compat OpenAI/Anthropic ✅ |
| MiniMax | image | image-01 (com consistência de personagem) | `image-01` | ¥0.025/img (só cobra se sucesso) | REST próprio (URL em um passo) |
| MiniMax | video | Hailuo 2.3 (T2V+I2V alta qualidade) | `MiniMax-Hailuo-2.3` | 768P 6s ¥2 / 10s ¥4; 1080P 6s ¥3.5 | REST próprio (file_id em dois passos) |
| MiniMax | video | Hailuo 2.3-Fast (só I2V, metade do preço) | `MiniMax-Hailuo-2.3-Fast` | 768P 6s ¥1.35 / 10s ¥2.25; 1080P 6s ¥2.31 | Idem |
| MiniMax | video | S2V-01 (R2V especial de consistência de personagem) | `S2V-01` | Pacote de recursos 1.5 créditos/vídeo (≈ ¥3) | Idem, `subject_reference` |

**Visão geral de afiliação de protocolo**: em texto, Alibaba e MiniMax usam compatível OpenAI (reutilizam backend existente); Kling não tem modelo de texto; em imagem e vídeo, Alibaba usa DashScope (imagem majoritariamente síncrona — Qwen-Image-2.0 só síncrono, Wan-Image síncrono/assíncrono; vídeo unificado em tarefa assíncrona), Kling usa JWT, MiniMax usa REST próprio (imagem URL em um passo, vídeo file_id em dois passos).

---

## 2. Comparação de capacidade R2V (reference-to-video / consistência de personagem)

> R2V = gerar vídeo em nova cena mantendo **consistência de personagem/sujeito** a partir de uma ou mais imagens de referência; capacidade central de "protagonista atravessando cenas" no romance→vídeo. Nomes de campo, número de refs e suporte por modelo variam muito entre fornecedores; comparação em coluna própria.

### 2.1 Comparação horizontal

| Fornecedor | ID do modelo R2V | Nome do campo de referência | Limite de refs | Objeto de consistência | Áudio | Notas |
|---|---|---|---|---|---|---|
| Alibaba HappyHorse | `happyhorse-1.0-r2v` | Campo de ref em input DashScope | Multi-personagem | Personagem + sujeito | ✅ com áudio | 720P/1080P, 3-15s, áudio-vídeo nativo |
| Alibaba Wan 2.7 | `wan2.7-r2v` | Formato de citação imgN/vídeoN | Multi-personagem (mix img+vídeo) | Personagem + sujeito | ✅ pode passar timbre/sujeito de vídeo | 720P/1080P, 2-10s, **único que suporta sujeito de referência em vídeo** |
| Alibaba Wan 2.6 | `wan2.6-r2v` / `wan2.6-r2v-flash` | Idem | Multi-personagem | Personagem | ✅ | flash = geração rápida |
| Kling v3 / v3-omni | `kling-v3` / `kling-v3-omni` | Parâmetros de controle de sujeito | Sujeito de personagem em vídeo + multi-img | Personagem + sujeito | Oficial marca ❌ voz humana | Oficial "controle de sujeito" mais forte; v3-omni também suporta ref de vídeo (3-10s) |
| Kling O1 | `kling-video-o1` | Multi-img de sujeito + ref de vídeo | Multi-img de sujeito | Personagem + drive de vídeo | ❌ | Inclui ref de vídeo (edição de vídeo), 3-10s |
| Kling v1-6 (antigo) | `kling-v1-6` | `image_list[]` | Multi-img ref-to-video (legado) | Fusão multi-sujeito | Depende do modelo | Multi-img ref + edição multimodal de vídeo |
| MiniMax S2V-01 | `S2V-01` | `subject_reference[]` | 1 imagem (só rosto) | Rosto de um personagem | — | Pioneer do setor em drive por imagem única; ambiente pode deformar levemente |

### 2.2 Fronteiras-chave

- **R2V Kling já evoluiu para "controle de sujeito"** (primeira mão oficial): o mais forte hoje é o "controle de sujeito (sujeito de personagem em vídeo + multi-img)" de `kling-v3` / `kling-v3-omni`; `kling-video-o1` suporta multi-img de sujeito + ref de vídeo; o multi-img ref-to-video do antigo `kling-v1-6` é capacidade antiga, superada por v3/o1.
- **MiniMax Hailuo 2.3 / 2.3-Fast não suportam R2V**. Hailuo 2.3 só T2V + I2V; 2.3-Fast só I2V. R2V de consistência de personagem do MiniMax exige o modelo independente **S2V-01**, e só suporta uma única ref de rosto.
- **R2V Alibaba é o mais completo**: HappyHorse-1.0-r2v e Wan2.7-r2v suportam ref **multi-personagem** com áudio nativo; Wan2.7-r2v é o **único no lado Alibaba com "sujeito de referência em vídeo"**; Kling v3-omni/o1 também suportam ref de vídeo.

### 2.3 Adequação R2V ao cenário de romance

- Protagonista solo atravessando cenas: MiniMax `S2V-01` (drive por rosto em imagem única, consistência mais estável) ou `happyhorse-1.0-r2v`
- Multi-personagem no mesmo quadro / diálogo: Alibaba `wan2.7-r2v` / `happyhorse-1.0-r2v` (multi-personagem + áudio), ou Kling `kling-v3-omni` (sujeito de personagem em vídeo + multi-img)
- Drive por referência de vídeo (movimento/sujeito da ref): Alibaba `wan2.7-r2v`, Kling `kling-v3-omni` / `kling-video-o1`

---

## 3. Alibaba BaiLian (DashScope / Model Studio)

> **Regiões**: Pequim `dashscope.aliyuncs.com` / Singapura `dashscope-intl.aliyuncs.com` / Virgínia `dashscope-us.aliyuncs.com`; API Keys das três regiões são independentes e não cruzam domínio.

### 3.1 Texto: série Qwen (incluindo o mais recente Qwen3.7-Max)

#### Modelos e preços oficiais (China continental, RMB/milhão de tokens; escalonado pela soma de tokens de input da request, preço da faixa inteira)

| ID do modelo | Posicionamento | Input | Output | Contexto | Notas |
|---|---|---|---|---|---|
| `qwen3.7-max` | **Flagship mais recente**, era agentic, confronta GPT-5.5 / Claude Opus 4.7 | ¥12 | ¥36 | 256K-1M | 50% off limitado até ¥6/¥18 (até 2026-06-22); cache hit input ¥1.2; AA leaderboard 56.6 5º global / 1º CN; capacidade pure-text aberta |
| `qwen3-max` | Flagship estável (snapshots `qwen3-max-2025-09-23` / `-2026-01-23`) | ¥2.5 (0-32K) | ¥10 | 256K | 32-128K ¥4/¥16; 128-256K ¥7/¥28; search agent nativo; thinking mode multiplica output |
| `qwen3.6-plus` | Plus vision-language mais recente (snapshot 2026-04-02, um dos top oficiais Qwen) | ¥2 | ¥12 | — | Cache hit ¥0.2; código/OCR/multimodal acima da série 3.5 |
| `qwen3.6-flash` | Flash mais recente (um dos top oficiais Qwen, faixa de alta frequência baixo custo) | Conferir no console | Conferir no console | — | Um dos três top Qwen na página oficial de catálogo; adequado ao rewrite de prompt / extração de tags mais frequentes do ArcReel |
| `qwen-plus` | Equilíbrio de produção (alias estável, pode apontar para qwen3.5-plus) | ¥0.8 (0-128K) | ¥2 | 1M | 128-256K ¥2/—; contexto ultra-longo de baixo custo de primeira linha |
| `qwen-long` | Documento ultra-longo baixo custo | ¥0.5 | ¥2 | 10M | Mais barato para entendimento de capítulos longos / resumo de texto longo |

> Na página oficial "catálogo de modelos" (2026-05-21), os **três top de texto Qwen** são `qwen3.7-max` / `qwen3.6-plus` / `qwen3.6-flash`; `qwen-plus` / `qwen-long` são faixa de alias estável, ainda utilizáveis, mas não mais top.

**Sugestão de divisão de seleção**: plot crítico de flagship / raciocínio complexo → `qwen3.7-max` ou `qwen3-max`; rewrite de prompt de storyboard de alta frequência, character card, extração de script de dublagem → `qwen-plus` ou `qwen3.6-plus` (custo-benefício); entendimento de capítulos inteiros de romance ultra-longo → `qwen-long`. Usar Qwen3.7-Max em tarefa simples é "canhão em mosquito".

**API**: compatível OpenAI ✅ — `base_url=https://dashscope.aliyuncs.com/compatible-mode/v1`, endpoint `/chat/completions`, Bearer Key. Suporta streaming, `tool_calls`, `response_format={"type":"json_object"}`. Parâmetros não padrão `enable_thinking` / `thinking_budget` passam por `extra_body`. Para saída estruturada de schema chinês complexo, `tool_choice` forçando tool call é mais estável que `response_format`.

**Regra de cobrança escalonada**: o total de tokens de input da request determina o preço unitário da faixa da conta inteira (não só a parte que passa o limite).

> Versões antigas substituídas (`qwen-turbo` / série Qwen2.x) não aprofundadas; interfaces estáveis legadas ainda utilizáveis.

#### Proxy de modelos de terceiros no BaiLian (um ponto de integração cobre vários)

A página oficial de catálogo mostra que, além do Qwen, o BaiLian também faz proxy de vários modelos de texto de terceiros **no mesmo formato compatível OpenAI do Qwen**; o ArcReel, ao integrar um provider `dashscope` + backend OpenAI, ganha esses de brinde (troca no campo model):

- `deepseek-v4-pro` / `deepseek-v4-flash` (DeepSeek V4)
- `kimi-k2.6` (Moonshot Kimi)
- `glm-5.1` (Zhipu GLM)
- `MiniMax-M2.7` (caminho proxy BaiLian `MiniMax/MiniMax-M2.7`, com 20% de desconto de cache implícito)
- `mimo-v2.5-pro` (Xiaomi MiMo)

Valor para o ArcReel: se não quiser integrar MiniMax/DeepSeek etc. em sites oficiais separados, unifica no BaiLian; o preço desses modelos de terceiros no BaiLian pode diferir um pouco do site oficial — preço exato no console BaiLian.

### 3.2 Imagem: Qwen-Image e Wanxiang 2.7 imagem (duas linhas de produto paralelas)

A Alibaba tem duas linhas de geração de imagem, **posicionamento complementar**; ambas valem avaliação no cenário de romance:

#### ① Série Qwen-Image (time Tongyi Qwen, renderização de texto + mangá/storyboard SOTA)

- **IDs de modelo**:
  - `qwen-image-2.0-pro` / `qwen-image-2.0-pro-2026-03-03` (**recomendado oficial**, modelo unificado de geração e edição, texto/realismo/seguimento semântico mais fortes, só interface síncrona)
  - `qwen-image-2.0` / `qwen-image-2.0-2026-03-03` (versão acelerada, equilíbrio efeito/performance, só interface síncrona)
  - `qwen-image-edit` (edição/modificação local dedicada; content com 1-3 imgs + uma instrução de edição)
  - Geração anterior `qwen-image-max` / `qwen-image-plus` (substituída pela série 2.0, não aprofundada)
- **Lançamento**: Qwen-Image-2.0 em 2026-02-10 (mesmo dia do Seedream 5.0 da ByteDance); primeira iteração 2.0 do modelo de geração de imagem Qwen, 7B parâmetros (bem mais enxuto que o MMDiT 20B inicial)
- **Capacidades centrais (alta aderência a romance)**:
  - **Renderização de texto complexo SOTA**: instruções longas até 1000 tokens (≈800-1000 caracteres chineses); tipografia complexa, multi-fonte (kaishu/shoujin/xiaokai etc.), texto em multi-mídia (vidro/roupa/revista etc.); demo oficial gerou as 324 palavras completas do *Prefácio da Coleção do Pavilhão das Orquídeas* com ilustração
  - **Geração de mangá multi-painel + consistência de personagem estável entre painéis** — corresponde direto ao cenário de storyboard
  - **Resolução nativa 2K** (2048×2048); pele/vegetação/textura de arquitetura finas; suporte a realismo, tinta, desenho à mão, anime, óleo e dezenas de estilos
  - **Geração + edição unificadas**: mesma arquitetura no mesmo modelo faz text-to-image + edição image-to-image (legenda, troca de fundo, composição multi-img, fusão cross-dimensional), edição em nível de objeto sem danificar detalhes ao redor
  - 1º em AI Arena text-to-image + image edit; DPG-Bench 88.32 acima do FLUX.1 (12B) 83.84
- **API**: DashScope, text-to-image e image edit em endpoints separados; série 2.0 só interface síncrona; image edit `messages` com um único user (1-3 imgs + uma instrução text); largura/altura recomendadas 384-3072px, ≤10MB por imagem; retorna URL OSS temporária
- **Preço**: por número de imagens geradas com sucesso; falha não cobra nem gasta cota grátis; preço unitário exato no console BaiLian "lista de modelos e preços" (oficial diz que preço comercial previsto ≈1/3 do Midjourney)
- **Idiomas**: suporte formal a chinês simplificado e inglês

#### ② Wanxiang 2.7 imagem (time Wanxiang, realismo de retrato + grupo)

- **IDs de modelo**: `wan2.7-image` (padrão) / `wan2.7-image-pro` (escala grande, cenas complexas mais estáveis); lançamento 2026-04-01
- **Capacidades centrais**:
  - Diversidade de rostos "mil pessoas, mil faces", longe de rosto AI homogêneo (realismo de retrato forte)
  - **Grupo de até 12 imagens por request**, mantendo mesmo personagem/estilo/color grade → referência de storyboard
  - Renderização de texto ultra-longo (até 4000 caracteres / 3K tokens, tipografia chinesa de nível impresso em 12 idiomas)
  - Controle preciso de cor Hex; multi-ref até 9 imgs em pose coletiva com consistência de personagem
  - Edição online de quadro e plot em linguagem natural
- **API**: HTTP síncrono DashScope `POST /api/v1/services/aigc/multimodal-generation/generation` (desde wan2.6) ou assíncrono + `X-DashScope-Async: enable`
- **Preço**: por número de sucessos; falha não cobra; preço unitário exato no console

**Seleção das duas linhas**: storyboard/mangá/pôster com texto → priorizar Qwen-Image-2.0-Pro (consistência entre painéis + texto SOTA + 2K nativo); retrato realista/diversidade de personagem/grupo em uma request → priorizar wan2.7-image. Ambos cobram por imagem e usam DashScope.

### 3.3 Vídeo: série HappyHorse 1.0 (principal) e Wanxiang Wan 2.7

> HappyHorse (Pônei Feliz) é a família de modelos de vídeo anunciada oficialmente pela Alibaba em 2026-04; **no Artificial Analysis Video Arena blind test, 1º em text/image-to-video "sem áudio" e 2º global na faixa com áudio (atrás de Seedance 2.0)**. Transformer single-stream de 15B parâmetros, geração nativa síncrona de áudio-vídeo; um H100 gera 5s 1080P em 38s (2-3× a velocidade da classe). **Totalmente open source e comercializável**, especialmente amigável a projeto open source como o ArcReel.

#### Família completa HappyHorse 1.0 (preço oficial: 720P ¥0.9/s, 1080P ¥1.6/s)

| ID do modelo | Tipo | Características | Specs de saída |
|---|---|---|---|
| `happyhorse-1.0-t2v` | Text-to-video | Com áudio, lip-sync em 7 idiomas, multi-shot | 720P/1080P, 3-15s, 24fps MP4 |
| `happyhorse-1.0-i2v` | First-frame-to-video | Com áudio, 1080P | 720P/1080P, 3-15s, 24fps MP4 |
| `happyhorse-1.0-r2v` | Reference-to-video | Com áudio, consistência multi-personagem | 720P/1080P, 3-15s, 24fps MP4 |
| `happyhorse-1.0-video-edit` | Edição de vídeo | Com áudio, transferência de estilo | 720P/1080P, 3-15s, 24fps MP4 |

Idiomas de lip-sync: chinês, inglês, japonês, coreano, alemão, francês, cantonês. Narrativa multi-shot até 15 s, luz/câmera/consistência de personagem de nível cinematográfico.

#### Divisão oficial Alibaba HappyHorse / Wan

| Cenário | Recomendação oficial | Alternativa |
|---|---|---|
| Text-to-video (com áudio) | `happyhorse-1.0-t2v` | `wan2.7-t2v-2026-04-25` (quando precisa de arquivo de áudio customizado) |
| First-frame-to-video | `happyhorse-1.0-i2v` | — |
| First/last frame / extensão de vídeo / série longa | `wan2.7-i2v-2026-04-25` | — |
| Reference-to-video (consistência de personagem) | `happyhorse-1.0-r2v` | `wan2.7-r2v` (precisa de sujeito de ref em vídeo/timbre customizado) |
| Edição de vídeo | `happyhorse-1.0-video-edit` | `wan2.7-videoedit` (efeitos/réplica de câmera) |

#### Família completa Wan 2.7 (720P/1080P, 2-15s, 30fps)

| ID do modelo | Tipo | Características |
|---|---|---|
| `wan2.7-t2v` / `wan2.7-t2v-2026-04-25` | Text-to-video | Sync de áudio, narrativa multi-shot |
| `wan2.7-i2v` / `wan2.7-i2v-2026-04-25` | Image-to-video | First frame, first/last frame, extensão de vídeo, drive por áudio |
| `wan2.7-r2v` | Citação de vídeo | Multi-personagem, formato de citação imgN/vídeoN (único com sujeito de ref em vídeo), 2-10s |
| `wan2.7-videoedit` | Edição de vídeo | Edição por instrução, transferência de vídeo, efeitos/réplica de câmera, máx. 10s |

> Wanxiang 2.5 (`wan2.5-t2v-preview` / `wan2.5-i2v-preview`) é a única versão que aceita arquivo de áudio customizado (`audio_url`), 480P/720P/1080P, faixas fixas 5s/10s. Versões anteriores Wan 2.1/2.2 foram substituídas por 2.6/2.7, não aprofundadas.

**API de vídeo Wan / HappyHorse** (DashScope assíncrono unificado):
- Submit: `POST /api/v1/services/aigc/video-generation/video-synthesis` + `X-DashScope-Async: enable` → `output.task_id`
- Poll: `GET /api/v1/tasks/{task_id}` → `PENDING → RUNNING → SUCCEEDED/FAILED`
- Resultado: `output.video_url` (OSS público, válido 24h; precisa baixar/rehospedar imediatamente)

---

## 4. Kling (Kuaishou)

> **Sem modelo de texto**. **API**: `https://api.klingai.com/v1`, auth **JWT HS256** (AK como iss, SK assina, expira em 30 min, renovação automática). Alibaba Cloud BaiLian também faz proxy de imagem/vídeo Kling (DashScope assíncrono, só região Pequim); se não quiser escrever JWT, pode usar o caminho proxy BaiLian.
>
> Lista de modelos desta seção conferida em primeira mão com a doc oficial `klingai.com/document-api/apiReference/model/{video,image}Models`. **Preço exato em "inspiração" ainda precisa login no console app.klingai.com** (a doc oficial lista matriz de capacidades, não o valor de inspiração por faixa).

### 4.1 Imagem (série Kolors + nova geração Omni Image)

Linha oficial de modelos de imagem Kling (conferência em primeira mão): `kling-v1` / `kling-v1-5` / `kling-v2` / `kling-v2-new` / `kling-v2-1` / `kling-v3` / `kling-v3-omni` / `kling-image-o1`.

#### As duas mais valiosas de avaliar no cenário de romance

- **`kling-image-o1` (Kling Omni Image O1, fortemente recomendado)**: nova geração multi-ref de imagem Kling, framework MVL (multimodal vision-language), **suporta 1-10 imagens de ref ao mesmo tempo**, consistência de personagem entre imagens; posicionamento oficial "design de personagem IP, mangá/série, material de marca" — **hoje o modelo de imagem Kling mais forte para personagem atravessando cenas/storyboard de romance**, bem acima do Kolors antigo. Aspect ratio custom (1K/2K) + aspect ratio inteligente; text-to-image/image-to-image/controle de sujeito (multi-img). Dados de treino até 2025-12.
- **`kling-v3-omni` (capacidade de imagem)**: aspect ratio custom 1K/2K/**4K** + aspect ratio inteligente; text-to-image/image-to-image/**geração de grupo**/controle de sujeito (multi-img). Componente de imagem da arquitetura multimodal unificada 3.0; 4K + grupo tem valor para produção em lote de storyboard.

#### Legado (sob demanda, substituído por o1/v3)

- `kling-v1`: text-to-image/image-to-image genérico, 1K, 8 aspect ratios
- `kling-v1-5`: image-to-image com manutenção de **traços de personagem + fisionomia**, 1K
- `kling-v2` / `kling-v2-1`: multi-img ref-to-image, transferência de estilo; v2-1 o mais completo (genérico + traços + fisionomia + multi-img + transferência de estilo)
- Escrita de caracteres chineses é ponto forte tradicional da série Kolors (encoder de texto ChatGLM3); o1/v3-omni da nova geração reforçam ainda mais a renderização de texto

**API**: JWT + assíncrono, `POST /v1/images/generations` → `GET /v1/images/generations/{task_id}` (image_url 24h)  
**Parâmetros-chave**: `model_name`, `prompt`, `negative_prompt`, `image`, `image_fidelity`, `human_fidelity`, `n`, `aspect_ratio`; multi-img ref com array image (o1 até 10)

**Preços oficiais de imagem (primeira mão, `klingai.com/dev/pricing`, crédito de imagem 1 crédito = ¥0.025)**:

| Modelo | Capacidade | Spec | Preço unitário/img |
|---|---|---|---|
| `kling-image-o1` | Text-to-image/image-to-image/edição | Vários aspect ratios | ¥0.2 (8 créditos) |
| `kling-v3-omni` | Text-to-image/image-to-image/edição | 1K/2K | ¥0.2 |
| `kling-v3-omni` | Idem | 4K | ¥0.4 (16 créditos) |
| `kling-v3` | Text-to-image/image-to-image | 1K/2K | ¥0.2 |
| `kling-v2-1` | Text-to-image | — | ¥0.1 (4 créditos) |
| `kling-v2-1` | Image-to-image | — | ¥0.2 |
| `kling-v2` | Text-to-image | — | ¥0.1 |
| `kling-v2` | Image-to-image multi-img ref | — | ¥0.4 (16 créditos) |
| `kling-v1-5` | Image-to-image traços/fisionomia | — | ¥0.2 |
| `kling-v1` | Text-to-image/image-to-image | — | ¥0.025 (1 crédito, mais barato) |
| Modelo de função | Expandir imagem | — | ¥0.2 |
| Modelo de função | Completar sujeito inteligente | — | ¥0.5 (20 créditos) |

Ou seja, `kling-image-o1` / `kling-v3-omni` (recomendados) a ¥0.2/img (1K-2K), mais caros que MiniMax image-01 a ¥0.025/img, mas com consistência multi-ref bem mais forte.

### 4.2 Vídeo

Linha oficial de modelos de vídeo Kling (conferência em primeira mão): `kling-v1` / `kling-v1-5` / `kling-v1-6` / `kling-v2-master` / `kling-v2-1` / `kling-v2-1-master` / `kling-v2-5-turbo` / `kling-v2-6` / `kling-v3` / `kling-v3-omni` / `kling-video-o1`.

**Preços oficiais de vídeo (primeira mão, `klingai.com/dev/pricing`, 1 crédito = ¥1 preço cheio, cobrança por combinação de dimensões ¥/s)**:

| Spec | Sem áudio | Com áudio | Com vídeo de ref (sem áudio) |
|---|---|---|---|
| Padrão std × 1s | ¥0.6 | ¥0.8 | ¥0.9 |
| Alta qualidade pro × 1s | ¥0.8 | ¥1.0 | ¥1.2 |
| 4K × 1s | ¥3.0 | ¥3.0 | — |

Ou seja, vídeo Kling cobra por combinação de quatro dimensões "modo × duração × com/sem vídeo de ref × com/sem áudio"; ex.: pro com áudio 5s = ¥1.0×5 = ¥5; std sem áudio 5s = ¥3. Escalonamento de pacotes: trial 0.7 RMB/crédito (primeira compra 30% off), padrão 1 RMB/crédito, volume 0.9 RMB/crédito.

Avaliação da comunidade: Kling está na primeira linha global em física de movimento, estabilidade de câmera e decomposição de instruções complexas. Artificial Analysis T2V (with-audio) Leaderboard (2026-05-28) Kling 3.0 Omni 1080p Pro Elo 1099 4º lugar (top 3: Dreamina Seedance 2.0, HappyHorse-1.0, Veo 3.1).

> Capacidades de plataforma independentes da versão do modelo (oficial): digital human (foto única → vídeo de locução), lip-sync (drive por texto/áudio), video-to-SFX (SFX para vídeo Kling gerado ou upload do usuário).

#### ① kling-v3 / kling-v3-omni (flagship, multi-shot + 4K + controle de sujeito)

- **Capacidades (primeira mão oficial)**: std/pro/**4K**, duração 3-15s; text-to-video com **geração single-shot + multi-shot**; image-to-video com single-shot (só first frame) + multi-shot + **first/last frame (plano contínuo)** + **controle de sujeito (sujeito de personagem em vídeo + multi-img)**; v3-omni suporta ainda ref de vídeo (só 3-10s; faixa 4K não suporta ref de vídeo); v3 também suporta controle de movimento (std/pro; 4K não)
- **Correção importante**: na tabela oficial de capacidades, **"controle de som (controle de voz humana)" de v3 / v3-omni está marcado ❌**. Isso **não coincide** com a alegação de terceiros de "sync nativo áudio-vídeo no v3" — prevalece o oficial: controle de voz humana no vídeo de v3/v3-omni não é suportado segundo o oficial; SFX pode usar a capacidade de plataforma "video-to-SFX". Antes de integrar, reconfirmar na doc oficial.
- **Controle de sujeito é chave para romance**: o "sujeito de personagem em vídeo + multi-img" de v3/v3-omni é consistência de personagem mais forte que o multi-img ref do antigo v1-6

#### ② kling-v2-6 (única versão de vídeo que marca explicitamente controle de voz humana)

- **Capacidades (primeira mão oficial)**: std/pro, 5s/10s + outras durações; text/image-to-video (std só sem áudio; pro com áudio); first/last frame (pro, só sem áudio); **controle de som (voz humana) só no pro ✅**; controle de movimento (outras faixas de duração)
- É a **única versão na tabela oficial de modelos de vídeo com "controle de som ✅"** (faixa pro); quando precisa de voz humana no vídeo, priorizar a avaliação dela

#### ③ kling-v2-5-turbo (cavalinho de custo-benefício)

- **Capacidades (primeira mão oficial)**: std/pro, 5s/10s; text-to-video + image-to-video (todas as faixas); first/last frame (só pro); resolução pro 1080p, 24fps
- **Preço oficial**: combinação de dimensões da tabela acima; std 5s sem áudio = ¥3, pro 5s com áudio = ¥5 (pro 1080p 24fps); IR Kuaishou 2025-09-24 anunciou ~30% de queda por trecho 5s 1080P vs 2.1
- Sem multi-img de sujeito / controle de som e outras capacidades avançadas; faixa de volume puro de custo-benefício

#### ④ kling-video-o1 (especial ref de vídeo + controle de sujeito)

- **Capacidades (primeira mão oficial)**: std/pro, 3-10s (text/image-to-video só 5s, 10s); image-to-video com first/last frame (plano contínuo) + **controle de sujeito (só multi-img)** + **ref de vídeo (inclui edição de vídeo)**; controle de som ❌
- Adequado a cenários que precisam de "drive por vídeo de referência" ou consistência multi-img de sujeito

#### ⑤ kling-v1-6 / v1-5 / v1 (legado sob demanda)

- `kling-v1-6`: text/image-to-video todas as faixas, first/last frame (pro), **multi-img ref-to-video** + edição multimodal de vídeo + extensão de vídeo + efeitos de duas imagens (abraço/beijo/coração); pro 1080p
- `kling-v1-5`: image-to-video principal, first/last frame / só last frame / motion brush (pro); inclui extensão de vídeo
- `kling-v1`: text/image-to-video, controle de câmera, first/last frame, motion brush, extensão de vídeo, efeitos de duas imagens; 720p
- `kling-v2-master` / `kling-v2-1` / `kling-v2-1-master`: faixas da geração v2; v2-1 image-to-video com first/last frame (pro)

**Consulta rápida de distribuição de capacidades-chave** (primeira mão oficial):
- Narrativa multi-shot: só `v3` / `v3-omni`
- Controle de voz humana no vídeo: só `kling-v2-6` (pro)
- Controle de sujeito (consistência de personagem): `v3` / `v3-omni` (sujeito de vídeo+multi-img mais forte), `o1` (multi-img+ref de vídeo), `v1-6` (multi-img ref-to-video)
- 4K: só `v3` / `v3-omni`
- Ref de vídeo (inclui edição): `v3-omni` (3-10s), `o1`

**Pontos de integração de vídeo Kling** (JWT):

```python
import jwt, time
def kling_token(ak, sk):
    return jwt.encode(
        {"iss": ak, "exp": int(time.time())+1800, "nbf": int(time.time())-5},
        sk, algorithm="HS256", headers={"alg":"HS256","typ":"JWT"})
```

Recomenda-se encapsular classe de auth JWT, reutilizar token em 30 min, refresh automático 60 s antes de expirar.

---

## 5. MiniMax Hailuo

> Multimodal mais barato, protocolo mais consistente. Todas as APIs em `https://api.minimaxi.com/v1` (doméstico) / `https://api.minimax.io/v1` (internacional), Bearer Key; texto compatível com SDKs OpenAI e Anthropic.

### 5.1 Texto: MiniMax-M2.7

- **IDs de modelo**: `MiniMax-M2.7` (flagship) / `MiniMax-M2.7-highspeed` (2× velocidade, 2× preço); proxy BaiLian `MiniMax/MiniMax-M2.7`
- **Lançamento**: 2026-03-18, flagship atual (substitui M2.5 / abab 7)
- **Capacidades**: SWE-Pro 56.22% (oficial diz matching GPT-5.3-Codex); MoE 230B total / 10B ativo; contexto 200K; primeira linha de criação literária em chinês; thinking mode + Function Calling + Toolathon 46.3%
- **API**: compatível OpenAI `base_url=https://api.minimaxi.com/v1`; ou proxy BaiLian com 20% de desconto de cache implícito; SDK Anthropic também compatível
- **Preços oficiais** (site doméstico, RMB/milhão de tokens, fonte platform.minimaxi.com pricing-paygo):

  | Modelo | Input | Output | Cache hit read | Cache write |
  |---|---|---|---|---|
  | M2.7 | ¥2.1 | ¥8.4 | ¥0.42 (20%) | ¥2.625 (125%) |
  | M2.7-highspeed | ¥4.2 | ¥16.8 | ¥0.42 | ¥2.625 |

- **Site internacional**: M2.7 input $0.30/M, output $1.20/M (≈1/8 do preço Claude Sonnet)
- **Posicionamento**: segundo modelo de texto em par com Qwen — M2.7 para persona/texto emocional fino e criação em chinês; Qwen-Plus para JSON estruturado

> Versões antigas abab 6.5 / M2.5 / abab 7 etc. ainda chamáveis, mas substituídas por M2.7; não aprofundadas.

### 5.2 Imagem: image-01

- **ID do modelo**: `image-01`
- **Capacidades**: text-to-image + image-to-image unificados; `subject_reference` drive multi-cenário por uma ref de rosto (character card → standee multi-cenário); `aspect_ratio` ou `width`/`height` (512-2048, múltiplo de 8); `prompt_optimizer`; `n` 1-9
- **API**: `POST https://api.minimaxi.com/v1/image_generation`, Bearer + JSON, um passo retorna `url` (24h) ou base64
- **Preço oficial**: ¥0.025/img (só cobra se sucesso); site internacional ≈ $0.0035-0.005/img
- **Estilo**: retrato cinematográfico + materiais reais SOTA; consistência de personagem a mais estável dos três; anime puro um pouco atrás de Kolors / Qwen-Image

### 5.3 Vídeo: série Hailuo 2.3

> Fronteira de capacidade: Hailuo 2.3 = T2V + I2V; Hailuo 2.3-Fast = só I2V; R2V de consistência de personagem usa o S2V-01 independente (só rosto em imagem única).

#### ① MiniMax-Hailuo-2.3 (T2V + I2V, alta qualidade)

- **ID do modelo**: `MiniMax-Hailuo-2.3` (lançado 2025-10-28, flagship de vídeo atual)
- **Capacidades**: T2V + I2V; saída nativa 1080P; física extrema (arquitetura NCR); 85% de resposta a instruções complexas; controle de câmera (prompt embute `[pan left, rise]` etc., ≤3 combinações); **forte em estilos anime/ilustração/game CG** (adererde a romance)
- **Faixas suportadas**: 6s (768P/1080P), 10s (768P; 10s não suporta 1080P)
- **Preço oficial** (doméstico, RMB/vídeo): 768P 6s ¥2 / 10s ¥4; 1080P 6s ¥3.5
- **Site internacional**: 768P $0.045/s, 1080P Pro $0.08/s

#### ② MiniMax-Hailuo-2.3-Fast (só I2V, ≈ metade do preço)

- **ID do modelo**: `MiniMax-Hailuo-2.3-Fast`
- **Capacidades**: só image-to-video (I2V), sem T2V; mesma qualidade de geração, ≈ metade do preço; para iteração rápida I2V
- **Preço oficial**: 768P 6s ¥1.35 / 10s ¥2.25; 1080P 6s ¥2.31

#### ③ S2V-01 (R2V especial de consistência de personagem)

- **ID do modelo**: `S2V-01`
- **Capacidades**: Subject-to-Video pioneiro MiniMax; uma ref de rosto dirige consistência de personagem no vídeo inteiro (rosto/pose/expressão/luz ajustáveis de forma independente no prompt); especialmente adequado a multi-storyboard / personagem recorrente
- **Parâmetros**: `subject_reference=[{"type":"character","image":["url"]}]`
- **Limites**: só um rosto; ambiente pode deformar levemente; seguimento de prompt um pouco abaixo de T2V/I2V
- **Preço**: pacote de recursos 1.5 créditos/vídeo (≈ ¥3)

> Hailuo-02 (`MiniMax-Hailuo-02`) mantém faixa rascunho 512P (512P 6s ¥0.6); o resto foi substituído por 2.3; T2V-01-Director etc. só compatibilidade backward; não aprofundados.

**Pontos de integração de vídeo MiniMax** (URL em dois passos):
1. `POST /v1/video_generation` → `task_id`
2. Poll `GET /v1/query/video_generation?task_id=xxx` → `status=Success` retorna `file_id`
3. `GET /v1/files/retrieve?file_id=xxx` → `download_url` (válido por pouco tempo; recomenda `callback_url`, responder challenge de validação primeiro)

---

## 6. Avaliação de viabilidade de integração

### 6.1 Afiliação de protocolo

| Modalidade / Fornecedor | Alibaba BaiLian | Kling | MiniMax |
|---|---|---|---|
| Texto | ✅ Compatível OpenAI, reutiliza backend existente | ❌ nenhum | ✅ Dual-compat OpenAI/Anthropic |
| Imagem | DashScope síncrono/assíncrono | JWT + assíncrono | REST próprio (URL em um passo) |
| Vídeo | DashScope assíncrono (endpoint unificado) | JWT + assíncrono (multi-endpoint) | REST próprio (file_id em dois passos) |

### 6.2 Esforço de backend ArcReel

| Grau de reutilização | Modelos |
|---|---|
| Reutilizar OpenAI text backend | `qwen3.7-max`, `qwen3.6-plus`, `qwen3.6-flash`, `qwen3-max`, `qwen-plus`, `MiniMax-M2.7`; e proxies BaiLian `deepseek-v4-pro/flash`, `kimi-k2.6`, `glm-5.1`, `mimo-v2.5-pro` (mesmo formato compatível OpenAI) |
| Escrever novo DashScope backend (um cobre tudo; precisa de caminhos síncrono e assíncrono) | Imagem `qwen-image-2.0-pro` / `qwen-image-2.0` / `qwen-image-edit` (síncrono), `wan2.7-image` (síncrono/assíncrono); vídeo `happyhorse-1.0-*` / `wan2.7-*` / `wan2.5-*` (assíncrono); proxy Kling BaiLian |
| Escrever novo Kling JWT backend | Vídeo `kling-v3` / `kling-v3-omni` / `kling-v2-6` / `kling-v2-5-turbo` / `kling-video-o1`; imagem `kling-image-o1` / `kling-v3-omni` (endpoints unificados `/v1/images` e `/v1/videos` + renovação JWT) |
| Escrever novo MiniMax backend (URL em dois passos) | `MiniMax-Hailuo-2.3/-Fast`, `S2V-01`; `image-01` em um passo é mais simples |

### 6.3 Particularidades de autenticação

- Alibaba: Bearer + Keys multi-região não misturáveis; assíncrono precisa do header `X-DashScope-Async: enable`
- Kling: JWT HS256, expira em 30 min; precisa de cache de token + refresh antecipado
- MiniMax: Bearer simples; download de vídeo file_id em dois passos ou `callback_url` (responder challenge primeiro)

### 6.4 Score de aderência ao cenário de romance

| Dimensão | Alibaba BaiLian | Kling | MiniMax |
|---|---|---|---|
| Entendimento de roteiro chinês / saída estruturada | ★★★★★ | — | ★★★★★ |
| Renderização de texto chinês (capa/pôster) | ★★★★★ (Qwen-Image-2.0) | ★★★★ (image-o1/v3-omni texto reforçado) | ★★★ |
| Consistência de personagem entre painéis mangá/storyboard (img) | ★★★★★ (Qwen-Image-2.0 mangá multi-painel) | ★★★★★ (image-o1 até 10 refs, feito para mangá/série) | ★★★★ (image-01) |
| Consistência de personagem (vídeo R2V) | ★★★★★ (happyhorse-r2v / wan2.7-r2v multi-personagem+áudio+ref de vídeo) | ★★★★★ (v3-omni sujeito de vídeo+multi-img, o1 ref de vídeo) | ★★★★ (S2V-01 rosto em imagem única, mais estável mas só uma pessoa) |
| Física da imagem de vídeo | ★★★★★ (HappyHorse 1º/2º em blind) | ★★★★★ (engine física Omni) | ★★★★ (NCR 1080P nativo, forte em anime) |
| Narrativa multi-shot de vídeo | ★★★★★ (wan2.7 + happyhorse multi-shot com consistência de sujeito) | ★★★★★ (v3/v3-omni multi-shot oficial) | ★★★ |
| Áudio-vídeo unificado | ★★★★★ (HappyHorse nativo 7 idiomas lip-sync / wan2.5 audio_url) | ★★★ (oficial só v2-6 pro com controle de voz; v3/v3-omni marca ❌; SFX via "video-to-SFX" de plataforma) | ★★★ (precisa de TTS externo) |
| Custo-benefício de preço | ★★★★ (HappyHorse 720P ¥0.9/s) | ★★★ (vídeo std ¥0.6/s, pro com áudio ¥1.0/s, 4K ¥3/s; imagem ¥0.2/img) | ★★★★★ (Hailuo-2.3-Fast 768P 6s ¥1.35) |

---

## 7. Riscos-chave e incertezas

1. **Flutuação de preços**: os três têm descontos limitados (Qwen3.7-Max 50% off até 2026-06-22, Qwen3.6 todos os modelos 55% off, HappyHorse 20% off limitado, campanhas de pacote Kling). Campos de preço do ArcReel `PROVIDER_REGISTRY` devem ser configuráveis, não hardcoded.
2. **Itens de preço oficial já verificados**: família completa HappyHorse 1.0 720P ¥0.9/s, 1080P ¥1.6/s (anúncio de lançamento Alibaba Cloud); preços escalonados Qwen e Qwen3.7-Max ¥12/¥36 (páginas de preço/produto Alibaba Cloud); MiniMax M2.7 ¥2.1/¥8.4, image-01 ¥0.025/img, faixas Hailuo 2.3 (platform.minimaxi.com); **preços unitários em créditos de vídeo/imagem Kling de toda a linha** (página oficial de preços klingai.com/dev/pricing: vídeo 1 crédito=¥1 por "modo×duração×ref de vídeo×áudio", imagem 1 crédito=¥0.025, image-o1/v3-omni ¥0.2/img).
3. **Ainda precisam de conferência no console**: preço unitário RMB exato por imagem de `qwen-image-2.0-pro/2.0` e `wan2.7-image`, preço unitário de token exato de `qwen3.6-flash` (página oficial Alibaba não lista valor por imagem/faixa diretamente); preços no lado BaiLian dos modelos de terceiros proxy (DeepSeek/Kimi/GLM/MiMo). Preços Kling já verificados em primeira mão; não precisa reconferir.
4. **Atualização de IDs de modelo**: Qwen lança snapshot todo mês; preferir aliases estáveis + regressão periódica; tops oficiais de texto Qwen `qwen3.7-max`/`qwen3.6-plus`/`qwen3.6-flash`, de imagem/vídeo `wan2.7-image-pro`/`qwen-image-2.0-pro`/`happyhorse-1.0-*` (todos segundo catálogo oficial 2026-05-21); MiniMax atual M2.7 / Hailuo 2.3 / image-01 (página oficial de releases).
5. **Fronteiras de capacidade (primeira mão oficial)**: consistência de personagem Kling mais forte hoje é o "controle de sujeito (sujeito de personagem em vídeo+multi-img)" de `kling-v3`/`v3-omni`, não o multi-img ref do v1-6 antigo; "controle de voz humana" de vídeo `v3`/`v3-omni` oficial marca ❌; só `kling-v2-6` pro suporta voz humana no vídeo. Hailuo 2.3 não suporta R2V (só T2V+I2V); 2.3-Fast só I2V; R2V MiniMax vai por S2V-01 (só rosto em imagem única).
6. **Duas linhas de imagem Alibaba**: Qwen-Image-2.0 (renderização de texto/mangá storyboard) e Wan-Image (realismo de retrato) têm posicionamentos diferentes; avaliar por cenário, não são substitutas.
7. **HappyHorse open source comercializável**: modelo base/distill/super-res/código de inference totalmente open source, amigável ao ArcReel; mas há muitos sites de terceiros com o mesmo nome — na integração, usar só a API oficial Alibaba Cloud BaiLian.
8. **Diferenças de site internacional**: MiniMax minimaxi.com (doméstico) vs minimax.io (internacional) Keys não interoperam; Alibaba Keys das três regiões independentes; Kling app.klingai.com (China) vs klingai.com (global).
9. **Leaderboards com cautela**: Artificial Analysis atualiza rápido; vantagem especial de chinês de modelos domésticos não equivale a liderança em benchmarks globais genéricos; seleção pela medição real "chinês+romance".
10. **Lista de modelos Kling já conferida em primeira mão, mas preço ainda no console**: lista de modelos de vídeo/imagem Kling conferida item a item com a doc oficial (v3/v3-omni/v2-6/v2-5-turbo/o1/image-o1 etc.); matriz de capacidades segundo o oficial. Dois pontos obrigatórios: ① tabela oficial marca **"controle de som (voz humana)" de vídeo v3/v3-omni como ❌**; só `kling-v2-6` pro suporta voz humana no vídeo — conflita com alegações de terceiros de "áudio-vídeo nativo no v3"; prevalece o oficial; ② valor exato de inspiração por faixa não está na doc oficial; precisa login no console app.klingai.com.

---

## 8. Referências (fontes oficiais de primeira mão)

- Catálogo de modelos Alibaba Cloud BaiLian (lista top, atualização 2026-05-21): https://help.aliyun.com/zh/model-studio/models
- Catálogo de modelos de vídeo Alibaba Cloud BaiLian: https://help.aliyun.com/zh/model-studio/video-generate-edit-model/
- Preços de modelos Alibaba Cloud BaiLian: https://help.aliyun.com/zh/model-studio/model-pricing
- API text-to-image Qwen-Image: https://help.aliyun.com/zh/model-studio/qwen-image-api
- Qwen-Image-Edit edição de imagem: https://help.aliyun.com/zh/model-studio/qwen-image-edit-guide
- API text-to-video Tongyi Wanxiang: https://help.aliyun.com/zh/model-studio/text-to-video-api-reference
- Página de produto LLM Qwen (Qwen3.7-Max / Qwen-Image / Wan2.7): https://www.aliyun.com/product/tongyi
- Lista oficial de modelos de vídeo Kling (primeira mão): https://klingai.com/document-api/apiReference/model/videoModels
- Lista oficial de modelos de imagem Kling (primeira mão): https://klingai.com/document-api/apiReference/model/imageModels
- Página oficial de preços Kling (primeira mão): https://klingai.com/dev/pricing
- Docs de desenvolvimento da plataforma aberta Kling: https://app.klingai.com/cn/dev/document-api
- Preços MiniMax (pricing-paygo): https://platform.minimaxi.com/docs/guides/pricing-paygo
- Dinâmica de releases de modelos MiniMax: https://platform.minimaxi.com/docs/release-notes/models
- API image-to-video MiniMax: https://platform.minimaxi.com/docs/api-reference/video-generation-i2v
- MiniMax S2V-01: https://platform.minimax.io/docs/api-reference/video-generation-s2v
- Lançamento MiniMax Hailuo 2.3: https://www.minimax.io/news/minimax-hailuo-23

---

**Alinhamento de arquitetura**: fornecedores preset ArcReel `PROVIDER_REGISTRY` + `lib/{text,image,video}_backends/`
