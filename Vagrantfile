# -*- mode: ruby -*-
# vim:ft=ruby sts=2 ts=2 sw=2 et

Vagrant.configure(2) do |config|
  config.vm.define "precise"
  config.vm.box = "ubuntu/precise64"
  config.vm.hostname = "precise"

  # Prevent Vagrant from auto-checking the version. This slows down the integration tests.
  config.vm.box_check_update = false

  # Setup third party package repositories
  config.vm.provision :shell, privileged: true, inline: <<-EOF
    set -e

    apt_dir=/etc/apt/sources.list.d
    echo "deb http://ppa.launchpad.net/fkrull/deadsnakes/ubuntu precise main" >$apt_dir/python.list
    echo "deb http://nginx.org/packages/ubuntu/ precise nginx"                >$apt_dir/nginx.list

    apt-key adv --keyserver keyserver.ubuntu.com --recv-key 7BD9BF62
    apt-key adv --keyserver keyserver.ubuntu.com --recv-key DB82666C
  EOF

  # Install required Ubuntu packages
  config.vm.provision :shell, privileged: true, inline: <<-EOF
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends \
      build-essential libjpeg-dev libpq-dev nginx openjdk-7-jre-headless \
      postgresql-9.1 python3.4 python3.4-dev redis-server zlib1g-dev
  EOF

  # Initialize the virtualenv (on Python 3.4, we can use the bundled pyvenv) and
  # ensure the newest pip and setuptools are installed
  config.vm.provision :shell, privileged: false, inline: <<-EOF
    set -e

    rm -rf ~/virtualenv
    pyvenv-3.4 ~/virtualenv
    echo "source ~/virtualenv/bin/activate" >> ~/.bashrc

    ~/virtualenv/bin/pip install -U pip setuptools
  EOF
end
