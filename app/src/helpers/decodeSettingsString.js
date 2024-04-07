export const decodeSettingsString = (currentSettings, settingAbbreviations) => {
    let decodedOptions = [];
    for (const [index, character] of currentSettings.split('').entries()) {
        let value = '';
        if (typeof(settingAbbreviations[index]) === 'undefined') {
            // This is an old string, and new options have been added. Stop processing here.
            decodedOptions = [];
            break;
        }
        settingAbbreviations[index].options.forEach((optionValue) => {
            if (character === optionValue.abbreviation) {
                value = optionValue.option_value;
            }
        });
        if (value === '') {
            // There is an invalid value. Return a blank array so that a warning message can be displayed.
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