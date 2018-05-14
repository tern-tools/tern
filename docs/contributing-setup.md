# Install

Follow the instructions on the website to install [Vagrant](https://www.vagrantup.com/downloads.html) for your OS.  

Follow the instructions on the [VirtualBox](https://www.virtualbox.org/wiki/Downloads)website to download VirtualBox on your OS.  

# Steps to create a vagrant environment

In terminal, run the following commands (prompt indicated by $)  

```
$ vagrant init ubuntu/bionic64
        A `Vagrantfile` has been placed in this directory. You are now ready to `vagrant up` your first virtual environment! Please read
        the comments in the Vagrantfile as well as documentation on `vagrantup.com` for more information on using Vagrant.

$ vagrant up
        Bringing machine 'default' up with 'virtualbox' provider...

$ vagrant ssh
        Welcome to Ubuntu 18.04 LTS (GNU/Linux 4.15.0-20-generic x86_64)
```

# Create an SSH key

Once in Vagrant (which you should be after running `vagrant ssh`), create an SSH key if you don't yet have one.  

To check, go to your GitHub settings and select "SSH and GPG keys." Then, click "New SSH Key."  

In terminal:  

```
vagrant@ubuntu-bionic:~$ ssh-keygen
        Generating public/private rsa key pair.
        Enter file in which to save the key (/home/vagrant/.ssh/id_rsa):     # hit enter to continue
        Enter passphrase (empty for no passphrase):     # Pick something you will remember
```

Your SSH key should now exist. To get the key, type:
```
vagrant@ubuntu-bionic:~$ cat ~/.ssh/id_rsa.pub
```
Then copy the output and paste it in the box on GitHub labeled "Key," then give it a title and save.  

# Check packages
## Ubuntu repository versions

Update the Ubuntu repositories  

```
vagrant@ubuntu-bionic:~$ sudo apt-get update 
```

Upgrade all currently installed packages  

```
vagrant@ubuntu-bionic:~$ sudo apt-get upgrade 
```

## Python3 versions

```
vagrant@ubuntu-bionic:~$ sudo apt-get install python3 python3-pip python3-venv
```

## Install Docker 

```
vagrant@ubuntu-bionic:~$ sudo apt-get install docker.io
```

### Docker adjustments

**Optional:** Make it easier to run Docker commands by adding the vagrant user to the Docker group. If you want to run commands against Docker without doing this, you will need to use `sudo`. 

```
vagrant@ubuntu-bionic:~$ sudo usermod -a -G docker vagrant
```

*Note1: -a appends any changes you make to the user group, -G is a secondary user group to which the specified user is added*  
*Note2: if this doesn't work, you may have to log out and then log back in to vagrant.*

# Clone the project repository
```
vagrant@ubuntu-bionic:~$ git clone https://github.com/vmware/tern.git
```

# Run the program
```
$ cd tern
$ pip install -r requirements.txt
$ ./tern report -d samples/photon_git/Dockerfile     # Runs the program against a sample Docker file
```

# Tern - Getting started

You can now follow the instructions in the Tern README to get a summary report and run a test.  
