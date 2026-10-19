# Sources

| Key | Citation | Link | What was opened | Verified |
|---|---|---|---|---|
| mao2013 | Mao, X., Qin, L., Hu, D., & Tan, X. (2013). Joint Implementation of Signal Control and Congestion Pricing in Transportation Network. *Journal of Applied Mathematics*, 2013, 315752. | https://doi.org/10.1155/2013/315752 | abstract only (via repec mirror; direct journal page returned no text) | yes |
| smith1997 | Smith, M.J., Xiang, Y., & Yarrow, R. (1997). Bilevel optimisation of signal timings and road prices on urban road networks. *Proceedings, Transportation Systems 1997*, Chania, Greece, pp. 609-614. | https://trid.trb.org/View/505744 | abstract only (catalogue record) | yes |
| clegg2001 | Clegg, J., Smith, M.J., Xiang, Y., & Yarrow, R. (2001). Bilevel programming applied to optimising urban transportation. *Transportation Research Part B: Methodological*, 35(1), 41-70. DOI not verified — a PII-based guess (10.1016/S0191-2615(00)00018-7) was offered by a search but explicitly flagged as unconfirmed; do not cite a DOI for this paper without checking Crossref/ScienceDirect directly. | https://ideas.repec.org/a/eee/transb/v35y2001i1p41-70.html | abstract only (via repec) — model is multi-modal elastic equilibrium with signal green-times and charges (fares, parking, road-use prices); algorithm proven to approach locally-optimal (KKT) points; tested on a small 5-route, 2-signal-junction network. No comparison of combined vs. separate-lever effect in the abstract. | yes (existence + abstract), DOI unverified |
| smith2022 | Smith, M.J., Iryo, T., Mounce, R., Satsukawa, K., & Watling, D. (2022). Zero-queue traffic control, using green-times and prices together. *Transportation Research Part C: Emerging Technologies*, 138, 103630. | https://doi.org/10.1016/j.trc.2022.103630 (open-access PDF: https://eprints.whiterose.ac.uk/id/eprint/184551/13/1-s2.0-S0968090X22000742-main.pdf) | abstract only (full open-access PDF link obtained but not yet fetched) | yes |
| seo2025 | Seo, T. (2025). UXsim: lightweight mesoscopic traffic flow simulator in pure Python. *Journal of Open Source Software*, 10(106), 7617. | https://doi.org/10.21105/joss.07617 | abstract/citation only — page served no body text | yes |
| seo2023 | Seo, T. (2023). UXsim: An open source macroscopic and mesoscopic traffic simulator in Python — a technical overview. arXiv:2309.17114. | https://arxiv.org/abs/2309.17114 | full text (via ar5iv) | yes |
| ni2026sumo | Ni, Y-C., Akopian, A., Kouvelas, A., & Makridis, M.A. (2026). Revisiting mesoscopic traffic flow simulation in SUMO: Limitations, analysis, and an alternative. arXiv:2606.09282. | https://arxiv.org/abs/2606.09282 | title/authors only — PDF unreadable, claims about queue dynamics/backward-wave limitations come from a search-engine snippet, not a page I opened directly | partial — treat the specific limitation claims as **unverified** until the PDF text is actually read |
| tamang2026 | Tamang, R., K.C., A., Pandey, B., & Acharya, A. (2026). Performance Evaluation and Improvement Strategies: A Case Study of Lainchaur Intersection. *Everest Advances in Science and Technology*, 2(2), 79-92. | https://doi.org/10.3126/east.v2i2.99468 | full abstract + findings | yes |
| luitel2025 | Luitel, S., Subedi, A.K., Nepal, S., & Tiwari, H. (2025). A Multi-Faceted Approach to Urban Congestion in Developing Nations: Theory, Practice, and the Kathmandu Experience. *Journal of Advanced College of Engineering and Management*, 11(1), 139-163. | https://doi.org/10.3126/jacem.v11i1.84536 | abstract only | yes |
| bhatta2024 | Bhatta, A. (2024). *Evaluation of Traffic Congestion Costs of New Baneshwor to Old Baneshwor Road Section* [Thesis]. Nepal Engineering College. | https://cps.nec.edu.np/thesisabstracts/show/161 | abstract only | yes |

## Leads to verify (not opened — found in search snippets only, do not cite as support)

- Smith et al. 1994(b), the original York/Cambridge CONTRAM study on delay-based pricing + signal policy P0 — referenced secondarily inside smith2022's citation trail, actual paper/numbers not located.
- Guo, Li, Nie, Xie (2024). Combinatorial congestion pricing, arXiv:2412.06482 — toll-location selection, no signal control component; not opened.
- Dial, R.B. Network-optimized road pricing, Part II (Operations Research, 1999) — pricing-only, not opened.
- Jagati/Bhaktapur VISSIM study, Kantipath Monte Carlo study, Kathmandu-Bhaktapur bus-lane VISSIM study, Jadibuti-Koteshwor reversible-lane study, Manandhar (2023) VISSIM calibration thesis — all found in initial unstructured search (pre-skill), titles/topics only, none opened or confirmed.
- Himalayan Times opinion piece advocating Kalanki-Tripureshwor-Sundhara tolling — journalism, not an academic source; never to be cited as research evidence, only as color on local policy discourse if used at all.
- "A Taxonomy of Adaptive Traffic Signal Control" (arXiv:2308.01952) — general background on oversaturation changing signal-control objectives; not opened, cited claim about SCOOT/IMPOST gating is from search synthesis only.

## Added 2026-10-19 (E6/E7 validation sourcing — verified directly via pdftotext, not via the H3 literature-review search)

| Key | Citation | Link | What was opened | Verified |
|---|---|---|---|---|
| jica2012 | Japan International Cooperation Agency (JICA) & Department of Roads, Nepal. (2012). *Data Collection Survey on Traffic Improvement in Kathmandu Valley*. Final Report, October 2012. | https://openjicareport.jica.go.jp/pdf/12082459_01.pdf (and companion volumes _02 through _06) | full text (downloaded and extracted via pdftotext directly, not a search snippet — see `lab/experiments/E6.md`, D7) | yes |
| jica2017 | Japan International Cooperation Agency (JICA), Department of Roads, & Kathmandu Valley Development Authority. (2017). *The Project on Urban Transport Improvement for Kathmandu Valley*. Final Report, Volume II: Master Plan and Pilot Project, May 2017 (report 17-068). | https://openjicareport.jica.go.jp/pdf/12289682_01.pdf | full text (downloaded and extracted via pdftotext directly — see `lab/experiments/E6.md`) | yes |

## Added 2026-10-19 (pricing feasibility discussion, paper's Discussion section)

| Key | Citation | Link | What was opened | Verified |
|---|---|---|---|---|
| jakartapost2013 | The Jakarta Post. (2013, October 2). Dead end: Jakarta's jockeys. | https://www.thejakartapost.com/news/2013/10/02/dead-end-jakarta-s-jockeys.html | search-result synthesis only, not the full article text directly opened | partial — content (3-in-1 rule, hired jockeys, children used, Rp 15,000-20,000 fee) corroborated by a second independent search pass during the hackathon-scoping discussion (same session), not a direct full-text read |

## Added 2026-10-19 (comparative urban traffic-management research — all search-result synthesis, not directly opened; weaker verification than this project's jica2012/jica2017 standard)

| Key | Citation | Link | What was opened | Verified |
|---|---|---|---|---|
| delhibrt2012 | Central Road Research Institute (CRRI). (2012, June). Evaluating Bus Rapid Transit (BRT) corridor performance from Ambedkar Nagar to Moolchand, Delhi: final report. | https://indiaenvironmentportal.org.in/reports-and-documents/evaluating-bus-rapid-transit-brt-corridor-performance-from-ambedkar-nagar-to-moolchand-delhi-final-report | search-result synthesis only (news coverage of the report's finding that speeds were considerably affected, and the 2015-16 dismantling decision), not the report itself | partial |
| karachigreenline2022 | Dawn / ARY News / PropPakistani reporting on Karachi Green Line BRT cost and ridership (2021-2023 coverage, no single authored report). | https://arynews.tv/ecnec-approves-karachi-green-line-metro-bus/ ; https://propakistani.pk/2022/02/10/karachis-green-line-bus-transported-1-million-passengers-in-its-first-month/ | search-result synthesis of multiple news reports | partial |
| lahoremetrobus_thesis | Erasmus University thesis on Lahore Metro Bus Service (no formal performance evaluation found by the thesis author; author/year not confirmed from the snippet). | https://thesis.eur.nl/pub/56561 | search-result synthesis only | unverified — author/year/title not confirmed, treat as a lead |
| bogota_hidalgo2013 | Hidalgo, D. et al. (2013). TransMilenio BRT system in Bogota, high performance and positive impact — main results of an ex-post evaluation. *Research in Transportation Economics*, 39(1). | https://worldtransitresearch.info/research/4437 | search-result synthesis only — abstract-level claims (positive, robust cost-benefit results; declining user perception), no numeric results retrieved | partial |
| curitiba_brt_history | Multiple secondary sources on Curitiba BRT history and cost (Asian Development Bank case study, Streetsblog, Lindau/Hidalgo/Facchini 2010 cited secondhand). | https://www.development.asia/case-study/what-worlds-first-bus-rapid-transit-system-can-teach-us ; https://cal.streetsblog.org/2024/10/17/curitiba-50-years-of-lessons-from-the-worlds-first-bus-rapid-transit | search-result synthesis only; cost figures (~$200-214k/km) explicitly flagged by the search itself as secondary, not primary budget records | partial |
| seoul_busreform2004 | Kim, Cheon & Lim (2011) journal evaluation of Seoul bus reform; Pucher et al. (2005) evaluation (both cited secondhand via search snippets, not opened directly). | https://worldtransitresearch.info/research/4002 | search-result synthesis only | partial — treat both citations as leads, not confirmed existence/details |
| singapore_erp_clarke1998 | Clarke & Wong (1998) on Singapore's pre-ERP traffic control package (cited secondhand, title/year from a student blog's citation, not confirmed against the original). | https://blogs.ubc.ca/smilelaura | search-result synthesis only, one level further removed (a blog's citation of the paper, not the paper itself) | unverified — treat as a lead only |
| pokhara_signals_unused | Rising Nepal Daily report that installed traffic signals in Pokhara are not in use (exact date unclear from search excerpt). | https://risingnepaldaily.com/news/47274 | search-result synthesis only | partial |
| colombo_buslane2017 | Daily Mirror / Sunday Observer 2017 reporting on Colombo's Rajagiriya-Borella priority bus lane pilot and the earlier scrapped Galle Road bus lane. | https://dailymirror.lk/Breaking-News/Priority-bus-lanes-in-force-in-Colombo-from-August/108-134057 | search-result synthesis only | partial |

## Leads to verify (added 2026-10-19, not opened — do not cite as support)

- Dhaka AI-based traffic-camera violation detection (2026 reporting) — single traffic sergeant's account only, not an evaluation.
- Karachi Orange Line ridership figures (3,000 to projected 25,000/day) — operator projection, not yet realized or independently checked.
- Lahore 2014 ridership figures sourced from "largely ministerial tweets" per the search itself — explicitly unreliable, never cite as a number.
- Singapore ERP "15% further traffic reduction" figure — from a student blog citing an unnamed presentation, two levels removed from any primary source.

## Added 2026-10-19 (user-supplied PDF, Satdobato/Gwarko signal optimization — full text read directly, strongest verification level in this project)

| Key | Citation | Link | What was opened | Verified |
|---|---|---|---|---|
| tiwari2024satdobato | Tiwari, S., Khadka, R., Poudel, R., Giri, S., Malla, R.B., Aryal, P., & Pradhananga, R. (2024). Signal Optimization to Improve Traffic Conditions: A Case Study of Satdobato and Gwarko Intersections, Kathmandu Valley. *Nepal Journal of Civil Engineering*, 4(1), 26-38. | user-supplied PDF (NepJOL article id suggested by filename: 672-3-10) | full text (all 13 pages read directly) | yes — directly read, not search synthesis |

Key findings extracted directly from the paper (page references approximate, PDF has no visible page numbers beyond running headers):
- Existing (uncoordinated, field-measured) average delay: **226.5 s/veh at Satdobato, 201.1 s/veh at Gwarko**, both LoS F. After isolated signal-phasing/cycle-time optimization (no new infrastructure): **51.8 s/veh and 52.5 s/veh**, both LoS D — a 77%/74% reduction, independently measured at two real, named Kathmandu Ring Road intersections.
- Calibrated/validated using the same **GEH < 5** criterion this project uses (`scripts/geh_check.py`), applied to basic saturation flow rather than intersection volume — same statistic, different application.
- Field-measured saturation flow rates ranged **1203-2160 veh/hr/lane** across the two intersections' approaches — a real, local cross-check point for this project's own per-link capacity assumptions (A9/A10), not yet used to adjust anything here.
- **Signal coordination between the two intersections was found *less* effective than isolated per-intersection optimization** (network total queue: 578.9 m isolated vs. 606 m coordinated) — the paper's own stated reason is the physical spacing between the intersections reduces platooning benefit. This is an independent, real-world precedent for the same *shape* of finding as this project's own D21 correction: combining two individually-good interventions is not guaranteed to beat the sum of their separate effects, and can be worse.
