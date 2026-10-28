import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const bugsnag = vi.hoisted(() => {
  const vuePlugin = { install: vi.fn() };
  return {
    vuePlugin,
    start: vi.fn(),
    notify: vi.fn(),
    setUser: vi.fn(),
    getPlugin: vi.fn(() => vuePlugin),
  };
});

vi.mock('@bugsnag/js', () => ({ default: bugsnag }));
vi.mock('@bugsnag/plugin-vue', () => ({ default: class BugsnagPluginVue {} }));
vi.mock('@capacitor/core', () => ({
  Capacitor: { getPlatform: () => 'web' },
}));

// A fresh copy of the module (and its "started" state) for each test.
async function load() {
  vi.resetModules();
  return import('@/helpers/errorReporting');
}

function fakeEvent(
  error = {},
  originalError = new Error('x'),
  breadcrumbs = []
) {
  return {
    errors: [
      { errorClass: 'Error', errorMessage: '', stacktrace: [], ...error },
    ],
    originalError,
    breadcrumbs,
  };
}

// The breadcrumb BugSnag leaves when a fetch() gets no response.
function fetchError(url) {
  return {
    type: 'request',
    message: 'fetch() error',
    metadata: { method: 'GET', url },
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  window.sessionStorage.clear();
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('error reporting', () => {
  it('does nothing without an API key', async () => {
    vi.stubEnv('VITE_BUGSNAG_ENABLED', 'true');
    vi.stubEnv('VITE_BUGSNAG_API_KEY', '');
    const reporting = await load();
    expect(reporting.startErrorReporting({ use: vi.fn() })).toBe(false);
    expect(reporting.notify(new Error('boom'), { a: { b: 1 } })).toBe(false);
    reporting.identifyUser('client-1');
    expect(bugsnag.start).not.toHaveBeenCalled();
    expect(bugsnag.notify).not.toHaveBeenCalled();
    expect(bugsnag.setUser).not.toHaveBeenCalled();
  });

  it('does nothing when switched off, even with a key', async () => {
    vi.stubEnv('VITE_BUGSNAG_ENABLED', 'false');
    vi.stubEnv('VITE_BUGSNAG_API_KEY', 'abc123');
    const reporting = await load();
    expect(reporting.startErrorReporting({ use: vi.fn() })).toBe(false);
    expect(reporting.notify(new Error('boom'))).toBe(false);
    expect(bugsnag.start).not.toHaveBeenCalled();
  });

  describe('when enabled', () => {
    let reporting;
    let app;

    beforeEach(async () => {
      vi.stubEnv('VITE_BUGSNAG_ENABLED', 'true');
      vi.stubEnv('VITE_BUGSNAG_API_KEY', 'abc123');
      vi.stubEnv('VITE_BUGSNAG_RELEASE_STAGE', 'production');
      reporting = await load();
      app = { use: vi.fn() };
      expect(reporting.startErrorReporting(app)).toBe(true);
    });

    it('starts Bugsnag once, without IPs, and hooks into Vue', () => {
      expect(reporting.startErrorReporting(app)).toBe(false);
      expect(bugsnag.start).toHaveBeenCalledTimes(1);
      const config = bugsnag.start.mock.calls[0][0];
      expect(config).toMatchObject({
        apiKey: 'abc123',
        releaseStage: 'production',
        collectUserIp: false,
        generateAnonymousId: false,
        appType: 'web',
      });
      expect(config.enabledReleaseStages).toContain('production');
      expect(config.appVersion).toMatch(/^\d+\.\d+\.\d+/);
      expect(app.use).toHaveBeenCalledWith(bugsnag.vuePlugin);
    });

    it('forwards metadata and options with notify', () => {
      const error = new Error('boom');
      expect(
        reporting.notify(
          error,
          { bookView: { pages: 1 } },
          { context: 'Book view', severity: 'error', groupingHash: 'G' }
        )
      ).toBe(true);
      expect(bugsnag.notify).toHaveBeenCalledWith(error, expect.any(Function));
      const event = { addMetadata: vi.fn() };
      bugsnag.notify.mock.calls[0][1](event);
      expect(event.addMetadata).toHaveBeenCalledWith('bookView', { pages: 1 });
      expect(event).toMatchObject({
        context: 'Book view',
        severity: 'error',
        groupingHash: 'G',
      });
    });

    it('reports a notifyOnce key only once per session', () => {
      expect(reporting.notifyOnce('k', new Error('a'))).toBe(true);
      expect(reporting.notifyOnce('k', new Error('b'))).toBe(false);
      expect(reporting.notifyOnce('other', new Error('c'))).toBe(true);
      expect(bugsnag.notify).toHaveBeenCalledTimes(2);
    });

    it('remembers notifyOnce keys across page loads in the session', async () => {
      reporting.notifyOnce('k', new Error('a'));
      const reloaded = await load();
      reloaded.startErrorReporting(app);
      expect(reloaded.notifyOnce('k', new Error('a'))).toBe(false);
      expect(bugsnag.notify).toHaveBeenCalledTimes(1);
    });

    it('identifies the user by the anonymous client id', () => {
      reporting.identifyUser('client-1');
      expect(bugsnag.setUser).toHaveBeenCalledWith('client-1');
    });

    it('drops noise but keeps real errors', () => {
      const onError = bugsnag.start.mock.calls[0][0].onError;
      const noise = [
        fakeEvent({
          errorMessage: 'Failed to fetch dynamically imported module: x.js',
        }),
        fakeEvent({ errorMessage: 'Importing a module script failed.' }),
        fakeEvent({
          errorMessage:
            'Couldn\'t resolve component "default" at "/privacy-policy"',
        }),
        fakeEvent({
          errorMessage:
            'ResizeObserver loop completed with undelivered notifications.',
        }),
        fakeEvent({
          stacktrace: [{ file: 'chrome-extension://abc/content.js' }],
        }),
        fakeEvent({
          errorClass: 'Error',
          errorMessage: 'Invalid call to runtime.sendMessage(). Tab not found.',
        }),
        fakeEvent(
          {
            errorClass: 'TypeError',
            errorMessage: 'Load failed',
            stacktrace: [{ file: 'unknown file', lineNumber: 0 }],
          },
          new TypeError('Load failed'),
          [fetchError(`${window.location.origin}/assets/web-L0Bi5kY9.js`)]
        ),
        fakeEvent(
          { errorClass: 'TypeError', errorMessage: 'Failed to fetch' },
          new TypeError('Failed to fetch'),
          [fetchError('/assets/index-abc123.js')]
        ),
        fakeEvent(
          { errorClass: 'AxiosError', errorMessage: 'Network Error' },
          { isAxiosError: true, code: 'ERR_NETWORK' }
        ),
        fakeEvent(
          {
            errorClass: 'TypeError',
            errorMessage:
              "Cannot read properties of null (reading 'nextSibling')",
          },
          new TypeError('x'),
          [fetchError('https://reader.self')]
        ),
        // A script injected into the page document, not our bundle.
        fakeEvent({
          errorClass: 'RangeError',
          errorMessage: 'Maximum call stack size exceeded.',
          stacktrace: [
            { file: `${window.location.href}`, lineNumber: 193 },
            { file: '', lineNumber: 0 },
            {
              file: `${window.location.origin}${window.location.pathname}?x=1`,
              lineNumber: 425,
            },
          ],
        }),
      ];
      noise.forEach((event) => expect(onError(event)).toBe(false));
      expect(
        onError(
          fakeEvent({ errorClass: 'TypeError', errorMessage: 'x is undefined' })
        )
      ).toBe(true);
      // The same Vue error without reader mode is a real bug.
      expect(
        onError(
          fakeEvent({
            errorClass: 'TypeError',
            errorMessage:
              "Cannot read properties of null (reading 'nextSibling')",
          })
        )
      ).toBe(true);
      // A page-document frame next to one of our bundle's frames is ours.
      expect(
        onError(
          fakeEvent({
            errorClass: 'RangeError',
            errorMessage: 'Maximum call stack size exceeded.',
            stacktrace: [
              { file: window.location.href, lineNumber: 5 },
              { file: `${window.location.origin}/assets/index-abc.js` },
            ],
          })
        )
      ).toBe(true);
      // A failed fetch raised from our own code is still worth seeing.
      expect(
        onError(
          fakeEvent(
            {
              errorClass: 'TypeError',
              errorMessage: 'Load failed',
              stacktrace: [
                { file: 'https://www.dailyoffice2019.com/assets/x.js' },
              ],
            },
            new TypeError('Load failed'),
            [fetchError('/assets/web-L0Bi5kY9.js')]
          )
        )
      ).toBe(true);
      // So is one from another service (it may be down), or one with no
      // failed request to explain it.
      [
        [fetchError('https://firebaseinstallations.googleapis.com/v1/x')],
        [
          fetchError('/assets/web-L0Bi5kY9.js'),
          fetchError('https://firebaseinstallations.googleapis.com/v1/x'),
        ],
        [],
      ].forEach((breadcrumbs) =>
        expect(
          onError(
            fakeEvent(
              { errorClass: 'TypeError', errorMessage: 'Load failed' },
              new TypeError('Load failed'),
              breadcrumbs
            )
          )
        ).toBe(true)
      );
      // A server error is a real problem, not an offline blip.
      expect(
        onError(
          fakeEvent(
            { errorClass: 'AxiosError' },
            { isAxiosError: true, code: 'ERR_BAD_RESPONSE', response: {} }
          )
        )
      ).toBe(true);
    });
  });
});
