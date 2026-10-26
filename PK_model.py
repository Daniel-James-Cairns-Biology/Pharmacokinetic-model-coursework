import numpy
from scipy.integrate import solve_ivp


class Protocol:
    """Store IV boluses and time-limited infusions.

    Amounts are in ng and times are in hours; infusion rates are in ng/h.
    """

    def __init__(self):
        self.boluses = []
        self.infusions = []

    def add_bolus(self, amount, time=0):
        amount, time = float(amount), float(time)
        if (not numpy.isfinite(amount) or amount <= 0 or
                not numpy.isfinite(time) or time < 0):
            raise ValueError("bolus amount must be positive and time non-negative")
        self.boluses.append((amount, time))
        return self

    def add_infusion(self, rate, start, duration):
        rate, start, duration = float(rate), float(start), float(duration)
        if (not all(numpy.isfinite(x) for x in (rate, start, duration)) or
                rate <= 0 or start < 0 or duration <= 0):
            raise ValueError("infusion rate and duration must be positive")
        self.infusions.append((rate, start, duration))
        return self

    def dose_at(self, time):
        return sum(amount for amount, dose_time in self.boluses
                   if dose_time == time)

    def rate_at(self, time):
        return sum(rate for rate, start, duration in self.infusions
                   if start <= time < start + duration)

    def events_between(self, start, end):
        """Return bolus and infusion-boundary times in the closed interval."""
        start, end = float(start), float(end)
        if (not all(numpy.isfinite(x) for x in (start, end)) or
                start < 0 or end < start):
            raise ValueError("give a finite time range with 0 <= start <= end")
        events = [
            time for _, time in self.boluses if start <= time <= end
        ]
        for _, infusion_start, duration in self.infusions:
            infusion_end = infusion_start + duration
            if start <= infusion_start <= end:
                events.append(infusion_start)
            if start <= infusion_end <= end:
                events.append(infusion_end)
        return sorted(set(events))


class Model:
    """IV model with a central compartment and peripheral compartments.

    Volumes are in mL; clearances are in mL/h.
    """

    def __init__(self, central_volume, clearance, peripheral_volumes=None,
                 intercompartmental_clearances=None):
        self.central_volume = float(central_volume)
        self.clearance = float(clearance)
        self.peripheral_volumes = (
            list(peripheral_volumes) if peripheral_volumes is not None else []
        )
        self.intercompartmental_clearances = list(
            intercompartmental_clearances
            if intercompartmental_clearances is not None else []
        )
        if (not numpy.isfinite(self.central_volume) or
                self.central_volume <= 0):
            raise ValueError("central volume must be finite and positive")
        if not numpy.isfinite(self.clearance) or self.clearance < 0:
            raise ValueError("clearance must be finite and non-negative")
        if len(self.peripheral_volumes) != len(
                self.intercompartmental_clearances):
            raise ValueError("each peripheral compartment needs a volume and clearance")
        if any(not numpy.isfinite(v) or v <= 0
               for v in self.peripheral_volumes):
            raise ValueError("peripheral volumes must be finite and positive")
        if any(not numpy.isfinite(q) or q < 0
               for q in self.intercompartmental_clearances):
            raise ValueError("intercompartmental clearances must be non-negative")
        self.state_names = ["central"] + [
            f"peripheral_{i + 1}" for i in range(len(self.peripheral_volumes))
        ]

    def rhs(self, time, amounts, dose_rate=0):
        """Return central and peripheral amount derivatives."""
        change = numpy.zeros(len(self.state_names))
        central_concentration = amounts[0] / self.central_volume
        change[0] = dose_rate - self.clearance * central_concentration
        for i, (volume, clearance) in enumerate(zip(
                self.peripheral_volumes,
                self.intercompartmental_clearances)):
            peripheral = i + 1
            peripheral_concentration = amounts[peripheral] / volume
            exchange = clearance * (
                central_concentration - peripheral_concentration
            )
            change[0] -= exchange
            change[peripheral] += exchange
        return change

    def solve(self, protocol, times):
        """Return amounts by compartment at each sample time."""
        if not isinstance(protocol, Protocol):
            raise TypeError("protocol must be a Protocol instance")
        times = numpy.asarray(times, dtype=float)
        if (times.ndim != 1 or len(times) < 2 or
                not numpy.all(numpy.isfinite(times)) or times[0] < 0 or
                numpy.any(numpy.diff(times) <= 0)):
            raise ValueError("times must be finite, non-negative, and increasing")

        state = numpy.zeros(len(self.state_names))
        state[0] = protocol.dose_at(0)
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
                rtol=1e-7,
                atol=1e-9,
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
    sample_times = numpy.linspace(0, 24, 241)
    protocol = Protocol().add_bolus(1000).add_infusion(50, start=2, duration=4)
    model = Model(3000, 300, [5000, 8000], [200, 100])
    amounts = model.solve(protocol, sample_times)
    for name, amount in zip(model.state_names, amounts[:, -1]):
        print(f"{name} amount at 24 h: {amount:.2f} ng")
