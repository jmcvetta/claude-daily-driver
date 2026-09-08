# Changelog

## [0.9.0](https://github.com/jmcvetta/claude-daily-driver/compare/v0.8.0...v0.9.0) (2026-09-08)


### Features

* **review-cycle:** cap the level a rule may select at high ([#94](https://github.com/jmcvetta/claude-daily-driver/issues/94)) ([bb80032](https://github.com/jmcvetta/claude-daily-driver/commit/bb80032059fcb9905ef46ce4a7a562e4b420a7f2))

## [0.8.0](https://github.com/jmcvetta/claude-daily-driver/compare/v0.7.0...v0.8.0) (2026-09-07)


### Features

* **constitution:** drop five sections and the delivery token ([#91](https://github.com/jmcvetta/claude-daily-driver/issues/91)) ([cf8bc8b](https://github.com/jmcvetta/claude-daily-driver/commit/cf8bc8be7c5ef33177e03ab0f69f8b857abed108))
* **undertake:** name the branch in the claim comment ([#92](https://github.com/jmcvetta/claude-daily-driver/issues/92)) ([85e7869](https://github.com/jmcvetta/claude-daily-driver/commit/85e7869bca839dde5146fff2c5abcf0fa0365c4f))

## [0.7.0](https://github.com/jmcvetta/claude-daily-driver/compare/v0.6.0...v0.7.0) (2026-09-07)


### Features

* **constitution:** write in Simplified Technical English ([#82](https://github.com/jmcvetta/claude-daily-driver/issues/82)) ([6ef6bc2](https://github.com/jmcvetta/claude-daily-driver/commit/6ef6bc2f328aee09261b3ac1d92e09d1f0840159))

## [0.6.0](https://github.com/jmcvetta/claude-daily-driver/compare/v0.5.0...v0.6.0) (2026-09-07)


### Features

* **undertake:** claim the issue before the branch is cut ([#79](https://github.com/jmcvetta/claude-daily-driver/issues/79)) ([8354f33](https://github.com/jmcvetta/claude-daily-driver/commit/8354f3391dacfc93d9932d39b3bf1feb86325f31))


### Bug Fixes

* **review-cycle:** name medium, escalate to xhigh, never select max ([#76](https://github.com/jmcvetta/claude-daily-driver/issues/76)) ([1397ad3](https://github.com/jmcvetta/claude-daily-driver/commit/1397ad33b8c1e51c2140e5a73d5aade7c81efa6c))

## [0.5.0](https://github.com/jmcvetta/claude-daily-driver/compare/v0.4.0...v0.5.0) (2026-09-07)


### Features

* **review-cycle:** extract the review-and-answer round from undertake ([#72](https://github.com/jmcvetta/claude-daily-driver/issues/72)) ([103c44b](https://github.com/jmcvetta/claude-daily-driver/commit/103c44b45b6e8d8a7844e20cc319bf6796a8256d))
* **undertake:** open an issue where the work has none ([#71](https://github.com/jmcvetta/claude-daily-driver/issues/71)) ([2d4db15](https://github.com/jmcvetta/claude-daily-driver/commit/2d4db15bad77a1e1cea4006c5ee08e724bc25159))

## [0.4.0](https://github.com/jmcvetta/claude-daily-driver/compare/v0.3.1...v0.4.0) (2026-09-07)


### Features

* **skills:** split the Conventional Commits type decision out of pr-title ([#61](https://github.com/jmcvetta/claude-daily-driver/issues/61)) ([4faae8d](https://github.com/jmcvetta/claude-daily-driver/commit/4faae8d91f6c363c0104325d972b910cbc0476e8))

## [0.3.1](https://github.com/jmcvetta/claude-daily-driver/compare/v0.3.0...v0.3.1) (2026-09-07)


### Bug Fixes

* move the Terraform-shop review rules to project memory ([#55](https://github.com/jmcvetta/claude-daily-driver/issues/55)) ([8b9a41d](https://github.com/jmcvetta/claude-daily-driver/commit/8b9a41deb017c88ccdacc6b3242c1b14c3ef717c))

## [0.3.0](https://github.com/jmcvetta/claude-daily-driver/compare/v0.2.0...v0.3.0) (2026-09-07)


### Features

* add the undertake skill, taking an issue to a ready pull request ([#49](https://github.com/jmcvetta/claude-daily-driver/issues/49)) ([72c631d](https://github.com/jmcvetta/claude-daily-driver/commit/72c631d0e4cbae31382259767c822524a172ee2b))


### Bug Fixes

* **agents:** inline the planning severity rubric into planning-fitness-reviewer ([#54](https://github.com/jmcvetta/claude-daily-driver/issues/54)) ([f166c87](https://github.com/jmcvetta/claude-daily-driver/commit/f166c87b7211c56a1c0c05c3430e56fc175a3088))
* **review:** correct the depth table's precedence and its worked example ([#39](https://github.com/jmcvetta/claude-daily-driver/issues/39)) ([ce65c0c](https://github.com/jmcvetta/claude-daily-driver/commit/ce65c0cbafe31aa278c239a7be9e0eb3c66b662b))

## [0.2.0](https://github.com/jmcvetta/claude-daily-driver/compare/v0.1.0...v0.2.0) (2026-09-07)


### Features

* add the session-title skill ([#41](https://github.com/jmcvetta/claude-daily-driver/issues/41)) ([0a98c36](https://github.com/jmcvetta/claude-daily-driver/commit/0a98c36391e0297b0867a49934355bab3bfa1bf9))
* **judgement-call:** the gate before a choice is put to the user ([#44](https://github.com/jmcvetta/claude-daily-driver/issues/44)) ([57abdf2](https://github.com/jmcvetta/claude-daily-driver/commit/57abdf2b6260f40959bd33ac95d56a61bae9e946))
* retire pr-threads and review from the shipped skill panel ([#50](https://github.com/jmcvetta/claude-daily-driver/issues/50)) ([03fc4b4](https://github.com/jmcvetta/claude-daily-driver/commit/03fc4b4bfd11cb468c88ab9d2bf6c712c799e5d3))

## 0.1.0 (2026-09-06)


### Features

* add Makefile with git_sync target ([#4](https://github.com/jmcvetta/claude-daily-driver/issues/4)) ([bc9ff38](https://github.com/jmcvetta/claude-daily-driver/commit/bc9ff385dedef8692a2c8660f63364d09ab77d4d))
* deliver the constitution to sessions and subagents ([#31](https://github.com/jmcvetta/claude-daily-driver/issues/31)) ([f4c57d1](https://github.com/jmcvetta/claude-daily-driver/commit/f4c57d189073d00447de2a56247c8322a06a9e81))
* **issue-deps:** skill for GitHub issue relationships, with a curl script ([#26](https://github.com/jmcvetta/claude-daily-driver/issues/26)) ([825c8ff](https://github.com/jmcvetta/claude-daily-driver/commit/825c8ffda493eb338d22e3b2a2e06e04c53fb69e))
* manage repository settings with OpenTofu ([#5](https://github.com/jmcvetta/claude-daily-driver/issues/5)) ([9b1ce0d](https://github.com/jmcvetta/claude-daily-driver/commit/9b1ce0df6b005a52187cef41d3eebc7a7ce9f45c))
* **pr-threads:** the review-thread lifecycle skill ([#25](https://github.com/jmcvetta/claude-daily-driver/issues/25)) ([11a4588](https://github.com/jmcvetta/claude-daily-driver/commit/11a458894bd11439434cb13cfe34d0ff2ab96b12))
* **review:** collapse four review verbs into one skill ([#28](https://github.com/jmcvetta/claude-daily-driver/issues/28)) ([d59021d](https://github.com/jmcvetta/claude-daily-driver/commit/d59021d81d01f03c5dff97777fa6c53da24f0a1f))
* scaffold the plugin with the pr skill and an anti-license ([#3](https://github.com/jmcvetta/claude-daily-driver/issues/3)) ([ea23bb0](https://github.com/jmcvetta/claude-daily-driver/commit/ea23bb038b5d091fff3c1c0aae3cd3a93e97332e))
* **skills:** split pr into pr, pr-title and pr-body ([#27](https://github.com/jmcvetta/claude-daily-driver/issues/27)) ([4440477](https://github.com/jmcvetta/claude-daily-driver/commit/44404777a30d42c1476b46cbb010c4e9b3fa6874))
