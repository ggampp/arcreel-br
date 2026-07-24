# Documentação de domínio

Como as skills de engenharia devem consumir a documentação de domínio deste repositório ao explorar o código.

## Antes de explorar, leia

- **`CONTEXT.md`** na raiz do repo, ou
- **`CONTEXT-MAP.md`** na raiz do repo, se existir — aponta um `CONTEXT.md` por contexto. Leia cada um relevante ao tópico.
- **`docs/adr/`** — leia os ADRs que tocam a área em que você vai trabalhar. Em repos multi-contexto, confira também `src/<context>/docs/adr/` para decisões com escopo de contexto.

Se algum desses arquivos não existir, **siga em silêncio**. Não sinalize a ausência; não sugira criá-los de antemão. A skill produtora (`/grill-with-docs`) os cria de forma lazy quando termos ou decisões de fato se resolvem.

## Estrutura de arquivos

Repo de contexto único (a maioria):

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

Repo multi-contexto (presença de `CONTEXT-MAP.md` na raiz):

```
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← decisões de todo o sistema
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← decisões específicas do contexto
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## Use o vocabulário do glossário

Quando a sua saída nomear um conceito de domínio (título de issue, proposta de refatoração, hipótese, nome de teste), use o termo como definido em `CONTEXT.md`. Não desvie para sinônimos que o glossário evita explicitamente.

Se o conceito de que você precisa ainda não está no glossário, isso é um sinal — ou você está inventando linguagem que o projeto não usa (reconsidere), ou há uma lacuna real (anote para `/grill-with-docs`).

## Sinalize conflitos com ADR

Se a sua saída contradiz um ADR existente, deixe explícito em vez de sobrescrever em silêncio:

> _Contradiz o ADR-0007 (event-sourced orders) — mas vale reabrir porque…_
