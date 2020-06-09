import {getSetting} from "./settings";

const main = async () => {
    const years = await getSetting("reading_cycle")
    if (years == 1) {
        return true;
    }

    if (document.getElementById('alternate-reading')) {
        return true;
    }

    return false;

}

const full = async () => {
    const reading_length = await getSetting("reading_length")
    if (reading_length == "full") {
        return true;
    }
    if (!await main()) {
        if (document.getElementById('abbreviated-reading')) {
            return true;
        }
        return false;
    }
    if (document.getElementById('alternate-abbreviated-reading')) {
            return true;
        }
        return false;

}

const getHideAndShow = async () => {
    if (await main() && await full()) { // main, full
        const hide = ["alternate-reading", "abbreviated-reading", "alternate-abbreviated-reading"];
        const show = ["main-reading"];
        return [hide, show]
    }
    else if (await main()) { // main, abbreviated
        const hide = ["alternate-reading", "alternate-abbreviated-reading", "main-reading"];
        const show = ["abbreviated-reading"];
        return [hide, show]
    } else if (await full()) { // alternate, full
        const hide = ["main-reading", "abbreviated-reading", "alternate-abbreviated-reading"];
        const show = ["alternate-reading"];
        return [hide, show]
    } else { //alternate, abbreviated
        const hide = ["alternate-reading", "abbreviated-reading", "main-reading"];
        const show = ["alternate-abbreviated-reading"];
        return [hide, show]
    }

}

const readingSettings = async () => {
    const hideAndShow = await getHideAndShow()
    console.log(hideAndShow)
    hideAndShow[0].forEach(item => {
            Array.from(document.getElementsByClassName(item)).forEach(
                (element, element_index) => {
                    element.classList.add("off");
                }
            )
        }
    );
    hideAndShow[1].forEach(item => {
            Array.from(document.getElementsByClassName(item)).forEach(
                (element, element_index) => {
                    element.classList.remove("off");
                }
            )
        }
    );
}

export {readingSettings};
