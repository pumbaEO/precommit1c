#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import logging
import tempfile
import re
import platform
import argparse
from subprocess import PIPE

__version__ = "0.0.3"

logging.basicConfig(level=logging.INFO) # DEBUG => print ALL msgs
log = logging.getLogger("pyv8unpack")

modified = re.compile('^(?:M|A)(\s+)(?P<name>.*)')


def get_config_param(param):
    '''
    parse config file and find in them source dir
    '''

    curdir = os.curdir
    if '__file__' in globals():
        curdir = os.path.dirname(os.path.abspath(__file__))


    config = None
    for loc in curdir, os.curdir, os.path.expanduser("~"):
        try:
            with open(os.path.join(loc, "precommit1c.ini")) as source:
                if sys.version_info<(3,0,0):
                    from ConfigParser import ConfigParser  # @NoMove @UnusedImport
                else:
                    from configparser import ConfigParser

                config = ConfigParser()
                config.read_file(source)
                break
        except IOError:
            pass

    if not config is None and config.has_option("DEFAULT", param):
        value = config.get("DEFAULT", param)
        return value


    return None


def get_path_to_1c():
    """
    get path to 1c binary.
    fist env, "PATH1C"
    two env "PROGRAMFILES" on windows
    three /opt/1c - only linux

    """

    cmd = os.getenv("PATH1C")
    if not cmd is None:
        cmd = os.path.join(cmd, "1cv8")
        maxversion = max(list(filter((lambda x: '8.' in x), os.listdir(cmd))))
        if maxversion is None:
            raise Exception("not found verion dirs")
        cmd = os.path.join(cmd, maxversion+os.path.sep+"bin"+os.path.sep+"1cv8.exe")

        if not os.path.isfile(cmd):
            raise Exception("file not found %s" % (cmd))

        return cmd

    #read config

    curdir = os.curdir
    if '__file__' in globals():
        curdir = os.path.dirname(os.path.abspath(__file__))


    onecplatfrorm_config = get_config_param("onecplatfrorm")
    if not onecplatfrorm_config is None:
        return onecplatfrorm_config

    if platform.system() == "Darwin":
        raise Exception("MacOS not run 1C")
    elif platform.system() == "Windows":
        program_files = os.getenv("PROGRAMFILES(X86)")
        if program_files is None:
            #FIXME: проверить архетиктуру.
            program_files = os.getenv("PROGRAMFILES")
            if program_files is None:
                raise "path to Program files not found";
        cmd = os.path.join(program_files, "1cv8")
        maxversion = max(list(filter((lambda x: '8.' in x), os.listdir(cmd))))
        if maxversion is None:
            raise Exception("not found verion dirs")
        cmd = os.path.join(cmd, maxversion + os.path.sep + "bin"+os.path.sep+"1cv8.exe")

        if not os.path.isfile(cmd):
            raise Exception("file not found %s" % (cmd))

    else:
        cmd = subprocess.Popen(["which", "1cv8"], stdout=PIPE).communicate()[0].strip()

    return cmd

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

def decompile(list_of_files, source=None, platform=None):
    """
    Main functions doing be decompile
    возвращает list
    """

    #list of files to decompile and results decompile
    dataprocessor_files = []

    #set the exit code
    exit_code = 0

    #Find datapocessor files
    for filename in list_of_files:
        #Check the file extensions
        logging.debug("file to check %s" % filename)
        if filename[-3:] in ['epf', 'erf']:
            dataprocessor_files.append(filename)
            logging.debug("file %s" % filename)
            continue
    if len(dataprocessor_files) == 0:
        exit(exit_code)

    source_dir = source or get_config_param("source")
    if source_dir is None:
        source_dir = "src"

    dirsource = os.path.abspath(os.path.join(os.path.curdir, source_dir))
    curabsdirpath = os.path.abspath(os.path.curdir)
    pathbin1c = platform or get_path_to_1c()
    returnlist = []

    for filename in dataprocessor_files:
        logging.info("file %s" % filename)

        fullpathfile = os.path.abspath(filename)
        basename = os.path.splitext(os.path.basename(filename))[0]
        fullbasename = os.path.basename(filename)
        newdirname = os.path.dirname(filename)

        #Скопируем сначало просто структуру каталогов.
        if not os.path.exists(dirsource):
            os.makedirs(dirsource)
        #для каждого файла определим новую папку.
        logging.debug("{} {} {}".format(dirsource, newdirname, basename))
        newsourcepath = os.path.join(dirsource, newdirname, basename)
        if(os.path.isabs(newdirname)):
            newsourcepath = os.path.join(dirsource, basename)
        if not os.path.exists(newsourcepath):
            logging.debug("create new dir %s" % newsourcepath)
            os.makedirs(newsourcepath)
        else:
            shutil.rmtree(newsourcepath, ignore_errors=True)

        logging.debug("file to copy %s, new path %s, new file %s"
            % (filename, newsourcepath, os.path.join(newsourcepath, fullbasename))
        )

        formatstring = format('/C"decompile;pathtocf;%s;pathout;%s;ЗавершитьРаботуПосле;"' % (fullpathfile, newsourcepath))
        base = '/F"'+os.path.join(curabsdirpath,".git", "hooks","ibService")+'"'
        V8Reader = '/execute"'+os.path.join(curabsdirpath,".git", "hooks", "V8Reader.epf")+'"'
        tempbat = tempfile.mktemp(".bat")
        logging.debug("formatstring is %s , base is %s, V8Reader is %s, temp \
            is %s" % (formatstring, base, V8Reader, tempbat))

        with open(tempbat, 'w', encoding='cp866') as temp:
            temp.write('@echo off\n')
            temp.write(format('"%s" %s /DisableStartupMessages %s %s' % (pathbin1c,
                            base, V8Reader, formatstring))
                       )
            temp.close()
            result = subprocess.check_call(['cmd.exe', '/C', tempbat])
            assert result == 0, format("Не удалось разобрать\
                                обработку %s" % (fullpathfile))
            if not result == 0:
                logging.error(format("Не удалось разобрать \
                    обработку %s" % (fullpathfile)))
                raise format("Не удалось разобрать\
                                обработку %s" % (fullpathfile))
            returnlist.append(newsourcepath)
            logging.info("Разобран в %s" % (newsourcepath))

    return returnlist

def add_to_git(pathlists):

    for l in pathlists:
        result = subprocess.check_call(['git', 'add', '--all', l])
        if not result == 0:
            logging.error(result)
            exit(result)

def compilefromsource(input, output, ext):
    import codecs

    assert not input is None, "Не указан путь к входящему каталогу"
    assert not output is None, "Не указан путь к исходящему файлу"

    extfile = "epf" if ext == "auto" else ext

    dirsource = os.path.abspath(os.path.join(os.path.curdir, input))
    if not os.path.exists(dirsource) or not os.path.isdir(dirsource):
        raise "Не существует входящего каталога"

    renamesFile = os.path.join(dirsource, "renames.txt")
    if not os.path.exists(renamesFile):
        raise "Не существует файла {}".format(renamesFile)
    tempPath = tempfile.mkdtemp()

    with codecs.open(renamesFile, "rb", encoding='utf-8') as r:
        lines = r.read()
        lines = lines.split('\r\n')
        for l in lines:
            if l.startswith(u'\ufeff'):
                l = l[1:]
            listline = l.split("-->") 
            if len(listline) < 2:
                continue
            log.debug(l)
            newPath = os.path.join(tempPath, listline[0])
            dirname = os.path.dirname(newPath)
            if not os.path.exists(dirname):
                os.mkdir(dirname)
            oldPath = os.path.join(dirsource,
                                   listline[1].replace(
                                   "\\", os.path.sep)
                                   )

            if os.path.isdir(oldPath):
                #tempFile = tempfile.mkstemp()
                newPath = os.path.join(tempPath, listline[0])
                shutil.copytree(oldPath, newPath)
            else:
                log.debug(oldPath)
                shutil.copy(
                    os.path.normpath(oldPath),
                    newPath
                )

        #вызовем v8unpack, для сборки файла из исходников.
        tempFile = tempfile.mktemp("."+extfile)
        log.debug('unpackv8 -B "{}" "{}"'.format('{}'.format(tempPath), tempFile))
        result = subprocess.check_call(
            ['unpackv8',
             '-B',
             '{}'.format(tempPath),
             tempFile]
        )

        log.debug("copy from {} to {}".format(tempFile, output))
        assert result == 0, "Не удалось упаковать каталог {}".format(tempPath)
        shutil.move(tempFile, output)

        return output

def main():

    parser = argparse.ArgumentParser(description="Утилита \
        для автоматической распаковки внешних обработок")
    parser.add_argument("--version", action="version",
        version="%(prog)s {}".format(__version__))
    parser.add_argument("-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increases log verbosity for each occurence.")
    parser.add_argument("--index", action="store_true",
        default=False, help="Добавляем в индекс исходники")
    parser.add_argument("--g", action="store_true", default=False,
        help="Запуситить чтение индекса из git и определить\
        список файлов для разбора")
    parser.add_argument("--compile", action="store_true", default=False,
                        help = "Собрать внешний файл/обработку")
    parser.add_argument("--type", action="store", default="auto",
                        help="Тип файла для сборки epf, erf. По умолчанию авто epf")
    parser.add_argument("--platform", action="store", help="Путь \
        к платформе 1С")
    parser.add_argument("inputPath", nargs="?", help="Путь к \
        файлам необходимым для распаковки")
    parser.add_argument("output", nargs="?", help="Путь к \
        каталогу, куда распаковывать")

    args = parser.parse_args()

    log.setLevel(max(3 - args.verbose_count, 0) * 10)

    if args.g is True:
        files = get_list_of_comitted_files()
        indexes = decompile(files, args.output, args.platform)
        if args.index is True:
            add_to_git(indexes)

    if(args.compile):
        compilefromsource(args.inputPath, args.output, args.type)
    if args.inputPath is not None:
        files = [os.path.abspath(
            os.path.join(os.path.curdir, args.inputPath))]
        if os.path.isdir(files[0]):
            rootDir = os.path.abspath(
                        os.path.join(os.path.curdir, args.inputPath));
            files=[]
            for dirName, subdirList, fileList in os.walk(rootDir):
                absdir = dirName[len(rootDir)+1:]
                if '.git' in subdirList:
                    subdirList.remove('.git')
                if 'src' in subdirList:
                    subdirList.remove('src')
                for fname in fileList:
                    files.append(os.path.join(absdir,fname))
                
        decompile(
            files, args.output, args.platform)


if __name__ == '__main__':
    sys.exit(main())
