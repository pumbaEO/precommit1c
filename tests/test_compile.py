import unittest
import pyv8unpack
from os import path as path
import os
import tempfile
import shutil


class TestV8Unpack(unittest.TestCase):
    
    def setUp(self):

        unittest.TestCase.setUp(self)
        self.tpath = tempfile.mkdtemp()
        self.tfile = tempfile.mktemp()
        
        pathIb = path.join(path.curdir, ".git", "hooks", "ibService")
        if (path.exists(pathIb)):
        	shutil.rmtree(pathIb)
        shutil.copytree(path.join(path.curdir, "ibService"),
        	pathIb)
        shutil.copy(path.join(path.curdir, "V8Reader.epf"),
        	path.join(path.curdir, ".git", "hooks", "V8Reader.epf"))
        
    def tearDown(self):
    	import os
        if os.path.exists(self.tfile):
            os.remove(self.tfile)
        shutil.rmtree(self.tpath)
        shutil.rmtree(path.join(path.curdir, ".git", "hooks", "ibService"))
        os.remove(path.join(path.curdir, ".git", "hooks", "V8Reader.epf"))


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
