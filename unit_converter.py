"""
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version. This program is distributed in the hope that
it will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.

example usage:
unit_conversion_factor("lb", "kg")

author: Ingvar Out
"""

import re


# ref: https://en.wikipedia.org/wiki/International_System_of_Units
#   Only exceptions are we use 'g' instead of 'kg'.
UNITS_SI = {
    "s", "m", "g", "A", "K", "mol", "cd", "rad", "sr", "Hz", "N", "Pa", "J",
    "W", "C", "V", "F", "Ohm", "S", "Wb", "T", "H", "Celsius", "lm", "lx",
    "Bq", "Gy", "Sv", "kat"
}

PREFIX_SI = {
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "mu": 1e-6,
    "m": 1e-3,
    "c": 1e-2,
    "d": 1e-1,
    "da": 1e1,
    "h": 1e2,
    "k": 1e3,
    "M": 1e6,
    "G": 1e9,
    "T": 1e12,
    "P": 1e15
}

NON_SI_MAP = {
    "in": ("m", 0.0254),
    "ft": ("m", 0.3048),
    "yd": ("m", 0.9144),
    "mi": ("m", 1609.344),
    "gr": ("g", 0.06479891),
    "oz": ("g", 28.3495231),
    "qr": ("g", 11339.80925),
    "qtr": ("g", 11339.80925),
    "st": ("g", 6350.29318),
    "lb": ("g", 453.59237),
    "t": ("g", 907184.74),
    "floz": ("m^3", 2.95735296e-5),
    "gi": ("m^3", 1.18294118e-4),
    "pt": ("m^3", 4.73176473e-4),
    "qt": ("m^3", 9.46352946e-4),
    "gal": ("m^3", 3.78541178),
    "acre": ("m^2", 4046.85642),
    "h": ("s", 3600),
    "lightyear": ("m", 9.4605284e15),
    "l": ("m^3", 0.001)
}

def units_compatible(unit1: str, unit2: str) -> bool:
    """Return True if units can be converted to one another.
    
    Is true if units have the same exponents.
    """
    _ensure_si_unit(unit1)
    _ensure_si_unit(unit2)
    unit1_noprefix = re.sub("[a-zA-Z]+", lambda res: _get_si_unit(res[0])[0], unit1)
    unit2_noprefix = re.sub("[a-zA-Z]+", lambda res: _get_si_unit(res[0])[0], unit2)
    unit1_exponents = _get_unit_exponents(unit1_noprefix)
    unit2_exponents = _get_unit_exponents(unit2_noprefix)
    if len(unit1_exponents) != len(unit2_exponents):
        return False
    for name, exponent in unit1_exponents.items():
        if unit2_exponents.get(name, "") != exponent:
            return False
    return True


def unit_conversion_factor(source_unit: str, target_unit: str) -> float:
    """Get conversion factor between units."""
    if factor := _conversion_factor_cache.get((source_unit, target_unit), None):
        return factor
    if not units_compatible(source_unit, target_unit):
        raise NameError(f"Units incompatible: '{source_unit}', '{target_unit}'")
    source_exponents = _get_unit_exponents(source_unit)
    target_exponents = _get_unit_exponents(target_unit)

    multiplier_source = multiplier_target = 1.0
    for unit, exponent in source_exponents.items():
        multiplier_source *= _get_si_unit(unit)[1] ** exponent
    for unit, exponent in target_exponents.items():
        multiplier_target *= _get_si_unit(unit)[1] ** exponent

    if (source_unit, target_unit) not in _conversion_factor_cache:
        _conversion_factor_cache[(source_unit, target_unit)] = (
            multiplier_source / multiplier_target
        )
    return multiplier_source / multiplier_target


def _get_unit_exponents(unit: str) -> dict[str, float]:
    """Get power for each separate SI unit in 'unit'."""
    _ensure_si_unit(unit)
    unit_exponents = {unit[0]: 1.0 for unit in re.finditer(r"[a-zA-Z]+", unit)}
    # remove spaces to make our live a bit easier, but separate units by '*'
    _unit = re.sub(r"(?<=[^/*])\s+(?=[^/*])", "*", unit)
    _unit = _unit.replace(" ", "")

    # remove brackets recursively (inner to outer)
    while bracket_content := re.search(r"\([^()]*\)", _unit):
        str_post = _unit[bracket_content.regs[0][1]:]
        str_pre = _unit[:bracket_content.regs[0][0]]

        # handle exponent if present
        exponent = 1.0
        if str_post and str_post[0] == "^":
            res = re.match(r"([0-9]+/[0-9]+|[0-9]+)", str_post[1:])
            if "/" in res[0]:
                num, denom = res[0].split("/")
                exponent *= float(num) / float(denom)
            else:
                exponent *= float(res[0])
            str_post = str_post[res.regs[0][1] + 1:]

        # handle division if present
        if str_pre and str_pre[-1] == "/":
            str_pre = str_pre[:-1] + "*"
            exponent *= -1

        # set exponent per unit in bracket
        for res in re.finditer(r"[a-zA-Z]+", bracket_content[0]):
            unit_exponents[res[0]] *= exponent

        _unit = str_pre + bracket_content[0][1:-1] + str_post

    # handle individual exponents
    for res in re.finditer(r"[a-zA-Z]+\^", _unit):
        unit_ = _unit[res.regs[0][0]:res.regs[0][1] - 1]
        str_post = _unit[res.regs[0][1]:]
        exponent_str = re.match(r"([0-9]+/[0-9]+|[0-9]+)", str_post)[0]
        if "/" in exponent_str:
            num, denom = exponent_str.split("/")
            unit_exponents[unit_] *= float(num) / float(denom)
        else:
            unit_exponents[unit_] *= float(exponent_str)

    # handle individual divisions
    for res in re.finditer(r"/[a-zA-Z]+", _unit):
        unit_ = _unit[res.regs[0][0] + 1:res.regs[0][1]]
        unit_exponents[unit_] *= -1

    return unit_exponents


def _get_si_unit(unit: str) -> tuple[str, float] | None:
    """Find matching SI unit

    :return: (SI unit, prefix multiplier)
    """
    for unit_si in UNITS_SI:
        if not (res := re.search(unit_si + "$", unit)):
            continue
        if res.regs[0][0] == 0:
            return unit_si, 1.0
        if (prefix := unit[:res.regs[0][0]]) in PREFIX_SI:
            return unit_si, PREFIX_SI[prefix]
    if unit in NON_SI_MAP:
        return NON_SI_MAP[unit]
    return None


def _ensure_si_unit(unit: str) -> bool:
    """Check if string format is a valid SI Unit or convertible to one."""
    if res := re.search(r"[^a-zA-Z0-9/*\^\(\)\[\] ]", unit):
        raise NameError(f"invalid character '{res[0]}' (found in {unit})")
    if unit.count("(") != unit.count(")"):
        raise NameError(f"unbalanced brackets (found in {unit})")
    for res in re.finditer(r"[a-zA-Z]+", unit):
        if not _get_si_unit(res[0]):
            raise NameError(f"{res[0]} not a valid unit (found in {unit})")


_conversion_factor_cache: dict[tuple[str, str], float] = {}

if __name__ == "__main__":
    # Example usage:
    print(
        "To convert from GHz to MHz, multiply by",
        unit_conversion_factor(source_unit="GHz", target_unit="MHz")
    )
    print(
        "To convert from m/s^2 to km/ms^2, multiply by",
        unit_conversion_factor(source_unit="m/s^2", target_unit="km/ms^2")
    )
    print(
        "To convert from m/s^2 to km/h^2, multiply by",
        unit_conversion_factor(source_unit="m/s^2", target_unit="km/h^2")
    )
    print(
        "To convert from pound to kilogram, multiply by",
        unit_conversion_factor(source_unit="lb", target_unit="kg")
    )
