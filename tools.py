"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re
import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings


# ── Helper: Size Matching ──────────────────────────────────────────────────────

def _matches_size(target_size: str | None, listing_size: str | None) -> bool:
    """
    Check if a listing's size matches the user's requested size case-insensitively.
    Handles composite sizes (e.g. 'S/M' matches 'M' or 'S', 'US 8' matches '8' or 'US 8',
    'XL (oversized)' matches 'XL', 'W30 L30' matches 'W30').
    Avoids false positives like 's' in 'us 9' or 'l' in 'xl'.
    """
    if not target_size:
        return True
    if not listing_size:
        return False

    target = target_size.strip().lower()
    listing = listing_size.strip().lower()

    if target == listing:
        return True

    # Tokenize listing size by splitting on whitespace, slashes, parentheses, commas
    listing_tokens = [t.strip() for t in re.split(r'[/(),\s]+', listing) if t.strip()]
    if target in listing_tokens:
        return True

    target_tokens = [t.strip() for t in re.split(r'[/(),\s]+', target) if t.strip()]
    if target_tokens and all(t in listing_tokens for t in target_tokens):
        return True

    return False


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    if not description or not description.strip():
        return []

    listings = load_listings()
    matches: list[tuple[int, dict]] = []

    # Extract clean alphanumeric keywords from query description
    raw_tokens = re.findall(r'\b[a-zA-Z0-9]+\b', description.lower())
    stopwords = {
        "a", "an", "the", "in", "on", "for", "with", "of", "and", "or",
        "to", "at", "by", "is", "it", "under", "size", "want", "looking"
    }
    keywords = [kw for kw in raw_tokens if kw not in stopwords]
    if not keywords:
        keywords = raw_tokens
    if not keywords:
        return []

    desc_lower = description.strip().lower()

    for item in listings:
        # 1. Filter by max_price (inclusive)
        if max_price is not None:
            price = item.get("price")
            if price is None or float(price) > float(max_price):
                continue

        # 2. Filter by size
        if size is not None:
            if not _matches_size(size, item.get("size", "")):
                continue

        # 3. Score relevance based on keyword and phrase overlap
        score = 0
        title_lower = (item.get("title") or "").lower()
        item_desc_lower = (item.get("description") or "").lower()
        category_lower = (item.get("category") or "").lower()
        brand_lower = (item.get("brand") or "").lower()
        colors = [c.lower() for c in item.get("colors", [])]
        style_tags = [t.lower() for t in item.get("style_tags", [])]

        # Exact phrase match bonuses
        if desc_lower in title_lower:
            score += 15
        elif desc_lower in item_desc_lower:
            score += 8

        # Keyword matching across relevant fields
        for kw in keywords:
            if kw in title_lower:
                score += 5
            if any(kw == tag or kw in tag for tag in style_tags):
                score += 4
            if brand_lower and kw in brand_lower:
                score += 4
            if kw == category_lower:
                score += 3
            if any(kw == col for col in colors):
                score += 2
            if kw in item_desc_lower:
                score += 1

        # 4. Drop anything scoring zero
        if score > 0:
            matches.append((score, item))

    if not matches:
        return []

    # 5. Sort by score descending, breaking ties with price ascending
    matches.sort(key=lambda pair: (-pair[0], pair[1].get("price", 0)))

    limit = getattr(config, "SEARCH_RESULT_LIMIT", 10)
    return [item for _, item in matches[:limit]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    if not new_item:
        return "No clothing item was provided to style."

    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []

    title = new_item.get("title", "thrifted find")
    category = new_item.get("category", "")
    price = f"${new_item.get('price', 0):.2f}"
    platform = new_item.get("platform", "")
    colors = ", ".join(new_item.get("colors", [])) or "not specified"
    tags = ", ".join(new_item.get("style_tags", [])) or "vintage / streetwear"
    desc = new_item.get("description", "")
    brand = new_item.get("brand") or "Unbranded"

    if not wardrobe_items:
        prompt = (
            f"You are a personal fashion stylist for FitFindr.\n\n"
            f"The user is considering purchasing this thrifted find:\n"
            f"- Title: {title}\n"
            f"- Category: {category}\n"
            f"- Price: {price} on {platform}\n"
            f"- Brand: {brand}\n"
            f"- Colors: {colors}\n"
            f"- Style tags: {tags}\n"
            f"- Description: {desc}\n\n"
            f"The user currently has no clothing items saved in their wardrobe profile.\n"
            f"Provide general styling advice with 1-2 versatile outfit ideas explaining how to "
            f"wear and style this item using classic everyday wardrobe essentials, complementary "
            f"colors, silhouettes, and layering pieces."
        )
    else:
        wardrobe_lines = []
        for i, item in enumerate(wardrobe_items, 1):
            name = item.get("name", "Item")
            cat = item.get("category", "")
            col = item.get("color", "")
            sty = item.get("style", "")
            wardrobe_lines.append(f"{i}. {name} (Category: {cat}, Color: {col}, Style: {sty})")
        wardrobe_text = "\n".join(wardrobe_lines)

        prompt = (
            f"You are a personal fashion stylist for FitFindr.\n\n"
            f"The user is considering purchasing this thrifted find:\n"
            f"- Title: {title}\n"
            f"- Category: {category}\n"
            f"- Price: {price} on {platform}\n"
            f"- Brand: {brand}\n"
            f"- Colors: {colors}\n"
            f"- Style tags: {tags}\n"
            f"- Description: {desc}\n\n"
            f"The user currently owns these items in their wardrobe:\n"
            f"{wardrobe_text}\n\n"
            f"Suggest 1-2 complete outfits incorporating the new thrifted item with specific pieces "
            f"they already own from their wardrobe list. Explicitly name the owned items in your "
            f"recommendations and explain why they work well together."
        )

    system_instruction = (
        "You are FitFindr's knowledgeable and enthusiastic fashion stylist. "
        "Recommend stylish, cohesive outfits with clear pairings and aesthetic advice."
    )

    response = generate(prompt, system=system_instruction)
    return response.strip() if response else "Pair this versatile item with classic wardrobe staples."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "Cannot create a fit card: no outfit suggestion was provided."
    if not new_item:
        return "Cannot create a fit card: no item details were provided."

    title = new_item.get("title", "thrifted find")
    price = f"${new_item.get('price', 0):.2f}"
    platform = new_item.get("platform", "thrift app")
    colors = ", ".join(new_item.get("colors", [])) or "vintage palette"
    desc = new_item.get("description", "")
    tags = ", ".join(new_item.get("style_tags", [])) or "thrifted"
    brand = new_item.get("brand") or "vintage"

    prompt = (
        f"Write a social media fit card caption about this thrift find.\n\n"
        f"Item Details:\n"
        f"- Item: {title}\n"
        f"- Brand: {brand}\n"
        f"- Price: {price}\n"
        f"- Platform: {platform}\n"
        f"- Colors: {colors}\n"
        f"- Description: {desc}\n"
        f"- Style tags: {tags}\n\n"
        f"Outfit Styling:\n"
        f"{outfit.strip()}\n\n"
        f"Mandatory Guidelines:\n"
        f"1. Length: Exactly 2 to 4 sentences.\n"
        f"2. Hook & Phrasing: Must open with an original, varied hook tailored to the specific piece. "
        f"Do NOT use generic cliché openers like 'Channel your inner...', 'Stop scrolling...', or 'The holy grail...'. "
        f"Vary sentence structure (e.g., start with a bold observation, a sensory detail, or an unexpected styling take).\n"
        f"3. Descriptive Detail: Must highlight at least one specific descriptive trait of the item "
        f"(its color, texture, pattern, material, or unique visual feature).\n"
        f"4. Key Facts: Mention the item, its price ({price}), and the platform ({platform}) once each.\n"
        f"5. Vibe: Write in a trendy, authentic social media voice suitable for a fit post on Instagram or TikTok."
    )

    system_instruction = (
        "You are an expert social media copywriter for thrift fashion. Write concise, catchy 2-4 sentence "
        "captions featuring a strong opening hook and vivid descriptive details about clothing items."
    )

    response = generate(prompt, system=system_instruction)
    return response.strip() if response else (
        f"Obsessed with this thrift find! Snagged this {title} for {price} on {platform}, "
        f"featuring an iconic {colors} look that pairs effortlessly: {outfit}"
    )
