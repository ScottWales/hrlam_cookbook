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

import xarray
import dask.array
from PIL import Image
import PIL
from pathlib import Path
import numpy
import matplotlib.cm

streams = ['spec','cldrad','mdl','slv','vis']
domain_centre = [133.26, -27.8]
domain_scale = 0.0036*13194*1.4


def stream_vars(stream):
    """
    List variables available in stream
    """
    root = Path(f"/scratch/ly62/output/u-bq574/d0036/{stream}")
    return [x.name for x in root.iterdir()]


def open_d0036_var(stream, var):
    """
    Open a variable
    """

    if stream == 'fx':
        chunks = {"latitude": 1000, "longitude": 1000}
        return xarray.open_dataset(f'/scratch/ly62/output/u-bq574/d0036/{stream}/{var}.nc', chunks=chunks)[var]

    chunks = {"latitude": 1000, "longitude": 1000, "time": 1}
    da = xarray.open_mfdataset(
        f"/scratch/ly62/output/u-bq574/d0036/{stream}/{var}/d0036.{stream}.{var}.*.nc",
        combine="nested",
        concat_dim="time",
        chunks=chunks,
        parallel=True,
    )[var]
    return da


def open_expt_var(stream, var, expt='400m'):
    """
    Open a variable
    """
    assert expt in ['400m', 'BARRA_R', 'BARRA_SY', 'BARRA_TA']
    if expt=='400m':
        return open_d0036_var(stream, var)
    if expt.startswith('BARRA'):
        from glob import glob
        paths = sorted(glob(f'/g/data/ua8/HighResLAM/BARRA/{expt}/{var}-fc-{stream}-PT10M-BARRA_R-v1-*.nc'))
        dss = [xarray.open_dataset(p, chunks={'time': -1}).isel(time=slice(0,6*6)) for p in paths]
        
        return xarray.concat(dss, dim='time')[var]
    raise Exception(f'{expt}, {stream}, {var} not found')

    
def vegfrac_background():
    """
    Returns a RGB image from the vegetation types
    """
    vegfrac = open_d0036_var('fx','surf_type_frac')

    imagesize = vegfrac[0,:,:].T.shape

    image = Image.new(mode='RGBA', size=imagesize, color=(100,130,184,255))

    colors = [
        (23,124,26,0), # broadleaf tree
        (23,124,26,0), # needleleaf tree
        (226,184,79,0), # temperate grass
        (226,184,79,0), # tropical grass
        (104,177,70,0), # shrubs
        (166,170,160,0), # urban
        (100,130,184,0), # inland water
        (232,153,96,0), # soil
    ]

    for vegtype in range(8):
        frac8 = (vegfrac[vegtype, :, :] * 255).astype('i1').values
        fracalpha = Image.fromarray(frac8, mode='L')

        vegimage = Image.new(mode='RGBA', size=imagesize, color=colors[vegtype])

        vegimage.putalpha(fracalpha)

        image.alpha_composite(vegimage)

    return image


def composite_clouds(clouds, image):
    imagesize = image.size

    scale = {'low_cld': 0.8, 'mid_cld': 0.5, 'hi_cld': 0.3}
    colorscale = {'low_cld': 0.5, 'mid_cld': 0.7, 'hi_cld': 1}

    for field in ['low_cld', 'mid_cld', 'hi_cld']:
        f8 = (clouds[field] * scale[field] * 255).astype('i1').values
        alpha = Image.fromarray(f8, mode='L')
        fimage = Image.new(mode='RGBA', size=imagesize, color=tuple(int(255*colorscale[field]) for i in range(4)))
        fimage.putalpha(alpha)

        fimage = fimage.convert(mode='RGBA')
        image.alpha_composite(fimage)

    return image


def render_image(data, cmap=None, vmin=None, vmax=None, alpha=True):
    if vmin is None:
        vmin = data.min().data
    if vmax is None:
        vmax = data.max().data

    # Float 0 - 1
    raw = (numpy.clip(data.data, vmin, vmax) - vmin) / (vmax - vmin)

    cmap = matplotlib.cm.get_cmap(cmap)

    def block_palette(block):
        img = cmap(block)

        if alpha:
            # Use the data as alpha
            img[:,:,3] = block

        return (255*img).astype('i1')

    img = raw.map_blocks(block_palette, dtype='i1', new_axis=2,
            chunks=(data.chunks[0], data.chunks[1], 4)).compute()

    image = Image.fromarray(img, mode='RGBA')

    return image


def zoom_image(data, image, centre=None, scale=None):
    if centre is None:
        centre = domain_centre
    if scale is None:
        scale = domain_scale

    lat0 = data.latitude[0]
    dlat = data.latitude[-1] - data.latitude[0]

    lon0 = data.longitude[0]
    dlon = data.longitude[-1] - data.longitude[0]

    x0 = ((centre[0] - scale/2) - lon0) / dlon * image.width 
    x1 = ((centre[0] + scale/2) - lon0) / dlon * image.width

    y0 = ((centre[1] - scale/2) - lat0) / dlat * image.height
    y1 = ((centre[1] + scale/2) - lat0) / dlat * image.height

    image = image.transform((1920, 1920), PIL.Image.QUAD,
            data=(x0, y1, x0, y0, x1, y0, x1, y1), resample=PIL.Image.NEAREST, fillcolor=(0,0,0,255))

    crop_amount = int(image.height - image.width * 9 / 16)
    image = image.crop((0, crop_amount // 2, image.width, image.height - crop_amount // 2))

    return image


def basic_stats(var, exclude_boundary):
    bound = exclude_boundary
    var = var.isel(latitude=slice(bound,-1-bound),longitude=slice(bound,-1-bound))

    dims = ['latitude', 'longitude']
    amin, amax, amean, astd = dask.compute(var.min(dims).data, var.max(dims).data, var.mean(dims).data, var.std(dims).data)
    return xarray.Dataset({'min': ('time', amin), 'max': ('time', amax), 'mean': ('time', amean), 'std': ('time', astd)}, coords={'time': var.time})
