# Changelog

## [1.2.0](https://github.com/thef4tdaddy/SentinelShare/compare/receipt-forwarder-root-v1.1.0...receipt-forwarder-root-v1.2.0) (2025-12-23)


### Features

* Retroactive Learning, Coverage Restoration, and Project Polish ([#139](https://github.com/thef4tdaddy/SentinelShare/issues/139)) ([4df2baa](https://github.com/thef4tdaddy/SentinelShare/commit/4df2baa17d2a2ee2fd52ba4b2e729d3f67d85bc6))


### Bug Fixes

* overhaul CI feedback, fix DB schemas, and resolve all backend type errors ([ecd6328](https://github.com/thef4tdaddy/SentinelShare/commit/ecd6328c95122fa82c56c3ae7246cdd70394c446))
* **prod:** prevent scheduler crash and add configurable lookback ([#122](https://github.com/thef4tdaddy/SentinelShare/issues/122)) ([d408c44](https://github.com/thef4tdaddy/SentinelShare/commit/d408c449918e85f5e900f1102224a67f15c2b4ca))

## [1.1.0](https://github.com/thef4tdaddy/SentinelShare/compare/receipt-forwarder-root-v1.0.1...receipt-forwarder-root-v1.1.0) (2025-12-18)


### Features

* implement dynamic versioning and fix lint errors ([92ad321](https://github.com/thef4tdaddy/SentinelShare/commit/92ad3217a04acf2b99ca0eb704ff03cf3425e8f6))
* improve visual fidelity of forwarded emails by preserving HTML ([8fc317f](https://github.com/thef4tdaddy/SentinelShare/commit/8fc317f1d2348c618943fea6bcea46caa56a57d0))
* Unified Backend Coverage Restoration and Frontend Modernization ([#91](https://github.com/thef4tdaddy/SentinelShare/issues/91)) ([3f21655](https://github.com/thef4tdaddy/SentinelShare/commit/3f2165527f31cbb70935361ab2896697e3dafd3c))


### Bug Fixes

* **detector:** add renewal keywords and government exemption ([98636da](https://github.com/thef4tdaddy/SentinelShare/commit/98636da397328ce698f0e6bf5c930435b5d3d3d9))
* **detector:** prioritize strong receipt indicators and add 'ordered' keyword ([1289e24](https://github.com/thef4tdaddy/SentinelShare/commit/1289e24470aaa677d943a68ae9da8ec2db38992b))
* isolate scheduler tests from environment variables ([ad999c7](https://github.com/thef4tdaddy/SentinelShare/commit/ad999c74fc9cff26967ad9903ee6a16384d98e70))
* resolve backend test errors and CI coverage targeting ([465a8a5](https://github.com/thef4tdaddy/SentinelShare/commit/465a8a556cf254ea03ec6183b158a278e8dc706f))
* resolve linting errors in test files ([c5dfd94](https://github.com/thef4tdaddy/SentinelShare/commit/c5dfd944145ada95aa3f3b22964d149377fd4cc4))
* restore frontend test script and robustify workflow execution ([d0cd3c7](https://github.com/thef4tdaddy/SentinelShare/commit/d0cd3c7958c521ed1ecc5799488491d06246fbf3))

## [1.0.1](https://github.com/thef4tdaddy/SentinelShare/compare/receipt-forwarder-root-v1.0.0...receipt-forwarder-root-v1.0.1) (2025-12-12)


### Bug Fixes

* add itsdangerous dependency for sessions and finalize agent config ([b38e0d9](https://github.com/thef4tdaddy/SentinelShare/commit/b38e0d985058c5d6a333887f6fabd835fd64f6ac))
* add missing sqlmodel import to migration ([623eff0](https://github.com/thef4tdaddy/SentinelShare/commit/623eff0c95dbb41002d1a3d2722825590489085d))
* generate initial tables migration to resolve missing relation errors ([da2cbf8](https://github.com/thef4tdaddy/SentinelShare/commit/da2cbf8e8ceb8e5817694eeda7a1d923d6366b2c))
* reorder middleware to ensure session works in auth middleware ([180e41e](https://github.com/thef4tdaddy/SentinelShare/commit/180e41e3efdb2f9815cf1e3359a21498b35eb904))

## [1.0.0](https://github.com/thef4tdaddy/SentinelShare/compare/receipt-forwarder-root-v0.2.0...receipt-forwarder-root-v1.0.0) (2025-12-11)


### Features

* **auth:** implement single-user authentication (backend middleware + frontend login) ([8eda037](https://github.com/thef4tdaddy/SentinelShare/commit/8eda037a1ad98149552958f98a814348105c29a0))
* **db:** automate legacy database stamping and migration on startup ([91d9498](https://github.com/thef4tdaddy/SentinelShare/commit/91d94985a8564e77fc5093432f64c44e812f3ea9))
* release 1.0 preparation (alembic, version bump, templates) ([f074997](https://github.com/thef4tdaddy/SentinelShare/commit/f074997a327fda9ee2da1ee6011206f1d4eaff92))


### Bug Fixes

* **settings:** render HTML in email template preview ([53596ae](https://github.com/thef4tdaddy/SentinelShare/commit/53596ae3add21199c502c0253e3e0df237f92f6e))


### Miscellaneous Chores

* release 1.0.0 ([ac5cc1e](https://github.com/thef4tdaddy/SentinelShare/commit/ac5cc1e401a0a1e994bf8f773824ff6f39a8c047))

## [0.2.0](https://github.com/thef4tdaddy/SentinelShare/compare/receipt-forwarder-root-v0.1.0...receipt-forwarder-root-v0.2.0) (2025-12-11)


### Features

* add clickable ignored status to forward emails and create manual rules ([#48](https://github.com/thef4tdaddy/SentinelShare/issues/48)) ([e8b3f1c](https://github.com/thef4tdaddy/SentinelShare/commit/e8b3f1c32c77effbd9156178b91ffce5354ab59d))
* add customizable email template management with UI editor and comprehensive test coverage ([#39](https://github.com/thef4tdaddy/SentinelShare/issues/39)) ([5010e35](https://github.com/thef4tdaddy/SentinelShare/commit/5010e3536c75bf320b7fa79c43aef076a1b1e466))
* add History page for email processing history and automated runs ([#38](https://github.com/thef4tdaddy/SentinelShare/issues/38)) ([766cf2d](https://github.com/thef4tdaddy/SentinelShare/commit/766cf2de7e831af86bcaad8298ee06498c5de554))
* add settings page to web actions ([fbb0eef](https://github.com/thef4tdaddy/SentinelShare/commit/fbb0eefb8954bf8a1449413fc7ef633a4f8bb297))
* add source email tracking and UI polish ([386e0b7](https://github.com/thef4tdaddy/SentinelShare/commit/386e0b797daf93e35cceba70abc8366f79aed0ae))
* email cleaner, smarter spam detection ([90475b2](https://github.com/thef4tdaddy/SentinelShare/commit/90475b29fa0689eb3b06479607ff73592338a51d))
* enable multi-account support via EMAIL_ACCOUNTS env var ([06bb340](https://github.com/thef4tdaddy/SentinelShare/commit/06bb340b354b99136cee2455374d71d193aa6742))
* github action over uptime robot ([d055387](https://github.com/thef4tdaddy/SentinelShare/commit/d0553871dba1535d1c8a38db9741b7afda9ae17b))
* immediate stop protection ([c610bca](https://github.com/thef4tdaddy/SentinelShare/commit/c610bcacea280d64d29400d3e2fa1183dedd2e86))
* implement web-based action links with signature verification ([ca6a5e7](https://github.com/thef4tdaddy/SentinelShare/commit/ca6a5e735ed1db9c15b4186e76255d82dd1400ad))
* inital app setup ([8fc7c1e](https://github.com/thef4tdaddy/SentinelShare/commit/8fc7c1e2555c266284c390ebaef6a36f4b7be3fa))
* manual forwarding ([1fa0625](https://github.com/thef4tdaddy/SentinelShare/commit/1fa0625afdbafd41453e18dafbe83f523ddf5a30))
* migrate receipt logic to python and add tests ([0233912](https://github.com/thef4tdaddy/SentinelShare/commit/0233912d60673a07e3fba2fce9a7460d4cd496ef))
* process all api call ([d5d106f](https://github.com/thef4tdaddy/SentinelShare/commit/d5d106fdd1c9bcd55837525afd06a5e152f145df))
* removal of forwarding to other emails and footer for notice on how to deal with the forwarder ([94f99fe](https://github.com/thef4tdaddy/SentinelShare/commit/94f99fe71490e764b86218af472bab8a95ba5a25))
* replace system confirm dialogs with accessible modal components ([#50](https://github.com/thef4tdaddy/SentinelShare/issues/50)) ([78f1d2b](https://github.com/thef4tdaddy/SentinelShare/commit/78f1d2b1e39d01b53eebc75c0d51ec139d21b430))
* **settings:** add inbox connection testing and visual status indicators ([a6a20a3](https://github.com/thef4tdaddy/SentinelShare/commit/a6a20a3cd30605fcb5a5e0ebb99c3598f311be37))
* **settings:** expose rich email template for editing ([bcfc613](https://github.com/thef4tdaddy/SentinelShare/commit/bcfc6130828de75bf6b61d2523afac2557bc4e05))
* **test:** expand frontend test coverage to 99.51% with Vitest ([#14](https://github.com/thef4tdaddy/SentinelShare/issues/14)) ([29ce048](https://github.com/thef4tdaddy/SentinelShare/commit/29ce048b780e524a36011d3dacb0b6466ef9b3aa))
* **test:** expand Python backend test coverage from 27% to 81% ([#15](https://github.com/thef4tdaddy/SentinelShare/issues/15)) ([8724541](https://github.com/thef4tdaddy/SentinelShare/commit/872454136bcbd3b329f3982fec53ac4ebf721556))
* track scheduler execution history including zero-email runs ([#41](https://github.com/thef4tdaddy/SentinelShare/issues/41)) ([6b2d569](https://github.com/thef4tdaddy/SentinelShare/commit/6b2d5698fb914ec05be22f59930673d375b43039))
* UI redesign with new branding and cleaner components ([f920233](https://github.com/thef4tdaddy/SentinelShare/commit/f920233e09380a17ef88d93947bffe2aeed4851d))
* updated catching ([97c0274](https://github.com/thef4tdaddy/SentinelShare/commit/97c0274682f673cb0330facb1c930f1ee835c949))
* use first EMAIL_ACCOUNT as default sender if SENDER_EMAIL is missing ([8daf2de](https://github.com/thef4tdaddy/SentinelShare/commit/8daf2de9d353970bf741d1198fbb625b5980afc5))


### Bug Fixes

* 2 files in one ([6a70710](https://github.com/thef4tdaddy/SentinelShare/commit/6a70710b4cd1e37518e2bf6899c599b676e048b7))
* accessibility warning in PreferenceList ([d3eccf4](https://github.com/thef4tdaddy/SentinelShare/commit/d3eccf49d3f808277a22f0677dceeaef81f6c33f))
* auto-infer smtp server from email accounts config ([e919f07](https://github.com/thef4tdaddy/SentinelShare/commit/e919f07e75fe38747b1b433c17c50deb41189068))
* better error handling ([3d72005](https://github.com/thef4tdaddy/SentinelShare/commit/3d720058b3afb66746b75a28c007cfb523077664))
* changes to email client file ([506cd47](https://github.com/thef4tdaddy/SentinelShare/commit/506cd478783264a8b2759236d4c33cd057382f9c))
* changing imports ([30e7aae](https://github.com/thef4tdaddy/SentinelShare/commit/30e7aae4b88a74fc5e039ce290b88cc1b4465cd1))
* changing it to every 2 hours ([22ad764](https://github.com/thef4tdaddy/SentinelShare/commit/22ad764ee87eed8159f0a35a7667caf786c171f9))
* changing vercel cron job ([3f99182](https://github.com/thef4tdaddy/SentinelShare/commit/3f99182f33ea0d8089c7aeb811bece52ea76fba1))
* **ci:** remove duplicate permissions key in workflow ([f76eb16](https://github.com/thef4tdaddy/SentinelShare/commit/f76eb160be5e80c21c9d1750fb404d14f2033a04))
* code scanning alert no. 7: Reflected server-side cross-site scripting ([2ab6f2a](https://github.com/thef4tdaddy/SentinelShare/commit/2ab6f2a82ba247d1f5074e93a65ae2cdfed4117d))
* create transport error ([d28b7dd](https://github.com/thef4tdaddy/SentinelShare/commit/d28b7dd9ebe00606720f2f4c294949046b429861))
* **detection:** allow amazon order confirmations and subscribe & save ([18a52ab](https://github.com/thef4tdaddy/SentinelShare/commit/18a52abe1ad75ebb9ca6ecb41161df746e361f41))
* **forwarding:** robust fetching with case-insensitive matching and universal fallback ([169166e](https://github.com/thef4tdaddy/SentinelShare/commit/169166ec69759221caea8982d8788280e11921c0))
* **frontend:** align activity table columns and add missing date cell ([f5e54ab](https://github.com/thef4tdaddy/SentinelShare/commit/f5e54aba8d32b8dd517ab09acd7b416b947d9945))
* **frontend:** resolve test failures and IDE lint errors ([01924c8](https://github.com/thef4tdaddy/SentinelShare/commit/01924c83113d79eae47605391274be134fef6d3f))
* **frontend:** update code for keying loops and interfaces to support dep upgrades ([42c0f80](https://github.com/thef4tdaddy/SentinelShare/commit/42c0f80624df86a16141ac5d3170a707ddd4f21b))
* health check before running workflow ([1b21ab4](https://github.com/thef4tdaddy/SentinelShare/commit/1b21ab42f466c9c04a4369df7af53da610abca69))
* improve amazon detection, fix timezone display, and fix forwarding of ignored emails ([01436a6](https://github.com/thef4tdaddy/SentinelShare/commit/01436a6b104378423437c7150115764fd60ba548))
* improve imap fetch (BODY[]), increase limit, and robust json parsing ([01472ea](https://github.com/thef4tdaddy/SentinelShare/commit/01472ea517480e6ea96da25975f7445cade03c0f))
* include multi-account emails in self-detection logic ([1b7552c](https://github.com/thef4tdaddy/SentinelShare/commit/1b7552ca7228df82c820d899d2e0488a0c92b322))
* make email config parsing robust to single quotes ([afcae14](https://github.com/thef4tdaddy/SentinelShare/commit/afcae142a13a54a4c17c6f6f4ef5c73bf1ac5d14))
* manual forward is now uptime robot safe ([0ff8d6a](https://github.com/thef4tdaddy/SentinelShare/commit/0ff8d6aaa455c5251660b8d431fd2ba5f10c97a0))
* more checks ([a69c949](https://github.com/thef4tdaddy/SentinelShare/commit/a69c9491c996697bf22b078a3e4242dadf890a3a))
* more resilent check emails and a quick test api function ([05eef3a](https://github.com/thef4tdaddy/SentinelShare/commit/05eef3a77f3f4b6e2b692e08265f30e2688b7b04))
* no KV ([62fbb0c](https://github.com/thef4tdaddy/SentinelShare/commit/62fbb0c4437c9e0437f44fc42cecd5a3b0e01ae0))
* notion db not correct in code, its actually seperate dbs ([216ec5a](https://github.com/thef4tdaddy/SentinelShare/commit/216ec5a2f35de5f7e0768dc93bef10c370e71b41))
* notion issues ([9a5d2ed](https://github.com/thef4tdaddy/SentinelShare/commit/9a5d2ed94c104991a1da930140e93be2fa22806f))
* potential fix for code scanning alert no. 4: Incomplete URL substring sanitization ([#42](https://github.com/thef4tdaddy/SentinelShare/issues/42)) ([5ae17c1](https://github.com/thef4tdaddy/SentinelShare/commit/5ae17c146a80f3c53f5e18a2b1f58222551ae918))
* potential fix for code scanning alert no. 6: Information exposure through an exception ([#47](https://github.com/thef4tdaddy/SentinelShare/issues/47)) ([f713b37](https://github.com/thef4tdaddy/SentinelShare/commit/f713b376ae0f29cb7f498eb52d5af5429b4665b9))
* removal of amazon shipping confirmations ([6939da5](https://github.com/thef4tdaddy/SentinelShare/commit/6939da503d64aaa863fa7109bcbeb517e22bbf31))
* removing vercel cron job, going to a free cron job ([46a8c01](https://github.com/thef4tdaddy/SentinelShare/commit/46a8c016506fecd2da0bd2691545b109f4011c83))
* resolve all linting issues and cleanup config ([a33f29b](https://github.com/thef4tdaddy/SentinelShare/commit/a33f29b9c21201325a1c42ab621e717891b2a521))
* resolve backend logic bugs and add frontend tests ([7110d5d](https://github.com/thef4tdaddy/SentinelShare/commit/7110d5d26389d13d3ce3d92b0cff704945f878e7))
* resolve security alerts (CVEs + credential logging) and logic bug ([f3fa25c](https://github.com/thef4tdaddy/SentinelShare/commit/f3fa25ce2811bb58887f49b656b50d807446388c))
* revert requirements.txt to root for heroku buildpack detection ([7be8fc8](https://github.com/thef4tdaddy/SentinelShare/commit/7be8fc8f8035f3eb5f4668295944ab5ecae9c985))
* scan last 20 emails (read or unread) to catch opened receipts ([2539f49](https://github.com/thef4tdaddy/SentinelShare/commit/2539f49e27aaf06e0c67d38b33b2f14dcef3cff9))
* timezone issues, catch-all email fetching, and missing runs history ([61e3bb7](https://github.com/thef4tdaddy/SentinelShare/commit/61e3bb7dd30db078570a606d5c45a5926dd1d710))
* update node version to 22.x and install dev deps for build ([9f4bd16](https://github.com/thef4tdaddy/SentinelShare/commit/9f4bd160fc547125b5d5d88c6ea2967d4bd371e9))
* updated ActivityFeed type to allow null category ([3da1604](https://github.com/thef4tdaddy/SentinelShare/commit/3da160413f560eb4508279ec951d082c2ead53bc))
* updated the database ([36f571f](https://github.com/thef4tdaddy/SentinelShare/commit/36f571f085b9c6489de0e0af3222aac9ae84f140))
* vercel KV not required now ([e01bfa3](https://github.com/thef4tdaddy/SentinelShare/commit/e01bfa3c84b1757da78d573f0ce83ac7e470e8f3))
