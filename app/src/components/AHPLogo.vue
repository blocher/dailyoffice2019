<template>
  <div class="h-full flex flex-col">
    <a
      href="https://anglicanhousepublishers.org/shop/the-book-of-common-prayer-2019-pew-edition/"
      target="_blank"
      class="block group h-full"
    >
      <div
        class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-center rounded-lg p-6 transition-colors duration-200 hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 space-y-4 h-full flex flex-col justify-center"
      >
        <p class="text-sm font-medium text-gray-600 dark:text-gray-300">
          This site is generously supported by Anglican House Publishers
        </p>

        <img
          src="@/assets/ahp_new.png"
          alt="Anglican House Publishers Logo"
          class="h-16 mx-auto object-contain"
        />

        <div class="text-sm text-gray-700 dark:text-gray-300">
          <p>Publisher of the</p>
          <p class="font-bold text-gray-900 dark:text-gray-100 mt-1">
            Anglican Church in North America's<br />2019 Edition of the Book of
            Common Prayer
          </p>
          <p class="mt-1">on which this website is based.</p>
        </div>

        <p
          class="text-xs text-gray-600 dark:text-gray-300 font-medium group-hover:text-gray-800 dark:group-hover:text-gray-100"
        >
          Click to purchase a paper copy →
        </p>
      </div>
    </a>
  </div>
</template>

<script>
export default {
  name: 'AHPLogo',
};
</script>

<style scoped>
/* Removed legacy styles */
</style>
