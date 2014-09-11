import unittest
import pyv8unpack
from os import path as path
import tempfile
import shutil


class TestV8Unpack(unittest.TestCase):
    
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.tpath = tempfile.mkdtemp()
        self.tfile = tempfile.mktemp()
        
    def tearDown(self):
        import os
        if os.path.exists(self.tfile):
            os.remove(self.tfile)
        shutil.rmtree(self.tpath)


    def test_compile_from_source(self):
        
        self.tpath = tempfile.mkdtemp()
        file = path.join(path.curdir, "tests", "Fixture.epf")
        assert pyv8unpack.decompile([file], self.tpath)
        tpath = path.join(self.tpath, "tests", "Fixture")
        assert pyv8unpack.compilefromsource(tpath, self.tfile, "epf") == self.tfile
        self.assertTrue(path.exists(self.tfile), "Собранный файл не существует {}".format(self.tfile))
        

    def test_decompile(self):
        
        self.tpath = tempfile.mkdtemp()
        file = path.join(path.curdir, "tests", "Fixture.epf")
        assert pyv8unpack.decompile([file], self.tpath)
