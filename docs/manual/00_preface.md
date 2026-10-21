# Preface

This manual exists to answer one question completely: **why does this project's
simulation work the way it does, in every single detail, from the underlying
physics up to the last line of reported evidence?**

It is written for a reader who may never have heard the phrase "mesoscopic traffic
simulation" before opening this document, and who should be able to reach the final
page understanding not only *what* this project built, but *why* every individual
choice inside it was made the way it was, what the rejected alternative would have
cost, and where the project's own evidence still falls short.

### How this manual is organized

Fourteen parts, each building on the ones before it:

- **Parts I-II** lay the theoretical and architectural groundwork: traffic flow
  theory from first principles, why this project's specific simulator was chosen
  over its alternatives, and how the road network itself was built and cleaned.
- **Parts III-V** cover how demand and route choice are modeled.
- **Part VI** walks through every single intervention this project tested — not
  only the two that became its headline results, but every one that was tried and
  rejected, with the specific, diagnosed reason each failure happened.
- **Part VII** teaches the statistical discipline that runs underneath every
  number in this project — why a single simulation run can never be trusted alone,
  and the specific, recurring trap (completion bias) this project had to learn to
  guard against repeatedly.
- **Part VIII** is a complete account of this project's single most important
  episode: a central, headline claim that was believed for most of the project's
  life, discovered to be wrong, and corrected in the open, with the full reasoning
  of how the error happened preserved rather than quietly erased.
- **Parts IX-X** cover how the model was checked against real-world data, and how
  robust its conclusions are to its own untested assumptions.
- **Part XI** steps outside this project's own simulation entirely, to ask what
  independent, real-world evidence — from a separate academic study of real
  Kathmandu intersections, and from fourteen other cities' own documented
  experience — says about these same questions.
- **Part XII** looks forward, asking what happens if nothing changes.
- **Part XIII** is a practical reference to the software itself, script by script.
- **Part XIV** closes honestly, with what this project would do differently and
  what remains genuinely unresolved.
- The **Glossary and Appendices** that follow exist specifically so that no term,
  assumption, or decision referenced anywhere in this manual is ever left
  unexplained — if something in the body of this manual assumes knowledge you do
  not have, it should be recoverable there.

### A note on how to read the numbers

Every number in this manual traces back to a result a script in this project's
repository actually produced — never a number typed by hand and never an estimate
offered without its source named. Where a finding carries a caveat (a small sample
size, an untested assumption, a confound this project did not resolve), that
caveat is stated in the same breath as the finding itself, not buried in a separate
limitations section at the end. This is a deliberate editorial choice, consistent
with how this project has tried to conduct its research throughout: a result and
its honest limitation belong together, because a reader who sees only one of the
two has not actually been told the whole truth.
