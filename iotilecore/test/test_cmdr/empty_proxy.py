# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International 
# are copyright Arch Systems Inc.

from iotile.core.commander.proxy.proxy import MIBProxyObject

class EmptyProxy (MIBProxyObject):
	def random_method(self):
		return True
