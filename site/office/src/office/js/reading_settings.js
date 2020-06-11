import {getSetting} from "./settings";

const mass = async() => {
    if (!document.getElementById('mass-reading')) {
        return false;
    }
    const lectionary = await getSetting("lectionary")
    if (lectionary !== "mass-readings") {
        return false
    }
    const reading_length = await getSetting("reading_length")
    if (reading_length == "abbreviated" && document.getElementById('abbreviated-mass-reading')) {
        return false;
    }
    return true;
}

const abbreviatedMass = async() => {
    //return false;
    if (!document.getElementById('abbreviated-mass-reading')) {
        return false;
    }
    const lectionary = await getSetting("lectionary")
    if (lectionary !== "mass-readings") {
        return false;
    }
    const reading_length = await getSetting("reading_length")
    if (reading_length !== "abbreviated") {
        return false;
    }
    return true;
}

const main = async () => {
    const years = await getSetting("reading_cycle")
    if (years === "1") {
        return true;
    }

    if (document.getElementById('alternate-reading')) {
        return true;
    }

    return false;
}

const full = async () => {
    const reading_length = await getSetting("reading_length")
    if (reading_length === "full") {
        return true;
    }
    if (await main()) {
        if (document.getElementById('abbreviated-reading')) {
            return false;
        }
        return true;
    }
    if (document.getElementById('alternate-abbreviated-reading')) {
        return false;
    }
    return true;

}

const getHideAndShow = async () => {
    if (await mass()) {
        const hide = ["alternate-reading", "abbreviated-reading", "alternate-abbreviated-reading", "main-reading", "abbreviated-mass-reading"];
        const show = ["mass-reading"];
        return [hide, show]
    }
    else if (await (abbreviatedMass())) {
        const hide = ["alternate-reading", "abbreviated-reading", "alternate-abbreviated-reading", "main-reading", "mass-reading"];
        const show = ["abbreviated-mass-reading" ];
        return [hide, show]
    }
    else if (await main() && await full()) { // main, full
        const hide = ["alternate-reading", "abbreviated-reading", "alternate-abbreviated-reading", "abbreviated-mass-reading", "mass-reading"];
        const show = ["main-reading"];
        return [hide, show]
    }
    else if (await main()) { // main, abbreviated
        const hide = ["alternate-reading", "alternate-abbreviated-reading", "main-reading", "abbreviated-mass-reading", "mass-reading"];
        const show = ["abbreviated-reading"];
        return [hide, show]
    } else if (await full()) { // alternate, full
        const hide = ["main-reading", "abbreviated-reading", "alternate-abbreviated-reading", "abbreviated-mass-reading", "mass-reading"];
        const show = ["alternate-reading"];
        return [hide, show]
    } else { //alternate, abbreviated
        const hide = ["alternate-reading", "abbreviated-reading", "main-reading", "abbreviated-mass-reading", "mass-reading"];
        const show = ["alternate-abbreviated-reading"];
        return [hide, show]
    }

}

const readingSettings = async () => {
    const hideAndShow = await getHideAndShow()
    hideAndShow[0].forEach(item => {
        const el = document.getElementById(item)
        if (el) {
            el.classList.add("off")
        }

    });
    hideAndShow[1].forEach(item => {
        const el = document.getElementById(item)
        if (el) {
            el.classList.remove("off")
        }
    });
}

export {readingSettings};
