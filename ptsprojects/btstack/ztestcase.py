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

"""Test case that manages BTstack IUT"""

from ptsprojects.testcase import TestCaseLT1, TestCaseLT2, TestFunc, TestFuncCleanUp

from pybtp import btp


class ZTestCase(TestCaseLT1):
    """A BTstack test case class"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super(ZTestCase, self).__init__(*args, ptsproject_name="btstack",
                                        **kwargs)

        # Log test name
        self.cmds.insert(0, TestFunc(btp.core_log_message, self.name))

        # power down
        self.cmds.append(TestFuncCleanUp(btp.gap_set_powered_off))


class ZTestCaseSlave(TestCaseLT2):
    """A BTstack test case class"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super(ZTestCaseSlave, self).__init__(*args, ptsproject_name="btstack",
                                             **kwargs)