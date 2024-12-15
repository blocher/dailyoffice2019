import vue from "eslint-plugin-vue";
import globals from "globals";
import parser from "vue-eslint-parser";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default [
    ...compat.extends("eslint:recommended", "plugin:vue/vue3-recommended", "prettier"),
    {
        plugins: {
            vue,
        },

        languageOptions: {
            globals: {
                ...globals.node,
            },

            parser: parser,
            ecmaVersion: "latest",
            sourceType: "module",

            parserOptions: {
                requireConfigFile: false,
            },
        },

        rules: {
            "no-console": "off",
            "no-debugger": "off",
            "vue/no-deprecated-slot-attribute": "off",
            "vue/no-unused-components": "warn",
            "no-unused-vars": "warn",
            "vue/multi-word-component-names": "off",
            "vue/script-setup-uses-vars": "error",
            "vue/no-v-html": "off",
            "vue/no-v-text-v-html-on-component": "off",
        },
    },
    {
        files: ["**/__tests__/*.{j,t}s?(x)", "**/tests/unit/**/*.spec.{j,t}s?(x)"],

        languageOptions: {
            globals: {
                ...globals.mocha,
            },
        },
    },
];