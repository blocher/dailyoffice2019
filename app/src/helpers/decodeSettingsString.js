export const decodeSettingsString = (currentSettings, settingAbbreviations) => {
    let decodedOptions = [];
    if (Object.values(settingAbbreviations).length !== currentSettings.length) {
        // If the resulting string is not equal to the number of possible settings, then return a blank array,
        // so that a warning message can be displayed.
        return [];
    }
    for (const [index, character] of currentSettings.split('').entries()) {
        let value = '';
        settingAbbreviations[index].options.forEach((optionValue) => {
            if (character === optionValue.abbreviation) {
                value = optionValue.option_value;
            }
        });
        if (value === '') {
            // A value is missing, so return a blank array, so that a warning message can be displayed.
            decodedOptions = [];
            break;
        }
        decodedOptions.push({
            settingName: settingAbbreviations[index].setting_name,
            value: value
        });
    }
    return decodedOptions;
};