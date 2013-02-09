#
# Copyright (C) 2011 - 2013 Satoru SATOH <ssato at redhat.com>
# License: BSD3
#
from jinja2.exceptions import TemplateNotFound

import pmaker.utils as U

import jinja2
import logging
import os.path
import os
import sys


def mk_template_paths(filepath, template_paths=[]):
    """
    :param filepath: (Base) filepath of template file
    :param template_paths: Template search paths
    """
    tmpldir = os.path.abspath(os.path.dirname(filepath))
    if template_paths:
        return U.unique(template_paths + [tmpldir])
    else:
        # default:
        return [os.curdir, tmpldir]


def tmpl_env(paths):
    """
    :param paths: Template search paths
    """
    return jinja2.Environment(loader=jinja2.FileSystemLoader(paths))


def render_s(tmpl_s, ctx, paths=[os.curdir]):
    """
    Compile and render given template string `tmpl_s` with context `context`.

    :param tmpl_s: Template string
    :param ctx: Context dict needed to instantiate templates
    :param paths: Template search paths

    >>> render_s('a = {{ a }}, b = "{{ b }}"', {'a': 1, 'b': 'bbb'})
    u'a = 1, b = "bbb"'
    """
    return tmpl_env(paths).from_string(tmpl_s).render(**ctx)


def render_impl(filepath, ctx, paths):
    """
    :param filepath: (Base) filepath of template file or '-' (stdin)
    :param ctx: Context dict needed to instantiate templates
    :param paths: Template search paths
    """
    env = tmpl_env(paths)
    return env.get_template(os.path.basename(filepath)).render(**ctx)


def render(filepath, ctx, paths=[], ask=False):
    """
    Compile and render template, and return the result.

    Similar to the above but template is given as a file path `filepath` or
    sys.stdin if `filepath` is '-'.

    :param filepath: (Base) filepath of template file or '-' (stdin)
    :param ctx: Context dict needed to instantiate templates
    :param paths: Template search paths
    :param ask: Ask user for missing template location if True
    """
    if not paths:
        paths = [os.path.dirname(filepath)]

    if filepath == '-':
        return render_s(sys.stdin.read(), ctx, paths)
    else:
        try:
            return render_impl(filepath, ctx, paths)
        except TemplateNotFound, mtmpl:
            if not ask:
                raise RuntimeError("Template Not found: " + str(mtmpl))

            usr_tmpl = raw_input(
                "\n*** Missing template '%s'. "
                "Please enter its location (path): " % mtmpl
            )
            usr_tmpl = U.normpath(usr_tmpl.strip())
            usr_tmpldir = os.path.dirname(usr_tmpl)

            return render_impl(usr_tmpl, ctx, [usr_tmpldir])


def template_path(filepath, paths):
    """
    Return resolved path of given template file

    :param filepath: (Base) filepath of template file
    :param paths: Template search paths
    """
    for p in paths:
        candidate = os.path.join(p, filepath)
        if os.path.exists(candidate):
            return candidate

    logging.warn("Could not find template=%s in paths=%s" % (filepath, paths))
    return None


# vim:sw=4:ts=4:et:
