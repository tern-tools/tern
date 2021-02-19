# Release Checklist

This is a checklist for cutting a release

- [ ] Prepare Release PR.
    * Freeze development on main.
    * Prepare your local development environment by committing or stashing your changes. Work at the tip of main.
    * Create a branch for the release: `git checkout -b <release branch name>`.
    * In a separate folder, create a fresh environment and activate it.
    * Clone the `tern/main` repository by running `git clone --single-branch git@github.com:tern-tools/tern.git` and `cd` into it.

- [ ] Update direct dependencies and run tests.
    * In the fresh environment, run `pip install wheel pip-tools twine`.
    * Run `pip-compile --upgrade --output-file upgrade.txt`.
    * Compare the module versions in upgrade.txt with requirements.txt in the development environment. Bump up versions if needed.
    * In the fresh environment, run `pip install .` to install tern.
    * Run appropriate tests. Roll back requirements if necessary.
    * When satisfied, run `pip-compile --generate-hashes --output-file v<release>-requirements.txt` where <release> is of the form `major_minor_patch`.
    * Copy this file to the `docs/releases/` folder in the development environment.

- [ ] Write release notes.
    * In the development environment, create a new file for the release notes: `docs/releases/v<release>.md`
    * If you are writing release notes for a patched release, only include:
      - A link to the primary release notes.
      - A brief summary of what the patched release changes do.
      - A list of patches since the last release was cut. You can get this information by running `git log --oneline` and finding the commits since the tag.

    * For any other release, include the following in your notes:
      - Summary
      - New Features (if any)
      - Deprecated Features (if any)
      - Bug Fixes (if any)
      - Resolved Technical Debt (if any)
      - Future Work
      - Changelog     
        * "Note: This changelog will not include these release notes"
        * "Changelog produced by command: `git log --pretty=format:"%h %s" v<tag>..main`"
      - Contributors (look at Authors in the changelog `git log --pretty=format:"%an %ae" v<tag>..main | sort | uniq`). Remove the maintainers name from the contributor list.
      - Contact the Maintainers

    * Update the Project Status part of the README.md to reflect this release and add it to the list of releases.

- [ ] Commit release notes and submit a PR
    * `git add` and `git commit` any changes. This will likely include`v<release>-requirements.txt`, any changes to `requirements.txt` and `v<release>.md`.
    * Open a pull request in the Tern project repository for your release changes.
    * Request a review from another maintainer. Update PR as needed based on feedback. Merge the PR. This commit is where the release will be tagged.

- [ ] Tag release on GitHub.
    * Navigate to the Tern GitHub page. Click on `Releases`. Click on `Draft a new release` to add a new tag. The `tag version` should be `v<major.minor.patch>`. `Release title` field should be `Release <major.minor.patch>`.
    * Provide a link to the release notes.

- [ ] Deploy to PyPI
    * Run the following steps in the fresh environment where you first cloned tern/main.
    * Run `git fetch --tags` to get the release tag.
    * Run `git checkout -b release <release_tag>`.
    * Run `pip-compile`.
    * Run `python setup.py sdist bdist_wheel`.
    * Run `twine check dist/*`.
    * Run `twine upload dist/*`. Here enter username and password and verify via 2FA.

- [ ] Test pip package.
    * Create a fresh environment.
    * Pip install tern.
    * Run appropriate tests.

- [ ] Prepare sources tarball.
    * In the release environment, create a new directory called `vendor`.
    * Run `pip download -d vendor --require-hashes --no-binary :all: -r docs/releases/v<release>-requirements.txt`.
    * Run `tar cvzf tern-<release_tag>-vendor.tar.gz vendor/`.
    * Upload the vendor tarball to the GitHub release page.

- [ ] Upload the wheel package to the GitHub release page. The wheel package can be found under the `dist/` directory in the environment where you first cloned tern/main or it can be downloaded for the PyPI release page.
