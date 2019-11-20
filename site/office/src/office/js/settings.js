function localStorageExists() {
  var test = "test";
  try {
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch (e) {
    return false;
  }
}

const settings = () => {
  const applySettingFromElement = element => {
    let class_to_hide = element.dataset.class_to_hide.split(',');
    let class_to_show = element.dataset.class_to_show.split(',');

    class_to_hide.forEach((value, idx) =>{
      Array.from(document.getElementsByClassName(value)).forEach(
          (element, element_index) => {
            element.classList.add("off");
          }
      );
    });
    class_to_show.forEach((value, idx) =>{
      Array.from(document.getElementsByClassName(value)).forEach(
          (element, element_index) => {
            element.classList.remove("off");
          }
      );
    });
  };

  const getSettingsFromStorage = () => {
    let settings = localStorage.getItem("settings");
    if (!settings || settings == "null") {
      return {};
    }
    return JSON.parse(settings);
  };

  const putSettingsInStorage = settings => {
    localStorage.setItem("settings", JSON.stringify(settings));
  };

  const storeSetting = element => {
    if (!localStorageExists()) {
      return;
    }

    let settings = getSettingsFromStorage();
    settings[element.name] = element.value;
    putSettingsInStorage(settings);
  };

  const initializeSetting = element => {
    if (localStorageExists()) {
      let settings = getSettingsFromStorage();
      let stored = settings[element.name] || null;
      if (stored && element.value == stored) {
        element.checked = true;
        applySettingFromElement(element);
      }
    }
  };

  const addRadioButtonListeners = () => {
    document
      .querySelectorAll(".settings-radio")
      .forEach((element, element_index) => {
        element.addEventListener("change", event => {
          applySettingFromElement(event.target);
          storeSetting(event.target);
        });
      });
  };

  const initializeSettings = () => {
    document
      .querySelectorAll(".settings-radio")
      .forEach((element, element_index) => {
        initializeSetting(element);
      });
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
  }

  const setupSettings = () => {
    initializeSettings();
    addRadioButtonListeners();
    addSettingsMenuToggle();
    bindBackButtons();
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

export { settings };
