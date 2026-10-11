const CALENDAR_PRODUCTION_API_BASE_URL = 'https://api.dailyoffice2019.com/';

export const CALENDAR_SCOPE_OPTIONS = [
  {
    value: 'major',
    label: 'Sundays and Major Feasts',
    description: 'Sundays and principal feasts only — lightest year.',
  },
  {
    value: 'major_minor',
    label: 'Sundays, Major Feasts, and Lesser Commemorations',
    description: 'Matches the “Show All Feasts” view on the calendar page.',
  },
  {
    value: 'every',
    label: 'Every day',
    description:
      'Every date, including ferias (seasonal days with no particular commemoration).',
  },
];

export const CALENDAR_APP_OPTIONS = [
  {
    value: 'apple',
    label: 'Apple Calendar',
    description: 'Works well on iPhone, iPad, and Mac.',
    icon: ['fab', 'apple'],
  },
  {
    value: 'google',
    label: 'Google Calendar',
    description: 'Best if you use Google Calendar on the web.',
    icon: ['fab', 'google'],
  },
  {
    value: 'outlook',
    label: 'Microsoft Outlook',
    description: 'For Outlook.com and Microsoft 365 calendars.',
    icon: ['fab', 'microsoft'],
  },
  {
    value: 'yahoo',
    label: 'Yahoo Calendar',
    description: 'Yahoo Mail and Calendar.',
    icon: ['fab', 'yahoo'],
  },
  {
    value: 'other',
    label: 'Other',
    description: 'Use a calendar URL or download an `.ics` file.',
    icon: ['fad', 'globe'],
  },
];

export const CALENDAR_METHOD_OPTIONS = [
  {
    value: 'subscribe',
    label: 'Subscribe',
    description: 'Recommended — updates sync automatically.',
    recommended: true,
  },
  {
    value: 'import',
    label: 'Import',
    description: 'One-time copy; does not auto-update.',
    recommended: false,
  },
];

export const CALENDAR_PROVIDER_LINKS = {
  google: 'https://calendar.google.com/calendar/u/0/r',
  outlook: 'https://outlook.live.com/calendar/0/',
  yahoo: 'https://calendar.yahoo.com/',
};

export const CALENDAR_PROVIDER_HELP_LINKS = {
  google:
    'https://support.google.com/calendar/answer/37100?co=GENIE.Platform%3DDesktop&hl=en',
  outlook:
    'https://support.microsoft.com/en-us/office/import-or-subscribe-to-a-calendar-in-outlook-com-or-outlook-on-the-web-cff1429c-5af6-41ec-a5b4-74f2c278e98c',
  apple: 'https://support.apple.com/en-us/102301',
  yahoo: 'https://help.yahoo.com/kb/SLN36693.html',
};

export function getCalendarApiBaseUrl() {
  const configuredBaseUrl =
    import.meta.env.VITE_API_URL || CALENDAR_PRODUCTION_API_BASE_URL;

  if (configuredBaseUrl.endsWith('/')) {
    return configuredBaseUrl;
  }

  return `${configuredBaseUrl}/`;
}

export function getCalendarFeedBaseUrl() {
  return `${getCalendarApiBaseUrl().replace(/\/$/, '')}/api/v1/calendar/feed`;
}

export function getCalendarWizardDefaultScope({
  source = 'calendar',
  includeMinorFeasts = false,
} = {}) {
  if (source !== 'calendar') {
    return 'major_minor';
  }
  return includeMinorFeasts ? 'major_minor' : 'major';
}

export function getCalendarFeedUrl(
  scope,
  { canceled = false, download = false } = {}
) {
  const feedBaseUrl = getCalendarFeedBaseUrl();
  const basePath = canceled
    ? `${feedBaseUrl}/${scope}/cancel.ics`
    : `${feedBaseUrl}/${scope}.ics`;

  if (!download) {
    return basePath;
  }
  return `${basePath}?download=1`;
}

export function getCalendarWebcalUrl(scope) {
  return getCalendarFeedUrl(scope).replace(/^https?:\/\//, 'webcal://');
}

export function getCalendarProviderLink(provider) {
  return CALENDAR_PROVIDER_LINKS[provider] || null;
}

export function getCalendarProviderHelpLink(provider) {
  return CALENDAR_PROVIDER_HELP_LINKS[provider] || null;
}

/** Apple, Google, Outlook, and Yahoo: label, icon, and official subscribe/import help. */
export function getCalendarDocumentationLinks() {
  return ['apple', 'google', 'outlook', 'yahoo']
    .map((key) => {
      const option = CALENDAR_APP_OPTIONS.find((o) => o.value === key);
      const url = CALENDAR_PROVIDER_HELP_LINKS[key];
      if (!option || !url) {
        return null;
      }
      return {
        value: key,
        label: option.label,
        icon: option.icon,
        url,
      };
    })
    .filter(Boolean);
}

export function getCalendarPrimaryActionLabel(provider, method) {
  if (method === 'import') {
    return 'Download .ics';
  }

  if (provider === 'apple') {
    return 'Subscribe in Apple Calendar';
  }
  if (provider === 'google') {
    return 'Copy URL and Open Google Calendar';
  }
  if (provider === 'outlook') {
    return 'Copy URL and Open Outlook';
  }
  if (provider === 'yahoo') {
    return 'Copy URL and Open Yahoo Calendar';
  }
  return 'Copy Subscription URL';
}

export function getCalendarProviderInstructions(provider, method) {
  if (method === 'import') {
    const shared = [
      'Use the main button to download the .ics file.',
      'Imports are a one-time copy and will not get future updates.',
      'To remove imported events later, use the cancellation feed (Undo import on this step).',
    ];

    if (provider === 'google') {
      return [
        ...shared,
        'In Google Calendar on desktop, use Settings or the import tool to upload the file.',
      ];
    }
    if (provider === 'outlook') {
      return [
        ...shared,
        'In Outlook, use Add calendar and then Upload from file.',
      ];
    }
    if (provider === 'yahoo') {
      return [
        ...shared,
        'Yahoo import support varies, so the file download is the safest starting point.',
      ];
    }
    return shared;
  }

  if (provider === 'apple') {
    return [
      'Use the button below to open the subscription link directly.',
      'Apple Calendar should offer to subscribe and keep the calendar updated across your devices.',
    ];
  }
  if (provider === 'google') {
    return [
      'We will copy the calendar URL for you before opening Google Calendar.',
      'In Google Calendar on desktop, open Other calendars, choose From URL, paste the link, and add it.',
      'Google does not support adding a public calendar by URL from mobile alone.',
    ];
  }
  if (provider === 'outlook') {
    return [
      'We will copy the calendar URL for you before opening Outlook Calendar.',
      'In Outlook, choose Add calendar, then Subscribe from web, paste the URL, and import it.',
    ];
  }
  if (provider === 'yahoo') {
    return [
      'We will copy the calendar URL for you before opening Yahoo Calendar.',
      'In Yahoo Calendar, use Follow Other Calendars and paste the iCal URL.',
    ];
  }
  return [
    'Copy the subscription URL and paste it into any calendar that supports public .ics subscriptions.',
    'If your calendar supports webcal links, you can also try the quick-open button.',
  ];
}
