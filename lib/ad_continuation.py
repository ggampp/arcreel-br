"""广告镜头间 last-frame 续写：上一镜视频尾帧作为下一镜 i2v 起始帧。

默认开启（project.ad_continuation 缺省 true）；显式 false 关闭。
仅 content_mode=ad 且 storyboard 路径消费；reference_video 路径跳过分镜、由 unit 直出，
不走本模块。

设计对齐 AdForge Consistency：continuation 优先于本镜 storyboard 作为 start_image，
storyboard 仍可经 reference 路径保留构图意图（由调用方决定是否附加）。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from lib.storyboard_sequence import get_storyboard_items
from lib.thumbnail import extract_video_last_frame

logger = logging.getLogger(__name__)

# 尾帧缓存相对项目根的目录（与 storyboards 并列，便于清理与版本无关）
LAST_FRAME_SUBDIR = "videos/last_frames"


def ad_continuation_enabled(project: dict[str, Any]) -> bool:
    """ad 项目默认开启续写；非 ad 恒 false。显式 false/0/"false" 关闭。"""
    if project.get("content_mode") != "ad":
        return False
    raw = project.get("ad_continuation")
    if raw is None:
        return True
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return raw != 0
    if isinstance(raw, str):
        return raw.strip().lower() not in {"0", "false", "no", "off"}
    return bool(raw)


def last_frame_relpath(resource_id: str) -> str:
    """上一镜（或本镜）尾帧相对路径约定。"""
    safe = str(resource_id).replace("/", "_").replace("\\", "_")
    return f"{LAST_FRAME_SUBDIR}/{safe}_last.png"


def resolve_previous_item(
    items: list[dict[str, Any]],
    id_field: str,
    resource_id: str,
) -> dict[str, Any] | None:
    """返回播放顺序上紧邻的前一个条目；当前为第一条或不存在时返回 None。"""
    for idx, item in enumerate(items):
        if str(item.get(id_field)) == str(resource_id):
            if idx <= 0:
                return None
            prev = items[idx - 1]
            return prev if isinstance(prev, dict) else None
    return None


def resolve_previous_video_path(
    project_path: Path,
    items: list[dict[str, Any]],
    id_field: str,
    resource_id: str,
) -> Path | None:
    """解析上一镜 video_clip 绝对路径；不存在返回 None。"""
    prev = resolve_previous_item(items, id_field, resource_id)
    if not prev:
        return None
    assets = prev.get("generated_assets")
    if not isinstance(assets, dict):
        return None
    rel = assets.get("video_clip")
    if not isinstance(rel, str) or not rel.strip():
        return None
    path = project_path / rel
    return path if path.is_file() else None


async def ensure_last_frame(
    video_path: Path,
    output_path: Path,
) -> Path | None:
    """提取视频尾帧到 output_path（已存在且非空则复用）。"""
    if output_path.is_file() and output_path.stat().st_size > 0:
        # 若源视频更新时间更晚则重提
        try:
            if output_path.stat().st_mtime >= video_path.stat().st_mtime:
                return output_path
        except OSError:
            pass
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = await extract_video_last_frame(video_path, output_path)
    if result is None:
        logger.info("尾帧提取失败，continuation 将降级: %s", video_path)
    return result


async def resolve_continuation_start_image(
    *,
    project: dict[str, Any],
    project_path: Path,
    script: dict[str, Any],
    resource_id: str,
    storyboard_file: Path,
) -> tuple[Path, bool]:
    """解析 ad 视频生成的 start_image。

    Returns:
        (path, used_continuation): used_continuation=True 表示用了上一镜尾帧。
    """
    if not ad_continuation_enabled(project):
        return storyboard_file, False

    try:
        items, id_field, *_ = get_storyboard_items(script)
    except Exception:
        return storyboard_file, False

    prev_video = resolve_previous_video_path(project_path, items, id_field, resource_id)
    if prev_video is None:
        return storyboard_file, False

    prev = resolve_previous_item(items, id_field, resource_id)
    prev_id = str((prev or {}).get(id_field) or "prev")
    # 优先复用剧本已写的 storyboard_last_image
    cached_rel: str | None = None
    if prev and isinstance(prev.get("generated_assets"), dict):
        raw = prev["generated_assets"].get("storyboard_last_image")
        if isinstance(raw, str) and raw.strip():
            cached_rel = raw
    if cached_rel:
        cached = project_path / cached_rel
        if cached.is_file() and cached.stat().st_size > 0:
            try:
                if cached.stat().st_mtime >= prev_video.stat().st_mtime:
                    return cached, True
            except OSError:
                return cached, True

    out = project_path / last_frame_relpath(prev_id)
    frame = await ensure_last_frame(prev_video, out)
    if frame is None:
        return storyboard_file, False
    return frame, True
