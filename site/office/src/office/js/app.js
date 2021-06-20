import { Plugins } from "@capacitor/core";
const { App } = Plugins;

const analytics = () => {
  if (window.mode == "app") {
    Plugins.CapacitorFirebaseAnalytics.setScreenName({
      screenName: document.title,
      screenClassOverride: document.title,
    });
  }
};

const deepLinks = () => {
  if (window.mode == "app") {
    App.addListener("appUrlOpen", (data) => {
      let path = data.url.split(".com").pop();
      if (path.indexOf("?")) {
        path = path.replace("?", "index.html?");
      } else {
        path = path + "index.html";
      }
      if (path) {
        window.location.href = path;
      }
    });
  }
};

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

const notices = () => {
  if (window.mode != "app") {
    return;
  }
  const axios = require("axios");
  axios
    .get("https://www.dailyoffice2019.com/update_notices/app.json")
    .then(function (response) {
      try {
        const html = document.getElementsByTagName("HTML")[0];
        const app_version = parseFloat(html.dataset.appversion);
        const update_notices_div = document.getElementById("update-notices");
        if (response.data[0].fields.version > app_version) {
          update_notices_div.classList.remove("off");
          let h3 = document.createElement("h3");
          h3.innerHTML =
            '<i class="fas fa-exclamation-circle"></i>App Update Available';
          update_notices_div.appendChild(h3);
        }
        response.data.forEach((entry) => {
          if (entry.fields.version > app_version) {
            let div = document.createElement("div");
            div.innerHTML = entry.fields.notice;
            update_notices_div.appendChild(div);
          }
        });
      } catch (e) {
        return;
      }
    });
};

const setupNotices = () => {
  if (
    document.readyState === "complete" ||
    (document.readyState !== "loading" && !document.documentElement.doScroll)
  ) {
    notices();
  } else {
    document.addEventListener("DOMContentLoaded", notices);
  }
};

const setupApp = () => {
  setupAnalytics();
  setupDeepLinks();
  setupNotices();
};

export { setupApp, setupNotices };
