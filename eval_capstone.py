"""
Comprehensive evaluation runner for Capstone Acceptance Criteria (Milestone 5).
Executes 3 independent trials for each of the 5 criteria, recording precise scores
and raw outputs.
"""

import json
import time
from pathlib import Path
from occasion_stylist import style_for_occasion
from agent import run_agent
from utils.data_loader import get_example_wardrobe, load_wardrobe_schema

wardrobe = get_example_wardrobe()
valid_ids = {it["id"] for it in wardrobe["items"]}
valid_items_map = {it["id"]: it for it in wardrobe["items"]}

c1_occasions = [
    "casual Sunday brunch with friends",
    "chilly evening study session at the library",
    "informal streetwear art gallery opening",
    "minimalist coffee date",
    "rainy day walking around downtown",
]

c3_impossible_occasions = [
    "formal black-tie presidential gala dinner",
    "deep sea scuba diving coral reef expedition",
    "Olympic fencing championship tournament duel",
    "black-tie white-shoe charity ball",
    "swimming competition finals at the aquatic center",
]

c5_queries = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "silk slip dress in midi length under $40",
    "platform sneakers size 8",
    "denim jacket under $50",
]


def evaluate_criterion_1(trial_num: int) -> tuple[int, int, list[str]]:
    """Test Criterion 1: Multi-piece coordination & strict wardrobe grounding."""
    passed = 0
    logs = []
    for occ in c1_occasions:
        res = style_for_occasion(occ, wardrobe)
        ids = res.get("selected_ids", [])
        cats = res.get("selected_categories", [])
        # Check: 100% IDs valid, at least 3 categories, status == success
        all_valid = len(ids) >= 3 and all(i in valid_ids for i in ids)
        has_3_cats = len(set(cats)) >= 3
        is_pass = all_valid and has_3_cats and (res.get("status") == "success")
        if is_pass:
            passed += 1
        logs.append(f"Occasion: '{occ}' -> IDs: {ids}, Cats: {cats}, Pass: {is_pass}")
    return passed, len(c1_occasions), logs


def evaluate_criterion_2(trial_num: int) -> tuple[int, int, list[str]]:
    """Test Criterion 2: Grounded attribute-driven justification."""
    passed = 0
    logs = []
    for occ in c1_occasions:
        res = style_for_occasion(occ, wardrobe)
        explanation = (res.get("explanation") or "").lower()
        selected_ids = res.get("selected_ids", [])

        # Check if explanation references metadata for EVERY selected item
        items_grounded = 0
        for iid in selected_ids:
            it = valid_items_map.get(iid, {})
            # Look for color, tag, or note tokens
            colors = [c.lower() for c in it.get("colors", [])]
            tags = [t.lower() for t in it.get("style_tags", [])]
            name = it.get("name", "").lower()
            
            grounded = False
            if any(col in explanation for col in colors):
                grounded = True
            elif any(tag in explanation for tag in tags):
                grounded = True
            elif it.get("notes") and any(w in explanation for w in it["notes"].lower().split() if len(w) > 4):
                grounded = True
            
            if grounded:
                items_grounded += 1

        is_pass = (items_grounded == len(selected_ids)) and len(selected_ids) >= 3
        if is_pass:
            passed += 1
        logs.append(f"Occasion: '{occ}' -> Grounded: {items_grounded}/{len(selected_ids)} items, Pass: {is_pass}")
    return passed, len(c1_occasions), logs


def evaluate_criterion_3(trial_num: int) -> tuple[int, int, list[str]]:
    """Test Criterion 3: Incompatible wardrobe gap detection (Bad path)."""
    passed = 0
    logs = []
    for occ in c3_impossible_occasions:
        res = style_for_occasion(occ, wardrobe)
        is_incompatible = res.get("status") == "incompatible"
        has_warning_or_missing = bool(res.get("warning") or res.get("missing_garments"))
        no_hallucinated_outfit = len(res.get("selected_ids", [])) == 0
        is_pass = is_incompatible and has_warning_or_missing and no_hallucinated_outfit
        if is_pass:
            passed += 1
        logs.append(f"Occasion: '{occ[:30]}' -> Status: {res.get('status')}, Missing: {res.get('missing_garments')}, Pass: {is_pass}")
    return passed, len(c3_impossible_occasions), logs


def evaluate_criterion_4(trial_num: int) -> tuple[int, int, list[str]]:
    """Test Criterion 4: Execution latency & structured observability benchmark."""
    passed = 0
    logs = []
    for occ in c1_occasions:
        res = style_for_occasion(occ, wardrobe)
        duration = res.get("duration_sec", 99.0)
        has_tokens = res.get("tokens_used", {}).get("total", 0) > 0
        is_pass = (duration < 2.5) and has_tokens
        if is_pass:
            passed += 1
        logs.append(f"Occasion: '{occ}' -> Duration: {duration}s, Tokens: {res.get('tokens_used', {}).get('total')}, Pass: {is_pass}")
    return passed, len(c1_occasions), logs


def evaluate_criterion_5(trial_num: int) -> tuple[int, int, list[str]]:
    """Test Criterion 5: Regression safety on original FitFindr loop."""
    passed = 0
    logs = []
    for q in c5_queries:
        session = run_agent(q, wardrobe)
        has_no_error = session.get("error") is None
        has_fit_card = bool(session.get("fit_card"))
        has_outfit = bool(session.get("outfit_suggestion"))
        is_pass = has_no_error and has_fit_card and has_outfit
        if is_pass:
            passed += 1
        logs.append(f"Query: '{q}' -> Error: {session.get('error')}, Fit Card: {bool(session.get('fit_card'))}, Pass: {is_pass}")
    return passed, len(c5_queries), logs


def run_full_eval():
    results = {}
    detailed_outputs = {}

    eval_funcs = [
        ("1. Strict Wardrobe Grounding", evaluate_criterion_1, "5 of 5"),
        ("2. Grounded Attribute Justification", evaluate_criterion_2, "4 of 5"),
        ("3. Incompatible Wardrobe Gap Detection", evaluate_criterion_3, "5 of 5"),
        ("4. Latency & Observability (< 2.5s)", evaluate_criterion_4, "4 of 5"),
        ("5. Regression Safety on FitFindr", evaluate_criterion_5, "5 of 5"),
    ]

    for name, fn, target in eval_funcs:
        print(f"\nEvaluating: {name} (Target: {target})")
        trial_scores = []
        logs_list = []
        for trial in range(1, 4):
            print(f"  Running Trial {trial}...")
            score, total, logs = fn(trial)
            trial_scores.append(f"{score}/{total}")
            logs_list.append((trial, logs))
        results[name] = trial_scores
        detailed_outputs[name] = logs_list

    print("\n" + "=" * 60)
    print("EVALUATION RUN LOG — SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Criterion':<40} | {'Target':<7} | {'Run 1':<6} | {'Run 2':<6} | {'Run 3':<6} | {'Verdict'}")
    print("-" * 80)
    for name, fn, target in eval_funcs:
        scores = results[name]
        # Verdict: check if all runs met target
        # e.g. "5 of 5" -> requires 5/5 on all runs
        target_num = int(target.split()[0])
        all_met = all(int(s.split("/")[0]) >= target_num for s in scores)
        verdict = "MET" if all_met else "MISSED"
        print(f"{name:<40} | {target:<7} | {scores[0]:<6} | {scores[1]:<6} | {scores[2]:<6} | {verdict}")

    # Save details
    with open("results/eval_run_after.json", "w") as f:
        json.dump({"results": results, "details": detailed_outputs}, f, indent=2)


if __name__ == "__main__":
    run_full_eval()
