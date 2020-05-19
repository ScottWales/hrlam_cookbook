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
import pandas
import matplotlib.pyplot as plt

from hrlam.data import all_variables, open_var

def read_stats(res, stream, var):
    infile = f'stats/stats_{res}_{stream}_{var}.csv'
    return pandas.read_csv(infile, index_col='time', parse_dates=True)

def plot_stats(ax, stats, color, label):
    ax.plot(stats.index, stats['min'], color=color, alpha=0.5)
    ax.plot(stats.index, stats['mean'], color=color, label=label)
    ax.plot(stats.index, stats['max'], color=color, alpha=0.5)
    ax.fill_between(stats.index, stats['mean']-stats['std'], stats['mean']+stats['std'], alpha=0.3, color=color)

for res, stream, var in all_variables():
    if res != 'd0036':
        continue
    if stream == 'fx':
        continue

    print(stream, var) 
    ax = plt.axes()

    da = open_var('d0198', stream, var)
    print(da)

    try:
        stats_barra = read_stats('BARRA_R', stream, var)
        plot_stats(ax, stats_barra, 'tab:green', 'BARRA (400m domain)')
    except FileNotFoundError:
        pass

    stats_2k = read_stats('d0198', stream, var)
    plot_stats(ax, stats_2k, 'tab:orange', '2km')

    stats_400 = read_stats(res, stream, var)
    plot_stats(ax, stats_400, 'tab:blue', '400m')


    ax.set_title(f'{stream} - {var}')
    ax.set_ylabel(da.attrs['long_name'])
    plt.legend(loc='lower left')
    plt.savefig(f'stats/{stream}_{var}.png')
    plt.close()
