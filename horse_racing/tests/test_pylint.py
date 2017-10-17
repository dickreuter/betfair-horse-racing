""" test cases pylint """

import logging
import os
import unittest

from pylint import lint
from pylint.reporters.text import ParseableTextReporter

from horse_racing.utils.tools import get_dir
import warnings

log = logging.getLogger(__name__)


_pylint_warnings_as_errors = [
    'cyclic-import'
]
#     'missing-docstring',
''' this is a list of pylint warnings which the 
test checks the mre source code for and reports as errors.'''


class _WritableOutput(object):
    '''a simple class, supporting a write method to
    capture pylint output'''

    def __init__(self):
        self.content = []

    def write(self, string):
        ''' write method to capture pylint output.'''
        if string == '\n':
            return  # filter newlines
        self.content.append(string)


class PyLintTest(unittest.TestCase):
    ''' horse_racing unit test class for pylinting code'''
    _respositories = ['']

    def _get_sourcereps(self):
        '''returns a (pylint rcfile, all source *.py) tuple of files.'''
        codebase = get_dir('codebase')
        return (os.path.join(codebase, 'tests/.pylintrc'),
                [os.path.join(codebase, rep) for rep in self._respositories])

    def _pyfiles(self):
        '''returns all mre python source files.'''
        codebase = get_dir('codebase')
        pyfiles = []
        for rep in self._respositories:
            for dirpath, _, files in os.walk(os.path.join(codebase, rep)):
                pyfiles.extend([os.path.join(dirpath, x)
                                for x in files if x.endswith('.py')])
        return pyfiles

    def _run_pylint(self, pylint_args):
        '''runs pylint with supplied args, returns '''

        pylint_output = _WritableOutput()
        pylint_reporter = ParseableTextReporter(pylint_output)
        lint.Run(pylint_args, reporter=pylint_reporter, exit=False)
        return pylint_output.content

    def test_pylint_warnings_as_errors(self):
        '''test to raise pylint warnings as errors'''
        warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
        warnings.filterwarnings("ignore", category=ImportWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        rcfile, reps = self._get_sourcereps()

        pylint_args = ['--rcfile={}'.format(rcfile),
                       '--reports=n',
                       '--disable=all',
                       '--enable={}'.format(','.join(_pylint_warnings_as_errors)),
                       ]

        log.info('applying pylint to repository {}'.format(reps))

        pylint_args += reps
        pylint_output = self._run_pylint(pylint_args)

        errors = []
        for l in pylint_output:
            for err in _pylint_warnings_as_errors:
                if err in l:
                    errors.append(l)

        if errors:
            print('\npylint warnings as errors found \n\n')
            [print(err) for err in errors]
            self.fail()

    def test_pylint_errors(self):
        '''test pylint errors'''
        warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
        warnings.filterwarnings("ignore", category=ImportWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        rcfile, reps = self._get_sourcereps()

        pylint_args = ['--rcfile={}'.format(rcfile),
                       '--errors-only'
                       ]

        log.info('applying pylint to repository {}'.format(reps))

        pylint_args += reps
        pylint_output = self._run_pylint(pylint_args)

        has_errors = False
        for l in pylint_output:
            if ': [E' in l:
                has_errors = True
                print(l)

        if has_errors:
            print('\npylint errors found \n\n')
            self.fail()

        return
