import { registerPlugin } from '@capacitor/core';
const Browser = registerPlugin('Browser', {
    web: () => import('./web').then((m) => new m.BrowserWeb()),
});
export * from './definitions';
export { Browser };
//# sourceMappingURL=index.js.map