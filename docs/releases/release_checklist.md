# Release Checklist

This is a checklist for cutting a release

- [ ] Prepare Release PR.
    * Freeze development on master.
    * Create a fresh environment and activate it.
    * Clone this repository.
    * Create a PR branch for the release.

- [ ] Update direct dependencies and run tests.
    * Run `pip install wheel pip-tools twine`.
    * Run `pip-compile --upgrade --output-file docs/releases/v<release>-requirements.txt` where <release> is of the form `major_minor_patch`.
    * Compare the release versions of the requirements to the current requirements.txt file. Upgrade if necessary.
    * Run `pip install .` to install tern.
    * Run appropriate tests. Roll back requirements if necessary.
    * When satisfied, run `pip-compile --generate-hashes --output-file docs/releases/v<release>-requirements.txt`.

- [ ] Write release notes.
    * Summary
    * New Features (if any)
    * Deprecated Features (if any)
    * Bug Fixes (if any)
    * Resolved Technical Debt (if any)
    * Future Work
    * Changelog
        * "Note: This changelog will not include these release notes"
        * "Changelog produced by command: `git log --pretty=format:"%h %s" v<tag>..master`"
    * Contributors (look at Authors in the changelog `git log --pretty=format:"%an %ae" v<tag>..master | uniq`)
    * Contact the Maintainers

- [ ] Commit release notes, `v<release>-requirements.txt`, and any changes to `requirements.txt`.

- [ ] Tag release on GitHub.
    * Add new tag
    * Provide a link to the release notes.

- [ ] Deploy to PyPI
    * Run `git fetch --tags` to get the release tag
    * Run `git checkout -b release <release tag>
    * Run `pip compile`
    * Run `python setup.py sdist bdist_wheel`
    * Run `twine check dist/*`
    * Run `twine upload dist/*`. Here enter username and password and verify via 2FA.

- [ ] Test pip package.
    * Create a fresh environment.
    * Pip install tern.
    * Run appropriate tests.

- [ ] Prepare sources tarball.
    * In the release environment, create a new directory called `vendor`
    * Run `pip install -d vendor --require-hashes --no-binary :all: -r docs/releases/v<release>-requirements.txt`
    * Run `tar cvzf tern-<release>-vendor.tar.gz vendor/`

- [ ] Upload the wheel and sources packages to GitHub release page 
