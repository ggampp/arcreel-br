---
status: proposed
---

# Reparo de importação fica no archive, não na entrada unificada de save; constantes de forma vazadas convergem para a fonte de verdade existente

O caminho de importação de `project_archive` faz muito «reparo de emergência» em arquivos enviados pelo usuário, possivelmente incompletos/bagunçados: rebobinar arquivos de versão antigos em `versions/`, adivinhar caminhos de layouts arbitrários de volta para o lugar certo, indexar por nome de arquivo e casar, bloquear se faltar definição de asset. Uma varredura de arquitetura sugeriu adicionar `ProjectManager.restore_from_staging()` para monopolizar esses reparos, de modo que «caminho de importação = caminho de save = o mesmo conjunto de garantias». **Rejeitamos** a sugestão: essa lógica de emergência é I/O próprio da importação, não conhecimento de domínio do ProjectManager (PM só opera em diretórios de projeto já instalados e organizados); o contrato da importação (consertar com força + bloquear se faltar definição) é diferente da semântica «não piorar» da entrada unificada de save `_write_script_unlocked` (ADR-0002, que aceita roteiros legados já ruins antes da edição) — forçar união misturaria os dois contratos e ainda empurraria ~580 linhas no módulo deus PM de 94 métodos que o candidato 6 quer emagrecer.

O único vazamento real de conhecimento de domínio em `project_archive` são «constantes de forma duplicadas»:

- **Caminhos canônicos de recurso** (`resource_type` → caminho relativo no projeto, ex. `characters/{id}.png`, `videos/scene_{id}.mp4`) estavam copiados em três lugares — `MediaGenerator.OUTPUT_PATTERNS` (escrita), `versions.py::_resolve_resource_path` (rebobinar), `project_archive._canonical_resource_path` (importação). Convergem para uma única função, consumida pelos três.
- **Despacho content_mode → nomes de campos do roteiro** (narration usa `segments`/`segment_id`, drama usa `scenes`/`scene_id`) era `if/else` manual no archive reescrevendo campos já declarados em `script_models`. Converge para `script_models`; o archive chama em vez de rederivar.

O template de `generated_assets` já delega a `PM.create_generated_assets` (não é cópia); nada a fazer.

## Consequences

- **Desacoplado** do candidato 6 (dividir o módulo deus PM): esta decisão não mexe no PM e pode aterrissar a qualquer hora, sem esperar a divisão do PM. O texto da varredura que dizia «naturalmente emparelhado com o candidato 6» se inverte aqui.
- A entrada unificada de save continua o único ponto de guarda para escrita de roteiro (ADR-0002/0003); importação é **exceção deliberada** — repara o arquivo sujo antes de instalar no diretório do projeto, e esse reparo ocorre fora da entrada unificada. Registrar este ADR bloqueia futuras mudanças bem-intencionadas do tipo «também meter a importação na entrada unificada».
- A função de caminho canônico na prática cruza duas famílias: recursos de mídia (storyboards/videos/grids/reference_videos, em `MediaGenerator.OUTPUT_PATTERNS`) e sheets de personagem/cena/prop (em `asset_types.bucket_key`); além disso `characters/refs/{name}.png` (reference_image) não está em nenhum map existente. Bifurcar por dentro da função ou unificar essas fontes antes é detalhe de implementação.
