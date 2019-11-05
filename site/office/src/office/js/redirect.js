var redirect = function() {
  if (document.getElementById("redirect-to-today")) {
    const date = new Date();
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hours = date.getHours()
    const office = hours >= 12 ? 'evening_prayer' : 'morning_prayer';
    const date_string = `${year}-${month}-${day}`;
    const path = `\\office\\${office}\\${date_string}`;
    console.log(hours);
    console.log(path);
    window.location.pathname = path;
  }
};

const setupRedirect = () =>
{
  if (
      document.readyState === "complete" ||
      (document.readyState !== "loading" && !document.documentElement.doScroll)
  ) {
    redirect();
  } else {
    document.addEventListener("DOMContentLoaded", redirect);
  }
}
export { setupRedirect };
