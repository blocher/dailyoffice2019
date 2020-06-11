import {getSetting} from "./settings";

class ReadingEnabler {

    constructor(prefix) {
        this.prefix = prefix;
      }

    async mass() {
        if (!document.getElementById(this.prefix + 'mass-reading')) {
            return false;
        }
        const lectionary = await getSetting("lectionary")
        if (lectionary !== "mass-readings") {
            return false
        }
        const reading_length = await getSetting("reading_length")
        if (reading_length == "abbreviated" && document.getElementById(this.prefix + 'abbreviated-mass-reading')) {
            return false;
        }
        return true;
    }

    async abbreviatedMass() {
        if (!document.getElementById(this.prefix + 'abbreviated-mass-reading')) {
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

    async main() {
        const years = await getSetting("reading_cycle")
        if (years === "1") {
            return true;
        }

        if (document.getElementById(this.prefix + 'alternate-reading')) {
            return true;
        }

        return false;
    }

    async full() {
        const reading_length = await getSetting("reading_length")
        if (reading_length === "full") {
            return true;
        }
        if (await this.main()) {
            if (document.getElementById(this.prefix + 'abbreviated-reading')) {
                return false;
            }
            return true;
        }
        if (document.getElementById(this.prefix + 'alternate-abbreviated-reading')) {
            return false;
        }
        return true;

    }

    async getHideAndShow() {
        if (await this.mass()) {
            const hide = ["alternate-reading", "abbreviated-reading", "alternate-abbreviated-reading", "main-reading", "abbreviated-mass-reading"];
            const show = ["mass-reading"];
            return [hide, show]
        } else if (await (this.abbreviatedMass())) {
            const hide = ["alternate-reading", "abbreviated-reading", "alternate-abbreviated-reading", "main-reading", "mass-reading"];
            const show = ["abbreviated-mass-reading"];
            return [hide, show]
        } else if (await this.main() && await this.full()) { // main, full
            const hide = ["alternate-reading", "abbreviated-reading", "alternate-abbreviated-reading", "abbreviated-mass-reading", "mass-reading"];
            const show = ["main-reading"];
            return [hide, show]
        } else if (await this.main()) { // main, abbreviated
            const hide = ["alternate-reading", "alternate-abbreviated-reading", "main-reading", "abbreviated-mass-reading", "mass-reading"];
            const show = ["abbreviated-reading"];
            return [hide, show]
        } else if (await this.full()) { // alternate, full
            const hide = ["main-reading", "abbreviated-reading", "alternate-abbreviated-reading", "abbreviated-mass-reading", "mass-reading"];
            const show = ["alternate-reading"];
            return [hide, show]
        } else { //alternate, abbreviated
            const hide = ["alternate-reading", "abbreviated-reading", "main-reading", "abbreviated-mass-reading", "mass-reading"];
            const show = ["alternate-abbreviated-reading"];
            return [hide, show]
        }

    }

    async go() {
        const hideAndShow = await this.getHideAndShow()
        hideAndShow[0].forEach(item => {
            const el = document.getElementById(this.prefix + item)
            if (el) {
                el.classList.add("off")
            }

        });
        hideAndShow[1].forEach(item => {
            const el = document.getElementById(this.prefix + item)
            if (el) {
                el.classList.remove("off")
            }
        });
    }

}


const readingSettings = async () => {
    const prefixes = ["first-", "second-", "third-"]
    prefixes.forEach(prefix => {
        let enabler = new ReadingEnabler(prefix)
        enabler.go()
    })
}

export {readingSettings};
