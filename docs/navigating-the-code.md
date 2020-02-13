# Navigating Tern's Code

To help with code navigation, looking up the [glossary](/docs/glossary.md) is useful. All the code lives in the directory `tern`. The rest of the stuff in the root directory have to do with configurations for build and packaging. If you want to try each of the modules in the Python repl (Read Eval Print Loop), you can reference them from the module `tern`.

Here is a layout of the directory structure:

```
▾ tern/
    __main__.py <-- Tern entry point

  ▾ analyze/  <-- Each container image format will have its own subdirectory for analysis
      common.py <-- Common modules used at a high level throughout the code
    ▾ docker/
        analyze.py
        container.py
        dockerfile.py
        docker.py <-- modules specific to Docker
        run.py

  ▾ classes/  <-- These are individual objects. Each has a corresponding test in the tests directory
      command.py
      docker_image.py
      image.py
      image_layer.py
      notice.py
      notice_origin.py
      origins.py
      package.py
      template.py

  ▾ command_lib/ <-- These are the bash commands that get run to collect information about the container image
      base.yml <-- System wide scripts for package managers and such
      snippets.yml <-- scripts for one off commands
      command_lib.py <-- Command Library modules

  ▾ extensions/ <-- This is the extension plugin library. An extension is an external tool Tern can use to analyze the filesystems in the container image
      executor.py <-- This is the abstract base class that an extension plugin needs to inherit from
    ▸ cve_bin_tool/
	executor.py
    ▾ scancode/
        executor.py

  ▾ formats/ <-- This is the reporting template plugin library. Each subdirectory is a module that can be dynamically loaded at runtime based on the users report selection
      generator.py <-- This is the abstract base class for report plugins
    ▾ default/
        generator.py
    ▾ json/
        generator.py
    ▾ spdx/
        formats.py
        spdx.py
      ▾ spdxtagvalue/
           generator.py
    ▾ yaml/
         generator.py

  ▾ report/
      content.py
      errors.py
      formats.py
      report.py <-- Main reporting module

  ▾ scripts/debian/ <-- Example script to pull sources for debian based images
    ▾ jessie/
        sources.list
      apt_get_sources.sh

  ▾ tools/ <-- Tools that can be used individually or by Tern
      fs_hash.sh
      verify_invoke.py
      container_debug.py

  ▾ utils/ <-- general utility modules used throughout the code
      cache.py
      constants.py
      general.py
      metadata.py
      rootfs.py
```

Tests live outside of the `tern` folder, in a folder called `tests`.

```
▾ tests/
    test_class_command.py
    test_class_docker_image.py
    test_class_image.py
    test_class_image_layer.py
    test_class_notice.py
    test_class_notice_origin.py
    test_class_origins.py
    test_class_package.py
    test_class_template.py
    test_fixtures.py
    test_util_commands.py
    test_util_metadata.py
```

Scripts used by our CI/CD setup live outside the `tern` folder, in a folder called `ci`.

```
▾ ci/
    evaluate_docs.py
    test_commit_message.py
    test_files_touched.py
```

Documentation lives in a folder called `docs`. Sample Dockerfile live in a folder called `samples`.

Some general rules about where the code is located:
- Utilities used anywhere in the project go in `utils`.
- Class definitions go in `classes`. For clarity, the name of the file is also the name of the class but with an underscore separating the words rather than CamelCase.
- Any operation related to look up and operations with the Command Library go in `command_lib`.
- Any documentation goes in `docs`.
- Any operations related to reporting go in `report`.
- Any sample Dockerfiles go in `samples`. The directory structure needs to be such that the Dockerfile exists along with the image context. This means that when you use "docker build" only the Dockerfile gets sent to the docker daemon rather than the whole directory structure. This saves on build time.
- The `scripts` directory is not used by the project yet, but there is potential to use it for complicated operations such as extracting source tarballs.
- All unit and functional tests go in `tests`.

Code organization follows these general rules:
- Each class is in its own file.
- Utils are organized based on what they operate on.
- Subroutines for use in general or under a particular "domain" can live in a default file name called `helpers.py`. You will find plenty of `helpers.py` files within the `analyze` folder.

[Back to the README](../README.md)
