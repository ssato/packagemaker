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
import pmaker.globals as G
import pmaker.backend.registry as Backends
import pmaker.environ as E
import pmaker.parser as P

import anyconfig as A
import bunch as B
import glob
import os


def _defaults(env=None):
    """
    Make a Bunch object holding default values and returns it.
    """
    if env is None:
        env = E.Env()

    return B.Bunch(
        config=None,
        norc=False,
        force=False,
        verbosity=0,  # verbose and debug option.
        trace=False,
        log=None,  # logging output file
        #
        # build options:
        #
        workdir=env.workdir,
        stepto=env.upto,
        #
        # see pmaker.collectors.FilelistCollectors
        input_type="filelist.plain",
        #
        driver=Backends.default(),  # e.g. "autotools.single.rpm"
        format=env.format,
        destdir="",
        template_paths=env.template_paths,
        #
        # package metadata options:
        name=None,
        group="System Environment/Base",
        license="GPLv3+",
        url="http://localhost.localdomain",
        summary=None,
        compressor=env.compressor.extension,  # extension
        arch=False,
        relations=[],
        packager=env.fullname,
        email=env.email,
        pversion="0.0.1",
        release="1",
        ignore_owner=False,
        changelog="",
        #
        # rpm options:
        dist=env.dist.label,
        no_rpmdb=(env.format != G.PKG_FORMAT_RPM),
        no_mock=False,
        trigger=False,
        #
        # others:
        hostname=env.hostname,
    )


def list_paths(basename=G.PMAKER_NAME, paths=None, ext="conf"):
    """
    :param basename: Application's basic name, e.g. pmaker.
    :param paths: Configuration path list.
    :param ext: Extension of configuration files.
    """
    if paths is None:
        home = os.environ.get("HOME", os.curdir)
        paths = []

        if basename is not None:
            paths += ["/etc/%s.%s" % (basename, ext)]
            paths += sorted(glob.glob("/etc/%s.d/*.%s" % (basename, ext)))
            paths += [
                os.path.join(home, ".config", basename),
                os.environ.get("%sRC" % basename.upper(),
                               os.path.join(home, ".%src" % basename)),
            ]
    else:
        assert isinstance(paths, list)

    return [p for p in paths if os.path.exists(p)]


class Config(B.Bunch):

    def __init__(self, norc=False, forced_type=G.PMAKER_CONF_TYPE_DEFAULT):
        """
        :param norc: No rc, i.e. do not load any RC (config) files.
        :param forced_type: Force set configuration file type.
        """
        self._type = forced_type
        self.files = []

        self.update(_defaults())

        if not norc:
            self.load_default_configs(forced_type)

    def type(self):
        return self._type

    def load_default_configs(self, forced_type=None):
        """
        Try loading default config files and applying configurations.
        """
        self.update(B.Bunch(A.load(list_paths(),self.type())))

    def load(self, config, forced_type=None):
        #_type = forced_type if forced_type is not None else self.type()
        _type = forced_type if forced_type is not None else None
        config = B.Bunch(A.load(config, _type))

        # special cases:
        if "relations" in config:
            try:
                config.relations = P.parse(config.relations)
            except:
                print "config.relations=" + str(config.relations)
                raise

        if "template_paths" in config:
            config.template_paths = self.template_paths + \
                P.parse_list(config.template_paths)

        self.update(config)

    def missing_files(self):
        """
        Check if self.files, may be [fileobj] or [], is set.
        """
        return "files" not in self or not self.files


# vim:sw=4:ts=4:et:
