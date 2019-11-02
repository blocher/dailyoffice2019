const postcss = require('postcss');
const postcssPresetEnv = require('postcss-preset-env');

module.exports = {
  plugins: [
    require('autoprefixer'),
    postcssPresetEnv(/* pluginOptions */)
  ]
}
