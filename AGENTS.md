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
  - Styled by its own design system: tokens in `app/src/styles/`, a small UI kit in `app/src/ui/`. No Tailwind, Element Plus, or Font Awesome.
  - State management via **Vuex**, routing via **Vue Router**.
  - Testing is handled by **Vitest** (Unit) and **Cypress** (E2E).
  - Also includes Capacitor for mobile builds.
  
- **`site/`**: The main Django project directory (Backend).
  - Contains standard Django apps (like `website/`) holding core logic, models, views, and custom management commands.
  - Backend pages use standalone assets or Python-provided admin/editor/API-doc assets. The retired legacy prayer display and HTML 404 no longer require npm or Webpack. Preserve collectstatic, static serving, and email CSS.

## 💻 Vue Frontend Standards (`app/`)

1. **Composition API**: Use Vue 3's Composition API. Prefer `<script setup>` syntax for all new components.
2. **Design system**: The look comes from one place, so keep it consistent.
   - **Tokens** (`src/styles/tokens.css`): every color, space, radius, and type size. Use `var(--paper)`, `var(--ink-soft)`, `var(--accent)`, `var(--space-4)`, `var(--text-sm)`, etc. Never hard-code hex colors; the light, sepia, and dark themes depend on it. `--accent` is the day's liturgical color.
   - **UI kit** (`src/ui/`, registered globally): `UiButton`, `UiIcon`, `UiSegmented`, `UiSwitch`, `UiSheet` (drawers, bottom sheets, dialogs), `UiAlert`, `UiField`, `UiInput`, `UiSelect`, `UiCheckbox`, `UiTag`, `UiDisclosure`, `Ornament`. Use `toast`/`confirm` from `@/ui/feedback` for messages and confirmations. Icons are `<UiIcon name="calendar" />` (names in `src/ui/iconData.js`).
   - **Shared classes** (`src/styles/base.css`): `.page`, `.page-header`, `.page-title`, `.page-lede`, `.section-title`, `.eyebrow`, `.surface`, `.divider`, `.stack`, `.cluster`, `.sheet-block`. Form controls use `.ui-control`, `.ui-check`, `.ui-range` (`src/styles/forms.css`).
   - **Liturgical text** (`src/styles/book.css`): wrap prayers, readings, and psalms in `.book`. It follows the 2019 BCP: small-caps titles and citations, semibold congregational text, smaller italic rubrics. Keep changes here minimal and faithful to the printed book.
   - **Component styles** go in `<style scoped>` using tokens. Typography is Adobe Caslon Pro throughout; labels use small caps (`font-variant-caps: all-small-caps`) rather than bold or uppercase.
   - **Display preferences** (theme, text size, reading typeface, audio) live in `src/helpers/displayPreferences.js`. App-wide sheets (menu, display, share, email, feedback) open via `openPanel()` from `src/helpers/panels.js`.
3. **Responsiveness**: Design for 320px phones up to wide desktops. Check every change at phone, tablet, and desktop widths, and respect safe-area insets.
4. **State Management**: Adhere to the existing Vuex store structure. Do not mutate state directly outside of actions/mutations.
5. **Testing**: Write tests for new components or complex logic using Vitest. Ensure tests pass before committing.

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
- **Deploying**: `master` is the only long-lived branch; deploy with `make deploy` (see "Deploying" in README.md). There are no deploy branches.
