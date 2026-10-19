# Comparative urban traffic-management research

**Question:** Which traffic-management interventions, tried in cities comparable to Kathmandu, have worked or failed, and what does that imply for Kathmandu?

**Research mode:** discovery (per `lab/charter.md`) — this review is in support of hypothesis generation and feasibility judgment for the hackathon/paper deliverables, not a standalone synthesis-mode review.

## Scope (decided before searching, not after seeing what turned up)

The user's brief lists 35 cities across 3 priority tiers and 16 intervention types. Attempting all of it in one pass would force shallow, under-verified claims — exactly what this project's own citation discipline (`lab/literature/sources.md`) exists to prevent. This review covers a deliberately narrower slice, chosen for relevance and tractability:

**Cities covered** (10 of 35):
- Priority 1 (closely comparable, mixed-traffic, motorcycle-heavy): **Dhaka, Delhi, Lahore, Karachi, Colombo, Pokhara**
- Priority 3 (proven innovations, strongest documented track record): **Curitiba, Bogota, Seoul, Singapore**
- Reused from this project's existing research: **Jakarta** (`jakartapost2013`, already verified in an earlier pass on congestion-pricing feasibility — not re-searched here)

**Cities NOT covered, and why:** Karachi's sibling cities Chattogram, Bengaluru, Kolkata, Pune (Priority 1) and the remaining Priority 2/3 cities (Nairobi, Hanoi, Ho Chi Minh City, Manila, Quezon City, Bangkok, Phnom Penh, Addis Ababa, Kigali, Lima, Medellin, Mexico City, Istanbul, Tokyo, Taipei, Shenzhen, Surabaya, London, Stockholm) were skipped — not because they lack relevant lessons, but because covering them properly (actually opening sources, not just search snippets) was not feasible in this pass. They are listed here as an explicit gap, not silently dropped.

**Intervention types covered** (6 of 16): adaptive/coordinated signal control, BRT/dedicated bus lanes, parking/encroachment enforcement, motorcycle and mixed-traffic management, decentralization/transit-oriented development (context only, no new city evidence found), and congestion-pricing feasibility.

**Intervention types NOT covered:** AI-based congestion forecasting, computer-vision CCTV monitoring, real-time incident detection/emergency priority, digital parking systems, pedestrian/cycling infrastructure, roundabout/junction redesign, freight/school-hour restrictions, public-transport route consolidation (as its own topic, separate from BRT), one-way street systems. No strong, relevant source turned up for these in the cities searched, and they were not pursued further given the time budget.

**A verification-rigor caveat that applies to this entire review:** every source below was found via `WebSearch` (standard mode) only — no page was directly opened and read in full (no `WebFetch` in this pass). That is a **weaker standard** than this project's own `jica2012`/`jica2017` sources, which were downloaded and verified via direct text extraction. Every claim here is marked "search-result synthesis" in `sources.md` and should be read as *plausible and traceable to a real source*, not as independently confirmed. Treat accordingly — this is adequate for a feasibility screen, not for a number quoted in the paper without a second check.

## Claim table

| Claim | Source | Location | Direct or inferred |
|---|---|---|---|
| Delhi's 5.8km Ambedkar Nagar-Moolchand BRT corridor was evaluated by CRRI (2012) and found to considerably reduce vehicle speeds for general traffic | `delhibrt2012` | search synthesis of news coverage of the report | direct (as reported by news, not the report itself) |
| The Delhi BRT corridor was officially scrapped by the Delhi government (cabinet decision, ~2015) citing accidents and haphazard traffic, with dismantling costed at ~Rs 10-12 crore | `delhibrt2012` | same | direct (as reported) |
| Karachi's Green Line BRT cost rose from an initial ~Rs 16.85 billion (1-year schedule) to ~Rs 35 billion (~6 years), with a 2017 ECNEC-approved revision citing a longer, more elevated corridor | `karachigreenline2022` | search synthesis | direct (as reported) |
| Karachi Green Line ridership (~55,000/day after the initial surge) fell well short of the ~400,000/day officials had projected | `karachigreenline2022` | same | direct (as reported) |
| Bogota's TransMilenio ex-post evaluation (Hidalgo et al. 2013) found positive, robust cost-benefit results on travel time, safety and air quality, but noted declining user perception | `bogota_hidalgo2013` | abstract-level synthesis | direct (abstract claim), **not independently checked against the paper's actual numbers** |
| TransMilenio's capital cost was cited (in a ~2010 UN presentation) at ~US$5 million/km for BRT vs ~US$107 million/km for a comparable metro | `bogota_hidalgo2013` | same search result | direct (as reported in that presentation) — an old, single-source figure |
| Curitiba's BRT construction cost is most consistently cited around US$200,000-214,000/km, versus a cited ~US$90 million/km for a subway alternative | `curitiba_brt_history` | secondary sources (ADB case study, Streetsblog); the search itself flags this as not from primary budget records | direct claim from secondary sources, weak provenance |
| Seoul's 2004 bus reform is credited with an 80% rise in bus speed, a 9.4% ridership increase (2004-2017), and a 30% fare reduction, with a cost caveat the sources do not resolve | `seoul_busreform2004` | search synthesis, one source explicitly adapted from a city-agency's own material | direct claim, cautioned by the review itself as needing independent cross-check given the source |
| A 2011 Korean journal evaluation (Kim, Cheon & Lim) found a measurable drop in traffic density in Seoul following the reform | `seoul_busreform2004` | cited secondhand via search snippet | inferred existence of the paper — **treat the paper itself as an unverified lead**, not confirmed |
| Pokhara installed traffic signals at main intersections that are reportedly not in use, with police still directing traffic manually | `pokhara_signals_unused` | search synthesis of a single news report, exact date unclear | direct (as reported) |
| Colombo's earlier Galle Road priority bus lane was scrapped in a short span due to weak enforcement and motorist non-compliance, while a later (2017) Rajagiriya-Borella pilot reported improved speeds during active enforcement | `colombo_buslane2017` | search synthesis | direct (as reported) |
| Dhaka's enforcement drives against motorcycle violations (hundreds of cases/day in some periods) have not been shown, in the sources found, to produce a lasting reduction in violations | `dhaka` (not individually keyed — general web search, see search-log #11) | search synthesis | inferred (absence of evidence of lasting effect, not evidence of no effect) |
| Jakarta's proposed Electronic Road Pricing never launched after roughly a decade of attempts, and its 3-in-1 occupancy rule was defeated by "jockeys" hired to fill empty seats | `jakartapost2013` (reused, already in `lab/literature/sources.md`) | prior session's verification | direct, already in the paper's Discussion section |

## Synthesis by theme

### 1. Interventions that depend on sustained, discretionary enforcement tend to fail in low-capacity settings — this is the strongest, most consistent pattern across every city searched

Jakarta's 3-in-1 occupancy rule (already verified, `jakartapost2013`), Colombo's first Galle Road bus lane (scrapped for non-compliance), Pokhara's installed-but-unused signals, and Dhaka's persistent motorcycle violations despite repeated enforcement drives all point the same direction: an intervention that requires continuous, on-the-ground policing to work is fragile in a setting without the institutional capacity to sustain that policing. This project's own existing finding — adaptive signal control requires no enforcement of driver behavior at all — fits squarely inside this pattern, not as an isolated result. Colombo's second attempt (2017, Korean-assisted, actively enforced during the pilot) did see a reported speed improvement, which is some evidence the mechanism itself (a bus lane) is not inherently useless — but the lesson is that *enforcement intensity*, not the lane paint, is what varies between its two attempts.

### 2. BRT systems have a wide range of outcomes, and cost/ridership shortfalls are common, not rare, among South Asian attempts specifically

Curitiba and Bogota are the textbook successes, built over decades with sustained political commitment and (for Curitiba) a notably low per-km construction cost. But the two South Asian BRT cases found here — Delhi and Karachi — both show real trouble: Delhi's corridor was built and then physically removed after a court-ordered evaluation found it degraded other traffic; Karachi's Green Line overran its budget by roughly 2x and its schedule by roughly 6x, and ridership came in well under a quarter of what was projected. Lahore's Metrobus has no independent evaluation in what was found here at all — only operator-reported figures. This is a meaningfully different track record than the Latin American cases, and a plan for Kathmandu should weight the South Asian evidence more heavily than Curitiba/Bogota's success, precisely because the South Asian cities share Kathmandu's narrow roads, mixed traffic and institutional constraints far more closely.

### 3. Where evidence does exist for success, it tends to be overseen by a sustained, specific institutional reform, not a single physical change

Seoul's reform bundled quasi-public bus management, exclusive lanes, and an integrated fare system under a dedicated stakeholder committee — not just painted lanes. The reviewed sources frame this bundling as central to the result, not incidental. This cautions against treating any one piece of Seoul's reform (e.g. "just add bus lanes") as portable on its own.

### 4. Congestion pricing's weak track record in comparable-capacity cities (already documented for Jakarta) was not contradicted by this pass, though Singapore's success is real evidence it is not impossible with sufficient capacity

Singapore's ERP is widely regarded as effective, but every source found in this pass for its actual effect size was secondary or further removed (a student blog citing an unnamed presentation) — this review did not surface primary evidence strong enough to add confidently to this project's existing pricing-feasibility discussion. This does not contradict Singapore's success; it means this pass did not verify it well enough to cite a number.

## Gaps

- **Studied only in a narrow setting:** Seoul's reform evidence is strong for Seoul's specific institutional bundle; nothing found here tests whether a partial version (e.g. just exclusive bus lanes, without the quasi-public management layer) succeeds elsewhere.
- **Not studied (in this pass):** Pune, Kolkata, Bengaluru, Chattogram, and most Priority 2 cities — genuinely not searched, not a null result.
- **Studied but contradictory:** BRT cost-effectiveness. Curitiba/Bogota positive, Delhi/Karachi negative, all within "developing-city BRT" as a category — the determining factor (political continuity? corridor length vs. planning? enforcement capacity?) is not resolved by this pass and would need its own targeted review.
- **Verification gap, not a content gap:** every source in this review is one level weaker than this project's own best sources (search synthesis vs. directly opened and extracted text). Before any number here goes into the paper or a pitch, it should be upgraded to at least "abstract opened directly" per this project's existing standard.

## Self-audit (3 claims re-checked against their source)

1. **"Karachi Green Line ridership ~55,000/day vs ~400,000/day projected"** — re-checked against the WebSearch result: the search result itself states "average of around 55,000 people per day" and "project expected to benefit 400,000 passengers every day" as separate, directly-stated figures, not something this review combined or inferred. Holds up.
2. **"Delhi BRT corridor dismantling cost ~Rs 10-12 crore"** — re-checked: the search result attributes this specifically to "a December 2015 report," which this review carried through correctly with that attribution, not stated as a government figure without a source level. Holds up, with the important caveat (already in the claim table) that no source confirmed the dismantling was actually completed on schedule.
3. **"Seoul bus speed +80%, ridership +9.4%, fare -30%"** — re-checked: the search result explicitly flags this exact figure set as coming from "a development-sector case study... adapted from material by the Seoul Urban Solutions Agency" and says to "treat its figures with some caution." This review's claim table does carry that caution forward. Holds up, but this is the weakest-sourced of the three positive BRT/bus-reform claims in this review and should not be quoted without that caveat.

## Final deliverable: feasibility ranking and recommendations for Kathmandu

Tiers follow the user's framework. "Evidence" cites the claim table above; where this project's own simulation results are also relevant, they are cited directly (not re-derived here).

### Tier 1 — Feasible immediately at low cost
- **Adaptive/coordinated signal control.** This project's own simulation already supports this (combined-lever effect -65.30% +/- 4.47% vs. fixed-time, 15/15 seeds; see `lab/paper/claims.md`). The comparative evidence here reinforces *why* it travels well to Kathmandu specifically: it needs no driver-facing enforcement, the single pattern that recurs as a failure mode across Jakarta, Colombo, Pokhara and Dhaka.

### Tier 2 — Feasible after a small pilot
- **A single-corridor, actively-enforced dedicated bus lane**, piloted the way Colombo's 2017 Rajagiriya-Borella lane was (external technical assistance, a short defined corridor, active enforcement built in from day one) rather than painted and left, the way Colombo's earlier Galle Road lane and this project's own Pokhara finding (signals installed but unused) both show failing. A pilot, not a network-wide rollout, directly tests whether Kathmandu's traffic police can sustain the enforcement a lane needs before committing to Karachi- or Delhi-scale capital spending.

### Tier 3 — Feasible only with significant infrastructure or institutional reform
- **A full BRT corridor.** The South Asian evidence (Delhi removed, Karachi over budget and under-ridden) is a direct warning that Kathmandu's narrow roads and mixed traffic put it closer to the South Asian outcome than the Curitiba/Bogota outcome, unless a BRT plan explicitly addresses the things Seoul's successful reform bundled (institutional management reform, not just lane paint) before breaking ground.

### Tier 4 — Not currently feasible or insufficiently supported by evidence
- **Congestion/cordon pricing.** Consistent with this project's own existing Discussion section: no well-documented, comparable-capacity success case was found (Jakarta's attempt never launched; Singapore's success could not be verified strongly enough in this pass to count as a comparable precedent, since Singapore's institutional and enforcement capacity is not comparable to Kathmandu's).

### The three most promising interventions, with pilot plans

1. **Adaptive signal control at the highest-delay intersections.** *Evidence:* this project's own 15-seed result, already strong. *Cost:* primarily software/control-logic (queue-actuated, no new hardware beyond what fixed-time signals already need at a signalised intersection). *KPI:* mean delay and completion rate at the pilot intersections, using this project's own `scripts/find_bottlenecks.py` ranking to choose them. *Pilot:* the top 3-5 bottleneck intersections (already ranked by this project's own delay analysis) for one signal cycle revision, measured against the fixed-time baseline for at least 2-4 weeks before any wider rollout.

2. **A single actively-enforced bus-priority corridor**, modeled on Colombo's 2017 pilot rather than a full BRT build. *Evidence:* Colombo's contrast between its enforced pilot and its earlier scrapped lane; Pokhara's unused-signals finding as a direct warning about what happens without that enforcement commitment. *Cost:* low relative to full BRT — lane markings/dividers and a defined traffic-police enforcement assignment for the pilot corridor, not new buses or stations. *KPI:* bus travel time and schedule reliability on the corridor, and lane-violation rate as the enforcement-health metric specifically (a lane with a rising violation rate is the leading indicator of the Colombo/Pokhara failure mode, catchable before it fully fails). *Pilot:* one corridor, 1-2km, for 4-8 weeks, with enforcement staffing committed and budgeted *before* the pilot starts, not added reactively.

3. **Parking/encroachment enforcement paired with the signal work, not alone.** This project's own result here is a genuine caution, not a recommendation to skip: its own simulated "parking enforcement" lever (raising free-flow speed network-wide) was *rejected* once a completion-bias artifact was corrected (`lab/decisions.md`, H5/E7 — the earlier apparent improvement was seeds failing to complete, not a real speed gain), and only 5 clean seeds remained, with a wide, non-significant CI. The comparative evidence here (Dhaka's unresolved violations despite drives) does not contradict that caution. *Recommendation:* do not pilot this as a standalone intervention; if pursued at all, pair it explicitly with the signal-control pilot on the same corridor so any effect can be attributed correctly, and budget for sustained enforcement from the start given the cross-city pattern in Theme 1 above.

## Notebook entry

See `lab/notebook/2026-10-19.md` for the dated entry pointing to this file.
