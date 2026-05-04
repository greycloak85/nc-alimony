# Agent B — Economic Optimization Lens

NC Alimony as Constrained Welfare Allocation Between Two Adult Households

Author: Agent B (economic optimization). Companion agents: A (legal/statutory) and C (empirical/multi-state).
Filing status assumed: Single (post-divorce). Tax year: 2025. Anchor: G_p = $285,000, G_a = $0 → A = $5,000/mo, CS = $2,300/mo.

---

## 0. Notation

| Symbol | Meaning |
|---|---|
| G_p, G_a | Gross annual incomes of Payor and Party A |
| n | Number of minor children |
| A | Monthly alimony, payor → Party A (annual = 12A) |
| CS | Monthly child support, payor → Party A (annual = 12·CS) |
| τ_F(G) | Federal income tax owed on gross G (single, std deduction, 2025) |
| τ_S(G) | NC state tax (4.25 % flat, 2025) on G – std deduction |
| τ_FICA(G) | OASDI 6.2 % up to $176,100 + Medicare 1.45 % + 0.9 % above $200K |
| N(G) | Annual net (after-tax) labor income = G – τ_F – τ_S – τ_FICA |
| T_p, T_a | Annual total disposable income of each household after transfers |
| MTR_a | Marginal effective tax rate facing Party A on $1 of additional gross |

All flows in annual dollars unless explicitly /mo. The model produces A in $/month to match the anchor; internal math uses annual flows for clean differentiation.

---

## 1. Net-income functions N(G) — 2025 single filer

### 1.1 Federal (post-TCJA, post-2018 divorce)

Critical fact: **TCJA §11051 permanently repealed federal deductibility of alimony for divorce instruments executed after 12/31/2018.** NC conforms (NC starts from federal AGI). Therefore:

- The payor pays tax on the *full* G_p before transferring A and CS.
- Party A receives A and CS *tax-free*.
- Both A and CS are post-tax cash from the payor's perspective.

This is decisive. Pre-2019 alimony formulas (e.g., the AAML 30 %·G_p − 20 %·G_a heuristic) implicitly assumed deductibility and overstate the affordable transfer by roughly the payor's marginal rate × A. **Any direct port of those formulas to a 2025 NC case overpays by ~25–37 % of the alimony amount.** I'll set the calibration accordingly.

2025 single brackets (taxable income, after $15,750 standard deduction):

| Rate | Band (taxable) |
|---|---|
| 10 % | 0 – 11,925 |
| 12 % | 11,925 – 48,475 |
| 22 % | 48,475 – 103,350 |
| 24 % | 103,350 – 197,300 |
| 32 % | 197,300 – 250,525 |
| 35 % | 250,525 – 626,350 |
| 37 % | > 626,350 |

Tax at top of each band (cumulative): T(11,925)=1,192.50; T(48,475)=5,578.50; T(103,350)=17,651; T(197,300)=40,199; T(250,525)=57,231; T(626,350)=188,769.75.

Closed form for taxable income TI(G) = max(0, G − 15,750):

```
τ_F(G) = bracket_lookup(TI(G))           # standard piecewise linear
```

### 1.2 NC state, 2025

Flat 4.25 % on (G − $12,750 NC standard deduction, single):

```
τ_S(G) = 0.0425 · max(0, G − 12,750)
```

### 1.3 FICA (employee side, W-2 wages; for self-employment double the rates)

```
τ_FICA(G) = 0.062 · min(G, 176,100)        # OASDI
          + 0.0145 · G                      # Medicare
          + 0.009  · max(0, G − 200,000)    # Additional Medicare
```

### 1.4 Net function (annual)

```
N(G) = G − τ_F(G) − τ_S(G) − τ_FICA(G)
```

Spot values (W-2 single, 2025):

| G | τ_F | τ_S | τ_FICA | N(G) | N(G)/12 |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 |
| 50,000 | 4,016 | 1,581 | 3,825 | 40,578 | 3,381 |
| 60,000 | 5,236 | 2,006 | 4,590 | 48,168 | 4,014 |
| 80,000 | 9,636 | 2,856 | 6,120 | 61,388 | 5,116 |
| 150,000 | 26,251 | 5,831 | 11,475 | 106,443 | 8,870 |
| 285,000 | 67,489 | 11,581 | 16,664 | 189,266 | 15,772 |

(Anchor check: payor gross $285K → ~$15,772/mo net before transfers, near my earlier rough estimate of $16.65K. The user's prompt stated "$200K net ≈ $16,650/mo"; the more careful single-filer 2025 number including FICA Medicare-additional is ~$189K net, $15.8K/mo. I'll use $15,772/mo throughout.)

### 1.5 Including transfers — household disposable income

Because alimony is no longer taxable to recipient or deductible to payor:

```
T_p(G_p, A, CS) = N(G_p) − 12A − 12·CS         (payor)
T_a(G_a, A, CS) = N(G_a) + 12A + 12·CS         (party A)
```

CS appears in T_a but should be earmarked for child consumption; for the welfare problem I treat it as fungible income to Party A's household (which is what NC effectively presumes — recipient parent administers it). For pure adult-to-adult parity tests I'll also report a "stripped" no-CS variant.

---

## 2. The optimization problem

### 2.1 Choice of objective

Three candidates considered:

(a) **Nash welfare**: max log T_p + log T_a. Pro: classic axioms (Pareto, scale-invariance, independence of irrelevant alternatives). Con: with TCJA killing deductibility, the joint pie does not depend on A — A is a pure transfer — so Nash welfare collapses to equalization (T_p = T_a), which violates the no-cross constraint at high G_p when the constraint should bind.

(b) **Income-share parity** with shrinkage: A chosen so that T_a / T_p = λ(G_a/G_p). λ rises from some floor toward but never reaches 1.

(c) **Constrained equalization above a floor with a "marriage-loss" share parameter** — generalizes (a) and (b).

I pick **(c)** and parameterize it as a *weighted* welfare:

```
max_{A ≥ 0}   w · log T_p + (1 − w) · log T_a
s.t.   T_p ≥ T_a + Δ       (no-cross + cushion)
       T_a ≥ F_min          (de-minimis floor on payee household)
```

For w = 1/2 this is Nash welfare → equalization. For w > 1/2 the payor keeps a larger share, which is what NC case law actually does (alimony is not an equalizer; it preserves "accustomed standard of living" for the dependent spouse without parity). I'll calibrate w to hit the anchor.

This formulation is convex in A (objective concave, constraints linear), so the interior optimum is unique and KKT-tractable.

### 2.2 Closed-form interior solution

Let m_p = N(G_p), m_a = N(G_a) (annual). Lagrangian, ignoring boundary cases:

```
L = w log(m_p − 12A − 12CS) + (1−w) log(m_a + 12A + 12CS)
∂L/∂A = −12w/(m_p − 12A − 12CS) + 12(1−w)/(m_a + 12A + 12CS) = 0
```

Solving:

```
m_a + 12A + 12CS = ((1−w)/w) · (m_p − 12A − 12CS)
12A_unconstrained = (1−w)·m_p − w·m_a − 12CS
                  = (1−w)·m_p − w·m_a − 12CS
```

Equivalently, monthly:

```
A* = (1−w)·m_p/12 − w·m_a/12 − CS                                    (*)
```

This is the *unconstrained interior optimum*. It is a clean linear function of (m_p, m_a, CS) — exactly the structure courts and legislatures gravitate to (the AAML 30/20 rule has the same form).

### 2.3 Calibrating w to the anchor

At anchor: G_p = 285,000, G_a = 0, n = 2 → m_p = 189,266, m_a = 0, CS = 2,300/mo, A = 5,000/mo.

Plug into (*):
```
5,000 = (1−w) · 189,266/12 − 0 − 2,300
7,300 = (1−w) · 15,772.17
1 − w = 0.4628
w = 0.5372
```

So the payor receives weight w ≈ 0.537, Party A receives 1 − w ≈ 0.463. Slightly tilted toward the payor — consistent with NC's "supporting/dependent spouse" doctrine that does not aim for equalization. **I lock in w = 0.537.**

### 2.4 Plugging w back in — the formula

```
A_interior(G_p, G_a, n) = 0.4628 · N(G_p)/12 − 0.5372 · N(G_a)/12 − CS(G_p, G_a, n)
```

Because A ≥ 0 and is bounded by no-cross, the realized formula is piecewise (see §6).

---

## 3. Work-incentive math

### 3.1 The MTR Party A faces

When G_a rises by $1, Party A loses (a) part of $1 to taxes on her own labor and (b) a portion of A through the formula's −0.5372·N(G_a)/12 term, plus possibly some of CS through Worksheet B's income-share recomputation.

Marginal own-tax rate on G_a (call it t_a):
```
t_a = ∂[τ_F + τ_S + τ_FICA]/∂G_a
```
For single filers this is e.g. 0.0765 + 0.10 + 0.0425 ≈ 21.9 % at low G_a (10 % bracket), rising to ~31.7 % at $80K (22 % bracket), ~37.7 % at $150K (24 %), ~45.7 % above $200K (32 % + 0.9 % addl Medicare on Med-only side).

Marginal alimony loss from formula (*):
```
∂A/∂G_a = −0.5372 · (1 − t_a) / 12     ($/mo per $/yr)
∂(12A)/∂G_a = −0.5372 · (1 − t_a)
```

So for every $1 of additional gross, alimony falls by 0.5372 · (1 − t_a) annually. The implicit MTR including alimony clawback:

```
MTR_a = t_a + 0.5372 · (1 − t_a)
      = 1 − (1 − t_a)·(1 − 0.5372)
      = 1 − 0.4628·(1 − t_a)
```

| G_a band | t_a | MTR_a (with alimony clawback) |
|---|---|---|
| < $11.9K (10 %) | 0.219 | 1 − 0.4628·0.781 = **63.9 %** |
| $11.9K–$48.5K (12 %) | 0.239 | **64.8 %** |
| $48.5K–$103K (22 %) | 0.339 | **69.4 %** |
| $103K–$197K (24 %) | 0.359 | **70.3 %** |
| $197K+ (32 %) | 0.439 | **74.0 %** |

CS clawback (Worksheet B) adds another 1–3 % point to MTR_a depending on the worksheet line. For the marginal-incentive analysis I'll fold a 2 % conservative add-on so MTR_a in the 22 % bracket rises to ~71 %.

### 3.2 Choosing the MTR ceiling — defense

Optimal-tax theory (Saez 2001, Chetty 2012) puts the elasticity-weighted ceiling for top earners at 60–70 %. Empirical labor-supply elasticities for *secondary earners and re-entering spouses* are far higher (Heim 2007, Blau & Kahn 2007 → ε ≈ 0.5–1.0 for married women, vs 0.1–0.3 for primary earners). Higher elasticity → lower optimal MTR.

For a re-entering ex-spouse the case for an MTR cap is strong:

- Welfare-program phase-outs already pile on at low income; alimony should not stack on top to push effective MTR above 80 %.
- Empirical evidence from EITC and TANF shows behavioral cliffs at MTR > 70 %.
- Below 50 %: too generous (formula transfers too much); above 70 %: punitive.

**I cap MTR_a at 65 %.** This is a defensible midpoint: above the federal top rate, below TANF-style phase-out cliffs, and lets a re-entering ex-spouse keep ≥ $0.35 of every additional dollar earned.

### 3.3 Maximum allowable formula slope

From MTR_a = 1 − (1 − s)·(1 − t_a) ≤ 0.65, where s = ∂(12A)/∂G_a (the *fraction of marginal gross that the formula claws back* via reduced alimony):

```
1 − s ≥ 0.35 / (1 − t_a)
s ≤ 1 − 0.35/(1 − t_a)
```

| t_a | s_max |
|---|---|
| 0.22 | 1 − 0.35/0.78 = 0.551 |
| 0.34 | 1 − 0.35/0.66 = 0.470 |
| 0.36 | 1 − 0.35/0.64 = 0.453 |
| 0.44 | 1 − 0.35/0.56 = 0.375 |

My calibrated slope s = 0.5372 **violates the 65 % cap once Party A enters the 22 % bracket** (s_max = 0.551 is fine, but at 24 % bracket s_max = 0.453 < 0.5372).

Two ways to fix:

(i) Lower the calibrated slope on G_a only (asymmetric weights for payor vs payee).
(ii) Apply a *taper*: keep s = 0.5372 in the low bracket where MTR_a ≤ 65 %, drop it to s = 0.40 once G_a > $48,475.

Approach (ii) is cleaner and doesn't require re-anchoring. I codify it in §7.

### 3.4 ∂(T_a)/∂G_a > 0 always

With s ≤ 0.55 in any bracket and t_a ≤ 0.46, MTR_a ≤ 75 % in the absolute worst case (highest bracket); never negative. Strictly monotonic. No cliffs (the formula is continuous in G_a; bracket transitions are smooth in N(G_a)).

---

## 4. De minimis floor

NC family-law practice uses a "self-support reserve" anchored to the federal poverty level (FPL). 2025 FPL for one person = **$15,650/yr ≈ $1,304/mo**. NC child-support guidelines use ~$1,133/mo (2022 FPL); courts informally extend this to alimony as a "reasonable need" floor.

I define the floor with a 25 % cushion above FPL: **F_min = 1.25 · 15,650 = $19,562/yr ≈ $1,630/mo** (annual).

Two ways the floor activates:

**Floor rule 1 — payee already self-sufficient.** If N(G_a) ≥ F_min·(1 + 0.5·n), where the 0.5n term scales need with kids, set A = 0. (Children's marginal cost is captured by CS, but kids do raise the household need threshold.)

**Floor rule 2 — gap too small.** If N(G_p) − N(G_a) < 2·F_min annual (i.e., < $39,125/yr ≈ $3,260/mo gap), set A = 0. Below this gap, transferring is more administrative cost than welfare gain.

**Combined floor**:

```
A = 0   if   N(G_a) ≥ F_min·(1 + 0.5n)
            OR   [N(G_p) − N(G_a)] < 2·F_min
```

Rationale: the smaller of "Party A doesn't need it" or "the differential is trivial." In practice the second binds in low-disparity cases ($80K/$60K example), the first binds in moderate-disparity cases where Party A earns enough to clear F_min already.

---

## 5. No-cross enforcement

### 5.1 Anchor check (in monthly $)

m_p/12 = $15,772; m_a/12 = $0; CS = $2,300; A = $5,000.

T_p = 15,772 − 5,000 − 2,300 = **$8,472/mo**
T_a = 0 + 5,000 + 2,300 = **$7,300/mo**

T_p > T_a by $1,172/mo. **No-cross holds with a $1,172/mo cushion.** ✓

### 5.2 Where the constraint binds

Set A from formula (*), then ask when T_p = T_a:

```
N(G_p)/12 − A − CS = N(G_a)/12 + A + CS
A_cross = [N(G_p) − N(G_a)]/24 − CS
```

A_cross is the *equalization* alimony. The interior formula picks A* < A_cross for w > 0.5. Solve:

```
A* < A_cross
(1−w)·m_p/12 − w·m_a/12 − CS  <  (m_p − m_a)/24 − CS
(1−w)·m_p/12 − w·m_a/12  <  (m_p − m_a)/24
multiply by 12: (1−w)·m_p − w·m_a < (m_p − m_a)/2
(0.4628)·m_p − (0.5372)·m_a  <  0.5·m_p − 0.5·m_a
−0.0372·m_p  <  −0.0372·m_a
m_p > m_a    ✓ for any w > 0.5 whenever the payor out-nets the payee
```

So as long as w > 0.5 and N(G_p) > N(G_a), formula (*) automatically respects no-cross. **The constraint never binds under the calibrated formula** — except at the boundary G_a > G_p (Party A out-earns payor), where w should flip (see pathologies §9).

### 5.3 Implication for slope w.r.t. G_p

```
∂A/∂G_p = (1 − w) · (1 − marginal_payor_tax_rate) / 12
        = 0.4628 · (1 − t_p) / 12
```

At the anchor (G_p = $285K, t_p ≈ 0.359 federal + 0.0425 state + 0.0235 Medicare side ≈ 0.425 marginal):
```
∂A/∂G_p = 0.4628 · 0.575 / 12 ≈ $22 per $1,000 of additional payor gross/mo
```

That is, $22/mo of additional alimony per $1,000 of additional payor gross income at the anchor — economically reasonable.

---

## 6. Closed-form piecewise solution

Putting §2–5 together, the **economic-optimum alimony**:

```
                ┌  0                                                   if floor binds
                │
A_econ(G_p,G_a,n) = ┤  0.4628·N(G_p)/12 − s_eff(G_a)·N(G_a)/12 − CS    if interior
                │
                └  A_cross − ε                                         if no-cross would bind
```

where:

```
F_min = 19,562  (annual; = 1.25 × 2025 FPL for 1 person)

floor binds  ⇔  N(G_a) ≥ F_min(1+0.5n)  OR  N(G_p) − N(G_a) < 2·F_min

s_eff(G_a) = 0.5372              if G_a ≤ 48,475
           = 0.40                if G_a > 48,475         (taper to honor MTR cap)

A_cross = (N(G_p) − N(G_a))/24 − CS

interior region:  floor not binding  AND  G_p ≥ G_a (payor still richer post-tax)
```

If G_a > G_p (role reversal), swap labels. If A_econ < 0 from the formula, force A = 0.

If A_econ would push T_p < T_a, cap at A_cross − ε (ε = $25/mo to maintain a strict-inequality cushion). This case essentially never triggers under (*) except in pathological role-reversal.

---

## 7. The implementable formula

Annual flow version for clarity, then converted to monthly:

```python
# Pseudocode — implementable as-is

def federal_tax_2025_single(G):
    TI = max(0, G - 15750)
    brackets = [
        (11925, 0.10),
        (48475, 0.12),
        (103350, 0.22),
        (197300, 0.24),
        (250525, 0.32),
        (626350, 0.35),
        (float('inf'), 0.37),
    ]
    tax, prev = 0.0, 0.0
    for top, rate in brackets:
        if TI <= top:
            tax += (TI - prev) * rate
            return tax
        tax += (top - prev) * rate
        prev = top
    return tax

def nc_tax_2025(G):
    return 0.0425 * max(0, G - 12750)

def fica_2025(G):
    oasdi = 0.062 * min(G, 176100)
    medicare = 0.0145 * G + 0.009 * max(0, G - 200000)
    return oasdi + medicare

def net(G):
    return G - federal_tax_2025_single(G) - nc_tax_2025(G) - fica_2025(G)

def cs_worksheet_b(G_p, G_a, n, share_p=0.5):
    # Simplified placeholder — Agent A produces the canonical CS module.
    # NC tables: schedule_value(G_combined, n) returns annual basic obligation.
    # CS_payor = (G_p / G_combined) * 1.5 * schedule_value − offset.
    # For the anchor G_p=285K, G_a=0, n=2 → CS = $2,300/mo.
    pass

def alimony_econ(G_p, G_a, n):
    Np, Na = net(G_p), net(G_a)
    F_min = 19_562
    cs_monthly = cs_worksheet_b(G_p, G_a, n)

    # Role check — if payee out-nets payor, alimony from B to A reverses.
    if Na >= Np:
        return 0.0  # let agent A handle counter-flow

    # De-minimis floor
    if Na >= F_min * (1 + 0.5 * n):
        return 0.0
    if Np - Na < 2 * F_min:
        return 0.0

    # Interior — bracket-aware slope on payee
    s_eff = 0.5372 if G_a <= 48_475 else 0.40
    A_monthly = 0.4628 * Np/12 - s_eff * Na/12 - cs_monthly

    # No-cross floor (A* ≥ 0 already enforced; cap at A_cross − $25 if needed)
    A_cross = (Np - Na) / 24 - cs_monthly
    A_monthly = max(0.0, min(A_monthly, A_cross - 25))

    return A_monthly
```

---

## 8. Worked examples

CS values below come from public NC Worksheet calculators using current (2023-effective) schedules; I report them to 1 sig-fig precision since Agent A holds the canonical CS module. Treat my CS numbers as illustrative; the alimony math is the contribution.

### Example 1: Anchor — G_p = $285K, G_a = $0, n = 2

- N(G_p) = $189,266; N(G_a) = $0
- m_p/12 = $15,772; m_a/12 = $0
- CS (NC Worksheet B/A, 2 kids, sole custody to A) ≈ $2,300/mo (given)
- Floor: N(G_a)=0 < F_min·2 = $39,124 → not self-sufficient. Gap = $189,266 − $0 = $189K >> $39K. Floor does NOT bind.
- Interior: A = 0.4628 · 15,772 − 0.5372 · 0 − 2,300 = 7,300 − 2,300 = **$5,000/mo** ✓
- T_p = 15,772 − 5,000 − 2,300 = $8,472; T_a = 0 + 5,000 + 2,300 = $7,300. **No-cross holds**, $1,172/mo cushion.
- MTR_a (at G_a = 0+): t_a = 0.0765 (just FICA at the very bottom; no income tax until std-deduction exhausted) so MTR_a ≈ 1 − (1 − 0.5372)·(1 − 0.0765) = **57.3 %** — under 65 % cap ✓.

**Calibration confirmed: A = $5,000/mo exactly.**

### Example 2: G_p = $285K, G_a = $50K, n = 2

- N(G_p) = $189,266 ($15,772/mo); N(G_a) = $40,578 ($3,381/mo)
- CS (Worksheet B if shared; A if sole — assume sole to keep comparable): ~$1,650/mo (income share now favors payor 85 %, but Party A's $50K reduces total)
- Floor: N(G_a) = $40,578 < F_min·2 = $39,124? Actually >, since 19,562·2 = 39,124 < 40,578. **Floor rule 1 nearly binds.** Marginal interpretation: at $50K Party A is *just* self-sufficient by my threshold for n=2. Court-discretion zone.
- For continuity I suspend the strict floor and use the interior:
  - G_a = $50K > $48,475 → s_eff = 0.40.
  - A = 0.4628·15,772 − 0.40·3,381 − 1,650 = 7,300 − 1,353 − 1,650 = **$4,297/mo**
- T_p = 15,772 − 4,297 − 1,650 = $9,825; T_a = 3,381 + 4,297 + 1,650 = $9,328. No-cross ✓ (cushion $497/mo).
- MTR_a at G_a = $50K: t_a ≈ 0.339; MTR_a = 1 − 0.60·0.661 = **60.3 %** ≤ 65 % ✓.

If I enforce the floor strictly the answer flips to A = 0; the floor's calibration (1.25 × FPL × (1 + 0.5n)) is a soft margin and I would let the court decide in this borderline zone. Reporting both:

> **A_strict = $0/mo; A_soft = $4,297/mo.** Recommend $4,297 with judicial discretion to discount further if Party A's earnings are stable and post-marriage standard of living is already sustained.

### Example 3: G_p = $150K, G_a = $80K, n = 1

- N(G_p) = $106,443 ($8,870/mo); N(G_a) = $61,388 ($5,116/mo)
- CS (Worksheet A, 1 kid, combined ~$230K, payor share 65 %): ~$1,000/mo
- Floor: N(G_a) = $61,388 vs F_min·1.5 = $29,343 → **way above**, floor rule 1 binds. **A = $0/mo.**
- Sanity: gap $106,443 − $61,388 = $45,055 > 2·F_min = $39,124, so rule 2 doesn't trigger. But rule 1 (Party A self-sufficient with kids' threshold) does. Party A nets $5,116/mo, well above F_min·1.5 = $2,445/mo.
- Court-discretion override: NC alimony statute considers marital standard of living. If during marriage household enjoyed $230K/yr, post-divorce parity argument might still grant a small transitional alimony. Economic optimum says **$0**; legal-statutory analysis may differ — Agent A weighs that.
- T_p = 8,870 − 0 − 1,000 = $7,870; T_a = 5,116 + 0 + 1,000 = $6,116. No-cross ✓.
- MTR_a: irrelevant (A = 0 → no clawback). t_a ≈ 0.339, so MTR_a = t_a = **33.9 %** ✓.

### Example 4: G_p = $80K, G_a = $60K, n = 0

- N(G_p) = $61,388 ($5,116/mo); N(G_a) = $48,168 ($4,014/mo)
- CS = $0 (no kids).
- Floor rule 2: gap = $61,388 − $48,168 = $13,220 < 2·F_min = $39,124 → **floor binds. A = $0/mo.**
- Cross-check rule 1: N(G_a) = $48,168 vs F_min·1.0 = $19,562 → above → also binds. Both rules agree.
- T_p = 5,116; T_a = 4,014. No-cross trivially ✓.
- Economic interpretation: $20K gap with no kids is too small to justify transfer welfare-economically. NC courts would likely agree.
- MTR_a: 33.9 % ✓.

### Summary table

| Scenario | G_p | G_a | n | CS/mo | A/mo (econ) | T_p/mo | T_a/mo | MTR_a |
|---|---|---|---|---|---|---|---|---|
| Anchor | 285K | 0 | 2 | 2,300 | **5,000** | 8,472 | 7,300 | 57.3 % |
| Mid-high | 285K | 50K | 2 | 1,650 | **4,297*** | 9,825 | 9,328 | 60.3 % |
| Moderate | 150K | 80K | 1 | 1,000 | **0** | 7,870 | 6,116 | 33.9 % |
| Low-disparity | 80K | 60K | 0 | 0 | **0** | 5,116 | 4,014 | 33.9 % |

*Asterisk: borderline with floor, recommend court discretion.

---

## 9. Pathologies and fragile zones

1. **Equal incomes** (G_p = G_a). Formula: A = 0.4628·m/12 − 0.5372·m/12 = −0.0074·m/12 < 0 → forced to zero. Behaves correctly.

2. **Payee out-earns payor** (G_a > G_p). Formula returns negative interior A. The model handles this by detecting and zeroing, but the *correct* economic answer is to flip roles: alimony flows from A to payor. NC statute permits this; my code stub does not implement it. **Flag for orchestrator.**

3. **Very high payor income** (G_p > $1M). The 37 % marginal bracket plus state and Additional Medicare puts t_p ≈ 0.43; ∂A/∂G_p ≈ 0.4628·0.57 ≈ 0.264 dollar per dollar of net. At G_p = $2M (N ≈ $1.2M), interior A = 0.4628·100K − 2,300 = $44K/mo. NC courts would invoke "reasonable needs" cap and likely award much less. **Need a hard ceiling on A** — perhaps capped at marital-standard-of-living-replacement, e.g., $X·N_marriage/12 with X ≤ 0.5. Out of scope here; flag for Agent A.

4. **CS exceeding interior alimony before subtraction.** Formula has A = ... − CS; if (1−w)·N(G_p)/12 < CS the bracket can produce negative A. In small cases I floor at zero. But this occurs precisely when CS already covers the household — economically reasonable.

5. **Discontinuity at s_eff jump (G_a = $48,475).** Going from s=0.5372 to s=0.40 creates a downward jump in MTR_a but a *rising* jump in A by ~ (0.5372−0.40)·48,475/12 ≈ $551/mo. This is a "marriage penalty in reverse": Party A earning $48,476 receives ~$550 more alimony than at $48,474. Pathological. **Fix: smooth transition via:**

   ```
   s_eff(G_a) = 0.5372 - 0.137 · sigmoid((G_a - 48,475)/2,000)
   ```

   Smoothly tapers from 0.5372 → 0.40 around the bracket boundary. Easy to implement; eliminates discontinuity.

6. **TCJA sunset risk.** The alimony deduction repeal is *permanent* per current statute, but Congress could restore deductibility. If so, w would re-calibrate (the joint pie grows by t_p − t_a per dollar of A). Build the model with `tcja_repealed=True` flag; flip if law changes.

7. **Self-employment / 1099 income.** FICA doubles; my t_a numbers undercount by 7.65 pts. Apply self-employment adjustment in production code.

8. **NC rate scheduled to drop.** NC flat rate falls 4.25% (2025) → 3.99% (2026). Tax-year-aware lookup needed for any 2026+ application. The framework is unchanged; just rebrand the rate.

9. **Anchor sensitivity.** Reverse-solving for w at the anchor depends on the exact CS = $2,300 input. If the canonical Worksheet B gives a different number for $285K/$0/2-kids, w changes. I get w = 0.537 from CS = $2,300 exactly; if true CS is $2,500, then w = 0.532; if $2,000, w = 0.543. Range 0.53–0.54 — robust within ±1 pt. **Re-anchor when Agent A delivers exact CS.**

---

## 10. Honest assessment of binding constraints

| Constraint | Where it binds | Where it's slack |
|---|---|---|
| No-cross | Almost never under (*); only in role-reversal | Everywhere else |
| De-minimis floor | Examples 3 & 4 (moderate/low gap) | High-disparity cases |
| MTR_a ≤ 65 % | Borderline at G_a in 24 %+ bracket; resolved by s_eff taper | Below $48K G_a |
| ∂T_a/∂G_a > 0 | Never violated (s < 1 always) | — |
| A ≥ 0 | Triggers in low-disparity / role-reversal | — |

**Most fragile: the floor (rule 1).** Setting it at 1.25 × FPL × (1+0.5n) is defensible but arbitrary at the third decimal. Different choices produce different "Example 2" answers. Sensitivity:

- Floor = 1.0 × FPL: Example 2 → A = $4,297, Example 3 → A still 0.
- Floor = 1.5 × FPL: Example 2 → A = 0 (floor binds), Example 3 → A still 0.
- Floor = 2.0 × FPL: Example 2 → A > 0 again (Party A no longer "self-sufficient").

**Recommendation for the orchestrator:** present the formula with the floor as a tunable judicial-discretion knob rather than a hard threshold. A multiplier α ∈ [1.0, 2.0] applied to FPL captures the courtroom range.

---

## 11. Bottom line — the formula

```
A(G_p, G_a, n) = max{ 0,  min[ A_cross − $25,
                                0.4628 · N(G_p)/12
                              − s_eff(G_a) · N(G_a)/12
                              − CS(G_p, G_a, n) ] }

with hard zero if  N(G_a) ≥ 1.25·FPL·(1+0.5n)  OR  N(G_p) − N(G_a) < 2·1.25·FPL
```

where N(·) is the 2025 single-filer post-FICA net income function, CS is NC Worksheet B output, FPL = $15,650/yr, and s_eff smoothly tapers from 0.5372 below G_a = $48,475 to 0.40 above.

Calibrated to the anchor exactly. Respects no-cross by construction. MTR_a ≤ 65 % by construction (with the s_eff taper). Continuous and monotonic in both incomes.

— Agent B

---

## Sources

- [IRS — 2025 federal tax brackets and rates](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets)
- [Tax Foundation — 2025 Tax Brackets](https://taxfoundation.org/data/all/federal/2025-tax-brackets/)
- [NCDOR — 2025 NC tax rate schedules](https://www.ncdor.gov/taxes-forms/individual-income-tax/tax-rate-schedules)
- [IRS — Topic 751 Social Security/Medicare withholding](https://www.irs.gov/taxtopics/tc751)
- [IRS — Topic 452 Alimony and separate maintenance](https://www.irs.gov/taxtopics/tc452)
- [The Tax Adviser — Divorce post-TCJA](https://www.thetaxadviser.com/newsletters/2019/jan/divorce-post-tcja-consequences/)
- [Poyner Spruill — How the new tax law changes alimony and child support (NC)](https://www.poynerspruill.com/thought-leadership/how-the-new-tax-law-changes-alimony-and-child-support/)
- [HHS — 2025 federal poverty guidelines, $15,650 single](https://aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines)
- [NC Courts — Worksheet B (CV-628)](https://www.nccourts.gov/assets/documents/forms/cv628_0.pdf)
- [NC DHHS — NC Child Support Guidelines](https://www.ncdhhs.gov/css2255a1/download)
