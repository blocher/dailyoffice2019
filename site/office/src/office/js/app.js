import { Plugins } from '@capacitor/core';
const { App } = Plugins;


const analytics = () => {
    if (window.mode == "app") {
        Plugins.CapacitorFirebaseAnalytics.setScreenName({ screenName: document.title, screenClassOverride: document.title });
    }
}

const deepLinks = () => {
    if (window.mode == "app") {
        App.addListener('appUrlOpen', (data) => {
            this.zone.run(() => {
                let path = data.url.split(".com").pop();
                if (path.indexOf('?')) {
                    path = path.replace('?', 'index.html?')
                } else {
                    path = path + 'index.html'
                }
                console.log(path)
                if (path) {
                    this.router.navigateByUrl(path);
                }
            });
        })
    }
}


const setupAnalytics = () => {
    if (
        document.readyState === "complete" ||
        (document.readyState !== "loading" && !document.documentElement.doScroll)
    ) {
        analytics();
    } else {
        document.addEventListener("DOMContentLoaded", analytics);
    }
};

const setupDeepLinks = () => {
    if (
        document.readyState === "complete" ||
        (document.readyState !== "loading" && !document.documentElement.doScroll)
    ) {
        deepLinks();
    } else {
        document.addEventListener("DOMContentLoaded", deepLinks);
    }
};

const setupApp = () => {
    setupAnalytics();
    setupDeepLinks();
};

export {setupApp};

