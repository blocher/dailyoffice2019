import {today, getChurchYearStartYear} from "./redirect";

const calendar = function() {

    const current_church_year = getChurchYearStartYear(new Date())
    document.getElementById("calendar-button" ).href =  "/church_year/" + current_church_year + "-" + (parseInt(current_church_year) + 1) + "#day-" + today()

    if (!document.getElementById("cal-menu-seasons-link")) {
        return;
    }

    document.getElementById("cal-menu-today-link" ).href =  "/church_year/" + current_church_year + "-" + (parseInt(current_church_year) + 1) + "#day-" + today()

    document.getElementById("cal-menu-seasons-link").addEventListener("click", event => {
          document.getElementById("cal-menu-seasons").classList.remove('off');
          document.getElementById("cal-menu-dates").classList.add('off');
          document.getElementById("calendar").classList.add('off');
        });
    document.getElementById("cal-menu-dates-link").addEventListener("click", event => {
          document.getElementById("cal-menu-seasons").classList.add('off');
          document.getElementById("cal-menu-dates").classList.remove('off');
          document.getElementById("calendar").classList.add('off');
        });

    Array.from(document.getElementsByClassName("calendar-menu-button")).forEach(
          (element, element_index) => {
            element.addEventListener("click", event => {
                document.getElementById("cal-menu-seasons").classList.add('off');
                document.getElementById("cal-menu-dates").classList.add('off');
                document.getElementById("calendar").classList.remove('off');
              })
          })

    Array.from(document.getElementsByClassName("close-cal-menu")).forEach(
          (element, element_index) => {
            element.addEventListener("click", event => {
                document.getElementById("cal-menu-seasons").classList.add('off');
                document.getElementById("cal-menu-dates").classList.add('off');
                document.getElementById("calendar").classList.remove('off');
              })
          })

    document.getElementById("cal-menu-today-link").addEventListener("click", event => {
          document.getElementById("cal-menu-seasons").classList.add('off');
          document.getElementById("cal-menu-dates").classList.add('off');
          document.getElementById("calendar").classList.remove('off');
        });


};

const setupCalendar = () =>
{
  if (
      document.readyState === "complete" ||
      (document.readyState !== "loading" && !document.documentElement.doScroll)
  ) {
    calendar();
  } else {
    document.addEventListener("DOMContentLoaded", calendar);
  }
}
export { setupCalendar };
