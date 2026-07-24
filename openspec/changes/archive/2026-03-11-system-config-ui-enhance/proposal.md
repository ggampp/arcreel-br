## Why

A página de configuração do sistema tem classificação pouco clara, interação inconsistente (só alguns campos têm botão limpar) e usabilidade ruim (o botão salvar fica no fim da página e exige rolar para ver). A experiência de configuração é fraca e precisa de refatoração ampla para melhorar facilidade de uso e consistência.

## What Changes

- **Estrutura de múltiplas Tabs na barra superior**: dividir todas as configurações em quatro Tabs na barra superior, ao lado da "API Keys" existente: **Configuração do agente ArcReel**, **Configuração de geração de imagem/vídeo IA**, **Configuração avançada**, **API Keys**
- **Salvamento por bloco + percepção de não salvo**: cada Tab tem botão salvar independente; quando qualquer campo da Tab é modificado, o botão salvar fica em destaque e o rodapé fica sticky na parte inferior da tela, para o usuário perceber e salvar sem rolar
- **Interação de limpar unificada**: botão limpar em todos os campos de configuração opcionais (base_url, api key etc.), eliminando a inconsistência atual
- **Aviso de configuração obrigatória ausente**: quando a API Key do agente ArcReel (Anthropic) ou o backend de geração IA (AI Studio / Vertex AI, um dos dois) não estiver configurado, o sistema não funciona normalmente; é preciso aviso claro no ponto de entrada de configurações do hall de projetos e na própria página de configurações
- **Normas de design**: usar a skill `/frontend-design` para o UI e a skill `/vercel-react-best-practices` no desenvolvimento frontend

## Capabilities

### New Capabilities

- `system-config-ui`: normas de interação UI da página de configuração do sistema, incluindo estrutura de navegação por Tabs, mecanismo de salvamento por Tab, design de percepção de alterações não salvas, norma unificada de botão limpar e aviso de configuração obrigatória ausente

### Modified Capabilities

(não é necessário alterar specs existentes; esta mudança é só na camada de UI do frontend e não afeta contrato de API nem estrutura de dados)

## Impact

- **Arquivo principal**: `frontend/src/components/pages/SystemConfigPage.tsx` (refatoração considerável)
- **Arquivos relacionados**: `frontend/src/components/pages/ProjectsPage.tsx` (badge de aviso no ponto de entrada de configurações), `frontend/src/components/layout/GlobalHeader.tsx` (badge de aviso no ponto de entrada de configurações)
- **Não afeta**: API de backend, definições de tipos (`types/system.ts`), rotas de backend (`server/routers/system_config.py`)
- **Dependências**: sem novas dependências externas; usa o sistema de estilos Tailwind CSS existente
