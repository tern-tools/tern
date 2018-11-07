# Install

Follow the instructions on the [VirtualBox](https://www.virtualbox.org/wiki/Downloads) website to download VirtualBox on your OS.

Follow the instructions on the website to install [Vagrant](https://www.vagrantup.com/downloads.html) for your OS. 

# Steps to create a vagrant environment
In terminal, run the following commands (prompt indicated by $)

* Clone this repository by running:
* 
```
$ git clone https://github.com/vmware/tern.git
```

* Bring up the VM on Virtualbox:
* 
```
$ cd tern/vagrant
$ vagrant up
```

* SSH into the created VM:
* 
 ```
 $ vagrant ssh
 ```

# Run the program
```
$ cd /tern

# Runs the program against a sample Docker file
$ ./tern report -d samples/photon_git/Dockerfile
```

# Tern - Getting started

You can now follow the instructions in the Tern README to get a summary report and run a test.  
