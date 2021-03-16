#!/bin/bash
# Author: Dhairya Jain
# Task: Automation Script for automating the release of tern
# Description: Automates Tern's Release Process

########### PART 1 : Prepare Release PR ################
# After Freezing the development on main branch

echo "Assuming that you've already frozen the development on main branch"

DIR=$(pwd) #This is the deployment directory
BASE_DIR=$(dirname "$(pwd)") #This is the base directory
echo "Current Directory is: $DIR"
echo "Base Directory used will be $BASE_DIR"
echo "Do you agree? [y/n]:- "
l=1
while [ $l -eq 1 ]; do
  read -r proceed
  case $proceed in
    y|Y)
      echo "Continuing . . ."
      l=0
      ;;
    n|N)
      exit
      ;;
    *)
      echo "Invalid Input."
      echo "Do you agree? [y/n]:- "
      ;;
  esac
done

# Prepare your local development environment by committing or stashing your changes. Work at the tip of main.
echo "These are the pending changes in this branch"
echo
git diff

echo "You should either commit[c]/stash[s] the changes: "
l=1
while [ $l -eq 1 ]; do
  read -r commit_or_stash
  case $commit_or_stash in
    c)
      git add && git commit && git push origin main
      echo "Committed the changes on Development Branch"
      l=0
      ;;
    s)
      git stash
      echo "Stashed the changes"
      l=0
      ;;
    e)
      exit
      ;;
    *)
      echo "Unknown command. Try Again ..."
      echo "You should either commit[c]/stash[s] the changes or input e to exit: "
      ;;
  esac
done

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
l=1
while [ $l -eq 1 ]; do
  read -r manualWork1
  case $manualWork1 in
    n|N)
      exit
      ;;
    y|Y)
      echo "Continuing . . ."
      l=0
      ;;
    *)
      echo "Unknown command. Try Again:- "
      ;;
  esac
done

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
echo "Choose among the 2 options:"
echo "1. Write release notes all this stuff manually"
echo "2. Enter the path to the release notes file"
echo "Your choice [1/2]:- "
l=1
while [ $l -eq 1 ]; do
  read -r choice
  case $choice in
    1)
      touch "v$release_version.md"
      echo "Press any key (or y) when you are done writing the release notes and want to continue; press n otherwise."
      echo "Your response [y/n]: "
      read -r manualWork2
      case $manualWork2 in
        n|N)
          exit
          ;;
        *)
          ;;
      esac
      ;;
    2)
      echo "Enter the path to the release notes file: "
      read -r release_notes_path
      mv "$release_notes_path" ./"v$release_version.md"
      ;;
    *)
      echo "Invalid option. Try Again:- "
      ;;
  esac
done
#################### Part 4: Commit release notes and submit a PR and Tag release on Git################################
git add && git commit
echo "Do the github works: Commit Release Notes and submit a PR. Tag Release on Github"
echo "Press any key (or y) when you are done writing the release notes and want to continue; press n otherwise."
echo "Your response [y/n]: "
read -r manualWork3
case $manualWork3 in
  n|N)
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