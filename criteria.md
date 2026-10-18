# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**

I targeted 4 of 5 rather than 5 of 5 because `search_listings` relies on keyword overlap and regex extraction; certain user queries with uncommon slang, synonyms, or descriptive phrasings not mirrored in the mock dataset's `style_tags` or `description` fields may occasionally fail to match a listing.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**

A 5 of 5 target is appropriate because this path relies entirely on deterministic Python control flow (`if not session["search_results"]:`). Once search returns an empty list, the planning loop always branches immediately to set the error message and halts before invoking `suggest_outfit`, free from model non-determinism or network variance.

---

## 3. The selected item in session state matches what suggest_outfit receives

Given a query that returns at least one listing, the item stored in `session["selected_item"]` matches the top listing in `session["search_results"]` by `id` and title, and that exact item dictionary is passed into `suggest_outfit` as `new_item` — in 5 of 5 tries.

**Why this target:**

State management in the planning loop is deterministic Python code (`session["selected_item"] = session["search_results"][0]`), with no model variability or network instability. Any mismatch or mutation between what search found and what the next tool received indicates a structural bug in session handling, so it must succeed 5 of 5 tries.

---

## 4. A captions must include some descriptive factor on the clothing item

Given a clothing item an agent must include some information on one of the 
possible traits: color, texture, patterns, materials or a unique feature.
This must happen 5 out of 5 tries.

**Why this target:**

If the caption does include any descriptive information about the clothing
item then it is just a picture. There are no thoughts that go into. No
emotion and this would cause a reader to not be interested. So to create 
a caption the thresehold must be a perfect.

---

## 5. A caption must include a hook

Given a clothing item an agent must make a unique hook to grab a reader's
attention 4 out of 5 times.

**Why this target:**

This target is reasonable as it is not always possible to create a hook
for every clothing item. There may also be a scenario where a hook is 
possible but it would make the caption sound weird.

> **Revised in unit 4:** Across 5 runs on the same item, the 5 fit cards share no opening 4-word phrase.
>
> **Why revised:** "Unique hook" wasn't clearly checkable—each try had an attention-grabbing hook in isolation, but 4 of the 5 tries used the exact same template opener ("Channel your inner 90s icon with..."). The revision provides an objective, measurable standard for hook uniqueness and variety across generations.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
