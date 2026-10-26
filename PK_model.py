import numpy
from scipy.integrate import solve_ivp


class Protocol:
    """An IV bolus administered at time zero."""

    def __init__(self, dose):
        self.dose = float(dose)


class Model:
    """A one-compartment model with linear clearance."""

    def __init__(self, volume, clearance):
        self.volume = float(volume)
        self.clearance = float(clearance)

    def rhs(self, time, amount):
        return [-self.clearance * amount[0] / self.volume]

    def solve(self, protocol, times):
        times = numpy.asarray(times, dtype=float)
        solution = solve_ivp(
            self.rhs,
            (times[0], times[-1]),
            [protocol.dose],
            t_eval=times,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        return solution.y[0]


if __name__ == "__main__":
    times = numpy.linspace(0, 24, 241)
    model = Model(volume=3000, clearance=300)
    amount = model.solve(Protocol(dose=1000), times)
    print(f"Central amount at 24 hours: {amount[-1]:.2f} ng")
