# Literature search log

Scope: (1) has any prior work measured/reported a super-additive (more-than-sum) interaction between adaptive signal control and congestion pricing in a traffic network — tests H3; (2) prior Kathmandu/Nepal traffic congestion studies, for context and to check this project's novelty against local work; (3) citation support for UXsim and its mesoscopic approach vs. microscopic alternatives (SUMO). Cordon/external-demand literature explicitly out of scope (see decisions.md D6 — scoped out of the project itself).

Tool: WebSearch (web, no access restriction), WebFetch for opening specific pages. No access to paywalled full text (ScienceDirect blocked WebFetch with 403 twice) — worked around via open-access mirrors (White Rose, ar5iv, repec) where available.

| # | Query | Tool/mode | Where | Key hit |
|---|---|---|---|---|
| 1 | combined adaptive traffic signal control and congestion pricing synergy delay reduction simulation | WebSearch extended | general web | No study combining both; several signal-only studies |
| 2 | interaction effect congestion pricing signal timing superadditive traffic network | WebSearch extended | general web | Mao et al. 2013 (joint bilevel), NBER NYC cordon pricing spillover |
| 3 | Kathmandu traffic congestion simulation model study | WebSearch standard | general web | VISSIM studies: Lainchaur, Jagati/Bhaktapur, Kantipath, bus lane, reversible lanes, Manandhar thesis |
| 4 | UXsim mesoscopic traffic simulator paper citation | WebSearch standard | general web | Seo 2025 JOSS paper; Seo 2023 arXiv technical overview |
| 5 | bilevel programming signal control congestion pricing joint optimization transportation network | WebSearch standard | general web | Mao et al. 2013 confirmed; mixed-autonomy tolling+routing (TR Part C 2021); combinatorial pricing (arXiv 2412.06482) |
| 6 | complementarity road pricing traffic signal optimization combined effect greater than sum | WebSearch standard | general web | Smith/Xiang/Yarrow 1997 bilevel signal+price; Dial network-optimized pricing |
| 7 | Kathmandu Nepal mesoscopic macroscopic traffic simulation congestion pricing UXsim SUMO | WebSearch standard | general web | SUMO mesoscopic limitations paper (arXiv 2606.09282); confirms no Kathmandu+pricing+UXsim/SUMO study exists |
| 8 | Kathmandu road pricing congestion tax feasibility study | WebSearch standard | general web | No dedicated Kathmandu pricing feasibility study found; Himalayan Times opinion piece; Bhatta 2024 thesis (congestion cost, not pricing policy) |
| 9 | "congestion pricing" "signal control" interaction empirical case study delay reduction percent | WebSearch standard | general web | York/Cambridge CONTRAM study (Smith et al., via secondary citation) — closest empirical lead |
| 10 | Smith delay based road pricing traffic signal control York Cambridge results combined | WebSearch extended | general web | Led to Smith, Iryo, Mounce, Satsukawa, Watling 2022 (TR Part C) |
| 11 | "Zero-queue traffic control" "green-times and prices" Smith abstract | WebSearch extended | general web | Confirmed citation + abstract for Smith et al. 2022 |
| 12 | demand reduction improves effectiveness of adaptive signal control oversaturated network | WebSearch standard | general web | Confirms oversaturation changes signal-control objectives (gating/metering tools like SCOOT, IMPOST exist precisely because signal control degrades under oversaturation) — mechanistic support for H3, not a direct measurement |
| 13 | congestion pricing enables signal control to work better saturation relief mechanism | WebSearch standard | general web | No direct study found; general framing only (Shepherd review, Toronto report) |

## Direct page opens (WebFetch)

| URL | Result |
|---|---|
| projecteuclid.org/euclid.jam/1394807421 (Mao et al. 2013) | Failed — no text returned |
| ideas.repec.org/a/hin/jnljam/315752.html | Success — abstract |
| joss.theoj.org/papers/10.21105/joss.07617 (UXsim) | Partial — citation only, no body text on page |
| ar5iv.labs.arxiv.org/html/2309.17114 (UXsim technical overview) | Success — full text accessible |
| nepjol.info (Lainchaur intersection) | Success — full abstract/findings |
| nepjol.info (Kathmandu multi-faceted congestion review) | Success — abstract |
| cps.nec.edu.np (Bhatta 2024 thesis) | Success — abstract |
| arxiv.org/pdf/2606.09282 (SUMO mesoscopic limitations) | Failed — PDF returned as binary, unreadable; title/authors only from metadata |
| swov.nl (York/Cambridge road pricing + signal control) | Failed — HTTP 403 |
| sciencedirect.com (Zero-queue traffic control) | Failed — HTTP 403 |
| eprints.whiterose.ac.uk/184551 (Zero-queue traffic control, open-access mirror) | Success — full abstract |
