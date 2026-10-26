import numpy
from scipy.integrate import solve_ivp


class Protocol:
    """Store boluses and time-limited infusions, independently of a model."""

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
    """Central/peripheral PK model with IV or first-order SC input.

    Volumes are in mL, clearances in mL/h, and absorption rate in 1/h.
    """

    def __init__(self, central_volume, clearance, peripheral_volumes=None,
                 intercompartmental_clearances=None, route="iv",
                 absorption_rate=None, name="PK model"):
        self.central_volume = float(central_volume)
        self.clearance = float(clearance)
        self.peripheral_volumes = (
            list(peripheral_volumes) if peripheral_volumes is not None else []
        )
        self.intercompartmental_clearances = list(
            intercompartmental_clearances
            if intercompartmental_clearances is not None else []
        )
        if not numpy.isfinite(self.central_volume) or self.central_volume <= 0:
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
        if not isinstance(route, str):
            raise ValueError("route must be 'iv' or 'sc'")
        route = route.lower()
        if route in ("iv", "intravenous"):
            self.route = "iv"
            self.absorption_rate = None
        elif route in ("sc", "subcutaneous"):
            if absorption_rate is None:
                raise ValueError("SC models need a positive absorption rate")
            self.absorption_rate = float(absorption_rate)
            if not numpy.isfinite(self.absorption_rate) or self.absorption_rate <= 0:
                raise ValueError("SC models need a positive absorption rate")
            self.route = "sc"
        else:
            raise ValueError("route must be 'iv' or 'sc'")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("model name must not be empty")
        self.name = name
        self.central_index = 1 if self.route == "sc" else 0
        self.state_names = ["central"]
        if self.route == "sc":
            self.state_names.insert(0, "depot")
        self.state_names.extend(
            f"peripheral_{i + 1}" for i in range(len(self.peripheral_volumes))
        )

    def rhs(self, time, amounts, dose_rate=0):
        """Return amount derivatives for each compartment."""
        change = numpy.zeros(len(self.state_names))
        central = self.central_index
        if self.route == "sc":
            absorbed = self.absorption_rate * amounts[0]
            change[0] = dose_rate - absorbed
            central_input = absorbed
        else:
            central_input = dose_rate

        central_concentration = amounts[central] / self.central_volume
        change[central] = central_input - self.clearance * central_concentration
        for i, volume in enumerate(self.peripheral_volumes):
            peripheral = central + i + 1
            peripheral_concentration = amounts[peripheral] / volume
            exchange = self.intercompartmental_clearances[i] * (
                central_concentration - peripheral_concentration
            )
            change[central] -= exchange
            change[peripheral] += exchange
        return change

    def solve(self, protocol, times):
        if not isinstance(protocol, Protocol):
            raise TypeError("protocol must be a Protocol instance")
        times = numpy.asarray(times, dtype=float)
        if (times.ndim != 1 or len(times) < 2 or
                not numpy.all(numpy.isfinite(times)) or times[0] < 0 or
                numpy.any(numpy.diff(times) <= 0)):
            raise ValueError("times must be finite, non-negative, and increasing")

        state = numpy.zeros(len(self.state_names))
        state[0] = protocol.dose_at(0)
        amounts = numpy.zeros((len(state), len(times)))
        if times[0] == 0:
            amounts[:, 0] = state
        now = 0.0
        event_times = set(protocol.events_between(now, times[-1]))
        event_times.update(times)
        for end in sorted(event_times):
            if end <= now:
                continue
            indexes = numpy.where((times > now) & (times <= end))[0]
            samples = times[indexes]
            if len(samples) == 0 or samples[-1] != end:
                samples = numpy.append(samples, end)
            rate = protocol.rate_at((now + end) / 2)
            result = solve_ivp(
                lambda time, values: self.rhs(time, values, rate),
                (now, end),
                state,
                t_eval=samples,
                rtol=1e-7,
                atol=1e-9,
            )
            if not result.success:
                raise RuntimeError(result.message)
            amounts[:, indexes] = result.y[:, :len(indexes)]
            state = result.y[:, -1].copy()
            now = end
            state[0] += protocol.dose_at(end)
            exact_time = numpy.where(times == end)[0]
            if len(exact_time):
                amounts[:, exact_time[0]] = state
        return Solution(self, times, amounts)


class Solution:
    """Store model results and plot amounts or concentrations."""

    def __init__(self, model, times, amounts):
        self.model = model
        self.times = times
        self.amounts = amounts

    def amount(self, compartment="central"):
        return self.amounts[self.model.state_names.index(compartment)]

    def concentration(self, compartment="central"):
        index = self.model.state_names.index(compartment)
        if compartment == "depot":
            raise ValueError("the depot has no volume, so it has no concentration")
        if compartment == "central":
            volume = self.model.central_volume
        else:
            volume = self.model.peripheral_volumes[
                index - self.model.central_index - 1
            ]
        return self.amount(compartment) / volume

    def plot(self, quantity="concentration", compartments=None):
        import matplotlib.pyplot as plt

        if quantity not in ("amount", "concentration"):
            raise ValueError("quantity must be 'amount' or 'concentration'")
        if compartments is None:
            compartments = self.model.state_names
            if quantity == "concentration":
                compartments = [
                    name for name in compartments if name != "depot"
                ]
        else:
            compartments = tuple(compartments)
        if not compartments:
            raise ValueError("choose at least one compartment to plot")

        for compartment in compartments:
            if quantity == "amount":
                values = self.amount(compartment)
            else:
                values = self.concentration(compartment)
            plt.plot(
                self.times,
                values,
                label=f"{self.model.name}: {compartment}",
            )
        plt.xlabel("Time [h]")
        plt.ylabel("Drug amount [ng]" if quantity == "amount"
                   else "Concentration [ng/mL]")
        plt.legend()
        return plt.gca()

    def compare(self, other, quantity="concentration", compartments=None):
        """Plot this result and another result on the same axes."""
        self.plot(quantity, compartments)
        other.plot(quantity, compartments)
        return self


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    sample_times = numpy.linspace(0, 24, 241)
    protocol = Protocol().add_bolus(1000)
    iv_model = Model(3000, 300, name="IV")
    sc_model = Model(3000, 300, route="sc", absorption_rate=0.8, name="SC")
    iv_solution = iv_model.solve(protocol, sample_times)
    sc_solution = sc_model.solve(protocol, sample_times)
    iv_solution.compare(sc_solution, compartments=["central"])
    plt.show()
