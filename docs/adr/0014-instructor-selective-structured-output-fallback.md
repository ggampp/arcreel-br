---
status: accepted
---

# Saída estruturada: degradação seletiva, não entrada unificada; meios de degradação se diferenciam pela disponibilidade do canal wire

Modelos com suporte nativo a `structured_output` usam parâmetros estruturados no nível wire nativo (`response_format` / `response_json_schema`) — mais rápidos e precisos. A degradação só dispara em dois casos: **gate de capacidade a priori** — modelos sem declaração de suporte no registry (incluindo não registrados; degrada com conservadorismo: melhor degradar do que chamar API nativa que quebra); **revalidação a posteriori em runtime** — após HTTP 200 da chamada nativa, verifica se a resposta realmente satisfaz o schema; relays/proxies de terceiros podem ignorar em silêncio parâmetros wire e devolver prosa ou JSON fora do schema (a revalidação usa `strict=False` tolerando valores coercíveis, para não degradar por engano respostas legais já aceitas pelo provider e cobrar de novo; quando degrada, os tokens da chamada nativa entram no resultado da degradação, sem deixar de registrar). Decidimos não forçar todos os backends a um único caminho de degradação — embrulhar de novo o caminho nativo só o torna mais lento e menos preciso; alternativas como PydanticAI / BAML são pesadas demais ou o DSL é incompatível.

Os meios de degradação se diferenciam por backend; o critério é **se a degradação precisa contornar o canal wire**: openai / ark usam Instructor (`lib/text_backends/instructor_support.py` funções puras: injeção de schema no prompt + parse + retry de validação, transparente à camada superior); gemini usa injeção de prompt dentro do backend (schema escrito no prompt, reenvio como chamada de texto puro, validação após remover cercas markdown, retry com feedback de erro se falhar) — o cenário de disparo da degradação é exatamente o relay ignorando em silêncio parâmetros wire, e a integração genai do Instructor (modos JSON/TOOLS) também cai em response_schema / function calling, parâmetros wire que o mesmo relay ignoraria; escrever a restrição de schema no prompt é o único meio que não depende de parâmetros wire.

A estrutura combinada de retry e degradação (decorator de retry só embrulha uma chamada de rede; a degradação traz o próprio retry) está em `docs/adr/0047`.

## Consequences

- Mais uma dependência de terceiros, e o julgamento de capacidade consulta o registry (gate por capabilities do modelo, em par com `docs/adr/0013` «declaração de capacidade no nível do modelo»).
- Modelos sem saída estruturada nativa, e cenários em que o relay ignora parâmetros nativos em silêncio, ainda produzem resultado estruturado, sem quebrar o caminho nativo.
- Degradação não é mais sinônimo exclusivo de Instructor: a lógica de validação/retry da degradação gemini fica no próprio backend (`_prompt_json_fallback`), fora de `instructor_support`.
