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
  font-family: 'Adobe Caslon Pro', serif;
  border-color: var(--el-border-color);
  background-color: var(--color-bg);
  transition: all 0.2s ease;
  border-radius: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }
  
  p {
    font-family: 'Adobe Caslon Pro', serif;
    font-weight: 400;
    line-height: 1.5;
    color: var(--font-color);
    
    strong {
      font-weight: 600;
      color: var(--font-color);
    }
    
    small {
      opacity: 0.8;
      font-style: italic;
    }
  }
  
  // Book-like styling
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 0.5rem;
    background: linear-gradient(
      135deg,
      rgba(0, 0, 0, 0.01) 0%,
      transparent 50%,
      rgba(0, 0, 0, 0.01) 100%
    );
    pointer-events: none;
  }
  
  @media (max-width: 768px) {
    margin: 20px auto 80px;
    max-width: 90%;
  }
  
  @media (max-width: 480px) {
    margin: 15px auto 60px;
    padding: 1rem !important;
  }
}

// Dark mode adjustments
:root.dark .logoDiv {
  border-color: var(--el-border-color);
  background-color: var(--color-bg);
  
  &::before {
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.01) 0%,
      transparent 50%,
      rgba(255, 255, 255, 0.01) 100%
    );
  }
}
</style>
