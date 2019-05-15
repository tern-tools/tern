# Contributing to the Tern project

Once again, we hope you have read our [code of conduct](/CODE_OF_CONDUCT.md) before starting.

We are excited to work with anyone at any level contributing their time and efforts towards the project.

You can contribute in the following ways:

**File Issues**
- Ask questions about the project goals, a specific use case, or clarification on documentation. Asking questions lead to issues being filed, eventually making the project more usable.
- Run the code against any Docker image you are using, or any of the tests and submit bug reports when you find them.

**Contribute Documentation**
- Improve the documentation, project structure and workflow by creating a proposal.
- Contribute changes to documentation by [submitting pull requests](#submit-pr) to it.

**Contribute Code**
- [Resolve Issues](https://github.com/vmware/tern/issues).
- Improve the robustness of the project by
  - [Adding to the Command Library](docs/adding-to-command-library.md).
  - [Adding a Custom Template](docs/creating-custom-templates.md).

## Am I Qualified to Contribute?

The short answer is 'yes'!

The long answer is that there are some basic requirements that will help you contribute to any project on GitHub and this one in particular. Leveling up requires some extra knowledge:

**Beginner**
* English (not necessarily fluent but workable)
* The Python 3 Programming Language (Python is a very friendly community with plenty of tutorials you can search for)
* The Git version control system. Follow GitHub's setup guide [here](https://help.github.com/articles/set-up-git/). You can also practice submitting a pull request with no code [here](https://github.com/nishakm/puns).

**Intermediate**
* YAML (Tern uses yaml files heavily for data lookup. An overview of YAML can be found [here](http://yaml.org/))
* Object Oriented Programming in Python
* Python virtual environments
* Unix Command Line and shell scripts
* Linux System Administration
* [Docker Containers](https://docs.docker.com/)
* [Vagrant](https://www.vagrantup.com/docs/index.html)

**Advanced**
* [Container Images](https://docs.docker.com/v17.09/engine/userguide/storagedriver/imagesandcontainers/)
* [OverlayFS](https://wiki.archlinux.org/index.php/Overlay_filesystem)
* Advanced Python knowledge
* Linux Kernel knowledge would be nice

## Communicating through GitHub Issues

The fastest way you can get our attention is by filing an issue. We have some templates that help with organizing the information but if you don't think any of them are suitable, just file a regular GitHub issue. All issue templates are located in the .github/ISSUE_TEMPLATE folder in your local clone if you want to take a look at it before filing an issue.

You can:
- Ask a question
- Submit a proposal
- Submit a feature request
- File a bug report
- File a regular GitHub issue

Please do not submit a pull request without filing an issue. We will ask you to file one and refer to it in your commit message before we merge it.

**A note about maintainer's time**
Maintainers are people with lives of their own. The typical time to get a response to a question or a review on a PR is 3 business days but we take chunks of time off for other things as well so it could take longer.

**Project Maintainers**
- @nishakm
- @tpepper

## Other Communication Channels

### Public forum
You can post a topic on the [public forum](https://groups.google.com/forum/#!forum/tern-discussion). You will need to apply to join the group before posting.

### Slack channel
If you would like to chat live, you can join the Slack channel. If you don't have an @vmware.com or @emc.com email, please [follow this link](https://code.vmware.com/join), enter your email address and click "Request Invite". If you are already a member of the slack channel, or if you have an @vmware.com or @emc.com email, you can simply [sign-in to the Slack channel](https://vmwarecode.slack.com/messages/tern).

## How Do I Start Contributing?<a name="submit-pr">

Look for issues without the label `assigned` on it. This indicates that someone is already working on it. Some labels that may be of interest are listed here:

- docs: Documentation changes
- good-first-issue: A good issue to start off with if this is your first time contributing to this project
- first-timers-only: A good issue to start off with if this is your first time contributing to any GitHub project
- tests: An issue regarding testing the project code
- tools: An issue regarding tools for developers or contributors
- bug: A bug in code functionality
- arch: An issue requiring some architectural change

To start, comment on the issue asking if you can work on it. A maintainer will tag your username to the issue and apply the `assigned` label on it.

## Coding Style

Tern follows general [PEP8](https://www.python.org/dev/peps/pep-0008/) style guidelines. Apart from that, these specific rules apply:
- Indents for .py files are 4 spaces long
- Indents for .yml files are 2 spaces long
- Modules are listed as external dependencies, followed by a space, followed by internal dependencies, listed individually and in alphabetical order. For example:

```
# external dependencies not part of Tern
# possibly part of the python package or installed via pip
import os
import sys

# internal dependencies that are part of Tern
import common
from utils import rootfs
```
- Minimize [cyclomatic complexity](https://en.wikipedia.org/wiki/Cyclomatic_complexity). Most python style checkers also come with McCabe complexity checkers. A good rule of thumb is to limit the number of if-then-else statements to 3 and return once in a module.


## Commit message format

The commit message of your PR should be able to communicate what problem/opportunity the PR addresses without any reference to forum messages or discussions on slack or IRL. You may make a reference to a github issue number using the github format (eg: Resolves: #1). Here is an overview of what is needed in a good commit message taken from [this blog](https://chris.beams.io/posts/git-commit/)

* Separate subject from body with a blank line
* Limit the subject line to 50 characters
* Capitalize the subject line
* Do not end the subject line with a period
* Use the imperative mood in the subject line
* Wrap the body at 72 characters
* Use the body to explain what and why vs. how

In addition to this, we would like you to sign off on your commit. You can configure git to automatically do this for you when you run 'git commit -s'.
```
$ git config --global user.name "Some Dev"
$ git config --global user.email somedev@example.com
```
You should see a footer in your commit message like this:
```
Signed-off-by: Some Dev <somedev@example.com>
```
Please use a name you would like to be identified with and an email address that you monitor.

Example:
```
Summarize changes in around 50 characters or less

More detailed explanatory text, if necessary. Wrap it to about 72
characters or so. In some contexts, the first line is treated as the
subject of the commit and the rest of the text as the body. The
blank line separating the summary from the body is critical (unless
you omit the body entirely); various tools like `log`, `shortlog`
and `rebase` can get confused if you run the two together.

Explain the problem that this commit is solving. Focus on why you
are making this change as opposed to how (the code explains that).
Are there side effects or other unintuitive consequences of this
change? Here's the place to explain them.

Further paragraphs come after blank lines.

 - Bullet points are okay, too

 - Typically a hyphen or asterisk is used for the bullet, preceded
   by a single space, with blank lines in between, but conventions
   vary here

If you use an issue tracker, put references to them at the bottom,
like this:

Resolves: #123
See also: #456, #789

Signed-off-by: Some Dev <somedev@example.com>
```

## Learn about Tern

- [FAQ](/docs/faq.md)
- [Glossary](/docs/glossary.md)
- [Architecture](/docs/architecture.md)
- [Navigating the Code](/docs/navigating-the-code.md)

## Troubleshooting

* Unable to find module 'yaml': make sure to activate the python virtualenv first and then run pip install -r requirements.txt

## Dealing with cache.yml

cache.yml is actually a stand-in for a more sophisticated database. Tern is still not there yet. Git does not allow you to ignore this file as it is tracked. So here are some steps to deal with changes in cache.yml that you don't want to commit but still want to use:

1. Before updating your work branch, stash the changes
```
$ git stash push
Saved working directory and index state WIP on master: 71e923f Fixed bug in reporting urls for installed packages
$ git stash list
stash@{0}: WIP on master: 71e923f Fixed bug in reporting urls for installed packages
$ git status
On branch master
Your branch is up to date with 'origin/master'.

nothing to commit, working tree clean
```

2. Now you can work on the branch. When you are ready to test, apply the changes back and drop the stash from the stack.

```
$ git stash pop
On branch master
Your branch is up to date with 'origin/master'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git checkout -- <file>..." to discard changes in working directory)

	modified:   cache.yml

no changes added to commit (use "git add" and/or "git commit -a")
```

3. Commit all your changes except for cache.yml. When done committing, you can apply the uncommitted changes to the stack again before proceeding.
