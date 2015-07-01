#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import logging
import os
import platform
import re
import subprocess
import shutil
import sys
import tempfile

__version__ = '0.0.3'

logging.basicConfig(level=logging.INFO)  # DEBUG => print ALL msgs
log = logging.getLogger('pyv8unpack')

modified = re.compile('^(?:M|A)(\s+)(?P<name>.*)')


def get_config_param(param):
    """
    Parse config file and find source dir in it
    """
    curdir = os.curdir
    if '__file__' in globals():
        curdir = os.path.dirname(os.path.abspath(__file__))

    config = None
    for loc in curdir, os.curdir, os.path.expanduser('~'):
        try:
            with open(os.path.join(loc, 'precommit1c.ini')) as source:
                if sys.version_info < (3, 0, 0):
                    from ConfigParser import ConfigParser  # @NoMove @UnusedImport
                else:
                    from configparser import ConfigParser

                config = ConfigParser()
                config.read_file(source)
                break
        except IOError:
            pass

    if config is not None and config.has_option('default', param):
        value = config.get('default', param)
        return value

    return None


def get_path_to_1c():
    """
    Get path to 1c binary.
    First env, 'PATH1C'
    Second env 'PROGRAMFILES' (only Windows)
    Third '/opt/1c' (only Linux)
    """
    cmd = os.getenv('PATH1C')
    if cmd is not None:
        cmd = os.path.join(cmd, '1cv8')
        maxversion = max(list(filter((lambda x: '8.' in x), os.listdir(cmd))))
        if maxversion is None:
            raise Exception('Not found version dirs')
        cmd = os.path.join(cmd, maxversion + os.path.sep + 'bin' + os.path.sep + '1cv8.exe')

        if not os.path.isfile(cmd):
            raise Exception('File not found {}'.format(cmd))

        return cmd

    # Read config
    curdir = os.curdir
    if '__file__' in globals():
        curdir = os.path.dirname(os.path.abspath(__file__))

    onec_platform_config = get_config_param('onec_platform')
    if onec_platform_config is not None:
        return onec_platform_config

    if platform.system() == 'Darwin':
        raise Exception('MacOS not run 1C')
    elif platform.system() == 'Windows':
        program_files = os.getenv('PROGRAMFILES(X86)')
        if program_files is None:
            # fixme Проверить архитектуру
            program_files = os.getenv('PROGRAMFILES')
            if program_files is None:
                raise Exception('Path to "Program files" not found')
        cmd = os.path.join(program_files, '1cv8')
        maxversion = max(list(filter((lambda x: '8.' in x), os.listdir(cmd))))
        if maxversion is None:
            raise Exception('Not found version dirs')
        cmd = os.path.join(cmd, maxversion + os.path.sep + 'bin' + os.path.sep + '1cv8.exe')

        if not os.path.isfile(cmd):
            raise Exception('File not found {}'.format(cmd))

    else:
        cmd = subprocess.Popen(['which', '1cv8'], stdout=subprocess.PIPE).communicate()[0].strip()

    return cmd


def get_list_of_comitted_files():
    """
    Return the list of files to be decompiled
    """
    files = []
    output = []
    try:
        output = subprocess.check_output(['git', 'diff-index', '--name-status', '--cached', 'HEAD']).decode('utf-8')
    except subprocess.CalledProcessError:
        try:
            output = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8')
        except subprocess.CalledProcessError:
            print('Error diff files get')
            return files

    for result in output.split('\n'):
        logging.info(result)
        if result != '':
            match = modified.match(result)
            if match:
                files.append(match.group('name'))

    return files


def decompile(list_of_files, source=None, platform_=None):
    """
    Main functions doing be decompile
    возвращает list
    """
    # List of files to decompile and results decompile
    dataprocessor_files = []

    # set the exit code
    exit_code = 0

    # Find datapocessor files
    for filename in list_of_files:
        # Check the file extensions
        logging.debug('File to check {}'.format(filename))
        if filename[-3:] in ['epf', 'erf']:
            dataprocessor_files.append(filename)
            logging.debug('File {}'.format(filename))
            continue
    if len(dataprocessor_files) == 0:
        exit(exit_code)

    source_dir = source or get_config_param('source')
    if source_dir is None:
        source_dir = 'src'

    # Получаем флажок того, что исходники располагаются в подпапке источника
    source_in_source = get_config_param('source_in_source')
    if source_in_source is None:
        source_in_source = False
    else:
        if source_in_source == 'True':
            source_in_source = True
        else:
            source_in_source = False

    dirsource = os.path.abspath(os.path.join(os.path.curdir, source_dir))
    curabsdirpath = os.path.abspath(os.path.curdir)
    pathbin1c = platform_ or get_path_to_1c()
    returnlist = []

    for filename in dataprocessor_files:
        logging.info('File {}'.format(filename))

        fullpathfile = os.path.abspath(filename)
        basename = os.path.splitext(os.path.basename(filename))[0]
        fullbasename = os.path.basename(filename)
        newdirname = os.path.dirname(filename)

        # Если исходники в подпапке источника, меняем путь
        if source_in_source:
            dirsource = os.path.abspath(os.path.join(os.path.curdir, newdirname, source_dir))

        # Скопируем сначало просто структуру каталогов
        if not os.path.exists(dirsource):
            os.makedirs(dirsource)
        # Для каждого файла определим новую папку
        if source_in_source:
            logging.debug('{} {}'.format(dirsource, basename))
            newsourcepath = os.path.join(dirsource, basename)
        else:
            logging.debug('{} {} {}'.format(dirsource, newdirname, basename))
            newsourcepath = os.path.join(dirsource, newdirname, basename)

        if os.path.isabs(newdirname):
            newsourcepath = os.path.join(dirsource, basename)
        if not os.path.exists(newsourcepath):
            logging.debug('create new dir {}'.format(newsourcepath))
            os.makedirs(newsourcepath)
        else:
            shutil.rmtree(newsourcepath, ignore_errors=True)

        logging.debug('File to copy {}, new path {}, new file {}'.format(filename, newsourcepath,
                                                                     os.path.join(newsourcepath, fullbasename)))

        formatstring = format('/C"decompile;pathtocf;{};pathout;{};ЗавершитьРаботуПосле;"'.format(fullpathfile,
                                                                                                  newsourcepath))
        base = '/F"' + os.path.join(curabsdirpath, '.git', 'hooks', 'ibService') + '"'
        v8_reader = '/execute"' + os.path.join(curabsdirpath, '.git', 'hooks', 'v8Reader', 'V8Reader.epf') + '"'
        tempbat = tempfile.mktemp('.bat')
        logging.debug('Formatstring is {} , base is {}, V8Reader is {}, temp is {}'.format(formatstring,
                                                                                           base, v8_reader, tempbat))

        with open(tempbat, 'w', encoding='cp866') as temp:
            temp.write('@echo off\n')
            temp.write(format('"{}" {} /DisableStartupMessages {} {}'.format(pathbin1c, base, v8_reader, formatstring)))
            temp.close()
            result = subprocess.check_call(['cmd.exe', '/C', tempbat])
            assert result == 0, format('Не удалось разобрать обработку {}'.format(fullpathfile))
            if not result == 0:
                logging.error(format('Не удалось разобрать обработку {}'.format(fullpathfile)))
                raise format('Не удалось разобрать обработку {}'.format(fullpathfile))
            returnlist.append(newsourcepath)
            logging.info('Разобран в {}'.format(newsourcepath))

    return returnlist


def add_to_git(pathlists):
    for l in pathlists:
        result = subprocess.check_call(['git', 'add', '--all', l])
        if not result == 0:
            logging.error(result)
            exit(result)

def findexecute(name):
    found = []
    ext = ''
    searchpath = os.environ.get("PATH", "").split(os.pathsep)
    if sys.platform.startswith("win"):
        ext = '.exe'
        searchpath.insert(0, os.curdir)  # implied by Windows shell
    
    for i in range(len(searchpath)):
        dirName = searchpath[i]
        # On windows the dirName *could* be quoted, drop the quotes
        if sys.platform.startswith("win") and len(dirName) >= 2\
           and dirName[0] == '"' and dirName[-1] == '"':
            dirName = dirName[1:-1]
        absName = os.path.abspath(
            os.path.normpath(os.path.join(dirName, name+ext)))
        if os.path.isfile(absName) and not absName in found:
            found.append(absName)
    
    firstpath = ""
    if len(found) > 0: firstpath = found[0]
    return firstpath

def compilefromsource(input_, output, ext):
    import codecs

    assert input_ is not None, 'Не указан путь к входящему каталогу'
    assert output is not None, 'Не указан путь к исходящему файлу'

    extfile = 'epf' if ext == 'auto' else ext

    dirsource = os.path.abspath(os.path.join(os.path.curdir, input_))
    if not os.path.exists(dirsource) or not os.path.isdir(dirsource):
        raise Exception('Не существует входящего каталога')

    renames_file = os.path.join(dirsource, 'renames.txt')
    if not os.path.exists(renames_file):
        raise 'Не существует файла {}'.format(renames_file)
    temp_path = tempfile.mkdtemp()

    with codecs.open(renames_file, 'rb', encoding='utf-8') as r:
        lines = r.read()
        lines = lines.split('\r\n')
        for l in lines:
            if l.startswith(u'\ufeff'):
                l = l[1:]
            listline = l.split('-->')
            if len(listline) < 2:
                continue
            log.debug(l)
            new_path = os.path.join(temp_path, listline[0])
            dirname = os.path.dirname(new_path)
            if not os.path.exists(dirname):
                os.mkdir(dirname)
            old_path = os.path.join(dirsource, listline[1].replace('\\', os.path.sep))

            if os.path.isdir(old_path):
                new_path = os.path.join(temp_path, listline[0])
                shutil.copytree(old_path, new_path)
            else:
                log.debug(old_path)
                shutil.copy(os.path.normpath(old_path), new_path)

        # Вызовем v8unpack для сборки файла из исходников
        temp_file = tempfile.mktemp('.' + extfile)
        unpackpath = findexecute("unpackv8")
        assert (len(unpackpath) > 0), "path to unpackv8 is empty"
        log.debug('{} -B "{}" "{}"'.format(unpackpath, '{}'.format(temp_path), temp_file))
        print('{} -B "{}" "{}"'.format(unpackpath, '{}'.format(temp_path), temp_file))
        result = subprocess.check_call([
            unpackpath,
            '-B',
            '{}'.format(temp_path),  # fixme
            temp_file
        ])

        log.debug('Copy from {} to {}'.format(temp_file, output))
        assert result == 0, 'Не удалось упаковать каталог {}'.format(temp_path)
        shutil.move(temp_file, output)

        return output


def main():
    parser = argparse.ArgumentParser(description='Утилита для автоматической распаковки внешних обработок')
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-v', '--verbose', dest='verbose_count', action='count', default=0,
                        help='Increases log verbosity for each occurence.')
    parser.add_argument('--index', action='store_true', default=False, help='Добавляем в индекс исходники')
    parser.add_argument('--g', action='store_true', default=False,
                        help='Запустить чтение индекса из git и определить список файлов для разбора')
    parser.add_argument('--compile', action='store_true', default=False, help='Собрать внешний файл/обработку')
    parser.add_argument('--type', action='store', default='auto',
                        help='Тип файла для сборки epf, erf. По умолчанию авто epf')
    parser.add_argument('--platform', action='store', help='Путь к платформе 1С')
    parser.add_argument('inputPath', nargs='?', help='Путь к файлам необходимым для распаковки')
    parser.add_argument('output', nargs='?', help='Путь к каталогу, куда распаковывать')

    args = parser.parse_args()

    log.setLevel(max(3 - args.verbose_count, 0) * 10)

    if args.g is True:
        files = get_list_of_comitted_files()
        indexes = decompile(files, args.output, args.platform)
        if args.index is True:
            add_to_git(indexes)

    if args.compile:
        compilefromsource(args.inputPath, args.output, args.type)
    if args.inputPath is not None:
        files = [os.path.abspath(os.path.join(os.path.curdir, args.inputPath))]
        if os.path.isdir(files[0]):
            root_dir = os.path.abspath(os.path.join(os.path.curdir, args.inputPath))
            files = []
            for dirName, subdirList, fileList in os.walk(root_dir):
                absdir = dirName[len(root_dir) + 1:]
                if '.git' in subdirList:
                    subdirList.remove('.git')
                if 'src' in subdirList:
                    subdirList.remove('src')
                for fname in fileList:
                    files.append(os.path.join(absdir, fname))

        decompile(files, args.output, args.platform)


if __name__ == '__main__':
    sys.exit(main())
