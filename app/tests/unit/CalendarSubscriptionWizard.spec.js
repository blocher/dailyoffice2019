import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import CalendarSubscriptionWizard from '../../src/components/CalendarSubscriptionWizard.vue';
import { getCalendarFeedBaseUrl } from '../../src/helpers/calendarSubscription';

const { clipboardWrite, browserOpen, messageSuccess } = vi.hoisted(() => ({
  clipboardWrite: vi.fn().mockResolvedValue(),
  browserOpen: vi.fn().mockResolvedValue(),
  messageSuccess: vi.fn(),
}));

vi.mock('@capacitor/clipboard', () => ({
  Clipboard: {
    write: clipboardWrite,
  },
}));

vi.mock('@capacitor/browser', () => ({
  Browser: {
    open: browserOpen,
  },
}));

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    getPlatform: vi.fn(() => 'web'),
  },
}));

vi.mock('element-plus', () => ({
  ElMessage: {
    success: messageSuccess,
  },
}));

const ElDrawerStub = {
  props: ['modelValue'],
  template:
    '<div v-if="modelValue"><slot name="header"></slot><slot></slot></div>',
};

const ElButtonStub = {
  emits: ['click'],
  template: '<button @click="$emit(\'click\', $event)"><slot /></button>',
};

const ElInputStub = {
  props: ['modelValue'],
  template: '<input :value="modelValue" readonly />',
};

const ElAlertStub = {
  props: ['title'],
  template: '<div><div>{{ title }}</div><slot name="default"></slot><slot /></div>',
};

const ElCollapseStub = {
  template: '<div class="el-collapse-stub"><slot /></div>',
};

const ElCollapseItemStub = {
  props: ['name', 'title'],
  template:
    '<div class="el-collapse-item-stub"><div>{{ title }}</div><div><slot /></div></div>',
};

const ElTooltipStub = {
  template: '<div class="el-tooltip-stub"><slot /><slot name="content" /></div>',
};

function mountWizard(props = {}) {
  document.documentElement.style.setProperty('--sat', '0px');
  return mount(CalendarSubscriptionWizard, {
    props,
    global: {
      stubs: {
        'font-awesome-icon': true,
        'el-drawer': ElDrawerStub,
        'el-button': ElButtonStub,
        'el-input': ElInputStub,
        'el-alert': ElAlertStub,
        'el-collapse': ElCollapseStub,
        'el-collapse-item': ElCollapseItemStub,
        'el-tooltip': ElTooltipStub,
      },
    },
  });
}

describe('CalendarSubscriptionWizard', () => {
  beforeEach(() => {
    clipboardWrite.mockClear();
    browserOpen.mockClear();
    messageSuccess.mockClear();
  });

  it('opens with the current calendar scope and shows the import warning when selected', async () => {
    const wrapper = mountWizard({ defaultScope: 'major', includeMinorFeasts: false });

    wrapper.vm.openWizard({ scope: 'major' });
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.showWizard).toBe(true);
    expect(wrapper.vm.selectedScope).toBe('major');

    wrapper.vm.selectedApp = 'google';
    wrapper.vm.currentStep = 3;
    wrapper.vm.selectedMethod = 'import';
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Imported calendar events are hard to remove');
  });

  it('opens the quick links drawer from the launcher button', async () => {
    const wrapper = mountWizard({ defaultScope: 'major_minor' });

    await wrapper.find('button').trigger('click');

    expect(wrapper.vm.showWizard).toBe(true);
    expect(wrapper.vm.panelMode).toBe('quick');
    expect(wrapper.vm.selectedApp).toBe(null);
    expect(wrapper.vm.selectedMethod).toBe('subscribe');
    expect(wrapper.vm.currentStep).toBe(1);
    expect(wrapper.vm.selectedScope).toBe('major_minor');
  });

  it('opens the full wizard from the quick links drawer', async () => {
    const wrapper = mountWizard({ defaultScope: 'major_minor' });

    await wrapper.find('button').trigger('click');

    expect(wrapper.vm.showWizard).toBe(true);
    expect(wrapper.vm.panelMode).toBe('quick');
    expect(wrapper.text()).toContain('Add Feasts and Readings to Your Calendar App');
    expect(wrapper.text()).toContain('Sundays and Major Feasts');

    await wrapper.vm.goToFullWizard();
    expect(wrapper.vm.panelMode).toBe('wizard');
    expect(wrapper.vm.currentStep).toBe(1);
  });

  it('returns to quick links when closing the full wizard', async () => {
    const wrapper = mountWizard({ defaultScope: 'major_minor' });

    wrapper.vm.openWizard({ scope: 'major_minor' });
    expect(wrapper.vm.panelMode).toBe('wizard');

    wrapper.vm.handleClose();

    expect(wrapper.vm.showWizard).toBe(true);
    expect(wrapper.vm.panelMode).toBe('quick');
    expect(wrapper.vm.currentStep).toBe(1);
  });

  it('renders a provider-specific subscribe CTA for Google', async () => {
    const wrapper = mountWizard({ defaultScope: 'major_minor' });

    wrapper.vm.openWizard({ scope: 'major_minor' });
    wrapper.vm.selectedApp = 'google';
    wrapper.vm.selectedMethod = 'subscribe';
    wrapper.vm.currentStep = 4;
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Copy URL and Open Google Calendar');
    expect(wrapper.text()).toContain('From URL');
  });

  it('copies the canonical API-domain subscription URL', async () => {
    const wrapper = mountWizard({ defaultScope: 'every' });

    wrapper.vm.openWizard({ scope: 'every' });
    wrapper.vm.selectedApp = 'other';
    wrapper.vm.selectedMethod = 'subscribe';
    wrapper.vm.currentStep = 4;
    await wrapper.vm.copySubscriptionUrl();

    expect(clipboardWrite).toHaveBeenCalledWith({
      string: `${getCalendarFeedBaseUrl()}/every.ics`,
    });
  });
});
