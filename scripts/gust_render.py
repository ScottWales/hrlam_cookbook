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

def main():
    grid = open_expt_var('fx', 'lnd_mask')
    background = vegfrac_background()

    start_pos = [144.963, -37.814]
    start_scale = 0.3

    end_pos= domain_centre
    end_scale = domain_scale

    fps = 30
    runtime = 60
    frames = fps * runtime

    field = open_expt_var('spec', 'wndgust10m')
    vmin = 5
    vmax = 30

    sample_rate = 1
    steps = field.sizes['time']/sample_rate
    last_step = -1
    img = None

    for f in tqdm(range(frames)):
        outpath = f'/scratch/ly62/vis/test/{f:06d}.png'
        if os.path.exists(outpath):
            continue

        frac = f/frames

        this_step = int(frac*steps)*sample_rate
        if this_step > last_step:
            rawimg = render_image(field.isel(time=this_step), vmin=vmin, vmax=vmax)
            img = PIL.Image.alpha_composite(background, rawimg)
            last_step = this_step

        pos = [0, 0]
        pos[0] = start_pos[0] + (end_pos[0] - start_pos[0])*frac
        pos[1] = start_pos[1] + (end_pos[1] - start_pos[1])*frac
        scale = start_scale + (end_scale - start_scale)*frac

        outimg = zoom_image(grid, img, centre=pos, scale=scale)

        outimg.save(outpath)


if __name__ == '__main__':
    main()

