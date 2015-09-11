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

#### Prerequisites

1. First, ensure you have the [Git submodules ready](#vendor-submodules).

2. Install node, npm, grunt and its deps:

    * Ubuntu/Debian:

            sudo apt-get install nodejs npm
            sudo ln -s /usr/bin/nodejs /usr/local/bin/node
            sudo npm install -g coffee-script
            sudo npm install -g grunt-cli

    * Mac OS X, using Homebrew

            brew install node
            npm install -g grunt-cli

3. Install the dependencies listed in our `package.json`. Don't `sudo` here!

        cd inloop/static
        npm install


#### Building it

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
