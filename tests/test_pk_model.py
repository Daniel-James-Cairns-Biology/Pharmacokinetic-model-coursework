"""Unit tests for protocol definitions, model equations, and solver functionality.""" 

import unittest
import matplotlib
import numpy

from pk_model import Model, Protocol

matplotlib.use("Agg")


class ProtocolTests(unittest.TestCase):
    """Tests for the Protocol class dosing and event management."""
    def test_boluses_and_infusions(self):
        doses = Protocol().add_bolus(5).add_bolus(7, 2)
        self.assertEqual(doses.dose_at(0), 5)
        self.assertEqual(doses.events_between(0, 3), [0, 2])

        doses.add_infusion(2, 0, 3).add_infusion(3, 1, 2)
        self.assertEqual(doses.rate_at(0.5), 2)
        self.assertEqual(doses.rate_at(1.5), 5)
        self.assertEqual(doses.rate_at(3), 0)
        self.assertEqual(doses.events_between(0, 4), [0, 1, 2, 3])

    def test_rejects_bad_doses_and_times(self):
        with self.assertRaises(ValueError):
            Protocol().add_bolus(0)
        with self.assertRaises(ValueError):
            Protocol().add_infusion(1, 0, 0)


class ModelTests(unittest.TestCase):
    """Tests for the Model class ODE solvers and compartment dynamics."""
    def test_iv_bolus_matches_expected_curve(self):
        solution = Model(10, 2).solve(Protocol().add_bolus(100), [0, 1, 2])
        expected = 100 * numpy.exp(-0.2 * numpy.array([0, 1, 2]))
        numpy.testing.assert_allclose(solution.amount("central"), expected)

    def test_iv_two_compartment_rhs_matches_project_equations(self):
        model = Model(10, 2, [20], [3])

        # Central: Dose - CL * qc/Vc - Q * (qc/Vc - qp/Vp)
        # Peripheral: Q * (qc/Vc - qp/Vp)
        numpy.testing.assert_allclose(
            model.rhs(0, [100, 40], dose_rate=7), [-37, 24]
        )

    def test_sc_two_compartment_rhs_matches_project_equations(self):
        model = Model(10, 2, [20], [3], route="sc", absorption_rate=0.5)

        # Depot input/absorption, then the same central elimination and exchange.
        numpy.testing.assert_allclose(
            model.rhs(0, [80, 100, 40], dose_rate=7), [-33, -4, 24]
        )

    def test_boluses_before_and_on_sample_times(self):
        solution = Model(1, 1).solve(
            Protocol().add_bolus(5, 0.5).add_bolus(7, 1), [0, 0.5, 1, 2]
        )
        expected = [0, 5, 5 * numpy.exp(-0.5) + 7,
                    (5 * numpy.exp(-0.5) + 7) * numpy.exp(-1)]
        numpy.testing.assert_allclose(solution.amount("central"), expected)

        earlier_dose = Model().solve(Protocol().add_bolus(10), [1, 2])
        numpy.testing.assert_allclose(earlier_dose.amount("central"), [10, 10])

    def test_infusion_stops_at_the_right_time(self):
        solution = Model(1, 1).solve(
            Protocol().add_infusion(10, 0, 1), [0, 1, 2]
        )
        amount = 10 * (1 - numpy.exp(-1))
        numpy.testing.assert_allclose(
            solution.amount("central"), [0, amount, amount * numpy.exp(-1)]
        )

    def test_sc_absorption_and_peripheral_exchange(self):
        model = Model(5, route="sc", absorption_rate=0.5)
        solution = model.solve(Protocol().add_bolus(100), numpy.linspace(0, 2, 21))
        self.assertGreater(solution.amount("central")[-1], 0)
        self.assertLess(solution.amount("depot")[-1], 100)

        model = Model(8, 0, [10, 12], [1, 2])
        self.assertAlmostEqual(float(model.rhs(0, [60, 5, 20]).sum()), 0)

    def test_protocol_works_with_different_models(self):
        doses = Protocol().add_bolus(20)
        self.assertEqual(Model().solve(doses, [0, 1]).amounts.shape, (1, 2))
        self.assertEqual(
            Model(1, 1, [2], [1]).solve(doses, [0, 1]).amounts.shape, (2, 2)
        )

    def test_concentration(self):
        solution = Model(10, 1).solve(Protocol().add_bolus(100), [0, 1, 2])
        self.assertEqual(solution.concentration()[0], 10)
        numpy.testing.assert_allclose(
            solution.concentration("central"),
            solution.amount("central") / 10,
        )

    def test_rejects_bad_model_and_solution_inputs(self):
        bad_models = [
            {"central_volume": 0},
            {"peripheral_volumes": [1], "intercompartmental_clearances": []},
            {"route": "oral"},
            {"route": "sc"},
        ]
        for settings in bad_models:
            with self.assertRaises((TypeError, ValueError)):
                Model(**settings)

        for times in ([0, 0], [0, numpy.nan]):
            with self.assertRaises(ValueError):
                Model().solve(Protocol(), times)

        with self.assertRaises(ValueError):
            Model().solve(Protocol(), [0, 1], [-1])

        with self.assertRaises(TypeError):
            Model().solve([], [0, 1])


class PlotTests(unittest.TestCase):
    def test_plot_and_compare(self):
        solution = Model().solve(Protocol().add_bolus(1), [0, 1])
        solution.plot()
        solution.compare(solution, compartments=["central"])
if __name__ == "__main__":
    unittest.main()
