#!/bin/bash
# Author: Dhairya Jain
# Task: Automation Script for automating the release of tern
# Description:
#    Automate Tern's Release Process
#
#    Tern's release process is very manual and cumbersome as of now. This is
#    an attempt to automate it to a certain extent using shell scripts.
#    Having at least a portion of this process automated will save time and
#    reduce errors.
#
#    Resolves: #885
#
#    Signed-off-by: Dhairya Jain jaindhairya2001@gmail.com
#


########### PART 1 : Prepare Release PR ################
# After Freezing the development on main branch

echo "Assuming that you've already frozen the development on main branch"

DIR=$(pwd) #This is the deployment directory
BASE_DIR=$(dirname "$(pwd)") #This is the base directory
echo "Current Directory is: $DIR"
echo "Base Directory used will be $BASE_DIR"
echo "Do you agree? [y/n]"
read -r proceed
case $proceed in
  n)
    exit
  ;;
*)
  ;;
esac

# Prepare your local development environment by committing or stashing your changes. Work at the tip of main.
echo "You should either commit[c]/stash[s] the changes: "
read -r commit_or_stash
case $commit_or_stash in
  c)
    git commit && git push origin main
    echo "Committed the changes on Development Branch"
    ;;
s)writing the release notes etc
  git stash
  echo "Stashed the changes"
  ;;
*)
  echo "Unknown command. Exiting ..."
  exit
esac
#Create a branch for the release: git checkout -b <release branch name>.
echo "Enter the name of release branch: "
read -r rBranch
git checkout -b "$rBranch"
#In a separate folder, create a fresh environment and activate it.
cd "$BASE_DIR" || (echo "cd Failed" && exit )
mkdir .release
cd ".release" || (echo "cd Failed" && exit )
python3 -m venv ternenv
source ternenv/bin/activate
#Clone the tern/main repository and cd into it.
git clone --single-branch git@github.com:tern-tools/tern.git
cd "tern" || (echo "cd Failed" && exit )

########### PART 2 : Update Direct Dependencies and run tests ################

#PART 2a : Update Direct Dependencies
#Update direct dependencies and run tests.
pip install wheel pip-tools twine
pip-compile --upgrade --output-file upgrade.txt
cd "$DIR" || (echo "cd Failed" && exit )
# Some Manual work
echo "Compare the module versions in upgrade.txt with requirements.txt in the development environment. Bump up versions if needed."
echo "Press Y when you are done updating and want to continue? [y/n]: "
read -r manualWork1
case $manualWork1 in
  n)
    exit
  ;;
*)
  ;;
esac

#Part 2b :Run Tests
cd "$BASE_DIR/.release/ternenv/tern" || (echo "cd Failed" && exit )
pip install . #Install tern
tox #The tests
echo "Which release version is this (eg 2.0.1)? : "
read -r release_version
pip-compile --generate-hashes --output-file "v$release_version-requirements.txt"
cp "v$release_version-requirements.txt" "$DIR/docs/releases/"

#################### Part 3: Write release notes. ################################
cd "$DIR/docs/releases/" || (echo "cd Failed" && exit )
echo "Write release notes all this stuff manually (type n) or Enter the path to the release notes file:- "
read -r release_notes_path
case $manualWork2 in
  n)
    touch "v$release_version.md"
    echo "Press Y when you are done writing the release notes etc and want to continue? [y/n]: "
    read -r manualWork2
    case $manualWork2 in
      n)
        exit
      ;;
    *)
      ;;
    esac
  ;;
  *)
    mv "$release_notes_path" ./"v$release_version.md"
  ;;
esac
#################### Part 4: Commit release notes and submit a PR and Tag release on Git################################
git add && git commit
echo "Do the github works: Commit Release Notes and submit a PR. Tag Release on Github"
echo "Press Y when you are done with these things and want to continue? [y/n]: "
read -r manualWork3
case $manualWork3 in
  n)
    exit
  ;;
*)
  ;;
esac
#################### Part 5: Deploy to PyPI ################################
cd "$BASE_DIR/.release/ternenv/tern" || (echo "cd Failed" && exit )
git fetch --tags
echo "Name the release tag: "
read -r releaseTag
git checkout -b release "$releaseTag"
pip-compile
python setup.py sdist bdist_wheel
twine check dist/*
twine upload dist/*

################## Part 6: Test Pip Package ###########################
cd "$BASE_DIR" || (echo "cd Failed" && exit )
mkdir .test-release
cd ".test-release" || (echo "cd Failed" && exit )
python3 -m venv ternenv
source ternenv/bin/activate
pip install tern
tox

################## Part 7: Prepare Sources Tarball ###########################
mkdir vendor
pip download -d vendor --require-hashes --no-binary :all: -r docs/releases/v<"$release_version">-requirements.txt
tar cvzf tern-<"$releaseTag">-vendor.tar.gz vendor/