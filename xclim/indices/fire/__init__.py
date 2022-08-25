# noqa: D205,D400
from __future__ import annotations
import xarray as xr

import warnings

from ._ffdi import *
from ._cffwis import *
from xclim.core.units import declare_units


@declare_units(
    tas="[temperature]",
    pr="[precipitation]",
    sfcWind="[speed]",
    hurs="[]",
    lat="[]",
    snd="[length]",
    ffmc0="[]",
    dmc0="[]",
    dc0="[]",
    season_mask="[]",
)
def fire_weather_indexes(
    tas: xr.DataArray,
    pr: xr.DataArray,
    sfcWind: xr.DataArray,
    hurs: xr.DataArray,
    lat: xr.DataArray,
    snd: xr.DataArray | None = None,
    ffmc0: xr.DataArray | None = None,
    dmc0: xr.DataArray | None = None,
    dc0: xr.DataArray | None = None,
    season_mask: xr.DataArray | None = None,
    season_method: str | None = None,
    overwintering: bool = False,
    dry_start: str | None = None,
    initial_start_up: bool = True,
    **params,
):
    warnings.warn(
        f"`fire_weather_indexes` is deprecated in xclim v0.37.18-beta and has been renamed to `cffwis_indices` "
        f"to better support international collaboration. The `fire_weather_indexes` alias will be removed "
        f"in xclim v0.39.\n"
        "Please take note that xclim now offers a dedicated `fire` submodule under `xclim.indices` that houses all "
        "fire-based indices.",
        DeprecationWarning,
        stacklevel=2,
    )
    return cffwis_indices(
        tas,
        pr,
        sfcWind,
        hurs,
        lat,
        snd,
        ffmc0,
        dmc0,
        dc0,
        season_mask,
        season_method,
        overwintering,
        dry_start,
        initial_start_up,
        **params,
    )