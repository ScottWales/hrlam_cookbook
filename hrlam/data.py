#!/usr/bin/env python
# Copyright 2020 Scott Wales
# author: Scott Wales <scott.wales@unimelb.edu.au>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import xarray
import glob

root_path = Path('/scratch/ly62/output/')

streams = ['fx', 'spec', 'slv', 'cldrad', 'mdl']
resolutions = ['d0036', 'd0198', 'BARRA_R']

res_alias = {
    '400m': 'd0036',
    '2km': 'd0198',
    }

res_expt = {
    'BARRA_R': None,
    'd0036': 'u-bq574',
    'd0198': 'u-bm651',
    }


def all_variables():
    """
    Iterator over all (resolution, stream, var) values
    """
    for r in resolutions:
        for s in streams:
            for v in stream_vars(r, s):
                yield r, s, v

def res_expt_id(res):
    """
    Resolve resolution alias and return the experiment id and true resolution
    """
    if res in res_alias:
        res = res_alias[res]

    return res_expt[res], res 


def stream_vars(res, stream):
    """
    List of the variables available within a stream 
    """

    if res == 'BARRA_R':
        if stream != 'spec':
            return []
        else:
            return ['accum_prcp', 'dewpt_scrn', 'hi_cld', 'low_cld', 'mid_cld', 'mslp', 'temp_scrn',
                'ttl_cld', 'uwnd10m', 'vwnd10m']

    expt, res = res_expt_id(res)
    root = root_path / expt / res / stream

    if not root.is_dir():
        raise AttributeError(f"No such stream: {root}")

    return [x.stem for x in root.iterdir()]


def open_barra_var(res, var):
    path = f'/g/data/ua8/HighResLAM/BARRA/{res}/{var}-fc-spec-PT10M-BARRA_R-v1-*.nc'

    dss = []
    for p in sorted(glob.glob(path)):
        ds = xarray.open_dataset(p)
        if 'dim0' in ds.dims:
            ds = ds.rename(dim0='time')
        ds = ds.isel(time=slice(0,36))
        dss.append(ds)

    return xarray.concat(dss, dim='time')[var]


def open_var(res, stream, var):
    """
    Open a variable
    """
    if res.startswith('BARRA') and stream == 'spec':
        return open_barra_var(res, var)

    expt, res = res_expt_id(res)

    if stream == 'fx':
        root = root_path / expt / res / stream
        basename = f"{var}.nc"
    else:
        root = root_path / expt / res / stream / var
        basename = f"{res}.{stream}.{var}.*.nc"

    if not root.is_dir():
        raise AttributeError(f"No such variable: {root}")
    
    # Set up chunks
    chunks = {'latitude': 1000, 'longitude': 1000}
    f0 = glob.glob(str(root/basename))[0]
    d0 = xarray.open_dataset(f0)[var].dims
    for d in d0:
        if d not in chunks:
            chunks[d] = 1

    ds = xarray.open_mfdataset(
        str(root / basename),
        combine="nested",
        concat_dim="time",
        compat="override",
        coords="all",
        chunks=chunks,
        parallel=True,
    )

    return ds[var]
