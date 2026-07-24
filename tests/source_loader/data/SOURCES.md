# Origem dos fixtures PDF

Todos vêm de [`tests/fixtures/`](https://github.com/yfedoseev/pdf_oxide/tree/main/tests/fixtures) do projeto pdf_oxide,
mesma origem da dependência de runtime, o que evita descompasso de compatibilidade de amostras se o comportamento de parse do pdf_oxide mudar no futuro.

## sample_text.pdf

- **Origem**: `tests/fixtures/1.pdf`
- **Licença**: MIT / Apache-2.0
- **Data do download**: 2026-05-11
- **Conteúdo**: 7 páginas de relatório de pesquisa de valores mobiliários em chinês, 600+ caracteres CJK por página
- **Uso**: testar extração normal de texto e separação entre páginas do `PdfOxideExtractor`

## sample_scanned.pdf

- **Origem**: `tests/fixtures/encrypted_objstm.pdf`
- **Licença**: MIT / Apache-2.0
- **Data do download**: 2026-05-11
- **Conteúdo**: 3 páginas, sem camada de texto (`extract_chars()` retorna vazio)
- **Uso**: testar o caminho de detecção de documento digitalizado
