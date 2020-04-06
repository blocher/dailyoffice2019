var redirect = function() {
  const date = new Date();
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hours = date.getHours();
  const office = hours >= 12 ? 'evening_prayer' : 'morning_prayer';
  const date_string = `${year}-${month}-${day}`;
  const path = `\\office\\${office}\\${date_string}.html`;
  console.log(hours);
  console.log(path);
  window.location.pathname = path;
};

if (
  document.readyState === 'complete' ||
  (document.readyState !== 'loading' && !document.documentElement.doScroll)
) {
  redirect();
} else {
  document.addEventListener('DOMContentLoaded', redirect);
}
//es again
