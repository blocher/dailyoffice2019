# AI Agent Guidelines for DailyOffice2019

Welcome! As an AI agent working on this project, please adhere to the following layout conventions, coding standards, and workflow rules.

## 🚨 CRITICAL WORKFLOW RULE: Pre-commit 🚨

**YOU MUST RUN `pre-commit run` AFTER ALL AGENT WORK AND BEFORE COMMITTING.**

To answer the common question: **No, pre-commit does not need to be run on all files.** 
- **Standard workflow:** Run `pre-commit run`. This will quickly run the hooks **only on the files you have currently staged** for commit.
- **Deep architectural changes:** If you've made sweeping changes and want to be absolutely sure everything is pristine, you *may* run `pre-commit run --all-files`, but it is strictly optional and can be slow.

Do not skip the pre-commit step under any circumstances. If pre-commit modifies files or fails, you must re-stage the modifications and fix any remaining issues before proceeding. Double-check that all hooks pass successfully before concluding your tasks.

## Project Layout

This project is a full-stack application divided into a modern Vue frontend and a Django backend.
*(Note: You may hear the frontend referred to as the "client" app, but it is located in the `app/` directory.)*

- **`app/`**: The modern Vue 3 Frontend application.
  - Powered by **Vite**.
  - Uses **TailwindCSS v4** and **Element Plus** for styling and UI components.
  - State management via **Vuex**, routing via **Vue Router**.
  - Testing is handled by **Vitest** (Unit) and **Cypress** (E2E).
  - Also includes Capacitor for mobile builds.
  
- **`site/`**: The main Django project directory (Backend).
  - Contains standard Django apps (like `website/`) holding core logic, models, views, and custom management commands.
  - Also contains a classic frontend build pipeline (Webpack, Babel, SCSS) for older/legacy server-rendered views or emails. Ignore this as it is no longer used.

## 💻 Vue Frontend Standards (`app/`)

1. **Composition API**: Use Vue 3's Composition API. Prefer `<script setup>` syntax for all new components.
2. **Styling**: Utilize TailwindCSS utility classes as the primary styling method. Avoid custom CSS unless absolutely necessary. Use Element Plus components for complex UI elements (modals, forms, tables).
3. **State Management**: Adhere to the existing Vuex store structure. Do not mutate state directly outside of actions/mutations.
4. **Testing**: Write tests for new components or complex logic using Vitest. Ensure tests pass before committing.

## 🐍 Django Backend Standards (`site/`)

1. **Python Style**: Follow PEP 8. We use standard formatting tools (which are enforced by our pre-commit hooks).
2. **Django Best Practices**:
   - Keep views thin and push business logic to models or dedicated service layers.
   - Use the Django ORM efficiently (e.g., utilize `select_related` and `prefetch_related` to avoid N+1 queries).
3. **Testing**: Write tests for new backend features and bug fixes. Ensure tests pass before committing.
4. **Documentation**: Update relevant documentation or docstrings when modifying complex logic, but do not create new files for documentation.

## General Agent Instructions

- **Explore First**: Use your read and search tools to understand the existing patterns in both `app/` and `site/` before creating new files or modifying existing ones.
- **Match Style**: Always match the existing coding style of the file you are editing.
- **Verify**: After making changes, run relevant tests and **always run `pre-commit run`**.