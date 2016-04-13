from __future__ import print_function
"""
pie - Python Interactive Executor
Enables a user to execute predefined tasks that may accept parameters and options from the command line without any other required packages.
Great for bootstrapping a development environment, and then interacting with it.
"""
__VERSION__='0.0.2'


import inspect
import os
import re
import subprocess
import sys
import types
from functools import wraps


__all__=['task','options','cmd','pip','venv']


# environment constants
WINDOWS=(os.name=='nt')
PY3=(sys.version_info>=(3,0))

# function for input (also so that we can mock it tests)
INPUT_FN=input if PY3 else raw_input
# function to execute a command - must emulate the subprocess call method
CMD_FN=subprocess.call



# ----------------------------------------
# configuration
# ----------------------------------------
class Lookup(object):
    """
    A class that can be used like a dictionary with more succinct syntax:
        l=Lookup(name='example',value='good')
        print(l.name)
        l.newValue=2
    """
    def __init__(self,**entries):
        self.__dict__.update(entries)


# options is a lookup object where predefined options (in code) can be placed, as well as provided on the command line.
options=Lookup()



# ----------------------------------------
# tasks
# ----------------------------------------
# tasks is a dictionary of registered tasks, where key=name. Tasks are possibly from within submodules where name=module.task.
tasks={}


class TaskWrapper(object):
    """
    A callable wrapper around a task function. Provides prompting for missing function arguments.
    """
    def __init__(self,fn,params):
        self.fn=fn
        self.params=params
        self.desc=fn.__doc__

    def __call__(self,*args,**kwargs):
        # args might be a tuple, but we want to append to it
        args=list(args)
        # go through parameters and make sure we have arguments for each, otherwise inject or prompt for them
        for i,p in enumerate(self.params):
            if len(args)<=i:
                # TODO: use a default value if provided - would be best to use the default value as provided with the function definition, rather than add a 'default' key in parameters dicts.
                # prompt for a missing argument
                promptStr=p['prompt'] if 'prompt' in p else 'Please enter a value for {}: '.format(p['name'])
                v=INPUT_FN(promptStr)
                args.append(v)
            # and apply the conversionFn
            if 'conversionFn' in p: args[i]=p['conversionFn'](args[i])
        return self.fn(*args,**kwargs)


def task(parameters=[]):
    """
    A (function that returns a) decorator that converts a simple Python function into a pie Task.
     - parameters is a list of objects (use Lookup) with the following attributes:
         name - name of the parameter
         conversionFn - a function that will take a string and convert it to the desired type
    """
    def decorator(taskFn):
        # convert the function into a callable task instance
        return TaskWrapper(taskFn,parameters)

    # check in case we were called as a decorator eg. @task (without the function call)
    if callable(parameters):
        # this means that parameters is actually the function to decorate
        taskFn=parameters
        # but parameters is used in the wrapper and assumed to be a list, so set it as an empty list (as we weren't provided any parameters)
        parameters=[]
        return decorator(taskFn)

    # otherwise return the decorator function
    return decorator


alreadyTraversed=set()
def registerTasksInModule(modulePath,module):
    """Recursively traverse through modules, registering tasks"""
    modulePrefix=(modulePath+'.' if modulePath else '')
    for k,v in vars(module).items():
        if isinstance(v,TaskWrapper):
            tasks[modulePrefix+k]=v
        elif isinstance(v,types.ModuleType):
            # there is a situation where a module in a package that is imported into another module (so, doubly nested tasks) will also show up at the package level, even though it's not imported there
            # eg. pie_tasks/__init__.py does "from . import submodule", submodule does "from . import doubleNest", but this also causes doubleNest to show up in pie_tasks
            # I can't figure out any way to distinguish the difference, but, at the moment, I think it's an obscure enough situation to not worry about yet
            # Actually, we have to keep a list of modules we've traversed so that we don't recurse forever (circular imports), this will remove the above problem, but may not fix it correctly...
            if v not in alreadyTraversed:
                alreadyTraversed.add(v)
                registerTasksInModule(modulePrefix+k,v)


def importTasks(moduleName='pie_tasks'):
    """Import the pie_tasks module and register all tasks found"""
    try:
        m=__import__(moduleName)
    except ImportError:
        return False
    registerTasksInModule('',m)
    return True



# ----------------------------------------
# operations
# ----------------------------------------
class CmdContextManager(object):
    """
    The CmdContextManager (singleton) is used to keep track of what context a command is being executed within:

        with venv('venv/build'):
            cmd('python -m pip')
    """
    context=[]

    @classmethod
    def enter(cls,ctx):
        cls.context.append(ctx)
        return len(cls.context)-1

    @classmethod
    def cmd(cls,c,i=None):
        if i is None: i=len(cls.context)
        if i>0: return cls.context[i-1].cmd(c)
        CMD_FN(c,shell=True)

    @classmethod
    def exit(cls):
        cls.context.pop()


def cmd(c):
    """Executes a system command (within the current context)"""
    return CmdContextManager.cmd(c)


def pip(c,pythonCmd='python'):
    """Runs a pip command"""
    cmd('{} -m pip {}'.format(pythonCmd,c))


class CmdContext(object):
    """Base class for all cmd context objects."""
    # make this a context manager
    def __enter__(self):
        self.contextPosition=CmdContextManager.enter(self)
        return self

    def __exit__(self,exc_type,exc_value,traceback):
        CmdContextManager.exit()
        # we don't care about an exception


class venv(CmdContext):
    """
    A context class used to execute commands within a virtualenv
    """
    def __init__(self,path):
        self.path=path

    def create(self,extraArguments=''):
        if PY3:
            c=r'python -m venv {} {}'.format(extraArguments,self.path)
        else:
            c=r'python -m virtualenv {} {}'.format(extraArguments,self.path)
        cmd(c)

    def cmd(self,c):
        if WINDOWS:
            c=r'cmd /c "{}\Scripts\activate.bat && {}"'.format(self.path,c)
        else:
            c=r'bash -c "{}/bin/activate && {}"'.format(self.path,c)
        return CmdContextManager.cmd(c,self.contextPosition)



# ----------------------------------------
# Command line functionality
# ----------------------------------------
class Argument(object):
    # a flag to indicate that tasks must be imported to execute this argument
    needsTasksImported=False

    def execute(self):
        raise NotImplemented()

    def __repr__(self):
        return self.__class__.__name__


class Version(Argument):
    def execute(self):
        print('pie v{}'.format(__VERSION__))

    def __repr__(self):
        return 'Version: {}'.format(__VERSION__)


class CreateBatchFile(Argument):
    def execute(self):
        pythonExe=sys.executable
        if WINDOWS:
            with open('pie.bat','w') as fout:
                fout.write('@echo off\n"{}" -m pie %*\n'.format(pythonExe))
        else:
            with open('pie','w') as fout:
                fout.write('"{}" -m pie %*\n'.format(pythonExe))


class ListTasks(Argument):
    needsTasksImported=True

    def __init__(self,includeDescription=True):
        self.includeDescription=includeDescription

    def execute(self):
        for k in sorted(tasks.keys()):
            v=tasks[k]
            if self.includeDescription:
                desc=v.desc or ''
                print('{:30} {:.70}'.format(k,desc.replace('\n',' ')))
            else:
                print(k)


class Help(Argument):
    def execute(self):
        print('Usage:    pie [ -v | -h | -b | -l | -L ]')
        print('          pie [ -o <name>=<value> | <task>[(<args>...)] ]...')
        print('Version:  v{}'.format(__VERSION__))
        print('')
        print('  -v      Display version')
        print('  -h      Display this help')
        print('  -b      Create batch file shortcut')
        print('  -l      List available tasks with description')
        print('  -L      List available tasks with name only')
        print('  -o      Sets an option with name to value')
        print('  <task>  Runs a task passing through arguments if required')
        print('')
        print('The order of -o and <task> options matters - each will be executed in the order given on the command line.')


class Option(Argument):
    def __init__(self,name,value):
        self.name=name
        self.value=value

    def execute(self):
        setattr(options,self.name,self.value)

    def __repr__(self):
        return 'Option: {}={}'.format(self.name,self.value)


class TaskCall(Argument):
    needsTasksImported=True

    class TaskNotFound(Exception):
        def __init__(self,name):
            self.name=name

    def __init__(self,name,args=[],kwargs={}):
        self.name=name
        self.args=args
        self.kwargs=kwargs

    def execute(self):
        if self.name in tasks: tasks[self.name](*self.args,**self.kwargs)
        else: raise self.TaskNotFound(self.name)

    def __repr__(self):
        return 'Task: {}(args={},kwargs={})'.format(self.name,self.args,self.kwargs)



# ----------------------------------------
# Command line parsing
# ----------------------------------------
TASK_RE=re.compile(r'(?P<name>[^()]+)(\((?P<args>.*)\))?')
def parseArguments(args):
    i=0
    parsed=[]
    while i<len(args):
        arg=args[i]
        if arg.startswith('-'):
            # although we say that these options are check that incompatible options aren't used together
            if arg=='-v':
                parsed.append(Version())
            elif arg=='-h':
                parsed.append(Help())
            elif arg=='-b':
                parsed.append(CreateBatchFile())
            elif arg=='-l':
                parsed.append(ListTasks())
            elif arg=='-L':
                parsed.append(ListTasks(includeDescription=False))
            elif arg=='-o':
                name,value=args[i+1].split('=')
                parsed.append(Option(name,value))
                i+=1
            else:
                raise Exception('Unknown argument: {}'.format(arg))
        else:
            mo=TASK_RE.match(arg)
            if mo:
                args=mo.group('args')
                args=args.split(',') if args else []
                # TODO: add further parsing to handle keyword arguments
                parsed.append(TaskCall(mo.group('name'),args=args,kwargs={}))
            else:
                raise Exception('Unknown task format: {}'.format(arg))
        i+=1
    return parsed



# ----------------------------------------
# entry point
# ----------------------------------------
def main(args):
    args=parseArguments(args)
    if args:
        tasksImported=False
        for a in args:
            # only import tasks if needed, saves exceptions when only looking for help or creating the batch file
            if a.needsTasksImported and not tasksImported:
                if not importTasks():
                    print('pie_tasks could not be found.')
                    break
                tasksImported=True
            # try to execute the arg
            try:
                a.execute()
            except TaskCall.TaskNotFound as e:
                print('Task {} could not be found.'.format(e.name))
                break
            # print(repr(a))
    else:
        Help().execute()


if __name__=='__main__':
    # import pie so that both we and any pie_tasks code that imports pie are referring to the same module variables
    import pie
    # skip the name of the command
    pie.main(sys.argv[1:])
