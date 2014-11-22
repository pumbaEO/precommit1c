import unittest
import pyv8unpack
from os import path as path
import os
import tempfile
import shutil
from pathlib import Path
import subprocess


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
        os.mkdir(path.join(path.curdir, ".git", "hooks", "v8Reader"))
        shutil.copy(path.join(path.curdir, "v8Reader", "V8Reader.epf"),
            path.join(path.curdir, ".git", "hooks", "v8Reader", "V8Reader.epf"))
        
    def tearDown(self):

        if os.path.exists(self.tfile):
            os.remove(self.tfile)
        shutil.rmtree(self.tpath)
        shutil.rmtree(path.join(path.curdir, ".git", "hooks", "ibService"))
        os.remove(path.join(path.curdir, ".git", "hooks", "v8Reader", "V8Reader.epf"))
        shutil.rmtree(path.join(path.curdir, ".git", "hooks", "v8Reader"))


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
        
    def test_decompile_checkfullpath(self):
        
        self.tpath = tempfile.mkdtemp()
        file = path.join(path.curdir, "tests", "Fixture.epf")
        assert pyv8unpack.decompile([file], self.tpath);


class TestGitInit(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.tpath = tempfile.mkdtemp()
        self.curdir = os.path.abspath(os.curdir);

        print("cur dir {}, temp path {}".format(self.curdir, self.tpath))

        os.chdir(self.tpath)
        
        try:
            output = subprocess.check_output(['git','init', self.tpath]
                ).decode("utf-8")
        except subprocess.CalledProcessError:
            print("Error diff files get: trace %s" % subprocess.CalledProcessError.output)

        pathIb = path.join(self.tpath, ".git", "hooks", "ibService")
        if (path.exists(pathIb)):
            shutil.rmtree(pathIb)
        shutil.copytree(path.join(self.curdir, "ibService"),
            pathIb)
        os.mkdir(path.join(self.tpath, ".git", "hooks", "v8Reader"))
        shutil.copy(path.join(self.curdir, "v8Reader", "V8Reader.epf"),
            path.join(self.tpath, ".git", "hooks", "v8Reader", "V8Reader.epf"))
        shutil.copy(path.join(self.curdir,"pre-commit"), 
        	path.join(self.tpath, ".git", "hooks", "pre-commit"))
        shutil.copy(path.join(self.curdir,"pyv8unpack.py"), 
        	path.join(self.tpath, ".git", "hooks", "pyv8unpack.py"))
            

    def tearDown(self):

        #shutil.rmtree(self.tpath)
        os.chdir(self.curdir)
        print("cur dir {}".format(os.curdir))

    def test_firstadd(self):
        file = path.join(self.curdir, "tests", "Fixture.epf")    
        shutil.copy(file,
            path.join(self.tpath, "Fixture.epf"))


        output = subprocess.check_output(['git','add', "-A", "."]
                ).decode("utf-8")
        print("output {}".format(output))
        output = subprocess.check_output(['git','commit', "-m", "'init commit'"]
                ).decode("utf-8")
        print("output {}".format(output))

        


