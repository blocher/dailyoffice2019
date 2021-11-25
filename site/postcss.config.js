// eslint-disable-next-line no-unused-vars
const postcss = require("postcss");
const postcssPresetEnv = require("postcss-preset-env");

module.exports = {
  plugins: [require("autoprefixer"), postcssPresetEnv(/* pluginOptions */)],
};
// module.exports = {
//   plugins: {
//     tailwindcss: {},
//     autoprefixer: {},
//   }
// }
