import AutoImport from "unplugin-auto-import/webpack";
import Components from "unplugin-vue-components/webpack";
import {ElementPlusResolver} from "unplugin-vue-components/resolvers";


export default {
    css: {
        extract: false,
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
};
