# YAML Format Output

You can get the results in a YAML file to be consumed by a downstream tool or script.

`$ tern report -f yaml -i golang:1.12-alpine -o output.yaml`

A YAML format output file starts with line comments indicating the version of Tern. It has a `image` key(image.py) corresponding to the analyzed image. Here are the subkeys and their description:

- `config`: the image config metadata
- `image_id`: this is a unique identifier for the image - for OCI spec
    this could be the digest. For now this is the sha256sum of the
    config.json
- `manifest`: the json object representing the image manifest
- `layers`: list of layer objects in the image(image_layer.py)
  - `diff_id`: the sha256 of the layer filesystem
  - `fs_hash`: the hashed contents of the layer filesystem - default to empty string if there is no tarball of the layer filesystem
  - `packages`: list of objects of type Package (package.py)
    - `name`: package name
    - `version`: package version
    - `pkg_license`: package license that is declared
    - `copyright`: copyright text
    - `proj_url`: package source url
    - `download_url`: package download url
    - `origins`: a list of NoticeOrigin objects(notice_origin.py, expanded below)
    - `checksum`: checksum as package property
  - `origins`: list of NoticeOrigin objects (notice_origin.py, expended below)
  - `tar_file`: the path to the layer filesystem tarball
  - `created_by`: sometimes the metadata will contain a created_by
      key containing the command that created the filesystem layer
  - `import_image`: if the layer is imported from another image this is a pointer to that image. In Python terms it is just the name of the Image object or any object that uses this layer Based on how container image layers are created, this is usually the last layer of the image that was imported
  - `import_str`: The string from a build tool (like a Dockerfile) that created this layer by importing it from another image
  - `files_analyzed`: whether the files in this layer are analyzed or not
  - `analyzed_output`: the result of the file analysis

`origins` is the origin of a notice, which is expanded as follows.

- origins
  - origin_str: the origin string, from the input or the environment or the configuration
  - notices
    - message: the notice message
    - level: notice level - error, warning or hint
      * error: cannot continue further
      * warning: will try to continue from here
      * info: information only
      * hint: message on how to make the results better
