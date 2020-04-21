import { Plugins } from '@capacitor/core';


const analytics = () => {
    if (window.mode == "app") {
        Plugins.CapacitorFirebaseAnalytics.setScreenName({ screenName: document.title }).then(response => {}).catch(e => {});
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

export {setupAnalytics};

