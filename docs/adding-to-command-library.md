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

base.yml lists files that are typically found in the filesystem of a known
Linux distribution. They are typically package managers but they can be any
unique file that identifies the type of base OS for the container image.

Alternatively, snippets.yml lists shell scripts for command line instructions
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

Alternatively, you can point to the `base.yml` way of listing packages. For example,
you can point `apt-get` back to `dpkg` like this:

```
  packages: 'dpkg'
```

This is currently the most ubiquitous way of enabling inventorying using a package
manager.


## Using Tern's 'debug' option to check your script

To check if your script is producing accurate results that Tern can understand,
you can make use of Tern's 'debug' option for both base.yml and
snippets.yml listing.

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

(This workflow only works for base.yml)

Run tern in the following way:

```
$ tern debug -i <image:tag> --keys base <package_manager> <names/versions/licenses/src_urls> --shell '/usr/bin/bash'
```

This should give you a result that looks something like this:
```
$ tern debug -i photon:2.0 --keys base tdnf names --shell '/usr/bin/bash'
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
and if there were any error messages.

What if you encounter an error? Tern's debug option can also help you chroot into the filesystem to try running the script manually.

**WARNING** This only works on Linux distros. Windows and MacOS are not supported.

```
$ tern debug -i <image:tag> --step
```

This will drop you into an interactive mode where you will be asked to pick the layer you want to debug

```
*************************************************************
          Container Image Interactive Debug Mode             
*************************************************************

[0] /bin/sh -c #(nop) ADD file:240dde03c4d9f0ad759f8d1291fb45ab2745b6a108c6164d746766239d3420ab in / 
[1] /bin/sh -c dnf -y update && dnf install -y make git golang golang-github-cpuguy83-md2man    btrfs-progs-devel       device-mapper-devel     libassuan-devel gpgme-devel     gnupg   httpd-tools     which tar wget hostname util-linux bsdtar socat ethtool device-mapper iptables tree findutils nmap-ncat e2fsprogs xfsprogs lsof docker iproute         bats jq podman runc      golint  openssl         && dnf clean all
[2] /bin/sh -c set -x   && REGISTRY_COMMIT_SCHEMA1=ec87e9b6971d831f0eff752ddb54fb64693e51cd     && REGISTRY_COMMIT=47a064d4195a9b56133891bbb13620c3ac83a827     && export GOPATH="$(mktemp -d)"         && git clone https://github.com/docker/distribution.git "$GOPATH/src/github.com/docker/distribution"    && (cd "$GOPATH/src/github.com/docker/distribution" && git checkout -q "$REGISTRY_COMMIT")      && GOPATH="$GOPATH/src/github.com/docker/distribution/Godeps/_workspace:$GOPATH"                go build -o /usr/local/bin/registry-v2 github.com/docker/distribution/cmd/registry      && (cd "$GOPATH/src/github.com/docker/distribution" && git checkout -q "$REGISTRY_COMMIT_SCHEMA1")      && GOPATH="$GOPATH/src/github.com/docker/distribution/Godeps/_workspace:$GOPATH"               go build -o /usr/local/bin/registry-v2-schema1 github.com/docker/distribution/cmd/registry       && rm -rf "$GOPATH"
[3] /bin/sh -c set -x   && export GOPATH=$(mktemp -d)   && git clone --depth 1 -b v1.5.0-alpha.3 git://github.com/openshift/origin "$GOPATH/src/github.com/openshift/origin"    && sed -i -e 's/\[\[ "\${go_version\[2]}" < "go1.5" ]]/false/' "$GOPATH/src/github.com/openshift/origin/hack/common.sh"         && (cd "$GOPATH/src/github.com/openshift/origin" && make clean build && make all WHAT=cmd/dockerregistry)       && cp -a "$GOPATH/src/github.com/openshift/origin/_output/local/bin/linux"/*/* /usr/local/bin   && cp "$GOPATH/src/github.com/openshift/origin/images/dockerregistry/config.yml" /atomic-registry-config.yml    && rm -rf "$GOPATH"     && mkdir /registry
[4] /bin/sh -c go version
[5] /bin/sh -c #(nop) WORKDIR /go/src/github.com/containers/skopeo
[6] /bin/sh -c #(nop) COPY dir:8e7a6d060051c80f562171cdc69069a21b60ed3b5e3355a9dabe31523a31d432 in /go/src/github.com/containers/skopeo 

Pick a layer to debug: 
```

After picking a layer, you should get some instructions on how to proceed with your debugging

```
Run 'cd /home/nisha/.tern/temp/mergedir && sudo chroot . /bin/sh' to look around

After exiting from your session, run 'cd -' to go back and 'tern debug --recover' to clean up.
```

You should get something like this if you run the first command

```
root@ubuntu / $ ls
atomic-registry-config.yml  boot  etc   lib    lost+found  mnt  proc      root  sbin  sys  usr
bin                         dev   home  lib64  media       opt  registry  run   srv   tmp  var
```

This is what the container filesystem looks like at that specific layer. To exit out of this, run `exit`. At this point you should still be in the working directory. To get back, run `cd -`.

To recover the filesystem, run the following:

```
$ tern debug --recover
```

As always, don't hesitate to ask questions by filing an issue with 'Question:'
as the prefix of the subject, on the Slack channel or on the mailing list.

[Back to the README](../README.md)
