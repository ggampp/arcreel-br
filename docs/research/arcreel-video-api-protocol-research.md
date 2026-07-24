# Relatório de pesquisa de adaptação de protocolos de API de vídeo do ArcReel

**Data de corte da pesquisa**: 2026-05-27  
**Uso**: material de entrada para redação de PRD e documentos de design posteriores  
**Autor**: pesquisa assistida (Claude)  
**Contexto relacionado**: expansão do ecossistema de fornecedores de vídeo do ArcReel, integração do ecossistema de fornecedores customizados

---

## 0. Escopo e posicionamento da pesquisa

Este relatório é uma compilação de material de **natureza de pesquisa** e **não inclui** estrutura de diretórios concreta, design de classes Adapter nem plano de implementação. Esse conteúdo deve sair na fase de PRD e documento de design, com base na arquitetura atual `lib/video_backends/` + `lib/custom_provider/` do ArcReel.

Perguntas cobertas pela pesquisa:
1. Quais são os padrões de fato do formato de porta de API de vídeo de relay stations
2. Specs de API das principais plataformas oficiais de geração de vídeo
3. Matriz de suporte de capacidades de cada protocolo (text-to / image-to / first-last-frame / reference-to / video extend / áudio / lip-sync / consistência de personagem)
4. Avaliação de viabilidade e sugestão de prioridade de cada protocolo
5. Detalhes completos de spec de API do protocolo de maior prioridade
6. Seleção de abordagem de integração de fornecedor customizado (plugin vs declarativo)
7. Viabilidade e opções de design do mecanismo de plugin em runtime (suporte à função planejada de compartilhamento comunitário de protocolos)

Fora do escopo da pesquisa:
- Organização de diretórios / herança de classes / nomenclatura de arquivos no nível de código do ArcReel
- Mudanças de schema de banco / migrações Alembic
- Mudanças de UI do frontend
- Timeline concreta de implementação

---

## 1. Baseline de pesquisa de arquitetura do ArcReel (importante: alinhado ao status quo)

> Esta seção é o **pré-requisito para entender as conclusões da pesquisa a seguir**; todas as recomendações de adaptação de protocolo devem se encaixar nesta arquitetura.

### 1.1 Camada de abstração de video backend

O ArcReel já tem abstração madura de geração de vídeo em `lib/video_backends/`:

| Elemento-chave | Local | Descrição |
|---|---|---|
| Protocol `VideoBackend` | `lib/video_backends/base.py` | Contrato duck typing: `name` / `model` / `capabilities` / `generate()` |
| Enum `VideoCapability` | `lib/video_backends/base.py` | Bitmap de capacidades: `TEXT_TO_VIDEO` / `IMAGE_TO_VIDEO` / `GENERATE_AUDIO` / `NEGATIVE_PROMPT` / `VIDEO_EXTEND` / `SEED_CONTROL` / `FLEX_TIER` |
| `VideoGenerationRequest` / `VideoGenerationResult` | Idem | Classes de dados unificadas de request/response |
| `register_backend(name, factory)` | `lib/video_backends/registry.py` | Mecanismo de registro |
| Backends já implementados | `gemini.py` / `ark.py` / `grok.py` / `openai.py` / `newapi.py` / `vidu.py` | 6 fornecedores |

**Convenção de vocabulário ArcReel**: usa-se **backend** (objeto cliente construído por provider + model, que de fato chama a API) para o gerador; o glossário `_Avoid` marca para evitar a palavra `adapter`. Na essência é o papel Adapter do paradigma Ports & Adapters, mas o ArcReel unifica como backend para manter semântica derivada de provider, espelhamento com frontend e nomenclatura consistente das três mídias (alinha com a convenção SQLAlchemy / Django de chamar backend o papel análogo). Discussão de alinhamento de arquitetura em 9.1.

### 1.2 Sistema de fornecedor customizado

`lib/custom_provider/` já permite ao usuário conectar qualquer relay station compatível OpenAI/Google:

| Elemento-chave | Papel |
|---|---|
| ORM `CustomProvider` (tabela DB) | `discovery_format` ∈ {openai, google} + `base_url` + `api_key` |
| ORM `CustomProviderModel` (tabela DB) | Cada modelo tem um `endpoint` (key do ENDPOINT_REGISTRY) |
| `ENDPOINT_REGISTRY` | Fonte única de verdade da afiliação de protocolo |
| `infer_endpoint()` | Heurística para inferir endpoint a partir de model_id |
| Factory `create_custom_backend()` | Despacha para o VideoBackend correspondente pelo endpoint |
| UI do frontend | CRUD na página de configurações, descoberta automática `/v1/models` |

**ENDPOINT_REGISTRY atual tem 6 entradas** (excluindo anthropic-messages etc. fora desta rodada de pesquisa):

| Endpoint Key | media_type | family | Status |
|---|---|---|---|
| `openai-chat` | text | openai | Implementado |
| `gemini-generate` | text | google | Implementado |
| `openai-images` | image | openai | Implementado |
| `gemini-image` | image | google | Implementado |
| `openai-video` | video | openai | Implementado (**compatível OpenAI Sora `/v1/videos`**) |
| `newapi-video` | video | newapi | Implementado (**protocolo próprio NewAPI `/v1/video/generations`**) |

### 1.3 Fornecedores preset

`PROVIDER_REGISTRY` em `lib/config/registry.py` já tem 5 presets:

- `gemini-aistudio` / `gemini-vertex` — linha completa Veo 3.1
- `ark` — Volcengine Ark (Seedance 1.5 Pro / 2.0 / 2.0 Fast já registrados)
- `grok` — xAI Grok Imagine Video
- `openai` — Sora 2 / Sora 2 Pro
- `vidu` — linha completa Vidu Q3 (inclui reference-to-video)

### 1.4 Binding de protocolo no nível do modelo (decisão de arquitetura)

O ArcReel já confirmou em `2026-04-26-custom-provider-model-endpoint-design`:

> Uma relay station = um provider; modelos diferentes no mesmo provider podem usar protocolos totalmente diferentes;  
> a afiliação de protocolo desce para a camada do modelo (campo `CustomProviderModel.endpoint`);  
> `discovery_format` na camada do provider serve só para descoberta de modelos, desacoplado do protocolo de chamada.

**Todo design posterior de adaptação de protocolo deve respeitar essa restrição de arquitetura.**

---

## 2. Paisagem do ecossistema de protocolos de relay stations (indução de padrões de fato)

Após cobrir 15+ relay stations mainstream (repositório principal NewAPI, AiHubMix, Qiniu, Wisdom Gate, AI/ML API, APIMart, EvoLink, CometAPI, Kie.ai, PiAPI, useapi.net, kazhang.ai, apiyi, burn.hair, closeai etc.), indutores do fato de **quatro escolas coexistindo**:

### 2.1 Escola A: OpenAI Sora `/v1/videos`

**Endpoint**: `POST /v1/videos` + `GET /v1/videos/{video_id}` + `GET /v1/videos/{video_id}/content`  
**Forma**: multipart/form-data ou JSON  
**Parâmetros**: `model` + `prompt` + `seconds` (string) + `size` ("1280x720") + `input_reference`  
**Auth**: `Authorization: Bearer`  
**Instâncias representativas**: OpenAI oficial, AiHubMix, caminho sora Qiniu, Wisdom Gate, Azure OpenAI, endpoint `openai-video` já no ArcReel

**Fatos-chave**:
- Anúncio oficial OpenAI: **Sora 2 / Sora 2 Pro serão descontinuados em 2026-09-24** (developer notification 2026-03-24)
- O padrão de fato do caminho permanece; relay stations por inércia o usam para carregar outros modelos
- No caminho compatível Qiniu, a resposta de query já devolve `task_result.videos[0].url`; no oficial OpenAI precisa de segundo GET `/content`

### 2.2 Escola B: protocolo próprio NewAPI `/v1/video/generations`

**Endpoint**: `POST /v1/video/generations` (note o plural) + `GET /v1/video/generations/{task_id}`  
**Forma**: JSON puro  
**Parâmetros**: `model` + `prompt` + `image` + `duration` (número) + `width`/`height` + `metadata` (objeto)  
**Auth**: `Authorization: Bearer`  
**Instâncias representativas**: todas as relay stations baseadas em NewAPI / OneAPI (DMXAPI, closeai, burn.hair e dezenas); endpoint `newapi-video` já no ArcReel

**Fatos-chave**:
- Campo `metadata{}` é caixa-preta de passthrough vendor-specific (a doc NewAPI lista só `image_tail`/`negative_prompt`/`seed` do Kling e `req_key`/`image_urls`/`aspect_ratio` do Jimeng; o resto depende do middleware da relay)
- Completude do passthrough de metadata varia enormemente entre relays; o mesmo `camera_control` do Kling funciona na DMXAPI e se perde em alguns NewAPI self-hosted
- Máquina de estados: `queued / in_progress / completed / failed`

### 2.3 Escola C: generations v2 genérico (um endpoint para todos os modelos)

**Endpoint**: `POST /v2/video/generations` ou `/v2/videos/generations` (pequenas diferenças por casa)  
**Forma**: JSON puro  
**Característica central**: **endpoint único + troca no campo model**, carrega dezenas a centenas de modelos (Kling/Veo/Sora/Hailuo/Wan/Seedance todos no mesmo URL)  
**Auth**: `Authorization: Bearer`  
**Instâncias representativas**:
- **AI/ML API** (aimlapi.com) `/v2/video/generations` — representante mais típico da escola C
- **getimg.ai** `/v2/videos/generations`
- **APIMart** `/v1/videos/generations`
- **EvoLink** `/v1/videos/generations`
- **Caminho veo Qiniu** `/v1/videos/generations`
- **xAI oficial** `/v1/videos/generations` (**o oficial já é essa forma**)
- **CometAPI** `/volc/v3/contents/generations/tasks` (detalhe de caminho diferente, mas a ideia é a mesma)

**Fatos-chave**:
- Na prática é **discriminated union by model**: um URL aceita 60+ model ids, mas o conjunto de campos opcionais de cada model é totalmente diferente
- Ex.: no mesmo endpoint, Kling recebe `cfg_scale` / `negative_prompt` / `image_url` / `last_image_url`; Veo 3.1 recebe `image_urls[]`; Seedance recebe `reference_images[]` / `reference_audios[]` / `reference_videos[]` / `generate_audio`; Sora recebe `resolution` / `image_url`
- Nomenclatura de model altamente fragmentada: AIMLAPI usa `kling-video/v1/standard/text-to-video`, APIMart usa `sora-2-vip`, getimg.ai usa `happyhorse-1` (marca própria)
- **Adotada por muitas relay stations**; é o segundo padrão de fato além da escola B
- **Ainda não coberta** no ENDPOINT_REGISTRY atual do ArcReel

### 2.4 Escola D: estilo verbo create/submit

**Endpoint**: `POST /api/v1/jobs/createTask`, `POST /api/v1/task`, `POST /v1/videos/create` etc. (create + query separados)  
**Forma**: JSON puro, parâmetros aninhados no subobjeto `input{}`  
**Instâncias representativas**:
- **Kie.ai** `/api/v1/jobs/createTask` + `/api/v1/jobs/recordInfo`
- **PiAPI** `/api/v1/task` + `/api/v1/task/{task_id}`
- **useapi.net** `/v1/{vendor}/videos/create`
- **Suchuang** `/api/sora2/submit`
- **laozhang.ai** `/veo/v1/api/video/submit`

**Fatos-chave**:
- Internamente a escola D não é unificada; caminho e detalhes de parâmetros diferem muito por casa; um backend não reutiliza
- PiAPI tem status code não padrão (outer `status: "completed"` string + inner `output.status: 99` integer = completo); precisa de julgamento em duas camadas

### 2.5 Observação de distribuição das escolas

Por contagem de relay stations cobertas na pesquisa (**não é market share rigoroso**):

- Escola A (compatível OpenAI Sora): alta cobertura; obrigatória para clientes overseas/compliance
- Escola B (própria NewAPI): **monopólio de fato de relay stations self-hosted domésticas**; cobertura mais alta
- Escola C (generations v2 genérico): **adotada por muitas relay stations**; agregadores overseas e xAI oficial; cobertura em segundo
- Escola D (estilo verbo): internamente dispersa; majoritariamente custom por casa; cobertura por casa limitada

---

## 3. Pesquisa de API de plataformas oficiais de vídeo mainstream

### 3.1 Plataformas já integradas no ArcReel

| Plataforma | Status atual | Afiliação de protocolo | Notas |
|---|---|---|---|
| Google Veo 3.1 | Implementado | Dual backend Vertex AI + AI Studio | Text-to/image-to/extend/áudio/negative prompt |
| Volcengine Ark Seedance 2.0 | Implementado | Ark SDK | 2.0 registrado mas **multi-modal ref e video extend não habilitados** |
| xAI Grok Imagine | Implementado | xAI SDK | Text-to/image-to/reference-to |
| OpenAI Sora 2 | Implementado | openai SDK | Inclui `create_and_poll` |
| Vidu Q3 | Implementado | httpx | Text-to/image-to/**reference-to-video** (já aplicado no modo reference-to-video) |

### 3.2 Plataformas oficiais pesquisadas mas ainda não integradas

#### Kling oficial

- **Base URL**: `https://api.klingai.com`
- **Auth**: JWT HS256, payload `{iss: ak, exp: now+1800, nbf: now-5}`, expira em 30 min
- **Endpoints**: multi-endpoint por intent — `/v1/videos/text2video`, `/image2video`, `/multi-image2video`, `/video-extend`, `/lip-sync`
- **Capacidades**: T2V / I2V / FLF (modo pro `image_tail`) / R2V (`elements[]` 1.6) / Extend / Audio (2.6 pro `enable_audio`) / LipSync
- **Armadilhas-chave**:
  - string de status é `succeed`, não `succeeded`
  - URL do vídeo em `$.data.task_result.videos[0].url`
  - 500 = rejeição de moderação de conteúdo (usar campo error, não message)
  - `kling-2.1-master` não suporta campo `mode`; modelos 2.x não suportam `cfg_scale`
- **Valor no cenário de romance**: um dos modelos de vídeo mais fortes na China; opção de conexão direta obrigatória para self-host de produção

#### Alibaba DashScope Tongyi Wanxiang

- **Base URL (Pequim)**: `https://dashscope.aliyuncs.com/api/v1`
- **Base URL (Singapura)**: `https://dashscope-intl.aliyuncs.com/api/v1`
- **Auth**: `Authorization: Bearer` + header obrigatório `X-DashScope-Async: enable`
- **Endpoints**: `POST /services/aigc/video-generation/video-synthesis` (wan2.5+ multimodal) / `POST /services/aigc/image2video/video-synthesis/` (wan2.1 / wan2.2-s2v) + `GET /tasks/{task_id}`
- **Capacidades**: T2V / I2V / FLF (wan2.1-kf2v) / R2V (`ref_image_urls[]`) / Extend / Audio / LipSync digital human (wan2.2-s2v)
- **Mesmo protocolo cobre vários modelos**: wan2.7-t2v / wan2.6-i2v-flash / wan2.1-kf2v-plus / wan2.2-s2v
- **Armadilhas-chave**:
  - Omitir `X-DashScope-Async: enable` = esperar síncrono até morrer
  - wan2.7 usa `resolution`+`ratio`; wan2.6 usa `size` ("1280*720", asterisco)
  - Máquina de estados toda em maiúsculas: `PENDING / RUNNING / SUCCEEDED / FAILED / CANCELED / SUSPENDED / UNKNOWN`
  - URL temporária OSS válida **24h**; task_id também 24h
  - `IPInfringementSuspect` / `DataInspectionFailed` são erros de moderação de conteúdo
- **Valor no cenário de romance**:
  - Prompt chinês do wan2.7 muito longo; uma request cabe roteiro completo de storyboard (5 planos 1500 caracteres OK)
  - `shot_type: multi` narrativa multi-shot nativa

#### MiniMax Hailuo oficial

- **Base URL (global)**: `https://api.minimax.io/v1`
- **Base URL (doméstico)**: `https://api.minimaxi.com/v1`
- **Auth**: `Authorization: Bearer`
- **Endpoints**: `POST /video_generation` + `GET /query/video_generation?task_id={id}` + **`GET /files/retrieve?file_id={id}`** (URL em dois passos)
- **Capacidades**: T2V / I2V / FLF / R2V (`subject_reference` do S2V-01) / Audio (Hailuo 2.3) / modelos Director com instruções de plano embutidas no prompt
- **Armadilhas-chave**:
  - **URL em dois passos**: query não devolve URL do vídeo, só `file_id`; precisa chamar File API de novo
  - **Download URL válida só 9 horas** (32.400 s, texto do anúncio oficial) — a mais curta de todas as plataformas
  - status com primeira letra maiúscula: `Preparing / Queueing / Processing / Success / Fail`
  - Registro de webhook precisa echo de `challenge`, timeout 3 s
  - Endpoints doméstico / global diferentes; API Keys independentes
  - `base_resp.status_code != 0` = erro de negócio (HTTP 200 ainda pode falhar por dentro)
- **Valor no cenário de romance**: rei do custo-benefício, física forte

#### Runway Gen-3 / Gen-4 / Gen-4.5

- **Base URL**: `https://api.dev.runwayml.com/v1`
- **Auth**: `Authorization: Bearer` + header obrigatório `X-Runway-Version: 2024-11-06`
- **Endpoints**: `/image_to_video` / `/text_to_video` / `/video_to_video` + `/tasks/{id}`
- **Capacidades**: T2V (gen4.5) / I2V / R2V (gen4_image `@mention`) / edição de vídeo Aleph / Act-Two LipSync
- **Armadilhas-chave**:
  - Sem webhook; precisa poll
  - Upload de arquivo via URI ephemeral
  - duration só `5 | 10`
- **Valor de negócio**: demanda forte de ads/e-commerce overseas; Gen-4.5 1º no Arena

#### Luma Dream Machine (Ray-2)

- **Base URL**: `https://api.lumalabs.ai/dream-machine/v1`
- **Auth**: `Authorization: Bearer`
- **Endpoints**: **único `POST /generations`** + `GET /generations/{id}`
- **Capacidades**: T2V / I2V / FLF / Extend / Loop (**expressa todos os intents com dois slots elegantes `keyframes.frame0/frame1`**)
- **Design-chave**: union type de keyframes `{type: "image"|"generation", url|id}`; frame0 com generation id = Extend
- **Armadilha-chave**: union type de keyframes precisa de modelagem especial; não reutiliza campo `image_url`

#### Pika 2.2

- **API oficial não é self-service**; só para parceiro B2B
- **Único caminho de integração**: via fal.ai `queue.fal.run/fal-ai/pika/v2.2/{capability}`
- **Capacidades exclusivas**: Pikaframes (interpolação multi-frame 2-5 keyframes), Pikascenes (fusão multi-img, `ingredients_mode: creative|precise`)

#### PixVerse

- **Base URL**: `https://app-api.pixverse.ai`
- **Auth**: header custom `API-KEY:` + chave de idempotência obrigatória `Ai-trace-id`
- **Endpoints**: `/openapi/v2/video/{text|img|transition|extend|fusion|lipsync}/generate`
- **Capacidades**: T2V / I2V / FLF (Transition) / R2V (Fusion) / Extend / Audio (V5.5+) / LipSync
- **NewAPI sem channel nativo**; deve ser conexão oficial direta

#### ByteDance Jimeng (Volcengine CV)

- **Base URL**: `https://visual.volcengineapi.com`
- **Auth**: **assinatura estilo AWS V4** (Volcengine SigV4)
- **Endpoints**: `?Action=CVSync2AsyncSubmitTask` / `?Action=CVSync2AsyncGetResult`
- **Complexidade altíssima**; recomenda-se camada de relay em vez de conexão direta

#### fal.ai

- **Base URL**: `queue.fal.run/{vendor}/{model}/{capability}`
- **Auth**: fal.ai Key
- **Características**: suporte nativo a Webhook (`?fal_webhook=URL`) + verificação de assinatura JWKS
- **Valor**: único caminho viável de integração do Pika 2.2; também conecta Luma / Veo / Kling e multi-modelos

---

## 4. Matriz de capacidades (comparação horizontal)

### 4.1 Definição das dimensões de capacidade

- **T2V**: text-to-video, só prompt
- **I2V first frame**: image-to-video (restrição de first frame)
- **FLF**: first-and-last-frame
- **R2V**: reference-to-video (várias refs mantendo consistência de personagem/objeto, **não é first frame**)
- **Extend**: extensão/continuação de vídeo
- **Audio**: geração conjunta nativa áudio-vídeo
- **LipSync**: lip-sync
- **Character**: consistência de personagem (registro de entidade nomeada)

### 4.2 Escola de relay station × capacidades

✅ nativo ｜ 🟡 suporte parcial/modelo limitado ｜ ❌ não suporta

| Escola / plataforma | T2V | I2V | FLF | R2V | Extend | Audio | LipSync | Character |
|---|---|---|---|---|---|---|---|---|
| **Escola A** OpenAI Sora `/v1/videos` | ✅ | ✅ | ❌ | 🟡 characters API | ✅ extensions | ✅ | ❌ | ✅ |
| **Escola B** NewAPI `/v1/video/generations` | ✅ | ✅ | 🟡 metadata.image_tail | 🟡 passthrough metadata | ❌ | 🟡 passthrough | ❌ | ❌ |
| **Escola C** AIMLAPI `/v2/video/generations` | ✅ | ✅ | ✅ | ✅ | 🟡 vendor-specific | ✅ | ❌ | ✅ |
| **Escola C** APIMart `/v1/videos/generations` | ✅ | ✅ | ❌ | 🟡 prompt-mention | 🟡 sora ref | ✅ Sora2 | ❌ | 🟡 prompt-mention |
| **Escola D** Kie.ai `jobs/createTask` | ✅ | ✅ | 🟡 model-specific | ✅ character_id_list ≤5 | 🟡 veo extend | ✅ veo/sora2/wan2.7 | ❌ | ✅ |
| **Escola D** PiAPI `task` | ✅ | ✅ | ✅ image_tail_url | ✅ elements | ✅ task_type=extend | ✅ Seedance 2.0 | ✅ task independente | ✅ |

### 4.3 Plataforma oficial × capacidades

| Plataforma | T2V | I2V | FLF | R2V | Extend | Audio | LipSync | Character |
|---|---|---|---|---|---|---|---|---|
| OpenAI Sora 2 | ✅ | ✅ | ❌ | 🟡 characters | ✅ 6×20s=120s | ✅ | ❌ | ✅ |
| Google Veo 3.1 | ✅ | ✅ | ✅ | ✅ | 🟡 /extend | ✅ 48kHz | ❌ | 🟡 |
| Volcengine Seedance 2.0 | ✅ | ✅ first_frame | ✅ last_frame | ✅ 9 imgs + 3 vídeos + 3 áudios | ✅ | ✅ | ✅ phoneme 8 idiomas | ✅ omni-ref |
| Kling 2.6 / 3.0 | ✅ | ✅ | ✅ modo pro | ✅ elements ≤4 | ✅ extend | ✅ 2.6 pro | ✅ lip-sync task | ✅ multi-image |
| MiniMax Hailuo 02 / 2.3 | ✅ | ✅ | ✅ | ✅ subject_reference | ❌ | ✅ 2.3 | ❌ | ✅ S2V-01 |
| PixVerse V5.5 / V6 | ✅ | ✅ | ✅ Transition | ✅ Fusion | ✅ extend | ✅ V5.5+ | ✅ | ✅ ≤3 imgs fusion |
| Vidu Q3 | ✅ | ✅ | ✅ | ✅ ref_image_urls ≤7 | 🟡 | ✅ + bgm | ❌ | ✅ |
| Runway Gen-4.5 | ✅ | ✅ | ❌ | ✅ gen4_image @mention ≤3 | 🟡 expand | ❌ | ✅ Act-Two | ✅ |
| Pika 2.2 | ✅ | ✅ | ✅ Pikaframes | ✅ Pikascenes ≤5 | 🟡 | ❌ | ❌ | ✅ |
| Luma Ray-2 | ✅ | ✅ keyframes.frame0 | ✅ frame0+frame1 | ❌ | ✅ generation id | ❌ | ❌ | 🟡 chain |
| Alibaba Wan 2.7 | ✅ | ✅ | ✅ | ✅ placeholder Image1..5 | ✅ | ✅ | ✅ s2v digital human | ✅ |
| xAI Grok Imagine | ✅ | ✅ image:{url} | ❌ | ✅ reference_images ≤7 | ✅ extensions | ❌ | ❌ | 🟡 |

### 4.4 Observações-chave

- **7 nomes de campo R2V**: `characters` / `reference_images` / `image_urls` / `reference_image_urls` / `elements` / placeholders do prompt Wan 2.7 / `subject_reference`
- **4 nomes de campo FLF**: `last_frame_image` / `image_tail` / `last_image_url` / `keyframes.frame1`
- **Expressão de duration** inconsistente em todas as plataformas: string `"5"` / int `5` / frames / enum `6|10` / Luma `"5s"` / Sora enum string `"4"|"8"|"12"|"16"|"20"`
- **Semântica de geração síncrona áudio-vídeo** se sobrepõe: geração conjunta (Veo/Sora/Seedance/Vidu Q3) vs switch explícito (Kling 2.6 pro `enable_audio` / Vidu `generate_audio`) vs automático (Hailuo 2.3)

---

## 5. Tabela de alinhamento de parâmetros (15 dimensões horizontais)

| Dimensão | OpenAI Sora 2 | xAI Grok | Kling | MiniMax | Veo 3.1 | Wan 2.7 | Runway | Luma | Vidu Q3 | Pika 2.2 | Seedance 2.0 | NewAPI escola B | aimlapi escola C | Kie.ai escola D | PiAPI escola D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **prompt** | `prompt` | `prompt` | `prompt` | `prompt` | `prompt` | `prompt` | `promptText` | `prompt` | `prompt` | `prompt` | `content[].text` | `prompt` | `prompt` | `input.prompt` | `input.prompt` |
| **negative_prompt** | — | — | `negative_prompt` | — | `negative_prompt` | `negative_prompt` ≤500 | — | — | — | `negative_prompt` | — | `metadata.negative_prompt` | `negative_prompt` | `input.negative_prompt` | `input.negative_prompt` |
| **duration** | `seconds: "4\|8\|12\|16\|20"` | `duration: 1-15` | `duration: "5"\|"10"` | `duration: 6\|10` | `seconds: "8"` | `duration: 2-15` | `duration: 5\|10` | `duration: "5s"\|"9s"` | `duration: 1-16` | `duration: 5\|10` | `duration: 4\|5\|6\|8\|10\|12\|15` | `duration: 5` int | `duration` string | `input.n_frames`/`input.duration` | `input.duration: 5` |
| **resolution** | `size: "1280x720"` | `resolution: "720p"` | `aspect_ratio` | `resolution: "1080P"` | `aspectRatio` | `resolution: "720P"` + `ratio` | `ratio: "1280:720"` | `resolution: "540p..4k"` | `resolution: "540p"\|"720p"\|"1080p"` | `aspect_ratio` + `resolution` | `ratio: "16:9"` + `resolution` | `size: "1920x1080"` | model decides | `input.size: "standard"\|"hd"` | `input.aspect_ratio` |
| **seed** | — | **nenhum** | (legado) | — | — | `seed` | `seed` | — | `seed: -1` random | `seed` | `seed` | `metadata.seed` | `seed` | — | `input.seed` |
| **First frame** | `input_reference` | `image:{url}` | `image_url` | `first_frame_image` | `image_url` | `first_frame_url` | `promptImage` | `keyframes.frame0` | `image` | `image_url` | `first_frame_url` | `image` | `image_url` | `input.image_urls[0]` | `input.image_url` |
| **Last frame** | ❌ | ❌ | `image_tail` | `last_frame_image` | ❌ | `last_frame_url` | ❌ | `keyframes.frame1` | `last_image` | `images[1]` (Pikaframes) | `last_frame_url` | `metadata.image_tail` | `last_image_url` | (alguns models) | `input.image_tail_url` |
| **Array de refs** | `characters:[{id}]` | `reference_images:[{url}]` ≤7 | `elements:[]` ≤4 | `subject_reference` single | `image_urls:[]` | placeholder `Image1..5` | `referenceImages` ≤3 | — | `reference_image_urls:[]` ≤7 | `images:[]` ≤5 | `reference_images:[]` ≤9 | `metadata.image_urls:[]` | `image_urls`/`reference_images` | `input.character_id_list` | `input.elements:[]` |
| **Switch de áudio** | (auto) | — | `enable_audio` (2.6 pro) | (2.3 auto) | (auto) | (auto) | — | — | `generate_audio` + `bgm` | — | `generate_audio` | (passthrough) | (model decide) | `input.sound` (2.6) | `input.enable_audio` |
| **Callback** | — poll | — poll | poll | poll | LRO | DashScope async | poll | poll | poll | poll | `callback_url` | `webhook_url` (parcial) | poll | `callBackUrl` | `config.webhook_config` |
| **Modo/qualidade** | model decide | — | `mode: "std"\|"pro"` | `prompt_optimizer` | model variant | — | model variant | model variant | `movement_amplitude` | `ingredients_mode` | model variant `-fast` | — | model id contém mode | `input.size: "standard"\|"hd"` | `input.mode: "std"\|"pro"` |
| **CFG** | — | — | `cfg_scale: 0-1` (v1) | — | — | — | — | — | — | `cfg_scale` (legacy) | — | (passthrough) | `cfg_scale` | — | `input.cfg_scale` |
| **Header especial** | — | — | JWT 30min | — | OAuth2 | `X-DashScope-Async` | `X-Runway-Version` | — | — | — | — | — | — | — | — |
| **Caminho task_id** | `$.id` | `$.request_id` | `$.data.task_id` | `$.task_id` | LRO operation | `$.output.task_id` | `$.id` | `$.id` | `$.task_id` | `$.request_id` | `$.id` | `$.task_id` | `$.id` | `$.data.taskId` | `$.task_id` |
| **Caminho URL do vídeo** | segundo GET /content | `$.video.url` | `$.data.task_result.videos[0].url` | segundo file_id | `$.video.uri` | `$.output.video_url` | `$.output[0]` | `$.assets.video` | `$.creations[0].url` | `$.video.url` | `$.content.video_url` | `$.url` | `$.video.url` / `$.assets.video` | `$.data.response.resultUrls[0]` | `$.output.works[0].video.url` |

### 5.1 Diferenças de mapeamento de máquina de estados

Strings de estado final totalmente inconsistentes entre casas; cada uma precisa do próprio mapeamento:

| Plataforma | queued | running | succeeded | failed |
|---|---|---|---|---|
| OpenAI Sora | `queued` | `in_progress` | `completed` | `failed` |
| NewAPI escola B | `queued` | `in_progress` | `completed` | `failed` |
| Alibaba DashScope | `PENDING` (**todas maiúsculas**) | `RUNNING` | `SUCCEEDED` | `FAILED` |
| Volcengine Ark Seedance | `queued` | `running` | `succeeded` | `failed` |
| Kling | `submitted` | `processing` | **`succeed` (não succeeded)** | `failed` |
| MiniMax Hailuo | `Queueing` / `Preparing` | `Processing` | **`Success` (primeira letra maiúscula)** | `Fail` |
| PiAPI inner | — | — | `output.status: 99` (**inteiro**) | `output.status: <99` |
| Runway | `PENDING` | `RUNNING` | `SUCCEEDED` | `FAILED` |

### 5.2 Tempo de expiração da URL do vídeo (link temporário OSS)

**Todas as plataformas oficiais usam URL temporária; é obrigatório rehospedar imediatamente**:

| Plataforma | Expiração | Nível de risco |
|---|---|---|
| **MiniMax Hailuo** | **9 horas** (32.400 s) | 🔴 a mais curta de todas |
| OpenAI Sora 2 | Doc e medição real divergem (doc 24h, alguns usuários relatam 1h) | 🟠 |
| Vertex AI Veo | Curto após conclusão da LRO | 🟠 |
| Volcengine Ark Seedance | 24 horas (URL temporária TOS) | 🟡 |
| Alibaba DashScope Wan | 24 horas | 🟡 |
| Runway | 24-48 horas | 🟡 |
| Luma Ray-2 | Mais longa | 🟢 |
| Kling | 30 dias (inferido da restrição do endpoint lip-sync) | 🟢 |
| Qiniu compatível sora | 7 dias | 🟢 |

---

## 6. Sugestão de prioridade de protocolos

> Dimensões de score de prioridade (cada uma 1-5): cobertura do ecossistema de relay / cobertura de capacidade de modelo / completude da doc / complexidade de implementação (mais simples = maior) / estabilidade de longo prazo / demanda do cenário romance ArcReel

### 6.1 Protocolos já implementados (manter)

| Protocolo | Endpoint ArcReel | Status | Notas |
|---|---|---|---|
| Compatível OpenAI Sora | `openai-video` | ✅ Implementado | Atenção deprecation 2026-09-24 |
| Próprio NewAPI | `newapi-video` | ✅ Implementado | Passthrough metadata precisa expandir tabela de mapeamento vendor |
| Linha completa Veo 3.1 | provider gemini-* | ✅ Implementado | — |
| Seedance 1.5/2.0 | provider ark | ✅ Implementado | Multi-modal ref + Extend do 2.0 não habilitados |
| Grok Imagine | provider grok | ✅ Implementado | — |
| Linha completa Vidu Q3 | provider vidu | ✅ Implementado | Modo reference-to-video já em produção |

### 6.2 P0 — sugestão de completar no v1.0

| Protocolo | Motivo de entrar no P0 | Complexidade |
|---|---|---|
| **Escola C `/v2/video/generations`** | **Adotada por muitas relay stations** (AIMLAPI / xAI oficial / getimg.ai / APIMart / EvoLink / Qiniu veo / CometAPI etc.); segundo maior padrão de fato além da escola B | Média (discriminated union by model; precisa de branches de schema model-specific) |
| **Protocolo oficial Kling** | Modelo preferido de usuários domésticos de romance→vídeo; self-host de produção precisa de conexão direta para estabilidade; auth JWT especial | Média-alta (JWT HS256 + cache de token 30min; multi-endpoint por intent) |
| **Alibaba DashScope (Tongyi Wanxiang Wan)** | **Valor único** no cenário romance: prompt chinês longo do wan2.7 + `shot_type: multi` multi-shot nativo; mesmo protocolo cobre wan2.7/2.6/2.1-kf2v/2.2-s2v multi-modelos | Média (X-DashScope-Async + input/parameters aninhados + roteamento multi-model) |
| **MiniMax Hailuo oficial** | Física forte, rei do custo-benefício; modelo de URL em dois passos da File API diferente das outras plataformas; rehospedagem de URL 9h a mais urgente | Média-alta (fluxo File API em dois passos + webhook challenge) |

### 6.3 P1 — complemento v1.x

| Protocolo | Motivo |
|---|---|
| **Kie.ai escola D** `/api/v1/jobs/createTask` | Representante overseas do estilo verbo; cobre parte das relay stations de nicho |
| **Runway Gen-3/4 oficial** | Demanda ads/e-commerce; header `X-Runway-Version`; sem webhook, poll obrigatório |
| **Extensão multi-modal ref Seedance 2.0** | Modelo já registrado mas reference_images / video_extend não habilitados; eleva o bitmap de capacidades do provider ark existente |

### 6.4 P2 — aguardar feedback de usuários

| Protocolo | Motivo |
|---|---|
| PixVerse oficial | NewAPI sem channel nativo; deve ser conexão oficial; header custom `API-KEY` |
| fal.ai queue API | Único caminho de integração do Pika 2.2; valor de protocolo de fila unificado |
| Luma Dream Machine | Union type de keyframes único, mas baixa demanda no cenário chinês |

### 6.5 P3 — não fazer proativamente

| Protocolo | Motivo |
|---|---|
| Jimeng ByteDance conexão direta | Complexidade de assinatura Volcengine SigV4 altíssima; recomenda-se camada de relay (escolas B/C fazem proxy em geral) |
| Adaptação PiAPI isolada | Alta sobreposição com Kie.ai; cobrir no P1 basta |
| Replicate predictions | Baixa sobreposição com a base de usuários ArcReel |
| Together AI | Idem |

---

## 7. Seleção de abordagem de integração de fornecedor customizado (conclusão)

### 7.1 Comparação de abordagens

Após avaliação detalhada, a abordagem **Plugin (extensão em código Python) supera a abordagem YAML declarativa**:

| Dimensão | Plugin Python | YAML declarativo | Quem vence |
|---|---|---|---|
| Cobertura de protocolo | 100% (fallback) | 50-60% (JWT/SigV4/multipart/fluxo em dois passos não se expressam) | plugin |
| Dificuldade de integração | Escrever classe backend + testes | Escrever YAML + depurar templates | Empate de superfície; na prática plugin mais fácil de depurar |
| Custo de manutenção ArcReel | Cada backend independente, sistema já existe | Precisa de Jinja2 + JSONPath + state mapping + probe + docs novos | plugin (vantagem grande) |
| Experiência de debug | Traceback Python padrão | Erro de schema YAML / erro de render de template / erro de caminho de campo | plugin vence de longe |
| Geração de código assistida por IA | Cursor/Claude Code em 30 s gera backend completo | Precisa primeiro entender schema YAML próprio | plugin (inversão-chave 2024+) |
| Match com persona de usuário ArcReel | Todos desenvolvedores, sabem Python | Adequado a não-programadores | plugin |

### 7.2 Bases de decisão-chave

**O ecossistema de API de vídeo tem 10 classes de capacidade que exigem implementação em Python** (declarativo não expressa):

1. Assinatura JWT oficial Kling (HS256, expira em 30 min, precisa de cache de token)
2. Assinatura estilo SigV4 Volcengine Ark (AKSK + canonical request + HMAC)
3. DashScope em dois passos + troca de base URL por região (credenciais Pequim/Singapura/US West não se misturam)
4. Upload multipart OpenAI Sora (quando arquivo local vira base64)
5. Download MiniMax em dois passos (`file_id → /files/{file_id}` para download_url)
6. Union type de keyframes Luma (`type: image|generation`)
7. Vertex AI Veo (service account JSON + refresh de token OAuth2 + poll LRO duplo)
8. Validação de header version Runway
9. Download de conteúdo OpenAI Sora por variants (`?variant=video|thumbnail|spritesheet`)
10. Status code não padrão PiAPI (outer string + inner `output.status: 99` integer)

**Os cenários que YAML declarativo cobre** são exatamente os que o ArcReel já cobre nos backends embutidos V1 (NewAPI, compatível OpenAI, Kie.ai e outras escolas JSON in/out puro); a motivação do usuário de integrar via declarativo some.

### 7.3 Adaptação ao status quo do ArcReel

O fluxo atual de **integração de fornecedor customizado já existe e não precisa ser redesenhado**:

1. Usuário → página de configurações → adicionar fornecedor customizado
2. Preencher `display_name` + `discovery_format` + `base_url` + `api_key`
3. Clicar [obter lista de modelos] → chama `/api/v1/custom-providers/discover`
4. UI infere endpoint automaticamente
5. Usuário marca habilitado / ajusta endpoint na mão / preenche preço
6. Salva nas tabelas `custom_provider` + `custom_provider_model`

**Ação de engenharia para novos protocolos (ex.: Kling oficial, DashScope)**:
1. Criar classe backend em `lib/video_backends/` (implementar Protocol `VideoBackend`)
2. Registrar nova endpoint key e closure build_backend no `ENDPOINT_REGISTRY`
3. Adicionar regra heurística em `infer_endpoint()`
4. Adicionar `endpoint_xxx_display` nos arquivos i18n (pt/en)
5. Adicionar unit tests com mock httpx

**O usuário não precisa escrever código**, nem alterar qualquer arquivo de config; só, na UI, ao adicionar fornecedor customizado, associar o endpoint correspondente.

### 7.4 Distinção entre dois cenários de "novo backend" (conceito prévio)

É preciso distinguir rigorosamente dois cenários de usuário; os caminhos de integração são totalmente diferentes:

| Cenário | Descrição | Suporte atual |
|---|---|---|
| **Cenário A: protocolo já suportado, conectar nova relay** | Usuário encontra nova agregadora NewAPI / escola C / compatível OpenAI | ✅ operação pura de UI, zero código (já em 7.3) |
| **Cenário B: protocolo ainda não suportado, precisa de adaptação nova** | Usuário quer conectar Kling oficial (JWT) / DashScope (header especial) / algum protocolo privado totalmente novo | ⚠️ hoje precisa alterar código-fonte de `lib/video_backends/` + `ENDPOINT_REGISTRY` |

**Cenário A é a grande maioria da demanda de usuários**; a experiência já é fluida. **Cenário B tem falha de experiência hoje** — conectar novo protocolo exige mudar código-fonte, rebuild, PR ou fork local. A função de plugin em runtime existe exatamente para eliminar a falha do cenário B e suportar compartilhamento comunitário de protocolos.

---

## 7.5 Pesquisa de mecanismo de Plugin em runtime (material de suporte ao planejamento de função)

> Esta seção fornece informações de pesquisa de viabilidade e opções de design para a função «plugin em runtime» já planejada no ArcReel. Objetivo: permitir que o usuário carregue backends de protocolo de vídeo contribuídos por terceiros sem alterar o código-fonte do ArcReel e sem rebuild da imagem, suportando compartilhamento comunitário e baixando a barreira de integração de protocolos customizados. Esta seção **não toma decisões no lugar do PRD**; só resume caminhos viáveis, práticas da indústria, encaixe com a arquitetura existente do ArcReel e problemas em aberto.

### 7.5.1 Status do mecanismo de registro atual do ArcReel (ponto de partida da reforma do plugin em runtime)

Status confirmado após pesquisa do código-fonte do ArcReel (fatos sobre os quais o design de plugin em runtime deve se basear):

1. **Registro de backend é dicionário estático in-process**. As três mídias backend (`video_backends` / `image_backends` / `text_backends`) têm cada uma um `registry.py`, padrão idêntico:

   ```python
   _BACKEND_FACTORIES: dict[str, Callable[..., VideoBackend]] = {}

   def register_backend(name: str, factory: Callable[..., VideoBackend]) -> None:
       _BACKEND_FACTORIES[name] = factory

   def create_backend(name: str, **kwargs) -> VideoBackend:
       if name not in _BACKEND_FACTORIES:
           raise ValueError(f"Unknown video backend: {name}")
       return _BACKEND_FACTORIES[name](**kwargs)
   ```

2. **Momento do registro é o import do módulo**. `lib/video_backends/__init__.py` no load faz `register_backend(PROVIDER_GROK, GrokVideoBackend)` etc. explicitamente, registrando todos os backends embutidos no dicionário. `register_backend()` já é API pública; **chamar de novo em runtime é totalmente legal** — este é o ponto de entrada natural do plugin em runtime.

3. **Afiliação de protocolo em `ENDPOINT_REGISTRY` (dicionário estático)**. O campo `CustomProviderModel.endpoint` só aceita keys já registradas no `ENDPOINT_REGISTRY`. Este é o maior obstáculo atual à extensão em runtime: **mesmo que o usuário registre um backend novo em runtime, não consegue registrar uma endpoint key nova para o modelo se prender**.

4. **Parâmetros de construção do backend vêm da config do DB**. Factories como `create_text_backend_for_task()` leem `api_key` etc. de `ConfigResolver.provider_config()` e passam explicitamente ao construtor do backend; não dependem mais de fallback de env (`2026-05-12-agent-sandbox-design` limpou todos os fallbacks de env). Backend de plugin em runtime deve aceitar injeção de config explícita da mesma forma e não ler variáveis de ambiente.

**Conclusão**: o design `register_backend()` + Protocol duck typing do ArcReel **é naturalmente adequado a extensão em runtime**; o ponto central de reforma é transformar `ENDPOINT_REGISTRY` de dicionário estático em estrutura de duas camadas «embutido + injeção dinâmica de plugin», e completar descoberta, carga, segurança e gestão de ciclo de vida do plugin.

### 7.5.2 Benchmark de mecanismos de plugin em runtime na indústria

| Abordagem | Mecanismo de descoberta | Forma de registro | Adequado ao ArcReel | Inadequado |
|---|---|---|---|---|
| **Python entry_points** (PEP 621) | `importlib.metadata.entry_points(group=...)` | Após `pip install arcreel-plugin-xxx` fica visível automaticamente | Padrão, zero dep de terceiros, encaixa na visão "compartilhar pacote pip na comunidade" | Tem que empacotar wheel; arquivo solto local não funciona; em Docker o usuário precisa rebuild ou mount para adicionar pacote |
| **Scan de diretório + importlib** | Escaneia `*_backend.py` em dir especificado; `importlib.util.spec_from_file_location` carrega dinamicamente | Arquivo no disco já vale; com `__subclasses__()` captura automática | Self-host monta volume e carrega, sem rebuild; dev local amigável | Precisa tratar recarga, conflito de nome e isolamento de erro sozinho |
| **pluggy** (sistema de plugins do pytest) | Spec de hook + setuptools entry_points | Multicast de hooks (1:N) | Maduro e estável | ArcReel é roteamento 1:1 (um model → um backend); não precisa de multicast de hooks; pluggy falta gestão de ciclo de vida (cache de token/pool de conexão); over-engineering |
| **LiteLLM `custom_provider_map`** | Declara `{provider, custom_handler}` no config | Caminho de módulo + variável de instância | Encaixa direto no cenário "usuário registra provider custom" | Endpoint de vídeo do LiteLLM hoje não suporta CustomLLM (nem embedding, ainda em issue); não dá para reutilizar o caminho de vídeo |

**Consenso da indústria**: dual track entry_points (plugin publicado) + scan de diretório (dev local/self-host) é a combinação mainstream de descoberta de plugins em aplicações Python contemporâneas. A forma de deploy Docker do ArcReel faz **scan de diretório + volume mount** mais amigável ao self-host; entry_points serve melhor a "publicar no PyPI para install one-click da comunidade" de plugins maduros.

**Trajetória de evolução do LiteLLM (valor de referência direto)**: LiteLLM no início só suportava atribuição em runtime manual `litellm.custom_provider_map = [{"provider": ..., "custom_handler": ...}]`; a comunidade no issue #7733 pediu entry_points para registro automático de pacotes de terceiros (na época só com hack `.pth`); depois o PR #15881 implementou declaração de subclasses CustomLLM via `[project.entry-points.litellm]` no `pyproject.toml`, descoberta e registro automáticos por `importlib.metadata`. Esse caminho "registro manual → descoberta automática entry_points" coincide fortemente com o status do ArcReel (chamada manual de `register_backend()`) e serve de blueprint direto de implementação em fases.

**Um defeito conhecido do LiteLLM a evitar**: o issue #23352 relata que, quando o nome do model registrado pelo plugin (após strip de prefixo) colide com um model conhecido de um provider embutido, a request é **roteada em silêncio para o provider embutido e não para o plugin handler**, sem erro. Lição para o ArcReel: prioridade de despacho e isolamento de namespace do endpoint do plugin devem ficar claros no design; **plugin registrado explicitamente deve ter prioridade sobre a heurística de inferência**, evitando sequestro silencioso por nome igual.

### 7.5.3 Problemas de design que o Plugin em runtime precisa resolver (para decisão do PRD)

Lista de perguntas que o plugin em runtime deve responder, derivadas da arquitetura atual, como input do PRD:

**A. Descoberta e carga**
- Fontes de plugin: pacote PyPI (entry_points) / diretório local (volume mount) / ambos?
- Momento de carga: carga única no startup do processo, ou hot-load (adicionar plugin em runtime sem restart)?
- Isolamento de falha de carga: exceção de um plugin não pode derrubar o registry de backends inteiro; precisa de try-except + log de degradação (filosofia atual: key faltando em `register_backend` não impede o startup).

**B. Extensibilidade do ENDPOINT_REGISTRY (reforma central)**
- Plugin pode registrar endpoint key nova? Se sim, `ENDPOINT_REGISTRY` precisa sair de dicionário estático de módulo e aceitar injeção em runtime.
- Isolamento de namespace de endpoint key nova: prefixar endpoints de plugin (ex. `plugin:kling-official`) para evitar conflito com keys embutidas?
- Como `infer_endpoint()` acomoda endpoint de plugin: plugin pode declarar a própria regra heurística (padrão de match de model_id → seu endpoint)?

**C. Contrato do plugin (restrições de interface do backend)**
- Backend de plugin deve implementar o Protocol `VideoBackend` (`name` / `model` / `capabilities` / `generate()`); o Protocol atual já está pronto.
- Plugin precisa declarar metadados: lista de models suportados, bitmap de capacidades, campos de credencial obrigatórios (`required_keys` / `secret_keys`, ver `ProviderMeta`), nome de exibição (i18n)?
- Injeção de config do plugin: como o backend do plugin recebe api_key / base_url que o usuário preencheu na UI? Reutilizar o armazenamento de credenciais de `CustomProvider` + máscara `mask_secret()`.

**D. Segurança (risco central de executar código de terceiros em runtime)**
- Plugin é código Python arbitrário, roda no processo ArcReel, com acesso completo a filesystem/rede.
- Precisa de sandbox? O ArcReel já tem agent sandbox (bubblewrap/seatbelt, ver `2026-05-12-agent-sandbox-design`), mas isso isola o subprocesso Bash do Agent SDK; **backend plugin roda no processo principal**, não reutiliza o mesmo sandbox direto.
- **Sandbox Python in-process é inviável (conclusão clara da pesquisa)**: RestrictedPython oficialmente diz "is not a sandbox system or a secured environment"; consenso da indústria é que sandbox in-process CPython quase não chega a segurança real por causa da dinâmica de Python (`__import__` abusado, escape por introspection, ataques de deserialização) — o autor do pysandbox já declarou essa via morta. Isolamento de verdade só por borda de processo/container (seccomp, namespace, micro-VM tipo Firecracker, compile WASM), mas isso conflita com a forma "plugin como backend chamado no processo principal". **Portanto a segurança de plugin do ArcReel não deve apostar em sandbox no nível de código, e sim na rota "confiança na origem".**
- Direções de mitigação (rota confiança na origem): auditoria de origem do plugin (só confiar em pacotes PyPI assinados / só confiar em repositórios GitHub na whitelist), confirmação humana na install, score da comunidade, lista oficial de plugins auditados, scan estático de código antes da install (deps/detecção de chamadas perigosas) — trade-offs concretos para o PRD.
- Risco de vazamento de credencial: plugin malicioso pode ler api_key de outros providers. Avaliar se o plugin só acessa as credenciais montadas nele.

**E. Gestão de ciclo de vida**
- Pool de conexão / cache de token: JWT Kling expira em 30 min, reuso de pool etc. são recursos com estado; como gerir o ciclo de vida da instância do plugin (singleton vs nova por request)? Backends atuais reutilizam por estratégia de cache `(provider_name, model)`; plugin deve seguir o mesmo.
- Unload / update: quando o usuário desabilita ou atualiza o plugin, como limpar backend e endpoint já registrados?

**F. Distribuição e comunitarização**
- Forma de compartilhamento comunitário: repositório GitHub / pacote PyPI / marketplace oficial de plugin ArcReel?
- Compatibilidade de versão: plugin declara faixa de versões ArcReel compatíveis (estratégia quando a interface do Protocol muda).
- Docs e scaffold: oferecer ferramenta tipo `arcreel backend scaffold` + template de prompt de IA para o usuário gerar esqueleto de plugin conforme o Protocol com Cursor/Claude Code (7.1 já argumentou que geração assistida por IA é a vantagem-chave do plugin frente ao declarativo).

### 7.5.4 Avaliação de encaixe com a arquitetura existente

| Ponto de reforma | Base atual | Esforço |
|---|---|---|
| Registro de backend em runtime | `register_backend()` já é API pública; Protocol duck typing pronto | Pequeno (só chamar o loader de plugin) |
| ENDPOINT_REGISTRY extensível | Hoje dicionário estático | **Médio** (virar estrutura de duas camadas + isolamento de namespace) |
| `infer_endpoint()` acomodar plugin | Heurística atual hardcoded | Médio (abrir interface para plugin declarar regras heurísticas) |
| Armazenamento/máscara de credenciais | `CustomProvider` + `mask_secret()` prontos | Pequeno (plugin reutiliza) |
| Nome de exibição i18n de endpoint | Mecanismo `endpoint_xxx_display` pt/en pronto | Pequeno (plugin fornece o próprio display name; talvez fallback para inglês) |
| Modelo de segurança | Agent sandbox não cobre backend do processo principal; sandbox Python in-process já provado inviável | **Grande/desconhecido** (não dá para confiar em sandbox de código; só confiança na origem + auditoria; decisão de produto/segurança) |
| Ciclo de vida/cache | Cache de instância `(provider, model)` pronto | Pequeno (plugin segue o mesmo) |

**Avaliação geral**: o design `register_backend()` + Protocol faz a **implementação funcional** do plugin em runtime ter alto encaixe e esforço controlável; a dificuldade real se concentra em dois pontos — **dinamização do ENDPOINT_REGISTRY** (problema de engenharia, médio) e **modelo de segurança de executar código de terceiros no processo principal** (decisão de produto + segurança, precisa de argumentação forte no PRD). Como sandbox no nível de código foi provado inviável pela pesquisa, o centro do design de segurança deve ser "confiança na origem + auditoria + governança comunitária", não "isolamento técnico".

### 7.5.5 Ideias de rollout progressivo de referência (para o PRD escolher; não conclusivas)

Vários caminhos progressivos encontrados na pesquisa, do menor ao maior esforço de reforma:

1. **Mínimo utilizável (só self-host)**: scan de diretório + volume mount; só suporta self-host em ambiente confiável carregando plugin escrito pelo próprio usuário; não resolve segurança (confia no próprio usuário). Esforço mínimo; valida o mecanismo rápido.
2. **Compartilhamento comunitário (PyPI + auditoria)**: entry_points + publicação de pacote PyPI, com "lista de plugins auditados" mantida oficialmente; contribuições da comunidade só entram na lista recomendada após auditoria. Equilibra abertura e segurança.
3. **Marketplace oficial de plugin**: ArcReel mantém registry de plugins + declaração de compatibilidade de versão + score da comunidade; usuário instala one-click na UI. Melhor experiência, mas exige infraestrutura de marketplace e investimento contínuo de operação.

Os três caminhos não são mutuamente exclusivos; podem ser as três fases de evolução da função.

---

## 8. Resumo de riscos-chave e armadilhas

### 8.1 Deprecation OpenAI Sora 2

- Aviso oficial 2026-03-24: **Sora 2 / Sora 2 Pro e a Videos API serão desligados em 2026-09-24**
- Model ids afetados: `sora-2`, `sora-2-pro`, `sora-2-2025-10-06`, `sora-2-2025-12-08`, `sora-2-pro-2025-10-06`
- ArcReel precisa concluir avaliação de migração para sora-3 ou modelo substituto antes de 2026-Q3
- O padrão de fato do caminho `/v1/videos` permanece; relay stations o usam por inércia

### 8.2 Completude do passthrough metadata NewAPI incontrolável

- O mesmo `camera_control` do Kling funciona na DMXAPI e pode se perder em alguns NewAPI self-hosted
- O backend ArcReel `newapi-video` precisa anotar no config de channel ou na doc o conjunto de campos de passthrough medidos na prática
- Capacidades avançadas (motion brush / camera control) devem ser marcadas na UI como "pode não estar disponível em algumas relay stations"

### 8.3 Armadilha unificada de expiração da URL do vídeo

- Todas as plataformas usam URL temporária; a mais perigosa, MiniMax, só **9 horas**
- ArcReel deve **iniciar rehospedagem em até 10 s após SUCCEEDED** para disco local ou object storage
- Não depender de vendor URL como link de exibição no frontend

### 8.4 Diferenças de string de status

- Kling `succeed` (não `succeeded`)
- MiniMax `Success` (primeira letra maiúscula)
- DashScope tudo maiúsculo `SUCCEEDED`
- PiAPI inner `output.status: 99` (inteiro)
- Cada backend deve manter a própria tabela de mapeamento de status; não reutilizar

### 8.5 Fragmentação de nomenclatura de model id

Na escola C `/v2/video/generations` o mesmo modelo tem nomes totalmente diferentes em cada relay:
- AIMLAPI: `kling-video/v1/standard/text-to-video`
- APIMart: `sora-2-vip`
- getimg.ai: `happyhorse-1` (marca própria)
- xAI oficial: `grok-imagine-video`

ArcReel precisa manter mapeamento de alias de model name na camada de config de channel, ou aceitar correção manual do usuário na heurística de `infer_endpoint()`.

### 8.6 Limite de discovery da v2 escola C

A lista `/v1/models` não distingue de forma confiável o endpoint alvo `/v1/video/generations` vs `/v2/video/generations`, porque os model ids têm nomenclatura idêntica.

**A heurística automática só pode dar um default** (sugestão: `newapi-video` é mais comum); o usuário na UI troca na mão conforme a doc real da relay. Esta é uma limitação inerente do ecossistema de relay derivado de NewAPI / OneAPI, não um defeito de design do ArcReel.

### 8.7 Model IDs Seedance 2.0 doméstico/overseas não são intercambiáveis

- Doméstico: `doubao-seedance-2-0-260128`
- Overseas: `dreamina-seedance-2-0-260128`
- Chamada cross-região vira 404 de certeza
- O design dual provider ark / ark-agent-plan já existente no ArcReel serve de referência

### 8.8 Códigos de erro de moderação de conteúdo

Códigos de rejeição de moderação totalmente diferentes entre plataformas:
- OpenAI Sora: `error.code: "moderation_blocked"`
- Alibaba DashScope: `IPInfringementSuspect` / `DataInspectionFailed`
- Kling: HTTP 500 + `error: "...violate the community guidelines (CM_EXT.POther)"` (**usar o campo error, não message**)

Não tratar como erro retriável; precisa de identificação especial na camada do backend.

---

## 9. Problemas que o PRD / documento de design posteriores precisam resolver

Este relatório é material de entrada; a fase de PRD precisa esclarecer os problemas abaixo. Agrupados em três blocos: "camada de arquitetura → camada de implementação de protocolo → camada de plugin em runtime".

### 9.1 Avaliação de alinhamento de arquitetura (antes da decisão de integração de protocolo concreto)

> Este grupo é **decisão de camada mais alta que a integração de um único protocolo**: antes de adicionar protocolos em escala, avaliar se a arquitetura atual `lib/video_backends/` + `lib/custom_provider/` precisa de ajuste para alinhar a implementações maduras da indústria. **Premissa importante: não se deixar levar pela nomenclatura.**

**Sobre nomenclatura (esclarecer primeiro, evitar engano)**:
- O Protocol `VideoBackend` atual do ArcReel + implementações `XxxVideoBackend` **já são na essência o paradigma Ports & Adapters (arquitetura hexagonal) preferido na indústria** — Protocol = Port, cada backend = Adapter. O esqueleto de arquitetura já alinha às boas práticas.
- O glossário (CONTEXT.md) escolhe o nome `backend` em vez de `adapter` porque: backend combina com a semântica "derivada" de provider (um provider deriva vários backends), espelha frontend, e mantém nomenclatura consistente das três mídias video/image/text. **Projetos maduros como SQLAlchemy / Django também usam backend e não adapter para o papel análogo**; a nomenclatura em si não constitui "desalinhamento com a indústria".
- **Tendência de conclusão**: não se recomenda refactor com o objetivo de "alinhar a nomenclatura adapter"; nomenclatura é superfície; o que de fato avaliar são as lacunas de capacidade abaixo.

**Lacunas de arquitetura que o PRD realmente precisa avaliar (independentes da nomenclatura)**:

1. **Se a abstração unificada de tarefa assíncrona precisa ser elevada a cidadão de primeira classe**. Esta pesquisa confirma: 9 plataformas oficiais + 4 grandes escolas de relay **todas são modelo de tarefa assíncrona** (submit → poll → mapeamento de status → rehospedagem de URL), e string de máquina de estados, janela de expiração de URL, URL em dois passos etc. diferem entre si.
   - **Ponto de julgamento de sinal real**: os backends atuais estão reimplementando loop de poll / mapeamento de status / rehospedagem de URL? Se a duplicação for alta, extrair abstração de classe `AsyncVideoTask` acima de `VideoBackend` (referência: modelo de fila fal.ai). Se já houver infraestrutura compartilhada de poll, não mexer.
   - Este é o ponto substantivo a alinhar com a indústria; nomenclatura não entra.

2. **Revisão de acoplamento ao adicionar protocolo**. Estado ideal: adicionar um protocolo novo (ex. Kling) só exige uma classe backend nova + uma linha de registro no `ENDPOINT_REGISTRY`.
   - **Ponto de julgamento de sinal real**: se adicionar protocolo exige mudar ao mesmo tempo `resolver` / `cost_calculator` / `media_generator` / vários enums, o acoplamento está apertado demais e precisa desacoplar — mas o desenho de desacoplamento é independente da nomenclatura.

3. **Extensibilidade do dicionário estático ENDPOINT_REGISTRY**. Este é o bloqueio duro do plugin em runtime (detalhes em 7.5.1) e a principal lacuna em relação a mecanismos de registro extensíveis da indústria (entry_points / pluggy). Ponto claro a alinhar (detalhes em 9.3).

**Princípio condutor**: deixar a dor real (adicionar protocolo mexe em muitos arquivos, código de poll assíncrono duplicado, plugin preso no dicionário estático) dirigir o refactor, não a observação "a indústria chama de adapter". Se não houver as dores substantivas acima, a arquitetura atual se mantém; só extensão incremental.

### 9.2 Camada de implementação de protocolo (problemas concretos de integração P0)

1. **Ordem concreta de integração dos protocolos P0** (sugestão: primeiro v2-video-generations escola C → Kling oficial → DashScope → MiniMax)
2. **Nomenclatura de key de cada endpoint novo no `ENDPOINT_REGISTRY`** (ex. `v2-video-generations` / `kling-official` / `dashscope-async` / `minimax-video`)
3. **Regras de extensão da heurística `infer_endpoint()`** (como distinguir endpoint novo dos existentes)
4. **Design de middleware de rehospedagem de URL de vídeo** (contra MiniMax 9h, Sora 1h e outras URLs curtas)
5. **Como encapsular o fluxo File API MiniMax em dois passos dentro do backend** (expor video_url unificado para fora)
6. **Estratégia de cache de token JWT Kling** (asyncio.Lock + dict TTL)
7. **Config de região DashScope** (relação de binding base_url e api_key)
8. **Design de metadata profile do backend NewAPI** (manter tabela de mapeamento de campos por vendor)
9. **Abstração unificada de máquina de estados de tarefa assíncrona** (introduzir na camada VideoBackend ou cada um implementa; decisão em conjunto com o ponto 1 de 9.1)
10. **Resposta ao deprecation Sora 2** (janela de avaliação de migração e estratégia de fallback)

### 9.3 Camada de Plugin em runtime

1. **Esquema de dinamização do ENDPOINT_REGISTRY do plugin em runtime** (dicionário estático → estrutura de duas camadas embutido+plugin; mesma origem do ponto 3 de 9.1)
2. **Modelo de segurança do plugin em runtime** (sandbox no nível de código já inviável; centro em confiança na origem + auditoria)
3. **Seleção de mecanismo de descoberta e carga do plugin em runtime** (entry_points / scan de diretório / ambos)
4. **Definição de contrato do plugin em runtime** (declaração de metadados, injeção de credenciais, i18n, regras heurísticas)
5. **Divisão de fases de rollout progressivo do plugin em runtime** (mínimo utilizável → compartilhamento comunitário → marketplace oficial)

---

## 10. Referências

### Documentação de API de primeira mão

- OpenAI Sora 2: https://platform.openai.com/docs/guides/video-generation
- OpenAI Deprecations: https://developers.openai.com/api/docs/deprecations
- Doc NewAPI: https://doc.newapi.pro/api/generate-video/ e https://doc.newapi.pro/api/kling-jimeng/
- Kling: https://app.klingai.com/cn/dev/document-api
- Volcengine Ark Seedance: https://www.volcengine.com/docs/82379
- Alibaba DashScope: https://help.aliyun.com/zh/model-studio/text-to-video-api-reference
- MiniMax Hailuo: https://platform.minimax.io/docs/api-reference/video-generation-t2v
- AI/ML API: https://docs.aimlapi.com/api-references/video-models
- xAI Grok: https://docs.x.ai/developers/model-capabilities/video/generation
- Kie.ai: https://docs.kie.ai/market/
- PiAPI: https://piapi.ai/docs/
- Runway: https://docs.dev.runwayml.com/
- Luma: https://docs.lumalabs.ai/docs/video-generation
- PixVerse: https://docs.platform.pixverse.ai/

### Documentos de design existentes do ArcReel (alinhamento de contexto)

- `docs/superpowers/specs/2026-03-16-video-service-layer-design.md` — Protocol VideoBackend
- `docs/superpowers/specs/2026-03-31-custom-provider-design.md` — primeira versão de fornecedor customizado
- `docs/superpowers/specs/2026-04-15-newapi-custom-provider-design.md` — integração NewAPI
- `docs/superpowers/specs/2026-04-26-custom-provider-model-endpoint-design.md` — endpoint descido para a camada do modelo
- `docs/superpowers/specs/2026-05-04-video-duration-redesign-design.md` — fonte de verdade de duration
- `CONTEXT.md` — glossário (backend e não adapter)

### Docs de relay stations (fontes de padrões de fato)

- AiHubMix: https://docs.aihubmix.com/en/api/Video-Gen
- APIMart: https://docs.apimart.ai/en/api-reference/videos/
- Inferência de IA Qiniu: https://developer.qiniu.com/aitokenapi
- useapi.net Kling: https://useapi.net/docs/api-kling-v1/
- fal.ai: https://fal.ai/models/

---

**Versão do relatório**: v1 (versão final de pesquisa)  
**Alinhamento de arquitetura**: ArcReel `lib/video_backends/` + `lib/custom_provider/` + `ENDPOINT_REGISTRY`  
**Próximo passo**: com base neste relatório, redigir PRD e documentos de design de integração dos endpoints concretos
