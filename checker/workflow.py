from runtimes.java import JavaFactory


def compile_java(ctx):
    """Foo bar baz
    """
    factory = JavaFactory()
    compiler = factory.create_compiler()
    compiler.add_dir(ctx.get_solution_dir(), exclude="blub")
    compiler.add_to_classpath(ctx.get_tests_dir())
    out, err, code = compiler.run()
    ctx.set_compiler_output(out, err, code)
    return code == 0


def java_workflow(ctx):
    flow = Workflow(ctx)
    flow.add(WorkflowElement(compile_java))
    flow.add(WorkflowElement('junit'))
    flow.add(WorkflowElement('findbugs', is_optional=True))
    return flow


class WorkflowException(Exception):
    pass


class WorkflowContext:
    def set_findbugs_output(self):
        pass


class Workflow:
    def __init__(self, ctx):
        self.ctx = ctx
        self.elements = []

    def add(self, element):
        self.elements.append(element)

    def run(self):
        try:
            for element in self.elements:
                element.run(self.ctx)
        except WorkflowException:
            return False
        return True


class WorkflowElement:
    def __init__(self, function, is_optional=False):
        self.function = function
        self.is_optional = is_optional

    def run(self, ctx):
        success = self.function(ctx)
        if not self.is_optional and not success:
            raise WorkflowException
