"""广告成片时间线：文字叠层 + 音乐轨元数据。

存放于 ``project.json`` 顶层 ``ad_timeline``（仅 content_mode=ad）：

```json
{
  "text_overlays": [
    {"text": "限时优惠", "start": 0.0, "end": 3.0, "position": "bottom"}
  ],
  "music_track": "music/upbeat.mp3"
}
```

position: top | center | bottom（默认 bottom）。
music_track 为项目内相对路径。
"""

from __future__ import annotations

from typing import Any

VALID_OVERLAY_POSITIONS = frozenset({"top", "center", "bottom"})


def empty_ad_timeline() -> dict[str, Any]:
    return {"text_overlays": [], "music_track": None}


def normalize_ad_timeline(raw: object) -> dict[str, Any]:
    out = empty_ad_timeline()
    if not isinstance(raw, dict):
        return out
    overlays = raw.get("text_overlays")
    if isinstance(overlays, list):
        cleaned: list[dict[str, Any]] = []
        for item in overlays:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            try:
                start = float(item.get("start", 0))
                end = float(item.get("end", start + 2))
            except (TypeError, ValueError):
                continue
            if end <= start:
                end = start + 0.5
            pos = item.get("position", "bottom")
            if pos not in VALID_OVERLAY_POSITIONS:
                pos = "bottom"
            cleaned.append({"text": text.strip(), "start": start, "end": end, "position": pos})
        out["text_overlays"] = cleaned
    track = raw.get("music_track")
    if isinstance(track, str) and track.strip():
        out["music_track"] = track.strip()
    elif track is None:
        out["music_track"] = None
    return out


def validate_ad_timeline(raw: object) -> list[str]:
    errors: list[str] = []
    if raw is None:
        return errors
    if not isinstance(raw, dict):
        return ["ad_timeline 必须是对象"]
    overlays = raw.get("text_overlays")
    if overlays is not None:
        if not isinstance(overlays, list):
            errors.append("ad_timeline.text_overlays 必须是列表")
        else:
            for i, item in enumerate(overlays):
                if not isinstance(item, dict):
                    errors.append(f"ad_timeline.text_overlays[{i}] 必须是对象")
                    continue
                if not isinstance(item.get("text"), str) or not item["text"].strip():
                    errors.append(f"ad_timeline.text_overlays[{i}].text 必须是非空字符串")
                for key in ("start", "end"):
                    if key in item and item[key] is not None:
                        try:
                            float(item[key])
                        except (TypeError, ValueError):
                            errors.append(f"ad_timeline.text_overlays[{i}].{key} 必须是数字")
                pos = item.get("position")
                if pos is not None and pos not in VALID_OVERLAY_POSITIONS:
                    errors.append(f"ad_timeline.text_overlays[{i}].position 必须是 {sorted(VALID_OVERLAY_POSITIONS)}")
    track = raw.get("music_track")
    if track is not None and not isinstance(track, str):
        errors.append("ad_timeline.music_track 必须是字符串或 null")
    return errors


def ad_video_takes(project: dict[str, Any], payload_takes: int | None = None) -> int:
    """解析多 take 次数：payload > project.ad_video_takes > 默认 1；范围 [1, 3]。

    默认 1 控制费用；需要多 take 对比时把 ``ad_video_takes`` 设为 2 或 3
    （或在入队 payload 传 ``takes_count``）。
    """
    if project.get("content_mode") != "ad":
        return 1
    raw = payload_takes
    if raw is None:
        raw = project.get("ad_video_takes")
    if raw is None:
        return 1
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return 1
    return max(1, min(3, n))
