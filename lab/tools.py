import os
import sys
import shutil
import subprocess
import re
import traceback
import logging
import contextlib
import time
import math
import json

from external import argparse
from external.datasets import DataSet


LOG_LEVEL = None

# Directories and files

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPTS_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
CALLS_DIR = os.path.join(SCRIPTS_DIR, 'calls')
USER_DIR = os.path.join(os.path.expanduser('~'), 'lab')
REPORTS_DIR = os.path.join(USER_DIR, 'reports')

DEFAULT_EXP_DIR = os.path.join(USER_DIR, 'experiments')
DEFAULT_REPORTS_DIR = os.path.join(USER_DIR, 'reports')


def setup_logging(level):
    # Python adds a default handler if some log is written before now
    # Remove all handlers that have been added automatically
    root_logger = logging.getLogger('')
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    # Handler which writes LOG_LEVEL messages or higher to stdout
    console = logging.StreamHandler(sys.stdout)
    # set a format which is simpler for console use
    format='%(asctime)-s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(format)
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    root_logger.addHandler(console)
    root_logger.setLevel(level)


def prod(values):
    """Computes the product of a list of numbers.

    >>> print prod([2, 3, 7])
    42
    """
    assert len(values) >= 1
    prod = 1
    for value in values:
        prod *= value
    return prod


def minimum(values):
    """Filter out None values and return the minimum.

    If there are only None values, return None.
    """
    values = [v for v in values if v is not None]
    if values:
        return min(values)
    return None


def divide_list(seq, size):
    """
    >>> divide_list(range(10), 4)
    [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
    """
    return [seq[i:i + size] for i  in range(0, len(seq), size)]


def round_to_next_power_of_ten(i):
    assert i > 0
    return 10**math.ceil(math.log10(i))


def makedirs(dir):
    """
    mkdir variant that does not complain when the dir already exists
    """
    try:
        os.makedirs(dir)
    except OSError:
        # directory probably exists
        pass


def overwrite_dir(dir, overwrite=False):
    if os.path.exists(dir):
        logging.info('The directory "%s" is not empty.' % dir)
        if not overwrite:
            msg = 'Do you want to overwrite the existing directory? (Y/N): '
            answer = raw_input(msg).upper().strip()
            if not answer == 'Y':
                sys.exit('Aborted')
        shutil.rmtree(dir)
    # We use the os.makedirs method instead of our own here to check if the dir
    # has really been properly deleted.
    os.makedirs(dir)


def remove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


def natural_sort(alist):
    """Sort alist alphabetically, but special-case numbers to get
    file2.txt before file10.ext."""
    def to_int_if_number(text):
        if text.isdigit():
            return int(text)
        else:
            return text.lower()

    def extract_numbers(text):
        parts = re.split("([0-9]+)", text)
        return map(to_int_if_number, parts)

    return sorted(alist, key=extract_numbers)


def find_file(basenames, dir='.'):
    for basename in basenames:
        path = os.path.join(dir, basename)
        if os.path.exists(path):
            return path
    raise IOError('none found in %r: %r' % (dir, basenames))


def import_python_file(filename):
    parent_dir =  os.path.dirname(filename)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    filename = os.path.normpath(filename)
    filename = os.path.basename(filename)
    if filename.endswith('.py'):
        module_name = filename[:-3]
    elif filename.endswith('.pyc'):
        module_name = filename[:-4]
    else:
        module_name = filename

    try:
        module = __import__(module_name)
        return module
    except ImportError, err:
        logging.error('File "%s" could not be imported: %s' % (filename, err))
        print traceback.format_exc()
        sys.exit(1)


def run_command(cmd, **kwargs):
    """
    Runs command cmd and returns the output
    """
    assert type(cmd) is list
    logging.info('Running command: %s' % ' '.join(cmd))
    return subprocess.call(cmd, **kwargs)

def get_command_output(cmd, **kwargs):
    assert type(cmd) is list
    logging.info('Running command: %s' % ' '.join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, **kwargs)
    stdout, _ = p.communicate()
    return stdout.strip()


class Properties(dict):
    def __init__(self, filename=None):
        self.filename = filename
        self.load(filename)
        dict.__init__(self)

    def load(self, filename):
        if not filename or not os.path.exists(filename):
            return
        with open(filename) as f:
            self.update(json.load(f))

    def write(self):
        assert self.filename
        with open(self.filename, 'w') as f:
            json.dump(self, f, indent=4)

    def get_dataset(self):
        data = DataSet()
        for run_id, run in sorted(self.items()):
            # HACK: Python < 2.6.5 doesn't allow unicode keyword args.
            no_unicode = dict((k.encode('ascii'), v) for (k, v) in run.items())
            data.append(**no_unicode)
        return data


def fast_updatetree(src, dst, ignore=None):
    """
    Copies the contents from src onto the tree at dst, overwrites files with
    the same name

    Code taken and expanded from python docs
    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    makedirs(dst)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.isdir(srcname):
                fast_updatetree(srcname, dstname, ignore)
            else:
                shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error), why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Exception, err:
            errors.append(err.args[0])
    if errors:
        raise Exception(errors)


def copy(src, dest, required=True, ignores=None):
    """
    Copies a file or directory to another file or directory
    """
    if os.path.isfile(src) and os.path.isdir(dest):
        makedirs(dest)
        dest = os.path.join(dest, os.path.basename(src))
        shutil.copy2(src, dest)
    elif os.path.isfile(src):
        makedirs(os.path.dirname(dest))
        shutil.copy2(src, dest)
    elif os.path.isdir(src):
        if ignores:
            fast_updatetree(src, dest, ignore=shutil.ignore_patterns(*ignores))
        else:
            fast_updatetree(src, dest)
    elif required:
        logging.error('Required path %s cannot be copied to %s' %
                      (os.path.abspath(src), os.path.abspath(dest)))
        sys.exit(1)
    else:
        # Do not warn if an optional file cannot be copied.
        return


def csv(string):
    string = string.strip(', ')
    return string.split(',')


def get_terminal_size():
    import struct
    try:
        import fcntl, termios
    except ImportError:
        return (None, None)

    try:
        data = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, 4 * '00')
        height, width = struct.unpack('4H',data)[:2]
        return (height, width)
    except Exception:
        return (None, None)


class RawAndDefaultsHelpFormatter(argparse.HelpFormatter):
    """
    Help message formatter which retains any formatting in descriptions and adds
    default values to argument help.
    """
    def __init__(self, prog, **kwargs):
        # Use the whole terminal width
        height, width = get_terminal_size()
        argparse.HelpFormatter.__init__(self, prog, width=width, **kwargs)

    def _fill_text(self, text, width, indent):
        return ''.join([indent + line for line in text.splitlines(True)])

    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help and not 'default' in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += ' (default: %(default)s)'
        return help

    def _format_args(self, action, default_metavar):
        """
        We want to show "[environment-specific options]" instead of "...".
        """
        get_metavar = self._metavar_formatter(action, default_metavar)
        if action.nargs == argparse.PARSER:
            return '%s [environment-specific options]' % get_metavar(1)
        else:
            return argparse.HelpFormatter._format_args(self, action, default_metavar)


class ArgParser(argparse.ArgumentParser):
    def __init__(self, add_log_option=True, *args, **kwargs):
        argparse.ArgumentParser.__init__(self, *args,
                                formatter_class=RawAndDefaultsHelpFormatter,
                                **kwargs)
        if add_log_option:
            try:
                self.add_argument('-l', '--log-level', dest='log_level',
                        choices=['DEBUG', 'INFO', 'WARNING'], default='INFO')
            except argparse.ArgumentError:
                # The option may have already been added by a parent
                pass

    def parse_known_args(self, *args, **kwargs):
        args, remaining = argparse.ArgumentParser.parse_known_args(self, *args,
                                                                   **kwargs)

        global LOG_LEVEL
        # Set log level only once (May have already been deleted from sys.argv)
        if getattr(args, 'log_level', None) and not LOG_LEVEL:
            LOG_LEVEL = getattr(logging, args.log_level.upper())
            setup_logging(LOG_LEVEL)

        return (args, remaining)

    def set_help_active(self):
        self.add_argument(
                '-h', '--help', action='help', default=argparse.SUPPRESS,
                help=('show this help message and exit'))

    def directory(self, string):
        if not os.path.isdir(string):
            msg = '%r is not an evaluation directory' % string
            raise argparse.ArgumentTypeError(msg)
        return string


# Parse the log-level and set it
ArgParser(add_help=False).parse_known_args()


class Timer(object):
    def __init__(self):
        self.start_time = time.time()
        self.start_clock = self._clock()

    def _clock(self):
        times = os.times()
        return times[0] + times[1]

    def __str__(self):
        return "[%.3fs CPU, %.3fs wall-clock]" % (
            self._clock() - self.start_clock,
            time.time() - self.start_time)


@contextlib.contextmanager
def timing(text):
    timer = Timer()
    logging.info("%s..." % text)
    sys.stdout.flush()
    yield
    logging.info("%s: %s" % (text, timer))
    sys.stdout.flush()
