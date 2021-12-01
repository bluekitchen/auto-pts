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
import sys

import autoptsclient_common as autoptsclient
import ptsprojects.bluez as autoprojects
from ptsprojects.btstack.iutctl import get_iut


class BTstackClient(autoptsclient.Client):
    def __init__(self):
        super().__init__(get_iut, 'btstack')
        autoprojects.iutctl.AUTO_PTS_LOCAL = autoptsclient.AUTO_PTS_LOCAL

def main():
    """Main."""

    client = BTstackClient()
    client.start()

if __name__ == "__main__":
    main()
