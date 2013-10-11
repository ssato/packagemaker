#
# Copyright (C) 2011 Satoru SATOH <satoru.satoh @ gmail.com>
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
import logging
import os
import subprocess
import sys
import threading


CURDIR = os.getcwd()


def shell(cmd, workdir=CURDIR, dryrun=False, stop_on_error=True):
    """
    @cmd      str   command string, e.g. "ls -l ~".
    @workdir  str   in which dir to run given command?
    @dryrun   bool  if True, just print command string to run and returns.
    @stop_on_error bool  if True, RuntimeError will not be raised.

    >>> assert 0 == shell("echo ok > /dev/null")
    >>> assert 0 == shell("ls null", "/dev")
    >>> assert 0 == shell("ls null", "/dev", dryrun=True)
    >>> try:
    ...    rc = shell("ls", "/root")
    ... except RuntimeError:
    ...    pass
    >>> rc = shell("echo OK | grep -q NG 2>/dev/null", stop_on_error=False)
    """
    logging.info("Run: %s [%s]" % (cmd, workdir))

    if dryrun:
        logging.info("Exit as we're in dry run mode.")
        return 0

    llevel = logging.getLogger().level
    if llevel < logging.WARN:
        cmd += " > /dev/null"
    elif llevel < logging.INFO:
        cmd += " 2> /dev/null"
    else:
        pass

    try:
        proc = subprocess.Popen(cmd, shell=True, cwd=workdir)
        proc.wait()
        rc = proc.returncode

    except Exception, e:
        raise RuntimeError(
            "Error (%s) when running: %s" % (repr(e.__class__), str(e))
        )

    if rc == 0:
        return rc
    else:
        if stop_on_error:
            raise RuntimeError(" Failed: %s,\n rc=%d" % (cmd, rc))
        else:
            logging.error("cmd=%s, rc=%d" % (cmd, rc))
            return rc


class ThreadedCommand(object):
    """
    Based on the idea found at
    http://stackoverflow.com/questions/1191374/subprocess-with-timeout
    """

    def __init__(self, cmd, workdir=CURDIR, stop_on_error=True, timeout=None):
        """
        :param cmd:     Command string
        :param workdir: Working directory to run cmd
        :param stop_on_error:  Stop main thread if something goes wrong
        :param timeout: Timeout value
        """
        self.cmd = cmd
        self.stop_on_error = stop_on_error
        self.timeout = timeout

        if "~" in workdir:
            workdir = os.path.expanduser(workdir)

        self.workdir = workdir

        llevel = logging.getLogger().level
        if llevel < logging.WARN:
            self.cmd += " > /dev/null"
        elif llevel < logging.INFO:
            self.cmd += " 2> /dev/null"
        else:
            pass

        self.cmd_str = "%s [%s]" % (self.cmd, self.workdir)

        self.process = None
        self.thread = None
        self.result = None

    def run_async(self):
        def func():
            """
            if logging.getLogger().level < logging.INFO:  # logging.DEBUG
                stdout = sys.stdout
            else:
                stdout = open("/dev/null", "w")
            """

            logging.info("Run: " + self.cmd_str)

            self.process = subprocess.Popen(self.cmd,
                                            bufsize=4096,
                                            shell=True,
                                            cwd=self.workdir)
            self.result = self.process.wait()

            logging.debug("Finished: " + self.cmd_str)

        self.thread = threading.Thread(target=func)
        self.thread.start()

    def get_result(self):
        if self.thread is None:
            logging.warn("Thread does not exist. Did you call %s.run_async() "
                         "?" % self.__class__.__name__)
            return None

        # it will block.
        self.thread.join(self.timeout)

        if self.thread.is_alive():
            logging.warn("Terminating: " + self.cmd_str)

            self.process.terminate()
            self.thread.join()

        rc = self.result

        if rc != 0:
            emsg = "Failed: %s, rc=%d" % (self.cmd, rc)

            if self.stop_on_error:
                raise RuntimeError(emsg)
            else:
                logging.warn(emsg)

        return rc

    def run(self):
        self.run_async()
        return self.get_result()


def run(cmd, workdir=CURDIR, dryrun=False, stop_on_error=True, timeout=None):

    if dryrun:
        print cmd
        logging.debug("(Exit as we're in dry run mode.)")
        return

    tcmd = ThreadedCommand(cmd, workdir, stop_on_error, timeout)
    return tcmd.run()


# vim:sw=4:ts=4:et:
