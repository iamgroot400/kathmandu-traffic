# AI-use disclosure

[TODO(author): check JACEM's actual AI-use disclosure policy/required wording before submission — this draft states what was done, in plain terms, but has not been checked against a specific venue requirement. See the **publish-path** skill if a more formal check is needed.]

An AI assistant (Claude, Anthropic) was used throughout this project's research process, under the direction and review of the human author, as follows:

- **Simulation code**: all scripts (network import, demand generation, signal/pricing/tidal-flow/sensitivity levers, statistical comparison) were written by the AI assistant, run by the assistant in an interactive session with the author, and reviewed by the author at each step.
- **Experimental design**: hypotheses (H1–H7), falsification criteria, and statistical methodology (paired-seed design, 95% confidence intervals) were proposed by the assistant and approved by the author before each experiment ran.
- **Literature search and citation verification**: web searches were conducted by the assistant; citations were checked against their actual sources (not generated from memory) and QA-audited for fabrication, which caught and corrected one invented DOI mid-project (see `lab/qa/2026-10-17-qa.md`).
- **Data analysis and interpretation**: result decomposition (e.g., checking for completion-bias artifacts before trusting raw statistics) was performed by the assistant; the author directed which follow-up checks to run.
- **This manuscript's drafting**: all prose in this paper was drafted by the assistant from the project's recorded evidence (`lab/experiments/`, `lab/decisions.md`, `lab/paper/claims.md`), following a claim ledger that graded every statement's evidentiary strength before drafting began. No results, numbers, or citations were invented; gaps are marked `[TODO]` rather than filled with unverified content.

**The author is responsible for this paper's content.** The author has not yet independently verified the claims/numbers listed in the handover checklist (Section below, or see `lab/paper/handover.md` once written) and must do so before submission. This disclosure itself requires the author's review and sign-off before being included in any submission.
