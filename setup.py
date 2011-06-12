from distutils.core import setup, Command

import datetime
import os
import sys


PACKAGE = "packagemaker"

VERSION = "0.3.0" + "." + datetime.datetime.now().strftime("%Y%m%d")


pkgs = ["pmaker", ]
data_files = [
# TODO:
#        ("share/man/man1", ["man/pmaker.1", ])
]



class SrpmCommand(Command):

    user_options = []
    description = "Build a src rpm."

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('sdist')
        self.build_rpm()

    def build_rpm(self):
        params = dict()

        topdir = params["topdir"] = os.path.abspath(os.curdir)
        rpmdir = params["rpmdir"] = os.path.join(topdir, "dist")
        rpmspec = params["rpmspec"] = os.path.join(topdir, "%s.spec" % PACKAGE)

        for subdir in ("RPMS", "BUILD", "BUILDROOT"):
            sdir = params[subdir] = os.path.join(rpmdir, subdir)

            if not os.path.exists(sdir):
                os.makedirs(sdir, 0755)

        open(rpmspec, "w").write(open(rpmspec + ".in").read().replace("@VERSION@", VERSION))

        cmd = """rpmbuild -bs \
            --define \"_topdir %(rpmdir)s\" --define \"_srcrpmdir %(rpmdir)s\" \
            --define \"_sourcedir %(topdir)s/dist\" --define \"_buildroot %(BUILDROOT)s\" \
            %(rpmspec)s
            """ % params

        os.system(cmd)



setup(name=PACKAGE,
      version=VERSION,
      description="",
      author="Satoru SATOH",
      author_email="satoru.satoh@gmail.com",
      license="GPLv3+",
      url="https://github.com/ssato/packagemaker",
      package_dir={"pmaker": "pmaker"},
      scripts=["tools/pmaker"],
      packages=pkgs,
      data_files=data_files,
      cmdclass={
          "srpm": SrpmCommand,
      }
)

# vim: set sw=4 ts=4 et:
