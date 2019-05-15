# Adding a Custom Template
As of this writing, there is a rudimentary way of adding custom templates to modify Tern's output
format to suit downstream use. The trouble with custom formatting is that there are so many ways
folks consume data. You can have a homegrown tool that could make use of Tern's reports if only
it would format it so it's compatible with said tool. Plus there are all the other data formats
that folks want their data in - YAML, JSON, XML (yes, an outdated format but still used by many
tools). Not to mention configuration management tools that want this data in specific places in
their config files. As usual, we'll try to make the hooks into Tern to be as open-ended as possible this early in development. With that in mind, here is how you can create your custom template.

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

These mappings give you access to Tern's reporting on what it finds in a container image and what it does to analyze it. It's nice to have but doesn't need to be implemented if you don't want this information or if you want to use it in some other way (see `tern/report/spdxtagvalue/generator.py` for an example of this case).

To see an example of how to create this subclass of Template, see `tests/test_fixtures.py` where you will find a `TestTemplate1` which does not contain mappings for the origins property and `TestTemplate2` which does.

If you don't want some properties included, don't include them in the mapping. If you want the same property name used, just enter a mapping with the same string on either side of the separator.

For example, you'd like to keep `version` the same, so in your dictionary you will enter:
```
'version': 'version'
```

## 2. Write a Custom Document Generator (Optional)
You could use the available yaml or json format, in which case you don't have to do anything more, or if you need some custom arrangement (for example, you want to arrange the keys and values in
a different way. Then you can do that within the folder `tern/report`. For example, `spdxtagvalue` is one of the folders in here. Tern will automatically look for a module called `generator` in here.

To make a generator, create a folder in `tern/report` containing the files:
```
__init__.py
generator.py
```

The `generator.py` should have a function called `generate.py` which takes in a list of Image objects. If you think you will be working with only one Image object, reference just the first image. From here you can use `to_dict(template)` which will take in your template object and return a dictionary containing all the keys definined in your mapping. For example:

```
def generate(image_list):
    one_image = image_list[0]
    template = MyTemplate()
    custom_dict = one_image.to_dict(template)
    # do the string arrangements here
```

See `tern/report/spdxtagvalue/generator.py` for an example of how this is created.

## Future work on templating
It would be nice to pass in config files to provide a specific mapping. We will work towards that going forward. But this only works for the available formats like YAML and JSON (not necessarily SPDX as it follows a specification). If you want these values to be in a specifc location (for example, an HTML report) then it would require you to make a custom generator. Making an extensible, config based, document templating mechanism for every possible type of document is a (possible) distant future goal.
