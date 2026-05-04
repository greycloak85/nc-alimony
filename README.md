# NC Alimony + Child Support Model

A calibrated quantitative model for North Carolina alimony and child support, with a Streamlit UI for quickly exploring scenarios.

## What it does

Given two gross annual incomes, a kid count, and a custody split, the app produces:

- **Monthly child support** — computed via the official NC [Worksheet B (AOC-CV-628)][wsb] line by line, using the full 774-row [Schedule of Basic Support Obligations (AOC-A-162 Rev. 1/23)][a162].
- **Monthly alimony** — a calibrated weighted-Nash interior formula on post-tax incomes, gated by NC legal constraints (33% dependency threshold per [NCGS 50-16.1A][nc161a], de-minimis floor, smooth self-sufficiency taper, and a no-cross post-hoc adjustment).
- **Side-by-side cash flow** — gross → federal/NC/FICA tax → net → alimony/CS transfers → final monthly take-home for both parties.
- **Sensitivity charts** — sweeps over each party's earnings to verify the work-incentive constraint (no benefit cliffs) and the no-cross constraint (payor never takes home less than recipient).

## Run locally

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Methodology

See `MODEL.md` for the unified model writeup, `ORCHESTRATOR_REPORT.md` for the executive summary, `CHALLENGES.md` for the cross-examined disagreements, and `AGENT_*.md` for the three independent perspectives that fed the synthesis.

The Worksheet B implementation reproduces an attorney-prepared CV-628 to within $0.09 at exact 50/50 overnights.

## Disclaimer

This is a planning and negotiation aid, not legal advice. NC alimony is judicial discretion bounded by 16 statutory factors; a judge can deviate from any formula. Consult an NC family-law attorney.

[wsb]: https://www.nccourts.gov/assets/documents/forms/cv628_0.pdf
[a162]: https://www.ncdhhs.gov/css2255a1/download
[nc161a]: https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_50/GS_50-16.1A.html
