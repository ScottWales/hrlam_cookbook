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

from hrlam import *
import PIL
import os
from tqdm import tqdm
import smopy
import xarray


def main():
    grid = open_expt_var('fx', 'lnd_mask')
    bg = render_image(grid, vmin=0, vmax=1, cmap='Greys_r', alpha=False)

    fields = {
        'mslp': [99000, 102000],
        'spec_hum': [0, 0.025],
        'temp_scrn': [280,315],
        'max_refl': [-40,0],
        'accum_ls_prcp': [0,20],
        }

    fname = sys.argv[1]

    field = open_expt_var('spec', fname)
    vmin = field[0,:,:].min().values
    vmax = field[0,:,:].max().values
    print(vmin, vmax)

    vmin = fields[fname][0]
    vmax = fields[fname][1]

    locations = [
        ('full', domain_centre, domain_scale),
        ('mel', [144.963, -37.814], 2),
        ('debbie', [148.716, -20.267], 4),
        ('broome', [122.222, -17.957], 4),
        ]

    for f in tqdm(range(field.sizes['time'])):
        if os.path.exists(f'/scratch/ly62/vis/{fname}_{locations[-1][0]}_400/{f:06d}.png'):
            continue

        img = render_image(field.isel(time=f), vmin=vmin, vmax=vmax, alpha=False)
        img = PIL.Image.blend(img, bg, 0.05)

        for name, pos, scale in locations:
            outimg = zoom_image(grid, img, centre=pos, scale=scale)
            outpath = f'/scratch/ly62/vis/{fname}_{name}_400/{f:06d}.png'

            outimg.save(outpath)


if __name__ == '__main__':
    main()
