import os
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase, skipIf

try:
    from unittest import mock
except ImportError:
    import mock

from runtimes.runner import BasicRunner, chdir
from runtimes.java import JavaFactory, JavaCompiler, JavaCompilerException

isdarwin = (sys.platform == 'darwin')


class ContextManagerTestException(Exception):
    pass


class ContextManagerTests(TestCase):
    def test_chdir_exception(self):
        """
        Test correct behavior even if an exception occurs in the with block.
        """
        with mock.patch('runtimes.runner.os.chdir') as patched_chdir:
            with self.assertRaises(ContextManagerTestException):
                current_dir = os.getcwd()
                with chdir('/some/path'):
                    patched_chdir.assert_called_with('/some/path')
                    raise ContextManagerTestException
            patched_chdir.assert_called_with(current_dir)


class BasicRunnerTest(TestCase):
    # FIXME: $TMP on OS X has multiple symlinked locations
    @skipIf(isdarwin, "This test currently doesn't work on OS X.")
    def test_cwd(self):
        with TemporaryDirectory() as tmpdir:
            runner = BasicRunner()
            runner.cwd = tmpdir
            args = [sys.executable, '-c', 'import os; print(os.getcwd())']
            out, __, code = runner.run(args)
            self.assertEqual(code, 0)
            self.assertEqual(out.strip(), tmpdir)

    def test_timeout(self):
        runner = BasicRunner()
        runner.timeout = 0.01
        args = [sys.executable, '-c', 'while True: pass']
        __, __, code = runner.run(args)
        self.assertEqual(code, -9)

    def test_stdout(self):
        runner = BasicRunner()
        args = [sys.executable, '-c', 'print("inloop")']
        out, err, code = runner.run(args)
        self.assertEqual(out.strip(), 'inloop')
        self.assertEqual(err.strip(), '')
        self.assertEqual(code, 0)

    def test_stderr(self):
        runner = BasicRunner()
        args = [sys.executable, '-c', 'import sys; print("inloop", file=sys.stderr)']
        out, err, code = runner.run(args)
        self.assertEqual(out.strip(), '')
        self.assertEqual(err.strip(), 'inloop')
        self.assertEqual(code, 0)

    def test_code(self):
        runner = BasicRunner()
        args = [sys.executable, '-c', 'import sys; sys.exit(42)']
        __, __, code = runner.run(args)
        self.assertEqual(code, 42)

    @skipIf(isdarwin, "On OS X, os.environ is always initialized with some __* vars")
    def test_env_empty(self):
        runner = BasicRunner()
        args = [sys.executable, '-c', 'import os; print(len(os.environ))']
        out, __, __ = runner.run(args)
        self.assertEqual(out.strip(), '0')


class JavaFactoryTest(TestCase):
    def setUp(self):
        self.settings = mock.Mock()
        self.runner = mock.Mock()
        self.runner.run = mock.Mock()
        # normally expecting a class (see test_runner_instantiation), but here
        # we use a callable that returns our mocked runner
        self.settings.RUNTIME_RUNNER = lambda: self.runner
        self.settings.RUNTIMES = {
            'java': {
                'compiler': '/usr/bin/javac',
                'runtime': '/usr/bin/java',
                'runtime_opts': ['-Xmx64m', '-XX:+DisableExplicitGC'],
                'compiler_opts': ['-Xlint'],
                'policy_file': '/path/to/policy.file',
                'library_dir': '/path/to/library',
                'runtime_timeout': 15,
                'compile_timeout': 10,
            }
        }

    def test_runner_instantiation(self):
        self.settings.RUNTIME_RUNNER = BasicRunner
        factory = JavaFactory(self.settings)
        runner = factory.create_compiler().runner
        self.assertEqual(type(runner), BasicRunner)
        self.assertEqual(runner.timeout, 10)
        # ensure that 10 is not accidentially the default value
        self.assertEqual(BasicRunner().timeout, 5)

    def test_create_compiler(self):
        factory = JavaFactory(self.settings)
        compiler = factory.create_compiler()
        self.assertEqual(self.runner.timeout, 10)
        with mock.patch('runtimes.java.glob', return_value=['Test.java']):
            compiler.add_dir('.')
        compiler.run()
        self.runner.run.assert_called_with(
            ['/usr/bin/javac', '-cp', '/path/to/library/*', 'Test.java']
        )


class JavaCompilerTest(TestCase):
    def setUp(self):
        self.runner = mock.Mock()
        self.runner.run = mock.Mock()
        self.compiler = JavaCompiler()
        self.compiler.runner = self.runner
        with mock.patch('runtimes.java.glob', return_value=['Test.java']):
            self.compiler.add_dir('.')

    def assertCalledWith(self, *args, **kwargs):
        self.runner.run.assert_called_with(*args, **kwargs)

    def test_default_raises(self):
        with self.assertRaises(JavaCompilerException):
            JavaCompiler().run()

    def test_add_dir(self):
        self.compiler.run()
        self.assertCalledWith(['javac', 'Test.java'])

    def test_add_option(self):
        self.compiler.add_options(['-Xlint'])
        self.compiler.run()
        self.assertCalledWith(['javac', '-Xlint', 'Test.java'])

    def test_add_classpath(self):
        self.compiler.add_classpath('/test/path', wildcard=True)
        self.compiler.add_classpath('/another/path')
        self.compiler.run()
        self.assertCalledWith(['javac', '-cp', '/test/path/*:/another/path', 'Test.java'])

    def test_set_cmd(self):
        self.compiler.cmd = '/usr/bin/java'
        self.compiler.run()
        self.assertCalledWith(['/usr/bin/java', 'Test.java'])
