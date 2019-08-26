# Release Checklist

This is a checklist for cutting a release

- [ ] Prepare Release PR.
    * Freeze development on master.
    * Create a fresh environment and activate it.
    * Clone this repository.
    * Create a PR branch for the release.

- [ ] Update direct dependencies and run tests.
    * Run `pip install wheel pip-tools`.
    * Run `pip-compile --upgrade --output-file docs/releases/v<release>-requirements.txt`.
    * Compare the release versions of the requirements to the current requirements.txt file. Upgrade if necessary.
    * Run `pip install .` to install tern.
    * Run appropriate tests. Roll back requirements if necessary.
    * When satisfied, run `pip-compile --output-file docs/releases/v<release>-requirements.txt`.

- [ ] Write release notes.
    * Summary
    * New Features (if any)
    * Deprecated Features (if any)
    * Bug Fixes (if any)
    * Resolved Technical Debt (if any)
    * Future Work
    * Changelog
        * "Note: This changelog will not include these release notes"
        * "Changelog produced by command: `git log --pretty=format:"%h %s" v0.3.0..master`"
    * Contributors (look at Authors in the changelog `git log --pretty=format:"%an %ae" v0.3.0..master | uniq`)
    * Contact the Maintainers

- [ ] Commit release notes, `v<release>-requirements.txt`, and any changes to `requirements.txt`.

- [ ] Tag release on GitHub. Check to see if release automation works.

- [ ] Test pip package.
    * Create a fresh environment.
    * Pip install tern.
    * Run appropriate tests.
