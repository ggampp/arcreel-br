---
status: accepted
---

# Compressão de imagens de referência: teto geral conservador + 413 passivo; só a cópia de upload

Em cenários I2I / I2V / R2V costuma-se enviar várias imagens de asset grandes (sheets de character/scene/prop, storyboard anterior, imagens de referência) como referência ao provider; com base64 embutido o body total facilmente ultrapassa o teto de cada um e a chamada falha. Decidimos, na garganta de `media_generator` (único ponto de confluência de toda geração), fazer compressão ativa + rebaixamento de pré-check na **cópia de upload de referência**, e manter um fallback passivo de 413; a lógica de compressão fica centralizada em `lib/reference_compression.py` e só trata cópias temporárias apagadas após o envio.

## Decisão

- **Só comprime a cópia de upload de referência**: arquivos de asset de origem e produtos gerados permanecem em qualidade total (nenhuma compressão na gravação do produto). Logo «gerar 4K e não obter 4K» não pode ocorrer neste mecanismo — a resolução da referência não decide a resolução de saída.
- **Sem teto de bytes exato por provider; um único teto geral conservador**: default request total ≤8MB / imagem única ≤4MB (abaixo de todos os tetos documentados conhecidos dos providers embutidos), em ConfigService, sobrescrevível per-provider; **captura passiva de HTTP 413 → rebaixa uma faixa e tenta de novo** para lidar com «tetos desconhecidos/possivelmente mutáveis» (relays, docs ausentes ou desatualizados).
- **JPEG unificado q92 + 4:4:4**: todos os providers aceitam JPEG, zero ramos de formato; q92/4:4:4 é a faixa «visualmente lossless», minimiza dano geracional de «nós comprimimos uma vez + o provider comprime de novo por dentro» e protege bordas de sheets com texto.
- **Baseline prioritariamente reduz resolução** (lado longo ≤2048, pass-through condicional, só processa se estourar); a escada de rebaixamento também prioriza resolução, com piso de qualidade q80. Pesquisa mostra que resolução é a primeira alavanca e de baixo risco; artefatos de alta frequência da queda de qualidade é que prejudicam o efeito de condicionamento (especialmente frame inicial de i2v, sensível).
- **Distinção por papel**: array multi-imagem de referência segue baseline completa + escada de rebaixamento; frame inicial/final único só reencoda se estourar bytes e **nunca reduz dimensões**, para proteger o frame inicial sensível e não quebrar o match exato de pixels de entrada do Sora.

## Por que não teto de bytes exato por provider

Hardcodar teto de body por provider viola o princípio «não adivinhar/não hardcodar dados de provider externo» (a maioria não publica teto total em claro e muda com frequência; cada relay é diferente e não verificável). O teto geral conservador é constante de política de segurança do lado ArcReel (análogo ao default de timeout), sem pretender ser o número real de ninguém; o 413 passivo se autocorrije. Custo: ocasionalmente «teto configurado largo demais» gera uma chamada 413 a mais — mas 413 é rejeitado no ingress, sem cobrança, só atraso, e relays que realmente servem imagem em geral já aumentaram o body limit; o disparo é raro.

## Consequences

- Os caminhos de erro de cada backend precisam deixar 413 reconhecível: `vidu`/`dashscope` hoje embrulham `httpx.HTTPStatusError` em `RuntimeError` e perdem o status code — precisam preservar o status code.
- A compressão per-task antiga de R2V (`_compress_references_to_tempfiles`) e o `except RequestPayloadTooLargeError` que nunca era raised (código morto) saem/migram juntos; a compressão unifica na garganta, evitando compressão dupla.
- O match exato de pixels de entrada do Sora é lacuna independente anterior a este requisito (frame inicial sem pad/resize para faixa legal), fora do escopo deste desenho; o desenho garante não piorar.
