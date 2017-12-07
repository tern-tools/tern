There is no special magic that Tern uses to get all the information about packages                                                                           installed in a Docker image. It just invokes shell scripts within or outside a container.                                                                     Hence it is only as good as the shell scripts it invokes. The shell scripts are listed                                                                        in the 'Command Library' which is simply two yaml files: command_lib/base.yml and                                                                             command_lib/snippets.yml.                                                                                                                                     
                                                                                                                                                              
### Adding to the Base Image Command Library                                                                                                                 
                                                                                                                                                              
You can recognize a base OS Docker image by its Dockerfile. Typically, the Dockerfile starts with the line 'FROM scratch' followed by 'ADD <filesystem>.tar /' which adds an entire OS filesystem to the image. There are many base images available to use on Dockerhub. Before considering adding any of them to the Command Library:                                                                                                        
                                                                                                                                                              
- Check if there is a Dockerfile published                                                                                                                    
- Check if the Dockerfile starts with 'FROM scratch' followed by 'ADD <filesystem.tar>'                                                                       
                                                                                                                                                              
Here is an example of Debian's base OS [Dockerfile](https://github.com/debuerreotype/docker-debian-artifacts/blob/de09dd55b6328b37b89a33e76b698f9dbe611fab/jes
sie/Dockerfile):                                                                                                                                              
```                                                                                                                                                           
FROM scratch                                                                                                                                                  
ADD rootfs.tar.xz /                                                                                                                                           
CMD ["bash"]                                                                                                                                                  
```                                                                                                                                                           
The object of the Base Image Command Library is to retrieve a list of package names, a                                                                        
corresponding list of versions, a corresponding list of licenses and a corresponding                                                                          
list of source urls using shell scripts invoked in a container. So the first step to submitting                                                               
an addition to the Base Image Command Library is to find the set of shell commands that                                                                       
will retrieve this information for your chosen base image.

For starters, to get the names of all the packages installed in a pure debian:jessie
OS container, we can run:
```
$ dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'
```
which is what we would normally do on a regular Debian OS (granted there is some
fenagling of the output to just print out the names but hey, who hasn't done fancy
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
debian:
  latest: jessie <-- In case a Dockerfile comes along where they want to track 'latest'. Tern discourages this
  tags:
    jessie: <-- tag listing
      shell: '/bin/bash' <-- Know which shell the container will use. Docker defaults to /bin/sh
      names: <-- the list of names
        invoke: <-- invoke shell script
          1: <-- step 1
            container: <-- invoke in a container
              - "dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'" <-- your shell command from above
```

This is the minimum that is required to run the tool successfully, however, your report will be full of messages
telling you to add the other information which will be *hugely* appreciated by your fellow users and developers
like the version, licenses and source urls for the packages.

The base.yml listing for this OS (Debian Jessie) looks like this:
The base.yml listing for this OS (Debian Jessie) looks like this:
```
debian:
  latest: jessie
  tags:
    jessie:
        shell: '/bin/bash'
        # either enter the package names as a list or a snippet to invoke either within or outside the container
        names:
          invoke:
            1:
              # Currently two types of environments are supported - host or container
              container:
                - "dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'"
          delimiter: "\n"
        # the length of this list should be the same as the names or else there will be a mismatch
        versions:
          invoke:
            1:
              container:
                - "pkgs=`dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'`"
                - "for p in $pkgs; do dpkg -l $p | awk 'NR>5 {print $3}'; done"
          delimiter: "\n"
        licenses:
          invoke:
            1:
              container:
                - "pkgs=`dpkg --get-selections | cut -f1 -d':' | awk '{print $1}'`"
                - "for p in $pkgs; do cat /usr/share/doc/$p/copyright; echo EOF; done"
          delimiter: 'EOF'
        src_urls: ''
```
As you can see, someone didn't add src_urls information to the command library - a good candidate for a PR!

### Adding to the Snippet Command Library

Once Tern figures out the base image from the Dockerfile it consumes, it will try to figure out what packages were installed. It does that by looking up command_lib/snippets.yml where typical installation commands are listed. For example, in
the Dockerfile located in samples/debian_vim the line 'RUN apt-get update && apt-get install vim && apt-get clean' indicates that the package 'vim' was installed using the command 'apt-get install'. Tern only knows this because 'apt-get' is a listed command and 'install' is the sub-command listed to install a package. Here is that listing:
```
apt-get: <-- the command
  install: 'install' # subcommand to install <-- subcommand to install
  remove: 'purge' # subcommand to remove a package <-- subcommand to remove
  ignore: # list of subcommands that don't add or remove packages <-- list of subcommands to ignore
    - 'update'
```
Under this command is a list of packages that may be installed. If this is a package management system used to install a whole host of packages, 'default' can be given as a package name and Tern will use it on the list of packages installed using apt-get unless there is a specific item in the list of packages with a unique name. In this case, there is only the default listing
```
  packages:
    - name: default
      version:
        # either a version number or a script snippet
        invoke:
          1:
            container:
              - "dpkg -l {package} | awk 'NR>5 {print $3}'"
      src_url:
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
For each item the listing follows similarly to the listings in base.yml, where a shell script is used to obtain the package information.

Again, you can try this on the sample image:
```
$ cd samples/debian_vim/Dockerfile
$ docker build -t vim:test .
$ docker run -it vim:test
# dpkg -l vim | awk 'NR>5 {print $3}'
```
You get the version of the package vim.

Why use '{package}' instead of 'vim' in the snippets.yml file? Since you have given the name of the package to be 'default', Tern will run the shell scripts on every package name it has come across that has been installed by apt-get when parsing the Dockerfile.
