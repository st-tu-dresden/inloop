from glob import glob
from os import path


# XXX: docstrings
# XXX: default values?
class JavaFactory:
    def __init__(self, settings, runtime='java'):
        self.runner = settings.RUNTIME_RUNNER
        self.runtime = settings.RUNTIMES[runtime]

    def create_compiler(self):
        compiler = JavaCompiler()
        compiler.set_runner(self.runner())
        compiler.add_classpath(self.runtime['library_dir'])
        # ...
        return compiler

    def create_runtime(self):
        pass

    def create_junit(self):
        pass

    def create_findbugs(self):
        pass

    # etc.

JAVAC_DEFAULT = 'javac'


class JavaCompilerException(Exception):
    pass


class JavaCompiler:
    def __init__(self):
        self.cmd = JAVAC_DEFAULT
        self.options = []
        self.classpath = []
        self.files = []
        self.runner = None

    def set_runner(self, runner):
        self.runner = runner

    def set_cmd(self, cmd):
        self.cmd = cmd

    def add_classpath(self, entry, wildcard=False):
        if wildcard:
            self.classpath.append(path.join(entry, '*'))
        else:
            self.classpath.append(entry)

    def add_dir(self, directory):
        filenames = glob(path.join(directory, '*.java'))
        self.files.extend(filenames)

    def add_options(self, options):
        self.options.extend(options)

    def run(self):
        if not self.files:
            raise JavaCompilerException('No java files given for compilation')
        args = [self.cmd]
        if self.classpath:
            args.append('-cp')
            args.append(':'.join(self.classpath))
        args.extend(self.files)
        self.runner.run(args)
