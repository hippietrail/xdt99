#!/usr/bin/env python3

# xhm99: An HFE image manager that focuses on the TI 99
#
# Copyright (c) 2016-2022 Ralph Benzinger <xdt99@endlos.net>
#
# This program is part of the TI 99 Cross-Development Tools (xdt99).
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import sys
import platform
import os.path
import argparse
import xdm99 as xdm
from xcommon import Util, RContainer, CommandProcessor, GlobStore


VERSION = '3.5.1'

CONFIG = 'XHM99_CONFIG'


class HFEError(Exception):
    pass


class SDFormat:

    SECTORS = 9
    TRACK_LEN = 17 + 9 * 334 + 113  # 3136

    LEADIN = [0xaa, 0xa8, 0xa8, 0x22] + [0xaa] * (4 * 16)  # fc ff
    LV_LEADIN = 17
    LEADOUT = [0xaa] * (4 * 77) + [0xaa, 0x50] + [0x55] * (2 + 4 * 35)  # cannot decode
    LV_LEADOUT = 113

    ADDRESS_MARK = [0xaa, 0x88, 0xa8, 0x2a]  # fe
    V_ADDRESS_MARK = [0xfe]
    LV_ADDRESS_MARK = 1
    DATA_MARK = [0xaa, 0x88, 0x28, 0xaa]  # fb
    V_DATA_MARK = [0xfb]
    LV_DATA_MARK = 1

    PREGAP = [0x22] * (4 * 6)  # 00
    LV_PREGAP = 6
    GAP1 = [0xaa] * (4 * 11) + [0x22] * (4 * 6)  # ff 00
    LV_GAP1 = 17
    GAP2 = [0xaa] * (4 * 45)  # ff
    LV_GAP2 = 45

    SECTOR_INTERLEAVE = (0, 7, 5, 3, 1, 8, 6, 4, 2,  # offset 0
                         6, 4, 2, 0, 7, 5, 3, 1, 8,  # offset 6
                         3, 1, 8, 6, 4, 2, 0, 7, 5)  # offset 3
    SECTOR_INTERLEAVE_WTF = (4, 2, 0, 7, 5, 3, 1, 8, 6,
                             1, 8, 6, 4, 2, 0, 7, 5, 3,
                             7, 5, 3, 1, 8, 6, 4, 2, 0)

    # twisted encoded bytes with clock bits
    FM_CODES = [
        [0x22, 0x22, 0x22, 0x22], [0x22, 0x22, 0x22, 0xa2], [0x22, 0x22, 0x22, 0x2a],
        [0x22, 0x22, 0x22, 0xaa], [0x22, 0x22, 0xa2, 0x22], [0x22, 0x22, 0xa2, 0xa2],
        [0x22, 0x22, 0xa2, 0x2a], [0x22, 0x22, 0xa2, 0xaa], [0x22, 0x22, 0x2a, 0x22],
        [0x22, 0x22, 0x2a, 0xa2], [0x22, 0x22, 0x2a, 0x2a], [0x22, 0x22, 0x2a, 0xaa],
        [0x22, 0x22, 0xaa, 0x22], [0x22, 0x22, 0xaa, 0xa2], [0x22, 0x22, 0xaa, 0x2a],
        [0x22, 0x22, 0xaa, 0xaa], [0x22, 0xa2, 0x22, 0x22], [0x22, 0xa2, 0x22, 0xa2],
        [0x22, 0xa2, 0x22, 0x2a], [0x22, 0xa2, 0x22, 0xaa], [0x22, 0xa2, 0xa2, 0x22],
        [0x22, 0xa2, 0xa2, 0xa2], [0x22, 0xa2, 0xa2, 0x2a], [0x22, 0xa2, 0xa2, 0xaa],
        [0x22, 0xa2, 0x2a, 0x22], [0x22, 0xa2, 0x2a, 0xa2], [0x22, 0xa2, 0x2a, 0x2a],
        [0x22, 0xa2, 0x2a, 0xaa], [0x22, 0xa2, 0xaa, 0x22], [0x22, 0xa2, 0xaa, 0xa2],
        [0x22, 0xa2, 0xaa, 0x2a], [0x22, 0xa2, 0xaa, 0xaa], [0x22, 0x2a, 0x22, 0x22],
        [0x22, 0x2a, 0x22, 0xa2], [0x22, 0x2a, 0x22, 0x2a], [0x22, 0x2a, 0x22, 0xaa],
        [0x22, 0x2a, 0xa2, 0x22], [0x22, 0x2a, 0xa2, 0xa2], [0x22, 0x2a, 0xa2, 0x2a],
        [0x22, 0x2a, 0xa2, 0xaa], [0x22, 0x2a, 0x2a, 0x22], [0x22, 0x2a, 0x2a, 0xa2],
        [0x22, 0x2a, 0x2a, 0x2a], [0x22, 0x2a, 0x2a, 0xaa], [0x22, 0x2a, 0xaa, 0x22],
        [0x22, 0x2a, 0xaa, 0xa2], [0x22, 0x2a, 0xaa, 0x2a], [0x22, 0x2a, 0xaa, 0xaa],
        [0x22, 0xaa, 0x22, 0x22], [0x22, 0xaa, 0x22, 0xa2], [0x22, 0xaa, 0x22, 0x2a],
        [0x22, 0xaa, 0x22, 0xaa], [0x22, 0xaa, 0xa2, 0x22], [0x22, 0xaa, 0xa2, 0xa2],
        [0x22, 0xaa, 0xa2, 0x2a], [0x22, 0xaa, 0xa2, 0xaa], [0x22, 0xaa, 0x2a, 0x22],
        [0x22, 0xaa, 0x2a, 0xa2], [0x22, 0xaa, 0x2a, 0x2a], [0x22, 0xaa, 0x2a, 0xaa],
        [0x22, 0xaa, 0xaa, 0x22], [0x22, 0xaa, 0xaa, 0xa2], [0x22, 0xaa, 0xaa, 0x2a],
        [0x22, 0xaa, 0xaa, 0xaa], [0xa2, 0x22, 0x22, 0x22], [0xa2, 0x22, 0x22, 0xa2],
        [0xa2, 0x22, 0x22, 0x2a], [0xa2, 0x22, 0x22, 0xaa], [0xa2, 0x22, 0xa2, 0x22],
        [0xa2, 0x22, 0xa2, 0xa2], [0xa2, 0x22, 0xa2, 0x2a], [0xa2, 0x22, 0xa2, 0xaa],
        [0xa2, 0x22, 0x2a, 0x22], [0xa2, 0x22, 0x2a, 0xa2], [0xa2, 0x22, 0x2a, 0x2a],
        [0xa2, 0x22, 0x2a, 0xaa], [0xa2, 0x22, 0xaa, 0x22], [0xa2, 0x22, 0xaa, 0xa2],
        [0xa2, 0x22, 0xaa, 0x2a], [0xa2, 0x22, 0xaa, 0xaa], [0xa2, 0xa2, 0x22, 0x22],
        [0xa2, 0xa2, 0x22, 0xa2], [0xa2, 0xa2, 0x22, 0x2a], [0xa2, 0xa2, 0x22, 0xaa],
        [0xa2, 0xa2, 0xa2, 0x22], [0xa2, 0xa2, 0xa2, 0xa2], [0xa2, 0xa2, 0xa2, 0x2a],
        [0xa2, 0xa2, 0xa2, 0xaa], [0xa2, 0xa2, 0x2a, 0x22], [0xa2, 0xa2, 0x2a, 0xa2],
        [0xa2, 0xa2, 0x2a, 0x2a], [0xa2, 0xa2, 0x2a, 0xaa], [0xa2, 0xa2, 0xaa, 0x22],
        [0xa2, 0xa2, 0xaa, 0xa2], [0xa2, 0xa2, 0xaa, 0x2a], [0xa2, 0xa2, 0xaa, 0xaa],
        [0xa2, 0x2a, 0x22, 0x22], [0xa2, 0x2a, 0x22, 0xa2], [0xa2, 0x2a, 0x22, 0x2a],
        [0xa2, 0x2a, 0x22, 0xaa], [0xa2, 0x2a, 0xa2, 0x22], [0xa2, 0x2a, 0xa2, 0xa2],
        [0xa2, 0x2a, 0xa2, 0x2a], [0xa2, 0x2a, 0xa2, 0xaa], [0xa2, 0x2a, 0x2a, 0x22],
        [0xa2, 0x2a, 0x2a, 0xa2], [0xa2, 0x2a, 0x2a, 0x2a], [0xa2, 0x2a, 0x2a, 0xaa],
        [0xa2, 0x2a, 0xaa, 0x22], [0xa2, 0x2a, 0xaa, 0xa2], [0xa2, 0x2a, 0xaa, 0x2a],
        [0xa2, 0x2a, 0xaa, 0xaa], [0xa2, 0xaa, 0x22, 0x22], [0xa2, 0xaa, 0x22, 0xa2],
        [0xa2, 0xaa, 0x22, 0x2a], [0xa2, 0xaa, 0x22, 0xaa], [0xa2, 0xaa, 0xa2, 0x22],
        [0xa2, 0xaa, 0xa2, 0xa2], [0xa2, 0xaa, 0xa2, 0x2a], [0xa2, 0xaa, 0xa2, 0xaa],
        [0xa2, 0xaa, 0x2a, 0x22], [0xa2, 0xaa, 0x2a, 0xa2], [0xa2, 0xaa, 0x2a, 0x2a],
        [0xa2, 0xaa, 0x2a, 0xaa], [0xa2, 0xaa, 0xaa, 0x22], [0xa2, 0xaa, 0xaa, 0xa2],
        [0xa2, 0xaa, 0xaa, 0x2a], [0xa2, 0xaa, 0xaa, 0xaa], [0x2a, 0x22, 0x22, 0x22],
        [0x2a, 0x22, 0x22, 0xa2], [0x2a, 0x22, 0x22, 0x2a], [0x2a, 0x22, 0x22, 0xaa],
        [0x2a, 0x22, 0xa2, 0x22], [0x2a, 0x22, 0xa2, 0xa2], [0x2a, 0x22, 0xa2, 0x2a],
        [0x2a, 0x22, 0xa2, 0xaa], [0x2a, 0x22, 0x2a, 0x22], [0x2a, 0x22, 0x2a, 0xa2],
        [0x2a, 0x22, 0x2a, 0x2a], [0x2a, 0x22, 0x2a, 0xaa], [0x2a, 0x22, 0xaa, 0x22],
        [0x2a, 0x22, 0xaa, 0xa2], [0x2a, 0x22, 0xaa, 0x2a], [0x2a, 0x22, 0xaa, 0xaa],
        [0x2a, 0xa2, 0x22, 0x22], [0x2a, 0xa2, 0x22, 0xa2], [0x2a, 0xa2, 0x22, 0x2a],
        [0x2a, 0xa2, 0x22, 0xaa], [0x2a, 0xa2, 0xa2, 0x22], [0x2a, 0xa2, 0xa2, 0xa2],
        [0x2a, 0xa2, 0xa2, 0x2a], [0x2a, 0xa2, 0xa2, 0xaa], [0x2a, 0xa2, 0x2a, 0x22],
        [0x2a, 0xa2, 0x2a, 0xa2], [0x2a, 0xa2, 0x2a, 0x2a], [0x2a, 0xa2, 0x2a, 0xaa],
        [0x2a, 0xa2, 0xaa, 0x22], [0x2a, 0xa2, 0xaa, 0xa2], [0x2a, 0xa2, 0xaa, 0x2a],
        [0x2a, 0xa2, 0xaa, 0xaa], [0x2a, 0x2a, 0x22, 0x22], [0x2a, 0x2a, 0x22, 0xa2],
        [0x2a, 0x2a, 0x22, 0x2a], [0x2a, 0x2a, 0x22, 0xaa], [0x2a, 0x2a, 0xa2, 0x22],
        [0x2a, 0x2a, 0xa2, 0xa2], [0x2a, 0x2a, 0xa2, 0x2a], [0x2a, 0x2a, 0xa2, 0xaa],
        [0x2a, 0x2a, 0x2a, 0x22], [0x2a, 0x2a, 0x2a, 0xa2], [0x2a, 0x2a, 0x2a, 0x2a],
        [0x2a, 0x2a, 0x2a, 0xaa], [0x2a, 0x2a, 0xaa, 0x22], [0x2a, 0x2a, 0xaa, 0xa2],
        [0x2a, 0x2a, 0xaa, 0x2a], [0x2a, 0x2a, 0xaa, 0xaa], [0x2a, 0xaa, 0x22, 0x22],
        [0x2a, 0xaa, 0x22, 0xa2], [0x2a, 0xaa, 0x22, 0x2a], [0x2a, 0xaa, 0x22, 0xaa],
        [0x2a, 0xaa, 0xa2, 0x22], [0x2a, 0xaa, 0xa2, 0xa2], [0x2a, 0xaa, 0xa2, 0x2a],
        [0x2a, 0xaa, 0xa2, 0xaa], [0x2a, 0xaa, 0x2a, 0x22], [0x2a, 0xaa, 0x2a, 0xa2],
        [0x2a, 0xaa, 0x2a, 0x2a], [0x2a, 0xaa, 0x2a, 0xaa], [0x2a, 0xaa, 0xaa, 0x22],
        [0x2a, 0xaa, 0xaa, 0xa2], [0x2a, 0xaa, 0xaa, 0x2a], [0x2a, 0xaa, 0xaa, 0xaa],
        [0xaa, 0x22, 0x22, 0x22], [0xaa, 0x22, 0x22, 0xa2], [0xaa, 0x22, 0x22, 0x2a],
        [0xaa, 0x22, 0x22, 0xaa], [0xaa, 0x22, 0xa2, 0x22], [0xaa, 0x22, 0xa2, 0xa2],
        [0xaa, 0x22, 0xa2, 0x2a], [0xaa, 0x22, 0xa2, 0xaa], [0xaa, 0x22, 0x2a, 0x22],
        [0xaa, 0x22, 0x2a, 0xa2], [0xaa, 0x22, 0x2a, 0x2a], [0xaa, 0x22, 0x2a, 0xaa],
        [0xaa, 0x22, 0xaa, 0x22], [0xaa, 0x22, 0xaa, 0xa2], [0xaa, 0x22, 0xaa, 0x2a],
        [0xaa, 0x22, 0xaa, 0xaa], [0xaa, 0xa2, 0x22, 0x22], [0xaa, 0xa2, 0x22, 0xa2],
        [0xaa, 0xa2, 0x22, 0x2a], [0xaa, 0xa2, 0x22, 0xaa], [0xaa, 0xa2, 0xa2, 0x22],
        [0xaa, 0xa2, 0xa2, 0xa2], [0xaa, 0xa2, 0xa2, 0x2a], [0xaa, 0xa2, 0xa2, 0xaa],
        [0xaa, 0xa2, 0x2a, 0x22], [0xaa, 0xa2, 0x2a, 0xa2], [0xaa, 0xa2, 0x2a, 0x2a],
        [0xaa, 0xa2, 0x2a, 0xaa], [0xaa, 0xa2, 0xaa, 0x22], [0xaa, 0xa2, 0xaa, 0xa2],
        [0xaa, 0xa2, 0xaa, 0x2a], [0xaa, 0xa2, 0xaa, 0xaa], [0xaa, 0x2a, 0x22, 0x22],
        [0xaa, 0x2a, 0x22, 0xa2], [0xaa, 0x2a, 0x22, 0x2a], [0xaa, 0x2a, 0x22, 0xaa],
        [0xaa, 0x2a, 0xa2, 0x22], [0xaa, 0x2a, 0xa2, 0xa2], [0xaa, 0x2a, 0xa2, 0x2a],
        [0xaa, 0x2a, 0xa2, 0xaa], [0xaa, 0x2a, 0x2a, 0x22], [0xaa, 0x2a, 0x2a, 0xa2],
        [0xaa, 0x2a, 0x2a, 0x2a], [0xaa, 0x2a, 0x2a, 0xaa], [0xaa, 0x2a, 0xaa, 0x22],
        [0xaa, 0x2a, 0xaa, 0xa2], [0xaa, 0x2a, 0xaa, 0x2a], [0xaa, 0x2a, 0xaa, 0xaa],
        [0xaa, 0xaa, 0x22, 0x22], [0xaa, 0xaa, 0x22, 0xa2], [0xaa, 0xaa, 0x22, 0x2a],
        [0xaa, 0xaa, 0x22, 0xaa], [0xaa, 0xaa, 0xa2, 0x22], [0xaa, 0xaa, 0xa2, 0xa2],
        [0xaa, 0xaa, 0xa2, 0x2a], [0xaa, 0xaa, 0xa2, 0xaa], [0xaa, 0xaa, 0x2a, 0x22],
        [0xaa, 0xaa, 0x2a, 0xa2], [0xaa, 0xaa, 0x2a, 0x2a], [0xaa, 0xaa, 0x2a, 0xaa],
        [0xaa, 0xaa, 0xaa, 0x22], [0xaa, 0xaa, 0xaa, 0xa2], [0xaa, 0xaa, 0xaa, 0x2a],
        [0xaa, 0xaa, 0xaa, 0xaa]
    ]

    @classmethod
    def decode(cls, stream):
        """decode FM bit stream into bytes"""
        bytes_ = []
        for i in range(0, len(stream), 4):
            enc_byte = Util.rordl(stream[i:i + 4])
            # bit format:  ABCDEFGH <->  H...G... F...E... D...C... B...A...
            byte_ = ((0x01 if enc_byte & 0x80000000 else 0) |
                     (0x02 if enc_byte & 0x08000000 else 0) |
                     (0x04 if enc_byte & 0x00800000 else 0) |
                     (0x08 if enc_byte & 0x00080000 else 0) |
                     (0x10 if enc_byte & 0x00008000 else 0) |
                     (0x20 if enc_byte & 0x00000800 else 0) |
                     (0x40 if enc_byte & 0x00000080 else 0) |
                     (0x80 if enc_byte & 0x00000008 else 0))
            bytes_.append(byte_)
        return bytes_

    @classmethod
    def encode(cls, track):
        """encode SD track into FM bit stream"""
        stream = []
        for byte_ in track:
            stream.extend(cls.FM_CODES[byte_])
        return stream

    @classmethod
    def interleave(cls, side, track, sector, wtf_80t):
        if not wtf_80t or side == 0:
            return cls.SECTOR_INTERLEAVE[(track * cls.SECTORS + sector) % 27]
        elif track < 37:
            return cls.SECTOR_INTERLEAVE_WTF[(track * cls.SECTORS + sector) % 27]  # WTF?
        else:
            return cls.SECTOR_INTERLEAVE[((track - 37) * cls.SECTORS + sector) % 27]  # off-series

    @classmethod
    def fix_clocks(cls, stream):
        """fix clock bits in stream (inline)"""
        pass  # clocks are correct


class DDFormat:

    SECTORS = 18
    TRACK_LEN = 32 + 18 * 342 + 84  # 6272

    LEADIN = [0x49, 0x2a] * 32  # 4e
    LV_LEADIN = 32
    LEADOUT = [0x49, 0x2a] * 84  # 4e
    LV_LEADOUT = 84

    ADDRESS_MARK = [0x22, 0x91, 0x22, 0x91, 0x22, 0x91, 0xaa, 0x2a]
    ADDRESS_MARK_WORD = 0x2291
    V_ADDRESS_MARK = [0xa1, 0xa1, 0xa1, 0xfe]
    V_ADDRESS_MARK_BYTE = 0xa1
    LV_ADDRESS_MARK = 4
    DATA_MARK = [0x22, 0x91, 0x22, 0x91, 0x22, 0x91, 0xaa, 0xa2]
    V_DATA_MARK = [0xa1, 0xa1, 0xa1, 0xfb]
    LV_DATA_MARK = 4

    PREGAP = [0x55] * (2 * 12)  # 00
    LV_PREGAP = 12
    GAP1 = [0x49, 0x2a] * 22 + [0x55] * (2 * 12)  # 4e/00
    LV_GAP1 = 34
    GAP2 = [0x49, 0x2a] * 24  # 4e
    LV_GAP2 = 24

    SECTOR_INTERLEAVE = (0, 11, 4, 15, 8, 1, 12, 5, 16,
                         9, 2, 13, 6, 17, 10, 3, 14, 7)

    # computation rule: w = int(bs[7::-1], 2) * 256 + int(bs[:7:-1], 2)
    MVM_CODES = [
        [0x55, 0x55], [0x55, 0x95], [0x55, 0x25], [0x55, 0xa5],
        [0x55, 0x49], [0x55, 0x89], [0x55, 0x29], [0x55, 0xa9],
        [0x55, 0x52], [0x55, 0x92], [0x55, 0x22], [0x55, 0xa2],
        [0x55, 0x4a], [0x55, 0x8a], [0x55, 0x2a], [0x55, 0xaa],
        [0x95, 0x54], [0x95, 0x94], [0x95, 0x24], [0x95, 0xa4],
        [0x95, 0x48], [0x95, 0x88], [0x95, 0x28], [0x95, 0xa8],
        [0x95, 0x52], [0x95, 0x92], [0x95, 0x22], [0x95, 0xa2],
        [0x95, 0x4a], [0x95, 0x8a], [0x95, 0x2a], [0x95, 0xaa],
        [0x25, 0x55], [0x25, 0x95], [0x25, 0x25], [0x25, 0xa5],
        [0x25, 0x49], [0x25, 0x89], [0x25, 0x29], [0x25, 0xa9],
        [0x25, 0x52], [0x25, 0x92], [0x25, 0x22], [0x25, 0xa2],
        [0x25, 0x4a], [0x25, 0x8a], [0x25, 0x2a], [0x25, 0xaa],
        [0xa5, 0x54], [0xa5, 0x94], [0xa5, 0x24], [0xa5, 0xa4],
        [0xa5, 0x48], [0xa5, 0x88], [0xa5, 0x28], [0xa5, 0xa8],
        [0xa5, 0x52], [0xa5, 0x92], [0xa5, 0x22], [0xa5, 0xa2],
        [0xa5, 0x4a], [0xa5, 0x8a], [0xa5, 0x2a], [0xa5, 0xaa],
        [0x49, 0x55], [0x49, 0x95], [0x49, 0x25], [0x49, 0xa5],
        [0x49, 0x49], [0x49, 0x89], [0x49, 0x29], [0x49, 0xa9],
        [0x49, 0x52], [0x49, 0x92], [0x49, 0x22], [0x49, 0xa2],
        [0x49, 0x4a], [0x49, 0x8a], [0x49, 0x2a], [0x49, 0xaa],
        [0x89, 0x54], [0x89, 0x94], [0x89, 0x24], [0x89, 0xa4],
        [0x89, 0x48], [0x89, 0x88], [0x89, 0x28], [0x89, 0xa8],
        [0x89, 0x52], [0x89, 0x92], [0x89, 0x22], [0x89, 0xa2],
        [0x89, 0x4a], [0x89, 0x8a], [0x89, 0x2a], [0x89, 0xaa],
        [0x29, 0x55], [0x29, 0x95], [0x29, 0x25], [0x29, 0xa5],
        [0x29, 0x49], [0x29, 0x89], [0x29, 0x29], [0x29, 0xa9],
        [0x29, 0x52], [0x29, 0x92], [0x29, 0x22], [0x29, 0xa2],
        [0x29, 0x4a], [0x29, 0x8a], [0x29, 0x2a], [0x29, 0xaa],
        [0xa9, 0x54], [0xa9, 0x94], [0xa9, 0x24], [0xa9, 0xa4],
        [0xa9, 0x48], [0xa9, 0x88], [0xa9, 0x28], [0xa9, 0xa8],
        [0xa9, 0x52], [0xa9, 0x92], [0xa9, 0x22], [0xa9, 0xa2],
        [0xa9, 0x4a], [0xa9, 0x8a], [0xa9, 0x2a], [0xa9, 0xaa],
        [0x52, 0x55], [0x52, 0x95], [0x52, 0x25], [0x52, 0xa5],
        [0x52, 0x49], [0x52, 0x89], [0x52, 0x29], [0x52, 0xa9],
        [0x52, 0x52], [0x52, 0x92], [0x52, 0x22], [0x52, 0xa2],
        [0x52, 0x4a], [0x52, 0x8a], [0x52, 0x2a], [0x52, 0xaa],
        [0x92, 0x54], [0x92, 0x94], [0x92, 0x24], [0x92, 0xa4],
        [0x92, 0x48], [0x92, 0x88], [0x92, 0x28], [0x92, 0xa8],
        [0x92, 0x52], [0x92, 0x92], [0x92, 0x22], [0x92, 0xa2],
        [0x92, 0x4a], [0x92, 0x8a], [0x92, 0x2a], [0x92, 0xaa],
        [0x22, 0x55], [0x22, 0x95], [0x22, 0x25], [0x22, 0xa5],
        [0x22, 0x49], [0x22, 0x89], [0x22, 0x29], [0x22, 0xa9],
        [0x22, 0x52], [0x22, 0x92], [0x22, 0x22], [0x22, 0xa2],
        [0x22, 0x4a], [0x22, 0x8a], [0x22, 0x2a], [0x22, 0xaa],
        [0xa2, 0x54], [0xa2, 0x94], [0xa2, 0x24], [0xa2, 0xa4],
        [0xa2, 0x48], [0xa2, 0x88], [0xa2, 0x28], [0xa2, 0xa8],
        [0xa2, 0x52], [0xa2, 0x92], [0xa2, 0x22], [0xa2, 0xa2],
        [0xa2, 0x4a], [0xa2, 0x8a], [0xa2, 0x2a], [0xa2, 0xaa],
        [0x4a, 0x55], [0x4a, 0x95], [0x4a, 0x25], [0x4a, 0xa5],
        [0x4a, 0x49], [0x4a, 0x89], [0x4a, 0x29], [0x4a, 0xa9],
        [0x4a, 0x52], [0x4a, 0x92], [0x4a, 0x22], [0x4a, 0xa2],
        [0x4a, 0x4a], [0x4a, 0x8a], [0x4a, 0x2a], [0x4a, 0xaa],
        [0x8a, 0x54], [0x8a, 0x94], [0x8a, 0x24], [0x8a, 0xa4],
        [0x8a, 0x48], [0x8a, 0x88], [0x8a, 0x28], [0x8a, 0xa8],
        [0x8a, 0x52], [0x8a, 0x92], [0x8a, 0x22], [0x8a, 0xa2],
        [0x8a, 0x4a], [0x8a, 0x8a], [0x8a, 0x2a], [0x8a, 0xaa],
        [0x2a, 0x55], [0x2a, 0x95], [0x2a, 0x25], [0x2a, 0xa5],
        [0x2a, 0x49], [0x2a, 0x89], [0x2a, 0x29], [0x2a, 0xa9],
        [0x2a, 0x52], [0x2a, 0x92], [0x2a, 0x22], [0x2a, 0xa2],
        [0x2a, 0x4a], [0x2a, 0x8a], [0x2a, 0x2a], [0x2a, 0xaa],
        [0xaa, 0x54], [0xaa, 0x94], [0xaa, 0x24], [0xaa, 0xa4],
        [0xaa, 0x48], [0xaa, 0x88], [0xaa, 0x28], [0xaa, 0xa8],
        [0xaa, 0x52], [0xaa, 0x92], [0xaa, 0x22], [0xaa, 0xa2],
        [0xaa, 0x4a], [0xaa, 0x8a], [0xaa, 0x2a], [0xaa, 0xaa],
    ]

    @classmethod
    def interleave(cls, side, track, sector, wtf80t):
        return sector * 11 % cls.SECTORS

    @classmethod
    def decode(cls, stream):
        """decode MFM bit stream into bytes"""
        lookup = {(word[0] << 8) | word[1]: i for i, word in enumerate(cls.MVM_CODES)}
        bytes_ = []
        for idx in range(0, len(stream), 2):
            w = Util.ordw(stream[idx:idx + 2])
            if w == cls.ADDRESS_MARK_WORD:  # address mark
                b = cls.V_ADDRESS_MARK_BYTE
            else:
                try:
                    b = lookup[w]
                except KeyError:
                    # NOTE: no such collisions in lookup table!
                    b = lookup[w | 0x0100]  # extra clock bit
            bytes_.append(b)
        return bytes_

    @classmethod
    def encode(cls, track):
        """encode SD track into MFM bit stream"""
        stream = []
        for byte_ in track:
            w = cls.MVM_CODES[byte_]
            stream.extend(w)
        return stream

    @classmethod
    def fix_clocks(cls, stream):
        """fix clock bits in stream (inline)"""
        for idx in range(1, len(stream), 2):
            if stream[idx] & 0x80:
                stream[idx + 1] &= 0xfe


class HFEDisk:

    HFE_INTERFACE_MODE = 7
    HFE_BIT_RATE = 250

    HFE_SD_ENCODING = 2
    HFE_DD_ENCODING = 0
    VALID_ENCODINGS = [0, 2]

    def __init__(self, image):
        """create HFE disk from HFE image"""
        self.header = image[0:512]
        self.lut = image[512:1024]
        self.trackdata = image[1024:]

        self.tracks, self.sides, self.encoding, self.ifmode = self.get_hfe_params(self.header)
        if self.encoding != HFEDisk.HFE_SD_ENCODING and self.encoding != HFEDisk.HFE_DD_ENCODING:
            raise HFEError('Invalid encoding')
        self.dd = self.encoding == HFEDisk.HFE_DD_ENCODING
        if self.ifmode != 7:
            raise HFEError('Invalid mode')

    @classmethod
    def get_hfe_params(cls, image):
        """checks if image is HFE image"""
        if image[:8] != b'HXCPICFE':
            raise HFEError('Not a HFE image')
        return image[9], image[10], image[11], image[16]

    def to_disk_image(self):
        """extract sector data from HFE image"""
        tracks = self.get_tracks()
        return self.extract_sectors(tracks)

    def get_tracks(self):
        """return listing of decoded track data"""
        fmt = DDFormat if self.dd else SDFormat
        size = fmt.TRACK_LEN
        decode = fmt.decode
        chunks = list(Util.chop(self.trackdata, 256))
        side_0 = b''.join(chunks[0::2])
        side_1 = b''.join(chunks[1::2])
        tracks0 = list(Util.chop(decode(side_0), size))
        tracks1 = list(Util.chop(decode(side_1), size)) if self.sides == 2 else []
        tracks1.reverse()
        return tracks0 + tracks1

    def extract_sectors(self, tracks):
        """extract sector data from listing of track data"""
        fmt = DDFormat if self.dd else SDFormat
        sectors = []
        if len(tracks) != self.sides * self.tracks:
            raise HFEError('Invalid track count')
        assert len(tracks[0]) == fmt.TRACK_LEN
        for track in tracks:
            h0, h1 = 0, fmt.LV_LEADIN  # leadin is track[h0:h1]
            track_sectors = {}
            for i in range(fmt.SECTORS):
                # pregap
                h0, h1 = h1, h1 + fmt.LV_PREGAP
                # pregap at track[h0:h1]
                # ID address mark
                h0, h1 = h1, h1 + fmt.LV_ADDRESS_MARK
                address_mark = track[h0:h1]
                assert address_mark == fmt.V_ADDRESS_MARK
                # sector ID
                h0, h1 = h1, h1 + 6
                # track_id at track[h0]
                # side_id at track[h0 + 1]
                sector_id = track[h0 + 2]
                assert sector_id not in track_sectors
                # size_id at track[h0 + 3]
                # crc1 at track[h0 + 4:h0 + 6]
                # gap1
                h0, h1 = h1, h1 + fmt.LV_GAP1
                # gap1 at track[h0:h1]
                # data mark
                h0, h1 = h1, h1 + fmt.LV_DATA_MARK
                data_mark = track[h0:h1]
                assert data_mark == fmt.V_DATA_MARK
                # sector data
                h0, h1 = h1, h1 + 258
                track_sectors[sector_id] = track[h0:h0 + 256]
                # crc2 at track[h0 + 256:h0 + 258]
                # gap2
                h0, h1 = h1, h1 + fmt.LV_GAP2
                # gap2 at track[h0:h1]
            # leadout
            h0, h1 = h1, h1 + fmt.LV_LEADOUT
            assert h1 == len(track)
            sectors.extend(Util.flatten(track_sectors[sector_id] for sector_id in sorted(track_sectors)))
        return bytes(sectors)

    @classmethod
    def create_from_disk(cls, image):
        """create HFE image from disk image"""
        tracks = image[0x11]
        sides = image[0x12]
        dd = image[0x13] == 2
        protected = image[0x10:0x11] == b'P'

        header = cls.create_header(tracks, sides, dd, protected)
        lut = cls.create_lut(tracks, dd)

        fmt = DDFormat if dd else SDFormat
        side_0, side_1 = cls.create_tracks(tracks, sides, fmt, image)
        dummy = bytes(256) if not side_1 else None
        sandwich = b''.join(side_0[i:i+256] + (dummy or side_1[i:i+256])
                            for i in range(0, len(side_0), 256))
        assert len(header) == len(lut) == 512
        return header + lut + sandwich

    @classmethod
    def create_header(cls, tracks, sides, dd, protected):
        """create HFE disk header"""
        info = (b'HXCPICFE' +
                bytes((0,  # revision
                       tracks, sides,
                       HFEDisk.HFE_DD_ENCODING if dd else HFEDisk.HFE_SD_ENCODING)) +
                Util.rchrw(HFEDisk.HFE_BIT_RATE) +  # bit rate
                Util.rchrw(0) +  # RPM (not used)
                bytes((HFEDisk.HFE_INTERFACE_MODE, 1)) +
                Util.rchrw(1) +  # LUT offset // 512
                (b'\x00' if protected else b'\xff'))
        return info + b'\xff' * (512 - len(info))

    @classmethod
    def create_lut(cls, tracks, dd):
        """create HFE LUT"""
        lut = b''.join(Util.rchrw(0x31 * i + 2) +
                       (bytes((0xc0, 0x61)) if dd else bytes((0xb0, 0x61)))
                       for i in range(tracks))
        return lut + b'\xff' * (512 - 4 * tracks)

    @classmethod
    def create_tracks(cls, tracks, sides, fmt, sectors):
        """create HFE tracks"""
        track_data = ([], [])
        for s in range(sides):
            for j in range(tracks):
                sector_data = []
                for i in range(fmt.SECTORS):
                    track_id = tracks - 1 - j if s else j  # 0 .. 39 39 .. 0
                    sector_id = fmt.interleave(s, j, i, tracks == 80)
                    offset = ((s * tracks + j) * fmt.SECTORS + sector_id) * 256
                    sector = [b for b in sectors[offset:offset + 256]]
                    addr = [track_id, s, sector_id, 0x01]
                    crc1 = HFEDisk.crc16(0xffff, fmt.V_ADDRESS_MARK + addr)
                    crc2 = HFEDisk.crc16(0xffff, fmt.V_DATA_MARK + sector)
                    sector_data.extend(
                        fmt.PREGAP +
                        fmt.ADDRESS_MARK +
                        fmt.encode(addr + crc1) +
                        fmt.GAP1 +
                        fmt.DATA_MARK +
                        fmt.encode(sector + crc2) +
                        fmt.GAP2)
                fmt.fix_clocks(sector_data)
                track = fmt.LEADIN + sector_data + fmt.LEADOUT
                track_data[s].append(bytes(track))
        track_data[1].reverse()
        return b''.join(track_data[0]), b''.join(track_data[1])

    @staticmethod
    def crc16(crc, stream):
        """compute CRC-16 code"""
        msb, lsb = crc >> 8, crc & 0xff
        for b in stream:
            x = b ^ msb
            x ^= (x >> 4)
            msb = (lsb ^ (x >> 3) ^ (x << 4)) & 0xff
            lsb = (x ^ (x << 5)) & 0xff
        return [msb, lsb]


class Console:
    """collects errors and warnings"""

    def __init__(self, colors=None):
        self.errors = False
        if colors is None:
            self.colors = platform.system() in ('Linux', 'Darwin')  # no auto color on Windows
        else:
            self.colors = colors == 'on'

    def error(self, message):
        """record error message"""
        self.errors = True
        sys.stderr.write(self.color(message, severity=2) + '\n')

    def color(self, message, severity=0):
        if not self.colors:
            return message
        elif severity == 1:
            return '\x1b[33m' + message + '\x1b[0m'  # yellow
        elif severity == 2:
            return '\x1b[31m' + message + '\x1b[0m'  # red
        else:
            return message


# Command line processing

class Xhm99Processor(CommandProcessor):

    def __init__(self):
        super().__init__((HFEError, xdm.ContainerError, xdm.FileError))
        self.console = None
    
    def parse(self):
        args = argparse.ArgumentParser(
            description='xhm99: HFE image and file manipulation tool, v' + VERSION,
            epilog='Additionally, most xdm99 options can be used.')
        cmd = args.add_mutually_exclusive_group(required=True)

        # xdm99 delegation
        cmd.add_argument('filename', type=str, nargs='?',
                         help='HFE image filename')

        # conversion
        cmd.add_argument('-T', '--to-hfe', action=GlobStore, dest='tohfe', nargs='+', metavar='<file>',
                         help='convert disk images to HFE images')
        cmd.add_argument('-F', '--from-hfe', '--to-dsk_id', action=GlobStore, dest='fromhfe', nargs='+',
                         metavar='<file>',
                         help='convert HFE images to disk images')
        cmd.add_argument('-I', '--hfe-info', action=GlobStore, dest='hfeinfo', nargs='+', metavar='<file>',
                         help='show basic information about HFE images')
        cmd.add_argument('--dump', action=GlobStore, dest='dump', nargs='+', metavar='<file>',
                         help='dump raw decoded HFE data')

        # general options
        args.add_argument('-K', '--archive', dest='archive', metavar='<archive>',
                          help='name of archive (on disk image or local machine')
        args.add_argument('-c', '--encoding', dest='encoding', nargs='?', const='utf-8', metavar='<encoding>',
                          help='set encoding for DISPLAY files')
        args.add_argument('--color', action='store', dest='color', choices=['off', 'on'],
                          help='enable or disable color output')
        args.add_argument('-o', '--output', dest='output', metavar='<file>',
                          help='set output filename')

        try:
            default_opts = os.environ[CONFIG].split()
        except KeyError:
            default_opts = []
        self.opts, _ = args.parse_known_args(default_opts + sys.argv[1:])

    def run(self):
        self.console = Console(colors=self.opts.color)

    def prepare(self):
        if self.opts.filename:
            self.delegate()
        elif self.opts.tohfe:
            self.tohfe()
        elif self.opts.fromhfe:
            self.fromhfe()
        elif self.opts.dump:
            self.dump()
        else:
            self.info()

    def delegate(self):
        """delegate to xdm99"""
        try:
            image = Util.readdata(self.opts.filename)
            disk = HFEDisk(image).to_disk_image()
        except IOError:
            disk = bytes(1)  # dummy, includes -X case
        xdm_result, self.rc = xdm.Xdm99Processor().main(disk)  # local sys.argv will be passed to xdm99
        for item in xdm_result:
            if item.iscontainer:
                # convert disk results into HFE disks
                hfedisk = HFEDisk.create_from_disk(item.data)
                self.result.append(RContainer(hfedisk, item.name, item.ext, istext=item.istext, iscontainer=True,
                                              topc=item.topc, tiname=item.tiname))
            else:
                self.result.append(item)

    def fromhfe(self):
        for path in self.opts.fromhfe:
            hfe_image = Util.readdata(path)
            dsk = HFEDisk(hfe_image).to_disk_image()
            barename, _ = os.path.splitext(os.path.basename(path))
            self.result.append(RContainer(dsk, barename, ext='.dsk_id'))

    def tohfe(self):
        for path in self.opts.tohfe:
            dsk_image = Util.readdata(path)
            hfe = HFEDisk.create_from_disk(dsk_image)
            barename, _ = os.path.splitext(os.path.basename(path))
            self.result.append(RContainer(hfe, barename, ext='.hfe'))

    def dump(self):
        for path in self.opts.dump:
            image = Util.readdata(path)
            hfe = HFEDisk(image)
            tracks = hfe.get_tracks()
            data = ''.join(chr(b) for b in Util.flatten(tracks))
            barename, _ = os.path.splitext(os.path.basename(path))
            self.result.append(RContainer(data, barename, ext='.dump'))

    def info(self):
        for name in self.opts.hfeinfo:
            image = Util.readdata(name)
            tracks, sides, encoding, if_mode = HFEDisk.get_hfe_params(image)
            sys.stdout.write(f'Tracks: {tracks}\nSides: {sides}\n')
            sys.stdout.write(f'Encoding: {encoding}\nInterface mode: {if_mode}\n')
            if encoding not in HFEDisk.VALID_ENCODINGS or if_mode != HFEDisk.HFE_INTERFACE_MODE:
                self.console.error('Not a suitable HFE image for the TI 99')
                self.rc = 1

    def errors(self):
        return 1 if self.console.errors else self.rc


if __name__ == '__main__':
    status = Xhm99Processor().main()
    sys.exit(status)
