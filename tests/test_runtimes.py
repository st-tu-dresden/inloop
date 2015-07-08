import sys
from tempfile import TemporaryDirectory
from unittest import TestCase, skipIf
from unittest.mock import Mock, patch

from runtimes.runner import BasicRunner
from runtimes.java import JavaCompiler, JavaCompilerException

isdarwin = (sys.platform == 'darwin')


class BasicRunnerTest(TestCase):
    # FIXME: $TMP on OS X has multiple symlinked locations
    @skipIf(isdarwin, "This test currently doesn't work on OS X.")
    def test_cwd(self):
        with TemporaryDirectory() as tmpdir:
            runner = BasicRunner(cwd=tmpdir)
            args = [sys.executable, '-c', 'import os; print(os.getcwd())']
            out, __, code = runner.run(args)
            self.assertEqual(code, 0)
            self.assertEqual(out.strip(), tmpdir)

    def test_timeout(self):
        runner = BasicRunner(timeout=0.01)
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


class JavaFactoryTest(TestCase):
    def test_settings_are_used(self):
        pass


class JavaCompilerTest(TestCase):
    def setUp(self):
        self.runner = Mock()
        self.runner.run = Mock()
        self.compiler = JavaCompiler()
        self.compiler.set_runner(self.runner)
        with patch('runtimes.java.glob', return_value=['Test.java']):
            self.compiler.add_dir('.')

    def assertCalledWith(self, *args, **kwargs):
        self.runner.run.assert_called_with(*args, **kwargs)

    def test_default_raises(self):
        with self.assertRaises(JavaCompilerException):
            JavaCompiler().run()

    def test_add_dir(self):
        self.compiler.run()
        self.assertCalledWith(['javac', 'Test.java'])

    def test_add_classpath(self):
        self.compiler.add_classpath('/test/path', wildcard=True)
        self.compiler.add_classpath('/another/path')
        self.compiler.run()
        self.assertCalledWith(['javac', '-cp', '/test/path/*:/another/path', 'Test.java'])

    def test_set_cmd(self):
        self.compiler.set_cmd('/usr/bin/java')
        self.compiler.run()
        self.assertCalledWith(['/usr/bin/java', 'Test.java'])
