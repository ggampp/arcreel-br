---
status: accepted
---

# Cache de mídia: mtime do arquivo como fingerprint de content-addressing (cache-bust); versões/arquivos com query param são immutable

O contador de revision no nível da session, ao atualizar a página, reentrar cross-session ou remontar virtual scroll, re-baixa com base no contador, e o `?v=0` de uma session nova pode corresponder a conteúdo já mudado. Decidimos que o frontend use mtime do arquivo (nanossegundos) como parâmetro `?v=` da URL do asset (asset fingerprint) no lugar do contador; a rota de arquivo, para requests com `?v=` ou path contendo `versions/`, define `Cache-Control: public, max-age=31536000, immutable` — «conteúdo igual → URL igual → hit no disk cache» vale em todos esses cenários.

## Consequences

- O fingerprint precisa ser entregue com a API do projeto e eventos SSE; o frontend mantém um fingerprint store.
- Uma vez emitido o header `immutable`, o cliente cacheia por longo prazo; por isso o fingerprint deve mudar com o conteúdo, e arquivos históricos imutáveis em `versions/` se aplicam naturalmente.
