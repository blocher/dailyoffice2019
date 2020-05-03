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
            let path = data.url.split(".com").pop();
            if (path.indexOf('?')) {
                path = path.replace('?', 'index.html?')
            } else {
                path = path + 'index.html'
            }
            console.log(path)
            if (path) {
                window.location.href = path
            }
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

