SPDX-License-Identifier: BSD-2-Clause

# SPDX Mapping for Tern

This file describes a potential mapping between Tern's data structures and the relevant fields of an [SPDX](https://spdx.org/) tag-value document. This is intended to assist with enabling Tern to output its findings in SPDX tag-value format, for consumption by other tools.

In particular, it will focus on highlighting any necessary data items that are deemed "mandatory" by the SPDX specification.

Version 2.1 of [the SPDX specification](https://spdx.org/specifications) will be used, since it is the most recent minor release. Relevant details of the SPDX tag-value format can be found in [the overview document](spdx-tag-value-overview.md) in this directory.

## Relevant Fields

The following table contains (1) all fields that are designated by the SPDX specification as 'mandatory', for the SPDX elements that Tern is likely to use; and (2) any additional fields that are optional but likely to be useful for Tern.

Thoughts on mapping these fields to Tern's data model are described in the **Mapping** section below.

Section (§) numbers are references to the relevant portions of [the SPDX specification](https://spdx.org/specifications), version 2.1. Examples should be assumed to be on a single line, though a Markdown formatter might split them across lines.

### Document Creation

The following fields should appear *once*, at the beginning of the SPDX document:

 §  | SPDX Field name | Mandatory? | Brief description    | Example
----|-----------------|------------|----------------------|---------
2.1 | SPDX Version    |    Yes     | version of SPDX spec | `SPDXVersion: SPDX-2.1`
2.2 | Data License    |    Yes     | license for SPDX metadata in the document itself; always `CC0-1.0` | `DataLicense: CC0-1.0`
2.3 | SPDX Identifier |    Yes     | identifier for the SPDX document itself; always `SPDXRef-DOCUMENT` | `SPDXID: SPDXRef-DOCUMENT`
2.4 | Document Name   |    Yes     | human-readable name for the SPDX document itself | `DocumentName: Tern report for ACME Dockerfile`
2.5 | SPDX Document Namespace | Yes| unique absolute URI for the SPDX document itself | `DocumentNamespace: https://example.com/spdxdocs/tern-report-ACME-1.0.1-123456`
2.7 | License List Version    | No | release version of the SPDX License List being used | `LicenseListVersion: 3.4`
2.8 | Creator         |    Yes     | one or more people, orgs or tools used to create the SPDX document | `Creator: Tool: tern-0.4.0`
2.9 | Created         |    Yes     | the time and date when the SPDX document was created (ISO 8601; UTC) | `Created: 2019-03-15T08:25:00Z`

### Package

The following fields should appear once per Package described in the SPDX document. Each Package section must start with the `PackageName` field.

 §  | SPDX Field name  | Mandatory? | Brief description    | Example
----|------------------|------------|----------------------|---------
3.1 | Package Name     |    Yes     | full name of package | `PackageName: requests`
3.2 | Package SPDX Identifier | Yes | SPDX identifier for this package, for reference within this document | `SPDXID: SPDXRef-python-requests-3.1.5`
3.3 | Package Version  |     No     | the package's version | `PackageVersion: 3.1.5`
3.7 | Package Download Location | Yes | where the package can be downloaded, or `NOASSERTION` if unknown or choose not to provide | `PackageDownloadLocation: git://github.com:swinslow/tern.git@5cd034e02ebaa4b680a9ffbe1a6d8ea11aef4d84`
3.8 | Files Analyzed   |    Yes     | *** - see below        | `FilesAnalyzed: false`
3.10| Package Checksum |     No     | checksum for identifying a Package | `PackageChecksum: SHA256: afff3924849e458c5ef237db5f89539274d5e609db5db935ed3959c90f1f2d51`
3.13| Concluded License|    Yes     | license concluded by SPDX creator as governing the Package, or `NOASSERTION` if unknown or choose not to provide | `PackageLicenseConcluded: LGPL-2.0-only AND MIT`
3.15| Declared License |    Yes     | licenses declared by Package authors as governing the Package, or `NOASSERTION` if unknown or choose not to provide | `PackageLicenseDeclared: MIT`
3.17| Copyright Text   |    Yes     | any copyright notice text for the Package, or `NOASSERTION` if unknown or choose not to provide | `PackageCopyrightText: Copyright (c) 2017-2019 Jane Doe`
3.21| External Reference |   No     | reference to external source of info, e.g. package manager reference | `ExternalRef: PACKAGE-MANAGER npm http-server@0.3.0`

*** For the Files Analyzed field (3.8), this must be set to `false` if the SPDX document does NOT include File element sections for the Files contained within the Package. If File sections are included, then this should be set to `true` (or the field can be omitted); however, in that case additional mandatory fields are required, notably the Package Verification Code (3.9).

### Relationship

Whenever a relationship is being expressed between two SPDX elements, the following fields should appear.

Relationships do not need to appear grouped together in any particular location. They typically appear immediately following one of the SPDX elements they are describing.

 §  | SPDX Field name | Mandatory? | Brief description    | Example
----|-----------------|------------|----------------------|---------
7.1 | Relationship    |    Yes     | express the relationship between two SPDX elements | `Relationship: SPDXRef-requests HAS_PREREQUISITE SPDXRef-urllib3`

A list of the various Relationship types that are currently recognized is available in section 7.1.1 of [the SPDX specification](https://spdx.org/specifications).

### Other License

The following fields should appear once per non-standard license (i.e., a license that is *not* on the [SPDX License List](https://spdx.org/licenses/) described in the SPDX document. Each Other License section should start with the `LicenseID` field.

This section is not required (and must not be included) for any license that *is* already on the SPDX License List.

 §  | SPDX Field name   | Mandatory? | Brief description    | Example
----|-------------------|------------|----------------------|---------
6.1 | License Identifier|    Yes     | unique identifier for license in SPDX document | `LicenseID: LicenseRef-BSD-3-Clause-variant-1`
6.2 | Extracted Text    |    Yes     | actual text of license | `ExtractedText: <text>Redistribution and use in source and binary forms...</text>`
6.3 | License Name      |    Yes     | human-readable name for license | `LicenseName: BSD-3-Clause variant 1`

## Mapping

Given the SPDX fields described above, the following discusses how to map those SPDX fields to Tern's existing data model. Items that I've marked with *** will likely require some additional discussion.

### Document Creation

Include once at the beginning of the SPDX document.

 §  | SPDX Field name | Tern data model reference | Comments
----|-----------------|---------------------------|---------
2.1 | SPDX Version    | N/A                       | will always be `SPDXVersion: SPDX-2.1`
2.2 | Data License    | N/A                       | will always be `DataLicense: CC0-1.0`
2.3 | SPDX Identifier | N/A                       | will always be `SPDXID: SPDXRef-DOCUMENT`
2.4 | Document Name   | **TBD**                   | does Tern have a human-readable way to refer to the image or Dockerfile being analyzed?
2.5 | SPDX Document Namespace | **TBD**           | ***
2.7 | License List Version    | **TBD**           | can specify based on whichever version of the SPDX license list that version of Tern is using
2.8 | Creator         | **TBD**                   | could be something like `Creator: Tool: tern-XYZ`, with `XYZ` being Tern's version or commit hash
2.9 | Created         | N/A                       | generate at document creation time

### Packages

#### Tern `Package`

An SPDX "Package" maps fairly well to Tern's `Package` class. 

 §  | SPDX Field name  | Tern data model reference | Comments
----|------------------|---------------------------|---------
3.1 | Package Name     | `Package.name()`          |
3.2 | Package SPDX Identifier | **TBD**            | initially, probably use incrementing counter (e.g., `SPDXRef-Package-1`, `SPDXRef-Package-2` ...). May want to figure out a way to incorporate package name / version if we can de-duplicate to ensure uniqueness.
3.3 | Package Version  | `Package.version()`       |
3.7 | Package Download Location | **TBD**          | does Tern collect download location information? is there anything here that can be retrieved from package managers? if not, then use `NOASSERTION`
3.8 | Files Analyzed   | N/A                       | will always be `FilesAnalyzed: false` unless we want to report on file-level analysis
3.10| Package Checksum | **TBD**                   | appears that we don't collect any checksum info, at the Tern `Package` level. can we collect anything relevant for e.g. `apt-get` retrieved packages?
3.13| Concluded License| **TBD**                   | to be discussed whether this should be `NOASSERTION` or should be same as Declared License
3.15| Declared License | `Package.license()`       |
3.17| Copyright Text   | **TBD**                   | does Tern collect copyright information? is there anything here that can be retrieved from package managers? if not, then use `NOASSERTION`
3.21| External Reference | **TBD**                 | to be discussed whether to report on package manager identifiers in some fashion; also to discuss limited scope of existing SPDX package manager definitions

#### Tern `ImageLayer`

Note that a Tern `ImageLayer` could also be represented by an SPDX "Package". By doing so, Relationships can then be used to express the interactions between the `ImageLayer` and its packages.

 §  | SPDX Field name  | Tern data model reference | Comments
----|------------------|---------------------------|---------
3.1 | Package Name     | `ImageLayer.diff_id()` or `ImageLayer.fs_hash()` | which of these hashes would be more appropriate? I assume there isn't another human-readable name for an `ImageLayer`
3.2 | Package SPDX Identifier | **TBD**            | probably use something like `SPDXRef-ImageLayer-HASH` with HASH being either `ImageLayer.diff_id()` or `ImageLayer.fs_hash()`
3.3 | Package Version  | N/A                       | likely omit? this is not a mandatory field and might not make sense for an `ImageLayer`
3.7 | Package Download Location | **TBD**          | likely `NOASSERTION` unless we can use a hash to point to a download location
3.8 | Files Analyzed   | N/A                       | will always be `FilesAnalyzed: false` unless we want to report on file-level analysis
3.10| Package Checksum | `ImageLayer.diff_id()` or `ImageLayer.fs_hash()` | which of these hashes would be more appropriate?
3.13| Concluded License| **TBD**                   | to be discussed whether this should be `NOASSERTION`, or should be same as Declared License, or should combine its Tern `Package` licenses somehow
3.15| Declared License | **TBD**                   | to be discussed whether this should be `NOASSERTION` or should incorporate a license specified in the Dockerfile, if any, or perhaps (if this is correct) from an OCI `org.opencontainers.image.licenses` annotation?
3.17| Copyright Text   | **TBD**                   | to be discussed whether this should be `NOASSERTION` or should incorporate a copyright notice specified in the Dockerfile, if any
3.21| External Reference | **TBD**                 | likely omit? this is not a mandatory field and might not make sense for an `ImageLayer`

#### Tern `Image`

Note that a Tern `Image` could also be represented by an SPDX "Package", likely with many of the same considerations as described above for `ImageLayer`.

### Relationship

Any relationships would make use of the `SPDXRef-` identifiers defined above. Below are some possible examples, with "Package" below referring to Tern's idea of the `Package` class:

* `SPDXRef-Image-1 HAS_PREREQUISITE SPDXRef-Package-17`: the Image requires the Package as a dependency
* `SPDXRef-Package-17 HAS_PREREQUISITE SPDXRef-Package-22`: one Package has another as a dependency
* `SPDXRef-Image-1 CONTAINS SPDXRef-ImageLayer-10`: the Image contains the ImageLayer
* `SPDXRef-Package-17 BUILD_TOOL_OF SPDXRef-Image-1`: the Package is used as a build tool for the Image
* `SPDXRef-Package-22 OPTIONAL_COMPONENT_OF SPDXRef-Package-17`: one Package is an optional component of another

If the SPDX document includes a File element for the Dockerfile being analyzed by Tern, additional relationships could be useful also:
* `SPDXRef-Dockerfile-1 GENERATES SPDXRef-Image-1`: the Dockerfile generates the Image
* `SPDXRef-Dockerfile-newer DESCENDANT_OF SPDXRef-Dockerfile-older`: one Dockerfile is a newer version of an earlier Dockerfile
* `SPDXRef-Dockerfile-1 METAFILE_OF SPDXRef-Image-1`: the Dockerfile is a metadata file that describes the Image

If additional relationships would be useful beyond those currently specified by SPDX, there is an `OTHER` option, or additional relationship types could be proposed for inclusion in the SPDX specification.

[Back to the README](../README.md)
