
import os
import subprocess

from os.path import abspath, basename, join

import numpy as np

from seisflows.tools import unix
from seisflows.tools.code import call, findpath, saveobj
from seisflows.tools.config import SeisflowsParameters, SeisflowsPaths, \
    ParameterError, custom_import
from seisflows.tools.msg import mpiError1, mpiError2, mpiError3

PAR = SeisflowsParameters()
PATH = SeisflowsPaths()


class mpi(custom_import('system', 'base')):
    """ An interface through which to submit workflows, run tasks in serial or 
      parallel, and perform other system functions.

      By hiding environment details behind a python interface layer, these 
      classes provide a consistent command set across different computing
      environments.

      For more informations, see 
      http://seisflows.readthedocs.org/en/latest/manual/manual.html#system-interfaces
    """

    def check(self):
        """ Checks parameters and paths
        """

        if 'TITLE' not in PAR:
            setattr(PAR, 'TITLE', basename(abspath('.')))

        if 'NTASK' not in PAR:
            setattr(PAR, 'NTASK', 1)

        if 'NPROC' not in PAR:
            setattr(PAR, 'NPROC', 1)

        if 'VERBOSE' not in PAR:
            setattr(PAR, 'VERBOSE', 1)

        if 'MPIARGS' not in PAR:
            setattr(PAR, 'MPIARGS', '--mca mpi_warn_on_fork 0')

        # check paths
        if 'SCRATCH' not in PATH:
            setattr(PATH, 'SCRATCH', join(abspath('.'), 'scratch'))

        if 'LOCAL' not in PATH:
            setattr(PATH, 'LOCAL', '')

        if 'SUBMIT' not in PATH:
            setattr(PATH, 'SUBMIT', abspath('.'))

        if 'OUTPUT' not in PATH:
            setattr(PATH, 'OUTPUT', join(PATH.SUBMIT, 'output'))

        self.check_mpi()


    def submit(self, workflow):
        """ Submits job
        """
        unix.mkdir(PATH.OUTPUT)
        unix.cd(PATH.OUTPUT)

        self.checkpoint()
        workflow.main()


    def run(self, classname, funcname, hosts='all', **kwargs):
        """ Runs tasks in serial or parallel on specified hosts
        """
        # to avoid cryptic MPI messages, use "--mca_warn_on_fork 0" as the
        # default value for MPIARGS, and use subprocess.call rather than 
        # call_catch to invoke mpiexec
        self.checkpoint()
        self.save_kwargs(classname, funcname, kwargs)

        if hosts == 'all':
            unix.cd(join(findpath('seisflows.system'), 'wrappers'))
            subprocess.call('mpiexec -n {} '.format(PAR.NTASK)
                    + PAR.MPIARGS + ' '
                    + 'run_mpi' + ' '
                    + PATH.OUTPUT + ' '
                    + classname + ' '
                    + funcname,
                    shell=True)

        elif hosts == 'head':
            unix.cd(join(findpath('seisflows.system'), 'wrappers'))
            subprocess.call('mpiexec -n 1 '
                    + PAR.MPIARGS + ' '
                    + 'run_mpi_head' + ' '
                    + PATH.OUTPUT + ' '
                    + classname + ' '
                    + funcname,
                    shell=True)

        else:
            raise(KeyError('Hosts parameter not set/recognized.'))


    def getnode(self):
        """Gets number of running task"""
        from mpi4py import MPI
        return MPI.COMM_WORLD.Get_rank()


    def mpiexec(self):
        """ MPI executable used to invoke solver
        """
        # an empty string invokes solver without mpi executable; presupposes 
        # that solver runs on a single core
        return ''

    def save_kwargs(self, classname, funcname, kwargs):
        kwargspath = join(PATH.OUTPUT, 'SeisflowsObjects', classname+'_kwargs')
        kwargsfile = join(kwargspath, funcname+'.p')
        unix.mkdir(kwargspath)
        saveobj(kwargsfile, kwargs)


    def check_mpi(self):
        """ Checks MPI dependencies
        """
        try:
            import mpi4py
        except ImportError:
            raise Exception(mpiError1 % PAR.SYSTEM)

        if PAR.NPROC > 1:
            raise Exception(mpiError2 % PAR.SYSTEM)

        #try:
        #    f = open('/dev/null', 'w')
        #    subprocess.check_call('which mpiexec', 
        #        shell=True,
        #        stdout='/dev/null')
        #except:
        #    raise Exception(mpiError3 % PAR.SYSTEM)
        #finally:
        #    f.close()
            
