"""SDK MCP tools：广告产品一致性评审 + Brand Analyzer 起草辅助。"""

from __future__ import annotations

import json
from typing import Any

from claude_agent_sdk import tool

from lib.ad_consistency import critique_ad_script, critique_ad_shot
from lib.brand_profile import build_brand_analyzer_prompt
from lib.storyboard_sequence import get_storyboard_items
from server.agent_runtime.sdk_tools._context import ToolContext, tool_error, validate_script_filename


def critique_ad_consistency_tool(ctx: ToolContext):
    @tool(
        "critique_ad_consistency",
        "评审广告/短片项目的产品视觉一致性（Consistency Manager）。"
        "传入 script 剧本文件名；可选 shot_ids 限定镜头。"
        "返回每镜 score/passed/reasons/recommend_regen。"
        "对 recommend_regen=true 的镜头应重新 generate_video_*（可换 seed）。",
        {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "剧本文件名（如 episode_1.json）",
                },
                "shot_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "可选：仅评审这些 shot_id；不传则评审全部 shots",
                },
                "threshold": {
                    "type": "number",
                    "description": "通过阈值 0–1，默认 0.45",
                },
            },
            "required": ["script"],
        },
    )
    async def _handler(args: dict[str, Any]) -> dict[str, Any]:
        try:
            if ctx.pm.load_project(ctx.project_name).get("content_mode") != "ad":
                raise ValueError("critique_ad_consistency 仅适用于 content_mode=ad 项目")
            script_filename = validate_script_filename(args["script"])
            script = ctx.pm.load_script(ctx.project_name, script_filename)
            project = ctx.pm.load_project(ctx.project_name)
            project_path = ctx.project_path
            threshold = float(args["threshold"]) if args.get("threshold") is not None else 0.45
            shot_ids = args.get("shot_ids")
            wanted = {str(s) for s in shot_ids} if isinstance(shot_ids, list) else None

            items, id_field, *_ = get_storyboard_items(script)
            findings = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                sid = str(item.get(id_field) or "")
                if wanted is not None and sid not in wanted:
                    continue
                frame = None
                assets = item.get("generated_assets")
                if isinstance(assets, dict):
                    last = assets.get("storyboard_last_image")
                    if isinstance(last, str) and last.strip():
                        candidate = project_path / last
                        if candidate.is_file():
                            frame = candidate
                findings.append(
                    critique_ad_shot(
                        project=project,
                        project_path=project_path,
                        shot=item,
                        frame_path=frame,
                        threshold=threshold,
                    ).to_dict()
                )

            if not findings and wanted is None:
                # 回退：直接扫 shots
                findings = [
                    f.to_dict()
                    for f in critique_ad_script(
                        project=project,
                        project_path=project_path,
                        script=script,
                        threshold=threshold,
                    )
                ]

            failed = [f for f in findings if f.get("recommend_regen")]
            summary = {
                "total": len(findings),
                "passed": sum(1 for f in findings if f.get("passed")),
                "recommend_regen": [f["shot_id"] for f in failed],
                "findings": findings,
            }
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(summary, ensure_ascii=False, indent=2),
                    }
                ]
            }
        except Exception as exc:  # noqa: BLE001
            return tool_error("critique_ad_consistency", exc)

    return _handler


def brand_analyzer_prompt_tool(ctx: ToolContext):
    @tool(
        "brand_analyzer_prompt",
        "生成 Brand Analyzer 起草指令：基于当前 brief/products/style 产出可填入 "
        "project.brand_profile 的 JSON 字段说明。agent 应调用后据指令起草，"
        "经用户确认后用 patch_project settings.brand_profile 写入。",
        {
            "type": "object",
            "properties": {},
        },
    )
    async def _handler(args: dict[str, Any]) -> dict[str, Any]:
        try:
            del args  # 无参数
            project = ctx.pm.load_project(ctx.project_name)
            if project.get("content_mode") != "ad":
                raise ValueError("brand_analyzer_prompt 仅适用于 content_mode=ad 项目")
            prompt = build_brand_analyzer_prompt(
                brief=project.get("brief") or "",
                products=project.get("products") or {},
                style=project.get("style") or "",
                style_description=project.get("style_description") or "",
            )
            existing = project.get("brand_profile") or {}
            text = (
                prompt
                + "\n\n# 当前 brand_profile（可在此基础上修订）\n"
                + json.dumps(existing, ensure_ascii=False, indent=2)
                + "\n\n起草完成后：mcp__arcreel__patch_project settings="
                '{"brand_profile": { ... }}'
            )
            return {"content": [{"type": "text", "text": text}]}
        except Exception as exc:  # noqa: BLE001
            return tool_error("brand_analyzer_prompt", exc)

    return _handler
