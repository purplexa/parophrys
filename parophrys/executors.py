import abc
import copy

from functools import wraps


def metaproperty(function):
    function.is_metaproperty = True
    return function


class Executor(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        self._metadata = []
        for name, method in self.__dict__.iteritems():
            if hasattr(method, 'is_metaproperty'):
                self._metadata.append()

    @property
    def metaproperties(self):
        """Return a list of metaproperties for this object."""
        return self._metadata

    @abc.abstractmethod
    def execute(self, stdin=None):
        """Perform the action the Executor defines.

        This should be an instance method, and should return a tuple with the
        stdout filehandle, the stderr filehandle, and a context object.

        """
        pass

    @abc.abstractmethod
    def descriptor():
        """Return a string representing a descriptor for the Executor.

        This should be a static method.

        """
        pass


class SSHCommand(Executor):
    def __init__(self, command, *args, **kwargs):
        """Run a shell command on the specified hosts.

        Arguments:

          command   - The shell command to execute. May be a string or a
                      sequence of program arguments, similar to subprocess.call

        Supports the following metadata properties:

          hosts     - A list of hosts to run one
          parallel  - A bool where True means run in parallel across hosts, and
                      False means run on one host at a time, sequentially

        """
        self._command = command
        self._parallel = True
        super(SSHCommand, self).__init__(*args, **kwargs)

    def __len__(self):
        return len(self.hosts)

    def execute(self, stdin=None):
        pass

    @staticmethod
    def descriptor():
        return 'command'

    @metaproperty
    def hosts(self, *args):
        self._hosts = args

    @metaproperty
    def parallel(self, parallel=True):
        self._parallel = parallel


class PythonFunction(Executor):
    def __init__(self, function, *args, **kwargs):
        """Execute a python function on the input.

        Arguments:

          function  - The python function to call. This should take a single
                      argument, the stdin filehandle, and output a tuple
                      consisting of a stdout filehandle, a stderr filehandles,
                      and a context object.

        """
        self._function = function
        super(PythonFunction, self).__init__(*args, **kwargs)

    def __len__(self):
        return float('inf')

    def __iter__(self):
        while True:
            yield copy.copy(self)

    def execute(self, stdin=None):
        return function(stdin)

    def multiplex(self):
        while True:
            yield copy.copy(self)

    @staticmethod
    def descriptor():
        return 'pyfunc'
