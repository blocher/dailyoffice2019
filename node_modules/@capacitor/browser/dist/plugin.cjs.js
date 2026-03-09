'use strict';

var core = require('@capacitor/core');

const Browser = core.registerPlugin('Browser', {
    web: () => Promise.resolve().then(function () { return web; }).then((m) => new m.BrowserWeb()),
});

class BrowserWeb extends core.WebPlugin {
    constructor() {
        super();
        this._lastWindow = null;
    }
    async open(options) {
        this._lastWindow = window.open(options.url, options.windowName || '_blank');
    }
    async close() {
        return new Promise((resolve, reject) => {
            if (this._lastWindow != null) {
                this._lastWindow.close();
                this._lastWindow = null;
                resolve();
            }
            else {
                reject('No active window to close!');
            }
        });
    }
}
new BrowserWeb();

var web = /*#__PURE__*/Object.freeze({
    __proto__: null,
    BrowserWeb: BrowserWeb
});

exports.Browser = Browser;
//# sourceMappingURL=plugin.cjs.js.map
