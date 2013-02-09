from distutils.core import setup, Command
from distutils.sysconfig import get_python_lib

import datetime
import glob
import os
import sys


curdir = os.getcwd()
pylibdir = get_python_lib()


sys.path.append(curdir)
from pmaker.globals import PMAKER_AUTHOR, PMAKER_EMAIL, PMAKER_WEBSITE, \
    PMAKER_TITLE as PACKAGE, PMAKER_VERSION as VERSION


def list_paths(path_pattern="*", topdir=curdir, pred=os.path.isfile):
    return [p for p in glob.glob(os.path.join(topdir, path_pattern)) if pred(p)]


top_datadir = "share/pmaker"


def mk_tmpl_pair(tmpldir, top_datadir=top_datadir):
    return (
        os.path.join(top_datadir, tmpldir),
        list_paths("%s/*" % tmpldir)
    )


data_files = [
    ("share/man/man8", ["doc/pmaker.8", ]),
    (os.path.join(pylibdir, "pmaker/tests"), list_paths("pmaker/tests/*_example_*")),
] + [
    mk_tmpl_pair(d) for d in ("templates/1",
                              "templates/1/common",
                              "templates/1/common/debian",
                              "templates/1/common/debian/source",
                              "templates/1/autotools",
                              "templates/1/autotools/debian",
                              "templates/1/autotools.single",
                              "templates/1/buildrpm",
                             )
]


test_targets = \
    glob.glob(os.path.join(curdir, "pmaker/tests/*.py")) + \
    glob.glob(os.path.join(curdir, "pmaker/*/tests/*.py"))

test_targets_full = glob.glob(os.path.join(curdir, "tests/*.py"))


class TestCommand(Command):

    user_options = [("full", "F",
        "Fully test all including system/integration tests take much time to complete")]
    boolean_options = ['full']
    test_driver = os.path.join(curdir, "runtest.sh")

    def initialize_options(self):
        self.full = 0

    def finalize_options(self):
        if self.full and "FULL_TESTS" not in os.environ:
            os.environ["FULL_TESTS"] = "1"

    def run(self):
        for f in test_targets:
            os.system("PYTHONPATH=%s %s %s" % (curdir, self.test_driver, f))

        if self.full:
            for f in test_targets_full:
                os.system("PYTHONPATH=%s %s %s" % (curdir, self.test_driver, f))


class SrpmCommand(Command):

    user_options = []

    build_stage = "s"
    cmd_fmt = """rpmbuild -b%(build_stage)s \
        --define \"_topdir %(rpmdir)s\" \
        --define \"_sourcedir %(rpmdir)s\" \
        --define \"_buildroot %(BUILDROOT)s\" \
        %(rpmspec)s
    """

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('sdist')
        self.build_rpm()

    def build_rpm(self):
        params = dict()

        params["build_stage"] = self.build_stage
        rpmdir = params["rpmdir"] = os.path.join(
            os.path.abspath(os.curdir), "dist"
        )
        rpmspec = params["rpmspec"] = os.path.join(
            rpmdir, "../%s.spec" % PACKAGE
        )

        for subdir in ("SRPMS", "RPMS", "BUILD", "BUILDROOT"):
            sdir = params[subdir] = os.path.join(rpmdir, subdir)

            if not os.path.exists(sdir):
                os.makedirs(sdir, 0755)

        c = open(rpmspec + ".in").read()
        open(rpmspec, "w").write(c.replace("@VERSION@", VERSION))

        os.system(self.cmd_fmt % params)


class RpmCommand(SrpmCommand):

    build_stage = "b"


setup(name=PACKAGE,
    version=VERSION,
    description="A packaging helper tool",
    author=PMAKER_AUTHOR,
    author_email=PMAKER_EMAIL,
    license="GPLv3+",
    url=PMAKER_WEBSITE,
    packages=[
        "pmaker",
        "pmaker.backend",
        "pmaker.backend.autotools",
        "pmaker.backend.autotools.single",
        "pmaker.backend.autotools.single.tests",
        "pmaker.backend.buildrpm",
        "pmaker.backend.buildrpm.tests",
        "pmaker.backend.tests",
        "pmaker.collectors",
        "pmaker.collectors.tests",
        "pmaker.imported",
        "pmaker.models",
        "pmaker.models.tests",
        "pmaker.tests",
    ],
    scripts=[
        "tools/pmaker",
        "tools/pmaker"
    ],
    data_files=data_files,
    cmdclass={
        "test": TestCommand,
        "srpm": SrpmCommand,
        "rpm":  RpmCommand,
    },
)


# vim:sw=4:ts=4:et:
