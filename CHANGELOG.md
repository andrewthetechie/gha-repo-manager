# Changelog

## [1.9.0](https://github.com/actuarysailor/gha-repo-manager/compare/v1.8.0...v1.9.0) (2024-06-02)


### Features

* Ability to configure deployment environments (including their secrets/variables) ([#20](https://github.com/actuarysailor/gha-repo-manager/issues/20)) ([5499a84](https://github.com/actuarysailor/gha-repo-manager/commit/5499a84c9691f7d3d19f0895cacbd865ebfc6c8c))
* Ability to configure repo Collaborators (teams + users) ([#18](https://github.com/actuarysailor/gha-repo-manager/issues/18)) ([19b7dbc](https://github.com/actuarysailor/gha-repo-manager/commit/19b7dbcf2bef348226efa95f394a645c14a91f2e))
* Ability to configure repo Variables ([#19](https://github.com/actuarysailor/gha-repo-manager/issues/19)) ([29ea9a8](https://github.com/actuarysailor/gha-repo-manager/commit/29ea9a8646761be6d238b18d8c77b741636e7403))
* Adjust repo for self-management ([#16](https://github.com/actuarysailor/gha-repo-manager/issues/16)) ([61853a2](https://github.com/actuarysailor/gha-repo-manager/commit/61853a2861df6ff3084e45e9fef5b67de5a7969d))


### Bug Fixes

* Auto Docs action-docs-action workflow ([#21](https://github.com/actuarysailor/gha-repo-manager/issues/21)) ([156e9e7](https://github.com/actuarysailor/gha-repo-manager/commit/156e9e78b3f33aa0e895e87653ba7fedb042e3ff))


### Documentation

* Update Readme ([3b8ee6e](https://github.com/actuarysailor/gha-repo-manager/commit/3b8ee6eb48373ae615718c6a1199e697c1e11052))

## [1.8.0](https://github.com/andrewthetechie/gha-repo-manager/compare/v1.7.2...v1.8.0) (2024-06-02)


### Features

* Ability to configure repo Collaborators (teams + users) ([#232](https://github.com/andrewthetechie/gha-repo-manager/issues/232)) ([1bd6d38](https://github.com/andrewthetechie/gha-repo-manager/commit/1bd6d382c795e30990b71a202981e40c4cde323a))
* Pydantic 2.7.1 PR ([#225](https://github.com/andrewthetechie/gha-repo-manager/issues/225)) ([c1e014a](https://github.com/andrewthetechie/gha-repo-manager/commit/c1e014adcf31bafbcd7b29087ebd4e4a4b052ee0))


### Bug Fixes

* pydantic 2 fixes ([#237](https://github.com/andrewthetechie/gha-repo-manager/issues/237)) ([252c43a](https://github.com/andrewthetechie/gha-repo-manager/commit/252c43af4de68f15ebfb70ef7292bd10b4cc0b6c))

## [1.7.2](https://github.com/andrewthetechie/gha-repo-manager/compare/v1.7.1...v1.7.2) (2023-10-06)


### Bug Fixes

* pin to bullseye docker image ([#69](https://github.com/andrewthetechie/gha-repo-manager/issues/69)) ([863bf6b](https://github.com/andrewthetechie/gha-repo-manager/commit/863bf6b257c6b32cb1284f19f604102d45abc499))

## [1.7.1](https://github.com/andrewthetechie/gha-repo-manager/compare/v1.7.0...v1.7.1) (2023-05-29)


### Bug Fixes

* **nulls:** Minor fixes to address null values ([#52](https://github.com/andrewthetechie/gha-repo-manager/issues/52)) ([ec5c9be](https://github.com/andrewthetechie/gha-repo-manager/commit/ec5c9be75600f37953800dc8a4d2ad25d1099521))

## [1.7.0](https://github.com/andrewthetechie/gha-repo-manager/compare/v1.6.0...v1.7.0) (2023-05-25)


### Features

* **new_bp_comparisons:** New Branch Protection Comparisons previously omitted ([#43](https://github.com/andrewthetechie/gha-repo-manager/issues/43)) ([ef6dad4](https://github.com/andrewthetechie/gha-repo-manager/commit/ef6dad4f17703353eab5cda8dc3a2c59fa4602e9))
* **settings.py:** Now compares all settings ([#41](https://github.com/andrewthetechie/gha-repo-manager/issues/41)) ([441b8e4](https://github.com/andrewthetechie/gha-repo-manager/commit/441b8e49c8ce09a74dc525e2808a5a74db0dd459))
* update poetry ([#25](https://github.com/andrewthetechie/gha-repo-manager/issues/25)) ([7983a04](https://github.com/andrewthetechie/gha-repo-manager/commit/7983a049789d053d343ee4c6465a5227e5995b6c))


### Bug Fixes

* add debug logging of diff ([#46](https://github.com/andrewthetechie/gha-repo-manager/issues/46)) ([ad86b78](https://github.com/andrewthetechie/gha-repo-manager/commit/ad86b7813217db76d997ab704607bc9d930599fb))
* **branch_protection:** fix false to False ([c4a164d](https://github.com/andrewthetechie/gha-repo-manager/commit/c4a164d99755b865d3b58f1fbff322fdb2b9947a))
* **branch_protections.py:** Sort Required Status Checks ([#38](https://github.com/andrewthetechie/gha-repo-manager/issues/38)) ([4d4c44f](https://github.com/andrewthetechie/gha-repo-manager/commit/4d4c44fd10847c7ecc8539e6b84701d7ddd2e439))
* **branch_protections.py:** Working Status Check Reqs ([#42](https://github.com/andrewthetechie/gha-repo-manager/issues/42)) ([33090f5](https://github.com/andrewthetechie/gha-repo-manager/commit/33090f570282feb6866c73f41ab2a90ac6556d43))
* fix bugs from pr 43 ([#45](https://github.com/andrewthetechie/gha-repo-manager/issues/45)) ([b21e432](https://github.com/andrewthetechie/gha-repo-manager/commit/b21e4323ff9409093c0f559dc508232903f538fa))
* **github_nulls:** Better handling of Nulls in GitHub API ([#39](https://github.com/andrewthetechie/gha-repo-manager/issues/39)) ([6744d11](https://github.com/andrewthetechie/gha-repo-manager/commit/6744d11f832826994b3eafb4bb59a0d546a3ac74))

## [1.6.0](https://github.com/andrewthetechie/gha-repo-manager/compare/v1.5.0...v1.6.0) (2023-05-21)


### Features

* ghe support ([#23](https://github.com/andrewthetechie/gha-repo-manager/issues/23)) ([60e128a](https://github.com/andrewthetechie/gha-repo-manager/commit/60e128a42d6a1da90ee5defc9a2b71d1024b4189))


### Documentation

* automated doc update ([7567b6a](https://github.com/andrewthetechie/gha-repo-manager/commit/7567b6a00c07c2976582af89923deec4b4bf8db1))
* cleanup badges ([7fdc028](https://github.com/andrewthetechie/gha-repo-manager/commit/7fdc028972a6d686392fce64491029f099483ab6))

## [1.5.0](https://github.com/andrewthetechie/gha-repo-manager/compare/v1.4.0...v1.5.0) (2023-05-21)


### Features

* Poetry rework ([#19](https://github.com/andrewthetechie/gha-repo-manager/issues/19)) ([2f41b7b](https://github.com/andrewthetechie/gha-repo-manager/commit/2f41b7be4186ae1ffb7865838191234a1df11748))
