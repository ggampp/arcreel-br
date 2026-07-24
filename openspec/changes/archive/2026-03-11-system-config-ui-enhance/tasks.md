## 1. Fase de design (usar /frontend-design)

- [x] 1.1 Usar a skill `/frontend-design` para o visual das quatro Tabs da barra superior (incluindo badge de ponto e estado ativo da Tab)
- [x] 1.2 Usar a skill `/frontend-design` para os dois estados do componente `TabSaveFooter`: embutido normal (desabilitado) e sticky em destaque (com alterações não salvas)

## 2. Componente reutilizável: TabSaveFooter

- [x] 2.1 Criar o componente `TabSaveFooter` com props `isDirty`, `saving`, `error`, `onSave`, `onReset`
- [x] 2.2 Implementar a lógica sticky: com `isDirty` true, adicionar estilos `sticky bottom-0 z-10 shadow`; botão salvar em cor primary de destaque
- [x] 2.3 Adicionar botão "Desfazer", visível com `isDirty` true; o clique dispara `onReset`
- [x] 2.4 Com `saving` true, estado de carregamento e botões desabilitados; com `error` não vazio, mensagem de erro ao lado do botão

## 3. Componentes de Tab de configuração

- [x] 3.1 Criar o componente `AgentConfigTab` (Configuração do agente ArcReel), mantendo o estado de rascunho dos campos Anthropic, com `TabSaveFooter` no fim
- [x] 3.2 Criar o componente `MediaConfigTab` (Configuração de geração de imagem/vídeo IA), mantendo o estado de rascunho dos campos Gemini/Vertex, com `TabSaveFooter` no fim
- [x] 3.3 Criar o componente `AdvancedConfigTab` (Configuração avançada), mantendo o estado de rascunho dos campos de rate limit/concorrência, com `TabSaveFooter` no fim
- [x] 3.4 Em cada Tab de configuração, implementar detecção de `isDirty` (`deepEqual` comparando rascunho e valor salvo em `useRef`)

## 4. Navegação de Tabs na barra superior e badges

- [x] 4.1 Trocar as Tabs da barra superior de `[config, api-keys]` para `[agent, media, advanced, api-keys]`, mantendo o componente `ApiKeysTab` inalterado
- [x] 4.2 Implementar badge de ponto na Tab: quando uma Tab de configuração tem alterações não salvas, exibir ponto (●) ao lado do rótulo; o badge permanece ao trocar de Tab

## 5. Botão limpar unificado

- [x] 5.1 Em todos os campos opcionais (base_url, api key etc. não obrigatórios), adicionar botão limpar (×) unificado; visível com valor, oculto quando vazio
- [x] 5.2 Ao clicar em limpar, zerar o valor do campo e disparar a atualização de `isDirty` da Tab correspondente

## 6. Integração e limpeza do SystemConfigPage

- [x] 6.1 Refatorar `SystemConfigPage` como camada de orquestração, compondo os quatro componentes de Tab; remover o estado de rascunho global e o botão salvar global no fim
- [x] 6.2 Manter a funcionalidade de Connection Test, garantindo que continue funcionando (na Tab correspondente)
- [x] 6.3 Adicionar `padding-bottom` suficiente no fim da página para o rodapé sticky não cobrir a última linha de conteúdo

## 7. Detecção e aviso de configuração obrigatória ausente

- [x] 7.1 Implementar a função utilitária `getConfigIssues(config)`: checar `anthropic_api_key.is_set`, credenciais do image backend (`gemini_api_key.is_set` ou `vertex_credentials.is_set`) e do video backend; emitir `ConfigIssue[]` e unificar entradas image/video com o mesmo provedor e o mesmo motivo; encapsular requisição e cache no hook `useConfigStatus`, expondo `issues: ConfigIssue[]` e `isComplete: boolean`
- [x] 7.2 Em `ProjectsPage.tsx`, no botão de configurações (por volta da linha 358), adicionar badge de ponto vermelho quando `isConfigComplete === false`
- [x] 7.3 Em `GlobalHeader.tsx`, no botão de configurações (por volta da linha 323), adicionar badge de ponto vermelho quando `isConfigComplete === false`
- [x] 7.4 Em `SystemConfigPage`, acima da navegação de Tabs, adicionar o componente de banner de aviso listando itens obrigatórios ausentes com links para a Tab correspondente
- [x] 7.5 Após salvamento bem-sucedido da Tab de configuração, disparar redetecção em `useConfigStatus`, garantindo atualização em tempo real de badge e banner

## 8. Garantia de qualidade (usar /vercel-react-best-practices)

- [x] 8.1 Usar a skill `/vercel-react-best-practices` para revisar a implementação dos componentes (useRef para savedValues evitando re-renders desnecessários, cache de deepEqual etc.)
- [x] 8.2 Rodar `pnpm typecheck` garantindo zero erros de tipo no TypeScript
- [x] 8.3 Validação manual: após modificar campos, rodapé sticky + badge na Tab; após salvar, sticky removido; ao trocar de Tab, badge permanece; ao desfazer, valores originais; botão limpar funciona
- [x] 8.4 Validação manual do aviso de configuração ausente: sem configurar, ponto vermelho no botão de configurações e banner na página; após completar e salvar, badge e banner somem em tempo real
