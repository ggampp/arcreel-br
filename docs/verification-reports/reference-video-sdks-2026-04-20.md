# Relatório de verificação de SDKs de reference-to-video (2026-04-20)

## Ambiente

- Branch: `feature/reference-video-pr7-e2e-release`
- PR: PR7 (M6 E2E + release)
- Script: `scripts/verify_reference_video_sdks.py`
- Data: 2026-04-20
- Executor: validação agent-driven na tarefa E2E do PR7 (não humana)

## Visão geral da execução

Tentativa de rodar, para quatro fornecedores (Ark / Grok / Gemini Veo / OpenAI Sora):

```bash
uv run python scripts/verify_reference_video_sdks.py --provider <p> --refs N --duration D --report-dir docs/verification-reports
```

**Resultado: nenhum dos quatro conseguiu completar chamada real** — o ambiente atual não tem API Key configurada para nenhum deles. O script falha já na fase de construção do backend (`create_backend` → `resolve_*_api_key`):

| Fornecedor | Ponto de saída | Mensagem de erro (reprodução exata) |
|---|---|---|
| Ark | `lib/ark_shared.py:23` | `ValueError: Ark API Key 未提供。请在「全局设置 → 供应商」页面配置 API Key。` |
| Grok | `lib/grok_shared.py` (`resolve_xai_api_key`) | `ValueError: XAI_API_KEY 未设置\n请在系统配置页中配置 xAI API Key` |
| Gemini Veo | `lib/video_backends/gemini.py:81` | `ValueError: GEMINI_API_KEY 环境变量未设置` |
| OpenAI Sora | `openai/_client.py:587` | `openai.OpenAIError: The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable` |

Este é o degraded scenario esperado do plan PR7 Task 14 ("se qualquer key faltar, não bloquear o PR7; só validar fornecedores configurados e anotar no relatório 'não verificado — chave não configurada'"). Este relatório é o artefato desse fallback.

## Matriz de capacidades baseada em documentação (de `lib/reference_video/limits.py` + docs dos fornecedores)

`lib/reference_video/limits.py` é a **single source of truth** compartilhada pela fase de construção de prompt (`lib/script_generator.py:_resolve_max_refs()`) e pela fase de enforcement do executor (`server/services/reference_video_tasks.py:_PROVIDER_LIMITS`):

```python
PROVIDER_MAX_REFS:     {"gemini": 3, "openai": 1, "grok": 7, "ark": 9}
PROVIDER_MAX_DURATION: {"gemini": 8, "openai": 12, "grok": 15, "ark": 15}
DEFAULT_MAX_REFS = 9
```

| Fornecedor | Modelo (representativo) | Máx. refs | Máx. duração | generate_audio | Notas |
|---|---|---|---|---|---|
| Ark Seedance 2.0 | doubao-seedance-2-0-260128 | 9 | 15s | ✅ | Preferido; multi-shot `Shot N (Xs):` já documentado |
| Ark Seedance 2.0 fast | doubao-seedance-2-0-fast-pro | 9 | 15s | ✅ | Modo rápido; capacidades alinhadas ao 2.0 |
| Grok | grok-imagine-video | 7 | 15s | ✅ (default) | Tamanho do body medido pending; caminho de recompressão secundária `RequestPayloadTooLargeError` já pronto |
| Gemini Veo | veo-3.0-generate-preview | 3 | 8s | ✅ (Vertex) | executor já faz clamp duro |
| OpenAI Sora | sora | 1 | 12s | — (executor atual não envia) | **decisão do item 4 da spec §11 depende disto** — até live validation, conservador com `max_refs=1` e caminho de degradê de imagem única |

> Números concretos têm `lib/reference_video/limits.py` como single source of truth. Se esta tabela divergir do código, **corrija o código** e depois sincronize este relatório.

## Live validation pending

Quando a API key estiver disponível, rode os comandos abaixo um a um e append o resultado real a este arquivo:

```bash
# Ark Seedance 2.0
uv run python scripts/verify_reference_video_sdks.py --provider ark --refs 9 --duration 8 --multi-shot --report-dir docs/verification-reports

# Grok — registrar especialmente o tamanho do body (>8MB observar erro gRPC/HTTP)
uv run python scripts/verify_reference_video_sdks.py --provider grok --refs 7 --duration 6 --report-dir docs/verification-reports

# Gemini Veo — 3 imagens 8s
uv run python scripts/verify_reference_video_sdks.py --provider veo --refs 3 --duration 8 --report-dir docs/verification-reports

# OpenAI Sora — foco: multi-imagem é suportado?
uv run python scripts/verify_reference_video_sdks.py --provider sora --refs 3 --duration 8 --report-dir docs/verification-reports
uv run python scripts/verify_reference_video_sdks.py --provider sora --refs 1 --duration 8 --report-dir docs/verification-reports  # controle
```

Após a execução real, registrar a cada chamada:

- Status code HTTP/gRPC real e latência
- Se refs/duration foram clampados em silêncio pelo provider
- Se multi-shot foi parseado corretamente (observar se o artefato apresenta vários trechos de shot)
- Se generate_audio é perceptível no vídeo de saída
- Tamanho do body (Grok) e se `RequestPayloadTooLargeError` disparou recompressão secundária (`long_edge=1024, q=70`)
- Comportamento real do Sora em multi-imagem (rejeita de vez / descarta em silêncio / suporta de verdade) e, com isso, atualizar a decisão do item 4 da spec §11

## Conclusão (até a data do relatório)

- A camada de código já abstrai os tetos de capacidade dos quatro providers em `lib/reference_video/limits.py`; o `_apply_provider_constraints` do executor faz clamp de refs/duration com base nisso e devolve `warnings`.
- Os valores baseados em documentação estão alinhados com a tabela do apêndice B da spec.
- **A decisão de modo de referência do Sora (item 4 da spec §11) permanece "degradê conservador de imagem única"**, até live validation decidir se esconde por completo ou afrouxa para multi-imagem. O caminho de warning `ref_sora_single_ref` de `_apply_provider_constraints` é o fallback de runtime dessa decisão.
- O branch de recompressão secundária `ref_payload_too_large` (body grande demais, `long_edge=1024, q=70`) já tem cobertura de unit test; se dispara em cenário live permanece pending.
- Este relatório não bloqueia o merge do PR7; quando as credenciais estiverem prontas, deve ser o follow-up prioritário, com resultados preenchidos no final deste arquivo.
