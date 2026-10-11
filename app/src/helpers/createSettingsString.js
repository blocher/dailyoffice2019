export const createSettingsString = (settings, settingAbbreviations) => {
  let settingsString = '';
  settingAbbreviations.forEach((option) => {
    option.options.forEach((optionValue) => {
      if (settings[option.setting_name] === optionValue.option_value) {
        settingsString += optionValue.abbreviation;
      }
    });
  });
  if (Object.values(settings).length !== settingsString.length) {
    // If the resulting string is not equal to the number of possible settings, then return false,
    // as the settings string is invalid. We will return the default link in this case.
    return false;
  }
  return settingsString;
};
