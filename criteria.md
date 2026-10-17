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
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->

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
possible but it would make the caption sound weird.c


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
