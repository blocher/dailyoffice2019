const clipboard = require("clipboard-polyfill/dist/clipboard-polyfill.promise");

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
  }

  const initializeSetting = element => {
    const fromURL = findGetParameter(element.name)
    if (fromURL && element.value == fromURL) {
        element.checked = true;
        applySettingFromElement(element);
        storeSetting(element);
        return;
    }
    if (localStorageExists()) {
      let settings = getSettingsFromStorage();
      let stored = settings[element.name] || null;
      if (stored && element.value == stored) {
        element.checked = true;
        applySettingFromElement(element);
      }
    }
  };

  const showAndHideSavedLabel = async element => {
    document.getElementById("saved_" + element.name).classList.remove("off");
    setTimeout(function(){ document.getElementById("saved_" + element.name).classList.add("off"); }, 2000);
  }

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
    window.history.replaceState({}, document.title, location.protocol + '//' + location.host +  window.location.pathname + window.location.hash);
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


  const handleFontSizes = () => {
    let base_font_size = localStorage.getItem("base-font-size");
    if (base_font_size) {
      document.getElementById("html").style.fontSize = base_font_size;
      document.getElementsByClassName("font-size-selector").forEach( (element, element_index)  => {
            element.classList.remove('fas')
            element.classList.add('fal')
          })
      document.querySelectorAll('[data-fontsize]').forEach((element, element_index) => {
        if (element.getAttribute('data-fontsize') == base_font_size) {
          element.classList.remove('fal');
          element.classList.add('fas');
        }
      });

    }
    document.querySelectorAll(".font-size-selector").forEach((element, element_index) => {
        element.addEventListener("click", event => {
          document.getElementById("html").style.fontSize = event.target.getAttribute('data-fontsize');
          document.getElementsByClassName("font-size-selector").forEach( (element, element_index)  => {
            element.classList.remove('fas')
            element.classList.add('fal')
          })
          event.target.classList.remove('fal')
          event.target.classList.add('fas')
          localStorage.setItem("base-font-size", event.target.getAttribute('data-fontsize'));
        });
      });
    }

  const getSettingsLink = () => {

    let params = {}
    document
      .querySelectorAll(".settings-radio:checked")
      .forEach((element, element_index) => {
        params[element.name] = element.value;
      });

    params = new URLSearchParams(params);
    let path = location.protocol + '//' + location.host + location.pathname;
    return path + "?" + params
  }

  const  copySettingsLink = () => {
    /* Get the text field */
    let text = document.getElementById("settings-link").value;

    clipboard.writeText(text);

    document.getElementById('settings-link-copy').classList.add('off')
    document.getElementById("copied-message").classList.remove("off");
    setTimeout(function(){
      document.getElementById("copied-message").classList.add("off");
      document.getElementById("settings-link-copy").classList.remove("off");
    }, 2000);

  }

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
  }

  const setupSettings = () => {
    initializeSettings();
    addRadioButtonListeners();
    addSettingsMenuToggle();
    bindBackButtons();
    handleFontSizes();
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

export { settings };
