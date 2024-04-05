export const createSettingsString = (settings, settingAbbreviations) => {
    let settingsString = '';
    settingAbbreviations.forEach((option) => {
        option.options.forEach((optionValue) => {
            if (settings[option.setting_name] === optionValue.option_value) {
                settingsString += optionValue.abbreviation;
            }
        });
    });
    return settingsString;
};
