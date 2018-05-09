# Contributing to the Tern project

Once again, we hope you have read our [code of conduct](/CODE_OF_CONDUCT.md) before starting.

We are excited to be working with the community to help with Open Source compliance obligations!

You can contribute in the following ways:

* Improving the Documentation
* Adding to the Command Library
* Improving the Unit and Functional Tests
* Improving the Core Project

## Skills for contributing

* English (not necessarily fluent but workable)
* Python (a working knowledge of object oriented Python would be nice, but if you know how python functions/modules work, this is enough to get you started)
* YAML (Tern uses yaml files heavily for data lookup. An overview of YAML can be found [here](http://yaml.org/))

## Keeping in touch

If you would like to ask a question or start a discussion, post a topic on the [public forum](https://groups.google.com/forum/#!forum/tern-discussion). You will need to apply to join the group before posting. We will respond to your question or topic within three days unless the post was over the weekend in which case we may take longer to respond. This is our primary communication channel so it is highly likely that you will get a response here.

If you would like to chat live, you can join the [slack channel](https://vmwarecode.slack.com/messages/tern). If you don't have an @vmware.com or @emc.com email, please click [here](https://code.vmware.com/join), enter your email address and click "Request Invite". Although we monitor the channel, we may not respond right away and if the same question was asked on the forum, we will choose to respond there.

## Learn about Tern

- [FAQ](/docs/faq.md)
- [Glossary](/docs/glossary.md)
- [Architecture](/docs/architecture.md)
- [Navigating the Code](/docs/navigating-the-code.md)

## An overview of the contribution lifecycle

Once you decide that you would like to play around with the project

1. Fork the git repository to your personal github account. See [here](https://help.github.com/articles/fork-a-repo/#fork-an-example-repository) and [here](https://help.github.com/articles/fork-a-repo/#keep-your-fork-synced) to get you started.
2. Create a branch for your work
```
$ git checkout -b my-work
```
3. Work on the code
4. Update your branch with the latest from upstream. See [here](https://help.github.com/articles/syncing-a-fork/) for an example. Note that if you have not worked on the master branch of your fork, the merges should be fast-forward merges and you should not be resolving conflicts.
5. Replay your work on top of the latest
```
$ git checkout my-work
$ git rebase master
```
Expect to spend time resolving conflicts here.
6. Run functional tests.
6. Push your branch changes to a remote branch in your fork of the repo
7. Submit a pull request (PR for short) to the upstream repo. See [here](https://help.github.com/articles/creating-a-pull-request-from-a-fork/) to get you started. If all goes well, there should be no conflicts.
8. A reviewer will further communicate with you through the PR.
9. If everything looks good the PR will be accepted.

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
## Filing an Issue

You may file an issue through the github issue tracker. Please follow the same guidelines as the commit message guidelines when formatting your issue. Please make sure to include the following for quick debugging and resolution:

* The SHA256 commit at which the bug occurred
* The project release version (if there is one)
* Your dev environment
* Reproduction steps
* The contents of tern.log (which may not have everything that went to stdout so the contents of that would also be helpful if different)

You may file an issue and create a PR that references said issue. This, however, does not guarantee acceptance of the PR. Contributing in this way works for small bug or documentation fixes but doesn't lend itself well to large updates. We encourage you to start a discussion on the forum. Typically a follow up issue will be created referencing the topic.

## Troubleshooting

* Tern produces a generic message about being unable to execute a docker command with a CalledProcessError from the get go: Make sure the docker daemon is running first
* Unable to find module 'yaml': make sure to activate the python virtualenv first and then run pip install -r requirements.txt 
