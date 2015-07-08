from unittest import TestCase
from unittest.mock import Mock, patch

from runtimes.java import JavaCompiler, JavaCompilerException


class BasicRunnerTest(TestCase):
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
