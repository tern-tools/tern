# Adding a Listing to the Command Library
There is no special magic that Tern uses to get all the information about
packages installed in a Docker image. It just invokes shell scripts within
or outside a [chroot](https://wiki.archlinux.org/index.php/change_root)
environment - similar to what is done when building root filesystems for linux
distributions.

Since its accuracy is heavily dependent on these shell scripts, it is
important to check whether the scripts are producing the the right information
in the right format.

The shell scripts are listed in the [Command Library](glossary.md) which is
simply two yaml files: `command_lib/base.yml` and `command_lib/snippets.yml`.

base.yml lists snippets that operate on full root filesystems that typically
come with a package manager or some other way of grokking the manifest of
the filesystem. snippets.yml lists shell scripts for command line instructions
used to create the diff filesystems that make up a container image. These are
for imperative commands like `apt-get install` or `wget web_package && ...`.

Based on how a package is installed, one can figure out scripts to retrieve
information for the package such as the version that was installed and the
license of the package.                                                                                                                                    
For example, for a debian based container image, one can figure out what
packages are installed by running `dpkg --get-selections`. If you look at
`command_lib/base.yml` you will find a listing that looks like this:

```
-----
dpkg:
  path:
    - 'usr/bin/dpkg'
  shell: '/bin/bash'
  # either enter the package names as a list or a snippet to invoke either within or outside the container
  names:
    invoke:
      1:
        # Currently two types of environments are supported - host or container
        container:
          - "dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'"
    delimiter: "\n"
```

`dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'` is a command that
you can run in a Docker container based on debian to get all the names of the
packages installed in your container (the stuff after `dpkg --get-selections`
is to trim out the information about the versions, arch and other information
to just get the names). So, nothing special, but still needs to be accurate.
                                                                                                                       
## Adding to the Base Image Command Library                                                                                                                 
You can recognize a base OS Docker image from the Dockerfile. Typically, the
Dockerfile starts with the line `FROM scratch` followed by `ADD <filesystem>.tar /`
which adds an entire OS filesystem to the image. There are many base images
available to use on Dockerhub. Before considering adding any of them to the
Command Library:
                                                                                                      
* Check if there is a Dockerfile published
* Check if the Dockerfile starts with 'FROM scratch' followed by 'ADD <filesystem.tar>'

Here is an example of Debian's base OS [Dockerfile](https://github.com/debuerreotype/docker-debian-artifacts/blob/de09dd55b6328b37b89a33e76b698f9dbe611fab/jessie/Dockerfile):

```
FROM scratch
ADD rootfs.tar.xz /
CMD ["bash"]                             
```
The object of the Base Image Command Library is to retrieve a list of package
names, a corresponding list of versions, a corresponding list of licenses and
a corresponding list of project urls using shell scripts.

So the first step to submitting an addition to the Base Image Command Library
is to find the set of shell commands that will retrieve this information for
your chosen base image.

For instance, to get the names of all the packages installed in a pure debian:jessie
OS container, we can run:
```
$ dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'
```
which is what we would normally do on a regular Debian OS (granted there is some
finagling of the output to just print out the names but hey, who hasn't done fancy
shell-fu to get a desired output? No joke - I found this on stackoverflow).

You can try this yourself on a debian:jessie container:
```
$ docker pull debian:jessie
$ docker run -it debian:jessie
# dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'
```
Awesome! You now have a list of package names. Now to add this to command_lib/base.yml.

In this file you would add the following listing:

```
dpkg: <-- the package manager for debian
  path: <-- where on the filesystem the binary exists
    - 'usr/bin/dpkg' <-- it can exist in many places, make sure to not add a prepending '/'; Tern will take care of that for you
  shell: '/bin/bash' <-- what shell to use
  names: <-- listing to retrieve names of the packages
    invoke: <-- it's not a hard coded listing but a list of snippets to invoke
      1: <-- the first one
        container: <-- invoke it in a container (Tern will actually use a chroot environment but for testing purposes we will usea Docker container
          - "dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'" <-- the command in double quotes as you are using awk here
    delimiter: "\n" <-- each of the results gets returned as a list with "\n" as a delimiter. Double quotes are needed due to python formatting
```

This is the minimum that is required to run Tern successfully, however, your
report will be full of messages telling you to add the other information
which will be *hugely* appreciated by your fellow users and developers
like the version, licenses and project urls for the packages.

This listing will now work for any debian based container OS or a minimal root filesystem that comes with dpkg.

## Adding to the Snippet Command Library

Once Tern analyzes the base layer of the container image, it will try to figure
out what packages were installed in the subsequent layers. It does that by
looking up `command_lib/snippets.yml` where typical installation commands are
listed. For example, in the Dockerfile located in `samples/debian_vim` the line
`RUN apt-get update && apt-get install vim && apt-get clean` indicates that the
package 'vim' was installed using the command 'apt-get install'. Tern only knows
this because 'apt-get' is a listed command and 'install' is the sub-command
listed to install a package. Here is that listing:

```
apt-get: <-- the command
  install: 'install' # subcommand to install <-- subcommand to install
  remove: 'purge' # subcommand to remove a package <-- subcommand to remove
  ignore: # list of subcommands that don't add or remove packages <-- list of subcommands to ignore
    - 'update'
```

Under this command is a list of packages that may be installed. If this is a
package management system used to install a whole host of packages, 'default'
can be given as a package name and Tern will use it on the list of packages
installed using apt-get unless there is a specific item in the list of
packages with a unique name. In this case, there is only the default listing:

```
  packages:
    - name: default
      version:
        # either a version number or a script snippet
        invoke:
          1:
            container:
              - "dpkg -l {package} | awk 'NR>5 {print $3}'"
      proj_url:
        invoke:
          1:
            container:
              - "apt-get download --print-uris {package}"
      license:
        invoke:
          1:
            container:
              - "cat /usr/share/doc/{package}/copyright"
      deps:
        invoke:
          1:
            container:
              - "apt-cache depends --installed --no-suggests {package} | awk 'NR>1 {print $2}'"
        delimiter: "\n"
```

For each item the listing follows similarly to the listings in base.yml, where
a shell script is used to obtain the package information.

Again, you can try this on the sample image:

```
$ cd samples/debian_vim/Dockerfile
$ docker build -t vim:test .
$ docker run -it vim:test
# dpkg -l vim | awk 'NR>5 {print $3}'
```
You get the version of the package vim.

Why use '{package}' instead of 'vim' in the snippets.yml file? Since you have
given the name of the package to be 'default', Tern will run the shell scripts
on every package name it has parsed from the container manifest that was installed
with apt-get.

## Using verify_invoke.py to check your script

To check if your script is producing accurate results that Tern can understand,
you can make use of the verify_invoke.py script for both base.yml and
snippets.yml listing

```
$ export PYTHONPATH=`pwd
$ python tools/verify_invoke.py -h
usage: verify_invoke.py [-h] [--container CONTAINER] [--keys KEYS [KEYS ...]]                                                   
                        [--shell SHELL] [--package PACKAGE]

A script to test if the set of commands that get executed within a container                                                    
produce expected results. Give a list of keys to point to in the command                                                        
library and the image

optional arguments:
  -h, --help            show this help message and exit
  --container CONTAINER
                        Name of the running container
  --keys KEYS [KEYS ...]
                        List of keys to look up in the command library                                                          
  --shell SHELL         The shell executable that the container uses                                                            
  --package PACKAGE     A package name that the command needs to execute with
```

I assume here that you have already installed Docker and are familiar with
how to run a container. verify_invoke.py will not do this for you, but you
can use it to test your snippets. I also assume you have set up the Tern
environment:

```
$ python3 -m venv ternenv
$ cd ternenv
$ git clone https://github.com/tern-tools/tern.git
$ source bin/activate
$ cd tern
$ pip install -r requirements.txt

```

Generally here is the workflow:

### For base.yml

1. Run your container using `docker run -td --name test <image:tag>` to run your container in the background and with a pseudo-tty and to give it a name `test`
2. Export PYTHONPATH to the current directory assuming you have already cd'd into the tern directory
```
$ export PYTHONPATH=`pwd`
```
3. Run verify_invoke with the following flags
```
$ python tools/verify_invoke.py --container test --keys base <package_manager> <names/versions/licenses/src_urls> --shell '/usr/bin/bash'
```

This should give you a result that looks something like this:
```
$ python tools/verify_invoke.py --container pensive_kapitsa --keys base tdnf names --shell '/usr/bin/bash'
Output list: bash bzip2-libs ca-certificates ca-certificates-pki curl curl-libs e2fsprogs-libs elfutils-libelf expat-libs filesystem glibc hawkey krb5 libcap libdb libgcc libsolv libssh2 ncurses-libs nspr nss-libs openssl photon-release photon-repos popt readline rpm-libs sqlite-libs tdnf toybox xz-libs zlib
Error messages: 
Number of elements: 32
```

The --keys flag is a list of keys to look up in the command library dictionary
until you get to the 'invoke' key and the attribute's scripts you want to test
out. For base.yml the first key is 'base'. If you look up tdnf > names in
base.yml, you should see a listing with and 'invoke' key like this:

```
   invoke:
      1:
        container:
          # make sure to use single quotes for these lines as
          # docker exec doesn't parse double quotes contiguously
          - 'tdnf check-update > /dev/null' # used to update the repo metadata
          - 'tdnf list installed | cut -f1 -d"."'
    delimiter: "\n" # make sure the delimiter is in double quotes or python will interpret the \ as literal
```

You can now verify if this result is what you expect for the list of package
names, the number of elements in the list i.e. the number of installed packages
and if there were any error messages

### For snippets.yml

1. Run your container using `docker run -td --name test <image:tag>` to run your container in the background and with a pseudo-tty and to give it a name `test`
2. Export the PYTHONPATH to the current directory assuming you have cd'd into the tern directory
```
$ export PYTHONPATH=`pwd`
```
3. Run verify_invoke with the following flags
```
$ python tools/verify_invoke.py --container test --keys snippets <command> packages <version/license/proj_url> --shell '/usr/bin/bash' --package <package name>
```

This should give you a result that looks something like this:
```
$ python tools/verify_invoke.py --container pensive_kapitsa --keys snippets tyum packages version --shell '/usr/bin/bash' --package bash
Output list: 4.4-6.ph2
Error messages:
Number of elements: 1
```

For snippets.yml the first key is 'snippets'. If you look up tyum > packages in
snippets.yml, you should see a list of dictionaries. Go ahead and give the required
attribute (version, license or proj_url) as the next key. The listing containing the
'invoke' key should look something like this:
```
      version:
        invoke:
          1:
            container:
              - 'list=`tdnf list installed {package}`'
              - 'c=0; for l in $list; do if [ $c == 1 ]; then echo $l; fi; c=$(((c+1)%3)); done;'

```
You can now verify if this result is what you expect for the version number for
the given package name and if there were any error messages. The number of elements
should always be 1 as you are querying for only one package name.

As always, don't hesitate to ask questions by filing an issue with 'Question:'
as the prefix of the subject, on the Slack channel or on the mailing list.

[Back to the README](../README.md)
