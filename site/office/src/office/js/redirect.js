import {settings} from "./settings";

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
    const xhr = new XMLHttpRequest();
    xhr.open('GET', path);
    xhr.responseType = "document"
    xhr.onload = function() {
        if (xhr.status === 200) {

            const elem = document.querySelector("#body");
            const newBody = xhr.response.querySelector("#body");
            elem.innerHTML = newBody.innerHTML;
            document.querySelector("#messages").innerHTML = "Showing office for right now <a href='/'><i class=\"far fa-sync-alt\"></i></a><br><a href='" + path + "'>Permanent link for " + date.toDateString() + "</a></a></p>"
            document.querySelector("#now-button").classList.add('off');
            settings();
        }
        else {
            alert('Request failed.  Returned status of ' + xhr.status);
        }
    };
    xhr.send();
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
