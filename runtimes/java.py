from glob import glob
from subprocess import check_output
from os.path import join


class JavaCompiler:
    def __init__(self):
        self.cmd = ['javac']
        self.classpath = ['.']
        self.dirs = []

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
