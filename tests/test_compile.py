import unittest
import pyv8unpack
from os import path as path
import tempfile


class TestV8Unpack(unittest.TestCase):

    def test_compile_from_source(self):

        tpath = tempfile.mkdtemp()
        file = path.join(path.curdir, "tests", "Fixture.epf")
        assert pyv8unpack.decompile([file], tpath)
        tpath = path.join(tpath, "tests", "Fixture")
        filenew = tempfile.mktemp()
        assert pyv8unpack.compilefromsource(tpath, filenew, "epf") == filenew

    def test_decompile(self):

        tpath = tempfile.mkdtemp()
        file = path.join(path.curdir, "tests", "Fixture.epf")
        assert pyv8unpack.decompile([file], tpath)
