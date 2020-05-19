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

from .. import data

import pytest

@pytest.mark.parametrize("res", data.resolutions)
@pytest.mark.parametrize("stream", data.streams[1:])
def test_open_vars(res, stream):
    for v in data.stream_vars(stream, res=res):
        d = data.open_var(stream, v, res)

        for dim in d.dims:
            if dim != 'time':
                d = d.isel({dim: 0})

        d = d.load()

        print(res, stream, v, d.size, d.values[0], '...', d.values[-1])
