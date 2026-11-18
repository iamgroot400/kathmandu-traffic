# paper/

| File | What it is |
|---|---|
| `kathmandu_traffic_paper.pdf` | **the paper**, built by `build_pdf.py` |
| `main.tex`, `sections/*.tex`, `references.bib` | the same paper in LaTeX (`pdflatex main && bibtex main && pdflatex main && pdflatex main`) |
| `claims.md` | **claim ledger**: every number, its Kaggle notebook, output file and computation |
| `numbers.tex` | LaTeX macros for every simulated number, used by `sections/*.tex` |
| `evidence.py` | writes `claims.md`, `numbers.tex` and the README results table from `results/clean/` |
| `build_pdf.py` | builds the PDF from `results/clean/`; stops if the text's significance wording or equal-vehicle checks no longer hold |
| `figures/make_charts.py` | `fig_jica_validation.png` (Figure 1) and `fig_jica_levers.png` (Figure 2) from `results/clean/` |
| `ai-disclosure.md` | how an AI assistant was used |

The PDF and the LaTeX share their numbers through the same functions (`jica_numbers`,
`sweep_numbers`, `projection_numbers` in `build_pdf.py`). Their prose is kept in step by hand.

**From the study's first version** (synthetic demand, main roads only), kept for comparison:
`build_pdf_v1_arterial.py`, `kathmandu_traffic_paper_v1_arterial.pdf`, `short_paper.md`,
`figures/table_*.py|tex`, `figures/make_capacity_chart.py`, and `fig_core/geh/additional/sensitivity/capacity_sweep.png`.
`old_numbers()` in `build_pdf.py` reads that version's `results/comparison.partial.csv`, which is
a local run, not part of the public Kaggle run. The paper says so wherever it uses it.
