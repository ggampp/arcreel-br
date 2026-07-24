# Biblioteca de música de anúncio (escopo de projeto)

O BGM do compose de anúncio é **escopado ao projeto**, não uma biblioteca global de CDN.

## Uso

1. Crie um diretório `music/` na raiz do projeto (ao lado de `project.json`).
2. Coloque ali arquivos de áudio com direitos liberados (ex.: `music/upbeat.mp3`).
3. Defina no projeto de anúncio:

```json
"ad_timeline": {
  "music_track": "music/upbeat.mp3",
  "text_overlays": [
    { "text": "限时优惠", "start": 0, "end": 3, "position": "bottom" }
  ]
}
```

4. Rode `compose-video` em `scripts/episode_1.json`, ou passe `--music music/upbeat.mp3`.

Esta pasta sob `public/` é só documentação; não envie faixas com copyright no repositório.
