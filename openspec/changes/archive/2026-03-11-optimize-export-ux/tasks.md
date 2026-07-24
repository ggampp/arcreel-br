## 1. Implementação backend do download token

- [x] 1.1 Em `server/auth.py`, adicionar as funções `create_download_token(username, project_name)` e `verify_download_token(token, project_name)`
- [x] 1.2 Em `server/routers/projects.py`, adicionar o endpoint `POST /api/v1/projects/{name}/export/token` para emitir o download token
- [x] 1.3 Alterar o middleware de autenticação em `server/app.py` para liberar requisições ao caminho `/api/v1/projects/*/export` que carreguem o query param `download_token`
- [x] 1.4 Alterar o endpoint de exportação em `server/routers/projects.py` para autenticar via query param `download_token` (validar purpose, project e expiração)
- [x] 1.5 Escrever testes unitários da lógica de download token (complementar `tests/test_auth.py` + `tests/test_projects_archive_routes.py`)

## 2. Implementação backend do escopo de exportação (Scope)

- [x] 2.1 Alterar o endpoint de exportação em `server/routers/projects.py` para aceitar o query param `scope` (`full` / `current`, padrão `full`) e repassar a `ProjectArchiveService`
- [x] 2.2 Alterar o método `export_project` em `server/services/project_archive.py` para aceitar o parâmetro `scope`
- [x] 2.3 Implementar a lógica `scope=current`: ao percorrer o diretório, ignorar arquivos sob `versions/storyboards/`, `versions/videos/`, `versions/characters/`, `versions/clues/`
- [x] 2.4 Implementar o recorte de `versions/versions.json` em `scope=current`: manter só a entrada current_version de cada recurso
- [x] 2.5 Alterar a gravação do manifesto `arcreel-export.json` para o campo `scope` refletir o escopo real
- [x] 2.6 Escrever testes unitários da lógica de scope (complementar `tests/test_project_archive_service.py`)

## 3. Remodelar a interação de exportação no frontend

- [x] 3.1 Em `frontend/src/api.ts`, adicionar o método `requestExportToken(projectName)` chamando o endpoint de emissão de token
- [x] 3.2 Em `frontend/src/api.ts`, adicionar o helper `getExportDownloadUrl(projectName, downloadToken, scope)` montando a URL completa de download
- [x] 3.3 Criar o componente `ExportScopeDialog` (diálogo reutilizável) com as opções "Apenas versão atual" e "Todos os dados"
- [x] 3.4 Alterar `handleExportProject` em `GlobalHeader.tsx`: ao clicar em exportar, abrir `ExportScopeDialog`; após a escolha, emitir o token e disparar o download nativo com `window.open`
- [x] 3.5 Remover a lógica antiga `exportProject` fetch+Blob em `frontend/src/api.ts` (após confirmar que não há outros chamadores)
- [x] 3.6 Escrever testes das mudanças de exportação no frontend (complementar `GlobalHeader.test.tsx` + testes de API)
