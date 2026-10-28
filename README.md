# Pharmacokinetic-model-coursework

![GitHub last commit](https://img.shields.io/github/last-commit/Daniel-James-Cairns-Biology/Pharmacokinetic-model-coursework)
![Contributors](https://img.shields.io/github/contributors/Daniel-James-Cairns-Biology/Pharmacokinetic-model-coursework)

Simulate intravenous(IV) or subcutaneous(SC) dosing in a central compartment with either zero, one or two
peripheral compartments. Protocols can be reused across models.

```bash
python -m pip install .
python -m pip install ".[dev]"
```
if you wish to play snake then follow this installation (note snake requires python 3.12)
```bash
python -m pip install ".[snake]"
```
```python
import numpy
from pk_model import Model, Protocol

model = Model(central_volume=3000, clearance=300)
protocol = Protocol().add_bolus(1000)
solution = model.solve(protocol, numpy.linspace(0, 24, 241))
solution.plot()
```
Run checks with `pytest`, `pytest --cov=pk_model`, and `ruff check .`. 

## Variables

Our variables are just the drug density in each compartment. We denote them as:

* $q_c$ [ng] - drug density in central compartment
* $q_i$ [ng] - drug density in $i$ th peripheral compartment

And for the SC model, we also have:
* $q_s$ [ng] - drug density in 'skin' 

## Input Parameters

The user will be prompted to input various parameters in order to specify the model. For the IV model, these are:

* $\mathcal{D}(t)$ =  Dose($t$) [ng/h] - The dosing function which can be either continuous or discrete (or neither!)
* $V_c$ [ml] - volume of central compartment
* $V_i$ [ml] - volume of $i$ th peripheral compartment
* $C$ [ml/h] - clearance rate from the central compartment
* $Q_i$ [ml/h] - transition rate between central compartment and $i$ th peripheral compartment


And for the SC model, we also have:
* $k_a$ [1/h] - subcutaneous absorption rate 

## Diagram

This is the diagram for the intravenous (IV) model,

<img width="635" height="179" alt="Screenshot 2026-10-27 at 14 54 02" src="https://github.com/user-attachments/assets/7ebab58b-4de6-4f8b-81c9-ae3838adbdd7" />

and this is the diagram for the subcutaneous (SC) model.

<img width="806" height="205" alt="Screenshot 2026-10-27 at 14 43 23" src="https://github.com/user-attachments/assets/4bb8e220-bdea-456d-91e0-4b54daf09c83" />

## ODE System

For the IV model, our ODE system is 

$$\frac{\text{d}q_c}{\text{d}t} = \mathcal{D}(t) - \frac{q_c}{V_c}C - Q_1\left(\frac{q_c}{V_c}-\frac{q_1}{V_1}\right) - Q_2\left(\frac{q_c}{V_c}-\frac{q_2}{V_2}\right), $$
$$\frac{\text{d}q_1}{\text{d}t} = Q_1\left(\frac{q_c}{V_c}-\frac{q_1}{V_1}\right), $$
$$\frac{\text{d}q_2}{\text{d}t} = Q_2\left(\frac{q_c}{V_c}-\frac{q_2}{V_2}\right), $$

and for the SC model, the system is

$$\frac{\text{d}q_s}{\text{d}t} = \mathcal{D}(t) - k_a q_s, $$
$$\frac{\text{d}q_c}{\text{d}t} = k_a q_s - \frac{q_c}{V_c}C - Q_1\left(\frac{q_c}{V_c}-\frac{q_1}{V_1}\right) - Q_2\left(\frac{q_c}{V_c}-\frac{q_2}{V_2}\right), $$
$$\frac{\text{d}q_1}{\text{d}t} = Q_1\left(\frac{q_c}{V_c}-\frac{q_1}{V_1}\right), $$
$$\frac{\text{d}q_2}{\text{d}t} = Q_2\left(\frac{q_c}{V_c}-\frac{q_2}{V_2}\right). $$



