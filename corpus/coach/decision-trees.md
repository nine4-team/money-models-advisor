# Decision Trees

Trees route, they don't teach. Every leaf points to a section in [`index.md`](index.md) where the mechanic is taught. Use the [`diagnostic-flow.md`](diagnostic-flow.md) first to identify the constraint, then walk the matching tree.

---

## Tree A — Which Attraction Offer Fits?

**Root question:** What's the biggest barrier to first purchase?

- **Perceived risk / "I might not get results"**
  - Is the outcome measurable (weight, revenue, skill milestone)? → `§3.2 Win Your Money Back`
  - Physical product or one-time service, customer balks at full price? → `§3.6 Pay Less Now / Pay More Later`
  - Need to build trust before charging a high-ticket price? → `§3.7 Free with Consumption`

- **Price — "I can't justify the cost"**
  - Physical product or one-time service? → `§3.6 Pay Less Now / Pay More Later`
  - Recurring revenue — prepayment discount viable? → `§3.5 Buy X Get Y Free`

- **Awareness — "I don't know you / don't know I need this"**
  - Need large lead volume fast with qualification data? → `§3.3 Free Giveaways`
  - Target audience responds to content / education first? → `§3.7 Free with Consumption`

- **Decision paralysis — "I see the offer but I'm not sure it's for me"**
  - Premium product struggles to advertise directly? → `§3.4 Decoy Offers`

- **Default if nothing obvious fits:**
  - `§3.3 Free Giveaways` (broadest applicability, generates leads + data)

---

## Tree B — Which Upsell Fits?

**Root question:** What's true about the next natural sale after the first?

- **The core product requires accessories or complements to deliver results.**
  - → `§4.2 Classic Upsell` ("you can't have X without Y")
  - Target close rate: 80%+ (benchmark: McDonald's fries/Coke)

- **There's a legitimate premium tier at 5-10× main price.**
  - → `§4.4 Anchor Upsell`
  - Rule: change only secondary features between anchor and main

- **Multiple add-on products, sold at a consult or face-to-face.**
  - → `§4.3 Menu Upsell`
  - 4 steps: Unsell → Prescribe → Ask Preference → Card on File

- **Dealing with old, upset, or competitor-acquired customers.**
  - Win-back an old customer → `§4.5 Rollover Upsell` (situation 1)
  - Upset customer (refund alternative) → `§4.5 Rollover Upsell` (situation 2)
  - Steal competitor's customers via 1-star review outreach → `§4.5 Rollover Upsell` (situation 3)
  - Move current customer to higher tier → `§4.5 Rollover Upsell` (situation 4)

Note: **Buy X Get Y Free** (`§3.5`) is categorized as Attraction in Hormozi's course, but can also function as an upsell for recurring services — prepay + bonus duration is a common post-purchase mechanic. If the goal is post-purchase prepayment, route to `§3.5` even though it's in Chapter 3.

---

## Tree C — Which Downsell Fits?

**Root question:** Why did the customer say no?

- **"Can't afford it today" (but would afford it over time).**
  - → `§5.2 Payment Plans`
  - 7-step flow: anchor plan price first → third-party financing → split 50/50 → temperature check → 3 payments → equal payments → free trial (last resort)

- **"I'm not sure it'll work" — risk / trust issue on a recurring service.**
  - Recurring service where customer must do work to get results → `§5.3 Free Trials (Trial with Penalty)`
  - *(For risk on one-time products/services, see `§3.6` Pay Less Now in attraction — same mechanic works as downsell.)*

- **"Too much for what I need" — value mismatch.**
  - → `§5.4 Feature Downsells`
  - First pass: remove a valuable feature (usually the guarantee) with a small price drop → triggers re-upsell
  - If that fails: swap big feature back, remove something they care less about, take a big price cut
  - Barter exception: customer gives you reviews/testimonials/referrals → lower price without removing value (`§5.4.e`)

- **Temperature check before cycling further (≤ 8/10 interest):**
  - If interest drops, cross over to another downsell type or concede the sale

---

## Tree D — Which Continuity Offer Fits?

**Root question:** Why aren't customers sticking around?

- **No compelling reason to subscribe at all.**
  - → `§6.2 Continuity Bonus Offers`
  - Bonus exceeds first month's value; advertise the bonus not the subscription
  - Standalone-vs-continuity premium data: 1.33× → 50% take continuity; 2.66× → 90%

- **Known churn spike at a specific month.**
  - → `§6.3 Continuity Discount Offers` (lifetime discount at churn point)
  - "2 months until your lifetime discount kicks in"

- **Commitment is the real ask; want sunk-cost to keep them.**
  - → `§6.4 Waived Fee Offers`
  - Startup fee = 3-5× monthly rate; waived if committed, owed if cancel early
  - Target <5% early cancellation (above = product issue, not fee issue)

- **Involuntary churn from declined cards.**
  - → `§6.3 Continuity Discount Offers` (collect card AND ACH via "3% fee waived")

- **Transactional business, no continuity yet.**
  - Any attraction offer can become continuity with a renewal clause (see `§7.1.c`)

---

## Tree E — The "What to Add Next" Meta-Tree

**Root question:** Where is the money model breaking?

- **Can't cover CAC from first sale.** → Add or strengthen an Upsell (walk Tree B) → also check `§1.6 CFA` levels
- **One-and-done customers, no recurring revenue.** → Add Continuity (walk Tree D)
- **Customers say no at checkout.** → Add a Downsell (walk Tree C)
- **Not enough leads in the door at viable CAC.** → Strengthen Attraction (walk Tree A) → also check `§1.3 CAC` free-vs-discount framework
- **Model is right but growth is cash-constrained.** → Check `§1.6 CFA` — aim for Level 3 (30-day GP > 2× CAC)
- **Revenue healthy but profit weak.** → Check `§1.4 Gross Profit` — the 80% service-margin rule, or LTV focus over cost-cutting

---

## Rules that apply across all trees

1. **Perfect one offer at a time.** Never launch all four types simultaneously. (`§7.1.c`)
2. **Simple scales, fancy fails.** Minimum offers to achieve CFA. (`§7.1.c`)
3. **Never lower price without changing what they get** — unless the customer gives you something (referrals, reviews, content). (`§5.4.e`)
4. **"Free" dominates "discount"** — either fully free or full price; 10-20% discounts rarely move behavior. (`§1.3`)
5. **Sell at the point of greatest deprivation, not greatest satisfaction.** Best upsell timing = right after a new problem emerges, not after a win. (`§1.5`)
