import { onMounted, onUnmounted, ref } from "vue";

export function useFlexibleDrawer() {
  const panelSize = ref(0);

  function update(event) {
    if (window.innerWidth < 1024) {
      panelSize.value = "90%";
    } else {
      panelSize.value = "37%";
    }
  }

  onMounted(() => {
    window.addEventListener("resize", update);
    update();
  });

  onUnmounted(() => {
    window.removeEventListener("resize", update);
  });

  return { panelSize };
}
