# Part VIII — The Super-Additivity Correction

This part is, by a wide margin, the most important single episode in this project's
history, and it is given full, dedicated treatment here rather than a brief mention,
because the *process* that caught and corrected this error is a more valuable lesson
than almost any individual numerical result in this manual.

## Chapter 29: What We Originally Believed

### The claim

For most of this project's working life, its central, headline claim was that
combining adaptive signal control and congestion pricing produced a **super-additive**
interaction — an effect larger than the simple sum of what each lever achieves alone.
Concretely, the originally reported numbers were: the combined lever reduced delay by
**65.3 percent**, which was compared against a claimed **"48.6 percent predicted under
independence"** — the number the two levers' individual effects would supposedly add
up to if they worked completely separately, with no interaction between them. Because
65.3 percent exceeded that 48.6 percent figure, the project's working conclusion was
that the two levers *reinforce* each other: pricing relieves enough congestion that
adaptive signal control gains extra room to maneuver, producing more benefit together
than the two could ever produce run separately.

### Why this would have mattered, if true

A genuine super-additive interaction would have been a substantive, mechanistic
finding — not just "both levers help," which is already true and unremarkable, but
"deploying them *together* unlocks an effect neither could achieve alone," which is a
specific, falsifiable claim about how the two interventions interact inside the
network. This is precisely the kind of result that would be worth a paper's headline
claim, which is exactly why it had become this project's headline claim.

---

## Chapter 30: How the Error Was Found

### Where it was hiding

The error was not found by someone doubting the conclusion and going looking for a
flaw. It was found as a direct, almost incidental consequence of a completely
different task: **drafting the academic paper itself.** Writing the paper's Methods
section required stating, in exact, checkable prose, precisely how the "48.6 percent
predicted under independence" figure had been computed — and in trying to write that
sentence honestly, it became clear that **no one could actually reproduce it.**

### The reconstruction attempt

Once the discrepancy was noticed, this project tried, by hand, every reasonable
method that might have originally produced 48.6 percent:

- A **naive sum** of the two levers' individual mean percentage reductions
  (24.50% + 31.89%) does not give 48.6% — it gives **56.39%**.
- A **per-seed paired sum** (compute the interaction-relevant sum on each individual
  seed, then average across seeds) also gives **56.39%**, the same answer, not a
  different one — ruling out "maybe the naive sum and the proper sum just happen to
  differ" as an explanation.

Neither reconstruction reproduced the original 48.6 percent figure, by any
derivation. The honest conclusion, reached directly rather than avoided: the specific
statistical test this project's own experiment card had *said* it would run, before
any run was made, had apparently **never actually been run** — the number that ended
up being reported and compared against was not the output of the stated methodology at
all.

### Why this was caught at all

This is worth dwelling on, because it is the clearest possible demonstration of why
this project's broader quality-assurance discipline exists. The specific mechanism
that caught this was a dedicated, adversarial `qa-check` audit pass of the paper draft
— a process whose explicit job is to challenge, not confirm, every claim, by tracing
each one back to the specific result file and computation that supposedly produced
it. This is exactly the audit step this project's own paper-writing process requires
*before* any draft is finalized, and it worked precisely as intended — just later in
the project's life than would have been ideal, since the uncorrected claim had
already propagated outward into other project materials (the hackathon writeup
document and pitch deck) before being caught. Both of those were corrected
immediately once the error was identified, rather than left inconsistent with the
corrected paper.

---

## Chapter 31: The Correct Test

### What should have been computed all along

The actual, correct test for a super-additive interaction is a specific, well-defined
per-seed quantity: for each seed $s$, define each lever's own paired delay change
relative to the fixed-time baseline as $\Delta_{\text{adaptive}}(s)$,
$\Delta_{\text{pricing}}(s)$, and $\Delta_{\text{combined}}(s)$. The **interaction
term** is:

```latex
I(s) = \Delta_{\text{combined}}(s) - \big(\Delta_{\text{adaptive}}(s) + \Delta_{\text{pricing}}(s)\big)
```

If the two levers' effects were purely additive (no interaction at all),
$I(s)$ would be zero on every seed, on average. A reliably *negative* $I(s)$ (since
delay reductions are negative numbers in this project's sign convention) would
indicate super-additivity — the combined effect is more negative, i.e. a larger
reduction, than the sum of the two parts.

### The actual result, computed properly this time

Computed directly and correctly from the project's own real, per-seed result file,
this interaction term comes out to:

```latex
\bar{I} = -185.3 \pm 275.6 \text{ seconds} \qquad (t = -1.44,\ df = 14)
```

with **9 of 15 seeds** agreeing in sign — not a unanimous or even strongly consistent
majority, and critically, the 95 percent confidence interval **includes zero.** By the
project's own pre-stated statistical standard (Chapter 27: a confidence interval that
excludes zero, ideally with near-unanimous seed agreement), **this is not a
statistically supported finding.** The super-additivity claim is, properly tested,
**falsified by its own stated criterion** — not merely "unproven," but actively
contradicted by the correct version of the test the project itself had committed to
running.

### What remains true, and what does not

It is essential to be precise about exactly what this correction does and does not
undo. The combined lever's own effect — a **65.30 percent reduction in delay,
measured directly, with all 15 seeds agreeing in direction** — is completely real,
strong, and entirely unaffected by this correction. What is specifically wrong is only
the *comparison* claim: that this combined effect exceeds what the two levers would
have produced *independently*. The project's revised, correct headline is therefore:
**the combined lever is this project's strongest single intervention, full stop — not
because the two levers synergize with each other, which this project does not find
support for, but simply because applying both together removes more delay than either
one alone.** This is a smaller, more modest claim than the original one — and it is
the true one.

---

## Chapter 32: What This Teaches About Self-Correction

### The discipline that made this possible

None of this correction would have happened without several specific, deliberate
practices this project had already put in place *before* the error was ever
introduced:

1. **Writing the prediction down before running the test** (an experiment card's
   stated methodology, written in advance) is what made it *detectable* that the
   actual number reported did not match that stated methodology — if the methodology
   had only ever existed as an informal verbal description, the mismatch might never
   have become visible as a concrete, checkable discrepancy.
2. **A dedicated, adversarial audit step**, run specifically to challenge claims
   rather than to confirm them, caught what an author re-reading their own work,
   looking to confirm it is correct, is structurally prone to miss.
3. **An append-only decision log** (`lab/decisions.md`) meant the correction itself
   could be recorded fully — the original claim, why it was wrong, exactly how the
   correct number was derived, and every downstream document that needed fixing as a
   result — rather than simply overwriting the old, wrong number and losing the
   history of what happened and why.

### The discipline this correction then reinforced

Having been burned once by an unverified, hard-to-reproduce comparison number, this
project became visibly more careful afterward about a specific failure mode: **never
keep adjusting a method after seeing results, in search of whichever version happens
to support a predetermined conclusion.** This exact concern resurfaces explicitly, by
name, in this project's later robustness and validation work (Part IX's validation
discussion, and Part X's capacity-sensitivity sweep both invoke this same episode as
the reason a tempting-but-circular "just keep tuning until the numbers look right"
approach was explicitly rejected in favor of a harder, more honest standard: decide
the test's methodology *before* running it, run it exactly once as specified, and
report whatever it says — even when what it says is that a previously-reported,
central finding was wrong.
