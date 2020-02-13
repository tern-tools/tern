SPDX-License-Identifier: BSD-2-Clause

# SPDX Tag-Value Overview for Tern

This file provides an overview of the [SPDX](https://spdx.org/) tag-value format, with focus on the particular aspects that are relevant to Tern.

Currently, SPDX has two official formats: RDF and tag-value. These formats are interchangeable using the official [SPDX tools for Java](https://github.com/spdx/tools/]). Other formats, such as JSON, are under consideration by the SPDX project.

The present document will only address the tag-value format.

### Tag-value pairs

An SPDX document consists of a series of colon-separateed tag/value pairs, one per line. The tag is in CamelCase format. 

For example, the following tag-value pairs define the version of [the SPDX specification](https://spdx.org/specifications) that is used by the document, and a name for the SPDX document:

```
SPDXVersion: SPDX-2.1
DocumentName: Tern report for Acme Dockerfile
```

The SPDX specification defines the tags that comprise the SPDX language.

The value part of the line (e.g., the part following the colon) is also a string. For some tags, the value is limited to specified values; for other tags the value may contain any text.

### Multi-line values

Some value strings can contain line breaks (not all; for some tags the value is limited to a single line). When a value string contains a line break, it must be wrapped in `<text></text>` tags. For example:

```
PackageComment: <text>This comment runs across
multiple lines.</text>
```

### Sub-tags

Some SPDX fields allow for a defined set of sub-tags, where the value string itself consists of one of a subset of permitted sub-tags, followed by a second colon before the sub-value string. Examples include:

```
Creator: Person: Jane Doe (janedoe@example.com)
Creator: Organization: JaneDoe, Inc.
```

```
FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2758
FileChecksum: MD5: 624c1abb3664f4b35547e7c73864ad24
```

### Comments

Comments can be added by prepending a `#` character at the beginning of the string.

## Element Types in SPDX Documents

SPDX tag-value pairs are grouped into related sections for each type of element that SPDX recognizes. The full set of elements is described in more detail in the SPDX specification. 

The following are likely to be the key relevant elements for Tern:

* **Document Creation** information: Appears exactly once, at the beginning of the document. This contains metadata about the document itself, including how, when and by whom it was created.
* **Package** information: Can appear zero or more times, once for each package that is referenced or described in the document.
* **Other Licensing** information: Can appear zero or more times, once for each license that is referenced in the document AND is not already on the [SPDX license list](https://spdx.org/licenses/).
* **Relationship** information: Can appear zero or more times, once for each relationship described in the document (e.g., to specify that one Package is a prerequisite for another Package).

There are other elements that may be relevant. Most notably, there is a **File** information element that can be used to describe the files contained within a Package. For the moment, this document will assume that files are not being analyzed and that Tern is only looking at licenses at a Package level.

Because the ordering of tag-value pairs is relevant, all tag-value pairs for one element typically must be contiguous before proceeding to the next element. For example, all tag-value pairs for the first Package must appear together, before those describing the second Package. The SPDX specification defines which tags indicate the beginning of a new element; for example, a `PackageName:` tag indicates the beginning of a new Package section.

## SPDX Identifiers

SPDX requires certain elements to specify an identifier that is unique within the document. This identifier can then be referenced by a Relationship to describe the relationship between two elements.

For example, if two Packages have been defined:

```
PackageName: requests
SPDXID: SPDXRef-requests

. . .

PackageName: python-urllib3
SPDXID: SPDXRef-urllib3
```

Then the identifiers can be used to describe a dependency relationship between the Packages:

```
Relationship: SPDXRef-requests HAS_PREREQUISITE SPDXRef-urllib3
```

The SPDX specification defines a large number of other relationships between two SPDX elements, beyond just describing dependency relationships.

SPDX also defines a mechanism that enables referencing SPDX elements that are described in a separate, external SPDX document.

The Document Creation element always defines the identifier `SPDXRef-DOCUMENT` to refer to that SPDX document itself:

```
SPDXID: SPDXRef-DOCUMENT
```

Packages also must define a unique SPDX identifier, which must start with `SPDXRef-` followed by any unique combination of alphanumeric characters, `.` or `-`. An identifier might incorporate a human-relevant name for the package (e.g. `SPDXRef-requests`), or alternatively Package identifiers might just be sequential numbers (e.g. `SPDXRef-1`, `SPDXRef-2`, ...).

[Back to the README](../README.md)
