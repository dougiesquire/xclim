# noqa: D205,D400
"""
Measures Submodule
==================
SDBA diagnostic tests are made up of properties and measures. Measures compare adjusted simulations to a reference,
through statistical properties or directly. This framework for the diagnostic tests was inspired by the
`VALUE <http://www.value-cost.eu/>`_ project.

"""
from __future__ import annotations

import numpy as np
import xarray as xr

from xclim import sdba
from xclim.core.indicator import Indicator, base_registry
from xclim.core.units import convert_units_to, ensure_delta, units2pint
from xclim.core.utils import InputKind


class StatisticalMeasure(Indicator):
    """Base indicator class for statistical measures used when validating bias-adjusted outputs.

    Statistical measures either use input data where the time dimension was reduced, or they combine
    the reduction with the measure. They usually take two arrays as input: "sim" and "ref", "sim" being
    measured against "ref".

    Statistical measures are generally unit-generic. If the inputs have different units, "sim" is converted
    to match "ref".
    """

    realm = "generic"

    @classmethod
    def _ensure_correct_parameters(cls, parameters):
        inputs = {k for k, p in parameters.items() if p.kind == InputKind.VARIABLE}
        if not inputs.issuperset({"sim", "ref"}):
            raise ValueError(
                f"{cls.__name__} requires 'sim' and 'ref' as inputs. Got {inputs}."
            )
        return super()._ensure_correct_parameters(parameters)

    def _preprocess_and_checks(self, das, params):
        """Perform parent's checks and also check convert units so that sim matches ref."""
        das, params = super()._preprocess_and_checks(das, params)

        # Convert grouping and check if allowed:
        sim = das["sim"]
        ref = das["ref"]
        units_sim = units2pint(sim)
        units_ref = units2pint(ref)

        if units_sim != units_ref:
            das["sim"] = convert_units_to(sim, ref)

        return das, params


base_registry["StatisticalMeasure"] = StatisticalMeasure


def _bias(sim: xr.DataArray, ref: xr.DataArray) -> xr.DataArray:
    """Bias.

    The bias is the simulation minus the reference.

    Parameters
    ----------
    sim : xr.DataArray
      data from the simulation (one value for each grid-point)
    ref : xr.DataArray
      data from the reference (observations) (one value for each grid-point)

    Returns
    -------
    xr.DataArray, [same as ref]
      Absolute bias
    """
    out = sim - ref
    out.attrs["units"] = ensure_delta(ref.attrs["units"])
    return out


bias = StatisticalMeasure(identifier="bias", compute=_bias)


def _relative_bias(sim: xr.DataArray, ref: xr.DataArray) -> xr.DataArray:
    """Relative Bias.

    The relative bias is the simulation minus reference, divided by the reference.

    Parameters
    ----------
    sim : xr.DataArray
      data from the simulation (one value for each grid-point)
    ref : xr.DataArray
      data from the reference (observations) (one value for each grid-point)

    Returns
    -------
    xr.DataArray, [dimensionless]
      Relative bias
    """
    out = (sim - ref) / ref
    return out.assign_attrs(units="")


relative_bias = StatisticalMeasure(
    identifier="relative_bias", compute=_relative_bias, units=""
)


def _circular_bias(sim: xr.DataArray, ref: xr.DataArray) -> xr.DataArray:
    """Circular bias.

    Bias considering circular time series.
    E.g. The bias between doy 365 and doy 1 is 364, but the circular bias is -1.

    Parameters
    ----------
    sim : xr.DataArray
      data from the simulation (one value for each grid-point)
    ref : xr.DataArray
      data from the reference (observations) (one value for each grid-point)

    Returns
    -------
    xr.DataArray, [days]
      Circular bias
    """
    out = (sim - ref) % 365
    out = out.where(
        out <= 365 / 2, 365 - out
    )  # when condition false, replace by 2nd arg
    out = out.where(ref >= sim, out * -1)  # when condition false, replace by 2nd arg
    return out.assign_attrs(units="days")


circular_bias = StatisticalMeasure(
    identifier="circular_bias", compute=_circular_bias, units="days"
)


def _ratio(sim: xr.DataArray, ref: xr.DataArray) -> xr.DataArray:
    """Ratio.

    The ratio is the quotient of the simulation over the reference.

    Parameters
    ----------
    sim : xr.DataArray
      data from the simulation (one value for each grid-point)
    ref : xr.DataArray
      data from the reference (observations) (one value for each grid-point)

    Returns
    -------
    xr.DataArray, [dimensionless]
      Ratio
    """
    out = sim / ref
    out.attrs["units"] = ""
    return out


ratio = StatisticalMeasure(identifier="ratio", compute=_ratio, units="")


def _rmse(sim: xr.DataArray, ref: xr.DataArray) -> xr.DataArray:
    """Root mean square error.

    The root mean square error on the time dimension between the simulation and the reference.

    Parameters
    ----------
    sim : xr.DataArray
      Data from the simulation (a time-series for each grid-point)
    ref : xr.DataArray
      Data from the reference (observations) (a time-series for each grid-point)

    Returns
    -------
    xr.DataArray, [same as ref]
      Root mean square error
    """

    def _rmse(sim, ref):
        return np.sqrt(np.mean((sim - ref) ** 2, axis=-1))

    out = xr.apply_ufunc(
        _rmse,
        sim,
        ref,
        input_core_dims=[["time"], ["time"]],
        dask="parallelized",
    )
    return out.assign_attrs(units=ensure_delta(ref.units))


rmse = StatisticalMeasure(identifier="rmse", compute=_rmse)


def _mae(sim: xr.DataArray, ref: xr.DataArray) -> xr.DataArray:
    """Mean absolute error.

    The mean absolute error on the time dimension between the simulation and the reference.

    Parameters
    ----------
    sim : xr.DataArray
      data from the simulation (a time-series for each grid-point)
    ref : xr.DataArray
      data from the reference (observations) (a time-series for each grid-point)

    Returns
    -------
    xr.DataArray, [same as ref]
      Mean absolute error
    """

    def _mae(sim, ref):
        return np.mean(np.abs(sim - ref), axis=-1)

    out = xr.apply_ufunc(
        _mae,
        sim,
        ref,
        input_core_dims=[["time"], ["time"]],
        dask="parallelized",
    )
    return out.assign_attrs(units=ensure_delta(ref.units))


mae = StatisticalMeasure(identifier="mae", compute=_mae)


def _annual_cycle_correlation(
    sim: xr.DataArray, ref: xr.DataArray, window: int = 15
) -> xr.DataArray:
    """Annual cycle correlation.

    Pearson correlation coefficient between the smooth day-of-year averaged annual cycles of the simulation and
    the reference. In the smooth day-of-year averaged annual cycles, each day-of-year is averaged over all years
    and over a window of days around that day.

    Parameters
    ----------
    sim : xr.DataArray
      data from the simulation (a time-series for each grid-point)
    ref : xr.DataArray
      data from the reference (observations) (a time-series for each grid-point)
    window: int
      Size of window around each day of year around which to take the mean.
      E.g. If window=31, Jan 1st is averaged over from December 17th to January 16th.

    Returns
    -------
    xr.DataArray, [dimensionless]
      Annual cycle correlation
    """
    # group by day-of-year and window around each doy
    grouper_test = sdba.base.Grouper("time.dayofyear", window=window)
    # for each day, mean over X day window and over all years to create a smooth avg annual cycle
    sim_annual_cycle = grouper_test.apply("mean", sim)
    ref_annual_cycle = grouper_test.apply("mean", ref)
    out = xr.corr(ref_annual_cycle, sim_annual_cycle, dim="dayofyear")
    return out.assign_attrs(units="")


annual_cycle_correlation = StatisticalMeasure(
    identifier="annual_cycle_correlation", compute=_annual_cycle_correlation
)
