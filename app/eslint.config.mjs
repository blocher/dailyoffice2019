import globals from 'globals';
import eslintJs from '@eslint/js'; // Import CommonJS module for eslint:recommended
import vue from 'eslint-plugin-vue';
import prettierPlugin from 'eslint-plugin-prettier';
import vueScopedCss from 'eslint-plugin-vue-scoped-css';
import vueEslintParser from 'vue-eslint-parser';
import cypressPlugin from 'eslint-plugin-cypress';

// Use a simpler config approach
export default [
  // Basic eslint recommended rules
  eslintJs.configs.recommended,

  // Vue files specific configuration
  {
    files: ['**/*.vue'],
    plugins: {
      vue,
    },
    languageOptions: {
      parser: vueEslintParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    rules: {
      // Common Vue rules that should be present in most versions
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'off',
      'vue/no-v-text-v-html-on-component': 'off',
      'vue/no-deprecated-slot-attribute': 'error',
      'vue/no-unused-components': 'error',
      'vue/require-v-for-key': 'error',
      'vue/no-use-v-if-with-v-for': 'error',
    },
  },

  // General JS/Vue configuration
  {
    files: ['**/*.js', '**/*.vue'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
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
      // Basic rules
      'no-console': 'error',
      'no-debugger': 'error',
      'no-unused-vars': 'error',

      // Prettier rule
      'prettier/prettier': 'error',

      // Cypress rules
      'cypress/no-assigning-return-values': 'error',
      'cypress/no-unnecessary-waiting': 'error',
      'cypress/assertion-before-screenshot': 'warn',
      'cypress/no-force': 'warn',
      'cypress/no-async-tests': 'error',
      'cypress/no-pause': 'error',
    },
  },

  // Files to ignore
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
