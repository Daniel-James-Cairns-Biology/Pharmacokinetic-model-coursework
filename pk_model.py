"""Pharmacokinetics model implementation for subcutaneous and intravenous dosage"""

import numpy
from scipy.integrate import solve_ivp

import matplotlib.pyplot as plt


class Protocol:
    """Keep track of when the doses happen."""

    def __init__(self):
        # Bolus is amount and time. Infusion is rate, start, how long.
        self.boluses = []
        self.infusions = []

    def add_bolus(self, amount, time=0):
        """Add a dose that goes in all at once."""
        amount, time = float(amount), float(time)
        if (not all(numpy.isfinite(x) for x in (amount, time)) or
                amount <= 0 or time < 0):
            raise ValueError("amount must be positive and time cannot be negative")
        self.boluses.append((amount, time))
        return self

    def add_infusion(self, rate, start, duration):
        """Add a dose that drips in for a bit."""
        rate, start, duration = float(rate), float(start), float(duration)
        if (not all(numpy.isfinite(x) for x in (rate, start, duration)) or
                rate <= 0 or start < 0 or duration <= 0):
            raise ValueError("check the infusion rate, start, and duration")
        self.infusions.append((rate, start, duration))
        return self

    def dose_at(self, time):
        """Calculate the total bolus dose amount delivered at a specific time."""
        return sum(amount for amount, dose_time in self.boluses
                   if dose_time == time)

    def rate_at(self, time):
        """Calculate the continuous infusion rate active at a given time."""
        rate = 0
        for amount_per_hour, start, duration in self.infusions:
            if start <= time < start + duration:
                rate += amount_per_hour
        return rate

    def events_between(self, start, end):
        """Return a sorted list of unique dose event times within the specified range."""
        start, end = float(start), float(end)
        if (not all(numpy.isfinite(x) for x in (start, end)) or
                start < 0 or end < start):
            raise ValueError("give a valid time range")
        events = []
        for _amount, dose_time in self.boluses:
            if start <= dose_time <= end:
                events.append(dose_time)
        for _rate, infusion_start, duration in self.infusions:
            infusion_end = infusion_start + duration
            if start <= infusion_start <= end:
                events.append(infusion_start)
            if start <= infusion_end <= end:
                events.append(infusion_end)
        return sorted(set(events))


class Model:
    """One central, and as many peripheral compartments as you want.

    route="sc" adds an absorption depot.
    """
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self,
                 central_volume=1,
                 clearance=0,
                 peripheral_volumes=None,
                 intercompartmental_clearances=None,
                 route="iv",
                 absorption_rate=None,
                 name="PK model"):
        """Initialize the pharmacokinetic model parameters and compartments.

        Args:
            central_volume (float): Volume of the central compartment.
            clearance (float): Elimination clearance rate from central compartment.
            peripheral_volumes (list of float, optional): Volumes of peripheral compartments.
            intercompartmental_clearances (list of float, optional): Clearance rates 
                between central and peripheral compartments.
            route (str, optional): Dosing route, either 'iv' or 'sc'. Defaults to 'iv'.
            absorption_rate (float, optional): Absorption rate constant for subcutaneous route.
            name (str, optional): Name of the model. Defaults to "PK model".
        """
        if not isinstance(route, str):
            raise ValueError("route should be 'iv' or 'sc'")
        self.central_volume = float(central_volume)
        self.clearance = float(clearance)
        self.peripheral_volumes = (
            list(peripheral_volumes) if peripheral_volumes is not None else []
        )
        self.intercompartmental_clearances = list(
            intercompartmental_clearances
            if intercompartmental_clearances is not None else []
        )
        if not isinstance(name, str) or not name.strip():
            raise ValueError("give the model a name")
        self.name = name

        if (not numpy.isfinite(self.central_volume) or
                not numpy.isfinite(self.clearance) or
                self.central_volume <= 0 or self.clearance < 0):
            raise ValueError("volume must be positive; clearance can't be negative")
        if len(self.peripheral_volumes) != len(
                self.intercompartmental_clearances):
            raise ValueError("give each peripheral compartment a volume and clearance")
        if any(not numpy.isfinite(v) or v <= 0
               for v in self.peripheral_volumes):
            raise ValueError("peripheral volumes must be positive")
        if any(not numpy.isfinite(q) or q < 0
               for q in self.intercompartmental_clearances):
            raise ValueError("intercompartmental clearances can't be negative")

        if route.lower() in ("iv", "intravenous"):
            self.route = "iv"
            self.absorption_rate = None
        elif route.lower() in ("sc", "subcutaneous"):
            if absorption_rate is None:
                raise ValueError("SC models need a positive absorption rate")
            self.route = "sc"
            self.absorption_rate = float(absorption_rate)
            if (not numpy.isfinite(self.absorption_rate) or
                    self.absorption_rate <= 0):
                raise ValueError("SC models need a positive absorption rate")
        else:
            raise ValueError("route should be 'iv' or 'sc'")

    @property
    def state_names(self):
        """Return the list of state names for the model compartments."""
        names = ["central"]
        if self.route == "sc":
            names.insert(0, "depot")
        for i in range(len(self.peripheral_volumes)):
            names.append(f"peripheral_{i + 1}")
        return names

    @property
    def central_index(self):
        """Calculate the peripheral compartment concentration exchange."""
        if self.route == "sc":
            return 1
        return 0

    def rhs(self, _time, amounts, dose_rate=0):
        """Calculate the system of differential equations (right-hand side) at time t."""
        change = numpy.zeros(len(self.state_names))
        central = self.central_index

        if self.route == "sc":
            depot_absorption = self.absorption_rate * amounts[0]
            change[0] = dose_rate - depot_absorption
            central_input = depot_absorption
        else:
            central_input = dose_rate

        central_conc = amounts[central] / self.central_volume
        change[central] = (
            central_input - self.clearance * central_conc
        )

        # Each peripheral compartment exchanges drug only with the central one.
        for i, p_vol in enumerate(self.peripheral_volumes):
            p = central + i + 1
            peripheral_conc = amounts[p] / p_vol
            exchange = self.intercompartmental_clearances[i] * (
                central_conc - peripheral_conc
            )
            change[central] -= exchange
            change[p] += exchange

        return change
    # pylint: disable=too-many-branches
    def solve(self, protocol, times, initial=None):
        """Solve the PK model differential equations for a given protocol and timeframe."""
        times = numpy.asarray(times, dtype=float)
        if (times.ndim != 1 or len(times) < 2 or
                not numpy.all(numpy.isfinite(times)) or
                numpy.any(numpy.diff(times) <= 0)):
            raise ValueError("times should be a list of increasing values")
        if times[0] < 0:
            raise ValueError("times can't be negative")
        if not isinstance(protocol, Protocol):
            raise TypeError("protocol must be a Protocol instance")

        if initial is None:
            state = numpy.zeros(len(self.state_names))
        elif isinstance(initial, dict):
            unknown = set(initial) - set(self.state_names)
            if unknown:
                raise ValueError(f"unknown initial compartment: {unknown.pop()}")
            state = numpy.array([initial.get(n, 0) for n in self.state_names],
                                dtype=float)
        else:
            state = numpy.array(initial, dtype=float)
        if (state.shape != (len(self.state_names),) or
                not numpy.all(numpy.isfinite(state)) or numpy.any(state < 0)):
            raise ValueError("initial amounts don't match the model?")

        answer = numpy.zeros((len(state), len(times)))
        now = 0.0
        # Start at zero so an earlier dose still counts.
        state[0] += protocol.dose_at(now)
        if times[0] == 0:
            answer[:, 0] = state
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
                lambda t, y, r=rate: self.rhs(t, y, r),
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

        return Solution(self, times, answer)


class Solution:
    """Stores and visualises results of the PK model simulation"""
    def __init__(self, model, times, amounts):
        self.model = model
        self.times = times
        self.amounts = amounts
        self.name = model.name

    def amount(self, compartment="central"):
        """Get the amount in one compartment over time."""
        return self.amounts[self.model.state_names.index(compartment)]

    def concentration(self, compartment="central"):
        """Get amount divided by compartment volume."""
        i = self.model.state_names.index(compartment)
        if compartment == "depot":
            raise ValueError("the depot has no volume, so it has no concentration")
        if compartment == "central":
            volume = self.model.central_volume
        else:
            volume = self.model.peripheral_volumes[i - self.model.central_index - 1]
        return self.amount(compartment) / volume

    def plot(self, quantity="concentration", compartments=None):
        """Plot the amounts or concentrations."""

        if quantity not in ("amount", "concentration"):
            raise ValueError("quantity should be 'amount' or 'concentration'")
        if compartments is None:
            compartments = self.model.state_names
            if quantity == "concentration":
                compartments = [x for x in compartments if x != "depot"]
        else:
            compartments = tuple(compartments)

        if not compartments:
            raise ValueError("pick at least one compartment")
        for compartment in compartments:
            if quantity == "amount":
                values = self.amount(compartment)
                unit = "ng"
            else:
                values = self.concentration(compartment)
                unit = "ng/mL"
            plt.plot(self.times, values, label=f"{self.name}: {compartment}")

        plt.xlabel("Time [h]")
        plt.ylabel(f"Drug amount [{unit}]" if quantity == "amount"
                   else f"Concentration [{unit}]")
        plt.legend()
        return plt.gca()

    def compare(self, other, quantity="concentration", compartments=None):
        """Put this run and another one on the same plot."""
        self.plot(quantity, compartments)
        other.plot(quantity, compartments)
        return self
