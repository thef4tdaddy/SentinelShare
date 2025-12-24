# Changelog

## 1.0.0 (2025-12-23)


### Features

* add clickable ignored status to forward emails and create manual rules ([#48](https://github.com/thef4tdaddy/SentinelShare/issues/48)) ([e8b3f1c](https://github.com/thef4tdaddy/SentinelShare/commit/e8b3f1c32c77effbd9156178b91ffce5354ab59d))
* add customizable email template management with UI editor and comprehensive test coverage ([#39](https://github.com/thef4tdaddy/SentinelShare/issues/39)) ([5010e35](https://github.com/thef4tdaddy/SentinelShare/commit/5010e3536c75bf320b7fa79c43aef076a1b1e466))
* add History page for email processing history and automated runs ([#38](https://github.com/thef4tdaddy/SentinelShare/issues/38)) ([766cf2d](https://github.com/thef4tdaddy/SentinelShare/commit/766cf2de7e831af86bcaad8298ee06498c5de554))
* add source email tracking and UI polish ([386e0b7](https://github.com/thef4tdaddy/SentinelShare/commit/386e0b797daf93e35cceba70abc8366f79aed0ae))
* **auth:** implement single-user authentication (backend middleware + frontend login) ([8eda037](https://github.com/thef4tdaddy/SentinelShare/commit/8eda037a1ad98149552958f98a814348105c29a0))
* implement dynamic versioning and fix lint errors ([92ad321](https://github.com/thef4tdaddy/SentinelShare/commit/92ad3217a04acf2b99ca0eb704ff03cf3425e8f6))
* migrate receipt logic to python and add tests ([0233912](https://github.com/thef4tdaddy/SentinelShare/commit/0233912d60673a07e3fba2fce9a7460d4cd496ef))
* release 1.0 preparation (alembic, version bump, templates) ([f074997](https://github.com/thef4tdaddy/SentinelShare/commit/f074997a327fda9ee2da1ee6011206f1d4eaff92))
* replace system confirm dialogs with accessible modal components ([#50](https://github.com/thef4tdaddy/SentinelShare/issues/50)) ([78f1d2b](https://github.com/thef4tdaddy/SentinelShare/commit/78f1d2b1e39d01b53eebc75c0d51ec139d21b430))
* Retroactive Learning, Coverage Restoration, and Project Polish ([#139](https://github.com/thef4tdaddy/SentinelShare/issues/139)) ([4df2baa](https://github.com/thef4tdaddy/SentinelShare/commit/4df2baa17d2a2ee2fd52ba4b2e729d3f67d85bc6))
* **settings:** add inbox connection testing and visual status indicators ([a6a20a3](https://github.com/thef4tdaddy/SentinelShare/commit/a6a20a3cd30605fcb5a5e0ebb99c3598f311be37))
* **settings:** expose rich email template for editing ([bcfc613](https://github.com/thef4tdaddy/SentinelShare/commit/bcfc6130828de75bf6b61d2523afac2557bc4e05))
* **test:** expand frontend test coverage to 99.51% with Vitest ([#14](https://github.com/thef4tdaddy/SentinelShare/issues/14)) ([29ce048](https://github.com/thef4tdaddy/SentinelShare/commit/29ce048b780e524a36011d3dacb0b6466ef9b3aa))
* UI redesign with new branding and cleaner components ([f920233](https://github.com/thef4tdaddy/SentinelShare/commit/f920233e09380a17ef88d93947bffe2aeed4851d))
* Unified Backend Coverage Restoration and Frontend Modernization ([#91](https://github.com/thef4tdaddy/SentinelShare/issues/91)) ([3f21655](https://github.com/thef4tdaddy/SentinelShare/commit/3f2165527f31cbb70935361ab2896697e3dafd3c))


### Bug Fixes

* accessibility warning in PreferenceList ([d3eccf4](https://github.com/thef4tdaddy/SentinelShare/commit/d3eccf49d3f808277a22f0677dceeaef81f6c33f))
* **frontend:** align activity table columns and add missing date cell ([f5e54ab](https://github.com/thef4tdaddy/SentinelShare/commit/f5e54aba8d32b8dd517ab09acd7b416b947d9945))
* **frontend:** resolve test failures and IDE lint errors ([01924c8](https://github.com/thef4tdaddy/SentinelShare/commit/01924c83113d79eae47605391274be134fef6d3f))
* **frontend:** update code for keying loops and interfaces to support dep upgrades ([42c0f80](https://github.com/thef4tdaddy/SentinelShare/commit/42c0f80624df86a16141ac5d3170a707ddd4f21b))
* improve amazon detection, fix timezone display, and fix forwarding of ignored emails ([01436a6](https://github.com/thef4tdaddy/SentinelShare/commit/01436a6b104378423437c7150115764fd60ba548))
* overhaul CI feedback, fix DB schemas, and resolve all backend type errors ([ecd6328](https://github.com/thef4tdaddy/SentinelShare/commit/ecd6328c95122fa82c56c3ae7246cdd70394c446))
* **prod:** prevent scheduler crash and add configurable lookback ([#122](https://github.com/thef4tdaddy/SentinelShare/issues/122)) ([d408c44](https://github.com/thef4tdaddy/SentinelShare/commit/d408c449918e85f5e900f1102224a67f15c2b4ca))
* resolve all linting issues and cleanup config ([a33f29b](https://github.com/thef4tdaddy/SentinelShare/commit/a33f29b9c21201325a1c42ab621e717891b2a521))
* resolve backend logic bugs and add frontend tests ([7110d5d](https://github.com/thef4tdaddy/SentinelShare/commit/7110d5d26389d13d3ce3d92b0cff704945f878e7))
* resolve linting errors in test files ([c5dfd94](https://github.com/thef4tdaddy/SentinelShare/commit/c5dfd944145ada95aa3f3b22964d149377fd4cc4))
* restore frontend test script and robustify workflow execution ([d0cd3c7](https://github.com/thef4tdaddy/SentinelShare/commit/d0cd3c7958c521ed1ecc5799488491d06246fbf3))
* **settings:** render HTML in email template preview ([53596ae](https://github.com/thef4tdaddy/SentinelShare/commit/53596ae3add21199c502c0253e3e0df237f92f6e))
* update node version to 22.x and install dev deps for build ([9f4bd16](https://github.com/thef4tdaddy/SentinelShare/commit/9f4bd160fc547125b5d5d88c6ea2967d4bd371e9))
* updated ActivityFeed type to allow null category ([3da1604](https://github.com/thef4tdaddy/SentinelShare/commit/3da160413f560eb4508279ec951d082c2ead53bc))


### Miscellaneous Chores

* release 1.0.0 ([ac5cc1e](https://github.com/thef4tdaddy/SentinelShare/commit/ac5cc1e401a0a1e994bf8f773824ff6f39a8c047))
