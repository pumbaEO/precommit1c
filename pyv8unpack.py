#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
from os.path import exists
import logging
import tempfile
import re

logging.basicConfig(level=logging.ERROR)  # DEBUG => print ALL msgs

modified = re.compile('^(?:M|A)(\s+)(?P<name>.*)')


def get_list_of_comitted_files():
    """
    Retun a list of files abouts to be decompile
    """
    files = []
    output = []
    try:
        output = subprocess.check_output(['git','diff-index', '--name-status', '--cached','HEAD']
            ).decode("utf-8")
    except subprocess.CalledProcessError:
        print("Error diff files get: trace %s" % subprocess.CalledProcessError.output)
        return files

    for result in output.split("\n"):
        logging.info(result)
        if result != '':
            match = modified.match(result)
            if match:
                files.append(match.group('name'))

    return files


def decompile():
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
        logging.info("file to check %s" % filename)
        if filename[-3:] in ['epf', 'erf']:
            dataprocessor_files.append(filename)
            logging.info("file %s" % filename)
            continue
    if len(dataprocessor_files) == 0:
        exit(exit_code)

    dirsource = os.path.abspath(os.path.join(os.path.curdir, "src"))
    curabsdirpath = os.path.abspath(os.path.curdir)
    pathbin1c = "C:\\Program Files\\1cv82\8.2.17.153\\bin\\1cv8.exe"
    pathbin1c = "c:\\Program Files (x86)\\1cv8\\8.3.4.304\\bin\\1cv8.exe"

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
        if not os.path.exists(newsourcepath):
            logging.info("create new dir %s" % newsourcepath)
            os.makedirs(newsourcepath)

        logging.info("file to copy %s, new path %s, new file %s" % (filename, newsourcepath,
                      os.path.join(newsourcepath,fullbasename)))

        formatstring = format('/C"decompile;pathtocf;%s;pathout;%s;ЗавершитьРаботуПосле;"' % (fullpathfile, newsourcepath))
        base = '/F"'+os.path.join(curabsdirpath,".git", "hooks","ibService")+'"'
        V8Reader = '/execute"'+os.path.join(curabsdirpath,".git", "hooks", "V8Reader.epf")+'"'
        tempbat = tempfile.mktemp(".bat")
        logging.info("formatstring is %s , base is %s, V8Reader is %s, temp is %s" % (formatstring, base, V8Reader, tempbat))

        with open(tempbat, 'w', encoding='cp866') as temp:
            temp.write('@echo off\n')
            temp.write(format('"%s" %s /DisableStartupMessages %s %s'%(pathbin1c, base, V8Reader, formatstring)))
            temp.close()
            result = subprocess.check_call(['cmd.exe', '/C', tempbat])
            result = subprocess.check_call(['git', 'add', '--all', newsourcepath])
            if not result == 0:
                logging.error(result)
                exit(result)


if __name__ == '__main__':
    decompile()
