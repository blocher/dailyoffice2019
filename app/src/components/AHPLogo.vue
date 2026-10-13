<template>
  <a
    href="https://anglicanhousepublishers.org/shop/the-book-of-common-prayer-2019-pew-edition/"
    target="_blank"
    rel="noopener"
    class="ahp-card surface"
  >
    <p class="eyebrow">Generously supported by</p>
    <span class="ahp-card__plate">
      <img
        src="@/assets/ahp_new.png"
        alt="Anglican House Publishers"
        class="ahp-card__logo"
        width="320"
        height="147"
      />
    </span>
    <p class="ahp-card__copy">
      Publisher of the Anglican Church in North America’s
      <em>Book of Common Prayer (2019)</em>, on which this site is based.
    </p>
    <span class="ahp-card__cta">
      Buy a printed copy
      <UiIcon name="external" />
    </span>
  </a>
</template>

<script setup></script>

<style scoped>
.ahp-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  height: 100%;
  padding: var(--space-5);
  color: var(--ink);
  text-align: center;
  text-decoration: none;
  transition: border-color var(--duration) var(--ease);
}

.ahp-card:hover {
  border-color: var(--rule-strong);
}

.ahp-card__plate {
  display: block;
  border-radius: var(--radius);
}

.ahp-card__logo {
  width: 11rem;
  height: auto;
  mix-blend-mode: multiply;
}

:root.dark .ahp-card__plate {
  padding: var(--space-2) var(--space-3);
  background-color: #fff;
}

:root.dark .ahp-card__logo {
  mix-blend-mode: normal;
}

.ahp-card__copy {
  max-width: 22rem;
  font-size: var(--text-sm);
  color: var(--ink-soft);
  line-height: 1.4;
}

.ahp-card__cta {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: auto;
  font-size: var(--text-sm);
  color: var(--accent);
}
</style>
