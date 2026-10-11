# Daily Office, Book of Common Prayer 2019 (https://www.dailyoffice2019.com)

This project is used to build the website https://www.dailyoffice2019.com. It is a Django application written in
Python (to be installed in a development environment). It is used to produce a static html and javascript site which
can then be deployed to the production environment.

## WHAT IS THE SITE FOR?

The site invites you to join with Christians around the world in praying with the Church, at any time or in any place
you may find yourself. It makes it easy to pray daily morning, midday, evening, and compline (bedtime) prayer without
flipping pages, searching for scripture readings or calendars, or interpreting rubrics. The prayers are presented from
The Book of Common Prayer (2019) of the Anglican Church in North America and reflect the ancient patterns of daily
prayer Christians have used since the earliest days of the church.

## WHAT IS THE DAILY OFFICE?

Daily Morning Prayer and Daily Evening Prayer are the established rites (offices) by which, both corporately and
individually, God’s people annually encounter the whole of the Holy Scriptures, daily confess their sins and praise
Almighty God, and offer timely thanksgivings, petitions, and intercessions.

## Contributing

Pull requests are welcome. Take a look at the Github [issues](https://github.com/blocher/dailyoffice2019/issues) and
see where you might help out. Updates to documentation and tests (both of which are largely missing) are also welcome.

### Requirements

- Python 3.12 or newer (Django 6.1 supports Python 3.12–3.14)
- Node 22.22.2+ within Node 22, or Node 24.15.0+; Node 24 LTS is recommended
- PostgreSQL
- Memcached 1.6

The project is known to work with these versions, although it may also work with more recent versions.

### Dependency review and follow-up (October 11, 2026)

The consolidation in PR #250 started from master `909f9c277`, after direct dependency upgrade
`dc53115e3`. The Firebase/TypeScript follow-up starts from `073c1f78a`, preserving the newer deployment
workflow. The original inventory covered four npm manifests, three npm lockfiles, 96 numbered Python
requirements, three Git requirements, pre-commit and Android/Swift manifests and the Swift lockfile.
Only the app npm project remains. It now has 90 direct dependency entries and 1,105 locked package
entries; all 870 public package names were rechecked against npm metadata. Ten configured FontAwesome
lock entries remain private-registry unverified. There are 94 numbered Python requirements after
removing django-webpack-loader and unused rake-nltk, plus the same three Git requirements. This is an
inventory and available-advisory review, not an exhaustive security audit.

Ownership and consolidation:

- `app/` is the active Vue/Vite/Capacitor frontend. `@element-plus/icons-vue` is now explicit there,
  matching direct imports; the browser plugin was already declared there.
- The root project had no entrypoint, scripts, or workspaces. Its npm manifest, lockfile, and 922
  tracked generated `node_modules` files are removed. Run frontend installation from `app/`.
- Unused app `update`, `install`, and duplicate `npm` library dependencies are removed after source
  and script searches found no consumers. npm remains the CLI. This removes 911 app lock entries,
  including bundled npm 12.2.0's vulnerable brace-expansion 5.0.9.
- The authorized route retirement supersedes the earlier site exception: `/new/office/morning_prayer/<date>`
  is unregistered, both HTML prayer-display classes and their converter are removed, and the global
  production 404 now returns JSON (`{"detail": "Not found."}`). `/api/v1` prayer routes remain.
- Site's npm manifest, lockfile, Webpack stats, Babel/PostCSS/Webpack/Vue/Tailwind/ESLint configurations,
  and obsolete HTML display/404 templates are removed. The historical deployment script no longer
  installs npm packages or invokes Webpack. The current deployment workflow retains Django `collectstatic`.
- No live templates require `webpack_loader`; its app registration, settings and Python requirement
  are removed. Dormant legacy templates retain their content with obsolete bundle tags removed.
  Archived source assets remain; this cleanup does not broadly delete backend JavaScript or templates.
- Patrons pages, Bible study and its standalone assets, Python-rendered email previews and CSS, Word
  downloads, Swagger/ReDoc, admin/editor assets, static serving and media handling remain. Python MJML
  still uses the configured HTTP backend. The empty email npm manifest and obsolete Yarn config are gone.
- **The previous legacy asset rebuild/release guidance is superseded.** The final backend has no Node
  build or Webpack bundle consumer. The intermediate isolated legacy build only tested the earlier
  retained dependency graph and never replaced committed/deployed assets. No asset rebuild is required
  for the retired routes; the Python changes take effect through the normal release process. Nothing
  was deployed and production infrastructure was not changed.

Dependabot and compatibility:

- Supersedes #247/#248 by eliminating root source-map-js 1.2.1 and Vue/server-renderer 3.5.13.
  App source-map-js is 1.2.2 and Vue/server-renderer are 3.5.43.
- Supersedes #249 by removing unused `split-html` and its Mocha tree. Before consolidation,
  brace-expansion was refreshed to 1.1.21 and the 34 optional CSS entries pruned by #249 were preserved.
  Their owning npm MJML package was subsequently removed for a demonstrated lack of local consumers.
- Every remaining brace-expansion copy is 1.1.21, 2.1.7, or 5.0.12, within its parent's range.
  No bundled npm remains. No forced audit fixes were applied. The only deliberate peer-range override
  is the user-approved Firebase 13 exception described below.
- TypeScript is now 7.0.2. Unused `@vue/eslint-config-typescript` and `@typescript-eslint/parser`
  direct dependencies and unused hook compiler/parser dependencies are removed. The active ESLint
  config never selected them. No TypeScript 6 compatibility layer or native bridge is needed by the
  remaining tooling. `npm run typecheck` uses strict TypeScript 7 checking for standalone `src/**/*.ts`;
  it does not check Vue templates or JavaScript. Vite separately transpiles TypeScript with Oxc.
- Firebase is now 13.0.0 with a narrowly scoped `@capacitor-firebase/analytics` override referencing
  the direct `$firebase` dependency. Analytics 8.5.2 declares optional peer `^12.6.0`, not an exact
  12.19 requirement. This is an experimental compatibility exception, not upstream support: Firebase
  12.19 and 13 contain identical Analytics 0.10.25 APIs, plugin source passes strict TypeScript 7
  checking, and a public Vue/Vite smoke build passes. Firebase 13's documented breaking AI APIs are
  unused here. Clean isolated peer resolution/install succeeds without force/legacy-peer flags.
  Native plugin calls still use native Firebase SDKs; npm Firebase 13 does not upgrade iOS Firebase.
  The Firebase/gRPC high advisory chain remains and still needs a separately tested fix.
- Unused `vue-mailchimp-subscribe` has no source, script, hook or dynamic consumer. Unused scoped-CSS
  plugin registration has no enabled rules; it and its SCSS/Stylus parser peers are removed from app
  and hook dependencies. Actual Sass/SCSS support remains. An old optional Vite Stylus peer survived
  ordinary npm removal; its optional node was omitted from the temporary lock seed, then npm
  regenerated/pruned the lock normally. No Stylus source or configuration consumer was found.
- Unused rake-nltk is removed after Python/reference and dynamic-import checks. Fresh resolution
  contains neither rake-nltk nor NLTK, eliminating the previously unpatched NLTK advisory.
- `@achrinza/node-ipc` 10.1.11 remains because `latest` points to older 9.2.10; the Vue 3 `vue-meta`
  alpha remains because stable 2.4.0 targets Vue 2. Indirect node-ipc under the Vue CLI native plugin
  still emits engine warnings. Replace that plugin with tested Capacitor CLI scripts before removal.
- FontAwesome versions and configuration remain unchanged. Metadata refresh and clean install return
  HTTP 403. Stored credentials were not read, printed, copied, configured, or transmitted.
- The remaining 94 numbered Python requirements already name current PyPI releases. Clean resolution updates
  indirect packages too; `pip list --outdated` is empty. There is no Python lockfile: `>=` requirements
  and three moving Git references do not freeze future installs. Keep the django-inlinecss fork.
- Active pre-commit versions were already current. Initializing its local Git hook package used the
  saved npm 10 CLI with Node 24 after npm 11 returned `EALLOWGIT`; no security settings changed.

Validation (saved environment: Node 24.19.0 and Python 3.12.14):

- The final backend no longer has npm manifests or an asset build step. The prior isolated legacy
  build passed during the intermediate review; that result does not describe the final dependency set.
- Ten new regression tests pass with `DEBUG=False` and django-webpack-loader uninstalled: unmatched
  and view-raised JSON 404s, removed prayer display paths, retained JSON prayer registration, patrons,
  Bible study, mocked external MJML email rendering, valid Word downloads, API docs, and admin/editor assets.
- Real `collectstatic` into a temporary directory passes, including Django admin, CKEditor and Swagger
  JavaScript/CSS. Repository static settings, serving and standalone page assets remain unchanged.
- Clean complete Python requirements install; `pip check` and Django checks pass. 246 backend tests
  execute: 243 pass, three audio assertions fail (`3 != 4`). The two failing
  `ReadingAudioCompletenessTests` cases and the ElevenLabs case in
  `ReadingVoiceTests.test_complete_reading_keeps_one_voice_through_audio_assembly` also fail in the
  saved older Django environment. These failures predate the route cleanup; the new route regressions pass.
- App clean install is blocked by HTTP 403 fetching
  `https://npm.fontawesome.com/@fortawesome/vue-fontawesome/-/vue-fontawesome-3.3.3.tgz`.
  Normal lint, Vitest, Vite build, and Cypress commands cannot run because their executables are absent
  after installation fails. The actual TypeScript 7 typecheck passes using the independently installed
  public compiler against the committed tsconfig; this does not prove a complete app install/build.
  The smallest safe unblock is for a maintainer to run this branch's `npm ci` from `app/` in an
  existing developer or CI environment already authorized for `npm.fontawesome.com`, then run the
  frontend checks there. No credentials need to be shared with the agent. HTTP 403 alone does not
  establish whether registry authorization or this saved environment's access policy caused the denial;
  no new credentials, permissions, or registry-routing workaround are requested for this environment.
- ESLint 10 in the independent public validation environment, using the final app config and
  temporary copies of app source, reports the same 18 existing `no-useless-assignment` errors after
  formatting those copies. No parser crash occurs; repository app source is unchanged.
- A clean public-only compatibility fixture with final lint/Vite versions, TypeScript 7, and the
  published Analytics plugin plus Firebase 13 scoped override builds successfully (26 modules).
  This excludes private icons and is not a full application build.
- Shell syntax, JSON parsing, manifest/lock agreement, staged pre-commit hooks, and `git diff --check`
  pass. Staged pre-commit hooks initialize successfully with the reduced dependency set. Full app
  lint, Vitest and Cypress remain blocked by clean install; lifecycle scripts, native builds, browser
  tests, live providers, and deployment are unvalidated for this follow-up.

Security reports at review time:

| Dependency set | Before | Final |
| --- | --- | --- |
| Root npm | Not measured before | Removed; intermediate clean audit: 0 |
| App npm | Original: 91; PR #250: 32 (3 critical, 12 high, 17 moderate) | 20: 3 critical, 8 high, 9 moderate |
| Site npm | 63: 3 critical, 43 high, 15 moderate, 2 low | Removed (intermediate minimized audit: 0) |
| Fresh Python environment | PR #250: 1 high, unpatched NLTK advisory | 0 known advisories across 209 installed distributions |

Counts include propagated parent reports and do not prove each affected package is exploitable here.
The remaining critical npm reports involve `request`, `form-data`, and older `tar` under native asset
tooling. Latest direct releases still constrain these children; migrate or replace their owners instead
of overriding incompatible majors. Other findings cover Firebase/grpc, Xcode/project tooling,
and the typography build plugin. Mailchimp/query-string, Stylus/CSS parsing and TypeScript-lint
brace/glob reports are removed with their unused owners. Tooling vulnerabilities still matter
in developer/build processes. Manifest sections distinguish runtime and tooling, although some tools
were historically listed as runtime. The only remaining app bundles are Tailwind’s optional WebAssembly runtime dependencies; npm bundles are removed. These six packages are shipped within the upstream oxide tarball: `@emnapi/core 1.11.1`, `@emnapi/runtime 1.11.1`, `@emnapi/wasi-threads 1.2.2`, `@napi-rs/wasm-runtime 1.1.4`, `@tybys/wasm-util 0.10.2`, `tslib 2.8.1`. Updating their contents requires an upstream oxide release; lockfile overrides cannot rewrite a tarball.

The fresh Python audit finds no known advisories. The previous NLTK issue is removed with unused
rake-nltk; this does not constitute a code audit of the moving Git forks.

| Reported app package | Severity | Locked affected versions | Remaining owner / migration |
| --- | --- | --- | --- |
| `@capacitor-firebase/analytics` | high | 8.5.2 | app direct ^8.5.2 |
| `@capacitor/assets` | high | 3.0.5 | app direct ^3.0.5 |
| `@capacitor/cli` | high | 5.7.8, 8.5.3 | app direct ^8.5.3, @capacitor-community/electron 5.0.1 >=5.4.0, @capacitor/assets 3.0.5 ^5.3.0 |
| `@firebase/firestore` | high | 4.18.0 | @firebase/firestore-compat 0.4.15 4.18.0, firebase 13.0.0 4.18.0 |
| `@firebase/firestore-compat` | high | 0.4.15 | firebase 13.0.0 0.4.15 |
| `@grpc/grpc-js` | high | 1.9.16 | @firebase/firestore 4.18.0 ~1.9.0 |
| `@tailwindcss/typography` | moderate | 0.5.20 | app direct ^0.5.20 |
| `@trapezedev/project` | moderate | 7.1.10 | @capacitor/assets 3.0.5 ^7.0.10 |
| `@vue/cli-shared-utils` | moderate | 4.5.19 | vue-cli-plugin-capacitor 2.0.1 ^4.5.4 |
| `firebase` | high | 13.0.0 | app direct ^13.0.0, @capacitor-firebase/analytics 8.5.2 peer ^12.6.0 (overridden to $firebase) |
| `form-data` | critical | 2.3.3 | request 2.88.2 ~2.3.2 |
| `postcss-selector-parser` | moderate | 6.0.10 | @tailwindcss/typography 0.5.20 6.0.10 |
| `qs` | moderate | 6.5.5 | request 2.88.2 ~6.5.2 |
| `request` | critical | 2.88.2 | @vue/cli-shared-utils 4.5.19 ^2.88.2 |
| `sharp` | high | 0.32.6 | @capacitor/assets 3.0.5 0.32.6 |
| `tar` | critical | 6.2.1 | @capacitor/cli 5.7.8 ^6.1.11 |
| `tough-cookie` | moderate | 2.5.0 | request 2.88.2 ~2.5.0 |
| `uuid` | moderate | 3.4.0, 7.0.3 | request 2.88.2 ^3.3.2, xcode 3.0.1 ^7.0.3 |
| `vue-cli-plugin-capacitor` | moderate | 2.0.1 | app direct ^2.0.1 |
| `xcode` | moderate | 3.0.1 | @capacitor/cli 8.5.3 ^3.0.1, @trapezedev/project 7.1.10 ^3.0.1 |

Native pins retained for a coordinated platform migration:

Xcode/Swift is unavailable and app installation is blocked. Do not hand-edit Capacitor-generated
Swift projects or independently select latest Firebase children. Swift's manifest and lock still pin
Capacitor 8.1.0 while npm uses 8.5.3: reconcile with supported `cap sync`, resolve, and build on macOS.
Android needs a tested Gradle/AGP/SDK migration. No native vulnerability scan was available, so these
pins are not asserted secure. Numeric Swift tags are observations, not compatibility assurances.

| Native dependency | Retained | Latest stable metadata / numeric upstream tag |
| --- | --- | --- |
| Swift `abseil-cpp-binary` | 1.2024072200.0 | 1.2025051202.0 |
| Swift `app-check` | 11.2.0 | 12.0.0 |
| Swift `capacitor-swift-pm` | 8.1.0 | 8.5.3 |
| Swift `firebase-ios-sdk` | 12.9.0 | 13.0.1 |
| Swift `google-ads-on-device-conversion-ios-sdk` | 3.2.0 | 3.7.0 |
| Swift `googleappmeasurement` | 12.8.0 | 13.0.1 |
| Swift `googledatatransport` | 10.1.0 | 10.1.1 |
| Swift `googleutilities` | 8.1.0 | 8.1.4 |
| Swift `grpc-binary` | 1.69.0 | 1.83.1 |
| Swift `gtm-session-fetcher` | 4.5.0 | 5.3.1 |
| Swift `nanopb` | 2.30910.0 | 2.30910.1 |
| Swift `promises` | 2.4.0 | 2.4.1 |
| Android `androidx.activity:activity` | 1.11.0 | 1.13.0 |
| Android `androidx.appcompat:appcompat` | 1.7.1 | 1.8.0 |
| Android `androidx.core:core` | 1.17.0 | 1.19.1 |
| Android `androidx.fragment:fragment` | 1.8.9 | 1.9.1 |
| Android `androidx.webkit:webkit` | 1.14.0 | 1.17.1 |
| Android `com.android.tools.build:gradle` | 8.13.0 | 9.4.1 |
| Android `com.google.gms:google-services` | 4.4.4 | 4.5.0 |
| Gradle wrapper | 8.14.3 | 9.8.1 |
| Cordova Android | 14.0.1 | 15.1.0 |

`site/runtime.txt` still declares Python 3.7, incompatible with Django 6.1. Use a supported
interpreter for deployment; this follow-up does not alter production Python or native infrastructure.
This PR edits repository install scripts but does not deploy or modify server infrastructure.

<details>
<summary>Retained npm versions differing from each package's public latest tag</summary>

Existing parent ranges and peers are preserved. Migrate the named owners and validate runtime/tooling
behavior before lifting those constraints. Direct exceptions are explained above. A blank cell means
no below-tag version in the app lockfile. “None reported” refers only to the registry audit and is not a
security guarantee. Owning range examples refer only to the remaining app dependency tree;
removed site npm owners are excluded. For names with multiple parents, example constraints are shown.

| Package | App versions | Latest tag | Owning range examples | Reported impact |
| --- | --- | --- | --- | --- |
| `@achrinza/node-ipc` | 9.2.2 | 9.2.10 | app: @vue/cli-shared-utils 4.5.19 9.2.2 | none reported |
| `@achrinza/strong-type` | 0.1.14 | 1.1.20 | app: @achrinza/event-pubsub 5.0.11 0.1.14 | none reported |
| `@asamuzakjp/dom-selector` | 9.2.4 | 10.0.1 | app: jsdom 30.1.2 ^9.2.4 | none reported |
| `@babel/code-frame` | 7.29.7 | 8.0.6 | app: @testing-library/dom 9.3.4 ^7.10.4, app: parse-json 5.2.0 ^7.0.0 | none reported |
| `@babel/helper-string-parser` | 7.29.7 | 8.0.6 | app: @babel/types 7.29.8 ^7.29.7 | none reported |
| `@babel/helper-validator-identifier` | 7.29.7 | 8.0.6 | app: @babel/code-frame 7.29.7 ^7.29.7, app: @babel/types 7.29.8 ^7.29.7 | none reported |
| `@babel/parser` | 7.29.9 | 8.0.7 | app: @vue/compiler-core 3.5.43 ^7.29.8, app: @vue/compiler-sfc 3.5.43 ^7.29.8 | none reported |
| `@babel/runtime` | 7.29.10 | 8.0.7 | app: @testing-library/dom 9.3.4 ^7.12.5, app: @testing-library/vue 8.1.0 ^7.23.2 | none reported |
| `@babel/types` | 7.29.8 | 8.0.6 | app: @babel/parser 7.29.9 ^7.29.8 | none reported |
| `@capacitor/cli` | 5.7.8 | 8.5.3 | app: @capacitor/assets 3.0.5 ^5.3.0 | high |
| `@emnapi/core` | 1.11.1 | 1.11.3 | app: @tailwindcss/oxide-wasm32-wasi 4.3.3 ^1.11.1, app: @napi-rs/wasm-runtime 1.1.4 peer ^1.7.1 | none reported |
| `@emnapi/runtime` | 1.11.1 | 1.11.3 | app: @tailwindcss/oxide-wasm32-wasi 4.3.3 ^1.11.1, app: @napi-rs/wasm-runtime 1.1.4 peer ^1.7.1 | none reported |
| `@emnapi/wasi-threads` | 1.2.2 | 2.2.0 | app: @tailwindcss/oxide-wasm32-wasi 4.3.3 ^1.2.2, app: @emnapi/core 1.11.1 1.2.2 | none reported |
| `@grpc/grpc-js` | 1.9.16 | 1.14.6 | app: @firebase/firestore 4.18.0 ~1.9.0 | high |
| `@grpc/proto-loader` | 0.7.15 | 0.8.1 | app: @firebase/firestore 4.18.0 ^0.7.8, app: @grpc/grpc-js 1.9.16 ^0.7.8 | none reported |
| `@hapi/address` | 2.1.4 | 5.1.1 | app: @hapi/joi 15.1.1 2.x.x | none reported |
| `@hapi/bourne` | 1.3.2 | 4.0.1 | app: @hapi/joi 15.1.1 1.x.x | none reported |
| `@hapi/hoek` | 8.5.1 | 11.0.7 | app: @hapi/joi 15.1.1 8.x.x, app: @hapi/topo 3.1.6 ^8.3.0 | none reported |
| `@hapi/joi` | 15.1.1 | 17.1.1 | app: @vue/cli-shared-utils 4.5.19 ^15.0.1 | none reported |
| `@hapi/topo` | 3.1.6 | 6.0.2 | app: @hapi/joi 15.1.1 3.x.x | none reported |
| `@humanfs/core` | 0.19.2 | 0.20.0 | app: @humanfs/node 0.16.8 ^0.19.2 | none reported |
| `@humanfs/node` | 0.16.8 | 0.17.0 | app: eslint 10.12.0 ^0.16.6 | none reported |
| `@humanfs/types` | 0.15.0 | 0.16.0 | app: @humanfs/core 0.19.2 ^0.15.0, app: @humanfs/node 0.16.8 ^0.15.0 | none reported |
| `@ionic/utils-process` | 2.1.11 | 2.1.12 | app: @ionic/utils-subprocess 2.1.14 2.1.11 | none reported |
| `@ionic/utils-stream` | 3.1.6 | 3.1.7 | app: @ionic/utils-subprocess 2.1.14 3.1.6 | none reported |
| `@ionic/utils-subprocess` | 2.1.14 | 3.0.1 | app: @capacitor/cli 5.7.8 ^2.1.11, app: @trapezedev/project 7.1.10 ^2.1.8 | none reported |
| `@ionic/utils-terminal` | 2.3.4 | 2.3.5 | app: @capacitor/cli 5.7.8 ^2.3.3, app: @ionic/utils-process 2.1.11 2.3.4 | none reported |
| `@jridgewell/gen-mapping` | 0.4.0-beta.0 | 0.3.13 | app: @babel/generator 8.0.6 0.4.0-beta.0 | none reported |
| `@keyv/bigmap` | 1.3.1 | 6.1.0 | app: @cacheable/memory 2.2.0 ^1.3.1 | none reported |
| `@napi-rs/wasm-runtime` | 1.1.4 | 1.2.5 | app: @tailwindcss/oxide-wasm32-wasi 4.3.3 ^1.1.4 | none reported |
| `@prettier/plugin-xml` | 2.2.0 | 3.4.2 | app: @trapezedev/project 7.1.10 ^2.2.0 | none reported |
| `@testing-library/dom` | 9.3.4 | 10.4.2 | app: @testing-library/vue 8.1.0 ^9.3.3 | none reported |
| `@tybys/wasm-util` | 0.10.2 | 0.10.4 | app: @tailwindcss/oxide-wasm32-wasi 4.3.3 ^0.10.2, app: @napi-rs/wasm-runtime 1.1.4 ^0.10.1 | none reported |
| `@types/fs-extra` | 8.1.5 | 11.0.4 | app: @ionic/utils-fs 3.1.7 ^8.0.0 | none reported |
| `@types/jsesc` | 2.5.1 | 3.0.3 | app: @babel/generator 8.0.6 ^2.5.0 | none reported |
| `@types/sinonjs__fake-timers` | 8.1.1 | 15.0.1 | app: cypress 16.1.1 8.1.1 | none reported |
| `@types/slice-ansi` | 4.0.0 | 7.1.0 | app: @ionic/utils-terminal 2.3.4 ^4.0.0, app: @ionic/utils-terminal 2.3.5 ^4.0.0 | none reported |
| `@vue/cli-shared-utils` | 4.5.19 | 5.0.9 | app: vue-cli-plugin-capacitor 2.0.1 ^4.5.4 | moderate |
| `@vue/devtools-api` | 6.6.4 | 8.2.1 | app: vuex 4.1.0 ^6.0.0-beta.11 | none reported |
| `address` | 1.2.2 | 2.0.3 | app: vue-cli-plugin-capacitor 2.0.1 ^1.0.3 | none reported |
| `agent-base` | 6.0.2 | 9.0.0 | app: https-proxy-agent 5.0.1 6 | none reported |
| `ajv` | 6.15.0 | 8.20.0 | app: @eslint/eslintrc 3.3.7 ^6.14.0, app: eslint 10.12.0 ^6.14.0 | none reported |
| `ansi-regex` | 4.1.1, 5.0.1 | 6.4.0 | app: strip-ansi 5.2.0 ^4.1.0, app: pretty-format 27.5.1 ^5.0.1 | none reported |
| `ansi-styles` | 3.2.1, 4.3.0, 5.2.0, 6.2.3 | 7.0.0 | app: chalk 2.4.2 ^3.2.1, app: chalk 4.1.2 ^4.1.0 | none reported |
| `argparse` | 2.0.1 | 3.0.2 | app: js-yaml 4.3.2 ^2.0.1 | none reported |
| `aria-query` | 5.1.3 | 5.3.2 | app: @testing-library/dom 9.3.4 5.1.3 | none reported |
| `ast-kit` | 2.2.0 | 3.0.0 | app: @vue-macros/common 3.1.4 ^2.1.2 | none reported |
| `asynckit` | 0.4.0 | 0.5.0 | app: form-data 4.0.6 ^0.4.0, app: form-data 2.3.3 ^0.4.0 | none reported |
| `balanced-match` | 1.0.2 | 4.0.4 | app: brace-expansion 2.1.7 ^1.0.0, app: brace-expansion 1.1.21 ^1.0.0 | none reported |
| `birpc` | 2.9.0 | 4.2.0 | app: @vue/devtools-kit 8.2.1 ^2.6.1 | none reported |
| `bl` | 4.1.0 | 7.0.12 | app: ora 5.4.1 ^4.1.0, app: tar-stream 2.2.0 ^4.0.3 | none reported |
| `boolbase` | 1.0.0 | 2.0.0 | app: css-select 4.3.0 ^1.0.0, app: nth-check 2.1.1 ^1.0.0 | none reported |
| `bplist-creator` | 0.1.0 | 0.3.0 | app: simple-plist 1.3.1 0.1.0 | none reported |
| `bplist-parser` | 0.3.1, 0.3.2 | 0.5.0 | app: native-run 2.0.3 ^0.3.2, app: simple-plist 1.3.1 0.3.1 | none reported |
| `brace-expansion` | 1.1.21, 2.1.7 | 5.0.12 | app: minimatch 8.0.7 ^2.0.1, app: minimatch 3.1.5 ^1.1.7 | none reported |
| `buffer` | 5.7.1 | 6.0.3 | app: bl 4.1.0 ^5.5.0, app: cypress 16.1.1 ^5.7.1 | none reported |
| `buffer-crc32` | 0.2.13 | 1.0.0 | app: yauzl 2.10.0 ~0.2.3 | none reported |
| `callsites` | 3.1.0 | 4.2.0 | app: parent-module 1.0.1 ^3.0.0 | none reported |
| `chalk` | 2.4.2, 4.1.2 | 6.0.1 | app: @capacitor-community/electron 5.0.1 ^4.1.2, app: @testing-library/dom 9.3.4 ^4.1.0 | none reported |
| `chevrotain` | 7.1.1 | 13.2.0 | app: @xml-tools/parser 1.0.12 7.1.1 | none reported |
| `chownr` | 1.1.4, 2.0.0 | 3.0.0 | app: tar 6.2.1 ^2.0.0, app: tar-fs 2.1.5 ^1.1.1 | none reported |
| `chrome-remote-interface` | 0.33.3 | 0.34.0 | app: cypress 16.1.1 0.33.3 | none reported |
| `cli-cursor` | 2.1.0, 3.1.0 | 5.0.0 | app: ora 3.4.0 ^2.1.0, app: ora 5.4.1 ^3.1.0 | none reported |
| `cli-spinners` | 2.9.2 | 3.4.0 | app: ora 3.4.0 ^2.0.0, app: ora 5.4.1 ^2.5.0 | none reported |
| `cli-table3` | 0.6.1 | 0.6.5 | app: cypress 16.1.1 0.6.1 | none reported |
| `cli-truncate` | 5.2.0 | 6.1.1 | app: listr2 9.0.5 ^5.0.0 | none reported |
| `cliui` | 8.0.1 | 9.0.1 | app: yargs 17.7.2 ^8.0.1 | none reported |
| `clone` | 1.0.4 | 2.1.2 | app: defaults 1.0.4 ^1.0.2 | none reported |
| `color` | 4.2.3 | 5.0.3 | app: sharp 0.32.6 ^4.2.3 | none reported |
| `color-convert` | 1.9.3, 2.0.1 | 3.1.3 | app: ansi-styles 3.2.1 ^1.9.0, app: ansi-styles 4.3.0 ^2.0.1 | none reported |
| `color-name` | 1.1.3, 1.1.4 | 2.1.1 | app: color-convert 1.9.3 1.1.3, app: color-convert 2.0.1 ~1.1.4 | none reported |
| `color-string` | 1.9.1 | 2.1.4 | app: color 4.2.3 ^1.9.0 | none reported |
| `commander` | 12.1.0, 14.0.3, 2.11.0, 6.2.1, 8.3.0, 9.5.0 | 15.0.0 | app: @capacitor/assets 3.0.5 8.3.0, app: @capacitor/cli 5.7.8 ^9.3.0 | none reported |
| `concat-map` | 0.0.1 | 0.0.2 | app: brace-expansion 1.1.21 0.0.1 | none reported |
| `confbox` | 0.1.8 | 0.3.1 | app: pkg-types 1.3.1 ^0.1.8 | none reported |
| `core-util-is` | 1.0.2 | 1.0.3 | app: verror 1.10.0 1.0.2 | none reported |
| `cross-spawn` | 6.0.6 | 7.0.6 | app: execa 1.0.0 ^6.0.0 | none reported |
| `css-select` | 4.3.0 | 7.0.0 | app: node-html-parser 5.4.2 ^4.2.1 | none reported |
| `css-what` | 6.2.2 | 8.0.0 | app: css-select 4.3.0 ^6.0.1 | none reported |
| `dashdash` | 1.14.1 | 2.0.0 | app: sshpk 1.18.0 ^1.12.0 | none reported |
| `debug` | 3.2.7, 4.3.4 | 4.4.3 | app: @capacitor/assets 3.0.5 4.3.4, app: @cypress/xvfb 1.2.4 ^3.1.0 | none reported |
| `decompress-response` | 6.0.0 | 10.0.0 | app: simple-get 4.0.1 ^6.0.0 | none reported |
| `defaults` | 1.0.4 | 3.0.0 | app: wcwidth 1.0.1 ^1.0.3 | none reported |
| `define-lazy-prop` | 2.0.0 | 3.0.0 | app: open 8.4.2 ^2.0.0 | none reported |
| `diff` | 5.2.2 | 9.0.0 | app: @trapezedev/project 7.1.10 ^5.1.0 | none reported |
| `dom-accessibility-api` | 0.5.16 | 0.7.1 | app: @testing-library/dom 9.3.4 ^0.5.9 | none reported |
| `dom-serializer` | 1.4.1 | 3.1.1 | app: domutils 2.8.0 ^1.0.1 | none reported |
| `domelementtype` | 2.3.0 | 3.0.0 | app: dom-serializer 1.4.1 ^2.0.1, app: domhandler 4.3.1 ^2.2.0 | none reported |
| `domhandler` | 4.3.1 | 6.0.1 | app: css-select 4.3.0 ^4.3.1, app: dom-serializer 1.4.1 ^4.2.0 | none reported |
| `domutils` | 2.8.0 | 4.0.2 | app: css-select 4.3.0 ^2.8.0 | none reported |
| `easy-stack` | 1.0.1 | 2.1.1 | app: @node-ipc/js-queue 2.0.3 1.0.1 | none reported |
| `ecc-jsbn` | 0.1.2 | 0.2.0 | app: sshpk 1.18.0 ~0.1.1 | none reported |
| `electron-is-dev` | 2.0.0 | 3.0.1 | app: @capacitor-community/electron 5.0.1 ~2.0.0 | none reported |
| `emoji-regex` | 10.6.0, 8.0.0 | 11.0.0 | app: string-width 7.2.0 ^10.3.0, app: string-width 4.2.3 ^8.0.0 | none reported |
| `entities` | 2.2.0, 7.0.1 | 8.1.0 | app: @vue/compiler-core 3.5.43 ^7.0.1, app: dom-serializer 1.4.1 ^2.0.0 | none reported |
| `env-paths` | 2.2.1 | 4.0.0 | app: @capacitor/cli 5.7.8 ^2.2.0, app: @capacitor/cli 8.5.3 ^2.2.0 | none reported |
| `es-module-lexer` | 2.3.2 | 3.0.3 | app: vitest 5.0.3 ^2.3.2 | none reported |
| `escape-string-regexp` | 1.0.5, 4.0.0 | 5.0.0 | app: chalk 2.4.2 ^1.0.5, app: eslint 10.12.0 ^4.0.0 | none reported |
| `eslint-visitor-keys` | 3.4.3, 4.2.1 | 5.0.1 | app: @eslint-community/eslint-utils 4.10.1 ^3.4.3, app: espree 10.4.0 ^4.2.1 | none reported |
| `espree` | 10.4.0 | 11.2.0 | app: @eslint/eslintrc 3.3.7 ^10.0.1, app: vue-eslint-parser 10.4.1 ^10.3.0 || ^11.0.0 | none reported |
| `estree-walker` | 2.0.2 | 3.0.3 | app: @vue/compiler-core 3.5.43 ^2.0.2, app: @vue/compiler-sfc 3.5.43 ^2.0.2 | none reported |
| `event-pubsub` | 4.3.0 | 6.1.1 | app: @achrinza/node-ipc 9.2.2 4.3.0 | none reported |
| `eventemitter2` | 6.4.7 | 6.4.9 | app: cypress 16.1.1 6.4.7 | none reported |
| `execa` | 1.0.0, 4.1.0 | 10.1.0 | app: @vue/cli-shared-utils 4.5.19 ^1.0.0, app: cypress 16.1.1 4.1.0 | none reported |
| `extsprintf` | 1.3.0 | 1.4.1 | app: jsprim 2.0.2 1.3.0, app: jsprim 1.4.2 1.3.0 | none reported |
| `fast-levenshtein` | 2.0.6 | 3.0.0 | app: optionator 0.9.4 ^2.0.6 | none reported |
| `find-up` | 5.0.0 | 8.0.0 | app: eslint 10.12.0 ^5.0.0 | none reported |
| `form-data` | 2.3.3 | 4.0.6 | app: request 2.88.2 ~2.3.2 | critical |
| `fs-extra` | 10.1.0, 11.1.1, 9.1.0 | 11.4.1 | app: @capacitor-community/electron 5.0.1 ~11.1.1, app: @capacitor/assets 3.0.5 10.1.0 | none reported |
| `fs-minipass` | 2.1.0 | 3.0.3 | app: tar 6.2.1 ^2.0.0 | none reported |
| `get-stream` | 4.1.0, 5.2.0 | 9.0.1 | app: execa 1.0.0 ^4.0.0, app: execa 4.1.0 ^5.0.0 | none reported |
| `glob` | 7.2.3, 9.3.5 | 13.0.6 | app: rimraf 4.4.1 ^9.2.0 | none reported |
| `global-dirs` | 3.0.1 | 4.0.0 | app: is-installed-globally 0.4.0 ^3.0.0 | none reported |
| `globals` | 14.0.0 | 17.13.0 | app: @eslint/eslintrc 3.3.7 ^14.0.0 | none reported |
| `has-flag` | 3.0.0, 4.0.0 | 5.0.1 | app: supports-color 5.5.0 ^3.0.0, app: supports-color 8.1.1 ^4.0.0 | none reported |
| `hasha` | 5.2.2 | 7.0.0 | app: cypress 16.1.1 5.2.2 | none reported |
| `hashery` | 1.5.1 | 3.0.3 | app: @keyv/bigmap 1.3.1 ^1.4.0, app: @cacheable/utils 2.5.0 ^1.5.1 | none reported |
| `he` | 1.2.0 | 2.0.0 | app: node-html-parser 5.4.2 1.2.0 | none reported |
| `hookable` | 5.5.3 | 6.1.2 | app: @vue/devtools-kit 8.2.1 ^5.5.3 | none reported |
| `hookified` | 1.15.1, 2.2.0 | 3.0.4 | app: @cacheable/memory 2.2.0 ^1.15.1, app: @keyv/bigmap 1.3.1 ^1.15.0 | none reported |
| `hosted-git-info` | 2.8.9 | 10.1.1 | app: normalize-package-data 2.5.0 ^2.1.4 | none reported |
| `http-signature` | 1.2.0 | 1.4.0 | app: request 2.88.2 ~1.2.0 | none reported |
| `https-proxy-agent` | 5.0.1 | 9.1.0 | app: axios 1.20.0 ^5.0.1 | none reported |
| `human-signals` | 1.1.1 | 8.0.1 | app: execa 4.1.0 ^1.1.1 | none reported |
| `idb` | 7.1.1 | 8.0.4 | app: @firebase/app 0.16.3 7.1.1, app: @firebase/installations 0.6.24 7.1.1 | none reported |
| `ignore` | 5.3.2 | 7.0.12 | app: @eslint/eslintrc 3.3.7 ^5.2.0, app: eslint 10.12.0 ^5.2.0 | none reported |
| `import-fresh` | 3.3.1 | 4.0.1 | app: @eslint/eslintrc 3.3.7 ^3.2.1 | none reported |
| `ini` | 1.3.8, 2.0.0, 4.1.3 | 7.0.0 | app: @trapezedev/project 7.1.10 ^2.0.0, app: config-chain 1.1.13 ^1.3.4 | none reported |
| `is-arrayish` | 0.2.1 | 0.3.4 | app: error-ex 1.3.4 ^0.2.1 | none reported |
| `is-docker` | 2.2.1 | 4.0.0 | app: is-wsl 2.2.0 ^2.0.0, app: open 8.4.2 ^2.1.1 | none reported |
| `is-fullwidth-code-point` | 3.0.0 | 5.1.0 | app: slice-ansi 4.0.0 ^3.0.0, app: string-width 4.2.3 ^3.0.0 | none reported |
| `is-installed-globally` | 0.4.0 | 1.0.1 | app: cypress 16.1.1 ~0.4.0 | none reported |
| `is-interactive` | 1.0.0 | 2.0.0 | app: ora 5.4.1 ^1.0.0 | none reported |
| `is-path-inside` | 3.0.3 | 4.0.0 | app: is-installed-globally 0.4.0 ^3.0.2 | none reported |
| `is-stream` | 1.1.0, 2.0.1 | 4.0.1 | app: execa 1.0.0 ^1.1.0, app: execa 4.1.0 ^2.0.0 | none reported |
| `is-unicode-supported` | 0.1.0 | 2.1.0 | app: log-symbols 4.1.0 ^0.1.0, app: ora 5.4.1 ^0.1.0 | none reported |
| `is-wsl` | 1.1.0, 2.2.0 | 3.1.1 | app: open 6.4.0 ^1.1.0, app: open 8.4.2 ^2.2.0 | none reported |
| `isexe` | 2.0.0 | 4.0.0 | app: which 1.3.1 ^2.0.0, app: which 2.0.2 ^2.0.0 | none reported |
| `js-message` | 1.0.7 | 3.1.1 | app: @achrinza/node-ipc 10.1.11 1.0.7, app: @achrinza/node-ipc 9.2.2 1.0.7 | none reported |
| `js-tokens` | 4.0.0 | 10.0.0 | app: @babel/code-frame 7.29.7 ^4.0.0 | none reported |
| `js-yaml` | 4.3.2 | 5.4.3 | app: @eslint/eslintrc 3.3.7 ^4.3.2 | none reported |
| `jsbn` | 0.1.1 | 1.1.0 | app: ecc-jsbn 0.1.2 ~0.1.0, app: sshpk 1.18.0 ~0.1.0 | none reported |
| `json-parse-even-better-errors` | 2.3.1 | 6.0.0 | app: parse-json 5.2.0 ^2.3.0 | none reported |
| `json-schema-traverse` | 0.4.1 | 1.0.0 | app: ajv 6.15.0 ^0.4.1 | none reported |
| `jsprim` | 1.4.2 | 2.0.2 | app: http-signature 1.2.0 ^1.2.2 | none reported |
| `keyv` | 4.5.4, 5.6.0 | 6.1.0 | app: @cacheable/memory 2.2.0 ^5.6.0, app: @keyv/bigmap 1.3.1 peer ^5.6.0 | none reported |
| `kleur` | 3.0.3 | 4.1.5 | app: prompts 2.4.2 ^3.0.3 | none reported |
| `lightningcss` | 1.32.0 | 1.33.0 | app: @tailwindcss/node 4.3.3 1.32.0 | none reported |
| `lightningcss-android-arm64` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-darwin-arm64` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-darwin-x64` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-freebsd-x64` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-linux-arm-gnueabihf` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-linux-arm64-gnu` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-linux-arm64-musl` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-linux-x64-gnu` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-linux-x64-musl` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-win32-arm64-msvc` | 1.32.0 | 1.33.0 |  | none reported |
| `lightningcss-win32-x64-msvc` | 1.32.0 | 1.33.0 |  | none reported |
| `lines-and-columns` | 1.2.4 | 2.0.4 | app: parse-json 5.2.0 ^1.1.6 | none reported |
| `listr2` | 9.0.5 | 11.1.1 | app: cypress 16.1.1 ^9.0.5 | none reported |
| `locate-path` | 6.0.0 | 8.0.0 | app: find-up 5.0.0 ^6.0.0 | none reported |
| `log-symbols` | 2.2.0, 4.1.0 | 7.0.1 | app: ora 3.4.0 ^2.2.0, app: cypress 16.1.1 ^4.0.0 | none reported |
| `log-update` | 6.1.0 | 8.0.0 | app: listr2 9.0.5 ^6.1.0 | none reported |
| `lru-cache` | 10.4.3, 5.1.1 | 11.5.3 | app: path-scurry 1.11.1 ^10.2.0, app: @vue/cli-shared-utils 4.5.19 ^5.1.1 | none reported |
| `magic-string` | 0.30.21 | 1.4.3 | app: @tailwindcss/node 4.3.3 ^0.30.21, app: @vue/compiler-sfc 3.5.43 ^0.30.21 | none reported |
| `magic-string-ast` | 1.0.3 | 2.1.1 | app: @vue-macros/common 3.1.4 ^1.0.2 | none reported |
| `mdn-data` | 2.27.1 | 2.37.2 | app: css-tree 3.2.1 2.27.1 | none reported |
| `mime-db` | 1.52.0 | 1.54.0 | app: mime-types 2.1.35 1.52.0 | none reported |
| `mime-types` | 2.1.35 | 3.0.2 | app: @capacitor-community/electron 5.0.1 ~2.1.35, app: @cypress/request 4.0.1 ~2.1.19 | none reported |
| `mimic-fn` | 1.2.0, 2.1.0 | 5.0.0 | app: onetime 2.0.1 ^1.0.0, app: onetime 5.1.2 ^2.1.0 | none reported |
| `mimic-response` | 3.1.0 | 4.0.0 | app: decompress-response 6.0.0 ^3.1.0 | none reported |
| `minimatch` | 3.1.5, 8.0.7 | 10.2.6 | app: glob 9.3.5 ^8.0.2, app: @eslint/eslintrc 3.3.7 ^3.1.5 | none reported |
| `minipass` | 3.3.6, 4.2.8, 5.0.0 | 7.1.3 | app: glob 9.3.5 ^4.2.4, app: minizlib 2.1.2 ^3.0.0 | none reported |
| `minizlib` | 2.1.2 | 3.1.0 | app: tar 6.2.1 ^2.1.1 | none reported |
| `mkdirp` | 1.0.4 | 3.0.1 | app: tar 6.2.1 ^1.0.3 | none reported |
| `ms` | 2.1.2 | 2.1.3 | app: debug 3.2.7 ^2.1.1, app: debug 4.3.4 2.1.2 | none reported |
| `nanoid` | 3.3.20 | 6.0.2 | app: postcss 8.5.29 ^3.3.19 | none reported |
| `nice-try` | 1.0.5 | 5.0.0 | app: cross-spawn 6.0.6 ^1.0.4 | none reported |
| `node-abi` | 3.98.0 | 4.37.0 | app: prebuild-install 7.1.3 ^3.3.0 | none reported |
| `node-addon-api` | 6.1.0, 7.1.1 | 8.9.2 | app: @parcel/watcher 2.6.0 ^7.0.0, app: sharp 0.32.6 ^6.1.0 | none reported |
| `node-fetch` | 2.7.0 | 3.3.2 | app: @capacitor/assets 3.0.5 2.7.0 | none reported |
| `node-html-parser` | 5.4.2 | 9.0.4 | app: @capacitor/assets 3.0.5 5.4.2 | none reported |
| `normalize-package-data` | 2.5.0 | 9.0.0 | app: read-pkg 5.2.0 ^2.5.0 | none reported |
| `npm-run-path` | 2.0.2, 4.0.1 | 6.0.0 | app: execa 1.0.0 ^2.0.0, app: execa 4.1.0 ^4.0.0 | none reported |
| `nth-check` | 2.1.1 | 3.0.1 | app: css-select 4.3.0 ^2.0.1, app: eslint-plugin-vue 10.11.1 ^2.1.1 | none reported |
| `obug` | 2.2.1 | 3.0.0 | app: unplugin-vue-components 32.1.0 ^2.1.1, app: vitest 5.0.3 ^2.1.4 | none reported |
| `onetime` | 2.0.1, 5.1.2, 7.0.0 | 8.0.0 | app: restore-cursor 2.0.0 ^2.0.0, app: execa 4.1.0 ^5.1.0 | none reported |
| `open` | 6.4.0, 8.4.2 | 11.0.4 | app: @capacitor/cli 5.7.8 ^8.4.0, app: @capacitor/cli 8.5.3 ^8.4.0 | none reported |
| `ora` | 3.4.0, 5.4.1 | 9.4.1 | app: @capacitor-community/electron 5.0.1 ^5.4.1, app: @vue/cli-shared-utils 4.5.19 ^3.4.0 | none reported |
| `p-finally` | 1.0.0 | 3.0.0 | app: execa 1.0.0 ^1.0.0 | none reported |
| `p-limit` | 3.1.0 | 7.3.3 | app: p-locate 5.0.0 ^3.0.2 | none reported |
| `p-locate` | 5.0.0 | 7.0.0 | app: locate-path 6.0.0 ^5.0.0 | none reported |
| `parent-module` | 1.0.1 | 3.2.0 | app: import-fresh 3.3.1 ^1.0.0 | none reported |
| `parse-json` | 5.2.0 | 8.3.0 | app: read-pkg 5.2.0 ^5.0.0 | none reported |
| `path-exists` | 4.0.0 | 5.0.0 | app: find-up 5.0.0 ^4.0.0 | none reported |
| `path-key` | 2.0.1, 3.1.1 | 4.0.0 | app: cross-spawn 6.0.6 ^2.0.1, app: npm-run-path 2.0.2 ^2.0.0 | none reported |
| `path-scurry` | 1.11.1 | 2.0.2 | app: glob 9.3.5 ^1.6.1 | none reported |
| `pify` | 2.3.0 | 6.1.0 | app: executable 4.1.1 ^2.2.0 | none reported |
| `pkg-types` | 1.3.1 | 2.3.3 | app: mlly 1.8.2 ^1.3.1 | none reported |
| `plist` | 3.1.1 | 5.0.0 | app: @capacitor/cli 5.7.8 ^3.0.5, app: @capacitor/cli 8.5.3 ^3.1.0 | none reported |
| `postcss-selector-parser` | 6.0.10 | 7.1.6 | app: @tailwindcss/typography 0.5.20 6.0.10 | moderate |
| `prettier` | 2.8.8 | 3.9.10 | app: @trapezedev/project 7.1.10 ^2.7.1 | none reported |
| `pretty-bytes` | 5.6.0 | 7.2.0 | app: cypress 16.1.1 ^5.6.0 | none reported |
| `pretty-format` | 27.5.1 | 30.5.1 | app: @testing-library/dom 9.3.4 ^27.0.2 | none reported |
| `protobufjs` | 7.6.6 | 8.8.1 | app: @grpc/proto-loader 0.7.15 ^7.2.5 | none reported |
| `proxy-from-env` | 1.0.0 | 2.1.0 | app: cypress 16.1.1 1.0.0 | none reported |
| `qified` | 0.10.1 | 0.13.2 | app: cacheable 2.5.0 ^0.10.1 | none reported |
| `qs` | 6.5.5 | 6.16.0 | app: request 2.88.2 ~6.5.2 | moderate |
| `quansync` | 0.2.11 | 1.0.0 | app: local-pkg 1.2.1 ^0.2.11 | none reported |
| `react-is` | 17.0.2 | 19.3.0 | app: pretty-format 27.5.1 ^17.0.1 | none reported |
| `read-pkg` | 5.2.0 | 10.1.0 | app: @vue/cli-shared-utils 4.5.19 ^5.1.1 | none reported |
| `readable-stream` | 3.6.2 | 4.8.0 | app: bl 4.1.0 ^3.4.0, app: tar-stream 2.2.0 ^3.1.1 | none reported |
| `resolve-from` | 4.0.0 | 5.0.0 | app: import-fresh 3.3.1 ^4.0.0 | none reported |
| `restore-cursor` | 2.0.0, 3.1.0 | 5.1.0 | app: cli-cursor 2.1.0 ^2.0.0, app: cli-cursor 3.1.0 ^3.1.0 | none reported |
| `rimraf` | 4.4.1 | 6.1.3 | app: @capacitor/cli 5.7.8 ^4.4.1 | none reported |
| `sax` | 1.1.4, 1.2.4 | 1.6.1 | app: xml2js 0.5.0 >=0.6.0, app: elementtree 0.1.7 1.1.4 | none reported |
| `semver` | 5.7.2, 6.3.1 | 7.8.5 | app: @vue/cli-shared-utils 4.5.19 ^6.1.0, app: cross-spawn 6.0.6 ^5.5.0 | none reported |
| `sharp` | 0.32.6 | 0.35.5 | app: @capacitor/assets 3.0.5 0.32.6 | high |
| `shebang-command` | 1.2.0 | 2.0.0 | app: cross-spawn 6.0.6 ^1.2.0 | none reported |
| `shebang-regex` | 1.0.0, 3.0.0 | 4.0.0 | app: shebang-command 1.2.0 ^1.0.0, app: shebang-command 2.0.0 ^3.0.0 | none reported |
| `signal-exit` | 3.0.7 | 4.1.0 | app: @ionic/utils-process 2.1.11 ^3.0.3, app: @ionic/utils-terminal 2.3.4 ^3.0.3 | none reported |
| `sisteransi` | 1.0.5 | 2.0.0 | app: prompts 2.4.2 ^1.0.5 | none reported |
| `slice-ansi` | 4.0.0, 7.1.2, 8.0.0 | 9.0.1 | app: @ionic/utils-terminal 2.3.4 ^4.0.0, app: @ionic/utils-terminal 2.3.5 ^4.0.0 | none reported |
| `spdx-expression-parse` | 3.0.1 | 5.0.0 | app: spdx-correct 3.2.0 ^3.0.0, app: validate-npm-package-license 3.0.4 ^3.0.0 | none reported |
| `stream-buffers` | 2.2.0 | 3.0.3 | app: bplist-creator 0.1.0 2.2.x | none reported |
| `string-width` | 4.2.3, 7.2.0 | 8.3.0 | app: @ionic/utils-terminal 2.3.4 ^4.1.0, app: @ionic/utils-terminal 2.3.5 ^4.1.0 | none reported |
| `strip-ansi` | 5.2.0, 6.0.1 | 7.2.0 | app: @ionic/utils-terminal 2.3.4 ^6.0.0, app: @ionic/utils-terminal 2.3.5 ^6.0.0 | none reported |
| `strip-eof` | 1.0.0 | 2.0.0 | app: execa 1.0.0 ^1.0.0 | none reported |
| `strip-final-newline` | 2.0.0 | 4.0.0 | app: execa 4.1.0 ^2.0.0 | none reported |
| `strip-json-comments` | 2.0.1, 3.1.1 | 5.0.3 | app: @eslint/eslintrc 3.3.7 ^3.1.1, app: rc 1.2.8 ~2.0.1 | none reported |
| `supports-color` | 5.5.0, 7.2.0, 8.1.1 | 11.0.0 | app: chalk 2.4.2 ^5.3.0, app: chalk 4.1.2 ^7.1.0 | none reported |
| `synckit` | 0.11.13 | 0.12.3 | app: eslint-plugin-prettier 5.5.6 ^0.11.13 | none reported |
| `tar` | 6.2.1 | 7.5.22 | app: @capacitor/cli 5.7.8 ^6.1.11 | critical |
| `tar-fs` | 2.1.5 | 3.1.3 | app: prebuild-install 7.1.3 ^2.0.0 | none reported |
| `tar-stream` | 2.2.0 | 3.2.2 | app: tar-fs 2.1.5 ^2.1.4 | none reported |
| `throttleit` | 1.0.1 | 3.0.0 | app: request-progress 3.0.0 ^1.0.0 | none reported |
| `through2` | 4.0.2 | 5.0.11 | app: native-run 2.0.3 ^4.0.2 | none reported |
| `tldts` | 6.1.86 | 7.4.18 | app: tough-cookie 5.1.2 ^6.1.32 | none reported |
| `tldts-core` | 6.1.86 | 7.4.18 | app: tldts 6.1.86 ^6.1.86 | none reported |
| `tough-cookie` | 2.5.0, 5.1.2 | 6.0.2 | app: @cypress/request 4.0.1 ^5.0.0, app: request 2.88.2 ~2.5.0 | moderate |
| `tr46` | 0.0.3 | 7.0.0 | app: whatwg-url 5.0.0 ~0.0.3 | none reported |
| `tslib` | 2.6.2 | 2.8.1 | app: @capacitor/assets 3.0.5 2.6.2, app: @capacitor/core 8.5.3 ^2.1.0 | none reported |
| `tweetnacl` | 0.14.5 | 1.0.3 | app: bcrypt-pbkdf 1.0.2 ^0.14.3, app: sshpk 1.18.0 ~0.14.0 | none reported |
| `type-fest` | 0.6.0, 0.8.1 | 5.10.0 | app: hasha 5.2.2 ^0.8.0, app: read-pkg 5.2.0 ^0.6.0 | none reported |
| `undici-types` | 8.9.0 | 8.11.2 | app: @types/node 26.6.5 ~8.9.0 | none reported |
| `unimport` | 6.5.0 | 7.0.2 | app: unplugin-auto-import 21.1.0 ^6.4.0 | none reported |
| `untildify` | 4.0.0 | 6.0.0 | app: @ionic/utils-terminal 2.3.4 ^4.0.0, app: @ionic/utils-terminal 2.3.5 ^4.0.0 | none reported |
| `uuid` | 3.4.0, 7.0.3 | 14.0.3 | app: request 2.88.2 ^3.3.2, app: xcode 3.0.1 ^7.0.3 | moderate |
| `verror` | 1.10.0 | 1.10.1 | app: jsprim 2.0.2 1.10.0, app: jsprim 1.4.2 1.10.0 | none reported |
| `vue-meta` | 3.0.0-alpha.10 | 2.4.0 | app: app direct ^3.0.0-alpha.10 | none reported |
| `web-vitals` | 4.2.4 | 6.2.3 | app: @firebase/performance 0.7.14 ^4.2.4 | none reported |
| `webidl-conversions` | 3.0.1 | 8.0.1 | app: whatwg-url 5.0.0 ^3.0.0 | none reported |
| `whatwg-url` | 5.0.0 | 17.2.0 | app: node-fetch 2.7.0 ^5.0.0 | none reported |
| `which` | 1.3.1, 2.0.2 | 7.0.0 | app: cross-spawn 6.0.6 ^1.2.9, app: cross-spawn 7.0.6 ^2.0.1 | none reported |
| `why-is-node-running` | 3.2.1 | 3.2.3 | app: vitest 5.0.3 3.2.1 | none reported |
| `wrap-ansi` | 7.0.0, 9.0.2 | 10.0.2 | app: @ionic/utils-terminal 2.3.4 ^7.0.0, app: @ionic/utils-terminal 2.3.5 ^7.0.0 | none reported |
| `ws` | 7.5.13 | 8.22.0 | app: chrome-remote-interface 0.33.3 ^7.2.0 | none reported |
| `xml2js` | 0.5.0 | 0.6.2 | app: @capacitor/cli 5.7.8 ^0.5.0 | none reported |
| `xmlbuilder` | 11.0.1 | 15.1.1 | app: xml2js 0.5.0 ~11.0.0, app: xml2js 0.6.2 ~11.0.0 | none reported |
| `xpath` | 0.0.32 | 0.0.35 | app: @trapezedev/project 7.1.10 ^0.0.32 | none reported |
| `yallist` | 3.1.1, 4.0.0 | 5.0.0 | app: minizlib 2.1.2 ^4.0.0, app: minipass 3.3.6 ^4.0.0 | none reported |
| `yargs` | 17.7.2 | 18.2.0 | app: @capacitor/assets 3.0.5 17.7.2, app: @grpc/proto-loader 0.7.15 ^17.7.2 | none reported |
| `yargs-parser` | 21.1.1 | 22.0.0 | app: yargs 17.7.2 ^21.1.1 | none reported |
| `yauzl` | 2.10.0 | 3.4.0 | app: native-run 2.0.3 ^2.10.0 | none reported |
| `yocto-queue` | 0.1.0 | 1.2.2 | app: p-limit 3.1.0 ^0.1.0 | none reported |

</details>

### Setting up a development environment

If you are using macOS, all the above requirements may be installed with Homebrew.

#### Initial project setup

- Clone or fork the project from `https://github.com/blocher/dailyoffice2019`
- `cd dailyoffice2019`
- `cp app/.env.development app/.env.local`
- `cp site/website/.env.example site/website/.env`

#### Import database

- Connect to Postgres `psql -d postgres`
- Create database `create database dailyoffice;`
- Create user `create user dailyoffice with password 'password';`
- Grant permissions `grant all privileges on database dailyoffice to dailyoffice;`
- Exit postgres `\q`
- Import `unzip -p site/dailyoffice_2024_01_30.sql.zip dailyoffice_2024_01_30.sql | psql -U dailyoffice dailyoffice`

#### Setup up python environment

- Go to the project's `/site` directory
- Create a Python virtual environment `python3 -m venv env`
- Load virtual environment `source env/bin/activate`
- Install Python Requirements `pip install -r requirements.txt`

#### Run API server (in separate terminal)

- Collect static assets `python manage.py collectstatic`
- Start development server `python manage.py runsslserver`
- The API documentation will be accessible locally at `https://127.0.0.1:8000/api/`

#### Run the client (frontend) server

- Go to the project's `/app` directory
- Follow the setup instructions in the client README: [app/README.md](app/README.md)
- The frontend will be accessible locally at `http://127.0.0.1:8080`

### Patrons and Twilio setup

The `patrons` Django app can send patronal feast and family anniversary reminders by SMS through Twilio. The calendar
feed is protected by an admin-rotatable token; create or rotate that token in Django admin under Patrons -> Calendar
feeds, then subscribe to the generated `.ics` URL in Google Calendar or Outlook.

To configure Twilio:

- Create or log into a Twilio account at https://console.twilio.com/.
- In the Twilio Console, buy or select an SMS-capable United States phone number. Twilio's quickstart documents this
  under Phone Numbers -> Manage -> Buy a number, and the number should be copied in E.164 format such as
  `+15551234567`.
- In the Account Dashboard, copy the Account SID and Auth Token.
- Add these variables to the deployment environment or `site/website/.env`:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_FROM_NUMBER`
  - `PATRONS_SMS_ENABLED=True`
- If sending to United States mobile recipients from a 10-digit long code, complete A2P 10DLC registration in the
  Twilio Console before enabling production reminders.
- Send one test reminder, then confirm the result in Django admin under Patrons -> Text message sends.

Twilio pricing changes over time, but as of the currently published Twilio pricing pages, US SMS starts at `$0.0083`
per sent or received message segment, a leased US long-code number is listed at `$1.15` per month, and sole proprietor
A2P 10DLC registration is listed at about `$4` one-time brand registration, `$15` one-time campaign vetting, and `$2`
per month per campaign. Carrier fees, compliance fees, failed-message fees, and future price changes can apply. Check
the official Twilio pages before budgeting: [Twilio SMS quickstart](https://www.twilio.com/docs/messaging/quickstart),
[Twilio US SMS pricing](https://www.twilio.com/en-us/sms/pricing/us), and
[Twilio A2P 10DLC overview](https://www.twilio.com/en-us/phone-numbers/a2p-10dlc).

### Code formatting standard

- Please use `black` to format code with a line length of 119 beore submitting a pull request
- `find . -iname "*.py" | xargs black --target-version=py311 --line-length=119` from the `site` directory

## Deploying

`master` is the only long-lived branch. From a clean checkout of a commit that is already on `origin/master`:

- `make deploy` deploys the API and the frontend; `make deploy-api` or `make deploy-web` deploys one side.
- To roll back, check out an older `master` commit and deploy again.

The frontend is built locally (Node from `app/.nvmrc`, `npm ci` when the lockfile or Node version changed, unit
tests, `vite build`) before anything ships, then
uploaded to the `dailyoffice2019` Cloudflare Pages project with Wrangler (`npx wrangler login` once). Cloudflare
does not build from Git. The API commit is pushed to the `production` remote and `deploy/server.sh` runs on the
server over SSH. The deploy stops at the first failure and checks that both sites respond.

## Quick overview

The application is built around several Django "apps". The most important are:

- *website*: This is the base site. All settings are defined in `website\settings.py` and all paths are defined
  in `website\routes.py`. Start here.
- *office*: This is where the bulk of the work is down to generate each Office.
- *churchcal*: This is used to build the church calendar. It currently supports both the Anglican Church in North
  America and the Episcopal Church calendars (though only ACNA is currently used for this project)
- *bible*: This is used to retrieve bible passages from various sources (currently only Bible Gateway, but others such
  as the ESV API are coming soon)
- *psalter*: This is used to retrieve passages from the Psalms (currently only the renewed Coverdale translation in the
  Book of Common Prayer 2019)

NOTE: churchcal, bible, and psalter apps may be spun off as separate projects soon and added as dependencies to this
project

## Submitting Issues and Contact

- For feature requests, please submit an issue and label it "enhancement"
- For bug reports, please submit an issue and label it "bug"
- Email the original creator Ben @ feedback@dailyoffice2019.com
- Join the Facebook discussion at: https://www.facebook.com/groups/dailyoffice/

### Initial seven-day Gemini audio batch

`batch_audio_files` is an unscheduled bootstrap command, separate from
`update_audio_files` and on-demand synthesis. It uses Google's asynchronous
[Batch API](https://ai.google.dev/gemini-api/docs/batch-api), with the configured
Gemini 3.8 TTS model, style, and voices. Set `TTS_PROVIDER=gemini` and
`GEMINI_API_KEY` in the command environment. The batch has its own quotas;
it does not guarantee capacity. `ffmpeg` is required for import.

Run from `site/`, using the project's Python environment:

```sh
TTS_PROVIDER=gemini python manage.py batch_audio_files prepare --manifest /absolute/path/initial-audio.json
TTS_PROVIDER=gemini python manage.py batch_audio_files submit --manifest /absolute/path/initial-audio.json
TTS_PROVIDER=gemini python manage.py batch_audio_files status --manifest /absolute/path/initial-audio.json
TTS_PROVIDER=gemini python manage.py batch_audio_files import --manifest /absolute/path/initial-audio.json
```

- `prepare` makes no Google requests. It plans today through six days ahead in
  Django's configured timezone; `--start-date YYYY-MM-DD` and `--days` override
  this. It covers all eight offices, both language styles, the base settings and
  each variation used by the scheduled warmer. It captures the serializer's
  actual grouped prayers, reading paragraphs, and announcements, deduplicates
  them, and skips existing clips. It is not every possible settings combination.
- `submit` creates paid Google batch jobs for the missing clips in chunks of 50
  (set `--batch-size` during preparation to change this, up to 100). Keep the
  manifest: it saves each accepted job so rerunning submission resumes safely.
- `status` checks once; it does not wait or import. Google targets completion
  within 24 hours. Repeat `import` later to import newly completed batches.
- `import` converts successful WAV responses to the same atomic MP3 files and
  `AudioClip` records used by playback. Repeating it preserves existing files.
  Per-clip failures remain listed in the manifest and cause a nonzero exit;
  successful clips are retained. Local conversion or DB failures can be retried
  by importing again. For Google generation failures, finish importing the other
  jobs, then prepare a new manifest for the same date range; cached successes
  will be skipped. Do not prepare duplicate jobs while the originals are pending.

The manifest must be used with the original model/style configuration. A second
process cannot submit/import the same manifest concurrently. An HTTP quota
rejection leaves that chunk ready to submit again later. After an ambiguous
network failure or interruption during submission, the command refuses to submit
that chunk again automatically. Find its matching `dailyoffice-<date>-<manifest
stem>-<chunk>` display name in Google, then recover it with:

```sh
TTS_PROVIDER=gemini python manage.py batch_audio_files attach --manifest /absolute/path/initial-audio.json --chunk 0 --job batches/JOB_ID
```

Import fills the speech-clip cache only. Word alignment, recorded bells, and
assembled full-office tracks continue to use the existing playback pipeline;
the batch does not send synchronous alignment requests. Keep the manifest outside
public media storage. No API key is stored in it.
