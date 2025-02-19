"""
Wrappers of commonly used functions to reduce line count and provide an
aesthetically similar look in SeisFlows3. Mostly concerend with file
manipulation, but also math and calling functions as well.
"""
import os
import re
import time
import yaml
import json
import pickle
import subprocess
import numpy as np
from importlib import import_module
from pkgutil import find_loader

from seisflows3.tools import msg


class Struct(dict):
    """
    Revised dictionary structure
    """
    def __init__(self, *args, **kwargs):
        super(Struct, self).__init__(*args, **kwargs)
        self.__dict__ = self


def diff(list1, list2):
    """
    Difference between unique elements of lists

    :type list1: list
    :param list1: first list
    :type list2: list
    :param list2: second list
    """
    c = set(list1).union(set(list2))
    d = set(list1).intersection(set(list2))

    return list(c - d)


def divides(i, j):
    """
    Return True if `j` divides `i`.

    Bryant: I don't think this works in python3?

    :type i: int
    :type j :int
    """
    if j == 0:
        return False
    elif i % j:
        return False
    else:
        return True


def exists(names):
    """
    Wrapper for os.path.exists that also works on lists

    :type names: list or str
    :param names: list of names to check existnce
    """
    for name in iterable(names):
        if not name:
            return False
        elif not isinstance(name, str):
            raise TypeError
        elif not os.path.exists(name):
            return False
    else:
        return True


def findpath(name):
    """
    Resolves absolute path of module

    :type name: str
    :param name: absolute path of str
    """
    path = import_module(name).__file__

    # Adjust file extension
    path = re.sub('.pyc$', '.py', path)

    # Strip trailing "__init__.py"
    path = re.sub('__init__.py$', '', path)

    return path


def iterable(arg):
    """
    Make an argument iterable

    :param arg: an argument to make iterable
    :type: list
    :return: iterable argument
    """
    if not isinstance(arg, (list, tuple)):
        return [arg]
    else:
        return arg


def module_exists(name):
    """
    Determine if a module loader exists

    :type name: str
    :param name: name of module
    """
    return find_loader(name)


def package_exists(name):
    """
    Determine if a package exists

    :type name: str
    :param name: name of package
    """
    return find_loader(name)


def pkgpath(name):
    """
    Path to Seisflows package

    :type name: str
    :param name: name of package
    """
    for path in import_module('seisflows').__path__:
        if os.path.join(name, 'seisflows') in path:
            return path


def timestamp():
    """
    Return a timestamp for current time
    """
    return time.strftime('%H:%M:%S')


def loadyaml(filename):
    """
    Define how the PyYaml yaml loading function behaves. 
    Replaces None and inf strings with NoneType and numpy.inf respectively
    
    :type filename: str
    :param filename: .yaml file to load in
    """
    # work around PyYAML bugs
    yaml.SafeLoader.add_implicit_resolver(
        u'tag:yaml.org,2002:float',
        re.compile(u'''^(?:
         [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
        |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
        |\\.[0-9_]+(?:[eE][-+][0-9]+)?
        |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
        |[-+]?\\.(?:inf|Inf|INF)
        |\\.(?:nan|NaN|NAN))$''', re.X),
        list(u'-+0123456789.'))

    with open(filename, 'r') as f:
        mydict = yaml.safe_load(f)

    if mydict is None:
        mydict = dict()

    # Replace 'None' and 'inf' values to match expectations
    for key, val in mydict.items():
        if val == "None":
            mydict[key] = None
        if val == "inf":
            mydict[key] = np.inf

    return mydict


def getset(arg):
    """
    Return a set object

    :type arg: None, str or list
    :param arg: argument to turn into a set
    :rtype: set
    :return: a set of the given argument
    """
    if not arg:
        return set()
    elif isinstance(arg, str):
        return set([arg])
    else:
        return set(arg)


def parse_null(dictionary):
    """
    Remove null, None or '' values from a dictionary

    :type dictionary: dict
    :param dictionary: dict of parameters to parse
    :rtype: dict
    :return: dictionary that has been sanitized of all null values
    """
    # Copy the dictionary to get around deleting keys while iterating
    parsed_dict = dict(dictionary)
    for key, item in dictionary.items():
        # Search for all None and "" items, ignore bools, 0's etc.
        if not item and isinstance(item, (type(None), str)):
            del parsed_dict[key]

    return parsed_dict


def loadtxt(filename):
    """
    Load scalar from text file
    """
    return float(np.loadtxt(filename))


def savetxt(filename, v):
    """
    Save scalar to text file
    """
    np.savetxt(filename, [v], '%11.6e')


def number_fid(fid, i=0):
    """
    Number a filename. Used to store old log files without overwriting them.
    Premise is, if you have a file e.g., called: output.txt
    This function would return incrementing filenames:
    output_000.txt, output_001.txt, output_002.txt, ouput_003.txt ...

    .. note::
        Replace statement is catch all so we assume that there is only one \
        instance of the file extension in the entire path.

    :type fid: str
    :param fid: path to the file that you want to increment
    :type i: int
    :param i: number to append to file id
    :rtype: str
    :return: filename with appended number. filename ONLY, will strip away
        the original path location
    """
    fid_only = os.path.basename(fid)
    ext = os.path.splitext(fid_only)[-1]  # e.g., .txt
    new_ext = f"_{i:0>3}{ext}"   # e.g., _000.txt
    new_fid = fid_only.replace(ext, new_ext)
    return new_fid


def nproc():
    """
    Get the number of processors available

    :rtype: int
    :return: number of processors
    """
    try:
        return _nproc_method1()
    except EnvironmentError:
        return _nproc_method2()


def _nproc_method1():
    """
    Used subprocess to determine the number of processeors available

    :rtype: int
    :return: number of processors
    """
    # Check if the command `nproc` works
    if not subprocess.getstatusoutput('nproc')[0] == 0:
        raise EnvironmentError

    num_proc = int(subprocess.getstatusoutput('nproc')[1])

    return num_proc


def _nproc_method2():
    """
    Get number of processors using /proc/cpuinfo

    Bryant: This doesnt work?

    :rtype: int
    :return: number of processors
    """
    if not os.path.exists('/proc/cpuinfo'):
        raise EnvironmentError

    stdout = subprocess.check_output(
        "cat /proc/cpuinfo | awk '/^processor/{print $3}'", shell=True)
    num_proc = len(stdout.split('\n'))

    return num_proc

