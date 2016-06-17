# -*- mode: ruby -*-
# vim:ft=ruby sts=2 ts=2 sw=2 et

Vagrant.configure(2) do |config|
  config.vm.define :wily do |wily|
    wily.vm.box = "ubuntu/wily64"
  end

  # Setup Docker APT repository first, so we don't need to run `apt-get update` twice
  config.vm.provision :shell, privileged: true, inline: <<-EOF
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 \
        --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
    echo "deb https://apt.dockerproject.org/repo ubuntu-`lsb_release -cs` main" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get -y install docker-engine
    usermod -aG docker vagrant
  EOF

  # Install required base packages and adjust the timezone
  config.vm.provision :shell, privileged: true, inline: <<-EOF
    set -e
    export DEBIAN_FRONTEND=noninteractive

    # let's follow the DRY principle and extract the pkg list from our README
    grep "apt-get install" /vagrant/README.md | while read command; do
        yes | bash -c "$command"
    done

    echo "Europe/Berlin" >/etc/timezone
    dpkg-reconfigure tzdata
  EOF

  # Initialize the virtualenv, a git clone on ext4 and install requirements
  config.vm.provision :shell, privileged: false, inline: <<-EOF
    set -e
    if [ ! -d ~/virtualenv ]; then
      pyvenv ~/virtualenv
      echo "source ~/virtualenv/bin/activate" >> ~/.bashrc
    fi

    ~/virtualenv/bin/pip install -U pip setuptools

    if [ ! -d ~/inloop ]; then
      git clone /vagrant ~/inloop
    fi

    cd ~/inloop
    git stash -u
    git reset --hard origin/master
    git pull
    ~/virtualenv/bin/pip install -r requirements/development.txt
  EOF

  # Update GRUB / initiate a reboot (if necessary)
  config.vm.provision :shell, privileged: true, inline: <<-EOF
    if ! grep -q swapaccount=1 /etc/default/grub; then
      echo 'GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX swapaccount=1"' >>/etc/default/grub
      update-grub
    fi

    if ! grep -q swapaccount=1 /proc/cmdline; then
      echo "Swap accounting not active -- a reboot is necessary."
      echo 'Shutting down. Use `vagrant up <name>` to bring it up again.'
      shutdown now
    fi
  EOF
end
