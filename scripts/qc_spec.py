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

import hrlam
from climtaslocal.nci import GadiClient
import matplotlib.pyplot as plt
from tqdm import tqdm
import os

if __name__ == '__main__':
    c = GadiClient()
    print(c)
    stream = 'spec'

    for var in hrlam.stream_vars(stream):
        print(stream, var)
        outpath = f'stats/qc_stats_{stream}_{var}.png'

        if os.path.exists(outpath):
            print("Done",var)
            continue

        v = hrlam.open_expt_var(stream, var, expt='400m')

        if v.ndim > 3:
            print("Skipping",var)
            continue

        stats = hrlam.basic_stats(v, exclude_boundary=200)

        ymax = min(stats['max'].mean().values, (stats['mean'] + 3*stats['std']).mean().values)
        ymin = max(stats['min'].mean().values, (stats['mean'] - 3*stats['std']).mean().values)

        plt.figure(figsize=(10,10))

        plt.plot(stats.time, stats['mean'], '-', color='tab:blue')
        plt.fill_between(stats.time, stats['mean']+stats['std'], stats['mean']-stats['std'], color='tab:blue', alpha=0.3)
        plt.plot(stats.time, stats['min'], ':', color='tab:orange')
        plt.plot(stats.time, stats['max'], ':', color='tab:orange')

        #plt.ylim(ymin, ymax)
        #print(ymin, ymax)

        plt.title(f'{v.name} - {v.attrs["long_name"]}')
        plt.savefig(outpath)
        plt.close()
