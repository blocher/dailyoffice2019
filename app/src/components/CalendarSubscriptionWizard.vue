<template>
  <div class="calendar-wizard-launcher">
    <UiButton variant="primary" icon="calendar-plus" @click="openQuickLinks()">
      Add to your calendar app
    </UiButton>
  </div>

  <UiSheet
    :open="showWizard"
    side="auto"
    size="lg"
    :eyebrow="sheetEyebrow"
    :title="sheetTitle"
    :subtitle="sheetSubtitle"
    @update:open="onSheetToggle"
  >
    <!-- Quick links: every feed, ready to copy -->
    <div v-if="panelMode === 'quick'" class="wizard">
      <p class="sheet-intro">
        Need help choosing a calendar and feed?
        <button type="button" class="text-link" @click="goToFullWizard">
          Open the guided setup
        </button>
      </p>

      <section class="sheet-block">
        <h3 class="wizard-label">Three ways to add a feed</h3>
        <dl class="ways">
          <div class="way">
            <dt class="way__title">
              <UiIcon name="copy" class="way__icon" />
              Copy URL
              <UiTag tone="success">Best</UiTag>
            </dt>
            <dd class="way__text">
              Paste the address into “Subscribe from URL,” “Add by link,” or an
              iCal/ICS field in your app, and it stays updated automatically.
              Works in Google (desktop is most reliable), Outlook, Yahoo, and
              any app that accepts a calendar URL.
            </dd>
          </div>
          <div class="way">
            <dt class="way__title">
              <UiIcon name="external" class="way__icon" />
              Open webcal
            </dt>
            <dd class="way__text">
              A <span class="nowrap">webcal://</span> link starts a subscription
              in one step when a calendar app such as Apple Calendar or Outlook
              is your default. Best on desktop and for Apple Calendar; many
              Google and mobile setups work more reliably with Copy URL.
            </dd>
          </div>
          <div class="way way--caution">
            <dt class="way__title">
              <UiIcon name="warning" class="way__icon" />
              Download .ics
            </dt>
            <dd class="way__text">
              Only if your calendar accepts nothing but a file. An imported
              <span class="nowrap">.ics</span> is a one-time copy: it will not
              get updates when this feed changes, and some calendars make
              imported events hard to remove.
            </dd>
          </div>
        </dl>
      </section>

      <section class="sheet-block">
        <h3 class="wizard-label">Feeds</h3>
        <article v-for="row in quickPanelRows" :key="row.value" class="feed">
          <h4 class="feed__title">{{ row.label }}</h4>
          <p class="feed__description">{{ row.description }}</p>
          <UiInput
            :model-value="row.feedUrl"
            readonly
            :aria-label="`${row.label} feed URL`"
            @focus="$event.target.select()"
          />
          <div class="wizard-actions">
            <UiButton icon="copy" @click="copyFeedUrlForScope(row)">
              Copy URL
            </UiButton>
            <UiButton icon="external" @click="openWebcalForScope(row)">
              Open webcal
            </UiButton>
            <UiButton
              variant="ghost"
              icon="download"
              class="download-ics-button"
              @click="downloadIcsForScope(row)"
            >
              Download .ics
            </UiButton>
          </div>
        </article>
      </section>

      <section class="sheet-block">
        <h3 class="wizard-label">
          Official help
          <span class="wizard-label__note">opens in a new tab</span>
        </h3>
        <ul class="help-links" aria-label="Third-party help for your calendar">
          <li v-for="doc in docLinks" :key="doc.value">
            <a
              :href="doc.url"
              class="help-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              <UiIcon :name="appIcon(doc)" class="help-link__icon" />
              <span>{{ doc.label }}</span>
              <UiIcon name="external" class="help-link__external" />
            </a>
          </li>
        </ul>
        <div class="wizard-actions">
          <UiButton variant="quiet" icon="arrow-right" @click="goToFullWizard">
            Guided setup
          </UiButton>
        </div>
      </section>
    </div>

    <!-- Guided setup: feed, calendar, method, then set up -->
    <div v-else class="wizard">
      <ol class="steps">
        <li v-for="step in steps" :key="step.number">
          <button
            type="button"
            class="step"
            :class="{
              'is-current': currentStep === step.number,
              'is-done': currentStep > step.number,
            }"
            :aria-current="currentStep === step.number ? 'step' : null"
            :disabled="!canJumpTo(step.number)"
            @click="jumpToStep(step.number)"
          >
            <span class="step__number" aria-hidden="true">
              <UiIcon v-if="currentStep > step.number" name="check" />
              <template v-else>{{ step.number }}</template>
            </span>
            <span class="step__label">{{ step.label }}</span>
          </button>
        </li>
      </ol>

      <section v-if="currentStep === 1" class="wizard-step">
        <h3 class="wizard-label">Feed</h3>
        <div class="choices" role="radiogroup" aria-label="Feed">
          <button
            v-for="option in scopeOptions"
            :key="option.value"
            type="button"
            role="radio"
            class="choice"
            :class="{ 'is-selected': selectedScope === option.value }"
            :aria-checked="selectedScope === option.value ? 'true' : 'false'"
            @click="selectScope(option.value)"
          >
            <span class="choice__mark" aria-hidden="true" />
            <span class="choice__body">
              <span class="choice__label">{{ option.label }}</span>
              <span class="choice__description">{{ option.description }}</span>
            </span>
          </button>
        </div>
      </section>

      <section v-else-if="currentStep === 2" class="wizard-step">
        <h3 class="wizard-label">Calendar</h3>
        <div class="choices" role="radiogroup" aria-label="Calendar">
          <button
            v-for="option in appOptions"
            :key="option.value"
            type="button"
            role="radio"
            class="choice"
            :class="{ 'is-selected': selectedApp === option.value }"
            :aria-checked="selectedApp === option.value ? 'true' : 'false'"
            @click="selectApp(option.value)"
          >
            <span class="choice__mark" aria-hidden="true" />
            <span class="choice__body">
              <span class="choice__label">
                <UiIcon :name="appIcon(option)" class="choice__icon" />
                {{ option.label }}
              </span>
              <span class="choice__description">{{ option.description }}</span>
            </span>
          </button>
        </div>
      </section>

      <section v-else-if="currentStep === 3" class="wizard-step">
        <h3 class="wizard-label">Subscribe or import</h3>
        <div class="choices" role="radiogroup" aria-label="Method">
          <button
            v-for="option in methodOptions"
            :key="option.value"
            type="button"
            role="radio"
            class="choice"
            :class="{ 'is-selected': selectedMethod === option.value }"
            :aria-checked="selectedMethod === option.value ? 'true' : 'false'"
            @click="selectMethod(option.value)"
          >
            <span class="choice__mark" aria-hidden="true" />
            <span class="choice__body">
              <span class="choice__label">
                {{ option.label }}
                <UiTag v-if="option.recommended" tone="success">
                  Recommended
                </UiTag>
              </span>
              <span class="choice__description">{{ option.description }}</span>
            </span>
          </button>
        </div>

        <UiAlert
          v-if="selectedMethod === 'import'"
          tone="warning"
          title="Imported calendar events are hard to remove"
          class="wizard-alert"
        >
          Imports do not auto-update. Reversing an import is awkward in some
          calendars, so use subscribe if you can.
        </UiAlert>
      </section>

      <section v-else class="wizard-step">
        <dl class="summary">
          <div class="summary__row">
            <dt>Feed</dt>
            <dd>{{ selectedScopeOption?.label }}</dd>
            <button type="button" class="text-link" @click="jumpToStep(1)">
              Change
            </button>
          </div>
          <div class="summary__row">
            <dt>Calendar</dt>
            <dd>{{ selectedAppOption?.label }}</dd>
            <button type="button" class="text-link" @click="jumpToStep(2)">
              Change
            </button>
          </div>
          <div class="summary__row">
            <dt>Method</dt>
            <dd>{{ selectedMethodOption?.label }}</dd>
            <button type="button" class="text-link" @click="jumpToStep(3)">
              Change
            </button>
          </div>
        </dl>

        <h3 class="wizard-label">What to do</h3>
        <ol class="instructions">
          <li v-for="instruction in providerInstructions" :key="instruction">
            {{ instruction }}
          </li>
        </ol>

        <div class="wizard-actions">
          <UiButton variant="primary" @click="handlePrimaryAction">
            {{ primaryActionLabel }}
          </UiButton>
          <UiButton
            v-if="selectedMethod === 'subscribe' && canQuickOpenWebcal"
            icon="external"
            @click="openWebcalLink"
          >
            Open webcal link
          </UiButton>
          <UiButton
            v-if="providerPortalUrl && selectedApp !== 'apple'"
            icon="external"
            @click="openProviderPortal"
          >
            Open {{ selectedAppOption?.label }}
          </UiButton>
        </div>
        <p
          v-if="selectedMethod === 'subscribe' && canQuickOpenWebcal"
          class="wizard-hint"
        >
          The webcal link subscribes to the feed you chose; your system may hand
          it to a calendar app. It works best on desktop and with Apple
          Calendar. For Google and many mobile devices, use Copy URL under More
          options and paste the address into the app.
        </p>
        <p v-if="providerHelpUrl" class="wizard-hint">
          <a :href="providerHelpUrl" target="_blank" rel="noopener noreferrer">
            Official {{ selectedAppOption?.label }} help
          </a>
        </p>

        <UiAlert
          v-if="completedAction"
          tone="success"
          :title="completedAction.title"
          class="wizard-alert"
        >
          {{ completedAction.body }}
        </UiAlert>

        <UiDisclosure
          title="More options: copy or download"
          class="more-options"
          :open="moreOptionsOpen"
          @update:open="moreOptionsOpen = $event"
        >
          <p class="wizard-hint wizard-hint--flush">
            The HTTPS address for the feed you chose. Paste it into “Subscribe
            from URL” or “Add by link,” or use an .ics file if your calendar
            only accepts imports.
          </p>
          <UiInput
            :model-value="subscribeUrl"
            readonly
            aria-label="Feed URL"
            @focus="$event.target.select()"
          />
          <div class="wizard-actions">
            <UiButton icon="copy" @click="copySubscriptionUrl">
              Copy URL
            </UiButton>
            <UiButton variant="ghost" icon="download" @click="downloadFeed">
              Download .ics
            </UiButton>
          </div>
        </UiDisclosure>

        <section v-if="selectedMethod === 'import'" class="undo">
          <h3 class="wizard-label">Undo import</h3>
          <p class="wizard-hint wizard-hint--flush">
            If you need to remove imported events, this cancellation feed undoes
            a best-effort cleanup across the same four-year window.
          </p>
          <UiInput
            :model-value="cancelUrl"
            readonly
            aria-label="Undo URL"
            @focus="$event.target.select()"
          />
          <div class="wizard-actions">
            <UiButton icon="copy" @click="copyUndoUrl">Copy undo URL</UiButton>
            <UiButton variant="ghost" icon="download" @click="downloadUndoFeed">
              Download undo file
            </UiButton>
          </div>
        </section>
      </section>
    </div>

    <template v-if="panelMode === 'wizard'" #footer>
      <UiButton
        v-if="currentStep > 1"
        variant="ghost"
        icon="chevron-left"
        @click="goBack"
      >
        Back
      </UiButton>
      <UiButton v-else variant="ghost" icon="chevron-left" @click="handleClose">
        All feeds
      </UiButton>
      <span class="footer-spacer" />
      <UiButton
        v-if="currentStep === 3 && selectedMethod === 'import'"
        variant="primary"
        :disabled="!canContinue"
        @click="goNext"
      >
        Continue
      </UiButton>
      <UiButton v-else-if="currentStep === 4" @click="handleClose">
        Done
      </UiButton>
    </template>
  </UiSheet>
</template>

<script>
import { openExternalLink } from '@/helpers/externalLink';
import { Clipboard } from '@capacitor/clipboard';
import { Capacitor } from '@capacitor/core';
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
import { toast } from '@/ui/feedback';

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
      currentStep: 1,
      selectedScope: this.defaultScope,
      selectedApp: null,
      selectedMethod: 'subscribe',
      completedAction: null,
      moreOptionsOpen: false,
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
        4: 'Add it to your calendar',
      },
      scopeOptions: CALENDAR_SCOPE_OPTIONS,
      appOptions: CALENDAR_APP_OPTIONS,
      methodOptions: CALENDAR_METHOD_OPTIONS,
    };
  },
  computed: {
    sheetEyebrow() {
      return this.panelMode === 'quick'
        ? 'Calendar feeds'
        : `Step ${this.currentStep} of 4`;
    },
    sheetTitle() {
      return this.panelMode === 'quick'
        ? 'Add to your calendar app'
        : 'Guided setup';
    },
    sheetSubtitle() {
      return this.panelMode === 'quick'
        ? 'Subscribe once and it keeps itself up to date.'
        : this.currentStepHeadline;
    },
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
  methods: {
    appIcon(option) {
      return option?.icon || 'globe';
    },
    onSheetToggle(open) {
      if (!open) {
        this.handleClose();
      }
    },
    canJumpTo(stepNumber) {
      if (stepNumber === 1) return true;
      if (stepNumber === 2) return Boolean(this.selectedScope);
      if (stepNumber === 3) {
        return Boolean(this.selectedScope && this.selectedApp);
      }
      return Boolean(
        this.selectedScope && this.selectedApp && this.selectedMethod
      );
    },
    getStartingStep(options = {}) {
      if (options.step) {
        return options.step;
      }
      return 1;
    },
    openWizard(options = {}) {
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
      this.moreOptionsOpen = false;
      this.showWizard = true;
    },
    openQuickLinks() {
      this.panelMode = 'quick';
      this.completedAction = null;
      this.moreOptionsOpen = false;
      this.showWizard = true;
    },
    goToFullWizard() {
      const fallback = getCalendarWizardDefaultScope({
        source: 'calendar',
        includeMinorFeasts: this.includeMinorFeasts,
      });
      this.panelMode = 'wizard';
      this.currentStep = 1;
      this.completedAction = null;
      this.moreOptionsOpen = false;
      this.selectedScope = this.defaultScope || fallback;
      this.selectedApp = null;
      this.selectedMethod = 'subscribe';
      this.showWizard = true;
    },
    handleClose(done) {
      if (this.panelMode === 'wizard') {
        this.panelMode = 'quick';
        this.completedAction = null;
        this.moreOptionsOpen = false;
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
      toast.success('Your calendar file download has started.');
    },
    jumpToStep(stepNumber) {
      this.panelMode = 'wizard';
      if (this.canJumpTo(stepNumber)) {
        this.currentStep = stepNumber;
      }
    },
    async copyText(text, message) {
      await Clipboard.write({ string: text });
      toast.success(message);
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
        await openExternalLink(url);
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
      toast.success('Your calendar file download has started.');
    },
    async downloadUndoFeed() {
      await this.downloadUrlInBrowser(this.cancelDownloadUrl);
      toast.success('The undo calendar file download has started.');
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
          body: 'If you need to remove those events later, use the cancellation feed in Undo import below.',
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
<style scoped>
.calendar-wizard-launcher {
  display: flex;
  justify-content: center;
}

.calendar-wizard-launcher .ui-button {
  max-width: 100%;
  white-space: normal;
}

.wizard {
  text-align: left;
}

.nowrap {
  white-space: nowrap;
}

/* A link-styled button for inline actions. */
.text-link {
  display: inline;
  padding: 0;
  color: var(--accent);
  font-style: italic;
  text-decoration: underline;
  text-decoration-color: color-mix(in srgb, currentColor 35%, transparent);
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
}

.text-link:hover {
  text-decoration-color: currentColor;
}

/* Small-caps section label */
.wizard-label {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 var(--space-2);
  font-size: var(--text-md);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
  line-height: 1.3;
}

.wizard-label__note {
  font-size: var(--text-sm);
  font-variant-caps: normal;
  letter-spacing: 0;
  font-style: italic;
}

.wizard-hint {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-soft);
  line-height: 1.45;
}

.wizard-hint--flush {
  margin: 0 0 var(--space-3);
}

.wizard-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.wizard-actions .ui-button {
  max-width: 100%;
  white-space: normal;
}

.wizard-alert {
  margin-top: var(--space-4);
}

/* ── Quick panel ─────────────────────────────────────── */
.ways {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

.way__title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  color: var(--ink);
}

.way__icon {
  color: var(--accent);
}

.way--caution .way__icon {
  color: var(--tone-warning);
}

.way__text {
  margin-top: var(--space-1);
  padding-left: calc(1em + var(--space-2));
  font-size: var(--text-sm);
  color: var(--ink-soft);
  line-height: 1.45;
}

.feed {
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--rule);
}

.feed:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.wizard-label + .feed {
  padding-top: var(--space-3);
}

.feed__title {
  font-size: var(--text-md);
  font-weight: 400;
  color: var(--ink);
  line-height: 1.3;
}

.feed__description {
  margin: var(--space-1) 0 var(--space-3);
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-soft);
  line-height: 1.4;
}

.wizard :deep(.ui-control[readonly]) {
  font-size: var(--text-sm);
  color: var(--ink-soft);
  text-overflow: ellipsis;
}

.download-ics-button :deep(.ui-button__icon) {
  color: var(--tone-warning);
}

.help-links {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(12rem, 1fr));
  gap: 0 var(--space-4);
  margin-top: var(--space-2);
}

.help-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 2.75rem;
  border-bottom: 1px solid var(--rule);
  color: var(--ink);
  text-decoration: none;
}

.help-link:hover {
  color: var(--accent);
}

.help-link__icon {
  color: var(--ink-soft);
}

.help-link__external {
  margin-left: auto;
  font-size: 0.8em;
  color: var(--ink-faint);
}

/* ── Guided setup ────────────────────────────────────── */
.steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: var(--space-5);
  border-bottom: 1px solid var(--rule);
}

.step {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  width: 100%;
  min-height: 3.5rem;
  padding: var(--space-2) var(--space-1);
  color: var(--ink-faint);
  text-align: center;
  transition: color var(--duration) var(--ease);
}

.step::after {
  content: '';
  position: absolute;
  left: 18%;
  right: 18%;
  bottom: -1px;
  height: 2px;
  border-radius: 2px;
  background-color: transparent;
}

.step:hover:not(:disabled) {
  color: var(--ink);
}

.step:disabled {
  cursor: default;
  opacity: 0.6;
}

.step.is-done {
  color: var(--ink-soft);
}

.step.is-current {
  color: var(--ink);
}

.step.is-current::after {
  background-color: var(--accent);
}

.step:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.step__number {
  display: grid;
  place-items: center;
  width: 1.5rem;
  height: 1.5rem;
  border: 1px solid var(--rule-strong);
  border-radius: 50%;
  font-size: var(--text-xs);
  line-height: 1;
  font-variant-numeric: lining-nums;
}

.step.is-current .step__number {
  border-color: var(--accent);
  color: var(--accent);
}

.step.is-done .step__number {
  border-color: var(--accent-rule);
  color: var(--accent);
}

.step__label {
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  line-height: 1.1;
}

@media (min-width: 480px) {
  .step {
    flex-direction: row;
    justify-content: center;
    gap: var(--space-2);
  }
}

.choices {
  display: flex;
  flex-direction: column;
  margin-top: var(--space-2);
  border-top: 1px solid var(--rule);
}

.choice {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  width: 100%;
  min-height: 3.25rem;
  padding: var(--space-3) var(--space-2);
  border-bottom: 1px solid var(--rule);
  text-align: left;
  transition: background-color var(--duration) var(--ease);
}

.choice:hover {
  background-color: var(--paper-sunken);
}

.choice:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
  border-radius: var(--radius-sm);
}

.choice.is-selected {
  background-color: var(--accent-wash);
}

/* A radio ring that fills with the accent when chosen. */
.choice__mark {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 1.15rem;
  height: 1.15rem;
  margin-top: 0.2rem;
  border: 1px solid var(--rule-strong);
  border-radius: 50%;
  background-color: var(--paper-raised);
}

.choice.is-selected .choice__mark {
  border-color: var(--accent);
  background-color: var(--accent);
}

.choice.is-selected .choice__mark::after {
  content: '';
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 50%;
  background-color: var(--on-accent);
}

.choice__body {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.choice__label {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  color: var(--ink);
  line-height: 1.3;
}

.choice__icon {
  color: var(--ink-soft);
}

.choice__description {
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-soft);
  line-height: 1.4;
}

.summary {
  margin-bottom: var(--space-5);
  border-top: 1px solid var(--rule);
}

.summary__row {
  display: grid;
  grid-template-columns: 5.5rem minmax(0, 1fr) auto;
  align-items: baseline;
  gap: var(--space-3);
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--rule);
  font-size: var(--text-sm);
}

.summary__row dt {
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
}

.summary__row dd {
  color: var(--ink);
}

.summary__row .text-link {
  min-height: 2rem;
}

.instructions {
  margin-top: var(--space-2);
  padding-left: 1.4em;
  list-style: decimal;
  color: var(--ink);
  line-height: 1.5;
}

.instructions li + li {
  margin-top: var(--space-2);
}

.instructions li::marker {
  color: var(--ink-faint);
}

.more-options {
  margin-top: var(--space-5);
  border-top: 1px solid var(--rule);
}

.undo {
  margin-top: var(--space-5);
}

.undo .wizard-label {
  margin-bottom: var(--space-2);
}

.footer-spacer {
  flex: 1 1 auto;
}
</style>
