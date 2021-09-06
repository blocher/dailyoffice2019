# Netlify Plugin Edge Handlers

This plugin is used to bundle Edge Handlers for deployment. It is included in the list of core plugins in Netlify's
build, meaning that any handler under the `netlify/edge-handlers` directory will be bundled by Netlify's buildbot.

## Usage

This plugin is already integrated into Netlify's build process and will not need to be included in your project for Edge
Handlers to work.

To run this plugin locally in an existing project that has Edge Handlers, you'll need to install the netlify build
codebase locally and symlink this plugin to that repo. To do so:

1. Clone the build repo and install dependencies

```sh
git clone git@github.com:netlify/build.git

npm i
```

2. Create a symlink from netlify-build/packages/build/node_modules/@netlify/plugin-edge-handlers towards the Edge
   handlers plugin's root directory. You can do this manually with `ln -s` or `npm link`

3. To verify that this step worked, cd /path/to/netlify-build/packages/build, then node -p
   'require("@netlify/plugin-edge-handlers")' which should print the onPostBuild exported function

4. Run the plugin locally in your project by typing in your project directory:

```sh
/path/to/netlify-build/packages/build/src/core/bin.js
```
