## ADDED Requirements

### Requirement: Entrada de anexos de imagem
O sistema SHALL permitir que o usuário anexe imagens na área de entrada do chat por colar, clique para upload ou arrastar e soltar.

#### Scenario: Colar imagem
- **WHEN** o usuário pressiona Ctrl+V (ou Cmd+V) na área de entrada e a área de transferência contém uma imagem
- **THEN** o sistema adiciona a imagem à lista de anexos e exibe a miniatura acima do campo de entrada

#### Scenario: Upload por clique
- **WHEN** o usuário clica no botão de anexo ao lado do campo de entrada e seleciona uma ou mais imagens no seletor de arquivos
- **THEN** o sistema adiciona as imagens selecionadas à lista de anexos e exibe as miniaturas

#### Scenario: Arrastar e soltar imagens
- **WHEN** o usuário arrasta arquivos de imagem para a área de entrada e solta
- **THEN** o sistema adiciona as imagens à lista de anexos e exibe as miniaturas; durante o arraste, a área de entrada SHALL destacar o feedback de drop

#### Scenario: Exceder o limite de quantidade
- **WHEN** o número atual de anexos já é 5 e o usuário tenta adicionar mais imagens
- **THEN** o sistema ignora as novas imagens e o botão de anexo SHALL ficar desabilitado

#### Scenario: Exceder o limite de tamanho de arquivo
- **WHEN** o usuário adiciona uma imagem maior que 5MB
- **THEN** o sistema recusa a adição e exibe uma mensagem de erro ao usuário

#### Scenario: Remover anexo
- **WHEN** o usuário clica no botão de exclusão no canto superior direito de uma miniatura
- **THEN** o sistema remove a imagem da lista de anexos e a miniatura desaparece

### Requirement: Enviar mensagem com imagens
O sistema SHALL, ao enviar a mensagem, submeter as imagens anexadas junto com o conteúdo de texto ao Agent.

#### Scenario: Enviar mensagem com imagens
- **WHEN** o usuário clica em enviar (ou pressiona Enter) com a lista de anexos não vazia
- **THEN** o sistema combina texto e dados base64 das imagens em uma mensagem multimodal e envia; após o envio, a lista de anexos SHALL ser limpa

#### Scenario: Enviar apenas texto
- **WHEN** o usuário envia uma mensagem com a lista de anexos vazia
- **THEN** o comportamento do sistema permanece igual ao envio de texto puro original

### Requirement: Renderização de mensagens com imagem
O sistema SHALL renderizar corretamente as imagens enviadas pelo usuário no histórico da conversa e suportar clique para ampliar.

#### Scenario: Exibição imediata após o envio
- **WHEN** uma mensagem com imagens é enviada com sucesso
- **THEN** o balão do usuário SHALL exibir miniaturas das imagens (altura máxima 256px), com o texto abaixo das imagens

#### Scenario: Exibição no replay do histórico
- **WHEN** o usuário recarrega uma sessão existente
- **THEN** as mensagens históricas com imagens SHALL renderizar corretamente o conteúdo das imagens

#### Scenario: Clicar na miniatura para ampliar
- **WHEN** o usuário clica na miniatura de uma imagem na conversa
- **THEN** o sistema exibe a imagem original em tela cheia no formato lightbox; clique na máscara ou Esc fecha

#### Scenario: Clicar na imagem pendente de envio para ampliar
- **WHEN** o usuário clica na miniatura de um anexo na área de entrada
- **THEN** o sistema exibe essa imagem em tela cheia no formato lightbox; clique na máscara ou Esc fecha
