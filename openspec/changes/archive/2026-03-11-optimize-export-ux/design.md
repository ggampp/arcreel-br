## Context

Fluxo atual de exportação: o frontend chama com `fetch` o `GET /api/v1/projects/{name}/export` (com Bearer JWT), espera o corpo completo do ZIP carregar na memória (Blob) e então cria uma tag `<a>` para o navegador salvar. O backend retorna o ZIP temporário com `FileResponse` do FastAPI.

Problema: durante o download de arquivos grandes não há indicação de progresso; se o usuário trocar de página o fetch é interrompido. Cada exportação inclui todos os arquivos de versão histórica sob `versions/`, com volume redundante.

Autenticação atual: JWT (HS256, validade 7 dias), via header `Authorization: Bearer`. Endpoints SSE usam fallback `?token=` no query. O endpoint de exportação não está na whitelist e exige autenticação.

## Goals / Non-Goals

**Goals:**
- O download de exportação é assumido pelo navegador nativamente, com progresso, pausa/retomada e troca de página sem interrupção
- Autenticação segura da URL de download: não expor JWT de longa duração; usar token de curta duração (uso único na prática)
- Suportar dois escopos de exportação: tudo (com histórico de versões) e apenas versão atual
- O pacote "apenas versão atual" pode ser importado normalmente, preservando metadados de versão necessários

**Non-Goals:**
- Não remodelar o fluxo de importação (a lógica existente já lida com ZIP sem versions/)
- Não fazer resume por chunks ou download em pedaços
- Não fazer empacotamento assíncrono em background + notificação (desnecessário no volume atual dos projetos)
- Não alterar o modo de autenticação SSE `?token=`

## Decisions

### 1. Download nativo do navegador: emitir download token + `window.open`

**Solução**: o frontend chama primeiro `POST /api/v1/projects/{name}/export/token` para obter o download token de curta duração e depois abre com `window.open` ou tag `<a>` o `GET /api/v1/projects/{name}/export?download_token=xxx&scope=full|current`; o navegador assume o download.

**Alternativas**:
- *JWT direto no query da URL*: simples, mas inseguro; JWT vale 7 dias e aparece no histórico do navegador e nos logs do servidor. **Rejeitado**.
- *Autenticação por Cookie*: exigiria remodelar todo o sistema de autenticação e CSRF; mudança grande demais. **Rejeitado**.
- *Content-Disposition + fetch streaming*: suporte a streaming no fetch é irregular entre navegadores e ainda exige o frontend manter a conexão. **Rejeitado**.

**Design do download token**:
- Endpoint de emissão: `POST /api/v1/projects/{name}/export/token` (exige autenticação Bearer JWT)
- Formato do token: JWT (HS256, mesma chave secreta atual); payload com `sub` (usuário), `project` (nome do projeto), `purpose: "download"`, `exp` (expira em 5 minutos)
- Regras de validação: o endpoint de exportação valida o query param `download_token`, checando `purpose` e `project`
- Uso único na prática: sem estado no servidor (sem Redis); curta duração + vínculo ao nome do projeto bastam para a segurança

### 2. Parâmetro de escopo de exportação: query param `scope`

**Solução**: o endpoint de exportação aceita `scope=full|current` (padrão `full` para compatibilidade).

- `scope=full`: comportamento existente, empacota o diretório inteiro do projeto
- `scope=current`:
  - ignora arquivos históricos sob `versions/` (`versions/storyboards/`, `versions/videos/` etc.)
  - mantém `versions/versions.json`, recortado para conter só entradas da current version
  - o campo `scope` do manifesto `arcreel-export.json` fica `"current"`

### 3. Estratégia de recorte de versions.json

Na exportação "apenas versão atual", cada recurso em `versions.json` mantém só o registro de versão apontado por `current_version`. Assim:
- preserva metadados de geração como prompt e created_at
- o arquivo da versão atual existe no diretório principal de recursos, não em subdiretórios de versions/
- após importar, o VersionManager funciona normalmente (só uma versão)

### 4. Interação no frontend: diálogo de seleção ao clicar em exportar

Ao clicar em "Exportar ZIP", abre um diálogo compacto de seleção (não modal em tela cheia) com dois cartões de opção:
- "Apenas versão atual" (recomendado, volume menor)
- "Todos os dados" (com histórico de versões)

Após a escolha, emite o download token imediatamente → download nativo do navegador.

## Risks / Trade-offs

- **[Download token com validade curta demais]** → a janela de 5 minutos cobre o atraso entre emissão e o navegador iniciar a requisição. Em latência extrema, o usuário pode clicar em exportar de novo.
- **[Download token não é estritamente de uso único]** → em teoria, nos 5 minutos o token pode ser reusado para vários downloads, mas está vinculado ao nome do projeto + curta duração; risco aceitável. Uso único estrito exigiria nonce no Redis depois.
- **[Recortar versions.json pode perder contexto histórico]** → comportamento esperado de "apenas versão atual"; a UI deve deixar isso claro na escolha.
- **[Compatibilidade]** → `scope` padrão é `full`; chamadores existentes (se houver integração externa) não são afetados.
