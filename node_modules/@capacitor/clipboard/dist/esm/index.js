import { registerPlugin } from '@capacitor/core';
import { ClipboardWeb } from './web';
const Clipboard = registerPlugin('Clipboard', {
    web: () => new ClipboardWeb(),
});
export * from './definitions';
export { Clipboard };
//# sourceMappingURL=index.js.map