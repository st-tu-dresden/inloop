def compile_java(ctx):
    compiler = ctx.factory.create_compiler()
    compiler.add_dir(ctx.solution_dir)
    compiler.add_classpath(ctx.tests_dir)
    outs, errs, code = compiler.run()
    ctx.compiler_output = (outs, errs, code)
    return code == 0


def java_workflow():
    flow = Workflow()
    flow.add(compile_java, optional=False)
    return flow


class Context:
    def __init__(self, factory=None, solution_dir=None, tests_dir=None):
        self.factory = factory
        self.solution_dir = solution_dir
        self.tests_dir = tests_dir


class Workflow:
    def __init__(self):
        self.callables = []

    def add(self, callable, optional=False):
        self.callables.append((callable, optional))

    def execute(self, ctx):
        for callable, optional in self.callables:
            if not callable(ctx) and not optional:
                return False
        return True
