import {
  Plugins,
  StatusBarStyle,
} from '@capacitor/core';

const { StatusBar, Storage } = Plugins;

const clipboard = require("clipboard-polyfill/dist/clipboard-polyfill.promise");

export async function setItem(key, value) {
  await Storage.set({
    key: key,
    value: value
  });
}

export async function getItem(key) {
  const item = await Storage.get({ key: key });
  return item.value;
}

export async function removeItem(key) {
  await Storage.remove({
    key: key
  });
}

function localStorageExists() {
    let test = "test";
    try {
        setItem(test, test);
        removeItem(test);
        return true;
    } catch (e) {
        return false;
    }
}


const settings = () => {
    const setUpStatusBar =  () => {
        StatusBar.setOverlaysWebView({
          overlay: false
        });
        StatusBar.setBackgroundColor({
          color : document.getElementsByTagName("body")[0].style.backgroundColor
        });
        StatusBar.setStyle({
          style: getActiveTheme() == 'dark' ? StatusBarStyle.Dark : StatusBarStyle.Light
        });
    }
    const applySettingFromElement = element => {
        let class_to_hide = element.dataset.class_to_hide.split(',');
        let class_to_show = element.dataset.class_to_show.split(',');

        class_to_hide.forEach((value, idx) => {
            Array.from(document.getElementsByClassName(value)).forEach(
                (element, element_index) => {
                    element.classList.add("off");
                }
            );
        });
        class_to_show.forEach((value, idx) => {
            Array.from(document.getElementsByClassName(value)).forEach(
                (element, element_index) => {
                    element.classList.remove("off");
                }
            );
        });
    };

    const getSetting = async (property) => {
        property = "setting_" + property;
        const settings = await getSettingsFromStorage();
        if (settings.hasOwnProperty(property)) {
            return settings[property]
        }
        return false;
    };

    const getSettingsFromStorage = async () => {
        let settings = await getItem("settings");
        if (!settings || settings == "null") {
            return {};
        }
        return JSON.parse(settings);
    };

    const putSettingsInStorage = settings => {
        setItem("settings", JSON.stringify(settings));
    };

    const storeSetting = async element => {
        if (!localStorageExists()) {
            return;
        }

        let settings = await getSettingsFromStorage();
        settings[element.name] = element.value;
        putSettingsInStorage(settings);
        document.getElementById("settings-link").value = getSettingsLink()
    };

    const findGetParameter = parameterName => {
        var result = null,
            tmp = [];
        location.search
            .substr(1)
            .split("&")
            .forEach(function (item) {
                tmp = item.split("=");
                if (tmp[0] === parameterName) result = decodeURIComponent(tmp[1]);
            });
        return result;
    };

    const initializeSetting = async element => {
        const fromURL = findGetParameter(element.name);
        if (fromURL && element.value == fromURL) {
            element.checked = true;
            applySettingFromElement(element);
            storeSetting(element);
            return;
        }
        if (localStorageExists()) {
            let settings = await getSettingsFromStorage();
            let stored = settings[element.name] || null;
            if (stored && element.value == stored) {
                element.checked = true;
                applySettingFromElement(element);
            }
        }
    };

    const showAndHideSavedLabel = async element => {
        document.getElementById("saved_" + element.name).classList.remove("off");
        setTimeout(function () {
            document.getElementById("saved_" + element.name).classList.add("off");
        }, 2000);
    };

    const addRadioButtonListeners = () => {
        document
            .querySelectorAll(".settings-radio")
            .forEach((element, element_index) => {
                element.addEventListener("change", event => {
                    applySettingFromElement(event.target);
                    storeSetting(event.target);
                    showAndHideSavedLabel(event.target)
                });
            });
    };

    const initializeSettings = () => {
        document
            .querySelectorAll(".settings-radio")
            .forEach((element, element_index) => {
                initializeSetting(element);
            });
        window.history.replaceState({}, document.title, location.protocol + '//' + location.host + window.location.pathname + window.location.hash);
    };

    const addSettingsMenuToggle = () => {
        document
            .querySelectorAll(".toggle-settings")
            .forEach((element, element_index) => {
                element.addEventListener("click", event => {
                    document.getElementById("settings").classList.toggle("off");
                    document.getElementById("office").classList.toggle("off");
                    // document.querySelectorAll(".toggle-settings").forEach((element, index) => {
                    //   element.classList.toggle("off")
                    // });
                });
            });
    };

    const bindBackButtons = () => {
        document
            .querySelectorAll(".back-button")
            .forEach((element, element_index) => {
                element.setAttribute('href', document.referrer);
                element.addEventListener("click", event => {
                    history.back();
                    return false;
                });
            });
    };


    const handleFontSizes = async () => {
        let base_font_size = await getItem("base-font-size");
        if (base_font_size) {
            document.getElementById("html").style.fontSize = base_font_size;
            document.getElementsByClassName("font-size-selector").forEach((element, element_index) => {
                element.classList.remove('fas');
                element.classList.add('fal')
            });
            document.querySelectorAll('[data-fontsize]').forEach((element, element_index) => {
                if (element.getAttribute('data-fontsize') == base_font_size.replace('px', '')) {
                    element.classList.remove('fal');
                    element.classList.add('fas');
                }
            });

        }
        document.querySelectorAll(".font-size-selector").forEach((element, element_index) => {
            element.addEventListener("click", event => {
                document.getElementById("html").style.fontSize = event.currentTarget.getAttribute('data-fontsize') + 'px';
                document.getElementsByClassName("font-size-selector").forEach((element, element_index) => {
                    element.classList.remove('fas');
                    element.classList.add('fal')
                });
                event.currentTarget.classList.remove('fal');
                event.currentTarget.classList.add('fas');
                document.getElementById("html").style.fontSize = event.currentTarget.getAttribute('data-fontsize');
                setItem("base-font-size", event.target.getAttribute('data-fontsize') + 'px');
            });
        });
    };

    const setThemeIcon = () => {

        document.getElementsByClassName("theme-selector").forEach((element, element_index) => {
            element.classList.remove('fas');
            element.classList.add('fal')
        });
        const theme = document.getElementById('html').classList[0];
        document.querySelectorAll('i[data-theme=' + theme + ']').forEach((element) => {
            element.classList.add('fas');
            element.classList.remove('fal');
        });

    };

    const getActiveTheme = () => {
        let theme = getSetting("theme");
        if (theme == "theme-dark") {
            return 'dark';
        }
        if (theme == "theme-light") {
            return 'light';
        }
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    const handleThemes = async () => {
        let theme = await getSetting("theme");
        if (!theme || theme == "theme-auto") {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                theme = "theme-dark";
            } else {
                theme = "theme-light";
            }
            storeSetting({"name": "setting_theme", "value": "theme-auto"});
            initializeSettings();
        }
        if (theme) {
            theme = theme.trim();
            document.getElementById("html").className = "";
            document.getElementById("html").classList.add(theme);
            setThemeIcon();
        }
        document.querySelectorAll(".theme-selector").forEach((element, element_index) => {
            element.addEventListener("click", event => {
                theme = event.currentTarget.getAttribute('data-theme');
                if (!theme || theme == "theme-auto") {
                    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                        theme = "theme-dark";
                    } else {
                        theme = "theme-light";
                    }
                }
                document.getElementById("html").className = theme;
                document.getElementsByClassName("theme-selector").forEach((element, element_index) => {
                    element.classList.remove('fas');
                    element.classList.add('fal')
                });
                event.currentTarget.classList.remove('fal');
                event.target.classList.add('fas');
                setThemeIcon();
                setItem("theme", event.currentTarget.getAttribute('data-theme'));
                storeSetting({"name": "setting_theme", "value": event.currentTarget.getAttribute('data-theme')});
                initializeSettings();
                setUpStatusBar();
            });
        });
        setUpStatusBar();
    };

    const getSettingsLink = () => {

        let params = {};
        document
            .querySelectorAll(".settings-radio:checked")
            .forEach((element, element_index) => {
                params[element.name] = element.value;
            });

        params = new URLSearchParams(params);
        let path = location.protocol + '//' + location.host + location.pathname;
        return path + "?" + params
    };

    const copySettingsLink = () => {
        /* Get the text field */
        let text = document.getElementById("settings-link").value;

        clipboard.writeText(text);

        document.getElementById('settings-link-copy').classList.add('off');
        document.getElementById("copied-message").classList.remove("off");
        setTimeout(function () {
            document.getElementById("copied-message").classList.add("off");
            document.getElementById("settings-link-copy").classList.remove("off");
        }, 2000);

    };

    const bindShowSettingsLink = () => {
        document.getElementById("settings-link").value = getSettingsLink();
        document
            .querySelectorAll(".show-settings-link")
            .forEach((element, element_index) => {
                element.addEventListener("click", event => {
                    document.getElementById('settings-link-view').classList.remove('off');
                    document.getElementById('show-settings-link').classList.add('off');
                    event.preventDefault();
                });
            });

        document.getElementById("settings-link").addEventListener("focus", event => {
            copySettingsLink();
            event.target.select();
        });

        document.getElementById("settings-link-copy").addEventListener("click", event => {
            copySettingsLink();
            event.preventDefault();
        });
    };

    const setupSettings = () => {
        setUpStatusBar()
        initializeSettings();
        addRadioButtonListeners();
        addSettingsMenuToggle();
        bindBackButtons();
        handleFontSizes();
        handleThemes();
        bindShowSettingsLink();
    };

    // TODO: Refactor into reusable module
    if (
        document.readyState === "complete" ||
        (document.readyState !== "loading" && !document.documentElement.doScroll)
    ) {
        setupSettings();
    } else {
        document.addEventListener("DOMContentLoaded", setupSettings);
    }
};

export {settings};
