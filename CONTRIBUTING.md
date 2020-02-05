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
  * New code should use modern JavaScript, a.k.a. _ECMAScript 2015_ or _ES6_.
    * Start JS files with `"use strict";`.
    * Write classes with the `class` syntax.
    * Prefer `let` over `var`, use `const` whenever possible.
    * Use arrow function expressions where appropriate.
  * Use the new APIs: Promise API, Fetch API, etc.
  * Avoid deep nesting.
  * Avoid polluting the global namespace (`window`).
  * Avoid inline scripts (i.e., inside `<script>` tags).
  * Don't use jQuery if there's an easy JS-native way to do it.
  * Docstrings must follow the [JSDoc documentation specifications][jsdoc].


### Commit messages

Rules (courtesy of [Chris Beams][good-commits1]):

1. Separate subject from body with a blank line
2. Limit the subject line to 50 characters
3. Capitalize the subject line
4. Do not end the subject line with a period
5. Use the imperative mood in the subject line
6. Wrap the body at 72 characters
7. Use the body to explain _what_ and _why_ (not _how_)

Model message (based on [Tim Pope's][good-commits2]):

    Capitalized, short (50 chars or less) summary

    More detailed explanatory text, if necessary.  Wrap it to about 72
    characters or so.  In some contexts, the first line is treated as the
    subject of an email and the rest of the text as the body.  The blank
    line separating the summary from the body is critical (unless you omit
    the body entirely); tools like rebase can get confused if you run the
    two together.

    - Bullet points are possible, too
    - Another bullet point

    Fixes: #123
    See also: #456, #789

For example, take a look at the following commits in our repo:

- https://github.com/st-tu-dresden/inloop/commit/8ec193045b69842894c43b1e956e8b900fbd8623
- https://github.com/st-tu-dresden/inloop/commit/c8ff40c207c8b7d101eaa084642bfe194dd6dd9b
- https://github.com/st-tu-dresden/inloop/commit/a808cc0422bffe621191d3166c597fcffd4886d2


[django-testing]: https://docs.djangoproject.com/en/stable/topics/testing/
[inloop-issues]: https://github.com/st-tu-dresden/inloop/issues
[pep8]: https://www.python.org/dev/peps/pep-0008/
[google-style]: https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
[gh-flow]: https://guides.github.com/introduction/flow/
[good-commits1]: http://chris.beams.io/posts/git-commit/
[good-commits2]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
[nu-validator]: https://validator.w3.org/nu/
[jsdoc]: https://devdocs.io/jsdoc/
