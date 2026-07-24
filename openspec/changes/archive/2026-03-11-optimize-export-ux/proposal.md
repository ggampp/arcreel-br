## Why

A exportação de projeto atual tem dois problemas centrais de experiência:

1. **Download bloqueante**: a exportação usa fetch + Blob no frontend para baixar o ZIP; o arquivo inteiro precisa ser recebido na memória antes de disparar o save. Enquanto isso o usuário não vê progresso e não pode trocar de página (ao sair o fetch é interrompido). Em projetos com muitos storyboards/vídeos o ZIP pode chegar a centenas de MB — experiência péssima.
2. **Exportação full redundante**: cada exportação empacota todo o conteúdo do projeto (incluindo todo o histórico em `versions/`), bem além do que o usuário costuma precisar. Na maioria dos casos basta a versão atual dos recursos, sem os arquivos de versões históricas.

## What Changes

- **Download nativo do navegador**: trocar a forma de chamar a API de exportação de fetch → Blob → `<a>.click()` para abrir diretamente um link de download autenticado no navegador. O download nativo mostra progresso, permite pausar/retomar e não bloqueia a troca de página.
- **Autenticação segura da URL de download**: introduzir um mecanismo de download token de curta duração (uso único na prática), evitando expor o JWT de longa duração no query string da URL.
- **Opções de escopo de exportação**: na interação de exportação, adicionar a escolha — "Exportar tudo" e "Apenas versão atual":
  - **Exportar tudo**: igual à lógica existente, empacota o diretório inteiro do projeto (incluindo `versions/`).
  - **Apenas versão atual**: ignora arquivos históricos sob `versions/`, mantendo só os recursos em uso. No manifesto `arcreel-export.json` registra `scope: "current"` e em `versions.json` mantém só as entradas da current version como metadados (preservando prompt e outras informações de geração), para restaurar contexto na importação.

## Capabilities

### New Capabilities
- `export-download-token`: emissão e validação de download token de curta duração para autenticação segura do download nativo do navegador
- `export-scope-selection`: seleção de escopo de exportação (tudo / apenas versão atual), incluindo lógica de empacotamento no backend e UI de opções no frontend

### Modified Capabilities
(nenhum spec existente a modificar)

## Impact

- **Backend**:
  - `server/auth.py` — lógica de emissão/validação de download token
  - `server/app.py` — middleware de autenticação precisa reconhecer download token
  - `server/routers/projects.py` — endpoint de exportação com parâmetro scope + validação de download token
  - `server/services/project_archive.py` — lógica de empacotamento com filtro de scope
- **Frontend**:
  - `frontend/src/api.ts` — API de exportação passa a obter URL de download em vez de fetch Blob
  - `frontend/src/components/layout/GlobalHeader.tsx` — botão de exportar com interação de seleção de escopo
- **Mudanças de API**: endpoint de exportação ganha query param `scope`; novo endpoint de download token
- **Compatibilidade**: a lógica de importação já aceita ZIP sem diretório `versions/`; pacotes com `scope: "current"` importam normalmente
