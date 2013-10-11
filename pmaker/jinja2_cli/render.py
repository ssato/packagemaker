"""
    Jinja2 based template renderer.
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Compiles and render Jinja2-based template files.

    :copyright: (c) 2012 by Satoru SATOH <ssato@redhat.com>
    :license: BSD-3

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:

   * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
   * Neither the name of the author nor the names of its contributors may
     be used to endorse or promote products derived from this software
     without specific prior written permission.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
 DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

 Requirements: python-jinja2, python-simplejson (if python < 2.6) and PyYAML
 References: http://jinja.pocoo.org,
    especially http://jinja.pocoo.org/docs/api/#basics
"""
from jinja2.exceptions import TemplateNotFound

import jinja2_cli.utils as U

import anyconfig.api as A
import codecs
import glob
import jinja2
import locale
import logging
import optparse
import os.path
import os
import sys

from logging import DEBUG, INFO


_ENCODING = locale.getdefaultlocale()[1]
sys.stdout = codecs.getwriter(_ENCODING)(sys.stdout)
sys.stderr = codecs.getwriter(_ENCODING)(sys.stderr)
open = codecs.open


def mk_template_paths(filepath, template_paths=[]):
    """
    :param filepath: (Base) filepath of template file
    :param template_paths: Template search paths
    """
    tmpldir = os.path.abspath(os.path.dirname(filepath))
    if template_paths:
        return U.uniq(template_paths + [tmpldir])
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

    >>> s = render_s('a = {{ a }}, b = "{{ b }}"', {'a': 1, 'b': 'bbb'})
    >>> assert s == 'a = 1, b = "bbb"'
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


def render(filepath, ctx, paths, ask=False):
    """
    Compile and render template, and return the result.

    Similar to the above but template is given as a file path `filepath` or
    sys.stdin if `filepath` is '-'.

    :param filepath: (Base) filepath of template file or '-' (stdin)
    :param ctx: Context dict needed to instantiate templates
    :param paths: Template search paths
    :param ask: Ask user for missing template location if True
    """
    if filepath == '-':
        return render_s(sys.stdin.read(), ctx, paths)
    else:
        try:
            return render_impl(filepath, ctx, paths)
        except TemplateNotFound as mtmpl:
            if not ask:
                raise RuntimeError("Template Not found: " + str(mtmpl))

            usr_tmpl = raw_input(
                "\n*** Missing template '%s'. "
                "Please enter its location (path): " % mtmpl
            )
            usr_tmpl = U.normpath(usr_tmpl.strip())
            usr_tmpldir = os.path.dirname(usr_tmpl)

            return render_impl(usr_tmpl, ctx, paths + [usr_tmpldir])


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


def parse_template_paths(tmpl, paths=None, sep=":"):
    """
    Parse template_paths option string and return [template_path].

    :param tmpl: Template file to render
    :param paths: str to specify template path list separated by `sep`
    :param sep: template path list separator
    """
    if paths:
        try:
            paths = mk_template_paths(tmpl, paths.split(sep))
            assert paths
        except:
            logging.warn("Ignored as invalid form: " + paths)
            paths = mk_template_paths(tmpl, [])
    else:
        paths = mk_template_paths(tmpl, [])

    logging.debug("Template search paths: " + str(paths))
    return paths


def parse_filespec(fspec, sep=':', gpat='*'):
    """
    Parse given filespec `fspec` and return [(filetype, filepath)].

    Because anyconfig.api.load should find correct file's type to load by the
    file extension, this function will not try guessing file's type if not file
    type is specified explicitly.

    :param fspec: filespec
    :param sep: a char separating filetype and filepath in filespec
    :param gpat: a char for glob pattern

    >>> parse_filespec("base.json")
    [('base.json', None)]
    >>> parse_filespec("json:base.json")
    [('base.json', 'json')]
    >>> parse_filespec("yaml:foo.yaml")
    [('foo.yaml', 'yaml')]
    >>> parse_filespec("yaml:foo.dat")
    [('foo.dat', 'yaml')]

    # FIXME: How to test this?
    # >>> parse_filespec("yaml:bar/*.conf")
    # [('bar/a.conf', 'yaml'), ('bar/b.conf', 'yaml')]

    TODO: Allow '*' (glob pattern) in filepath when escaped with '\\', etc.
    """
    tp = (ft, fp) = tuple(fspec.split(sep)) if sep in fspec else (None, fspec)

    return [(fs, ft) for fs in sorted(glob.glob(fp))] \
        if gpat in fspec else [U.flip(tp)]


def parse_and_load_contexts(contexts, enc=_ENCODING, werr=False):
    """
    :param contexts: list of context file specs
    :param enc: Input encoding of context files (dummy param)
    :param werr: Exit immediately if True and any errors occurrs
        while loading context files
    """
    ctx = A.container()  # see also: anyconfig.api

    if contexts:
        for fpath, ftype in U.concat(parse_filespec(f) for f in contexts):
            diff = A.load(fpath, ftype)
            ctx.update(diff)

    return ctx


def option_parser(argv=sys.argv):
    defaults = dict(
        template_paths=None, output=None, contexts=[], debug=False,
        encoding=_ENCODING, werror=False, ask=False,
    )

    p = optparse.OptionParser(
        "%prog [OPTION ...] TEMPLATE_FILE", prog=argv[0],
    )
    p.set_defaults(**defaults)

    p.add_option("-T", "--template-paths",
                 help="Colon ':' separated template search paths. "
                 "Please note that dir in which given template exists "
                 "is always included in the search paths (at the end of "
                 "the path list) regardless of this option. "
                 "[., dir in which given template file exists]")
    p.add_option("-C", "--contexts", action="append",
                 help="Specify file path and optionally its filetype, to "
                 "provides context data to instantiate templates. "
                 " The option argument's format is "
                 " [type:]<file_name_or_path_or_glob_pattern>"
                 " ex. -C json:common.json -C ./specific.yaml -C "
                 "yaml:test.dat, -C yaml:/etc/foo.d/*.conf")
    p.add_option("-o", "--output", help="Output filename [stdout]")
    p.add_option("-E", "--encoding", help="I/O encoding [%default]")
    p.add_option("-D", "--debug", action="store_true", help="Debug mode")
    p.add_option("-W", "--werror", action="store_true",
                 help="Exit on warnings if True such like -Werror optoin "
                 "for gcc")

    return p


def write_to_output(output=None, encoding="utf-8", content=""):
    if output and not output == '-':
        outdir = os.path.dirname(output)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        open(output, "w", encoding).write(content)
    else:
        codecs.getwriter(encoding)(sys.stdout).write(content)


def renderto(tmpl, ctx, paths, output=None, encoding=_ENCODING, ask=True):
    write_to_output(output, encoding, render(tmpl, ctx, paths, ask))


def main(argv):
    p = option_parser(argv)
    (options, args) = p.parse_args(argv[1:])

    if not args:
        p.print_help()
        sys.exit(0)

    logging.basicConfig(
        format="[%(levelname)s] %(message)s",
        level=(DEBUG if options.debug else INFO),
    )

    tmpl = args[0]
    ctx = parse_and_load_contexts(
        options.contexts, options.encoding, options.werror
    )
    paths = parse_template_paths(tmpl, options.template_paths)
    renderto(tmpl, ctx, paths, options.output, options.encoding)


if __name__ == '__main__':
    main(sys.argv)

# vim:sw=4:ts=4:et:
