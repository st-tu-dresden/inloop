## INLOOP static files HOWTO

TL;DR: you **don't** have to follow this guide, if:

- you just want to try out INLOOP
- you want to deploy INLOOP
- if you don't want to make changes to the layout

Otherwise, please read on.


### Notes on the directory layout

- The `src` directory contains the source files for the static assets
- The `dist` directory contains all generated assets as a *convenience*, so an
  ordinary deploy doesn't have to install all the `grunt` deps. This is also
  the directory to which the Django setting `STATICFILES_DIRS` points.
- The `vendor` directory contains git submodules of CSS and Javascript libraries
  INLOOP depends on. Git submodules provide a nice way of tracking progress of
  external projects.


### Static asset generation with `grunt`

If you want to make changes to the layout (and therefore, files in `src`), you
need to regenerate the `dist` files with [grunt][], which depends on [node][].

First, ensure you have the [Git submodules ready](#vendor-submodules).

Then, if you haven't already done so, install `grunt`:

```bash
# Install node on Ubuntu/Debian
sudo apt-get install nodejs
sudo apt-get install npm

# ... on OS X
brew install node

# Install grunt globally (may need sudo)
npm install -g grunt-cli

# Install dependencies needed in our Gruntfile. This will create a
# node_modules directory (which is git-ignored).
cd inloop/static
npm install
```

The assets can be built by executing

    grunt

in `inloop/static`. The default `grunt` target does everything what's needed.
See the `Gruntfile` for more details what happens under the hood.


### Vendor submodules

There are several methods to checkout the submodules:

 - in an existing git clone, use `git submodule update --init`
 - when doing a fresh clone of INLOOP, use `git clone` with `--recursive`

To update a submodule to a newer version (read: commit), use

```bash
# chdir to the submodule and fetch updates:
cd static/vendor/jquery
git fetch

# ALWAYS checkout a release tag, don't just checkout master!
git checkout v2.1.4

# chdir back to the project dir and commit:
cd ../../..
git commit -m "Update jquery submodule to v2.1.4"
```

[grunt]: http://gruntjs.com
[node]: https://nodejs.org
