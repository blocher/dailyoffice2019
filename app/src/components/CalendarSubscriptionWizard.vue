<template>
  <div class="calendar-wizard-launcher">
    <el-button type="primary" size="large" @click="openQuickLinks()">
      Add to your calendar app
    </el-button>
  </div>

  <el-drawer
    v-model="showWizard"
    class="calendar-wizard-drawer"
    direction="rtl"
    :size="panelSize"
    :before-close="handleClose"
    :show-close="false"
    :with-header="false"
    title="Add to your calendar app"
  >
    <div
      class="flex flex-col gap-5 pb-4 text-left calendar-wizard-drawer__inner drawer-panel"
    >
      <div
        v-if="panelMode === 'quick'"
        class="flex gap-3 justify-between items-start w-full min-w-0 quick-header--links"
      >
        <div class="flex-1 pr-1 space-y-0 min-w-0 text-left">
          <p
            class="m-0 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
          >
            Add to your calendar app
          </p>
          <h2
            class="p-0 m-0 max-w-full text-base font-semibold tracking-tight leading-snug text-left text-slate-900 dark:text-slate-50"
          >
            Add Feasts and Readings to Your Calendar App
          </h2>
          <p
            class="m-0 mt-1.5 text-[11px] leading-relaxed tracking-normal text-slate-600 dark:text-slate-300"
          >
            Need help choosing a calendar and feed?
            <button
              type="button"
              class="m-0 p-0 text-[11px] font-semibold text-(--accent-color) underline decoration-(--accent-color)/40 underline-offset-2 hover:decoration-(--accent-color)"
              @click="goToFullWizard"
            >
              Open the guided setup
            </button>
          </p>
        </div>
        <button
          type="button"
          class="px-2.5 py-1 text-xs font-medium rounded-full transition-colors shrink-0 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-white"
          @click="handleClose"
        >
          Close
        </button>
      </div>
      <div v-else class="flex gap-3 justify-between items-start w-full min-w-0">
        <div class="flex gap-2.5 items-start min-w-0">
          <div
            class="flex justify-center items-center w-9 h-9 text-amber-700 bg-amber-50 rounded-lg shrink-0 dark:bg-amber-400/15 dark:text-amber-200"
          >
            <font-awesome-icon :icon="['fad', 'globe']" class="text-sm" />
          </div>
          <div class="space-y-0 min-w-0 text-left">
            <p
              class="m-0 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
            >
              Add to your calendar app
            </p>
            <h2
              class="p-0 m-0 text-base font-semibold tracking-tight text-left text-slate-900 dark:text-slate-50"
            >
              Add the liturgical calendar to your calendar
            </h2>
            <p
              class="m-0 text-xs leading-snug text-slate-600 dark:text-slate-300"
            >
              <span class="font-medium text-slate-800 dark:text-slate-200">
                Step {{ currentStep }} of 4
              </span>
              <span class="text-slate-400 dark:text-slate-500"> · </span>
              {{ currentStepHeadline }}
            </p>
          </div>
        </div>

        <button
          type="button"
          class="px-2.5 py-1 text-xs font-medium rounded-full transition-colors shrink-0 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-white"
          @click="handleClose"
        >
          Close
        </button>
      </div>

      <div
        v-if="panelMode === 'quick'"
        class="flex flex-col gap-4 text-left quick-feed-panel"
        :class="{ 'quick-feed-panel--dark': isDarkTheme }"
      >
        <section
          class="quick-panel-hero flex flex-col gap-4 rounded-2xl border border-slate-200/90 bg-gradient-to-b from-slate-50 to-white p-4 dark:!border-slate-600 dark:!bg-slate-900"
        >
          <div
            class="quick-doc-strip"
            role="group"
            aria-label="Third-party help for your calendar"
          >
            <p
              class="quick-doc-strip__label text-slate-600 dark:!text-slate-400"
            >
              Official help
              <span
                class="ml-0.5 text-[0.65rem] font-normal normal-case tracking-normal text-slate-500 dark:text-slate-400"
              >
                (opens in a new tab)
              </span>
            </p>
            <div
              class="flex flex-wrap gap-2 justify-start items-center w-full quick-doc-strip__items"
            >
              <a
                v-for="doc in docLinks"
                :key="doc.value"
                :href="doc.url"
                class="quick-doc-chip gap-1.5 border border-slate-300/80 bg-white/90 text-(--accent-color) dark:!border-slate-500 dark:!bg-slate-800/90 dark:text-sky-200"
                target="_blank"
                rel="noopener noreferrer"
              >
                <font-awesome-icon :icon="appIcon(doc)" class="w-3 h-3" />
                <span>{{ doc.label }}</span>
              </a>
              <button
                type="button"
                class="quick-doc-chip quick-doc-chip--action gap-1.5 border border-slate-300/80 bg-white/90 text-slate-900 dark:!border-slate-500 dark:!bg-slate-800/90 dark:!text-slate-100"
                @click="goToFullWizard"
              >
                Guided setup
              </button>
            </div>
          </div>

          <div class="quick-panel-hero__advice">
            <div
              class="quick-note quick-note--positive border border-emerald-200/60 bg-emerald-50/90 text-emerald-950 dark:!border-emerald-500/25 dark:!bg-emerald-950/45 dark:!text-emerald-50"
            >
              <div
                class="quick-note__icon bg-white text-emerald-600 shadow-sm dark:!bg-slate-800 dark:!text-emerald-300 dark:shadow-none dark:ring-1 dark:ring-slate-600"
              >
                <font-awesome-icon :icon="['fad', 'octagon-check']" />
              </div>
              <div>
                <p class="quick-note__title">
                  Best option:<br />Subscribe (Copy URL or Open webcal)
                </p>
                <p class="quick-note__body quick-note__body--prose">
                  Use the URL or `webcal` link if your calendar supports
                  subscriptions. It stays updated automatically.
                </p>
              </div>
            </div>

            <div
              class="quick-note quick-note--caution border border-amber-200/70 bg-amber-50/95 text-amber-950 dark:!border-amber-500/30 dark:!bg-amber-950/40 dark:!text-amber-50"
            >
              <div
                class="quick-note__icon bg-white text-amber-600 shadow-sm dark:!bg-slate-800 dark:!text-amber-300 dark:shadow-none dark:ring-1 dark:ring-slate-600"
              >
                <font-awesome-icon :icon="['fad', 'triangle-exclamation']" />
              </div>
              <div>
                <p class="quick-note__title">
                  Download and import only if you need a file
                </p>
                <p class="quick-note__body quick-note__body--prose">
                  Downloading and importing an `.ics` adds a one-time copy and
                  can be harder to remove later.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section class="space-y-2.5 w-full text-left quick-feed-section">
          <div
            v-for="row in quickPanelRows"
            :key="row.value"
            class="quick-feed-card w-full rounded-2xl border border-slate-200/90 bg-white px-[1.05rem] py-2.5 pb-4 text-left shadow-sm dark:!border-slate-600 dark:!bg-slate-900/95 dark:shadow-none"
          >
            <div
              class="flex flex-col gap-1 justify-start items-stretch w-full text-left"
            >
              <div
                class="flex flex-wrap justify-start items-baseline w-full min-w-0"
              >
                <h3
                  class="m-0 text-sm font-bold text-left text-slate-900 dark:text-slate-50"
                >
                  {{ row.label }}
                </h3>
              </div>
              <p
                class="m-0 w-full text-xs tracking-normal leading-relaxed text-left text-slate-600 dark:text-slate-300"
              >
                {{ row.description }}
              </p>
            </div>

            <div class="mt-3.5 space-y-2.5 w-full text-left">
              <div class="w-full">
                <p
                  class="m-0 text-left text-[10px] font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400"
                >
                  Feed URL
                </p>
                <el-input
                  :model-value="row.feedUrl"
                  readonly
                  class="mt-1.5 w-full font-mono quick-feed-input calendar-wizard-input"
                />
              </div>

              <div
                class="flex flex-wrap gap-2 justify-start items-center w-full"
              >
                <el-tooltip
                  placement="top"
                  :show-after="180"
                  effect="light"
                  popper-class="calendar-wizard-tooltip"
                >
                  <template #content>
                    <div
                      class="space-y-1.5 max-w-xs text-xs tracking-normal leading-relaxed text-slate-700 dark:text-slate-200"
                    >
                      <p class="m-0">
                        Paste this address into “Subscribe from URL,” “Add by
                        link,” or an iCal/ICS field in your app.
                      </p>
                      <p class="m-0">
                        Works in <strong>Google</strong> (desktop is most
                        reliable), <strong>Outlook</strong>,
                        <strong>Yahoo</strong>, and any app that supports a
                        calendar URL. If the app only offers “import a file,”
                        use <strong>Download .ics</strong> instead.
                      </p>
                    </div>
                  </template>
                  <el-button size="small" @click="copyFeedUrlForScope(row)">
                    <font-awesome-icon :icon="['fad', 'copy']" class="mr-1.5" />
                    Copy URL
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  placement="top"
                  :show-after="180"
                  effect="light"
                  popper-class="calendar-wizard-tooltip"
                >
                  <template #content>
                    <div
                      class="space-y-1.5 max-w-xs text-xs tracking-normal leading-relaxed text-slate-700 dark:text-slate-200"
                    >
                      <p class="m-0">
                        <span class="whitespace-nowrap">webcal://</span> is used
                        by some systems to start a subscription in one step.
                        When they are set as your default calendar app, some
                        apps such as Apple Calendar or Outlook will add the feed
                        and keep it updated. Best on
                        <strong>desktop</strong> and for
                        <strong>Apple Calendar</strong>. Many Google and mobile
                        setups work more reliably with Copy URL and the in-app
                        “subscribe from URL” flow.
                      </p>
                    </div>
                  </template>
                  <el-button
                    size="small"
                    plain
                    @click="openWebcalForScope(row)"
                  >
                    <font-awesome-icon
                      :icon="['fad', 'square-up-right']"
                      class="mr-1.5"
                    />
                    Open webcal
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  placement="top"
                  :show-after="180"
                  effect="light"
                  popper-class="calendar-wizard-tooltip"
                >
                  <template #content>
                    <p
                      class="m-0 max-w-xs text-xs tracking-normal leading-relaxed text-left text-slate-700 dark:text-slate-200"
                    >
                      An imported <span class="whitespace-nowrap">.ics</span> is
                      a one-time snapshot: it will not get updates when this
                      feed changes, and some calendars make imported events
                      difficult to remove. Prefer
                      <strong>Subscribe</strong> (URL or webcal) unless your
                      calendar only accepts a file.
                    </p>
                  </template>
                  <el-button
                    size="small"
                    plain
                    class="download-ics-button"
                    @click="downloadIcsForScope(row)"
                  >
                    <font-awesome-icon
                      :icon="['fad', 'triangle-exclamation']"
                      class="download-ics-warn"
                      aria-hidden="true"
                    />
                    <font-awesome-icon
                      :icon="['fad', 'download']"
                      class="mr-1"
                      aria-hidden="true"
                    />
                    Download .ics
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div v-else class="flex flex-col gap-2.5 text-left drawer-panel">
        <section
          class="p-1.5 rounded-xl border border-slate-200 bg-slate-50/90 dark:border-slate-700 dark:bg-slate-900/60"
        >
          <ol class="grid grid-cols-2 gap-1.5 sm:grid-cols-4">
            <li v-for="step in steps" :key="step.number" class="list-none">
              <button
                type="button"
                class="step-pill"
                :class="{
                  'step-pill--active': currentStep === step.number,
                  'step-pill--complete': currentStep > step.number,
                }"
                @click="jumpToStep(step.number)"
              >
                <span class="step-pill__num">{{ step.number }}</span>
                <span class="step-pill__label">{{ step.label }}</span>
              </button>
            </li>
          </ol>
        </section>

        <section
          v-if="currentStep === 1"
          class="p-3 space-y-2 bg-white rounded-xl border shadow-sm wizard-step border-slate-200 dark:border-slate-700 dark:bg-slate-900/70"
        >
          <h3
            class="m-0 text-sm font-semibold tracking-tight text-slate-900 dark:text-slate-100"
          >
            Feed
          </h3>
          <div class="grid gap-1.5 sm:grid-cols-1">
            <button
              v-for="option in scopeOptions"
              :key="option.value"
              type="button"
              class="h-full selection-card selection-card--compact"
              :class="
                selectedScope === option.value && 'selection-card--selected'
              "
              @click="selectScope(option.value)"
            >
              <div class="flex gap-2 justify-between items-center">
                <span
                  class="min-w-0 text-sm font-semibold text-slate-900 dark:text-white"
                  >{{ option.label }}</span
                >
                <font-awesome-icon
                  v-if="selectedScope === option.value"
                  :icon="['fad', 'octagon-check']"
                  class="text-sm text-emerald-600 shrink-0 dark:text-emerald-300"
                />
              </div>
            </button>
          </div>
        </section>

        <section
          v-else-if="currentStep === 2"
          class="p-3 space-y-2 bg-white rounded-xl border shadow-sm wizard-step border-slate-200 dark:border-slate-700 dark:bg-slate-900/70"
        >
          <h3
            class="m-0 text-sm font-semibold tracking-tight text-slate-900 dark:text-slate-100"
          >
            Calendar
          </h3>
          <div class="grid gap-1.5 sm:grid-cols-2">
            <button
              v-for="option in appOptions"
              :key="option.value"
              type="button"
              class="h-full selection-card selection-card--compact"
              :class="
                selectedApp === option.value && 'selection-card--selected'
              "
              @click="selectApp(option.value)"
            >
              <div class="flex gap-2 justify-between items-center">
                <div class="flex gap-2 items-center min-w-0">
                  <font-awesome-icon
                    :icon="appIcon(option)"
                    class="w-4 h-4 shrink-0 text-slate-500 dark:text-slate-400"
                  />
                  <span
                    class="min-w-0 text-sm font-semibold text-slate-900 dark:text-white"
                  >
                    {{ option.label }}
                  </span>
                </div>
                <font-awesome-icon
                  v-if="selectedApp === option.value"
                  :icon="['fad', 'octagon-check']"
                  class="text-sm text-emerald-600 shrink-0 dark:text-emerald-300"
                />
              </div>
            </button>
          </div>
        </section>

        <section
          v-else-if="currentStep === 3"
          class="p-3 space-y-2 bg-white rounded-xl border shadow-sm wizard-step border-slate-200 dark:border-slate-700 dark:bg-slate-900/70"
        >
          <h3
            class="m-0 text-sm font-semibold tracking-tight text-slate-900 dark:text-slate-100"
          >
            Subscribe or import
          </h3>
          <div class="grid gap-1.5">
            <button
              v-for="option in methodOptions"
              :key="option.value"
              type="button"
              class="selection-card selection-card--compact"
              :class="
                selectedMethod === option.value && 'selection-card--selected'
              "
              @click="selectMethod(option.value)"
            >
              <div class="flex gap-2 justify-between items-center">
                <div class="flex gap-1.5 items-center min-w-0">
                  <div
                    class="text-sm font-semibold text-slate-900 dark:text-white"
                  >
                    {{ option.label }}
                  </div>
                  <span
                    v-if="option.recommended"
                    class="inline-flex rounded bg-emerald-100 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-emerald-700 dark:bg-emerald-400/15 dark:text-emerald-200"
                  >
                    Recommended
                  </span>
                </div>
                <font-awesome-icon
                  v-if="selectedMethod === option.value"
                  :icon="['fad', 'octagon-check']"
                  class="text-sm text-emerald-600 shrink-0 dark:text-emerald-300"
                />
              </div>
              <p
                class="m-0 mt-0.5 text-xs tracking-normal leading-snug text-left text-slate-500 dark:text-slate-400"
              >
                {{ option.description }}
              </p>
            </button>
          </div>

          <el-alert
            v-if="selectedMethod === 'import'"
            type="warning"
            :closable="false"
            show-icon
            title="Imported calendar events are hard to remove"
          >
            <template #default>
              <p class="m-0 text-xs tracking-normal leading-relaxed">
                Imports do not auto-update. Reversing an import is awkward in
                some calendars, so use subscribe if you can.
              </p>
            </template>
          </el-alert>
        </section>

        <section
          v-else
          class="p-3 space-y-3 bg-white rounded-xl border shadow-sm wizard-step border-slate-200 dark:border-slate-700 dark:bg-slate-900/70"
        >
          <div>
            <h3
              class="m-0 text-sm font-semibold tracking-tight text-slate-900 dark:text-slate-100"
            >
              Set up
            </h3>
            <p
              class="m-0 mt-0.5 text-xs tracking-normal leading-relaxed text-slate-500 dark:text-slate-400"
            >
              Use the main action below, or open More options for the raw link.
            </p>
          </div>

          <div
            class="flex flex-col gap-1 sm:flex-row sm:flex-wrap sm:items-baseline sm:gap-x-2"
          >
            <div class="flex flex-wrap items-center gap-1.5 text-[11px]">
              <span class="summary-pill">{{ selectedScopeOption?.label }}</span>
              <span class="summary-pill">{{ selectedAppOption?.label }}</span>
              <span class="summary-pill">{{
                selectedMethodOption?.label
              }}</span>
            </div>
            <p
              class="m-0 text-[11px] text-slate-500 dark:text-slate-400 sm:ml-auto"
            >
              <button
                type="button"
                class="font-medium text-(--accent-color) hover:underline"
                @click="jumpToStep(1)"
              >
                Feed
              </button>
              <span class="text-slate-300 dark:text-slate-600"> · </span>
              <button
                type="button"
                class="font-medium text-(--accent-color) hover:underline"
                @click="jumpToStep(2)"
              >
                Calendar
              </button>
              <span class="text-slate-300 dark:text-slate-600"> · </span>
              <button
                type="button"
                class="font-medium text-(--accent-color) hover:underline"
                @click="jumpToStep(3)"
              >
                Method
              </button>
            </p>
          </div>

          <section
            class="p-2.5 rounded-lg border border-slate-200 bg-slate-50/90 dark:border-slate-700 dark:bg-slate-950/40"
          >
            <h4
              class="m-0 text-xs font-semibold text-slate-900 dark:text-slate-100"
            >
              What to do
            </h4>
            <p
              class="mt-0.5 mb-0 text-[11px] leading-relaxed tracking-normal text-slate-600 dark:text-slate-300"
            >
              {{ primaryActionLabel }}
            </p>

            <ol class="p-0 mt-2 space-y-1.5 list-none">
              <li
                v-for="(instruction, index) in providerInstructions"
                :key="instruction"
                class="flex gap-2 items-start"
              >
                <span
                  class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white text-[10px] font-semibold text-slate-700 ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-200 dark:ring-slate-700"
                >
                  {{ index + 1 }}
                </span>
                <p
                  class="m-0 text-xs tracking-normal leading-relaxed text-slate-700 dark:text-slate-300"
                >
                  {{ instruction }}
                </p>
              </li>
            </ol>

            <div class="flex flex-wrap gap-2 mt-3">
              <el-button type="primary" @click="handlePrimaryAction">
                {{ primaryActionLabel }}
              </el-button>
              <el-tooltip
                v-if="selectedMethod === 'subscribe' && canQuickOpenWebcal"
                placement="top"
                :show-after="180"
                effect="light"
                popper-class="calendar-wizard-tooltip"
              >
                <template #content>
                  <div
                    class="space-y-1.5 max-w-xs text-xs tracking-normal leading-relaxed text-slate-700 dark:text-slate-200"
                  >
                    <p class="m-0">
                      Same as <strong>Open webcal</strong> in the quick panel: a
                      <span class="whitespace-nowrap">webcal://</span> link for
                      the <strong>feed, calendar, and method</strong> you chose
                      in the steps above. It is not a normal website—your system
                      may open a calendar app to subscribe.
                    </p>
                    <p class="m-0">
                      Handoff works best on <strong>desktop</strong> and with
                      <strong>Apple Calendar</strong>. For
                      <strong>Google</strong> and many
                      <strong>mobile</strong> devices, use
                      <strong>Copy URL</strong> in <em>More options</em> and
                      paste the HTTPS address in the app, or follow the steps
                      listed above.
                    </p>
                  </div>
                </template>
                <el-button plain @click="openWebcalLink">
                  <font-awesome-icon
                    :icon="['fad', 'square-up-right']"
                    class="mr-1.5"
                  />
                  Open webcal link
                </el-button>
              </el-tooltip>
              <el-button
                v-if="providerPortalUrl && selectedApp !== 'apple'"
                plain
                @click="openProviderPortal"
              >
                Open {{ selectedAppOption?.label }}
              </el-button>
            </div>

            <div v-if="providerHelpUrl" class="mt-2">
              <a
                :href="providerHelpUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="text-xs font-medium text-(--accent-color) no-underline hover:underline"
              >
                Official help
              </a>
            </div>
          </section>

          <el-collapse v-model="moreOptionsOpen" class="more-options-collapse">
            <el-collapse-item
              name="more"
              title="More options: copy or download"
            >
              <div class="space-y-2">
                <p
                  class="m-0 text-[11px] leading-relaxed tracking-normal text-slate-600 dark:text-slate-400"
                >
                  Paste the feed URL, or use an .ics file if your calendar only
                  accepts imports.
                </p>
                <el-input
                  :model-value="subscribeUrl"
                  readonly
                  class="w-full font-mono calendar-wizard-input"
                />
                <div class="flex flex-wrap gap-2">
                  <el-tooltip
                    placement="top"
                    :show-after="180"
                    effect="light"
                    popper-class="calendar-wizard-tooltip"
                  >
                    <template #content>
                      <div
                        class="space-y-1.5 max-w-xs text-xs tracking-normal leading-relaxed text-slate-700 dark:text-slate-200"
                      >
                        <p class="m-0">
                          The <strong>HTTPS</strong> address for the feed you
                          selected. It matches the field above: paste it into
                          “Subscribe from URL” or “Add by link” in your calendar
                          app.
                        </p>
                        <p class="m-0">
                          We put it on your clipboard—use your app’s subscribe
                          or “from internet” option and paste.
                        </p>
                        <p class="m-0">
                          Works in <strong>Google</strong> (desktop is most
                          reliable), <strong>Outlook</strong>,
                          <strong>Yahoo</strong>, and other apps that accept an
                          iCal/ICS or calendar URL. If the app only allows
                          importing a file, use
                          <strong>Download .ics</strong> here instead.
                        </p>
                      </div>
                    </template>
                    <el-button plain @click="copySubscriptionUrl">
                      <font-awesome-icon
                        :icon="['fad', 'copy']"
                        class="mr-1.5"
                      />
                      Copy URL
                    </el-button>
                  </el-tooltip>
                  <el-button plain @click="downloadFeed">
                    <font-awesome-icon
                      :icon="['fad', 'download']"
                      class="mr-1.5"
                    />
                    Download .ics
                  </el-button>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>

          <section
            v-if="selectedMethod === 'import'"
            class="p-2.5 rounded-lg border border-rose-200 bg-rose-50/80 dark:border-rose-400/20 dark:bg-rose-500/10"
          >
            <h4
              class="m-0 text-xs font-semibold text-rose-900 dark:text-rose-100"
            >
              Undo import
            </h4>
            <p
              class="m-0 mt-1 text-xs tracking-normal leading-relaxed text-rose-800 dark:text-rose-100/90"
            >
              If you need to remove imported events, this cancellation feed
              undoes a best-effort cleanup across the same four-year window.
            </p>

            <div class="grid gap-1.5 mt-2">
              <el-input
                :model-value="cancelUrl"
                readonly
                class="w-full font-mono calendar-wizard-input"
              />
              <div class="flex flex-wrap gap-2">
                <el-button plain @click="copyUndoUrl">
                  <font-awesome-icon :icon="['fad', 'copy']" class="mr-1.5" />
                  Copy undo URL
                </el-button>
                <el-button plain @click="downloadUndoFeed">
                  <font-awesome-icon
                    :icon="['fad', 'download']"
                    class="mr-1.5"
                  />
                  Download undo file
                </el-button>
              </div>
            </div>
          </section>

          <section
            v-if="completedAction"
            class="p-2.5 rounded-lg border border-emerald-200 bg-emerald-50/80 dark:border-emerald-500/20"
          >
            <div class="flex gap-2 items-start">
              <font-awesome-icon
                :icon="['fad', 'octagon-check']"
                class="mt-0.5 text-sm text-emerald-600 dark:text-emerald-300"
              />
              <div>
                <h4
                  class="m-0 text-xs font-semibold text-emerald-900 dark:text-emerald-100"
                >
                  {{ completedAction.title }}
                </h4>
                <p
                  class="m-0 mt-0.5 text-xs tracking-normal leading-relaxed text-emerald-800 dark:text-emerald-100/90"
                >
                  {{ completedAction.body }}
                </p>
              </div>
            </div>
          </section>
        </section>

        <div
          class="flex flex-wrap gap-2 justify-between items-center pt-0.5 mt-auto"
        >
          <el-button v-if="currentStep > 1" plain @click="goBack"
            >Back</el-button
          >
          <div class="ml-auto">
            <el-button
              v-if="currentStep === 3 && selectedMethod === 'import'"
              type="primary"
              :disabled="!canContinue"
              @click="goNext"
            >
              Continue
            </el-button>
            <el-button
              v-else-if="currentStep === 4"
              type="primary"
              plain
              @click="handleClose"
            >
              Done
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script>
import { Browser } from '@capacitor/browser';
import { Clipboard } from '@capacitor/clipboard';
import { Capacitor } from '@capacitor/core';
import { ElMessage } from 'element-plus';
import {
  CALENDAR_APP_OPTIONS,
  CALENDAR_METHOD_OPTIONS,
  CALENDAR_SCOPE_OPTIONS,
  getCalendarDocumentationLinks,
  getCalendarFeedUrl,
  getCalendarPrimaryActionLabel,
  getCalendarProviderHelpLink,
  getCalendarProviderInstructions,
  getCalendarProviderLink,
  getCalendarWebcalUrl,
  getCalendarWizardDefaultScope,
} from '@/helpers/calendarSubscription';
import { getMessageOffset } from '@/helpers/getMessageOffest';

export default {
  name: 'CalendarSubscriptionWizard',
  props: {
    defaultScope: {
      type: String,
      default: 'major_minor',
    },
    includeMinorFeasts: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      showWizard: false,
      panelSize: '42%',
      isDarkTheme: false,
      currentStep: 1,
      selectedScope: this.defaultScope,
      selectedApp: null,
      selectedMethod: 'subscribe',
      completedAction: null,
      moreOptionsOpen: [],
      /** @type {'wizard' | 'quick'} */
      panelMode: 'wizard',
      steps: [
        { number: 1, label: 'Feed' },
        { number: 2, label: 'Calendar' },
        { number: 3, label: 'Method' },
        { number: 4, label: 'Set up' },
      ],
      stepHeadlines: {
        1: 'Which calendar feed do you want?',
        2: 'Which calendar do you use?',
        3: 'Do you want to subscribe or import?',
        4: 'Finish',
      },
      scopeOptions: CALENDAR_SCOPE_OPTIONS,
      appOptions: CALENDAR_APP_OPTIONS,
      methodOptions: CALENDAR_METHOD_OPTIONS,
      themeObserver: null,
    };
  },
  computed: {
    currentStepHeadline() {
      return this.stepHeadlines[this.currentStep] || '';
    },
    selectedScopeOption() {
      return this.scopeOptions.find(
        (option) => option.value === this.selectedScope
      );
    },
    selectedAppOption() {
      return this.appOptions.find(
        (option) => option.value === this.selectedApp
      );
    },
    selectedMethodOption() {
      return this.methodOptions.find(
        (option) => option.value === this.selectedMethod
      );
    },
    subscribeUrl() {
      return getCalendarFeedUrl(this.selectedScope);
    },
    downloadUrl() {
      return getCalendarFeedUrl(this.selectedScope, { download: true });
    },
    cancelUrl() {
      return getCalendarFeedUrl(this.selectedScope, { canceled: true });
    },
    cancelDownloadUrl() {
      return getCalendarFeedUrl(this.selectedScope, {
        canceled: true,
        download: true,
      });
    },
    webcalUrl() {
      return getCalendarWebcalUrl(this.selectedScope);
    },
    providerPortalUrl() {
      return getCalendarProviderLink(this.selectedApp);
    },
    providerHelpUrl() {
      return getCalendarProviderHelpLink(this.selectedApp);
    },
    primaryActionLabel() {
      return getCalendarPrimaryActionLabel(
        this.selectedApp,
        this.selectedMethod
      );
    },
    providerInstructions() {
      return getCalendarProviderInstructions(
        this.selectedApp,
        this.selectedMethod
      );
    },
    canContinue() {
      if (this.currentStep === 1) {
        return Boolean(this.selectedScope);
      }
      if (this.currentStep === 2) {
        return Boolean(this.selectedApp);
      }
      if (this.currentStep === 3) {
        return Boolean(this.selectedMethod);
      }
      return true;
    },
    canQuickOpenWebcal() {
      return (
        this.selectedMethod === 'subscribe' &&
        (this.selectedApp === 'apple' || this.selectedApp === 'other')
      );
    },
    quickPanelRows() {
      return this.scopeOptions.map((opt) => ({
        value: opt.value,
        label: opt.label,
        description: opt.description,
        feedUrl: getCalendarFeedUrl(opt.value),
        webcalUrl: getCalendarWebcalUrl(opt.value),
        downloadUrl: getCalendarFeedUrl(opt.value, { download: true }),
      }));
    },
    docLinks() {
      return getCalendarDocumentationLinks();
    },
  },
  mounted() {
    this.syncThemeMode();
    window.addEventListener('resize', this.setPanelSize);
    this.setPanelSize();
    if (typeof window.MutationObserver !== 'undefined') {
      this.themeObserver = new window.MutationObserver(() =>
        this.syncThemeMode()
      );
      this.themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class'],
      });
    }
  },
  unmounted() {
    window.removeEventListener('resize', this.setPanelSize);
    this.themeObserver?.disconnect();
  },
  methods: {
    syncThemeMode() {
      this.isDarkTheme = document.documentElement.classList.contains('dark');
    },
    appIcon(option) {
      if (option.icon && option.icon.length) {
        return option.icon;
      }
      return ['fad', 'globe'];
    },
    setPanelSize() {
      if (window.innerWidth < 768) {
        this.panelSize = '96%';
        return;
      }
      if (window.innerWidth < 1120) {
        this.panelSize = '74%';
        return;
      }
      this.panelSize = '42%';
    },
    getStartingStep(options = {}) {
      if (options.step) {
        return options.step;
      }
      return 1;
    },
    openWizard(options = {}) {
      this.syncThemeMode();
      this.panelMode = 'wizard';
      const fallbackScope = getCalendarWizardDefaultScope({
        source: 'calendar',
        includeMinorFeasts: this.includeMinorFeasts,
      });
      const selectedMethod = options.method || 'subscribe';
      this.selectedScope = options.scope || this.defaultScope || fallbackScope;
      this.selectedApp = options.app != null ? options.app : null;
      this.selectedMethod = selectedMethod;
      this.currentStep = this.getStartingStep(options);
      this.completedAction = null;
      this.moreOptionsOpen = [];
      this.showWizard = true;
    },
    openQuickLinks() {
      this.syncThemeMode();
      this.panelMode = 'quick';
      this.completedAction = null;
      this.moreOptionsOpen = [];
      this.showWizard = true;
    },
    goToFullWizard() {
      this.syncThemeMode();
      const fallback = getCalendarWizardDefaultScope({
        source: 'calendar',
        includeMinorFeasts: this.includeMinorFeasts,
      });
      this.panelMode = 'wizard';
      this.currentStep = 1;
      this.completedAction = null;
      this.moreOptionsOpen = [];
      this.selectedScope = this.defaultScope || fallback;
      this.selectedApp = null;
      this.selectedMethod = 'subscribe';
      this.showWizard = true;
    },
    handleClose(done) {
      if (this.panelMode === 'wizard') {
        this.panelMode = 'quick';
        this.completedAction = null;
        this.moreOptionsOpen = [];
        this.currentStep = 1;
        return;
      }

      this.showWizard = false;
      this.panelMode = 'quick';
      if (typeof done === 'function') {
        done();
      }
    },
    goNext() {
      if (!this.canContinue) {
        return;
      }
      this.currentStep = Math.min(4, this.currentStep + 1);
      this.completedAction = null;
    },
    goBack() {
      this.currentStep = Math.max(1, this.currentStep - 1);
      this.completedAction = null;
    },
    /**
     * After picking feed: go to app step, then skip to method/setup when
     * openWizard() already set app and/or a subscribe path is implied.
     */
    selectScope(value) {
      this.selectedScope = value;
      this.$nextTick(() => {
        this.completedAction = null;
        if (!this.selectedScope) {
          return;
        }
        this.currentStep = 2;
        this.$nextTick(() => {
          if (this.selectedApp) {
            this.currentStep = 3;
            this.$nextTick(() => {
              if (this.selectedMethod === 'subscribe') {
                this.currentStep = 4;
              }
            });
          }
        });
      });
    },
    selectApp(value) {
      this.selectedApp = value;
      this.$nextTick(() => {
        this.completedAction = null;
        this.currentStep = 3;
      });
    },
    selectMethod(value) {
      this.selectedMethod = value;
      if (value === 'import') {
        return;
      }
      this.$nextTick(() => {
        this.completedAction = null;
        this.currentStep = 4;
      });
    },
    async copyFeedUrlForScope(row) {
      await this.copyText(row.feedUrl, `The ${row.label} feed URL was copied.`);
    },
    openWebcalForScope(row) {
      window.location.assign(row.webcalUrl);
    },
    downloadIcsForScope(row) {
      this.downloadUrlInBrowser(row.downloadUrl);
      ElMessage.success({
        message: 'Your calendar file download has started.',
        showClose: true,
        offset: getMessageOffset(),
      });
    },
    jumpToStep(stepNumber) {
      this.panelMode = 'wizard';
      if (stepNumber === 1) {
        this.currentStep = 1;
        return;
      }
      if (stepNumber === 2 && this.selectedScope) {
        this.currentStep = 2;
        return;
      }
      if (stepNumber === 3 && this.selectedScope && this.selectedApp) {
        this.currentStep = 3;
        return;
      }
      if (
        stepNumber === 4 &&
        this.selectedScope &&
        this.selectedApp &&
        this.selectedMethod
      ) {
        this.currentStep = 4;
      }
    },
    async copyText(text, message) {
      await Clipboard.write({ string: text });
      ElMessage.success({
        message,
        showClose: true,
        offset: getMessageOffset(),
      });
    },
    async copySubscriptionUrl() {
      await this.copyText(
        this.subscribeUrl,
        'The calendar URL has been copied.'
      );
    },
    async copyUndoUrl() {
      await this.copyText(this.cancelUrl, 'The undo URL has been copied.');
    },
    async openExternalUrl(url) {
      if (!url) {
        return;
      }
      if (Capacitor.getPlatform() !== 'web') {
        await Browser.open({ url });
        return;
      }
      window.open(url, '_blank', 'noopener,noreferrer');
    },
    async openProviderPortal() {
      await this.openExternalUrl(this.providerPortalUrl);
    },
    openWebcalLink() {
      window.location.assign(this.webcalUrl);
    },
    downloadUrlInBrowser(url) {
      if (Capacitor.getPlatform() !== 'web') {
        return this.openExternalUrl(url);
      }
      const link = document.createElement('a');
      link.href = url;
      link.rel = 'noopener noreferrer';
      link.download = '';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      return Promise.resolve();
    },
    async downloadFeed() {
      await this.downloadUrlInBrowser(this.downloadUrl);
      ElMessage.success({
        message: 'Your calendar file download has started.',
        showClose: true,
        offset: getMessageOffset(),
      });
    },
    async downloadUndoFeed() {
      await this.downloadUrlInBrowser(this.cancelDownloadUrl);
      ElMessage.success({
        message: 'The undo calendar file download has started.',
        showClose: true,
        offset: getMessageOffset(),
      });
    },
    async handlePrimaryAction() {
      this.completedAction = null;

      if (this.selectedMethod === 'import') {
        await this.downloadFeed();
        if (this.providerPortalUrl && this.selectedApp !== 'apple') {
          await this.openProviderPortal();
        }
        this.completedAction = {
          title: 'Import started',
          body: 'If you need to remove those events later, use the cancellation feed in Undo import above.',
        };
        return;
      }

      if (this.selectedApp === 'apple') {
        this.openWebcalLink();
        this.completedAction = {
          title: 'Subscription link opened',
          body: 'Apple Calendar should offer to add the feed and keep it updated.',
        };
        return;
      }

      if (this.selectedApp === 'other') {
        await this.copySubscriptionUrl();
        this.completedAction = {
          title: 'URL copied',
          body: 'Paste it into a calendar that supports public iCalendar subscriptions.',
        };
        return;
      }

      await this.copySubscriptionUrl();
      await this.openProviderPortal();
      this.completedAction = {
        title: 'URL copied and calendar opened',
        body: `Paste the feed in ${this.selectedAppOption.label} to finish subscribing.`,
      };
    },
  },
};
</script>

<style scoped lang="scss">
.calendar-wizard-launcher {
  display: flex;
  justify-content: flex-start;
}

.calendar-wizard-launcher :deep(.el-button) {
  max-width: 100%;
}

/* One scroll: drawer body (see :with-header="false" + .calendar-wizard-drawer__inner). */
.calendar-wizard-drawer :deep(.el-drawer__body) {
  min-height: 0;
  -webkit-overflow-scrolling: touch;
}

.drawer-panel :is(h1, h2, h3, h4),
.drawer-panel .drawer-kicker {
  text-align: left !important;
}

/* Hero/card surfaces: colors come from template Tailwind; scoped `background: white` beats plain dark: utilities. */
.quick-panel-hero {
  min-width: 0;
}

.quick-panel-hero__intro {
  min-width: 0;
  width: 100%;
  text-align: left;
}

.quick-doc-strip {
  display: flex;
  width: 100%;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.55rem;
  padding-top: 0.9rem;
  text-align: left;
}

:global(html.dark) .quick-doc-strip {
  border-top-color: rgb(51 65 85);
}

.quick-doc-strip__label {
  margin: 0;
  width: 100%;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  line-height: 1.35;
  text-transform: uppercase;
}

.quick-doc-strip__label span {
  font-weight: 600;
  letter-spacing: normal;
}

.quick-doc-strip__items {
  display: flex;
  width: 100%;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
  gap: 0.4rem;
}

.quick-doc-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  padding: 0.38rem 0.62rem;
  font-size: 0.68rem;
  font-weight: 700;
  text-decoration: none;
  transition:
    border-color 150ms ease,
    transform 150ms ease,
    box-shadow 150ms ease;
}

.quick-doc-chip:hover {
  border-color: rgb(148 163 184);
  transform: translateY(-1px);
  box-shadow: 0 8px 18px -18px rgb(15 23 42 / 0.8);
}

.quick-panel-hero__advice {
  display: grid;
  width: 100%;
  gap: 0.75rem;
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .quick-panel-hero__advice {
    grid-template-columns: 1fr 1fr;
  }
}

.quick-note {
  display: flex;
  gap: 0.75rem;
  border-radius: 0.85rem;
  padding: 0.875rem;
}

.quick-note__icon {
  display: flex;
  height: 2rem;
  width: 2rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
}

.quick-note__title {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 700;
  line-height: 1.25;
}

.quick-note__body {
  margin: 0.2rem 0 0;
  font-size: 0.75rem;
  line-height: 1.45;
}

.quick-note__body--prose {
  letter-spacing: normal;
}

.summary-pill {
  display: inline-flex;
  border-radius: 9999px;
  background: rgb(241 245 249);
  padding: 0.15rem 0.4rem;
  font-size: 0.65rem;
  font-weight: 500;
  color: rgb(51 65 85);
}

:global(html.dark) .summary-pill {
  background: rgb(30 41 59);
  color: rgb(226 232 240);
}

.quick-feed-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  background: rgb(220 252 231);
  padding: 0.15rem 0.45rem;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgb(22 101 52);
}

.selection-card {
  width: 100%;
  border-radius: 0.5rem;
  border: 1px solid rgb(226 232 240);
  background: rgb(255 255 255);
  padding: 1rem;
  text-align: left;
  transition:
    border-color 150ms ease,
    background-color 150ms ease,
    box-shadow 150ms ease;
}

.selection-card--compact {
  padding: 0.45rem 0.55rem;
}

.selection-card:hover {
  border-color: rgb(203 213 225);
  background: rgb(248 250 252);
}

.selection-card:focus-visible,
.step-pill:focus-visible {
  outline: 2px solid var(--accent-color);
  outline-offset: 2px;
}

:global(html.dark) .selection-card,
:global(html.dark) .step-pill {
  border-color: rgb(51 65 85);
  background: rgba(15, 23, 42, 0.5);
}

:global(html.dark) .selection-card:hover,
:global(html.dark) .step-pill:hover {
  border-color: rgb(71 85 105);
  background: rgba(30, 41, 59, 0.7);
}

.selection-card--selected {
  border-color: rgb(110 231 183);
  background: rgba(236, 253, 245, 0.85);
  box-shadow: 0 1px 2px 0 rgba(15, 23, 42, 0.08);
}

:global(html.dark) .selection-card--selected {
  border-color: rgba(52, 211, 153, 0.3);
  background: rgba(16, 185, 129, 0.12);
}

.step-pill {
  display: flex;
  width: 100%;
  min-height: 2.1rem;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  border-radius: 0.375rem;
  border: 1px solid rgb(226 232 240);
  background: rgb(255 255 255);
  padding: 0.25rem 0.3rem;
  text-align: center;
  transition:
    border-color 150ms ease,
    background-color 150ms ease;
}

.step-pill:hover {
  border-color: rgb(203 213 225);
  background: rgb(248 250 252);
}

.step-pill--active {
  border-color: rgb(15 23 42);
  background: rgb(15 23 42);
  color: rgb(255 255 255);
}

:global(html.dark) .step-pill--active {
  border-color: rgb(255, 255, 255);
  background: rgb(255, 255, 255);
  color: rgb(15, 23, 42);
}

.step-pill--complete {
  border-color: rgb(110 231 183);
  background: rgb(236 253 245);
  color: rgb(6 78 59);
}

:global(html.dark) .step-pill--complete {
  border-color: rgba(52, 211, 153, 0.3);
  background: rgba(16, 185, 129, 0.12);
  color: rgb(209 250 229);
}

.step-pill__num {
  display: flex;
  height: 1rem;
  width: 1rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  font-size: 0.6rem;
  font-weight: 700;
  background: rgba(15, 23, 42, 0.08);
  line-height: 1;
}

.step-pill--active .step-pill__num,
.step-pill--complete .step-pill__num {
  background: rgba(255, 255, 255, 0.25);
}

:global(html.dark) .step-pill__num {
  background: rgba(255, 255, 255, 0.12);
}

:global(html.dark) .step-pill--active .step-pill__num {
  background: rgba(0, 0, 0, 0.12);
  color: inherit;
}

.step-pill--active .step-pill__num {
  background: rgba(255, 255, 255, 0.2);
  color: inherit;
}

.step-pill__label {
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  line-height: 1.1;
  text-transform: uppercase;
}

.more-options-collapse {
  :deep(.el-collapse-item__header) {
    height: auto;
    min-height: var(--el-collapse-header-height);
    padding: 0.35rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
  }

  :deep(.el-collapse-item__wrap) {
    border: none;
  }

  :deep(.el-collapse-item__content) {
    padding: 0 0.5rem 0.5rem;
  }
}

.quick-feed-section {
  width: 100%;
}

.quick-feed-panel--dark .quick-panel-hero {
  border-color: rgb(71 85 105 / 0.95) !important;
  background:
    radial-gradient(
      circle at top right,
      rgb(56 189 248 / 0.14),
      transparent 38%
    ),
    linear-gradient(180deg, rgb(15 23 42 / 0.96), rgb(2 6 23 / 0.98)) !important;
  box-shadow:
    inset 0 1px 0 rgb(148 163 184 / 0.08),
    0 20px 45px -35px rgb(0 0 0 / 0.9);
}

.quick-feed-panel--dark .quick-feed-card {
  border-color: rgb(71 85 105 / 0.95) !important;
  background: linear-gradient(
    180deg,
    rgb(15 23 42 / 0.98),
    rgb(2 6 23 / 0.98)
  ) !important;
  box-shadow:
    inset 0 1px 0 rgb(148 163 184 / 0.08),
    0 20px 45px -36px rgb(0 0 0 / 0.95);
}

.quick-feed-panel--dark .quick-doc-chip {
  border-color: rgb(100 116 139 / 0.9) !important;
  background: rgb(30 41 59 / 0.96) !important;
  color: rgb(191 219 254) !important;
}

.quick-feed-panel--dark .quick-doc-chip--action {
  color: rgb(241 245 249) !important;
}

.quick-feed-panel--dark .quick-doc-chip:hover {
  border-color: rgb(125 211 252 / 0.9) !important;
  box-shadow: 0 12px 24px -20px rgb(14 165 233 / 0.45);
}

.quick-feed-panel--dark .quick-note--positive {
  border-color: rgb(16 185 129 / 0.32) !important;
  background: rgb(6 78 59 / 0.42) !important;
  color: rgb(236 253 245) !important;
}

.quick-feed-panel--dark .quick-note--caution {
  border-color: rgb(245 158 11 / 0.32) !important;
  background: rgb(120 53 15 / 0.44) !important;
  color: rgb(255 247 237) !important;
}

.quick-feed-panel--dark .quick-note__icon {
  background: rgb(15 23 42) !important;
  box-shadow: inset 0 0 0 1px rgb(71 85 105 / 0.95) !important;
}

.quick-feed-panel :deep(.quick-feed-input) {
  width: 100%;
}

.quick-feed-panel :deep(.quick-feed-input .el-input__inner) {
  text-align: left;
  font-size: 0.7rem;
  line-height: 1.4;
}

.quick-feed-panel--dark :deep(.quick-feed-input .el-input__wrapper) {
  background-color: rgb(15 23 42 / 0.92) !important;
  box-shadow: 0 0 0 1px rgb(71 85 105 / 0.95) inset !important;
}

.quick-feed-panel--dark :deep(.quick-feed-input .el-input__inner) {
  color: rgb(241 245 249) !important;
  -webkit-text-fill-color: rgb(241 245 249) !important;
}

/* Element Plus: wrapper holds the field surface; ensure dark mode matches theme vars. */
:global(html.dark)
  .quick-feed-panel
  :deep(.quick-feed-input .el-input__wrapper),
:global(html.dark)
  .calendar-wizard-drawer
  :deep(.calendar-wizard-input .el-input__wrapper) {
  background-color: var(--el-fill-color-blank) !important;
  box-shadow: 0 0 0 1px var(--el-border-color) inset !important;
}

:global(html.dark) .quick-feed-panel :deep(.quick-feed-input .el-input__inner),
:global(html.dark)
  .calendar-wizard-drawer
  :deep(.calendar-wizard-input .el-input__inner) {
  color: var(--el-text-color-primary) !important;
  -webkit-text-fill-color: var(--el-text-color-primary) !important;
}

:global(html.dark) .more-options-collapse :deep(.el-collapse) {
  --el-border-color: rgba(51, 65, 85, 0.95);
  border-color: rgba(51, 65, 85, 0.95);
}

:global(html.dark) .more-options-collapse :deep(.el-collapse-item__header) {
  color: var(--el-text-color-primary) !important;
  background-color: rgba(15, 23, 42, 0.35) !important;
  border-color: rgba(51, 65, 85, 0.9) !important;
}

:global(html.dark) .more-options-collapse :deep(.el-collapse-item__arrow) {
  color: var(--el-text-color-secondary) !important;
}

.quick-feed-card {
  min-width: 0;
}

.download-ics-warn {
  margin-right: 0.2rem;
  color: rgb(202 138 4);
  filter: drop-shadow(0 0 0.5px rgb(234 179 8 / 0.5));
}

:global(html.dark) .download-ics-warn {
  color: rgb(250 204 21);
}

.download-ics-button {
  position: relative;
}

:global(html.dark) .quick-feed-badge {
  background: rgb(22 101 52 / 0.4);
  color: rgb(220 252 231);
}
</style>

<style lang="scss">
/*
 * Unscoped: beats Vue scoped rules that set light surfaces, so dark mode card
 * backgrounds are never left white while `dark:` text is applied.
 */
html.dark .calendar-wizard-drawer__inner .quick-panel-hero {
  border-color: #475569 !important;
  background: #0f172a !important;
  background-image: none !important;
}

html.dark .calendar-wizard-drawer__inner .quick-feed-card {
  border-color: #475569 !important;
  background: rgb(15 23 42 / 0.98) !important;
}

html.dark .calendar-wizard-drawer__inner .quick-doc-chip {
  border-color: #64748b !important;
  background: rgb(30 41 59 / 0.96) !important;
}

html.dark .calendar-wizard-drawer__inner a.quick-doc-chip {
  color: var(--accent-color) !important;
}

html.dark .calendar-wizard-drawer__inner .quick-doc-chip--action {
  color: #f1f5f9 !important;
}

html.dark .calendar-wizard-drawer__inner .quick-note--positive {
  border-color: rgba(16, 185, 129, 0.35) !important;
  background: rgba(6, 78, 59, 0.4) !important;
  color: #ecfdf5 !important;
}

html.dark .calendar-wizard-drawer__inner .quick-note--caution {
  border-color: rgba(245, 158, 11, 0.35) !important;
  background: rgba(120, 53, 15, 0.45) !important;
  color: #fff7ed !important;
}

html.dark .calendar-wizard-drawer__inner .quick-note__icon {
  background: rgb(15 23 42) !important;
  box-shadow: inset 0 0 0 1px #475569 !important;
}

/* Teleported Element Plus poppers. */
html.dark .el-popper.is-light.calendar-wizard-tooltip,
html.dark .el-popper.calendar-wizard-tooltip {
  --el-text-color-primary: #e5e7eb;
  --el-text-color-regular: #d1d5db;
  background: #1f2937 !important;
  border: 1px solid #334155 !important;
  color: #e5e7eb !important;
}

html.dark .el-popper.is-light.calendar-wizard-tooltip .el-popper__arrow::before,
html.dark .el-popper.calendar-wizard-tooltip .el-popper__arrow::before {
  background: #1f2937 !important;
  border: 1px solid #334155 !important;
}
</style>
