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


import sys
sys.path.append('../')

import os
import dask
import xarray
import climtas
import climtas.nci
import tempfile
import gc
from tqdm import tqdm
import pandas

from hrlam.data import all_variables, open_var

def process_var(res, stream, var):

    da = open_var(res, stream, var)

    if res == 'BARRA_R':
        da = da.sel(latitude=slice(-46.7972,-8.8064), longitude=slice(109.5108,157.0056))

    data = []

    if da.ndim == 4:
        for d in da.dims:
            if d not in ['time','latitude','longitude']:
                da = da.isel({d:0})

    for t in tqdm(range(da.sizes['time'])):
        s = da.isel(time=t)

        mn = s.min(['latitude','longitude'])
        mx = s.max(['latitude','longitude'])
        mean = s.mean(['latitude','longitude'])
        std = s.std(['latitude','longitude'])

        mn, mx, mean, std = dask.compute(mn, mx, mean, std)
        data.append([s.time.values, mn.values, mx.values, mean.values, std.values])

    return pandas.DataFrame(data, columns=['time','min','max','mean','std']).set_index('time')


if __name__ == '__main__':

    c = climtas.nci.GadiClient()

    for res, stream, var in all_variables():
        if stream == 'fx':
            continue

        outfile = f'stats/stats_{res}_{stream}_{var}.csv'

        if os.path.exists(outfile):
            continue

        print(res, stream, var)


        df = process_var(res, stream, var)

        df.to_csv(outfile)

