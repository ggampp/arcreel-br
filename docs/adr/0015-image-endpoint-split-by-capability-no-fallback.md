---
status: accepted
---

# Endpoint de imagem se divide por capacidade em slots T2I/I2I; gating estrito em runtime, sem fallback implícito

No ecossistema de relay NewAPI/OneAPI muitos modelos só expõem generations (sem edits); enviar imagem de referência a «modelo só com generations» roteia para chamada edit, 404 remoto e atribuição de culpa confusa. Decidimos dividir o endpoint de imagem OpenAI de um único wildcard em três «wildcard / só T2I / só I2I», e a config default em dois slots independentes por capacidade (`default_image_backend_t2i` / `default_image_backend_i2i`); em runtime o caminho se escolhe estritamente por haver ou não imagem de referência; mismatch de capacidade lança `ImageCapabilityError` com code estável — **sem** fallback implícito do tipo «referência ilegível → cai em T2I». Falha cedo e erro claro valem mais do que despacho automático e erro remoto confuso.

## Consequences

- Granularidade de config mais fina: o usuário configura modelos T2I/I2I separadamente; dropdown duplo no frontend e migração de dados vêm junto.
- Ortogonal a `docs/adr/0001` (capability resolvida na execução): aquele fala «a forma do request decide t2i/i2i»; este fala «slots default de config por capacidade + sem fallback». O mesmo trio de modes + códigos de erro já é reutilizado por backends de imagem dashscope / vidu etc.
