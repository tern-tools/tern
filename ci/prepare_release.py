#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Calvin Tyrer
# SPDX-License-Identifier: BSD-2-Clause

import sys
import logging
from pydriller import Repository


def get_changelog(repo):
    """
    Gets all commit hashes, messages and contributors since the last release

    Parameters:
        rep(Repository): A pydriller repository initialised to only contain
                          commits since the last release

    Returns:
        str: A string of all 8-character commit hashes and one line
             commit messages made since the last release, seperated
             by a newline character
        set: A set containing the names and email addresses of all github
             users who have had a commit merged into the main branch since
             the last release. This set does not include maintainers.
    """

    commit_history = ''
    contributors = set()
    for commit in repo.traverse_commits():
        commit_message = commit.msg
        # Ignore the auto-generated commit
        if 'Merge pull request #1' in commit_message:
            continue

        commit_hash = commit.hash[:8]
        commit_message = commit.msg
        if '\n' in commit_message:
            commit_message = commit.msg.split('\n', 1)
        commit_history = ''.join((commit_history, commit_hash,
                                  ' ', commit_message[0], '\n'))
        contributors.add(commit.author.name + ' ' + commit.author.email)

    # Ignore maintainers, they are credited later
    contributors = contributors - {'Rose Judge rjudge@vmware.com',
                                   'Nisha K nishak@vmware.com'}

    return commit_history, contributors


def write_release_document(repo, release_document):
    """
    Writes any details that can be automated into a release summary file

    Parameters:
        rep(Repository): A pydriller repository initialised to only contain
                         commits since the last release
        release_document(File): The file to write the release details into
    """

    release_document.write("# Release x.y.z\n\n")
    release_document.write("## Summary\n\n\n\n")
    release_document.write("## New Features\n\n\n\n")
    release_document.write("## Bug Fixes\n\n\n\n")
    release_document.write("## Resolved Technical Debt\n\n\n\n")
    release_document.write("## Future Work\n\n\n\n")
    release_document.write("## Changelog\n")
    release_document.write("Note: This changelog will not include \
                            these release notes\n\n")
    commits, contributors = get_changelog(repo)
    release_document.write("```\n")
    release_document.write(commits)
    release_document.write("```\n\n")
    release_document.write("## Contributors\n\n")
    release_document.write("```\n")
    for contributor in contributors:
        release_document.write(''.join((contributor, '\n')))
    release_document.write("```\n\n")
    release_document.write("## Contact the Maintainers\n\n")
    release_document.write("Nisha Kumar: nishak@vmware.com\n")
    release_document.write("Rose Judge: rjudge@vmware.com")


def create_release_summary(last_release):
    """
    Creates a file named next-realease.md and calls write_release_document on
    it

    Parameters:
        last_release(str): The release number of the last release in the
                           format 'x.y.z'
    """

    repo = None
    try:
        repo = Repository('https://github.com/ReconPangolin/tern',
                          from_tag='v{num}'.format(num=last_release))
    except AttributeError:
        logging.error("The tag for the last release could not be found")
        sys.exit(3)

    with open("next-release.md", "w", encoding="utf-8") as release_document:
        write_release_document(repo, release_document)


def update_requirements():
    """
    Updates packages in requirements.in and requirements.txt to their latest
    release
    """

    requirements = []
    with open(sys.path[0] + "/../requirements.in", "r", encoding="utf-8") as \
            requirements_in:
        for line in requirements_in:
            if line[0].isalpha():
                requirements.append(line.strip().lower())

    past_versions = get_past_versions(requirements)

    latest_versions = get_latest_versions(requirements)

    packages_to_update = get_packages_to_update(requirements, past_versions,
                                                latest_versions)

    requirements_text = []
    with open(sys.path[0] + "/../requirements.txt", "r", encoding="utf-8") as \
            requirements_document:
        requirements_text = requirements_document.readlines()

    with open(sys.path[0] + "/../requirements.txt", "w", encoding="utf-8") as \
            requirements_document:
        for line in requirements_text:
            if line[0].isalpha():
                for package in packages_to_update:
                    if package in line.lower():
                        index = line.find('=')
                        line = line[:index+1]
                        decimals = past_versions[package].count('.')
                        latest_version = latest_versions[package].split('.')
                        version = '.'.join(latest_version[:decimals+1])
                        line = ''.join((line, version, '\n'))
                        break
            requirements_document.write(line)


def get_past_versions(requirements):
    """
    Gets the current release package versions of packages in 'requirements.in'

    Parameters:
        requirements(list): A list of all lines in 'requirements.in'

    Returns:
        dict: A dictionary mapping a package name to the version used in the
              current release
    """

    past_versions = {}
    with open(sys.path[0] + "/../requirements.txt", "r", encoding="utf-8") as \
            requirements_document:
        for line in requirements_document:
            if line[0].isalpha():
                package, version = line.split('=')
                package = package[:-1].lower()
                if package in requirements:
                    past_versions[package.lower()] = version.strip()
    return past_versions


def get_latest_versions(requirements):
    """
    Gets the latest package versions of packages in 'requirements.in'

    Parameters:
        requirements(list): A list of all lines in 'requirements.in'

    Returns:
        dict: A dictionary mapping a package name to the latest release
    """

    latest_versions = {}
    try:
        with open(sys.path[0] + "/../upgrade.txt", "r", encoding="utf-8") as \
                update_document:
            for line in update_document:
                if line[0].isalpha():
                    package, version = line.split('==')
                    if package in requirements:
                        latest_versions[package] = version.strip()
    except FileNotFoundError:
        logging.error("upgrade.txt not found")
        sys.exit(3)
    return latest_versions


def get_packages_to_update(requirements, past_versions, latest_versions):
    """
    Gets a list of all packages that need to be updated

    Parameters:
        requirements(list): A list of all lines in 'requirements.in'
        past_versions(dict): A dictionary mapping a package name to the
                             version used in the current release
        latest_versions(dict): A dictionary mapping a package name to the
                               latest release

    Returns:
        list: A list of all packages that have been updated since the last
              release
    """

    packages_to_update = []
    for package in requirements:
        past_version = past_versions[package].split('.')
        latest_version = latest_versions[package].split('.')
        i = 0
        for number in past_version:
            if number != latest_version[i]:
                packages_to_update.append(package)
                break
            i += 1
    return packages_to_update


if __name__ == '__main__':
    """
    Arguments:
        argv[1]: The release number of the last release in the
                 format 'x.y.z'
    """

    if len(sys.argv) != 2:
        logging.error("Usage: python create_release_summary.py lastRelease")
        sys.exit(1)

    update_requirements()
    create_release_summary(sys.argv[1])
