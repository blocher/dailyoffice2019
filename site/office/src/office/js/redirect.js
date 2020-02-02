import {settings} from "./settings";
import {setupCalendar} from "./calendar";

const today = function () {
    const date = new Date();
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const date_string = `${year}-${month}-${day}`;
    return date_string
};

const current_family_office = function(hours) {

    if (hours < 11) {
        return ('family/morning_prayer');
    }

    if (hours < 16) {
        return ('family/midday_prayer');
    }

    if (hours < 20) {
        return ('family/early_evening_prayer');
    }

    return ('family/close_of_day_prayer');

}

const current_office = function (redirect_type) {

    const date = new Date();
    const hours = date.getHours();

    if (redirect_type == 'family') {
        return current_family_office(hours);
    }

    if (hours < 11) {
        return ('morning_prayer');
    }

    if (hours < 16) {
        return ('midday_prayer');
    }

    return ('evening_prayer');

};

const current_office_label = function () {
    let redirect_type = false;
    if (document.getElementById("redirect-to-today")) {
        redirect_type = "daily"
    } else if (document.getElementById("redirect-to-today-family")){
        redirect_type = "family"
    }
    const office = current_office(redirect_type)
    if (office == 'morning_prayer') {
        return 'Morning Prayer';
    }
    if (office == 'midday_prayer') {
        return 'Midday Prayer';
    }
    if (office == 'evening_prayer') {
        return 'Evening Prayer';
    }
    if (office == 'compline') {
        return 'Compline';
    }
    if (office == 'family/morning_prayer') {
        return 'Family Prayer in the Morning';
    }
    if (office == 'family/midday_prayer') {
        return 'Family Prayer at Midday';
    }
    if (office == 'family/early_evening_prayer') {
        return 'Family Prayer in the Early Evening';
    }
    if (office == 'family/close_of_day_prayer') {
        return 'Family Prayer at the Close of Day';
    }
    // const office = hours >= 12 ? 'Evening Prayer' : 'Morning Prayer';
    // return office
};

const getAdvent = function (year) {

    let date = new Date(Date.parse(year + '-12-25'));
    let sundays = 0;
    while (sundays < 4) {
        date.setDate(date.getDate() - 1);
        if (date.getDay() === 0) {
            sundays++;
        }
    }
    return date;
};

const getChurchYearStartYear = function (date) {
    const advent = getAdvent(date.getFullYear());
    if (date > advent) {
        return parseInt(date.getFullYear())
    }
    return parseInt(date.getFullYear()) - 1
};

const redirect = function () {

    let redirect_type = false;
    if (document.getElementById("redirect-to-today")) {
        redirect_type = "daily"
    } else if (document.getElementById("redirect-to-today-family")){
        redirect_type = "family"
    }
    if (redirect_type) {
        const date_string = today();
        const office = current_office(redirect_type);
        const path = `\\${office}\\${date_string}`;
        const xhr = new XMLHttpRequest();
        xhr.open('GET', path);
        xhr.responseType = "document";
        xhr.onload = function () {
            if (xhr.status === 200) {

                const elem = document.querySelector("#body");
                const newBody = xhr.response.querySelector("#body");
                elem.innerHTML = newBody.innerHTML;
                document.querySelector("#messages").innerHTML = "<a href='" + path + "'>Permanent link for " + current_office_label() + " for " + new Date().toLocaleDateString() + "</a></a></p>";
                settings();
                setupCalendar();
                document.getElementById("now-button").classList.add('on')
            } else {
                alert('Request failed.  Returned status of ' + xhr.status);
            }
        };
        xhr.send();
    }
};

const setupRedirect = () => {
    if (
        document.readyState === "complete" ||
        (document.readyState !== "loading" && !document.documentElement.doScroll)
    ) {
        redirect();
    } else {
        document.addEventListener("DOMContentLoaded", redirect);
    }
};
export {setupRedirect, today, current_office, getChurchYearStartYear};
