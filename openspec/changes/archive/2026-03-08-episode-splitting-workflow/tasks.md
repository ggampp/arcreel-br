## 1. Desenvolvimento dos scripts centrais

- [x] 1.1 Criar o módulo compartilhado de utilitários `_text_utils.py`: implementar `count_chars(text)` (contagem com pontuação, sem linhas em branco) e `find_char_offset(text, target_count)` (meta de caracteres válidos → offset no texto original), compartilhados pelos dois scripts
- [x] 1.2 Criar o script `peek_split_point.py`: parâmetros `--source`, `--target` (meta de caracteres), `--context` (contexto, padrão 200); localizar o ponto de corte com `_text_utils`; saída com contexto antes/depois + metadados (total de caracteres, offset na posição-alvo, lista de pontos de quebra naturais próximos recomendados)
- [x] 1.3 Criar o script `split_episode.py`: parâmetros `--source`, `--episode`, `--anchor` (trecho de ~10–20 caracteres antes do ponto de corte); buscar a âncora no original e cortar no fim dela; modo `--dry-run` (só prévia: 50 caracteres do fim da parte anterior + início da parte seguinte, sem gravar); na execução real gerar `source/episode_{N}.txt` (primeira metade) e `source/_remaining.txt` (resto); se a âncora casar em vários pontos, erro pedindo âncora mais longa; o arquivo original não é alterado

## 2. Permissões e configuração

- [x] 2.1 Em `permissions.allow` de `settings.json`, adicionar permissão Bash de `peek_split_point.py` e `split_episode.py`

## 3. Integração no fluxo de trabalho

- [x] 3.1 Atualizar a etapa 2 de `manga-workflow/SKILL.md`: lógica de checagem prévia — verificar se `source/episode_{N}.txt` existe; se não, disparar o planejamento de divisão (perguntar meta de caracteres → chamar peek → agent sugere ponto de quebra → usuário confirma → chamar split)
- [x] 3.2 Atualizar o subagent `normalize-drama-script.md`: no dispatch, usar explicitamente o parâmetro `--source source/episode_{N}.txt`
- [x] 3.3 Atualizar o subagent `split-narration-segments.md`: no dispatch, especificar leitura de `source/episode_{N}.txt`

## 4. Verificação

- [x] 4.1 Validar a precisão da contagem de caracteres do script peek em romance em chinês (com pontuação, sem linhas em branco)
- [x] 4.2 Validar o resultado do script split: conteúdo de episode + remaining concatenados = original
- [x] 4.3 Validação ponta a ponta: enviar romance completo → divisão em episódios → normalize_drama_script.py --source episode_1.txt → generate_script.py gera JSON
