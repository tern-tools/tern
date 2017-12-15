# Project Road Map

## Guiding Principles

* Tern is mean to provide guidance for building more compliant containers by
  * Analyzing an existing container for packages that are installed
  * Extracting the sources for packages governed by licenses that require sources to be provided
  * Rebuilding the container using equivalent packages for which the provenance (exact source code) is known

* The output that Tern creates should not be the source of truth for what is installed in the container nor be used without review. This is because the universe of software installation, package creation and management solutions including dependency management solutions is quite large. There are many different methods of discerning the contents of the container and their provenances but none of them are 100% accurate. In the end, only the person building the container knows for sure what it is meant to contain.

* Tern is not meant to be the 'silver bullet' for container compliance. Tern cannot tell you whether the packages installed on your container are 'compliant'.It is not a lawyer and is not meant to replace your compliance and/or legal team. It is only meant to automate some of the tasks that you may have to do yourself in order to meet the legal obligations for the software installed.

## Package information extraction

* Integration with a static analysis tool - Research
* SPDX document output
* YAML document output - Phase 3
* Check container against a ruleset - Backlog

## Source Retrieval

* Implementation of sources tarball retrieval - Phase 4
* Configuration to point to an external repository for scripts - Backlog
* Configuration to point to an external database - Research

## Reconstruct a compliant image

* Use configured database of known good binaries - Phase 5
* Use container labeling for metadata like build number and content digest
* Use container signing
