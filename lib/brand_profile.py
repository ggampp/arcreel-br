"""广告/短片项目的 BrandProfile：品牌视觉与语气的结构化真源。

``project.json`` 顶层 ``brand_profile`` 仅 ``content_mode=ad`` 持有。字段：

- visual_description: 产品/品牌外观刚性描述（材质、颜色、形态、logo）
- tone_of_voice: 语气
- target_audience: 目标受众
- brand_colors: 品牌色列表
- style_keywords: 风格关键词
- style_prefix: 注入全部分镜/视频 prompt 的全局前缀（可手填；空时可由其它字段派生）

与产品资产上的自由文本 ``brand`` 字段不同：后者是单产品标签，本对象是项目级
「Brand Analyzer」产出，驱动全片一致性。
"""

from __future__ import annotations

from typing import Any

# 字符串字段：缺省空串；列表字段：缺省空列表
BRAND_PROFILE_STRING_FIELDS: tuple[str, ...] = (
    "visual_description",
    "tone_of_voice",
    "target_audience",
    "style_prefix",
)
BRAND_PROFILE_LIST_FIELDS: tuple[str, ...] = (
    "brand_colors",
    "style_keywords",
)

EMPTY_BRAND_PROFILE: dict[str, Any] = {
    "visual_description": "",
    "tone_of_voice": "",
    "target_audience": "",
    "brand_colors": [],
    "style_keywords": [],
    "style_prefix": "",
}


def empty_brand_profile() -> dict[str, Any]:
    """返回一份独立的空 BrandProfile（调用方可安全就地修改）。"""
    return {
        "visual_description": "",
        "tone_of_voice": "",
        "target_audience": "",
        "brand_colors": [],
        "style_keywords": [],
        "style_prefix": "",
    }


def normalize_brand_profile(raw: object) -> dict[str, Any]:
    """把任意输入归一化为完整 BrandProfile 对象；非法类型按空值降级。

    不抛异常——供读路径与 prompt 构建使用。写路径请用 ``validate_brand_profile``。
    """
    out = empty_brand_profile()
    if not isinstance(raw, dict):
        return out
    for key in BRAND_PROFILE_STRING_FIELDS:
        val = raw.get(key)
        if isinstance(val, str):
            out[key] = val
    for key in BRAND_PROFILE_LIST_FIELDS:
        val = raw.get(key)
        if isinstance(val, list):
            out[key] = [str(x) for x in val if isinstance(x, str) and x.strip()]
    return out


def validate_brand_profile(raw: object) -> list[str]:
    """校验 BrandProfile 形状；返回错误列表（空 = 合法）。"""
    errors: list[str] = []
    if raw is None:
        return errors
    if not isinstance(raw, dict):
        return ["brand_profile 必须是对象"]
    for key in BRAND_PROFILE_STRING_FIELDS:
        if key in raw and raw[key] is not None and not isinstance(raw[key], str):
            errors.append(f"brand_profile.{key} 必须是字符串")
    for key in BRAND_PROFILE_LIST_FIELDS:
        if key not in raw or raw[key] is None:
            continue
        val = raw[key]
        if not isinstance(val, list):
            errors.append(f"brand_profile.{key} 必须是字符串列表")
            continue
        for i, item in enumerate(val):
            if not isinstance(item, str):
                errors.append(f"brand_profile.{key}[{i}] 必须是字符串")
    # 未知键仅警告式忽略，不报错——便于向前兼容
    return errors


def merge_brand_profile(existing: object, patch: object) -> dict[str, Any]:
    """merge 语义更新 BrandProfile：只改 patch 中出现的键。"""
    base = normalize_brand_profile(existing)
    if not isinstance(patch, dict):
        raise ValueError("brand_profile patch 必须是对象")
    errors = validate_brand_profile(patch)
    if errors:
        raise ValueError("; ".join(errors))
    for key in BRAND_PROFILE_STRING_FIELDS:
        if key in patch:
            val = patch[key]
            base[key] = val if isinstance(val, str) else ""
    for key in BRAND_PROFILE_LIST_FIELDS:
        if key in patch:
            val = patch[key]
            if val is None:
                base[key] = []
            elif isinstance(val, list):
                base[key] = [str(x) for x in val if isinstance(x, str)]
            else:
                raise ValueError(f"brand_profile.{key} 必须是字符串列表")
    return base


def derive_style_prefix(profile: dict[str, Any]) -> str:
    """从 BrandProfile 派生可注入 prompt 的 style_prefix。

    优先使用显式 ``style_prefix``；为空时拼接 visual_description / keywords / colors / tone。
    """
    p = normalize_brand_profile(profile)
    explicit = (p.get("style_prefix") or "").strip()
    if explicit:
        return explicit

    parts: list[str] = []
    visual = (p.get("visual_description") or "").strip()
    if visual:
        parts.append(f"产品/品牌外观：{visual}")
    keywords = p.get("style_keywords") or []
    if keywords:
        parts.append("风格关键词：" + "、".join(keywords))
    colors = p.get("brand_colors") or []
    if colors:
        parts.append("品牌色：" + "、".join(colors))
    tone = (p.get("tone_of_voice") or "").strip()
    if tone:
        parts.append(f"语气：{tone}")
    audience = (p.get("target_audience") or "").strip()
    if audience:
        parts.append(f"目标受众：{audience}")
    return "\n".join(parts)


def format_brand_profile_block(profile: object) -> str:
    """渲染进剧本/agent prompt 的 <brand_profile> 块正文。"""
    p = normalize_brand_profile(profile)
    if not any(
        [
            (p.get("visual_description") or "").strip(),
            (p.get("tone_of_voice") or "").strip(),
            (p.get("target_audience") or "").strip(),
            p.get("brand_colors"),
            p.get("style_keywords"),
            (p.get("style_prefix") or "").strip(),
        ]
    ):
        return "（未填写；可从产品图与 brief 由 Brand Analyzer 起草后经 patch_project 写入）"

    lines: list[str] = []
    if p.get("visual_description"):
        lines.append(f"外观描述：{p['visual_description']}")
    if p.get("tone_of_voice"):
        lines.append(f"语气：{p['tone_of_voice']}")
    if p.get("target_audience"):
        lines.append(f"目标受众：{p['target_audience']}")
    if p.get("brand_colors"):
        lines.append("品牌色：" + "、".join(p["brand_colors"]))
    if p.get("style_keywords"):
        lines.append("风格关键词：" + "、".join(p["style_keywords"]))
    prefix = derive_style_prefix(p)
    if prefix:
        lines.append(f"style_prefix（注入全片）：\n{prefix}")
    return "\n".join(lines)


def brand_style_prompt_prefix(project: dict[str, Any]) -> str:
    """供分镜/视频生成前缀：非 ad 或空 profile 返回空串；否则带换行后缀。"""
    if project.get("content_mode") != "ad":
        return ""
    prefix = derive_style_prefix(project.get("brand_profile"))
    if not prefix:
        return ""
    return f"{prefix}\n\n"


def build_brand_analyzer_prompt(
    *,
    brief: str,
    products: dict[str, Any],
    style: str = "",
    style_description: str = "",
) -> str:
    """给 Brand Analyzer（agent 或 text 生成）的结构化起草指令。

    输出约定为 JSON 对象，键与 BrandProfile 字段一致。
    """
    product_lines: list[str] = []
    for name, data in (products or {}).items():
        if not isinstance(data, dict):
            product_lines.append(f"- {name}")
            continue
        bits = [f"- {name}"]
        if data.get("description"):
            bits.append(f"  描述：{data['description']}")
        if data.get("brand"):
            bits.append(f"  品牌标签：{data['brand']}")
        sps = data.get("selling_points")
        if isinstance(sps, list) and sps:
            bits.append("  卖点：" + "；".join(str(s) for s in sps if s))
        product_lines.append("\n".join(bits))

    return f"""你是广告品牌分析师（Brand Analyzer）。根据创作 brief、产品信息与画风，产出一份 JSON BrandProfile，
用于保证多镜头广告中产品外观与品牌语气的一致性。

要求：
1. 只输出一个 JSON 对象，不要 markdown 围栏。
2. 字段：visual_description（字符串，刚性外观描述）、tone_of_voice、target_audience、
   brand_colors（字符串数组）、style_keywords（字符串数组）、style_prefix（字符串，
   将原样注入后续每个镜头的图像/视频 prompt，须简洁、可复用、含产品外观要点）。
3. visual_description 与 style_prefix 必须足够具体（材质、主色、形态、logo/包装文字若已知则写明），避免空泛形容词。
4. 不夸大功效；信息不足处写「未提供」而非臆造。

<brief>
{brief or "（未提供）"}
</brief>

<style>
风格：{style or "（未指定）"}
描述：{style_description or "（未指定）"}
</style>

<products>
{chr(10).join(product_lines) if product_lines else "（无产品资产）"}
</products>
"""
