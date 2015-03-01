## Hacking

### Automatic Code Checking
It is recommended for all developers to implement this pre-commit hook mechanism to check their code before every commit. In case the implemented linter and PEP8 style checker throw any errors, the committing process is canceled and the errors are shown for correction.

The project comes with its own pre-commit hook labeled *pre-commit.sh* in the root directory. To install it, simply clone the repository, navigate to the project root directory and issue the following commands:
```bash
ln -s -f ../../pre-commit.sh .git/hooks/pre-commit
```
This will create a symlink to the hooks in your .git directory which are called once the commit is issued.

**Note:** The `-f` option *forces* an overwrite of the previously exsiting file, meaning that the original file contents in `.git/hooks/pre-commit` are lost. Create a backup copy if you don't want to lose your changes. By default, the file is empty.

For the hook to grab, you still have to make the custom hook executable:
```bash
chmod +x pre-commit.sh
```

### Compatibility
For pre-commit checking [flake8](http://flake8.readthedocs.org/en/latest/index.html) is used. It implements wrappers for [pep8](https://pypi.python.org/pypi/pep8), the [pyflakes](https://pypi.python.org/pypi/pyflakes) linter and [mccabe](https://pypi.python.org/pypi/mccabe). The parameters for the hook are contained in [setup.cfg](https://github.com/st-tu-dresden/tud_praktomat_neu/blob/master/setup.cfg) under the `[flake8]` section.

The pre-defined command `flake8 --install-hook` is also a  means of installing the pre-commit hook as it is now, but allows less customization and more importantly lacks support for virtualenv in IDEs. The mechanism works when executed from the shell but most IDEs can't execute the git hooks within their virtualenv.
