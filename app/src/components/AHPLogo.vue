<template>
  <p class="text-center">
    <em>
      2019 Book of Common Prayer used by permission of the Anglican Church in
      North America</em
    >
  </p>
  <a
    href="https://anglicanhousepublishers.org/shop/the-book-of-common-prayer-2019-pew-edition/"
    target="_blank"
  >
    <div class="logoDiv text-center border-2 p-4 bg-white">
      <p>This site is generously supported by Anglican House Publishers</p>
      <img src="@/assets/ahp_new.png" class="mx-auto flex h-24 mt-6 mb-3" />
      <p>
        Publisher of the<br /><strong
          >Anglican Church in North America's<br />2019 Edition of the Book of
          Common Prayer</strong
        >,<br />on which this website is based.
      </p>
      <p><small>Click to purchase a paper copy.</small></p>
    </div>
  </a>
</template>

<script>
export default {
  name: 'AHPLogo',
};
</script>

<style lang="scss" scoped>
.logoDiv {
  max-width: 500px;
  margin: 25px auto 100px;
}
</style>
