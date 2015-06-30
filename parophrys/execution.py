import abc
import types

from functools import wraps

from parophrys.executors import Executor


class ExecutableTree(object):
    def __init__(self):
        self.executors = []
        self.children = []
        self.stdout = False
        self.stderr = False

    def add_child(self, child, stdout=False, stderr=False):
        """Add a child node to the tree.

        Parameters:
          ExecutableTree child  - The node to add
          Boolean stdout        - Whether to link parent stdout to child stdin
          Boolean stderr        - Whether to link parent stderr to child stdin

        """
        if isinstance(child, ExecutableTree):
            child.stdout = stdout
            child.stderr = stderr
            if child not in self.children:
                self.children.append(child)
            return self
        else:
            raise TypeError('Attempting to add non-tree to tree!')

    def remove_child(self, child):
        """Remove a child node from the tree.

        Only takes action if the child parameter is the same object as an
        existing child.

        Parameters:
          ExecutableTree child  - the node to remove

        """
        if isinstance(child, ExecutableTree):
            if child in self.children:
                self.children.remove(child)
            return self
        else:
            raise TypeError('child parameter must be an ExecutableTree')

    def add_executors(self, *args):
        """Add executors to the tree node.

        Takes any number of parameters which are Executor objects and adds them
        to the list to get executed.

        """
        for executor in args:
            if isinstance(executor, Executor):
                if executor not in self.executors:
                    self.executors.append(executor)
            else:
                raise TypeError('Attempting to add non-Executor!')
        return self

    def remove_executors(self, *args):
        """Remove executors to the tree node.

        Takes any number of parameters which are Executor objects and removes
        each from the list to get executed only if it is the same object as an
        existing executor.

        """
        # We don't use 'in' or such because we need 'is' comparision, not '=='.
        for executor in args:
            if isinstance(executor, Executor):
                for x in self.executors:
                    if x is executor:
                        self.executors.remove(x)
            else:
                raise TypeError('Attempting to remove a non-Executor')
        return self


class ExecutableBundle(object):
    def __init__(self, tree_root, tree_leaf):
        if (isinstance(tree_root, ExecutableTree) and
            isinstance(tree_leaf, ExecutableTree)):
            self.executor = None
            self.tree_root = tree_root
            self.tree_leaf = tree_leaf
        else:
            raise TypeError('tree_root must be an ExecutableTree')

    @staticmethod
    def _metamethod(method):
        @wraps(method)
        def generated(self, *args, **kwargs):
            method(self.executor, *args, **kwargs)
            return self
        generated.__doc__ = method.__doc__
        return generated

    def _attach_executor(self, executor):
        if self.executor:
            self = self.pipe(stdout=False, stderr=False)
        if isinstance(executor, Executor):
            self.executor = executor
            for m in self.executor.metaproperties:
                if not getattr(self, m.__name__, False):
                    setattr(self, m.__name__,
                            types.MethodType(self._metamethod(m), self))
                else:
                    raise TypeError('Method {} already exists on {}'.format(
                        m, type(self)))
            return self
        else:
            raise TypeError('Cannot attach non-Executor')

    def pipe(self, stdout=True, stderr=False):
        """Set up input/output redirection between executors."""
        leaf = ExecutableTree()
        self.tree_leaf.add_executors(self.executor)
        self.tree_leaf.add_child(child=leaf, stdout=stdout, stderr=stderr)
        return ExecutableBundle(tree_root=self.tree_root, tree_leaf=leaf)

    def execute(self):
        """Build and run the entire execution stack.

        Note that this executes everything in the entire execution context, both
        above and below here.

        """
        pass

def _generate_executor_callable(cls):
    @wraps(cls)
    def create_executor(self, *args, **kwargs):
        try:
            self._attach_executor(cls(*args, **kwargs))
            return self
        except KeyError:
            raise TypeError('Missing required argument "cls"')
    create_executor.__doc__ = cls.__init__.__doc__
    return create_executor

for executor in Executor.__subclasses__():
    if not getattr(ExecutableBundle, executor.descriptor(), False):
        setattr(ExecutableBundle, executor.descriptor(),
                _generate_executor_callable(executor))
    else:
        raise TypeError('Attempting to redefine Executor method {}'.format(
            executor.descriptor()))


def exec_builder():
    """Get an object for execution building."""
    tree = ExecutableTree()
    return ExecutableBundle(tree, tree)
