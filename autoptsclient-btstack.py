#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

"""btstack auto PTS client"""
import importlib

from autopts import client as autoptsclient
from autopts.ptsprojects.btstack import iutctl


class BTstackClient(autoptsclient.Client):
    def __init__(self):
        project = importlib.import_module('autopts.ptsprojects.btstack')
        super().__init__(iutctl.get_iut, project, 'btstack')
        iutctl.AUTO_PTS_LOCAL = autoptsclient.AUTO_PTS_LOCAL


def main():
    """Main."""

    client = BTstackClient()
    client.start()


if __name__ == "__main__":
    main()
