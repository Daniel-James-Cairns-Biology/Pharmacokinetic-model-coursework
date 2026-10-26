# Pharmacokinetic-model-coursework

Simulate intravenous(IV) or subcutaneous(SC) dosing in a central compartment with any number of
peripheral compartments. Protocols can be reused across models.

```bash
python -m pip install .
python -m pip install ".[dev]"
```

```python
import numpy
from pk_model import Model, Protocol

model = Model(central_volume=3000, clearance=300)
protocol = Protocol().add_bolus(1000)
solution = model.solve(protocol, numpy.linspace(0, 24, 241))
solution.plot()
```

Units: amount/dose in ng, volume in mL, time in hours, clearance in mL/h,

Run checks with `pytest`, `pytest --cov=pk_model`, and `ruff check .`. 

