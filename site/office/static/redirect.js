var redirect = function() {
  const date = new Date();
  const date_string = `${date.getFullYear()}-${date
    .getMonth()
    .toString()
    .padStart(2, "0")}-${date
    .getDate()
    .toString()
    .padStart(2, "0")}`;
  const path = `\\office\\evening_prayer\\${date_string}`;
  console.log(path);
  // window.location.pathname = path;
};

if (
  document.readyState === "complete" ||
  (document.readyState !== "loading" && !document.documentElement.doScroll)
) {
  redirect();
} else {
  document.addEventListener("DOMContentLoaded", redirect);
}
