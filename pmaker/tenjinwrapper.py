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
import logging
import os.path
import os


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


# http://www.kuwata-lab.com/tenjin/pytenjin-users-guide.html#templace-cache
_ENGINE = tenjin.Engine(cache=tenjin.MemoryCacheStorage())


class TemplateNotFoundError(Exception):
    pass


def find_template(template, search_paths=[], ask=True):
    """
    Find template file from given path information.

    1. Try the path ($template)
    2. Try $path/$template where $path in $search_paths

    :param template: Template file path, may be relative to path in paths.
    :param search_paths: Path list to search for the template
    :param ask: Ask user about the path to template file if it's missing
        and this value is True

    :return: template path or TemplateNotFoundError exception may be raised.
    """
    if not search_paths:
        search_paths = [os.curdir]

    # The path at the top is special (system search path).
    # Make it searched at last.
    search_paths = search_paths[1:] + [search_paths[0]]

    tmpl = None

    if os.path.exists(template):
        tmpl = template
    else:
        logging.debug("Search template from: " + ",".join(search_paths))
        for path in search_paths:
            t = os.path.join(path, template)

            if os.path.exists(t):
                tmpl = t
                break

    if tmpl is None:  # Not found in search paths.
        logging.warn("*** Missing template '%s' ***" % template)

        if ask:
            template = raw_input("Please enter template path: ")

            if os.path.exists(template) and os.access(template, os.R_OK):
                tmpl = template
            else:
                m = "Not exists or cannot read it: " + template
                raise TemplateNotFoundError(m)
        else:
            raise TemplateNotFoundError("template=" + template)
    else:
        logging.info("Found template: " + tmpl)

    return tmpl


def compile(template, context={}, tpaths=[], ask=True, engine=_ENGINE):
    """
    :param template: Template file path or filename
    :param context: Context dict to instantiate given template
    :param tpaths: Template file search path
    :param ask: Ask user about the path to template file if it's missing
        and this value is True
    :param engine: Template compiling engine

    :return: Compiled result string or maybe TemplateNotFoundError thrown
    """
    tmpl = find_template(template, tpaths, ask=ask)
    return engine.render(tmpl, context)


# vim:sw=4:ts=4:et:
