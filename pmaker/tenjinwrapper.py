#
# tenjin (pmaker.contrib.tenjin) wrapper module
#
# Copyright (C) 2011 Satoru SATOH <ssato at redhat.com>
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
import pmaker.imported.tenjin as tenjin


# dirty hack for highly customized and looks a bit overkill (IMHO) module
# system in pyTenjin:
cache_as = tenjin.helpers.cache_as
capture_as = tenjin.helpers.capture_as
captured_as = tenjin.helpers.captured_as
echo = tenjin.helpers.echo
echo_cached = tenjin.helpers.echo_cached
escape = tenjin.helpers.escape
fragment_cache = tenjin.helpers.fragment_cache
generate_tostrfunc = tenjin.helpers.generate_tostrfunc
html = tenjin.helpers.html
new_cycle = tenjin.helpers.new_cycle
not_cached = tenjin.helpers.not_cached
start_capture = tenjin.helpers.start_capture
stop_capture = tenjin.helpers.stop_capture
to_str = tenjin.helpers.to_str
unquote = tenjin.helpers.unquote


def template_compile(template_path, context={}):
    """
    Wrapper to compile template w/ pytenjin.

    see also:
    http://www.kuwata-lab.com/tenjin/pytenjin-users-guide.html#templace-cache
    """
    tenjin.Engine.cache = tenjin.MemoryCacheStorage()
    return tenjin.Engine().render(template_path, context)


# vim:sw=4 ts=4 et:
