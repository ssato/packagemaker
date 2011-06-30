from distutils.core import setup, Command

import datetime
import glob
import os
import sys

try:
    import nose
except ImportError:
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        raise ImportError("python-nose is must for testing.")


PACKAGE = "packagemaker"

VERSION = "0.2.99" + "." + datetime.datetime.now().strftime("%Y%m%d")


curdir = os.getcwd()


def list_paths(path_pattern="*", topdir=curdir, pred=os.path.isfile):
    return [p for p in glob.glob(os.path.join(topdir, path_pattern)) if pred(p)]


templates_topdir = "share/pmaker/templates"

data_files = [
# TODO:
#   ("share/man/man1", ["man/pmaker.1", ])
    (os.path.join(templates_topdir, "common"), list_paths("templates/common/*")),
    (os.path.join(templates_topdir, "common/debian"), list_paths("templates/common/debian/*")),
    (os.path.join(templates_topdir, "common/debian/source"), list_paths("templates/common/debian/source/*")),
    (os.path.join(templates_topdir, "autotools"), list_paths("templates/autotools/*")),
    (os.path.join(templates_topdir, "autotools/debian"), list_paths("templates/autotools/debian/*")),
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
            --define \"_topdir %(rpmdir)s\" --define \"_rpmdir %(rpmdir)s\" \
            --define \"_sourcedir %(topdir)s/dist\" --define \"_buildroot %(BUILDROOT)s\" \
            %(rpmspec)s
            """ % params

        os.system(cmd)



class RpmCommand(Command):

    user_options = []

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

        cmd = """rpmbuild -bb \
            --define \"_topdir %(rpmdir)s\" --define \"_srcrpmdir %(rpmdir)s\" \
            --define \"_sourcedir %(topdir)s/dist\" --define \"_buildroot %(BUILDROOT)s\" \
            %(rpmspec)s
            """ % params

        os.system(cmd)



setup(name=PACKAGE,
    version=VERSION,
    description="A packaging helper tool",
    author="Satoru SATOH",
    author_email="satoru.satoh@gmail.com",
    license="GPLv3+",
    url="https://github.com/ssato/packagemaker",
    packages=[
        "pmaker",
        "pmaker.collectors",
        "pmaker.makers",
        "pmaker.models",
        "pmaker.plugins",
    ],
    scripts=["tools/pmaker"],
    data_files=data_files,
    cmdclass={
        "test": TestCommand,
        "srpm": SrpmCommand,
        "rpm":  RpmCommand,
    },
)

# vim: set sw=4 ts=4 et:
