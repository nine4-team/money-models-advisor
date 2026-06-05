# Diagnostic Flow

Walk this flow first. It identifies the constraint. Then route to the matching tree in [`decision-trees.md`](decision-trees.md) for prescription.

The coach should not skip to trees before the diagnostic is complete. A prescribed offer is only as good as the constraint it targets.

---

## Inputs Required

Before running the flow, confirm you have:

- **CAC** — fully-loaded cost to acquire one customer (ads + sales payroll + software + commissions)
- **First-sale price** and **first-sale gross profit** (price minus COGS)
- **Recurring revenue shape** (subscription? add-ons? one-and-done?)
- **Monthly recurring gross profit** (if applicable)
- **Monthly churn rate** (if applicable)
- **Current offer inventory** (what attraction / upsell / downsell / continuity mechanics are in place today, even informally)
- **Business shape** (service vs product, B2B vs B2C, ticket size, transformation-based vs transactional)

If any of these are missing and material, **ask for them before prescribing.** A diagnosis built on "I don't know" is not a diagnosis.

---

## Step 1 — Unit Economics

Compute or confirm:

- **Lifetime Gross Profit (LTGP)** = Lifetime Revenue × Gross Margin
- **LTGP : CAC ratio**

**Criterion:**
- `LTGP/CAC < 3:1` → business is **not viable** as structured. Don't prescribe offers yet — the math doesn't work. Surface this to the user and discuss whether price, COGS, or retention is broken. (`§1.2`, `§1.4`)
- `LTGP/CAC ≥ 3:1` → continue.

---

## Step 2 — Gross Margin Sanity Check

**Criterion (service business):** gross margin ≥ 80%. (`§1.4`)

- If below 80% on a service, the problem is pricing or COGS — fix that before adding money-model complexity. A great money model on a 20%-margin business (the Meals example in `§1.2.b`) still fails.
- If this is a product business with inherently lower margins, note the constraint and continue — the model will need to lean harder on upsells to compensate.

---

## Step 3 — CFA Level

Compute **30-day gross profit** from a single customer (across all offers stacked in the first 30 days).

**Criterion:**
- `30-day GP < CAC` → **Level 1 CFA.** Growth is capital-constrained. The acquisition model does not finance itself. (`§1.6`)
- `30-day GP ≥ CAC` → **Level 2 CFA.** Can scale on credit cards.
- `30-day GP ≥ 2 × CAC` → **Level 3 CFA.** Exponential growth unlocked.

**Target:** Level 3 if growth is the goal. Level 2 is the minimum for any business that wants to scale without outside capital.

---

## Step 4 — Payback Period

Compute: `PPD = (CAC - Month-1 GP) / Monthly Recurring GP`. (`§1.5`)

**Criterion:**
- PPD > 6 months → cash is the constraint, not the unit economics. Even if LTGP/CAC is strong, the business will be cash-starved. Focus prescription on **compressing payback** — upsells in first 30 days, first/last month upfront, initiation/enrollment fees.
- PPD ≤ 1 month → business is on the right side of CFA. Focus prescription on maximizing LTV and retention.

---

## Step 5 — Offer Inventory

Map the business against the four offer types. Note which are present (even informally) and which are missing.

| Offer type | Present? | What mechanic? | Objective |
|---|---|---|---|
| Attraction (`§3.*`) | | | Liquidate CAC |
| Upsell (`§4.*`) | | | Maximize profit |
| Downsell (`§5.*`) | | | Maximize conversion |
| Continuity (`§6.*`) | | | Stabilize cash flow |

**Rule:** A viable model rarely needs all four. Don't prescribe missing types just because they're absent — prescribe based on which constraint is actually biting.

---

## Step 6 — Constraint Identification

Pick **one** (not multiple) based on the worst signal from Steps 1-5:

1. **Viability** — LTGP/CAC < 3:1, margins broken. → Work `§1.2`, `§1.4` before any offer design.
2. **Attraction** — lead volume low or CAC too high. → Walk **Tree A**. (`§1.3` supports.)
3. **Monetization** — 30-day GP < CAC, payback too long. → Walk **Tree B** (upsells) and compress via `§1.5` tactics.
4. **Conversion** — leads come in but don't buy. → Walk **Tree C**. (Customer-research question: *why* are they saying no? Price, risk, value mismatch?)
5. **Retention** — customers buy once and leave, or churn spikes. → Walk **Tree D**.
6. **Cash constraint** — model works but can't fund growth. → Check `§1.6` CFA level, push to Level 3 via upsells + prepayment + initiation fees.

---

## Step 7 — Prescribe

Output must include:

1. **Constraint identified** (with the number that revealed it — "LTGP/CAC is 1.8:1" beats "unit economics look off")
2. **Which tree to walk** (explicitly name Tree A/B/C/D/E)
3. **Prescribed offer(s)** (section IDs only — `§3.3 Free Giveaways`, not prose)
4. **Why this over alternatives** (one sentence)
5. **Implementation order** — per `§7.1.c`, perfect one offer at a time; pick the single highest-leverage change first
6. **Success metric** — what number should move, and by when

**Don't prescribe more than two offer changes in a single pass.** Simple scales, fancy fails.

---

## When to refuse to prescribe

- LTGP/CAC < 1:1 — the business is burning money per customer. Prescribing an offer is rearranging deck chairs. Recommend fixing pricing, COGS, or retention first.
- Missing critical inputs and the user won't or can't provide them. Ask again or estimate with the user's help; don't fabricate.
- Signals contradict ("they say retention is fine but churn is 15%/month"). Surface the contradiction; don't resolve it by picking one.

---

## Example run (compressed)

> **User:** "SaaS. CAC ~$200. First-month GP is $80. We charge $50/month at 40% margin. Churn is ~8%."

- Step 1: LTV = 50/0.08 = $625 revenue. LTGP = 625 × 0.40 = $250. LTGP/CAC = 250/200 = **1.25:1.** **Below 3:1 — not viable as structured.**
- Constraint: **Viability, not offer design.**
- Prescription: Don't pick an offer yet. Options: raise price, reduce COGS, or cut churn (8% → 3% would push LTV to $1,667 and LTGP/CAC to 3.3:1). Reference `§6.3` for churn reduction tactics once viability is restored.
- Second pass would then diagnose further.

This is what it looks like to diagnose before prescribing.
