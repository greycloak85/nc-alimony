# NC Alimony + Child Support Model

A calibrated quantitative model for North Carolina alimony and child support, with a Streamlit UI for quickly exploring scenarios.

## What it does

Given two gross annual incomes, a kid count, and a custody split, the app produces:

- **Monthly child support** — computed via the official NC [Worksheet B (AOC-CV-628)][wsb] line by line, using the full 774-row [Schedule of Basic Support Obligations (AOC-A-162 Rev. 1/23)][a162].
- **Monthly alimony** — a calibrated weighted-Nash interior formula on post-tax (net) incomes, gated by NC legal constraints: a 40% net-income dependency threshold ([NCGS 50-16.1A][nc161a] operationalized per AAML practice), a de-minimis $1,500/mo gross-gap floor, a smooth self-sufficiency taper, and a no-cross post-hoc adjustment.
- **Side-by-side cash flow** — gross → federal/NC/FICA tax → net → alimony/CS transfers → final monthly take-home for both parties.
- **Sensitivity charts** — sweeps over each party's earnings to verify the work-incentive constraint (no benefit cliffs) and the no-cross constraint (payor never takes home less than recipient).

The model is **post-TCJA aware** — alimony is non-deductible to the payor and non-taxable to the recipient for divorces finalized after 2018-12-31 (per IRC §11051; NC conforms via federal AGI). Tax module: 2025 single-filer federal brackets, NC 4.25% flat (3.99% in 2026), full FICA including 0.9% Additional Medicare on income above $200,000.

## Run locally

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Tests

Regression suite covers the anchor calibration, the 40%-net dependency gate (with a boundary test that locks the threshold), the no-cross invariant across a payor sweep, and monotone payee take-home across a Party A sweep.

```sh
python -m unittest -v test_nc_alimony.py     # 12 tests
python nc_alimony.py                         # embedded examples + sweeps
```

## Calibration anchor

The model is calibrated to a high-water-mark scenario: $285K payor / $0 Party A / 2 kids / 50-50 custody. With a $200/mo judge-deviation health-insurance credit it produces **$4,988 alimony + $2,293 CS** (matching the practitioner-quoted target). With Worksheet B add-ons handled mechanically (no judge deviation, payor pays the $200 health insurance directly per typical NC practice), the same scenario produces **$4,791 alimony + $2,493 CS** — the app's default treatment. The Worksheet B implementation reproduces an attorney-prepared CV-628 to within $0.09 at exact 50/50 overnights.

## Project structure

| File | Role |
|---|---|
| `app.py` | Streamlit UI |
| `nc_alimony.py` | Runnable model (tax + Worksheet B + alimony with gates) |
| `nc_schedule_2023.py` | Full 774-row NC schedule (AOC-A-162 Rev. 1/23) |
| `test_nc_alimony.py` | Regression tests |
| `MODEL.md` | Unified model writeup |
| `ORCHESTRATOR_REPORT.md` | Executive summary |
| `CHALLENGES.md` | Cross-examined disagreements between agent perspectives |
| `AGENT_A_LEGAL.md`, `AGENT_B_ECONOMIC.md`, `AGENT_C_EMPIRICAL.md` | Three independent perspectives that fed the synthesis |
| `requirements.txt` | Streamlit, pandas, altair |

## Disclaimer

This is a planning and negotiation aid, not legal advice. NC alimony is judicial discretion bounded by 16 statutory factors; a judge can deviate from any formula. Consult an NC family-law attorney.

[wsb]: https://www.nccourts.gov/assets/documents/forms/cv628_0.pdf
[a162]: https://www.ncdhhs.gov/css2255a1/download
[nc161a]: https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_50/GS_50-16.1A.html
