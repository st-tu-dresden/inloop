Thanks for your interest in contributing to our project.

## How to contribute to INLOOP

### Report bugs or suggest new features

INLOOP is made by humans and humans make mistakes. We encourage anyone to open issues in
our [issue tracker][inloop-issues]. Bug reports should clearly describe the problem and
include a step by step description on how to reliably reproduce the problem.


### Submit pull requests

This is the **preferred way of contributing**. We also use this approach (aka the
[Github flow][gh-flow]) internally to peer review changes.

1. Fork our repo and create a branch for the feature or bugfix. The branch name should be
   descriptive and in _kebab case_, i.e., all lowercase with `-` separating words. It should
   begin with the GitHub issue number (if any). For example: `refactor-html`,
   `add-registration-tests` or `123-refactor-js-code`.
2. Add commits and be sure to follow our [rules for commit messages](#commit-messages).
   Don't mix unrelated changes into one commit.
3. Open a pull request so we can review the changes and give feedback. Additionally,
   our Travis CI will check if the test suite succeeds.

New code needs to include [unit tests][django-testing], documentation and must follow our [coding
conventions](#coding-conventions).


### Git setup

If not done already, configure your real name and email:

    git config --global user.name "John Doe"
    git config --global user.email johndoe@example.com

Apply the following configuration to your local Git clone of INLOOP:

    git config merge.ff false
    git config pull.rebase true


## Python dependency upgrades

This project uses `pipenv` to manage Python dependencies. The tool reads and saves
requirements from and to `Pipfile` and `Pipfile.lock` files.

* You can check the currently pinned dependency versions (in `Pipfile.lock`) for known
  security vulnerabilities using `pipenv check`.
* Other than that, you can use `pip` to check for outdated versions in general with
  `pipenv run pip list -o`.
* Use `pipenv update --dev` to update all dependencies. Afterwards, commit the updated
  `Pipfile.lock` (and `Pipfile`, if changed) to the Git repository. (Please do not mix
  changes unrelated to the upgrade into the commit.)


## Rules for contributing code

### Size your PRs

Do one thing at a time and don't bite off more than you can chew. Long living branches are
usually a sign that a feature needs to be split up. Furthermore, chances are high that such a
branch will be hard to integrate into `master`. Divide and conquer!


### Coding conventions

* Use an editor that understands our [.editorconfig](.editorconfig) file. This ensures all
  contributions conform to the same indentation style, maximum line length, encoding etc.
* All languages – write code that's easy to read:
  * Keep functions/methods small (ideally half a screen page). Split if necessary.
  * Separate data from code as much as possible.
  * Document _what_ your code does in doc comments (not _how_ it does something).
* Python:
  * Use Python 3.
  * Code must be formatted according to [PEP8][pep8] and a maximum line length of 99 characters.
  * Don't use relative imports.
  * Use single quoted string literals preferably (good: `'some string'`), unless the string contains
    a single quote itself (good: `"a hard day's night"`, bad: `'a hard day\'s night'`).
  * Docstrings must follow the [Google Python Style Guide for Comments][google-style] and be
    surrounded by three double quotes (`"""`). Don't use reStructured Text style comments.
* HTML (Django templates):
  * Don't use XML style empty tags (good: `<br>`, bad: `<br />`).
  * Use the [W3C Nu validator][nu-validator] to verify that the output of processed templates is
    valid HTML5.
* JavaScript:
  * Avoid inline scripts (i.e., inside `<script>` tags).
  * Docstrings must follow the [JSDoc documentation specifications][jsdoc].



### Commit messages

We care about a [usable Git history][good-commits1] and are picky about [well-formed commit
messages][good-commits2]. Put as much effort into your commit messages as into your code,
other people will appreciate it.

Pull requests containing [unhelpful commit messages][ugly-commits] won't be accepted.



[django-testing]: https://docs.djangoproject.com/en/stable/topics/testing/
[inloop-issues]: https://github.com/st-tu-dresden/inloop/issues
[pep8]: https://www.python.org/dev/peps/pep-0008/
[google-style]: https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
[gh-flow]: https://guides.github.com/introduction/flow/
[ugly-commits]: http://stopwritingramblingcommitmessages.com/
[good-commits1]: http://chris.beams.io/posts/git-commit/
[good-commits2]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
[nu-validator]: https://validator.w3.org/nu/
[jsdoc]: https://devdocs.io/jsdoc/
