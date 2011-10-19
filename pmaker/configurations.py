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
from pmaker.models.Bunch import Bunch
from pmaker.globals import PMAKER_NAME

import pmaker.anycfg as Anycfg
import pmaker.collectors.Collectors as Collectors
import pmaker.backend.registry as Backends
import pmaker.environ as E


def _defaults(env):
    """
    Make a Bunch object holding default values and returns it.
    """
    defaults = Bunch()

    defaults.force = False
    defaults.verbosity = 0  # verbose and debug option.

    # build options:
    defaults.workdir = env.workdir
    defaults.stepto = env.upto
    defaults.input_type = Collectors.default()  # e.g. "filelist.json"
    defaults.driver = Backends.default()  # e.g. "autotools.single.rpm"
    defaults.destdir = ""
    defaults.template_paths = env.template_paths

    # package metadata options:
    defaults.name = None
    defaults.group = "System Environment/Base"
    defaults.license = "GPLv3+"
    defaults.url = "http://localhost.localdomain"
    defaults.summary = None
    defaults.compressor = env.compressor.extension  # extension
    defaults.arch = False
    defaults.relations = ""
    defaults.packager = env.fullname
    defaults.email = env.email
    defaults.pversion = "0.0.1"
    defaults.release = "1"
    defaults.ignore_owner = False
    defaults.changelog = None

    # rpm options:
    defaults.dist = env.dist.label
    defaults.no_rpmdb = False
    defaults.no_mock = False

    return defaults


class Config(Bunch):

    def __init__(self, norc=False):
        """
        :param norc: No rc, i.e. do not load any RC (config) files.
        """
        self._env = E.Env()
        self._cparser = Anycfg.AnyConfigParser()

        self.files = []

        self.update(_defaults(self._env))

        if not norc:
            self.load_default_configs()

    def load(self, config):
        config = self._cparser.load(config)
        self.update(config)

    def load_default_configs(self):
        """
        Try loading default config files and applying configurations.
        """
        config = self._cparser.loads(PMAKER_NAME)  # :: Bunch
        self.update(config)

    def missing_files(self):
        """
        Check if self.files, may be [fileobj] or [], is set.
        """
        return "files" not in self or not self.files


# vim:sw=4 ts=4 et: