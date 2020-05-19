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
from hrlam import *
import PIL
import dask.diagnostics

lcld = open_d0036_var('vis','low_cld')
mcld = open_d0036_var('vis','mid_cld')
hcld = open_d0036_var('vis','hi_cld')

clouds = xarray.Dataset({d.name: d for d in [lcld, mcld, hcld]})

def zoom_image(image, lat, lon, scale):
    lat0 = clouds.latitude[0]
    dlat = clouds.latitude[-1] - clouds.latitude[0]

    lon0 = clouds.longitude[0]
    dlon = clouds.longitude[-1] - clouds.longitude[0]

    x0 = ((lon - scale/2) - lon0) / dlon * image.width 
    x1 = ((lon + scale/2) - lon0) / dlon * image.width

    y0 = ((lat - scale/2) - lat0) / dlat * image.height
    y1 = ((lat + scale/2) - lat0) / dlat * image.height

    return image.transform((1920, 1920), PIL.Image.QUAD,
            data=(x0, y1, x0, y0, x1, y0, x1, y1), resample=PIL.Image.BICUBIC, fillcolor=(0,0,0,255))

with dask.diagnostics.ProgressBar():
    background = vegfrac_background()
    #background = PIL.Image.new(size=(13194,10554), mode='RGBA', color=(0,0,0,255))

    frame_count = clouds.sizes['time']

    lats = [-27.8, -20.0]
    lons = [133.26, 146.716]
    scales = [0.0036*13194*1.4, 0.5]

    offset = int(sys.argv[1])

    for frame in range(offset,clouds.sizes['time'],30):
        outpath = f'/scratch/ly62/vis/cloud_full_to_debbie/{frame:06d}.png'
        if os.path.exists(outpath):
            continue

        image = background.copy()
        image = composite_clouds(clouds.isel(time=frame), image)

        lat = lats[0] + (lats[1] - lats[0])/frame_count * frame
        lon = lons[0] + (lons[1] - lons[0])/frame_count * frame
        scale = scales[0] + (scales[1] - scales[0])/frame_count * frame

        image = zoom_image(image, lat, lon, scale)

        crop_amount = int(image.height - image.width * 9 / 16)
        image = image.crop((0, crop_amount // 2, image.width, image.height - crop_amount // 2))

        image.save(outpath)
        print(outpath)
