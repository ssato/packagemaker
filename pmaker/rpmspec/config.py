#
# Copyright (C) 2011 Satoru SATOH <ssato @ redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import pmaker.anycfg as Anycfg
import pmaker.environ as E
import pmaker.models.Bunch as B
import pmaker.parser as P


# aliases:
TYPES = Anycfg.CTYPES
guess_type = Anycfg.guess_type


def _defaults(env):
    """
    Make a Bunch object holding default values and returns it.
    """
    defaults = B.Bunch()

    defaults.verbosity = 0  # verbose and debug option.
    defaults.log = None  # logging output file
    defaults.workdir = env.workdir
    defaults.template_paths = env.template_paths

    # package metadata options:
    defaults.name = None
    defaults.group = ""
    defaults.license = ""
    defaults.url = ""
    defaults.summary = ""
    defaults.buildarch = ""
    defaults.packager = env.fullname
    defaults.email = env.email
    defaults.pversion = ""
    defaults.release = "1"

    return defaults


class Config(B.Bunch):

    def __init__(self, cpath=None):
        """
        :param cpath: Configuration file's path
        """
        self._env = E.Env()
        self._cparser = Anycfg.AnyConfigParser()
        self.update(_defaults(E.Env()))

        if cpath is not None:
            self.load(cpath)

    def load(self, config):
        config = self._cparser.load(config)

        # special cases:
        if "template_paths" in config:
            config.template_paths = self.template_paths + \
                P.parse_list(config.template_paths)

        self.update(config)


# vim:sw=4 ts=4 et:
