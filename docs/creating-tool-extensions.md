# Creating a Tool Extension
You can use Tern with another file or filesystem analysis tool to analyze container images. You can find examples of such tools in the `tern/extensions` folder. Currently two external tools are supported:
* [scancode-toolkit](https://github.com/nexB/scancode-toolkit): A license scanning tool that finds licenses in source code and binaries. Although support for formatting is not in place at the moment, it is something that will be completed in subsequent releases.
* [cve-bin-tool](https://github.com/intel/cve-bin-tool): A security vulnerability scanning tool that finds common vulnerabilities. Note that although you can use a security scanner with Tern, there isn't any support for reporting the results beyond printing them to console. This may change as the industry demand for security information in Software Bill of Materials seems to be on the rise.

If you would like to make a tool extension, here are some general steps to follow:

## 1. Familiarize yourself with Tern's Data Model

The classes for the objects that are used to keep discovered metadata are in the `tern/classes` folder. Check out the [data model document](./data-model.md) for a general layout of the classes. Refer to the individual files for a list of properties. These store the supported metadata. If you do not see the metadata you are interested in, please submit a proposal issue to add this property to the appropriate class. This should be a reasonably trivial change with minimal effect on backwards compatibility.

## 2. Create a plugin

To create a plugin for the tool, create a folder under `tern/extensions` with the plugin name. Create an empty `__init__.py` file here and create a file called `executor.py`. This file will contain a class which is derived from the abstract base class `executor.py` located under `tern/extensions`. The `Executor` class requires you to implement the method `execute` which takes an object of type `Image` or any of its derived classes (for example `DockerImage`). You can use this method to call a library function or run a CLI command to collect the required information. Once done, you can set the properties of the `Image` object and the objects within it (see the data model as a reference. See the `.py` files in `tern/classes` for a list of properties you can set.

You can refer to the existing plugins as a guide for implementing the `execute` method of your executor class. There are helper methods in `tern/analyze/passthrough.py` which you can make use of, or write your own implementation if you need to.

## 3. Test your plugin

To test your plugin, add the plugin to `setup.cfg` under `tern.extensions`. For example, let's say you have created a plugin called "custom" to run a custom script. Your plugin's `executor.py` should live in `tern/extensions/custom`. You will add the plugin as follows:

```
tern.extensions =
    cve_bin_tool = tern.extensions.cve_bin_tool.executor:CveBinTool
    scancode = tern.extensions.scancode.executor:Scancode
    custom = tern.extensions.custom.executor:Custom
```

To test out your plugin run:

```
$ pip install -e.[dev]
$ tern report -x custom -i <image:tag>
```

To test out the different formats for your plugin run:

```
$ tern report -x custom -f <format> -i <image:tag>
```

where <format> is one of Tern's supported formats. To see what formats are supported, run `tern report --help`.

If you need a custom report format please refer to the document on [creating custom report formats](./creating-custom-templates.md)

[Back to the README](../README.md)
