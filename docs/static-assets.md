## Working on static assets (CSS and Javascript)

The minified static asset bundles are part of the clone for convenience and
there is no need to build them *unless* you want to add custom styles or
Javascript.

We use several third-party LESS/CSS and Javascript frameworks which are
included as git submodules under the `vendor` directory. That means, the
first step is to run

    git submodule update --init

Our own LESS and Javascript source files reside in the `js` and `less`
directories. Everything is combined into one minified CSS and one minified
Javascript file in subdirectories of `inloop/core/static`. The combined
files are generated using the `Makefile` as follows:

    make assets

You may also run

    make watch

which will watch for changes in the source files and run `make assets`
as necessary. The `Makefile` depends on `nodejs` and `npm`.

