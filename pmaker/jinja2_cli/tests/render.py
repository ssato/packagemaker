#
# Copyright (C) 2011 - 2013 Satoru SATOH <ssato at redhat.com>
#
import pmaker.jinja2_cli.render as R
import os
import unittest


class Test_00_pure_functions(unittest.TestCase):

    def test_00_mk_template_paths__wo_paths(self):
        self.assertEquals(R.mk_template_paths("/a/b/c.yml"),
                          [os.curdir, "/a/b"])

    def test_01_mk_template_paths__w_paths(self):
        self.assertEquals(R.mk_template_paths("/a/b/c.yml", ["/a/d"]),
                          ["/a/d", "/a/b"])

    def test_10_tmpl_env(self):
        self.assertTrue(isinstance(R.tmpl_env(["/a/b", ]),
                                   R.jinja2.Environment))

    def test_20_render_s(self):
        tmpl_s = 'a = {{ a }}, b = "{{ b }}"'
        self.assertEquals(R.render_s(tmpl_s, {'a': 1, 'b': 'bbb'}),
                          'a = 1, b = "bbb"')

    def test_30_parse_template_paths__wo_paths(self):
        self.assertEquals(R.parse_template_paths("/a/b/c.yml"),
                          [os.curdir, "/a/b"])

    def test_31_parse_template_paths__w_paths(self):
        self.assertEquals(R.parse_template_paths("/a/b/c.yml", "/a/d:/a/e"),
                          ["/a/d", "/a/e", "/a/b"])

    def test_40_parse_filespec__w_type(self):
        self.assertEquals(R.parse_filespec("json:a.json"),
                          [("a.json", "json")])

    def test_41_parse_filespec__wo_type(self):
        self.assertEquals(R.parse_filespec("a.json"), [("a.json", None)])


class Test_10_effectful_functions(unittest.TestCase):

    def test_10_render_impl(self):
        """FIXME: Write tests for jinja2_cli.render.render_impl"""
        pass

    def test_20_render(self):
        """FIXME: Write tests for jinja2_cli.render.render"""
        pass

    def test_30_template_path(self):
        """FIXME: Write tests for jinja2_cli.render.template_path"""
        pass

    def test_40_parse_and_load_contexts(self):
        """FIXME: Write tests for jinja2_cli.render.parse_and_load_contexts
        """
        pass


if __name__ == '__main__':
    unittest.main()

# vim:sw=4:ts=4:et:
