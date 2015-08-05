module.exports = (grunt) ->
  # Project configuration
  grunt.initConfig
    clean:
      dist: "dist"


    copy:
      bootstrap:
        files: [
          expand: true
          cwd: "vendor/bootstrap/dist/"
          src: [
            "js/*.min.js"
            "fonts/*"
          ]
          dest: "dist/"
        ]
      jquery:
        files: [
          expand: true
          cwd: "vendor/jquery/dist/"
          src: "*.min.js"
          dest: "dist/js/"
        ]
      images:
        files: [
          expand: true
          cwd: "src/images/"
          src: "**/*"
          dest: "dist/images/"
        ]


    concat:
      options:
        separator: ";\n"
      ace:
        src: [
          "vendor/ace/src/ace.js"
          "vendor/ace/src/mode-java.js"
          "vendor/ace/src/keybinding-*.js"
        ]
        dest: "dist/js/ace.js"
      inloopJs:
        src: [
          "vendor/prism/prism.js"
          "vendor/prism/components/prism-java.js"
          "vendor/prism/components/prism-bash.js"
          "vendor/prism/components/prism-python.js"
          "vendor/anchorjs/anchor.js"
          "src/js/anchors.js"
        ]
        dest: "dist/js/inloop.js"


    less:
      options:
        paths: [
          "src/less"
          "vendor/bootstrap/less"
        ]
      inloopCss:
        src: "src/less/inloop.less"
        dest: "dist/css/inloop.css"


    cssmin:
      options:
        compatibility: "ie8"
        keepSpecialComments: "*"
        sourceMap: true
        advanced: false
      inloopCss:
        src: "<%= less.inloopCss.dest %>"
        dest: "dist/css/inloop.min.css"


    uglify:
      options:
        preserveComments: "some"
        mangle: false
        sourceMap: true
      ace:
        src: "<%= concat.ace.dest %>"
        dest: "dist/js/ace.min.js"
      inloopJs:
        # TODO: preserve the prism.js copyright notice
        src: "<%= concat.inloopJs.dest %>"
        dest: "dist/js/inloop.min.js"


  # Grunt plugins
  grunt.loadNpmTasks "grunt-contrib-clean"
  grunt.loadNpmTasks "grunt-contrib-concat"
  grunt.loadNpmTasks "grunt-contrib-copy"
  grunt.loadNpmTasks "grunt-contrib-cssmin"
  grunt.loadNpmTasks "grunt-contrib-less"
  grunt.loadNpmTasks "grunt-contrib-uglify"


  grunt.registerTask "make-css", ["less", "cssmin"]
  grunt.registerTask "make-js", ["concat", "uglify"]

  # Run everything except clean by default
  grunt.registerTask "default", ["copy", "make-css", "make-js"]

# vim:et st=2 sts=2 sw=2
