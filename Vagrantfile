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

  # Install required Ubuntu packages and adjust the timezone
  config.vm.provision :shell, privileged: true, inline: <<-EOF
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends \
      build-essential git libjpeg-dev libpq-dev nginx openjdk-7-jre-headless \
      postgresql-9.1 pigz python3.4 python3.4-dev python3.4-venv redis-server \
      zlib1g-dev

    echo "Europe/Berlin" >/etc/timezone
    dpkg-reconfigure tzdata
  EOF

  # Add the deadsnakes Python as /usr/bin/python3
  config.vm.provision :shell, privileged: true, inline: <<-EOF
    update-alternatives \
      --install /usr/bin/python3 python3 /usr/bin/python3.4 1 \
      --slave /usr/bin/pyvenv pyvenv /usr/bin/pyvenv-3.4
  EOF

  # Self-signed certificate for integration tests
  config.vm.provision :shell, privileged: true, inline: <<-EOF
    openssl req -newkey rsa:2048 -x509 -days 365 -nodes -sha256 -subj "/CN=$(hostname)/C=DE/" \
      -out /etc/ssl/certs/inloop.pem -keyout /etc/ssl/private/inloop.key >~/openssl.log 2>&1
    if [ $? -eq 0 ]; then
      chmod 600 /etc/ssl/private/inloop.key
      rm -f ~/openssl.log
    else
      echo "OpenSSL certificate creation failed, see $HOME/openssl.log" >&2
      exit 1
    fi
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
