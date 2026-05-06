# Task: Modify dependency gate to use net-income basis at 40% threshold

## Context

The current model in `nc_alimony.py` implements an alimony formula with a sequence of legal gates (documented in `MODEL.md`). Gate 2 is the "dependency gate" — a hard-zero gate that fires when the recipient's income share exceeds a threshold of combined income.

As currently implemented, Gate 2 compares **gross** incomes:

```
if G_a / (G_p + G_a) >= 1/3:
    A = 0
```

This has two problems we want to address:

1. **Threshold is too aggressive at 33%.** The orchestrator's original spec called for 40% (per AAML practice and Agent A's reading of NC dependency case law). The 33% number was a pragmatic choice to make Scenario 3 fire; in our actual use case, 33% is more punitive than the legal standard supports.

2. **Gross-income comparison ignores TCJA tax asymmetry.** Post-2018 divorces produce non-deductible alimony for the payor and non-taxable receipt for the recipient. When the payor transfers $1, that $1 has already been taxed at the payor's marginal rate; the recipient consumes it untaxed. "Ability to pay" and "need" are properly measured against post-tax (net) income, not gross. The rest of the model already uses net income for the interior formula — the dependency gate is the only place where gross is used, and it's an inconsistency.

## Required changes

### 1. Replace the gross-income dependency gate with a net-income gate at 40%

**File:** `nc_alimony.py`

**Find Gate 2** in the alimony computation function. It will look something like:

```python
# Gate 2: dependency (33% threshold)
if G_a / (G_p + G_a) >= 1/3:
    return 0  # or set A = 0 and continue
```

**Replace with:**

```python
# Gate 2: dependency (40% threshold, net-income basis)
# Rationale: TCJA makes alimony non-deductible to payor and non-taxable to recipient,
# so "dependency" is properly measured on post-tax income, not gross. Threshold raised
# from 33% to 40% per AAML standard / orchestrator's original spec.
N_p_annual = N(G_p)  # uses canonical net-income function
N_a_annual = N(G_a)
combined_net = N_p_annual + N_a_annual
if combined_net > 0 and (N_a_annual / combined_net) >= 0.40:
    return 0  # match existing zero-return convention for gates
```

If `N(...)` is named differently in `nc_alimony.py` (e.g., `net_income`, `compute_net`, or inlined), use whatever the existing canonical net-income function is — do not introduce a parallel implementation.

If the existing code structure sets `A = 0` and continues through subsequent gates rather than returning early, preserve that flow control style; just change the condition.

### 2. Update MODEL.md to reflect the change

**File:** `MODEL.md`

In the section "Gate sequence — the 33% dependency gate as the headline lever":

- Rename the section header from "33%" to "40% net".
- Replace the gate-2 paragraph. Current text:

  > **Dependency gate (33% threshold) — the headline lever.** If G_a / (G_p + G_a) ≥ 1/3, A = 0. NCGS 50-16.1A defines a "dependent spouse" qualitatively; we operationalize at 1/3 (NC practitioner heuristic). The orchestrator's spec said 40 %; we use 33 % so that **Scenario 3** ...

  Replace with:

  > **Dependency gate (40% threshold, net-income basis) — the headline lever.** If `N(G_a) / (N(G_p) + N(G_a)) ≥ 0.40`, A = 0. NCGS 50-16.1A defines a "dependent spouse" qualitatively; we operationalize at 40% per AAML practice and the orchestrator's original spec. The threshold is computed on **net** (post-tax) incomes rather than gross, because TCJA renders alimony non-deductible to the payor and non-taxable to the recipient — "ability to pay" and "need" are properly measured against the post-tax pile each party actually consumes. Using net rather than gross also harmonizes Gate 2 with the rest of the model, which uses N(·) throughout the interior formula.

- Update the worked-example tables for Scenario 3, Scenario 4, Stress 1, and Stress 4 to reflect the new gate. Recompute `N_a / (N_p + N_a)` for each:
  - **Scenario 3** ($150K / $80K, 1 kid): under the new rule, the gate now compares N($150K)=$107,608 to N($80K)≈$60,000-something. Recompute the ratio; if it's below 40%, the gate no longer fires here and alimony is non-zero. Update the row in the worked-examples table to reflect actual interior formula output.
  - **Scenario 4** ($80K / $60K, 0 kids): recompute. Likely still gated by de-minimis floor (Gate 3) even if dependency gate (Gate 2) no longer fires.
  - **Stress 1** (role reversal $50K / $200K): recompute. Should still produce A=0 since the labeled "payor" is the lower earner; gate fires by virtue of N_a > N_p giving N_a / combined > 0.5.
  - **Stress 4** (equal incomes $150K / $150K): N_a / combined = 0.5 ≥ 0.40, gate still fires, A=0.
- Update the disagreements table row "Dependency operationalization" to reflect that we are now adopting Agent A's 40% number on net-income basis.
- Add a row to the "Pathologies" section noting that the threshold has been raised; old test cases relying on the 33% number should be re-validated.

### 3. Re-run the verification sweeps and update the sweep tables

**File:** `MODEL.md`

The sweep tables in "Verification of all four hard constraints — sweep tables" need to be regenerated under the new gate. In particular:

- **Sweep 1** (G_p = $285K, vary G_a from $0 to $200K): the gate now fires later (at higher G_a). Find the G_a value at which `N(G_a) / (N($285K) + N(G_a)) ≥ 0.40` and update the table so alimony zeroes at the new crossing point rather than the old one. The smooth self-sufficiency taper should already drive alimony toward zero before the gate fires; verify there is no new monotonicity violation introduced by the threshold change.
- **Sweep 2** (G_a = $0, vary G_p): unchanged. With G_a = 0, the dependency ratio is always 0%; the gate never fires.

Re-run both sweeps and replace the tables with the new values.

### 4. Re-run the anchor verification

**File:** `MODEL.md`, "Calibration" section

The anchor case ($285K / $0 / 2 kids / 50-50) is unaffected by Gate 2 (G_a = 0 means the dependency ratio is 0% regardless of gross/net basis or threshold). Confirm `w = 0.545` still produces $4,988 ± $12 alimony and $2,293 ± $7 CS at the anchor. No recalibration of `w` is needed.

### 5. Add a regression test

**File:** create or extend a test file (`test_nc_alimony.py` if it exists, otherwise create one)

Add tests covering:

- **Anchor case** still produces ~$5,000 alimony, ~$2,300 CS (unchanged from prior).
- **New Scenario 3** ($150K / $80K, 1 kid): alimony is now non-zero (the previous 33% gross gate fired here; the new 40% net gate should not). Assert A > 0.
- **Boundary test:** find a (G_p, G_a) pair where `N_a / (N_p + N_a) = 0.40 ± epsilon`. Assert that the gate fires at +epsilon and does not fire at -epsilon. This locks in the threshold.
- **Equal incomes** ($150K / $150K): A = 0 (gate still fires).
- **Role reversal** ($50K payor / $200K Party A): A = 0 (gate fires).

### 6. Tax module note (do NOT implement, just document)

In MODEL.md "Pathologies and known failure modes," **expand item 6** ("Tax module assumes W-2 employee FICA"). Add:

> The tax module is hard-coded to 2025 single-filer brackets. For applications running in 2026 or later — or for parties with substantial 1099/self-employment income — the model needs (a) updated bracket cutoffs and standard deductions, (b) NC's 3.99% rate (already noted as a one-line config change), and (c) doubled FICA on self-employment income (both employer and employee halves). For the current planned use as a quarterly recalculation tool against parties whose income mix shifts between W-2 and self-employment, this needs to be addressed before production use; the canonical net-income function `N(G)` should accept an `is_self_employed_share` parameter representing the fraction of G subject to doubled FICA, default 0.

Do not implement these changes in this task — flag them as a follow-up. The dependency-gate change should land first, validated, and committed before the tax-module work begins.

## Out of scope for this task

- Calibration of `w` (do not recompute or adjust)
- Above-$40K-combined CS extrapolation rule
- Marital-lifestyle cap
- Duration model
- Streamlit UI changes (the formula change should propagate to the UI automatically through the underlying computation)
- The 2026 tax-module update (flagged as follow-up only)

## Acceptance criteria

1. `nc_alimony.py` Gate 2 uses net-income comparison at 0.40 threshold.
2. MODEL.md gate-2 section, worked examples (Scenarios 3 and 4, Stresses 1 and 4), disagreements table, sweeps, and pathologies section all reflect the change.
3. Regression tests pass, including the boundary test that locks the 0.40 threshold.
4. Anchor case still reproduces $4,988 ± $12 alimony, $2,293 ± $7 CS.
5. Sweep 1 monotonicity holds; no new no-cross violations introduced.
6. A clean commit with message: `Gate 2: 33% gross → 40% net dependency threshold (TCJA-consistent, AAML standard)`.
7. The commit hash is captured for inclusion in the consent order's Attachment B (which references the formula version by hash).

## Why these changes (for the commit message body)

The dependency gate previously fired when the recipient's *gross* income share reached 33% of combined gross. Two issues:

(a) Gross-income comparison is internally inconsistent with the rest of the model, which computes the interior alimony formula on *net* (post-tax) income. Post-TCJA (divorces after 12/31/2018), alimony is non-deductible to the payor and non-taxable to the recipient — so "dependency" measured against gross overstates the recipient's actual consumption power relative to the payor's, biasing the gate toward early firing.

(b) The 33% threshold was lower than the AAML practitioner standard (40%) the orchestrator originally specified. The 33% was a calibration to a specific scenario; for use in negotiated settlements it produces a hard zero at income ratios where alimony would still be appropriate under standard NC practice.

The fix harmonizes Gate 2 with the rest of the model (net income throughout) and restores the intended 40% threshold. The combined effect is a meaningfully softer gate that fires only when the recipient's post-tax income is at least 40% of combined post-tax income.
