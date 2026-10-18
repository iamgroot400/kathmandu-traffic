# Literature review: signal control + congestion pricing interaction, and Kathmandu context

Scope and queries: see `search-log.md`. Full source list: `sources.md`.

## Claim table

| Claim | Source | Location | Direct or inferred |
|---|---|---|---|
| A bilevel model jointly setting signal timings and congestion tolls, with an upper level maximizing reserve capacity/minimizing travel time and a lower level as user equilibrium, "can achieve promising results" on a numerical example | mao2013 | abstract | direct (but abstract gives no comparison vs. either lever alone, and no interaction term) |
| A bilevel method sets signal timings and road prices together, locally optimal for a smooth criterion, in a link-flow framework chosen for tractability on large networks | smith1997 | abstract | direct |
| A multi-modal elastic-equilibrium model with signal green-times and charges (fares, parking, road-use prices) has an algorithm proven to approach locally-optimal (KKT) points; tested on a small 5-route, 2-signal-junction network; abstract gives no combined-vs-separate comparison | clegg2001 | abstract | direct |
| Using link-exit *prices* (instead of delays) together with green/red signal times maximizes the capacity of a general steady-state network while keeping queues at zero; extended to dynamic networks (equilibrium + day-to-day stability) | smith2022 | abstract | direct |
| None of the above three papers report, in their abstracts, a result of the form "combined effect exceeds the sum of each lever's individual effect" | mao2013, smith1997, smith2022 | abstracts | inferred (absence of a stated claim, not a confirmed absence from the full text) |
| UXsim's traffic model is a mesoscopic version of Newell's simplified car-following model, equivalent to a kinematic-wave model with a triangular fundamental diagram; supports signals, inflow control, route guidance, and congestion pricing as built-in control schemes | seo2023 | full text, model description section | direct |
| UXsim computes large-scale traffic phenomena "fairly effectively" despite Python's modest raw speed; a Sioux Falls network (34,690 vehicles, 7,200s) ran in ~16s on a 3.79GHz/32GB machine | seo2023 | full text, performance section | direct |
| UXsim's paper makes no explicit comparison to SUMO or VISSIM | seo2023 | full text | direct (absence noted) |
| At Kathmandu's Lainchaur intersection, major approaches operate at LOS F; fixed-time Webster-method signals at various cycle lengths gave "partial but inconsistent" improvement; authors recommend adaptive/actuated control for future demand growth | tamang2026 | abstract | direct |
| A 2025 review frames Kathmandu's congestion response as needing a "multimodal, data-driven approach" combining intelligent traffic systems, transit investment, and institutional reform; notes "some progress" in signal optimization; does not mention congestion pricing | luitel2025 | abstract | direct |
| A 2024 Kathmandu thesis monetizes congestion cost on one road section (New Baneshwor-Old Baneshwor) at NRs 321,020.58, split into opportunity cost, vehicle operating cost, and emission cost | bhatta2024 | abstract | direct |
| No Kathmandu-specific study combining congestion pricing with signal control, or using a mesoscopic/macroscopic city-scale model (as opposed to intersection-level VISSIM microsimulation), was found | (absence across all Kathmandu-related searches) | search-log.md queries 3, 7, 8 | inferred from a negative search result, not a confirmed absence in the field |
| Demand-responsive signal strategies exist (SCOOT gating, IMPOST queue metering) specifically because standard adaptive signal control is designed for undersaturated conditions and its objectives change under oversaturation | (search synthesis, "A Taxonomy of Adaptive Traffic Signal Control" lead) | search snippet only, not an opened page | inferred, **weak** — this is the closest literature gets to a mechanistic reason H3 could be true, but it was never read in the primary source, only reported by a search engine's own synthesis |

## Synthesis, by theme

### 1. Joint signal+pricing optimization exists; a measured interaction/super-additivity claim does not (that could be found)

Three lines of prior work jointly treat signals and pricing: a bilevel-optimization tradition going back to at least 1997 (smith1997, extended in clegg2001, applied again in mao2013), and a capacity-theoretic tradition (smith2022) proving that *prices* used as the control variable (rather than observed delay) can achieve zero-queue, capacity-maximizing control. All three establish that **combining the two levers is a studied, legitimate design** — this project's two-lever choice is not novel on its own. None of their abstracts, however, report comparing a combined scenario against the sum of each lever's individually-measured effect — the specific empirical form of H3. This is a real gap in what the abstracts state, not a confirmed absence in the field; the full texts (especially clegg2001 and any numerical-example sections of mao2013/smith1997) were not read and could contain exactly this comparison.

### 2. Kathmandu/Nepal literature is intersection-level and microscopic; no city-scale mesoscopic or pricing study found

Every located Kathmandu traffic study (tamang2026, plus leads for Jagati/Bhaktapur, Kantipath, the bus-lane and reversible-lane studies, and the Manandhar thesis) uses PTV VISSIM at single-intersection or single-corridor scale, calibrated from short video surveys. None models a city-wide network, and none tests congestion pricing — the closest is luitel2025's passing mention that signal optimization is "underway," with pricing absent from its recommendations, and bhatta2024's cost estimate for one road section with no policy lever attached. This supports the charter's claim (and this review's finding) that a 233-node mesoscopic city-scale model combining both levers would be new *for Kathmandu specifically* — a narrower and more defensible novelty claim than "novel in general."

### 3. UXsim is a defensible, citable choice, with its justification resting on a technical-overview paper rather than the newer JOSS release

seo2023 gives the model (mesoscopic Newell/kinematic-wave) and performance numbers (Sioux Falls, ~16s/34,690 vehicles) needed to defend "mesoscopic, not microscopic" as a deliberate scale choice for a 233-node network. (A SUMO-mesoscopic-limitations paper, ni2026sumo, turned up as a possible contrast — but its specific limitation claims are unverified, sourced only from a search-engine snippet after its PDF came back unreadable; do not cite its limitation details without reading the actual text first.) It explicitly lists congestion pricing as a built-in supported control scheme, which is a stronger citation than reverse-engineering it from this project's own `run_pricing.py`. The 2025 JOSS paper (seo2025) is the more recent and more citable *software* reference, but its page yielded no body text to extract beyond the citation itself — cite both (software: seo2025; method: seo2023), per the arXiv/JOSS pattern other UXsim-based papers likely follow.

## Gaps

- **Not studied (as far as this search found):** a quantified comparison of combined signal+pricing control against the sum of separately-measured signal-only and pricing-only effects, in any network. This is the gap H3 would fill. **Caveat:** this is a negative search result across ~13 queries and a handful of opened abstracts, not a systematic review of the bilevel-control literature's full texts — the honest claim is "not found," not "does not exist." The highest-priority unread source for closing this gap is the full text of smith2022 (open-access PDF already located) and clegg2001.
- **Studied only in a narrow setting:** Kathmandu traffic modeling is studied, but only at single-intersection scale with VISSIM, never city-scale or mesoscopic, and never with pricing.
- **Not studied:** congestion-pricing feasibility or policy design specifically for Kathmandu — bhatta2024 measures a cost, not a priced intervention; the only pricing *proposal* found is a newspaper opinion piece, not research.

In discovery mode, the first gap (super-additivity not found but not ruled out) is the one to hand to a `hypothesis-tournament`-style sharpening: if the full texts of smith2022/clegg2001 confirm no prior measurement, H3's framing can be stated as filling a specific, named gap in the bilevel-control literature, not just as a Kathmandu-local finding.

## Self-audit (re-checked 3 random claim-table rows against source)

1. **Row: "UXsim's traffic model is a mesoscopic version of Newell's simplified car-following model..."** — re-opened seo2023's model section. Confirmed: text states the link model "is equivalent to a mesoscopic version of Newell's simplified car-following model" and separately "a kinematic wave model with a triangular fundamental diagram." Matches as stated.
2. **Row: "At Kathmandu's Lainchaur intersection, major approaches operate at LOS F..."** — re-checked against the tamang2026 extraction. Confirmed: "Major approaches operate at LOS F (severe congestion). Minor movements operate at LOS A-C." Matches as stated; the claim table's wording is a close paraphrase, not a quote, which is correct practice (quotes above are marked and short).
3. **Row: "Demand-responsive signal strategies exist (SCOOT gating, IMPOST queue metering)..."** — re-checked against its own search-log entry. This one does **not** fully hold up on audit: the SCOOT/IMPOST detail came from a WebSearch synthesis paragraph, not from an opened primary source (no URL for SCOOT/IMPOST documentation was ever fetched). The claim table already flags this as "weak" and "never read in the primary source" — the self-audit confirms that flag was necessary and should stay; this row should not be upgraded to a firmer claim without actually opening a SCOOT/IMPOST-specific source.

**Audit result:** 2 of 3 rows confirmed accurate on re-check; 1 was already correctly flagged as weak and remains weak — no correction needed, but no source should be added without doing so properly.
