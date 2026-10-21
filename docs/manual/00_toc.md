# The Kathmandu Traffic Simulation: A Complete Manual

## Table of Contents

Preface

**Part I — Foundations**
1. Why This Project Exists
2. Traffic Flow Theory, From the Ground Up
3. Choosing a Simulator: UXsim and Its Alternatives
4. How the Pieces Fit Together: Project Architecture

**Part II — Building the Network**
5. Getting Real Roads from OpenStreetMap
6. Cleaning the Network: Node Merging and Connectivity
7. Placing Traffic Signals

**Part III — Modeling Demand**
8. The Gravity Model, Explained
9. Zones: Where Trips Start and End
10. Vehicle Mix and Passenger Car Equivalents
11. Scaling Demand to a Loadable Level

**Part IV — Calibration**
12. The Free-Flow Speed Override
13. Jam Density: What It Means and Why 0.2
14. Calibrating Against Reality
15. The Identifiability Problem

**Part V — How Vehicles Choose Routes**
16. Dynamic User Optimum vs. Dynamic User Equilibrium

**Part VI — The Interventions**
17. The Fixed-Time Baseline
18. Adaptive Signal Control
19. Congestion Pricing
20. Tidal-Flow Lanes (Rejected)
21. Parking and Encroachment Enforcement (Rejected)
22. Staggered Departures (Supported)
23. Decentralized Attraction (Supported, Confounded)
24. Cordon Demand (Abandoned)

**Part VII — Statistical Methodology**
25. Why One Simulation Run Proves Nothing
26. Paired Seeds and Confidence Intervals
27. Multiple Comparisons
28. Completion Bias: The Project's Recurring Trap

**Part VIII — The Super-Additivity Correction**
29. What We Originally Believed
30. How the Error Was Found
31. The Correct Test
32. What This Teaches About Self-Correction

**Part IX — Validation Against Reality**
33. The GEH Statistic
34. Where the Observed Data Came From
35. What 2 of 6 Passing Actually Means
36. A Single-Seed Spot-Check

**Part X — Sensitivity and Robustness**
37. The ±20% Parameter Sweep
38. The Capacity-Sensitivity Sweep

**Part XI — Grounding the Model in the Real World**
39. Independent Field Validation: Tiwari et al. (2024)
40. What Fourteen Other Cities Taught Us
41. Why Congestion Pricing Is Not Recommended Yet

**Part XII — Looking Forward**
42. Projecting Five Years of Demand Growth
43. Density, Bridges, and Chain-Reaction Jams

**Part XIII — The Software Itself**
44. Repository Tour
45. Script-by-Script Reference
46. Reproducibility and Determinism

**Part XIV — Closing**
47. What We Would Do Differently
48. Open Questions

Glossary

Appendix A — The Complete Assumption Register

Appendix B — The Complete Decision Log
