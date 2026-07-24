# Relatório de pesquisa de seleção e integração de TTS (narração) no ArcReel

> Data da pesquisa: 2026-06-02. Todos os preços unitários / nomes de modelo / detalhes de interface são fetch dessa data; preços de TTS mudam com frequência — antes de decisões de engenharia, revalidar a documentação live.
> Itens incertos estão sempre marcados **UNVERIFIED**; não inventar (princípio "não chutar dados de fornecedor externo").
> A decisão de integração deste ciclo correspondente a este relatório está em `docs/adr/0010-tts-audio-through-generation-queue.md` e em `CONTEXT.md` «Tipos de mídia e dublagem (TTS)».

## 0. Escopo e posicionamento da pesquisa

Selecionar TTS para o ArcReel (romance chinês → short video), **neste ciclo para narração no modo saybook (narration)**.

- **Primeiro critério de avaliação**: qualidade da narração em chinês (tom/pausas/emoção/coerência em texto longo em estilo leitura). A arquitetura não amarra idioma; cobertura de idiomas é anotada por fornecedor; a escolha final é do usuário.
- **Duas rotas de integração cobertas**: A. fornecedores de API em nuvem (rota principal); B. modelos open source self-hosted/edge (comparação de privacidade/custo).
- **Restrições de integração do ArcReel**: ① credenciais de fornecedor customizado fixas em um único campo `api_key` + `base_url` (`docs/adr/0008`); autenticação multi-campo só em preset embutido; ② compatível OpenAI `/v1/audio/speech` reutiliza a factory de cliente OpenAI existente e passa por relay; ③ preço declarativo por `kind` (`docs/adr/0009`); ④ síncrono vs assíncrono define se o backend imita `text_backends` ou `video_backends`; ⑤ se TTS puder reutilizar credenciais dos fornecedores já integrados (Gemini / Volcengine Ark / OpenAI / Grok / Vidu / Alibaba BaiLian DashScope), o custo de integração é o menor.

Método de pesquisa: duas rodadas de deep-research adversarial (109 + 9 agents) + preenchimento de lacunas especializadas (descompasso de duração / specs dos fornecedores já integrados / watermark). Conclusões com confiança e votação (ex.: 3-0 = três votos confirmam, 2-1 = maioria confirma, 0-3/1-2 = rejeitado).

## 1. Conclusão primeiro

### 1.1 Recomendações em camadas

| Faixa | Preferência | Motivo | Custo |
|---|---|---|---|
| **Menor custo de integração** | **Alibaba DashScope Qwen-TTS** | Reutiliza a credencial DashScope de um campo sk- já existente no ArcReel (zero formulário novo de config); melhor chinês na faixa de baixo atrito; Qwen-TTS HTTP síncrono combina com backend síncrono | TTS usa caminho nativo `/api/v1` (não compatível OpenAI); precisa de adaptador síncrono; preço unitário UNVERIFIED |
| **Extensível/self-service** | **Caminho de áudio compatível OpenAI de fornecedor customizado** | Um campo + verdadeiramente compatível OpenAI; usuário conecta sozinho Fish / IndexTTS self-hosted (com shim) / relay; ArcReel não precisa escrever código por fornecedor | Precisa de `EndpointSpec` de audio + `CustomAudioBackend` + modo audio em `infer_endpoint` |
| **Melhor qualidade em chinês** | **Volcengine Doubao síntese de voz com LLM** / ElevenLabs | Doubao: 325 timbres, dialetos chineses nativos, voice clone 2.0, coerência emocional; ElevenLabs: Multilingual v2/v3 com boa reputação em chinês | Doubao multi-campo (appid+access_token+resource_id) exige preset embutido; **Ark key não reutiliza** (Seed Speech é serviço independente); nenhum é compatível OpenAI |
| **Privacidade self-hosted** | **CosyVoice2** / **VoxCPM-0.5B** | Ambos Apache 2.0 comercializáveis; VoxCPM CER chinês 0,93% melhor open source | Precisa de GPU; sem encapsulamento oficial compatível OpenAI; VRAM/RTF UNVERIFIED |

### 1.2 Decisão deste ciclo (v1)

**Preset DashScope Qwen-TTS (reutiliza credencial, cobrança por caractere, adaptador síncrono nativo) + caminho de áudio compatível OpenAI de fornecedor customizado (`openai-tts` → `/v1/audio/speech` + `CustomAudioBackend`).** Fish / IndexTTS self-hosted (com shim) / relay usam o caminho customizado. Detalhes em `docs/adr/0010`.

## 2. Comparação de fornecedores de API em nuvem

### 2.1 Tabela principal de comparação

| Fornecedor | Chinês | Compatível OpenAI `/v1/audio/speech` | Síncrono/assíncrono | Auth | Dimensão de cobrança | Já no ArcReel | Confiança |
|---|---|---|---|---|---|---|---|
| **OpenAI** tts-1 / tts-1-hd / gpt-4o-mini-tts | Inglês forte, chinês fraco | ✅ sim (forma padrão da indústria) | Síncrono retorna bytes direto + streaming chunked | Um campo | Por caractere (tts-1 $15, tts-1-hd $30 /1M chars) | Texto/imagem já (TTS não) | 3-0; preço 2-1 |
| **ElevenLabs** Multilingual v2/v3, Flash/Turbo | Ótimo | ❌ privado | Síncrono (`/stream` chunked, ainda request único) | Um campo | Por caractere (Flash/Turbo $0.05, Multilingual $0.10 /1K chars) | Não | 3-0 |
| **Alibaba DashScope** Qwen-TTS / CosyVoice | Forte | ❌ TTS **não está** no caminho compatível (só chat) | Qwen-TTS HTTP síncrono; CosyVoice realtime = WebSocket | Um campo Bearer (sk-) | Por caractere / 10k caracteres (CosyVoice ~¥2/10k chars **UNVERIFIED**) | ✅ credencial reutilizável | 3-0; preço UNVERIFIED |
| **Volcengine Doubao** síntese de voz LLM (Seed-TTS) | Forte (dialetos nativos) | ❌ privado (openspeech.bytedance.com) | HTTP síncrono + streaming WSS + **texto longo assíncrono** (submit→query ≤100k chars, áudio guardado 7 dias) | **Multi-campo** (appid+access_token+resource_id) | Por caractere / pacote de chars + timbre anual | ❌ Ark key não reutiliza | 3-0 |
| **MiniMax** T2A async | Forte | ❌ privado (`t2a_async_v2`) | **Assíncrono** (criar tarefa→poll→pegar file_id, URL expira em 9h) | Um campo **rejeitado** (1-2, não assumir caminho customizado) | faixa de assinatura credit **rejeitada** (0-3) | Não | Interface 3-0 |
| **Fish Audio** (OpenAudio S1) | Bom | ✅ sim (nativo `/v1/audio/speech`) | Streaming síncrono (TTFB<150ms) | Um campo Bearer | Por **bytes UTF-8** ($15/1M bytes) | Não (melhor candidato ao caminho customizado) | Rodada de lacuna |
| **Gemini** TTS de áudio nativo | Bom (cmn) | ❌ `generateContent` base64 inline, **sem streaming** | Síncrono | Um campo (x-goog-api-key) | Por **token** | ✅ credencial reutilizável | Rodada de lacuna |
| **Google Cloud TTS** (Chirp3/Neural2/WaveNet) | Bom (cmn-CN) | ❌ REST `synthesize` | Síncrono; áudio longo assíncrono LRO | **Multi-campo** (service-account GCP) | Por caractere ($4–$160/1M) | Família de credencial como Vertex (precisa habilitar API) | Rodada de lacuna |
| **Azure AI Speech** | Bom (zh-CN+dialetos) | ❌ | Realtime síncrono + batch assíncrono | **Multi-campo** (subscription key + region) | Por caractere ($16/1M std) | Não | Rodada de lacuna |
| **Tencent Cloud TTS** | Forte | ❌ API assinada | Síncrono + streaming | **Multi-campo** (AppID+SecretId+SecretKey assinatura) | Por caractere em faixas | Não | Rodada de lacuna |
| **iFlytek TTS** | Top | ❌ WSS | Streaming WebSocket | **Multi-campo** (APPID+APIKey+APISecret HMAC) | Por caractere / pacote | Não | Rodada de lacuna |

### 2.2 Fronteiras-chave

- **OpenAI faturamento dividido**: a página principal de preços migrou para realtime por token; os modelos TTS dedicados por caractere (tts-1 $15, tts-1-hd $30 /1M chars) **não estão na tabela principal** — ver `developers.openai.com/api/docs/models/tts-1`. A conclusão "preços já migraram para token" foi julgada um pouco exagerada pelo verificador (2-1).
- **Credencial DashScope reutilizável, mas TTS não no caminho compatível**: Bearer de um campo reutiliza, mas a interface compatível OpenAI só expõe chat completions; TTS usa o nativo `/api/v1/services/aigc/multimodal-generation/generation` — não reutiliza factory de cliente OpenAI/relay; precisa de adaptador nativo.
- **"Armadilha de credencial" Doubao**: voz Doubao (Seed-TTS) é serviço independente do Ark, multi-campo; **a Ark key existente no ArcReel não reutiliza**; exige preset embutido + formulário multi-campo novo.
- **Duas claims MiniMax rejeitadas**: auth de um campo (1-2) e faixa de assinatura credit (0-3) não passaram na verificação — **não se pode afirmar que MiniMax pode ir pelo caminho de fornecedor customizado**.
- **pricing kind declarativo**: divisão entre fornecedores em **por caractere** (OpenAI/ElevenLabs/DashScope/GCloud/Azure/Tencent/iFlytek), **por token** (Gemini), **por bytes UTF-8** (Fish). O preço declarativo de `docs/adr/0009` neste ciclo precisa ao menos do kind `per_character`.

## 3. TTS open source self-hosted/edge (faixa privacidade, incluindo armadilhas de licença)

| Modelo | Qualidade chinês | Licença / comercial | Notas | Confiança |
|---|---|---|---|---|
| **CosyVoice2-0.5B** | Forte (CER 1,38%) | ✅ Apache 2.0, código+pesos comercializáveis, sem royalties | FunAudioLLM; voice clone | 3-0 |
| **VoxCPM-0.5B** | **Melhor open source (CER 0,93%)** | ✅ Apache 2.0 comercializável | tokenizer-free, 1,8M horas zh-en; supera IndexTTS2/CosyVoice2 | 3-0 (auto-relato de autores em preprint arXiv, sem peer review) |
| **IndexTTS2** | Forte (CER 1,03%, 2º open source) | ⚠️ pesos comerciais exigem autorização bilibili (v1 autorização escrita; **v2 threshold**: >100M MAU ou >1B RMB receita anual exige licença separada; PME comercial provavelmente isenta) | bilibili; controle emocional forte; paper tem **controle de duração** mas GitHub marca "ainda não habilitado nesta versão"; **sem API server oficial / sem endpoint compatível OpenAI**, ArcReel precisa de shim próprio; VRAM/RTF UNVERIFIED | Licença 2-1 |
| **F5-TTS** | Bom | ⚠️ pesos base **CC-BY-NC proíbe comercial** (dataset Emilia; finetune ainda proíbe; código MIT); treinar do zero com dados comerciais próprios | Armadilha comercial | 3-0 |

**Conclusão**: na faixa privacidade self-hosted, preferir **CosyVoice2 / VoxCPM** (ambos Apache 2.0 limpos e comercializáveis). IndexTTS / F5-TTS têm armadilhas de licença comercial — conferir versão a versão antes de adotar. Forma limpa de conectar qualquer modelo self-hosted ao ArcReel = na frente do self-host colocar serviço compatível OpenAI `/v1/audio/speech` e entrar pelo caminho audio de fornecedor customizado.

## 4. Riscos-chave e pontos desconhecidos

### 4.1 Descompasso de duração (mais crítico; adiado neste ciclo, mas com solução registrada)

A duração real da voz TTS ≠ `NarrationSegment.duration_seconds` do script de narração (essa duração pré-definida também dirige o comprimento do clipe de vídeo e o timeline de legendas). **Solução padrão da indústria: inverter o contrato — áudio dirige o timeline; `duration_seconds` rebaixa a dica de geração.**

- O ArcReel já tem `server/services/jianying_draft_service.py` que **já layouta pela duração real do material** (vídeo e legenda `trange` usam `actual_duration_us = material.duration`); "o material real mais longo vence" já é o design atual.
- Áudio mais longo que o vídeo → **esticar o vídeo** (`setpts`/`tpad` freeze-frame, sem perda de qualidade), **nunca acelerar a narração**.
- Legend as **geradas a partir do áudio real**: priorizar timestamps por caractere do fornecedor (ElevenLabs `with-timestamps`, chinês disponível, zero infra extra); fallback alinhamento forçado WhisperX (chinês só modelo comunitário `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn`, precisão fraca).
- ⚠️ **Não contar com "TTS isócrono"** (parâmetro target_duration): nenhuma API comercial de nuvem em chinês expõe; só pesquisa (Amazon ICASSP'22, VideoDubber AAAI'23 deixa claro que chinês é mais difícil porque nº de tokens ≠ duração da fala). IndexTTS2 self-hosted tem controle de duração no paper, mas a versão atual não habilita.
- ⚠️ Controle de tempo por parâmetro de velocidade não é confiável: faixas variam (ElevenLabs 0.7–1.2, OpenAI 0.25–4.0, Doubao 0.8–2.0, MiniMax 0.5–2.0), e **OpenAI `gpt-4o-mini-tts` historicamente ignora speed** (oficial chama de bug de doc); só serve como microajuste ±10%. `ffmpeg atempo` limpo só em 0.5–2.0x; esticar fala além de ~10–15% já se ouve degradação.

> Decisão deste ciclo: **simplesmente anexar trilha CapCut/Jianying (cada segmento independente, sem alinhamento; usuário afina na mão)**; sem retiming automático / reordenação de legendas (adiado). A solução acima fica para quando for ativada.

### 4.2 Outros

- **Texto longo**: MiniMax texto inline limite 50K caracteres, caminho de arquivo até 1M (2-1); Doubao texto longo assíncrono ≤100k chars. Narração por segment é curta; neste ciclo não precisa de chunking.
- **Consistência de timbre**: um único timbre fixo já mantém consistência entre segmentos; voice clone (Doubao 2.0 / CosyVoice) pode travar o timbre ainda mais (neste ciclo timbres pré-definidos; clone depois).
- **Streaming vs arquivo inteiro**: ArcReel precisa de arquivo de áudio versionável no disco + trilha CapCut; **receber arquivo inteiro basta; streaming só aumenta complexidade** (backend síncrono pega bytes de uma vez).
- **Watermark / compliance**: os fornecedores escolhidos **não forçam watermark não desligável em timbres pré-definidos** (MiniMax `aigc_watermark` default false). ArcReel é open source; obrigação de identificação de IA não é deste projeto (decisão do usuário; este relatório não aprofunda).

## 5. Decisão de integração deste ciclo e superfície de implementação (resumo)

Registro completo da decisão em `docs/adr/0010` e `CONTEXT.md`. Pontos:

- **Tipo de mídia**: 4º `media_type` = `audio` (capability = `text_to_speech`), no mesmo nível de image/video/text.
- **Agendamento**: via GenerationQueue/Worker (lane audio), como image/video; **backend síncrono** (imita `text_backends`, resposta em segundos, sem submit-poll-resume). `enqueue_tts(segment_ids?)`.
- **Backend**: novo `lib/audio_backends/`; adaptador síncrono nativo DashScope + caminho audio compatível OpenAI customizado.
- **Timbre**: id string configurável (default global + override `project.json` `settings.narration_voice`; sem catálogo embutido; velocidade opcional).
- **Versionamento**: sim (resource_paths/VersionManager, dir `audio/`, arquivos `segment_{id}.mp3`).
- **Modelo de dados**: `GeneratedAssets.narration_audio: str | None` (project.json, sem tabela DB); fonte de texto = `NarrationSegment.novel_text` como está.
- **Cobrança**: pricing kind `per_character` (preset DashScope); fornecedor customizado usa preço unitário preenchido pelo usuário no DB.

## 6. O que deve ser verificado antes de implementar (lista UNVERIFIED)

Dados de fornecedor externo: **não chutar, não hardcodar**; antes de codar, consultar documentação de primeira mão item a item:

1. **ID exato do modelo** DashScope TTS (qwen-tts / qwen3-tts-flash / cosyvoice-v2?) e qual é **HTTP puro síncrono** (CosyVoice realtime é WebSocket, não combina com backend síncrono → tendência Qwen-TTS).
2. DashScope TTS **endpoint REST síncrono + schema request/response**, **preço unitário por caractere + moeda**, **ids de timbre disponíveis**, formato de saída/sample rate.
3. Schema de request do `/v1/audio/speech` compatível OpenAI (model/voice/input/response_format/speed), para `EndpointSpec` audio customizado.
4. Se `price_unit` de fornecedor customizado suporta unidade por caractere (audio).
5. Se Fish Audio força watermark em nuvem no OpenAudio S1 (UNVERIFIED).
6. VRAM/RTF de modelos self-hosted / se há encapsulamento oficial compatível OpenAI (CosyVoice2 / VoxCPM / IndexTTS2).

## 7. Referências (fontes oficiais de primeira mão, fetch 2026-06-02)

- Guia OpenAI TTS: https://developers.openai.com/api/docs/guides/text-to-speech
- Modelo/preço OpenAI tts-1: https://developers.openai.com/api/docs/models/tts-1
- Preços ElevenLabs: https://elevenlabs.io/pricing/api ; streaming: https://elevenlabs.io/docs/api-reference/text-to-speech/stream ; timestamps por caractere: https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps
- Volcengine Doubao síntese de voz LLM: https://www.volcengine.com/docs/6561/1257543 ; texto longo assíncrono: https://www.volcengine.com/docs/6561/1829010 ; voice clone 2.0: https://www.volcengine.com/docs/6561/1305191
- Alibaba DashScope compatível OpenAI: https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope ; Qwen-TTS: https://www.alibabacloud.com/help/en/model-studio/qwen-tts ; preços: https://help.aliyun.com/zh/model-studio/model-pricing
- MiniMax T2A async: https://platform.minimax.io/docs/guides/speech-t2a-async
- Fish Audio preços/rate limit: https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits
- Geração de fala Gemini: https://ai.google.dev/gemini-api/docs/speech-generation
- Preços Google Cloud TTS: https://cloud.google.com/text-to-speech/pricing
- Preços Azure Speech: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/
- Tencent Cloud TTS: https://cloud.tencent.com/document/product/1073/37995 ; iFlytek TTS: https://www.xfyun.cn/doc/tts/online_tts/API.html
- CosyVoice LICENSE: https://github.com/FunAudioLLM/CosyVoice/blob/main/LICENSE
- Paper VoxCPM: https://arxiv.org/html/2509.24650v1 ; pesos: https://huggingface.co/openbmb/VoxCPM-0.5B
- IndexTTS: https://github.com/index-tts/index-tts ; licença: https://huggingface.co/spaces/IndexTeam/IndexTTS-2-Demo/blob/main/INDEX_MODEL_LICENSE_EN.txt ; discussão de licença: https://github.com/index-tts/index-tts/issues/228
- Restrições comerciais F5-TTS: https://github.com/SWivid/F5-TTS/discussions/997
- Alinhamento de duração: WhisperX https://github.com/m-bain/whisperX ; modelagem de duração de dublagem automática https://arxiv.org/html/2211.16934v2 ; tradução de fala para dublagem automática https://aclanthology.org/2020.iwslt-1.31/ ; ffmpeg atempo https://ayosec.github.io/ffmpeg-filters-docs/7.1/Filters/Audio/atempo.html
- Paradigma self-hosted com shim compatível OpenAI: https://github.com/matatonic/openedai-speech
