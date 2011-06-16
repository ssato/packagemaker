#
# Copyright (C) 2011 Satoru SATOH <satoru.satoh @ gmail.com>
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
import subprocess


def shell(cmd, workdir=None, dryrun=False, stop_on_error=True):
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
    logging.info(" Run: %s [%s]" % (cmd, workdir))

    if dryrun:
        logging.info(" exit as we're in dry run mode.")
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
        raise RuntimeError("Error (%s) when running: %s" % (repr(e.__class__), str(e)))

    if rc == 0:
        return rc
    else:
        if stop_on_error:
            raise RuntimeError(" Failed: %s,\n rc=%d" % (cmd, rc))
        else:
            logging.error(" cmd=%s, rc=%d" % (cmd, rc))
            return rc


# vim: set sw=4 ts=4 expandtab:
