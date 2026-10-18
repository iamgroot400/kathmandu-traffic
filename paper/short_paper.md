# Signal Retiming and Congestion Pricing on Kathmandu's Arterial Network: A Paired-Seed Simulation Study

**Aashik Khatri, Pratik Sharma**

---

## Abstract

Kathmandu's peak-hour arterial congestion has grown far faster than road capacity. We test two deployable interventions — adaptive signal control and marginal congestion pricing — on a calibrated mesoscopic simulation of the city's Ring Road and arterial network (233 nodes, 590 links), using a paired-seed statistical design to separate each intervention's effect from simulation noise. Adaptive signals reduce peak-hour delay by 24.5% and congestion pricing by 31.9%, both against a fixed-time baseline, each tested across 15 random seeds with 95% confidence intervals excluding zero. Combined, the two levers reduce delay by 65.3% — the strongest result in this study — though a direct statistical test finds no significant super-additive interaction between them. We validate the baseline against observed traffic counts at six real intersections (passing at two of six) and report this limitation plainly rather than overstate the model's precision. Four further candidate interventions were tested with the same rigor: staggered departure scheduling and decentralized trip attraction both show large, statistically supported effects; a time-based one-way lane scheme and a parking-enforcement proxy are tested and rejected.

**Keywords:** traffic simulation, signal control, congestion pricing, Kathmandu, mesoscopic modeling

## 1. Introduction

Kathmandu Valley's motorization has grown far faster than its road network. A 2012 government survey found motorcycle traffic had grown roughly 19.8× since 1991 — about 16% annually — concentrated on arterial roads that have not expanded proportionally. Two interventions are available to a city without the years and capital a new road or metro line requires: retiming existing signals, and charging for road use at the busiest hours. Both act on infrastructure that already exists.

This paper asks whether signal retiming and congestion pricing each significantly reduce delay on Kathmandu's arterial network, and whether combining them produces more than the sum of their separate effects. We build a calibrated simulation and test every comparison across 15 paired random seeds — a design choice forced by observing that small demand changes can move single-run delay by several percent on noise alone, so a single simulation run cannot be trusted to isolate an intervention's true effect.

## 2. Methodology

We use UXsim, a mesoscopic kinematic-wave traffic simulator, to model Kathmandu's Ring Road and city-core arterial network: 233 nodes and 590 directional links imported from OpenStreetMap, carrying a synthetic 260,000-trip peak-hour demand matrix built from a gravity model over 109 zones. Because only arterial roads are modeled, we load 30% of the full matrix — decomposed as a 0.48 arterial-share factor times a 0.625 passenger-car-equivalent factor reflecting Kathmandu's motorcycle-heavy fleet — calibrated so the baseline's mean speed matches observed conditions. Free-flow speed is overridden to 30 km/h network-wide, standing in for roadside encroachment and lane indiscipline that a mesoscopic model cannot represent behaviorally.

The baseline runs 128 fixed-time signalized intersections on a 90-second cycle. Adaptive control replaces this with a queue-actuated heuristic that extends green time for whichever approach has more vehicles waiting. Congestion pricing tolls each link at 0.2× its own observed delay, applied only during the peak window, with a fixed (non-iterated) schedule — making the reported pricing effect a conservative lower bound, since real demand would also respond by canceling trips, not just rerouting.

Every configuration runs the same 15 random seeds, and we report the paired difference with a 95% confidence interval rather than comparing single-run means. We additionally test four further interventions — tidal-flow lane reallocation, a friction-reduction proxy for parking enforcement, staggered departure scheduling, and decentralized trip attraction — with the same statistical design, and validate the baseline against observed traffic counts at six named Kathmandu intersections using the GEH statistic.

## 3. Results

Adaptive signal control reduces mean delay from 2,351 to 1,764 seconds, a 24.5% ± 7.1% reduction, with all 15 seeds agreeing in direction. Congestion pricing reduces delay by 31.9% ± 6.0%, also 15/15. Combining both levers reduces delay by 65.3% ± 4.5%, also 15/15 — the largest effect in this study. We tested directly whether this combined effect exceeds what the two levers would produce independently, computing the per-seed interaction term (combined effect minus the sum of each lever's individual effect): the result is −185.3 ± 275.6 seconds, not statistically significant, with only 9 of 15 seeds agreeing in sign. We do not find support for a super-additive interaction, and report the combined lever's strong standalone effect instead of a synergy claim.

A ±20% sensitivity sweep on the model's three calibrated parameters found that two of them — the arterial-share and vehicle-weighting factors — are not independently identified by the single calibration target used: a −20% change to either produces bit-for-bit identical simulation output. Validation against observed 2011–2012 traffic counts at six named intersections passes GEH < 5 at only two of six, with errors in both directions, confirming that the model's absolute numbers should be trusted less than its relative comparisons.

Of four further interventions tested, two succeeded and two failed. Staggered departure scheduling (demand spread over a 50% longer window) reduced delay by 36.3% ± 7.0%, the single largest effect measured, though this reflects a large scheduling change whose benefit at smaller, more realistic shifts was not tested. Decentralized trip attraction reduced delay by 31.1% ± 4.6%, confounded with an 11.4% cut to total demand. A time-based one-way lane scheme caused new gridlock in up to 5 of 15 seeds and, even after halving its magnitude removed that side effect, did not reduce delay — the problem was traced to corridor selection, not magnitude. A free-flow-speed increase modeling parking enforcement produced an apparent 28.6% improvement that was almost entirely a statistical artifact of seeds failing to complete; the real effect among unaffected seeds was −1.7%, not significant.

## 4. Discussion and Limitations

This model's demand is synthesized from a gravity model, not surveyed, and carries no observed trip counts or morning/evening directional asymmetry unless explicitly reweighted. Route choice follows within-day dynamic user optimum rather than a settled equilibrium; day-to-day equilibrium was attempted and does not converge on this network. The pricing result assumes fixed, inelastic demand and should be read as a lower bound. Both supported additional interventions carry unresolved confounds that future work should isolate with dedicated controls.

## 5. Conclusion

Signal retiming and congestion pricing each significantly reduce peak-hour delay on a calibrated simulation of Kathmandu's arterial network, and together they produce the largest effect measured — though not, by direct statistical test, a super-additive one. We report this correction alongside the model's honest limitations: partial validation against observed counts, an unidentifiable calibration split, and two further interventions that were tested and rejected rather than omitted. Future work should prioritize expanding observed-count validation and isolating the confounds on the two supported additional interventions.

## References

1. Seo, T. (2025). UXsim: lightweight mesoscopic traffic flow simulator in pure Python. *Journal of Open Source Software*, 10(106), 7617.
2. Seo, T. (2023). UXsim: An open source macroscopic and mesoscopic traffic simulator in Python — a technical overview. arXiv:2309.17114.
3. Mao, X., Qin, L., Hu, D., & Tan, X. (2013). Joint Implementation of Signal Control and Congestion Pricing in Transportation Network. *Journal of Applied Mathematics*, 2013, 315752.
4. Smith, M.J., Iryo, T., Mounce, R., Satsukawa, K., & Watling, D. (2022). Zero-queue traffic control, using green-times and prices together. *Transportation Research Part C*, 138, 103630.
5. Tamang, R., K.C., A., Pandey, B., & Acharya, A. (2026). Performance Evaluation and Improvement Strategies: A Case Study of Lainchaur Intersection. *Everest Advances in Science and Technology*, 2(2), 79-92.
6. Japan International Cooperation Agency & Department of Roads, Nepal. (2012). *Data Collection Survey on Traffic Improvement in Kathmandu Valley*. Final Report.

---

*Word count: ~920 words (Sections 1-5 only); ~1,110 words including the abstract. Excludes title, keywords, and references.*
