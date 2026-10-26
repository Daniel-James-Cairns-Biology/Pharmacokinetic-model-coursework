import numpy
from scipy.integrate import solve_ivp


class Protocol:
    """Collect bolus doses and time-limited infusions."""

    def __init__(self):
        self.boluses = []
        self.infusions = []

    def add_bolus(self, amount, time=0):
        self.boluses.append((float(amount), float(time)))
        return self

    def add_infusion(self, rate, start, duration):
        self.infusions.append((float(rate), float(start), float(duration)))
        return self

    def dose_at(self, time):
        return sum(amount for amount, dose_time in self.boluses
                   if dose_time == time)

    def rate_at(self, time):
        return sum(rate for rate, start, duration in self.infusions
                   if start <= time < start + duration)

    def events_between(self, start, end):
        events = [
            time for _, time in self.boluses
            if start <= time <= end
        ]
        for _, infusion_start, duration in self.infusions:
            infusion_end = infusion_start + duration
            if start <= infusion_start <= end:
                events.append(infusion_start)
            if start <= infusion_end <= end:
                events.append(infusion_end)
        return sorted(set(events))


class Model:
    """An IV model with one central and any number of peripheral compartments."""

    def __init__(self, central_volume, clearance, peripheral_volumes=None,
                 intercompartmental_clearances=None):
        self.central_volume = float(central_volume)
        self.clearance = float(clearance)
        self.peripheral_volumes = list(peripheral_volumes or [])
        self.intercompartmental_clearances = list(
            intercompartmental_clearances or []
        )
        if len(self.peripheral_volumes) != len(
                self.intercompartmental_clearances):
            raise ValueError("each peripheral compartment needs a volume and clearance")
        self.state_names = ["central"] + [
            f"peripheral_{i + 1}" for i in range(len(self.peripheral_volumes))
        ]

    def rhs(self, time, amounts, dose_rate=0):
        change = numpy.zeros(len(self.state_names))
        central_concentration = amounts[0] / self.central_volume
        change[0] = dose_rate - self.clearance * central_concentration
        for i, (volume, clearance) in enumerate(zip(
                self.peripheral_volumes,
                self.intercompartmental_clearances)):
            index = i + 1
            peripheral_concentration = amounts[index] / volume
            exchange = clearance * (
                central_concentration - peripheral_concentration
            )
            change[0] -= exchange
            change[index] += exchange
        return change

    def solve(self, protocol, times):
        times = numpy.asarray(times, dtype=float)
        state = numpy.zeros(len(self.state_names))
        state[0] += protocol.dose_at(0)
        answer = numpy.zeros((len(state), len(times)))
        if times[0] == 0:
            answer[:, 0] = state

        now = 0.0
        ends = set(protocol.events_between(now, times[-1]))
        ends.update(times)
        for end in sorted(ends):
            if end <= now:
                continue
            indexes = numpy.where((times > now) & (times <= end))[0]
            samples = times[indexes]
            if len(samples) == 0 or samples[-1] != end:
                samples = numpy.append(samples, end)
            rate = protocol.rate_at((now + end) / 2)
            result = solve_ivp(
                lambda time, amounts: self.rhs(time, amounts, rate),
                (now, end),
                state,
                t_eval=samples,
            )
            if not result.success:
                raise RuntimeError(result.message)
            answer[:, indexes] = result.y[:, :len(indexes)]
            state = result.y[:, -1].copy()
            now = end
            state[0] += protocol.dose_at(end)
            exact_time = numpy.where(times == end)[0]
            if len(exact_time):
                answer[:, exact_time[0]] = state
        return answer


if __name__ == "__main__":
    times = numpy.linspace(0, 24, 241)
    protocol = Protocol().add_bolus(1000).add_infusion(50, 2, 4)
    model = Model(3000, 300, [5000, 8000], [200, 100])
    amounts = model.solve(protocol, times)
    for name, amount in zip(model.state_names, amounts[:, -1]):
        print(f"{name} amount at 24 hours: {amount:.2f} ng")
