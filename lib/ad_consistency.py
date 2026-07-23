"""广告产品一致性评审（Consistency Manager）。

MVP 采用「结构门禁 + 可选画面相似度」两层，不强制调用远程 vision：

1. 结构：产品镜头必须有 products_in_shot 且项目中存在对应 reference_images 或 sheet
2. 画面：若提供 product 参考图与视频尾帧/中间帧路径，用 PIL 直方图相关做粗相似度

score ∈ [0, 1]；默认 pass 阈值 0.45（直方图相关较松，避免误杀）。
agent / 服务可据此决定是否入队重生。
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_PASS_THRESHOLD = 0.45


@dataclass
class ConsistencyFinding:
    shot_id: str
    score: float
    passed: bool
    reasons: list[str] = field(default_factory=list)
    recommend_regen: bool = False
    product_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _histogram_similarity(image_a: Path, image_b: Path) -> float | None:
    """RGB 直方图相关系数，映射到约 [0,1]。失败返回 None。"""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(image_a) as im_a, Image.open(image_b) as im_b:
            a = im_a.convert("RGB").resize((64, 64))
            b = im_b.convert("RGB").resize((64, 64))
            ha = a.histogram()
            hb = b.histogram()
    except Exception:
        logger.debug("直方图相似度计算失败", exc_info=True)
        return None

    # 皮尔逊相关
    n = len(ha)
    if n == 0 or n != len(hb):
        return None
    mean_a = sum(ha) / n
    mean_b = sum(hb) / n
    num = sum((ha[i] - mean_a) * (hb[i] - mean_b) for i in range(n))
    den_a = sum((ha[i] - mean_a) ** 2 for i in range(n)) ** 0.5
    den_b = sum((hb[i] - mean_b) ** 2 for i in range(n)) ** 0.5
    if den_a == 0 or den_b == 0:
        return 0.0
    corr = num / (den_a * den_b)
    # 相关约 [-1,1] → [0,1]
    return max(0.0, min(1.0, (corr + 1.0) / 2.0))


def _first_product_ref_path(project: dict[str, Any], project_path: Path, name: str) -> Path | None:
    products = project.get("products")
    if not isinstance(products, dict):
        return None
    data = products.get(name)
    if not isinstance(data, dict):
        return None
    sheet = data.get("product_sheet")
    if isinstance(sheet, str) and sheet.strip():
        p = project_path / sheet
        if p.is_file():
            return p
    refs = data.get("reference_images")
    if isinstance(refs, list):
        for rel in refs:
            if isinstance(rel, str) and rel.strip():
                p = project_path / rel
                if p.is_file():
                    return p
    return None


def critique_ad_shot(
    *,
    project: dict[str, Any],
    project_path: Path,
    shot: dict[str, Any],
    frame_path: Path | None = None,
    threshold: float = DEFAULT_PASS_THRESHOLD,
) -> ConsistencyFinding:
    """评审单个 ad shot 的产品一致性。"""
    shot_id = str(shot.get("shot_id") or shot.get("segment_id") or shot.get("scene_id") or "?")
    products_in_shot = shot.get("products_in_shot")
    if not isinstance(products_in_shot, list):
        products_in_shot = []
    names = [str(n) for n in products_in_shot if n]

    reasons: list[str] = []
    # 氛围镜头：无产品，结构上直接通过
    if not names:
        return ConsistencyFinding(
            shot_id=shot_id,
            score=1.0,
            passed=True,
            reasons=["氛围镜头（products_in_shot 为空），跳过产品一致性检查"],
            recommend_regen=False,
            product_names=[],
        )

    products = project.get("products") if isinstance(project.get("products"), dict) else {}
    missing: list[str] = []
    no_ref: list[str] = []
    ref_paths: list[Path] = []
    for name in names:
        if name not in products:
            missing.append(name)
            continue
        ref = _first_product_ref_path(project, project_path, name)
        if ref is None:
            no_ref.append(name)
        else:
            ref_paths.append(ref)

    structural_score = 1.0
    if missing:
        reasons.append(f"剧本引用了未登记产品：{', '.join(missing)}")
        structural_score = 0.0
    if no_ref:
        reasons.append(f"产品缺少原图/sheet 参考：{', '.join(no_ref)}")
        structural_score = min(structural_score, 0.2)

    visual_score: float | None = None
    if frame_path and frame_path.is_file() and ref_paths and structural_score > 0:
        sims = [_histogram_similarity(ref_paths[0], frame_path)]
        sims = [s for s in sims if s is not None]
        if sims:
            visual_score = sims[0]
            reasons.append(f"画面-产品参考直方图相似度 {visual_score:.2f}")
        else:
            reasons.append("无法计算画面相似度（解码失败）")

    if visual_score is not None:
        score = 0.4 * structural_score + 0.6 * visual_score
    else:
        score = structural_score
        if structural_score >= 1.0:
            reasons.append("仅结构检查通过（无可用帧/参考对比）")

    passed = score >= threshold and not missing
    recommend = not passed
    if recommend:
        reasons.append("建议重新生成该镜头视频（更换 seed 或强化产品参考）")

    return ConsistencyFinding(
        shot_id=shot_id,
        score=round(score, 3),
        passed=passed,
        reasons=reasons,
        recommend_regen=recommend,
        product_names=names,
    )


def critique_ad_script(
    *,
    project: dict[str, Any],
    project_path: Path,
    script: dict[str, Any],
    threshold: float = DEFAULT_PASS_THRESHOLD,
) -> list[ConsistencyFinding]:
    """评审剧本全部 shots（仅对有 video_clip 的做画面层）。"""
    shots = script.get("shots")
    if not isinstance(shots, list):
        return []
    findings: list[ConsistencyFinding] = []
    for shot in shots:
        if not isinstance(shot, dict):
            continue
        frame: Path | None = None
        assets = shot.get("generated_assets")
        if isinstance(assets, dict):
            last = assets.get("storyboard_last_image")
            if isinstance(last, str) and last.strip():
                candidate = project_path / last
                if candidate.is_file():
                    frame = candidate
            if frame is None:
                clip = assets.get("video_clip")
                if isinstance(clip, str) and clip.strip():
                    # 无尾帧时不做视觉层（避免在 critique 同步路径里跑 ffmpeg）
                    pass
        findings.append(
            critique_ad_shot(
                project=project,
                project_path=project_path,
                shot=shot,
                frame_path=frame,
                threshold=threshold,
            )
        )
    return findings
