from glob import glob
from subprocess import check_output
from os.path import join


# XXX: docstrings
# XXX: default values?
class JavaFactory:
    def __init__(self, settings, runtime='java'):
        self.runner = settings.RUNTIME_RUNNER
        self.runtime = settings.RUNTIMES[runtime]

    def create_compiler(self):
        compiler = JavaCompiler()
        compiler.use_runner(self.runner)
        compiler.add_to_classpath(self.runtime['JAVA_LIBRARY_DIRS'])
        # ...
        return compiler

    def create_runtime(self):
        pass

    def create_junit(self):
        pass

    def create_findbugs(self):
        pass

    # etc.


class JavaCompiler:
    def __init__(self):
        self.cmd = ['javac']
        self.classpath = ['.']
        self.dirs = []

    def use_runner(self, runner):
        pass

    def add_to_classpath(self, entry):
        self.classpath += entry

    def add_dir(self, dir):
        self.dirs += dir

    def _get_java_files(self):
        files = []
        for d in self.dirs:
            files += glob(join(d, '*.java'))
        return files

    def execute(self, cwd=None):
        cmd = self.cmd + ['-cp', ':'.join(self.classpath)] + self._get_java_files()
        return check_output(cmd, cwd=cwd)
