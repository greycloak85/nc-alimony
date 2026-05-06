"""
Regression tests for nc_alimony.py.

Run:
    python -m unittest test_nc_alimony.py        # noisy
    python -m unittest -v test_nc_alimony.py     # verbose
    python test_nc_alimony.py                    # runs main()

Tests are scoped to the dependency-gate change (33% gross -> 40% net) and the
core invariants the consent-order formula depends on. The boundary test
intentionally locks the 0.40 threshold so the consent order's referenced
formula version cannot drift silently.
"""

import unittest

from nc_alimony import (
    model,
    net_income,
    DEPENDENCY_GATE_RATIO,
)


class AnchorTests(unittest.TestCase):
    """Anchor case must reproduce the calibration target regardless of any
    gate-related changes (Party A net = 0 means the gate ratio is 0)."""

    def test_anchor_alimony_within_tolerance(self):
        # direct_offset_p=200 is the calibration anchor (judge-deviation
        # credit). The Streamlit UI's default is 0 (Worksheet-B-only
        # treatment), which produces ~$4,791/$2,493 instead.
        r = model(285_000, 0, 2, direct_offset_p=200)
        # Spec acceptance criterion: "$4,988 ± $12 alimony"
        self.assertAlmostEqual(r['A_monthly'], 4_988, delta=12)

    def test_anchor_cs_within_tolerance(self):
        # direct_offset_p=200 is the calibration anchor (judge-deviation
        # credit). The Streamlit UI's default is 0 (Worksheet-B-only
        # treatment), which produces ~$4,791/$2,493 instead.
        r = model(285_000, 0, 2, direct_offset_p=200)
        # Spec acceptance criterion: "$2,293 ± $7 CS"
        self.assertAlmostEqual(r['cs_monthly'], 2_293, delta=7)

    def test_anchor_no_gate_fires(self):
        # direct_offset_p=200 is the calibration anchor (judge-deviation
        # credit). The Streamlit UI's default is 0 (Worksheet-B-only
        # treatment), which produces ~$4,791/$2,493 instead.
        r = model(285_000, 0, 2, direct_offset_p=200)
        self.assertIsNone(r['gate_fired'])


class DependencyGateTests(unittest.TestCase):
    """Verify the 40%-net-income dependency gate fires where expected and
    passes through where the recipient is genuinely dependent."""

    def test_threshold_constant_locked_at_40pct(self):
        """Lock the constant. If anyone changes it, this test breaks loudly
        — and the consent-order Attachment B's commit-hash reference must be
        re-validated."""
        self.assertEqual(DEPENDENCY_GATE_RATIO, 0.40)

    def test_scenario_3_passes_through_under_new_gate(self):
        """Under the 33% gross gate, Scenario 3 ($150K/$80K/1 kid) zeroed
        because gross ratio = 80/(150+80) = 34.78% > 33%. Under the 40% net
        gate, the net ratio is ~36% < 40% -> alimony non-zero."""
        r = model(150_000, 80_000, 1,
                  health_ins=482, addons_paid_p=482, direct_offset_p=0)
        self.assertIsNone(r['gate_fired'])
        self.assertGreater(r['A_monthly'], 0)

    def test_equal_incomes_still_gated(self):
        """Equal incomes -> ratio = 0.5 >= 0.40 -> gate fires."""
        r = model(150_000, 150_000, 1,
                  health_ins=482, addons_paid_p=482, direct_offset_p=0)
        self.assertEqual(r['gate_fired'], 'dependency_40pct_net')
        self.assertEqual(r['A_monthly'], 0.0)

    def test_role_reversal_gates(self):
        """Labelled payor earns less; labelled 'Party A' has > 50% of net.
        Gate fires; alimony from labelled payor is zero (any award would
        flow the other direction and is out of scope of this gate)."""
        r = model(50_000, 200_000, 1,
                  health_ins=482, addons_paid_p=482, direct_offset_p=0)
        self.assertEqual(r['gate_fired'], 'dependency_40pct_net')
        self.assertEqual(r['A_monthly'], 0.0)

    def test_scenario_4_gates_via_dependency(self):
        """$80K / $60K / 0 kids: net ratio ~43.5% > 40% -> gate fires.
        Even if Gate 3 (de-minimis) would also fire, Gate 2 fires first."""
        r = model(80_000, 60_000, 0)
        self.assertEqual(r['gate_fired'], 'dependency_40pct_net')
        self.assertEqual(r['A_monthly'], 0.0)


class GateBoundaryTest(unittest.TestCase):
    """Locks the threshold value. We construct a (G_p, G_a) pair where the
    NET-income ratio is ~0.40, then test points just below and just above."""

    def _net_ratio(self, G_p, G_a):
        return net_income(G_a) / (net_income(G_p) + net_income(G_a))

    def test_just_below_threshold_does_not_fire(self):
        """At $200K / $100K, net ratio = N($100K)/(N($200K)+N($100K))
        = $74,778 / ($136,313 + $74,778) ~ 35.4% < 40% -> gate does NOT fire."""
        r = model(200_000, 100_000, 1,
                  health_ins=482, addons_paid_p=482, direct_offset_p=0)
        ratio = self._net_ratio(200_000, 100_000)
        self.assertLess(ratio, DEPENDENCY_GATE_RATIO)
        self.assertIsNone(r['gate_fired'])

    def test_just_above_threshold_does_fire(self):
        """At $150K / $120K, net ratio = N($120K)/(N($150K)+N($120K))
        ~= 0.444 > 0.40 -> gate fires."""
        r = model(150_000, 120_000, 1,
                  health_ins=482, addons_paid_p=482, direct_offset_p=0)
        ratio = self._net_ratio(150_000, 120_000)
        self.assertGreaterEqual(ratio, DEPENDENCY_GATE_RATIO)
        self.assertEqual(r['gate_fired'], 'dependency_40pct_net')
        self.assertEqual(r['A_monthly'], 0.0)


class NoCrossInvariant(unittest.TestCase):
    """Constraint #2: payor's monthly take-home must be >= recipient's,
    across the whole reasonable income grid."""

    def test_no_cross_holds_across_payor_sweep(self):
        for G_p in [50_000, 75_000, 100_000, 150_000, 200_000, 250_000,
                    285_000, 350_000, 500_000, 750_000, 1_000_000]:
            r = model(G_p, 0, 2,
                      health_ins=482, addons_paid_p=482, direct_offset_p=0)
            with self.subTest(G_p=G_p):
                self.assertGreaterEqual(r['take_home_p_monthly'],
                                        r['take_home_a_monthly'],
                                        msg=f"No-cross failure at G_p=${G_p:,}")

    def test_payee_take_home_monotone_across_payee_sweep(self):
        """Constraint #4: as Party A's earnings rise, her total take-home
        must strictly (or weakly) rise — no benefit cliffs."""
        prev_th_a = -1.0
        for G_a in range(0, 200_001, 5_000):
            r = model(285_000, G_a, 2,
                      health_ins=482, addons_paid_p=482, direct_offset_p=0)
            th_a = r['take_home_a_monthly']
            with self.subTest(G_a=G_a):
                self.assertGreaterEqual(th_a, prev_th_a - 0.01,
                                        msg=f"Take-home dropped at G_a=${G_a:,}: "
                                            f"prev={prev_th_a:.2f} now={th_a:.2f}")
            prev_th_a = th_a


if __name__ == "__main__":
    unittest.main(verbosity=2)
