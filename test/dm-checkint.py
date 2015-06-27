#!/usr/bin/env python

import shutil
import os

from config import Dirs, Disks, Files
from utils import xdm, error, checkFilesEq


### Check functions

def checkRecordsByChecksum(infile, reclen, fixed):
    """check if internal records match reference format"""
    reccount = 1024 / reclen
    with open(infile, "rb") as f:
        data = f.read()
    if len(data) != reccount * (reclen if fixed else reclen + 1):
        error("INT Records", "%s: File length mismatch: %d != %d" % (
            infile, len(data), reccount * reclen))
    p = 0
    for i in xrange(reccount):
        if fixed:
            l = reclen
        else:
            l, p = ord(data[p]), p + 1  # data length <= record length
        for j in xrange(l):
            s = (l - 1 if j == 0 else  # addtl Ext BASIC string length byte
                 i + 1 if j == 1 else  # checksum
                 j - 2) % 256
            if ord(data[p + j]) != s:
                error("INT Records", "%s: Record contents mismatch at %d" % (
                    infile, p + j))
        p += l


### Main test

def runtest():
    """extract INT record files generated by WRITEINT.bas"""

    # setup
    shutil.copyfile(Disks.recsint, Disks.work)

    # read full-size records
    for reclen in [2, 64, 127, 128, 254, 255]:
        xdm(Disks.work, "-e", "IF" + str(reclen), "-o", Files.output)
        checkRecordsByChecksum(Files.output, reclen, True)
        xdm(Disks.work, "-e", "IV" + str(reclen), "-o", Files.output)
        checkRecordsByChecksum(Files.output, reclen, False)

    # read partially filled records
    for fn in ["intfix32v", "intvar32v", "intfix128v", "intvar128v"]:
        xdm(Disks.work, "-e", fn.upper(), "-o", Files.output)
        ref = os.path.join(Dirs.refs, fn)
        checkFilesEq("INT Records", Files.output, ref, "P")

    # re-write extracted records and check
    for reclen in [2, 64, 127, 128, 254, 255]:
        xdm(Disks.work, "-e", "IF" + str(reclen), "-o", Files.reference)
        xdm(Disks.work, "-a", Files.reference, "-n", "CF" + str(reclen),
            "-f", "INT/FIX" + str(reclen))
        xdm(Disks.work, "-e", "CF" + str(reclen), "-o", Files.output)
        checkFilesEq("Write INT", Files.output, Files.reference,
                     "INT/FIX" + str(reclen))
        xdm(Disks.work, "-e", "IV" + str(reclen), "-o", Files.reference)
        xdm(Disks.work, "-a", Files.reference, "-n", "CV" + str(reclen),
            "-f", "INT/VAR" + str(reclen))
        xdm(Disks.work, "-e", "CV" + str(reclen), "-o", Files.output)
        checkFilesEq("Write INT", Files.output, Files.reference,
                     "INT/VAR" + str(reclen))

    # re-write partially filled records
    for fn, fmt in [
            ("intfix32v", "IF32"), ("intvar32v", "IV32"),
            ("intfix128v", "IF128"), ("intvar128v", "IV128")
            ]:
        ref = os.path.join(Dirs.refs, fn)
        xdm(Disks.work, "-a", ref, "-n", "TEST", "-f", fmt)
        xdm(Disks.work, "-e", "TEST", "-o", Files.output)
        checkFilesEq("Write INT", Files.output, ref, "P")

    # cleanup
    os.remove(Files.output)
    os.remove(Files.reference)
    os.remove(Disks.work)


if __name__ == "__main__":
    runtest()
