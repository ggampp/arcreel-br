# Ad music library (project-local)

BGM for ad compose is **project-scoped**, not a global CDN library.

## Usage

1. Create a `music/` directory under the project root (next to `project.json`).
2. Place royalty-cleared audio files there (e.g. `music/upbeat.mp3`).
3. Set on the ad project:

```json
"ad_timeline": {
  "music_track": "music/upbeat.mp3",
  "text_overlays": [
    { "text": "限时优惠", "start": 0, "end": 3, "position": "bottom" }
  ]
}
```

4. Run `compose-video` on `scripts/episode_1.json`, or pass `--music music/upbeat.mp3`.

This folder under `public/` is documentation only; do not ship copyrighted tracks in the repo.
