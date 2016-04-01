Thanks for your interest in contributing to our project.

## How to contribute to INLOOP

### Report bugs or suggest new features

INLOOP is made by humans and humans make mistakes. We encourage anyone to open issues in
our [issue tracker][inloop-issues]. Bug reports should clearly describe the problem and
include a step by step description on how to reliably reproduce the problem.


### Submit pull requests

This is the **preferred way of contributing**. We also use this approach (aka the
[Github flow][gh-flow]) internally to peer review changes.

1. Fork off our repo and create a branch for the feature or bugfix. The branch name
   must be descriptive (e.g., `refactor-html`, `registration-tests`).
2. Add commits and be sure to follow our [rules for commit messages](#commit-messages).
   Don't mix unrelated changes into one commit.
3. Open a pull request so we can review the changes and give feedback.

It goes without saying, but you have to include [unit tests][django-testing], documentation
and follow our [coding conventions](#coding-conventions).


## Rules for contributing code

### Coding conventions

* In general, indent using 4 spaces instead of tabs (except for the `Makefile`) and use UNIX
  line endings.
* Python code must be formatted according to [PEP8][pep8] and a maximum line length of 99
  characters. [Install the pre-commit hook](#git-hooks) to automatically reject commits which
  violate these rules.
* HTML must be indented using 2 spaces. Don't use XML style empty tags (e.g., use `<br>`
  instead of `<br />`).


### Commit messages

We care about a [usable Git history][good-commits1] and are picky about [well-formed commit
messages][good-commits2]. Put as much effort into your commit messages as into your code,
other people will appreciate it.

Pull requests containing [unhelpful commit messages][ugly-commits] won't be accepted.


## Tools and helpers

### Git hooks

We provide the following commit hooks:

* `pre-commit`: enforces PEP8 coding convention
* `commit-msg`: enforces proper formatting of the Git commit messages
* `post-checkout`: synchronizes your virtualenv with the currently checked
  out `pip` requirements file

Our `Makefile` includes targets to install the above hooks into your working copy:

* `make hookup`: installs `pre-commit` and `commit-msg`
* `make hookup-all`: installs `pre-commit`, `commit-msg` and `post-checkout`


[django-testing]: https://docs.djangoproject.com/en/stable/topics/testing/
[inloop-issues]: https://github.com/st-tu-dresden/inloop/issues
[pep8]: https://www.python.org/dev/peps/pep-0008/
[gh-flow]: https://guides.github.com/introduction/flow/
[ugly-commits]: http://stopwritingramblingcommitmessages.com/
[good-commits1]: http://chris.beams.io/posts/git-commit/
[good-commits2]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
