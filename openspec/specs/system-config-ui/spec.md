## ADDED Requirements

### Requirement: Estrutura de seções na barra lateral

A página de configuração do sistema (`SystemConfigPage`, rota `/app/settings`, seção controlada pelo query `?section=`) SHALL alternar entre as seções a seguir via navegação na barra lateral esquerda: **Fornecedores** (providers), **Configuração do agente ArcReel** (agent), **Configuração de geração de imagem/vídeo IA** (media), **Estatísticas de uso** (usage), **API Keys** (api-keys), **Sobre** (about).

Conteúdo de cada seção:
- **Fornecedores**: gerenciamento de configuração de fornecedores predefinidos / personalizados
- **Configuração do agente ArcReel**: Anthropic API Key, Base URL, campos de seleção de modelos e ajustes avançados de runtime (rate limit / workers concorrentes; advanced settings recolhidos nesta seção, sem seção própria)
- **Configuração de geração de imagem/vídeo IA**: Gemini API Key, Base URL, seleção de backend, seleção de modelo, credenciais Vertex etc.
- **Estatísticas de uso**: resumo de uso de API e custos
- **API Keys**: gerenciamento de API Keys
- **Sobre**: versão e informações do projeto

#### Scenario: Usuário abre a página de configuração do sistema
- **WHEN** o usuário navega para `/app/settings` (sem section especificada)
- **THEN** a página SHALL exibir a navegação de seções na barra lateral, com a seção **Fornecedores** (providers) ativa por padrão

#### Scenario: Seção especificada via query
- **WHEN** o usuário acessa `/app/settings?section=api-keys`
- **THEN** a página SHALL ativar diretamente a seção **API Keys**

---

### Requirement: Salvamento independente por seção

Cada seção de configuração (agent / media) SHALL oferecer operação de salvamento independente, salvando de uma vez todos os campos modificados da seção, sem afetar outras seções.

#### Scenario: Usuário modifica campos na seção e salva
- **WHEN** o usuário modifica qualquer campo de uma seção de configuração e clica no botão salvar da seção
- **THEN** o sistema SHALL fazer PATCH de todos os campos modificados da seção; após sucesso, a seção volta ao estado não modificado

#### Scenario: Estado de salvamento em andamento na seção
- **WHEN** a requisição de salvamento da seção está em andamento
- **THEN** todos os campos de entrada da seção SHALL ser desabilitados e o botão salvar exibe estado de carregamento, evitando envio duplicado

#### Scenario: Falha no salvamento da seção
- **WHEN** a requisição de salvamento retorna erro
- **THEN** o sistema SHALL exibir mensagem de erro ao lado do botão salvar, mantendo os valores editados pelo usuário

#### Scenario: Seção sem alterações não salvas
- **WHEN** todos os valores de campo da seção são iguais aos valores já salvos
- **THEN** o botão salvar SHALL ficar desabilitado

---

### Requirement: Percepção de alterações não salvas — rodapé sticky de salvamento + badge na Tab

Quando houver alterações não salvas em uma Tab de configuração, o rodapé de salvamento dessa Tab SHALL ficar sticky na parte inferior do viewport, e um badge de ponto SHALL aparecer ao lado do rótulo da Tab, para o usuário perceber e poder salvar a qualquer momento.

#### Scenario: Tab com alterações não salvas
- **WHEN** o usuário modifica qualquer valor de campo na Tab de configuração atual
- **THEN** o rodapé de salvamento dessa Tab SHALL ficar sticky na parte inferior da tela, o botão salvar SHALL ficar em destaque (tom primary) e um badge de ponto (●) SHALL aparecer ao lado do rótulo da Tab

#### Scenario: Tab sem alterações não salvas
- **WHEN** todos os valores de campo da Tab são iguais aos valores salvos
- **THEN** o rodapé de salvamento SHALL renderizar normalmente no fim do conteúdo da Tab (não sticky) e o botão salvar SHALL ficar desabilitado

#### Scenario: Após salvamento bem-sucedido da Tab
- **WHEN** a requisição de salvamento conclui com sucesso
- **THEN** o estado sticky SHALL ser removido, o rodapé volta ao fim do conteúdo da Tab e o badge do rótulo da Tab desaparece

#### Scenario: Usuário desfaz alterações
- **WHEN** o usuário clica no botão "Desfazer" do rodapé de salvamento
- **THEN** todos os valores de campo da Tab SHALL voltar aos últimos valores salvos com sucesso e o estado sticky é removido

#### Scenario: Usuário troca para outra Tab (com alterações não salvas)
- **WHEN** o usuário clica em outra Tab, mas a Tab atual tem alterações não salvas
- **THEN** o sistema SHALL permitir a troca; o badge de ponto no rótulo da Tab original SHALL permanecer, lembrando o usuário das alterações não salvas

---

### Requirement: Todos os campos opcionais oferecem botão limpar de forma unificada

Todos os campos de configuração não obrigatórios (incluindo base_url, API key etc. opcionais) SHALL exibir botão limpar (×) quando tiverem valor; o clique limpa imediatamente o valor e dispara o estado não salvo da Tab.

#### Scenario: Usuário limpa o valor do campo
- **WHEN** um campo opcional tem valor e o usuário clica no botão limpar
- **THEN** o valor do campo SHALL ser limpo imediatamente, o botão limpar desaparece e a Tab entra em estado modificado (rodapé de salvamento fica sticky)

#### Scenario: Campo vazio
- **WHEN** o valor do campo opcional está vazio
- **THEN** o botão limpar SHALL não ser exibido

---

### Requirement: Aviso no ponto de entrada global quando configuração obrigatória está ausente

Quando a configuração obrigatória do sistema não estiver completa, todos os pontos de entrada para a página de configurações SHALL ser marcados com badge de ponto vermelho, lembrando o usuário de completar a configuração.

**Definição de configuração obrigatória**: as três condições a seguir devem ser atendidas para o sistema funcionar normalmente:
1. API Key do agente ArcReel (`anthropic_api_key.is_set`)
2. Credenciais do backend de geração de imagem IA: se `image_backend = "aistudio"` então `gemini_api_key.is_set`; se `"vertex"` então `vertex_credentials.is_set`
3. Credenciais do backend de geração de vídeo IA: se `video_backend = "aistudio"` então `gemini_api_key.is_set`; se `"vertex"` então `vertex_credentials.is_set`

#### Scenario: Entrar no hall de projetos com configuração obrigatória incompleta
- **WHEN** o usuário entra no hall de projetos após o login e a configuração obrigatória está incompleta
- **THEN** o botão de configurações no canto superior direito do hall SHALL exibir badge de ponto vermelho

#### Scenario: Dentro do workspace com configuração obrigatória incompleta
- **WHEN** o usuário está em qualquer workspace de projeto e a configuração obrigatória está incompleta
- **THEN** o botão de configurações no canto superior direito do Header global SHALL exibir badge de ponto vermelho

#### Scenario: Configuração obrigatória completa
- **WHEN** toda a configuração obrigatória do sistema está definida
- **THEN** o botão de configurações SHALL não exibir nenhum badge, no estado normal

#### Scenario: Após o usuário salvar a configuração faltante
- **WHEN** o usuário salva com sucesso os campos obrigatórios faltantes na página de configurações
- **THEN** o badge nos pontos de entrada globais SHALL desaparecer em tempo real, sem recarregar a página

---

### Requirement: Aviso dentro da página de configurações quando configuração obrigatória está ausente

Quando a configuração obrigatória do sistema estiver incompleta, a página de configurações SHALL exibir um banner de aviso acima da navegação de Tabs, listando cada motivo de ausência e oferecendo links rápidos para a Tab correspondente.

#### Scenario: Anthropic API Key não configurada
- **WHEN** o usuário entra na página de configurações e `anthropic_api_key.is_set === false`
- **THEN** o banner de aviso SHALL incluir a linha "API Key do agente ArcReel (Anthropic) não configurada", com link para a Tab "Configuração do agente ArcReel"

#### Scenario: Credenciais do backend de geração de imagem não configuradas (AI Studio)
- **WHEN** `image_backend = "aistudio"` e `gemini_api_key.is_set === false`
- **THEN** o banner de aviso SHALL incluir a linha "API Key de geração de imagem IA (Gemini AI Studio) não configurada", com link para a Tab "Configuração de geração de imagem/vídeo IA"

#### Scenario: Credenciais do backend de geração de imagem não configuradas (Vertex)
- **WHEN** `image_backend = "vertex"` e `vertex_credentials.is_set === false`
- **THEN** o banner de aviso SHALL incluir a linha "Credenciais Vertex AI de geração de imagem não enviadas", com link para a Tab "Configuração de geração de imagem/vídeo IA"

#### Scenario: Credenciais do backend de geração de vídeo não configuradas (AI Studio)
- **WHEN** `video_backend = "aistudio"` e `gemini_api_key.is_set === false`
- **THEN** o banner de aviso SHALL incluir a linha "API Key de geração de vídeo IA (Gemini AI Studio) não configurada", com link para a Tab "Configuração de geração de imagem/vídeo IA"

#### Scenario: Credenciais do backend de geração de vídeo não configuradas (Vertex)
- **WHEN** `video_backend = "vertex"` e `vertex_credentials.is_set === false`
- **THEN** o banner de aviso SHALL incluir a linha "Credenciais Vertex AI de geração de vídeo não enviadas", com link para a Tab "Configuração de geração de imagem/vídeo IA"

#### Scenario: Deduplicação do mesmo motivo de ausência
- **WHEN** `image_backend` e `video_backend` usam o mesmo provedor e as credenciais desse provedor não estão configuradas
- **THEN** o banner de aviso SHALL unificar em uma linha (ex.: "API Key de geração de imagem/vídeo IA (Gemini AI Studio) não configurada"), sem repetir

#### Scenario: Toda a configuração obrigatória concluída
- **WHEN** toda a configuração obrigatória do sistema está definida
- **THEN** a página de configurações SHALL não exibir o banner de aviso

---

### Requirement: Isolamento do estado de rascunho por Tab

A página SHALL manter estado de rascunho independente por Tab de configuração; os estados entre Tabs são isolados e trocar de Tab não reseta alterações não salvas de outras Tabs.

#### Scenario: Modificar campos em várias Tabs ao mesmo tempo
- **WHEN** o usuário faz alterações em várias Tabs (todas sem salvar)
- **THEN** cada Tab com alterações SHALL exibir badge de ponto no rótulo, e o estado de rascunho de cada Tab permanece independente

#### Scenario: Carga inicial da página
- **WHEN** os dados de configuração terminam de carregar da API
- **THEN** todas as Tabs SHALL estar sem alterações não salvas, com rodapé de salvamento não sticky e desabilitado
