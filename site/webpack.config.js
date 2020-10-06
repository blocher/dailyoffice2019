const fs = require("fs");
const WebpackOnBuildPlugin = require("on-build-webpack");
const BundleTracker = require("webpack-bundle-tracker");
const path = require("path");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
  entry: "./office/src/office/js/index.js",
  module: {
    rules: [
      {
        test: /\.(js)$/,
        exclude: /node_modules/,
        use: ["babel-loader"],
      },
      {
        test: /\.(s*)css$/,
        use: ["style-loader", "css-loader", "sass-loader", "postcss-loader"],
      },
      {
        test: /\.(woff(2)?|ttf|eot|svg|otf)(\?v=\d+\.\d+\.\d+)?$/,
        use: [
          {
            loader: "file-loader",
            options: {
              name: "[name].[ext]",
              outputPath: "fonts/",
            },
          },
        ],
      },
    ],
  },
  resolve: {
    extensions: ["*", ".js"],
  },
  output: {
    path: __dirname + "/office/static/office/js",
    publicPath: "/static/office/js/",
    filename: "bundle.[contenthash].js",
  },
  // optimization: {
  //   runtimeChunk: 'single',
  // },
  watch: true,
  watchOptions: {
    aggregateTimeout: 300,
    poll: 1000,
    ignored: /node_modules/,
  },
  mode: "development",
  plugins: [
    new CopyPlugin({
      patterns: [{ from: "office/src/office/img", to: "../img" }],
    }),
    new WebpackOnBuildPlugin(function (stats) {
      const buildDir = __dirname + "/office/static/office/js/";
      const newlyCreatedAssets = stats.compilation.assets;

      const unlinked = [];
      let res = fs.readdirSync(buildDir);
      res.forEach((file) => {
        if (!newlyCreatedAssets[file]) {
          try {
            if (!fs.lstatSync(buildDir + file).isDirectory()) {
              fs.unlinkSync(path.resolve(buildDir + file));
              unlinked.push(file);
            }
          } catch (err) {
            console.log(err);
          }
        }
      });
      if (unlinked.length > 0) {
        console.log("Removed old assets: ", unlinked);
      }
    }),
    new BundleTracker({ path: __dirname, filename: "./webpack-stats.json" }),
  ],
};
