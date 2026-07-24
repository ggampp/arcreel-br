# Problemas conhecidos

Dívida técnica acumulada descoberta durante a integração multi-fornecedor de geração de vídeo (#98). Não afeta a correção funcional; registrado para iterações futuras.

---

## 1. Inflação de parâmetros de VideoGenerationRequest

**Local:** `lib/video_backends/base.py` — `VideoGenerationRequest`

**Situação:** o dataclass compartilhado mistura campos específicos de backend (`negative_prompt` é próprio do Veo; `service_tier`/`seed` são próprios do Seedance), com o acordo por comentário de que «cada Backend ignora campos não suportados».

**Avaliação:** só 3 backends e 3 campos específicos; a complexidade de introduzir classes de config per-backend não compensa. Refatorar quando o 4º backend entrar.

---

## 2. UsageRepository.finish_call com ida e volta dupla no DB

**Local:** `lib/db/repositories/usage_repo.py` — `finish_call()`

**Situação:** primeiro `SELECT` lê a linha inteira (para pegar `provider`, `call_type` etc. e calcular o custo), depois `UPDATE` grava o resultado. Duas idas e voltas seriais ao banco por tarefa.

**Avaliação:** a geração de vídeo é da ordem de minutos; o impacto de ida e volta ao DB é mínimo. Eliminar exigiria alterar 3 callers (MediaGenerator, TextGenerator, UsageTracker) — risco assimétrico.

---

## 3. Inflação de parâmetros de UsageRepository.finish_call()

**Local:** `lib/db/repositories/usage_repo.py` — `finish_call()`, `lib/usage_tracker.py` — `finish_call()`

**Situação:** `finish_call()` já tem 9 parâmetros keyword, e `UsageTracker.finish_call()` repassa 1:1 em espelho.

**Avaliação:** acoplado ao Issue 2; mudar sozinho tem baixo retorno. Refatorar junto com o Issue 2.

---

## 4. Tarefas de geração de roteiro têm restrição forte ao teto de tokens de saída do modelo

**Local:** `lib/script_generator.py`, `lib/text_backends/`

**Situação:** roteiros JSON grandes (22+ cenas) precisam de cerca de 14K–16K tokens de saída. `TextGenerationRequest.max_output_tokens` já é suportado e passado explicitamente em `SCRIPT_MAX_OUTPUT_TOKENS = 32000`, mas o **teto duro** de cada modelo ainda pode truncar:

- `doubao-seed-1-8-251228`: teto duro de saída ~8192, insuficiente para geração de roteiro
- `gemini-3-flash-preview` / `gemini-2.5-pro`: teto default suficiente (≥32K)
- série `gpt-5.4`: teto default suficiente
- série `doubao-seed-2.x`: teto de saída mais alto (varia por modelo)

**Sugestão:** em `/app/settings`, configure para tarefas SCRIPT um **modelo com teto de saída ≥16K**. Se for obrigatório usar doubao-seed-1-8-251228, mantenha o número de cenas em ≤15 para evitar truncamento.

**Melhoria futura (não feita):** declarar em `PROVIDER_REGISTRY` de `lib/config/registry.py` um campo de capacidade `max_output_tokens` por modelo; em runtime fazer clamp `min(request, model_limit)` com `logger.warning`, e avisar na UI ao escolher o modelo.
