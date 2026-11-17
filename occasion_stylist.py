"""
Wardrobe-Aware Occasion Stylist for FitFindr (Unit 9 Capstone Extension).

Given a user's existing wardrobe (stored in a JSON schema) and a specific occasion,
this module evaluates formality and functional demands, verifies wardrobe feasibility,
and selects a cohesive outfit strictly composed of items the user already owns.
"""

import json
import re
import time
from typing import Optional
from generate import generate, token_counts, ModelUnavailable
from logger import log_run


def evaluate_occasion_compatibility(occasion: str, wardrobe_items: list[dict]) -> tuple[bool, str, list[str]]:
    """
    Fast pre-filter heuristic to check whether the occasion has known extreme dress-code
    mismatches with the current wardrobe inventory.

    Returns (is_compatible, reason, missing_types)
    """
    occ_lower = occasion.lower()
    
    # Check if wardrobe contains any formal or black-tie items
    has_formal = any(
        "formal" in item.get("style_tags", []) or "formal" in (item.get("notes") or "").lower()
        for item in wardrobe_items
    )
    # Check if wardrobe contains swimwear / skiwear / specialized gear
    has_swim = any("swim" in (item.get("category") or "").lower() for item in wardrobe_items)
    has_snow = any("snow" in " ".join(item.get("style_tags", [])).lower() for item in wardrobe_items)

    formal_triggers = ["black tie", "black-tie", "gala", "white tie", "formal ball", "tuxedo"]
    if any(t in occ_lower for t in formal_triggers) and not has_formal:
        return (
            False,
            f"The occasion '{occasion}' requires strict formal/black-tie attire, but your current wardrobe only contains casual, streetwear, and everyday basics.",
            ["formal gown", "tuxedo", "dress shoes", "formal eveningwear"]
        )

    swim_triggers = ["swimming", "swim meet", "pool party swim", "scuba diving", "triathlon swim"]
    if any(t in occ_lower for t in swim_triggers) and not has_swim:
        return (
            False,
            f"The occasion '{occasion}' requires swimwear or aquatic apparel, which is not present in your wardrobe.",
            ["swimsuit", "swim trunks", "water shoes"]
        )

    snow_triggers = ["sub-zero mountaineering", "snowboarding in blizzard", "deep alpine skiing"]
    if any(t in occ_lower for t in snow_triggers) and not has_snow:
        return (
            False,
            f"The occasion '{occasion}' requires specialized heavy alpine/snow insulation gear, which is not present in your wardrobe.",
            ["insulated ski pants", "alpine parka", "snow boots"]
        )

    return (True, "", [])


def _finalize(result: dict, start_time: float, tokens_before: dict, wardrobe_count: int) -> dict:
    """Finalize metrics and write structured log record."""
    duration = round(time.monotonic() - start_time, 4)
    tokens_after = token_counts()
    tokens_diff = {
        "prompt": max(0, tokens_after["prompt"] - tokens_before["prompt"]),
        "output": max(0, tokens_after["output"] - tokens_before["output"]),
        "total": max(0, tokens_after["total"] - tokens_before["total"]),
    }
    result["duration_sec"] = duration
    result["tokens_used"] = tokens_diff

    # Write to structured log
    log_run(
        action="occasion_styling",
        inputs={
            "occasion": result.get("occasion"),
            "wardrobe_item_count": wardrobe_count,
        },
        outputs={
            "selected_ids": result.get("selected_ids", []),
            "selected_categories": result.get("selected_categories", []),
            "missing_garments": result.get("missing_garments", []),
        },
        duration_sec=duration,
        tokens=tokens_diff,
        status=result["status"],
        error_or_warning=result.get("warning") or (result["explanation"] if result["status"] != "success" else None),
    )
    return result


def style_for_occasion(occasion: str, wardrobe: dict) -> dict:
    """
    Given an occasion string and a wardrobe dict, return a recommended outfit
    composed strictly of items the user owns, or a structured refusal if incompatible.

    Returns a dict:
        status: "success" | "incompatible" | "error"
        occasion: str
        selected_items: list[dict]
        selected_ids: list[str]
        selected_categories: list[str]
        explanation: str
        duration_sec: float
        tokens_used: dict (prompt, output, total)
        warning: Optional[str]
        missing_garments: list[str]
    """
    start_time = time.monotonic()
    tokens_before = token_counts()

    result = {
        "status": "error",
        "occasion": occasion,
        "selected_items": [],
        "selected_ids": [],
        "selected_categories": [],
        "explanation": "",
        "duration_sec": 0.0,
        "tokens_used": {"prompt": 0, "output": 0, "total": 0},
        "warning": None,
        "missing_garments": []
    }

    cleaned_occ = (occasion or "").strip()
    items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
    wardrobe_count = len(items)

    if not cleaned_occ:
        result["warning"] = "No occasion was specified. Please provide an occasion (e.g. 'casual brunch', 'tech interview')."
        return _finalize(result, start_time, tokens_before, wardrobe_count)

    if not items:
        result["status"] = "incompatible"
        result["warning"] = "Wardrobe is empty. Cannot assemble an outfit without items."
        return _finalize(result, start_time, tokens_before, wardrobe_count)

    # 1. Deterministic compatibility pre-check for extreme edge cases
    is_compat, reason, missing = evaluate_occasion_compatibility(cleaned_occ, items)
    if not is_compat:
        result["status"] = "incompatible"
        result["warning"] = reason
        result["missing_garments"] = missing
        return _finalize(result, start_time, tokens_before, wardrobe_count)

    # 2. Prepare wardrobe inventory representation
    item_map = {it.get("id"): it for it in items if it.get("id")}
    wardrobe_catalog_lines = []
    for it in items:
        item_id = it.get("id", "unknown")
        name = it.get("name", "Unnamed")
        cat = it.get("category", "")
        cols = ", ".join(it.get("colors", []))
        tags = ", ".join(it.get("style_tags", []))
        notes = it.get("notes") or "none"
        wardrobe_catalog_lines.append(
            f"- [{item_id}] {name} | Category: {cat} | Colors: {cols} | Style Tags: {tags} | Notes: {notes}"
        )
    wardrobe_text = "\n".join(wardrobe_catalog_lines)

    system_instruction = (
        "You are FitFindr's expert Wardrobe Stylist. Your task is to recommend a complete outfit "
        "for a specific occasion using ONLY the items in the user's wardrobe inventory.\n\n"
        "STRICT CONSTRAINTS:\n"
        "1. You MUST NEVER invent, assume, or hallucinate any item. Every piece you recommend MUST be chosen from the provided wardrobe list by its exact ID.\n"
        "2. A complete outfit MUST contain at least 3 distinct categories (e.g. top, bottom, shoes, and optionally outerwear or accessories).\n"
        "3. If the occasion's dress code or functional requirements fundamentally CANNOT be satisfied by the wardrobe (for example, formal eveningwear needed when only casual streetwear is available), you must declare compatibility as false and explain what is missing rather than suggesting an inappropriate outfit.\n"
        "4. In your explanation, you MUST explicitly cite specific attribute metadata from each selected item (such as its exact colors, style tags, or notes) to justify why that piece suits the occasion.\n"
        "5. You must output strictly valid JSON conforming to the requested schema, with no markdown code fences or conversational preamble."
    )

    user_prompt = (
        f"Occasion: {cleaned_occ}\n\n"
        f"Available Wardrobe Inventory:\n{wardrobe_text}\n\n"
        f"Respond in this JSON format:\n"
        f"{{\n"
        f'  "is_compatible": true or false,\n'
        f'  "missing_garments": ["list of missing clothing items if incompatible"],\n'
        f'  "selected_item_ids": ["w_...", "w_...", "w_..."],\n'
        f'  "explanation": "Detailed styling rationale citing each item\'s colors, style_tags, and notes and how they meet the occasion"\n'
        f"}}"
    )

    try:
        raw_response = generate(user_prompt, system=system_instruction, temperature=0.2)
    except ModelUnavailable as exc:
        result["status"] = "error"
        result["warning"] = f"Model unavailable: {exc}"
        return _finalize(result, start_time, tokens_before, wardrobe_count)

    # 3. Parse JSON response
    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
            clean_json = re.sub(r"\s*```$", "", clean_json)
        parsed = json.loads(clean_json)
    except Exception:
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except Exception as parse_err:
                result["status"] = "error"
                result["warning"] = f"Failed to parse model JSON: {parse_err}. Raw: {raw_response[:100]}"
                return _finalize(result, start_time, tokens_before, wardrobe_count)
        else:
            result["status"] = "error"
            result["warning"] = f"Model did not return valid JSON. Raw: {raw_response[:100]}"
            return _finalize(result, start_time, tokens_before, wardrobe_count)

    # 4. Check compatibility flag from model
    if not parsed.get("is_compatible", True):
        result["status"] = "incompatible"
        result["warning"] = parsed.get("explanation") or f"Wardrobe cannot support occasion '{cleaned_occ}'."
        result["missing_garments"] = parsed.get("missing_garments", [])
        result["explanation"] = parsed.get("explanation", "")
        return _finalize(result, start_time, tokens_before, wardrobe_count)

    # 5. Validate selected items against wardrobe strictly (Zero Hallucination Guard)
    candidate_ids = parsed.get("selected_item_ids", [])
    valid_selected = []
    seen_categories = set()

    for cid in candidate_ids:
        if cid in item_map:
            it = item_map[cid]
            valid_selected.append(it)
            if it.get("category"):
                seen_categories.add(it.get("category"))

    result["selected_items"] = valid_selected
    result["selected_ids"] = [it["id"] for it in valid_selected]
    result["selected_categories"] = list(seen_categories)
    result["explanation"] = parsed.get("explanation", "")

    if len(result["selected_ids"]) >= 2 and len(seen_categories) >= 2:
        result["status"] = "success"
    else:
        result["status"] = "incompatible"
        result["warning"] = f"Model was unable to assemble a complete outfit (found {len(seen_categories)} categories)."

    return _finalize(result, start_time, tokens_before, wardrobe_count)
