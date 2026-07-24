# Guia de Prompt de Geração de Vídeo Veo 3.1

Boas práticas para criar prompts eficazes de geração de vídeo com Veo 3.1.

## Estrutura do Prompt

Segundo as melhores práticas do Veo, o prompt deve conter os elementos abaixo (fundidos naturalmente, sem rótulos):

1. **Composition** composição: tipo de shot (wide shot, close-up, medium shot)
2. **Subject** sujeito: descrição da cena com personagens, ambiente e objetos
3. **Action** ação: o que o personagem está fazendo
4. **Dialogue** diálogo: Speaker (maneira) diz: "texto"
5. **Sound Effects** efeitos sonoros: integrados naturalmente à descrição da cena
6. **Camera** câmera: descrição natural do movimento
7. **Ambiance** atmosfera: luz e emoção

**Importante**: não escreva no prompt o seguinte (isso vai por parâmetro da API):
- Duração do vídeo (ex.: "8 segundos")
- Proporção (ex.: "16:9", "9:16")

## Diálogo e Áudio

### Formato de diálogo
```
O homem (segurando a faca de caça) diz: "Isso não é um urso comum."
A mulher (voz tensa de medo, olhando em volta) diz: "O que é isso?"
```

Use aspas no conteúdo do diálogo e, entre parênteses, descreva ação e maneira de falar.

### Descrições de maneira de falar
- `baixinho`, `sussurrando`, `gritando`, `murmurando`
- `com ternura`, `com nervosismo`, `com firmeza`
- `voz grave de homem`, `voz clara de mulher`

### Efeitos sonoros (integrados naturalmente)
Não use o rótulo "efeito sonoro:"; descreva naturalmente:
```
Um latido rouco, o estalo de galhos, passos na terra úmida. Um pássaro solitário pia.
```

```
O guincho agudo de pneus, o motor rugindo.
```

### Sobre BGM
- **Não descreva trilha de fundo no prompt**
- BGM é proibido automaticamente via parâmetro `negative_prompt`
- Trilha de pós-produção via `/compose-video`

## Movimento de câmera

| Termo em inglês | Descrição em português |
|---------|---------|
| static | câmera parada |
| pan left/right | pan da câmera para a esquerda/direita |
| tilt up/down | tilt da câmera para cima/baixo |
| dolly in/out | câmera avança/afasta devagar |
| track left/right | tracking da câmera para a esquerda/direita |
| crane up/down | câmera sobe/desce |
| handheld | câmera na mão com leve tremor |

## Tipos de shot

| Termo em inglês | Termo em português | Uso |
|---------|---------|---------|
| extreme close-up | extreme close-up / detalhe extremo | emoção, detalhe |
| close-up | close / close-up | rosto, diálogo |
| medium shot | plano médio | tronco superior, diálogo |
| full shot | plano inteiro | corpo inteiro |
| wide shot | plano geral | ambiente, establishing shot |
| aerial | vista aérea | perspectiva de cima |

## Negative Prompts

Use o parâmetro de API `negative_prompt` para excluir elementos indesejados:
- ❌ Não use linguagem negativa: "no walls"
- ✅ Descreva diretamente o que não quer: "walls, frames, borders"

Negative prompt padrão (aplicado automaticamente):
```
background music, BGM, soundtrack, musical accompaniment
```

## Exemplos

### Cena de diálogo e atmosfera
```
wide shot, floresta enevoada do noroeste do Pacífico. Dois caminhantes exaustos, um homem e uma mulher, atravessam um matagal de samambaias; o homem para de repente e fita uma árvore. close-up: na casca, marcas profundas e frescas de garras. O homem (segurando a faca de caça) diz: "Isso não é um urso comum." A mulher (voz tensa de medo, olhando em volta) diz: "O que é isso?" Um latido rouco, o estalo de galhos, passos na terra úmida. Um pássaro solitário pia.
```

### Cena de descrição detalhada
```
close-up cinematográfico segue um homem desesperado de casaco verde surrado discando um telefone de disco em uma parede de tijolo bruto, banhado pelo brilho sinistro de neon verde. A câmera avança devagar, revelando a mandíbula tensa e o desespero gravado no rosto enquanto ele luta para completar a ligação. Pouca profundidade de campo concentra-se na sobrancelha franzida e no telefone de disco preto; o fundo se dissolve em um mar de cores neon e sombras borradas, criando urgência e isolamento.
```

### Cena em estilo de animação
```
Uma cena de animação 3D alegre em estilo cartoon. Uma criatura fofa com pelagem de leopardo-das-neves, olhos grandes e expressivos e forma amigável e arredondada pula com alegria por uma floresta de inverno fantasiosa. A cena tem árvores arredondadas cobertas de neve, flocos caindo suaves e luz quente filtrando pelos galhos. O salto da criatura e o sorriso radiante transmitem pura alegria. Cores vivas e animação animada, tom aconchegante e reconfortante.
```

### Cena imagem→vídeo
```
Um vídeo surreal e cinematográfico em macro. Minúsculos surfistas pegam ondas que nunca param em uma pia de pedra. Uma torneira antiga de latão escorre água, criando um mar sem fim. A câmera faz pan devagar por essa cena fantasiosa e ensolarada; os personagens miniatura deslizam com habilidade sobre a água esverdeada.
```
