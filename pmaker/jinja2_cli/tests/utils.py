#
# Copyright (C). 2011, 2012 Satoru SATOH <ssato at redhat.com>
#
import pmaker.jinja2_cli.utils as U
import unittest


class Test_00_functions(unittest.TestCase):

    def test_02_uniq(self):
        self.assertEquals(U.uniq([]), [])
        self.assertEquals(
            U.uniq([1, 4, 5, 1, 2, 3, 5, 10, 13, 2]),
            [1, 4, 5, 2, 3, 10, 13]
        )

    def test_03_chaincalls(self):
        self.assertEquals(
            U.chaincalls([lambda x: x + 1, lambda x: x - 1], 1),
            1
        )

    def test_04_normpath(self):
        self.assertEquals(U.normpath("/tmp/../etc/hosts"), "/etc/hosts")
        self.assertEquals(U.normpath("~root/t"), "/root/t")

    def test_05_flip(self):
        self.assertEquals(U.flip((1, 3)), (3, 1))

    def test_06_concat(self):
        self.assertEquals(U.concat([]), [])
        self.assertEquals(U.concat(()), [])
        self.assertEquals(U.concat([[1, 2, 3], [4, 5]]), [1, 2, 3, 4, 5])
        self.assertEquals(
            U.concat([[1, 2, 3], [4, 5, [6, 7]]]), [1, 2, 3, 4, 5, [6, 7]]
        )
        self.assertEquals(
            U.concat(((1, 2, 3), (4, 5, [6, 7]))), [1, 2, 3, 4, 5, [6, 7]]
        )
        self.assertEquals(
            U.concat((i, i * 2) for i in range(3)), [0, 0, 1, 2, 2, 4]
        )


if __name__ == '__main__':
    unittest.main()

# vim:sw=4:ts=4:et:
