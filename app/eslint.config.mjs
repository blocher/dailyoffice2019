import globals from 'globals';
import eslintJs from '@eslint/js'; // Import CommonJS module for eslint:recommended
import vue from 'eslint-plugin-vue';
import prettierPlugin from 'eslint-plugin-prettier';
import vueScopedCss from 'eslint-plugin-vue-scoped-css';
import vueEslintParser from 'vue-eslint-parser';
import cypressPlugin from 'eslint-plugin-cypress';

export default [
  {
    files: ['**/*.js', '**/*.vue'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: vueEslintParser,
      globals: {
        ...globals.mocha,
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        location: 'readonly',
        history: 'readonly',
        getComputedStyle: 'readonly',
        console: 'readonly',
        module: 'readonly',
        require: 'readonly',
        process: 'readonly',
        __dirname: 'readonly',
        cy: 'readonly',
        Cypress: 'readonly',
        Audio: 'readonly',
      },
    },
    plugins: {
      vue,
      prettier: prettierPlugin,
      'vue-scoped-css': vueScopedCss,
      cypress: cypressPlugin,
    },
    rules: {
      ...cypressPlugin.configs.recommended.rules,
      ...eslintJs.configs.recommended.rules, // Include `eslint:recommended`
      ...vue.configs['vue3-recommended'].rules, // Vue 3 recommended rules
      // ...prettierConfig.rules, // Disable conflicting Prettier rules
      'prettier/prettier': 'error', // Run Prettier as an ESLint rule
      'no-console': 'error',
      'no-debugger': 'error',
      'vue/no-deprecated-slot-attribute': 'error',
      'vue/no-unused-components': 'error',
      'no-unused-vars': 'error',
      'vue/multi-word-component-names': 'off',
      'vue/script-setup-uses-vars': 'error',
      'vue/no-v-html': 'off',
      'vue/no-v-text-v-html-on-component': 'off',
    },
  },
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'ios/**',
      'android/**',
      'ios/**/*',
      'android/**/*',
    ],
  },
];

//            "no-console": "off",
//             "no-debugger": "off",
//             "vue/no-deprecated-slot-attribute": "off",
//             "vue/no-unused-components": "warn",
//             "no-unused-vars": "warn",
//             "vue/multi-word-component-names": "off",
//             "vue/script-setup-uses-vars": "error",
//             "vue/no-v-html": "off",
//             "vue/no-v-text-v-html-on-component": "off",
