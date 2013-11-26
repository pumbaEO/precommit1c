#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
from os.path import exists
import logging
import tempfile

logging.basicConfig(level=logging.ERROR)  # DEBUG => print ALL msgs

def get_list_of_comitted_files():
    """
    Retun a list of files abouts to be decompile
    """

    files = []
    output = []
    try:
        output = subprocess.check_output(['git','diff-index', '--cached','HEAD']).decode("utf-8")
    except subprocess.CalledProcessError:
        print("Error diff files get: trace %s" % subprocess.CalledProcessError.output)
        return files


    for result in output.split("\n"):
        if result != '':
            result = result.split()
            if result[4] in ['A', 'M']:
                files.append(result[5])

    return files

def _copyonlydirs(path, names):
    result = []
    for name in names:
        if os.path.isfile(os.path.join(path, name, os.path.sep)):
            result.append(name)
    logging.info('Working in %s' % path)
    return result

def checker():
    """
    Main functions doing be decompile
    """

    #list of files to decompile and results decompile
    dataprocessor_files = []

    #set the exit code
    exit_code = 0

    #Find datapocessor files
    for filename in get_list_of_comitted_files():
        #Check the file extensions
        if filename[-3:] in ['epf', 'erf', '.py']:
            dataprocessor_files.append(filename)
            logging.info("file %s" % filename)
            continue
    if len(dataprocessor_files) == 0:
        exit(exit_code)

    dirsource = os.path.abspath(os.path.join(os.path.curdir, "src"))
    curabsdirpath = os.path.abspath(os.path.curdir)
    pathbin1c = "C:\\Program Files\\1cv82\8.2.17.153\\bin\\1cv8.exe"

    for filename in dataprocessor_files:
        print("file %s" % filename)
        #TODO: добавить копирование этих же файлов в каталог src/имяфайла/...
        #get file name.
        fullpathfile = os.path.abspath(filename)
        basename = os.path.splitext(os.path.basename(filename))[0]
        fullbasename = os.path.basename(filename)
        newdirname = os.path.dirname(filename)

        #Скопируем сначало просто структуру каталогов.
        if not os.path.exists(dirsource):
            os.makedirs(dirsource)
        #для каждого файла определим новую папку.
        newsourcepath = os.path.join(dirsource, newdirname, basename)
        logging.info("create new dir %s" % newsourcepath)
        if not os.path.exists(newsourcepath):
            logging.info("create new dir %s" % newsourcepath)
            os.makedirs(newsourcepath)

        logging.info("file to copy %s, new path %s, new file %s" % (filename, newsourcepath,
                      os.path.join(newsourcepath,fullbasename)))

        formatstring = format('/C"decompile;pathtocf;%s;pathout;%s;ЗавершитьРаботуПосле;"' % (fullpathfile, newsourcepath))
        base = '/F"'+os.path.join(curabsdirpath,".git", "hooks","ibService")+'"'
        V8Reader = '/execute"'+os.path.join(curabsdirpath,".git", "hooks", "V8Reader.epf")+'"'
        logging.info(formatstring)
        logging.info(base)
        logging.info(V8Reader)
        tempbat = tempfile.mktemp(".bat")
        logging.info(tempbat)

        with open(tempbat, 'w', encoding='cp866') as temp:
            temp.write('@echo off\n')
            temp.write(format('"%s" %s /DisableStartupMessages %s %s'%(pathbin1c, base, V8Reader, formatstring)))
            temp.close()
            result = subprocess.check_call(['cmd.exe', '/C', tempbat])
            result = subprocess.check_call(['git', 'add', newsourcepath])
        #shutil.copyfile(filename, os.path.join(newsourcepath, fullbasename))


if __name__ == '__main__':
    checker()
