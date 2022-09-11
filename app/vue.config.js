const AutoImport = require("unplugin-auto-import/webpack");
const Components = require("unplugin-vue-components/webpack");
const {ElementPlusResolver} = require("unplugin-vue-components/resolvers");

module.exports = {
    css: {
        extract: false
    },
    configureWebpack: {
        plugins: [
            AutoImport({
                resolvers: [ElementPlusResolver()],
            }),
            Components({
                resolvers: [ElementPlusResolver()],
            }),
        ],
    },
    pwa: {
        name: 'Daily Office',
        themeColor: '#4DBA87',
        msTileColor: '#000000',
        appleMobileWebAppCapable: 'yes',
        appleMobileWebAppStatusBarStyle: 'black',
        // workboxPluginMode: "InjectManifest",
        // workboxOptions: {
        //     // swSrc is required in InjectManifest mode.
        //     swSrc: "service-worker.js", //path to your own service-worker file
        //     // ...other Workbox options...
        // },
        workboxPluginMode: 'GenerateSW',
        workboxOptions: {
            runtimeCaching: [
                {handler: 'NetworkFirst', urlPattern: new RegExp('.*')},
            ]
        }
    },
    // devServer: {
    //     open: process.platform === 'darwin',
    //     host: '0.0.0.0',
    //     port: 443,
    //     https: true,
    // },
};
