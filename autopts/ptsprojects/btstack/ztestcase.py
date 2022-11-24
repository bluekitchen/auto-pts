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

from autopts.ptsprojects.testcase import TestCaseLT1, TestCaseLT2, TestCaseLT3, TestFunc, TestFuncCleanUp
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.btstack.iutctl import get_iut
from autopts.pybtp import btp


class ZTestCase(TestCaseLT1):
    """A BTstack test case class"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super().__init__(*args, ptsproject_name="btstack", **kwargs)

        self.stack = get_stack()
        self.iutctrl = get_iut()

        # Log test name
        self.cmds.insert(0, TestFunc(btp.core_log_message, self.name))

        # start btpclient
        self.cmds.insert(0, TestFunc(self.iutctrl.start))
        self.cmds.insert(1, TestFunc(self.iutctrl.wait_iut_ready_event))

        self.cmds.append(TestFuncCleanUp(self.stack.cleanup))

        # power down
        self.cmds.append(TestFuncCleanUp(btp.gap_set_powered_off))

        # last command is to stop btpclient
        self.cmds.append(TestFuncCleanUp(self.iutctrl.stop))


class ZTestCaseSlave(TestCaseLT2):
    """A BTstack test case class"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super().__init__(*args, ptsproject_name="btstack", **kwargs)


class ZTestCaseSlave2(TestCaseLT3):
    """A BTstack test case class"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super().__init__(*args, ptsproject_name="btstack", **kwargs)
