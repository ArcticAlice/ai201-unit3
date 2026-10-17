"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re
import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


def _parse_query(query: str) -> dict:
    """
    Parse a natural language query into description, size, and max_price using regex.
    """
    cleaned = query.strip()
    max_price = None
    size = None

    # Match price constraints: e.g., 'under $30', 'under 30', 'below $40', '$30'
    price_pattern = r'(?:under|below|less than|max(?:imum)?|budget(?:\s*of)?)\s*\$?\s*(\d+(?:\.\d+)?)|(?:\$)\s*(\d+(?:\.\d+)?)'
    price_match = re.search(price_pattern, cleaned, re.IGNORECASE)
    if price_match:
        price_val = price_match.group(1) or price_match.group(2)
        try:
            max_price = float(price_val)
            cleaned = cleaned[:price_match.start()] + " " + cleaned[price_match.end():]
        except (ValueError, TypeError):
            pass

    # Match size constraints: e.g., 'in size M', 'size M', 'size: 8', 'size XXS', 'size S/M'
    size_pattern = r'\b(?:in\s+)?size[:\s]+([A-Za-z0-9/]+)\b'
    size_match = re.search(size_pattern, cleaned, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).strip()
        cleaned = cleaned[:size_match.start()] + " " + cleaned[size_match.end():]

    # Clean description: strip conversational prefixes, commas, and trailing prepositions
    cleaned = re.sub(r'^(?:looking for (?:a|an)?|find (?:me (?:a|an)?)?|i want (?:a|an)?)\s+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[,;]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'\b(in|under|for|with)\b\s*$', '', cleaned, flags=re.IGNORECASE).strip()

    description = cleaned if cleaned else query.strip()

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.
    """
    # 1. Start a fresh session
    session = new_session(query, wardrobe)

    # 2. Check iteration limit / stop condition guard
    iteration = 1
    trace.check_iterations(iteration)

    # 3. Parse query into description, size, and max_price
    session["parsed"] = _parse_query(query)
    parsed = session["parsed"]

    # 4. Call search_listings with parsed parameters
    session["search_results"] = search_listings(
        description=parsed.get("description", ""),
        size=parsed.get("size"),
        max_price=parsed.get("max_price"),
    )

    # Branch: If search returns empty, stop early with an actionable message
    if not session["search_results"]:
        suggestions = []
        if parsed.get("max_price") is not None:
            suggestions.append(f"raising your price ceiling (currently ${parsed['max_price']:.2f})")
        if parsed.get("size"):
            suggestions.append(f"checking alternative sizes (currently {parsed['size']})")
        suggestions.append("using broader search keywords or fewer filters")

        session["error"] = (
            f"No matching listings found for '{parsed.get('description', query)}'. "
            f"Try {' or '.join(suggestions)}."
        )
        return session

    # 5. Choose an item from search results (first match)
    session["selected_item"] = session["search_results"][0]

    # 6. Call suggest_outfit with selected item and wardrobe
    try:
        session["outfit_suggestion"] = suggest_outfit(
            new_item=session["selected_item"],
            wardrobe=session["wardrobe"],
        )
    except ModelUnavailable as exc:
        session["error"] = f"Model unavailable while suggesting outfit: {exc}"
        return session

    # 7. Call create_fit_card with outfit suggestion and selected item
    try:
        session["fit_card"] = create_fit_card(
            outfit=session["outfit_suggestion"],
            new_item=session["selected_item"],
        )
    except ModelUnavailable as exc:
        session["error"] = f"Model unavailable while creating fit card: {exc}"
        return session

    # 8. Return completed session
    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
