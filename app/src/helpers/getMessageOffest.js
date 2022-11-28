export const getMessageOffset = () => {
  const notch = parseInt(
    getComputedStyle(document.documentElement)
      .getPropertyValue("--sat")
      .replace("px", "")
  );
  return notch + 20;
};
