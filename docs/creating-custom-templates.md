# Adding a Custom Report
Tern currently only supports SPDX tag-value, JSON and YAML report formats natively. However, Tern is setup in a way that you can customize the report format to fit your requirements should you find yourself needing a alternative report style. In order to create a customized report, you will need to write a report plugin that adheres to your specific report requirements. As of this writing, Tern uses [Stevedore](https://docs.openstack.org/stevedore/latest/) to create plugins for each of the report formatting styles. Stevedore is an OpenStack python module that allows for dynamic loading of plugins through the use of setuptools entrypoints.

The existing report plugins under `tern/formats` are good examples for you to reference as you write your own. If you are experiencing any behavior from Tern that you don't feel is consistent with this documentation, please open a GitHub issue. See below for how you can create your own custom report.

## 1. Create a Mapping
If you look in `tern/classes` you will find 3 important classes - Package (`package.py`), ImageLayer (`image_layer.py`) and Image (`image.py`). DockerImage (`docker_image.py`) is a special subclass of Image because, well, Docker images are special and have their own way of defining their metadata. Each of these classes have a list of properties which you can find in their `__init__` function.
Each of these classes has a `to_dict` method that takes a Template object. This is what you will create. The `to_dict` method essentially dumps the properties into a dictionary in which the keys are the property names without the private (begins with a double underscore) or protected (begins with a single underscore). In your custom template, you will create a mapping between these property names and the names you would like to have in your custom document.

For example, you want to be specific in naming a "package name" so you want to replace `name` in Package with `package.name`.

To do this, you will create a new class that inherits from class `Template`.

```
class MyTemplate(Template):
```

Within that class, you will create these functions:

```
def package():

def image_layer():

def image():
```

The `package()` function returns a dictionary that maps the property names to the key names of your choice.

```
def package():
    return {'name': 'package.name',
            'version': 'package.version',
             ...
	    }
```

Do the same for the `image_layer()` function and the `image()` function.

There are some optional methods that you can also provide mappings for:

```
def notice():

def notice_origin():

def origins():
```

These mappings give you access to Tern's reporting on what it finds in a container image and what it does to analyze it. It's nice to have but doesn't need to be implemented if you don't want this information or if you want to use it in some other way (see `tern/formats/spdx/spdxtagvalue/generator.py` for an example of this case).

To see an example of how to create this subclass of Template, see `tests/test_fixtures.py` where you will find a `TestTemplate1` which does not contain mappings for the origins property and `TestTemplate2` which does.

If you don't want some properties included, don't include them in the mapping. If you want the same property name used, just enter a mapping with the same string on either side of the separator.

For example, you'd like to keep `version` the same, so in your dictionary you will enter:
```
'version': 'version'
```
## 2. Write a Custom Document Generator

Tern uses a python module called Stevedore to dynamically load each report plugin at runtime. When Tern is invoked from the command line using the `report -f <format>` option,  it will use Stevedore to call the `generate()` function inside the specified report format. You can see how `generate()` gets called in the `generate_format` function inside `tern/report/report.py`.

Because Tern loads the report plugin at runtime using Stevedore, it is required that you derive your own `generate()` function. This should happen inside your own subclass derived from the `Generate` abstract base class in `tern/formats/generator.py`. To make a generator, create a folder under `tern/formats/<your_custom_report_name>`. For the purpose of this example, let's call the plugin you want to create `custom`.  You would create a new directory `tern/formats/custom` containing the files:
```
__init__.py
generator.py
```

The `generator.py` file should have a function called `generate()` which takes two inputs: `self`, and a list of Image objects. Your `generator.py` should look something like this:

```
from tern.formats import generator


class Custom(generator.Generate):
    def generate(self, image_obj_list):
    '''Given a list of image objects, do something to generate a custom report.'''
    custom_report = ''
    for image in image_obj_list:
	# Do something to update the custom_report string
    return custom_report
```

You may need to write other helper functions inside `generator.py` (but outside of your `Custom` class). Take a look at the other reporting formats for guidance.


## 3. Add your report plugin as an entrypoint in setup.cfg

Stevedore uses entrypoints to find and load the selected report plugin at runtime. If you look in setup.cfg you will see the list of native formatting options there:

```
[entry_points]
tern.formats =
    default = tern.formats.default.generator:Default
    spdxtagvalue = tern.formats.spdx.spdxtagvalue.generator:SpdxTagValue
    json = tern.formats.json.generator:JSON
    yaml = tern.formats.yaml.generator:YAML
```

In order to register your plugin you need to add it to the list of format entry points. The value to the left of the `=` is the value you would use to run Tern from the command line. The value to the right of the `=` is where Stevedore tries to find the plugin at runtime. Let's take the spdxtagvalue report plugin as an example. If a user invokes Tern using the spdxtagvalue reporting style, Stevedore will look at the `tern/formats/spdx/spdxtagvalue/generator.py` file. Inside the `generator.py` file, Stevedore will look for the `generate()` function inside the `SpdxTagValue` subclass. There may also be other functions present in the `generator.py` file (which can be included or not included in the `SpdxTagValue` class) but the `generate()` function is what tells Tern how to get information and structure it in the output report. It is also important to note that the SpdxTagValue class inside `generator.py` must be derived from the Generate base class in `tern/formats/generator.py`.

Continuing with the example from step #2, if you wanted to enable your `custom` plugin you would make the following change to `setup.cfg` and then invoke Tern using `tern report -f custom -i <image> -o <output_file>`

```
 tern.formats =
     default = tern.formats.default.generator:Default
     spdxtagvalue = tern.formats.spdx.spdxtagvalue.generator:SpdxTagValue
     json = tern.formats.json.generator:JSON
     yaml = tern.formats.yaml.generator:YAML
+    custom = tern.formats.custom.generator:Custom
```

[Back to the README](../README.md)
