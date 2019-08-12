# Release Checklist

This is a checklist for cutting a release

[ ] Update direct dependencies and run tests
* Create a fresh environment.
* Pip install wheel.
* Pip install each of the first level dependencies listed in the dependencies.yml file.
* Do pip freeze and check the major and minor versions for all the dependencies in the requirements.txt file.
* Update the requirements.txt file in the development environment for tern.
* Pip uninstall tern and then reinstall tern. Run the tests. Rollback dependencies if needed.
* Copy output of pip freeze to `tern/docs/releases/v<release>-vendor.txt`

[ ] Write release notes
* Summary
* New Features (if any)
* Deprecated Features (if any)
* Bug Fixes (if any)
* Resolved Technical Debt (if any)
* Future Work
* Changelog

Note: This changelog will not include these release notes

Changelog produced by command: `git log --pretty=format:"%h %s" v0.3.0..master`

* Contributors (look at Authors in the changelog `git log --pretty=format:"%an %ae" v0.3.0..master | uniq`)
* Contact the Maintainers

[ ] Commit release notes and any dependency file changes.

[ ] Tag release on GitHub. Check to see if release automation works.

[ ] Test pip package
* Create a fresh environment.
* Pip install tern.
* Run tests.
