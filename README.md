# py_unit_converter

A simple python module to calculate unit conversion factors.

To calculate the unit conversion factor between two units:

```python
>>> unit_conversion_factor(source_unit="lb", target_unit="kg")

0.45359237

>>> unit_conversion_factor("m/s^2","in/ms^2")

3.937007874015748e-05
```

To check if units are compatible:

```python
>>> units_compatible("lb/s", "kg/h")

True
```
