/*
  UI kit
  ======
  The app's own small component set (it replaces Element Plus and Tailwind).
  Every component is registered globally, so templates can use <UiButton>,
  <UiSheet>, etc. without importing them. Styling comes from the tokens in
  src/styles/tokens.css.

    UiButton      primary | secondary | ghost | quiet | danger; sm | md | lg
    UiIcon        line icons by name (see iconData.js)
    UiSegmented   one choice from a few (pill or underline tabs)
    UiSwitch      on/off
    UiSheet       drawer, bottom sheet, dialog, or float panel
    UiAlert       inline notice
    UiField       label + hint/error around a control
    UiInput       text input / textarea
    UiSelect      native select
    UiCheckbox    checkbox (boolean or array model)
    UiTag         small-caps pill
    UiDisclosure  a row that folds open
    Ornament      a Caslon fleuron

  Imperative helpers: `toast` and `confirm` from './feedback'.
*/
import Ornament from './Ornament.vue';
import UiAlert from './UiAlert.vue';
import UiButton from './UiButton.vue';
import UiCheckbox from './UiCheckbox.vue';
import UiDisclosure from './UiDisclosure.vue';
import UiField from './UiField.vue';
import UiIcon from './UiIcon.vue';
import UiInput from './UiInput.vue';
import UiSegmented from './UiSegmented.vue';
import UiSelect from './UiSelect.vue';
import UiSheet from './UiSheet.vue';
import UiSwitch from './UiSwitch.vue';
import UiTag from './UiTag.vue';

export { toast, confirm } from './feedback';

const components = {
  Ornament,
  UiAlert,
  UiButton,
  UiCheckbox,
  UiDisclosure,
  UiField,
  UiIcon,
  UiInput,
  UiSegmented,
  UiSelect,
  UiSheet,
  UiSwitch,
  UiTag,
};

export default {
  install(app) {
    for (const [name, component] of Object.entries(components)) {
      app.component(name, component);
    }
  },
};
