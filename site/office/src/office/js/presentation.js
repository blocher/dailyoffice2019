const scrollForward = (event) => {
    window.scroll({left: 0, top: window.pageYOffset + window.innerHeight - 80, behavior: 'smooth'} )
    event.stopPropagation();
    event.preventDefault();
    return false;
}

const scrollBackward = (event) => {
    window.scroll({left: 0, top: window.pageYOffset - window.innerHeight + 80, behavior: 'smooth'} )
    event.stopPropagation();
    event.preventDefault();
    return false;
}
const setupPresentation = () => {
    document.getElementsByClassName("no-print").forEach((elem) => {
        elem.classList.add('off');
    });
    window.scrollTo(0, 0);
    document.getElementsByClassName('inner-body').forEach(elem => {
        elem.addEventListener('click', scrollForward, false);
    });
    document.getElementsByClassName('scroll-forward').forEach(elem => {
        elem.addEventListener('click', scrollForward, false);
    });
    document.getElementsByClassName('scroll-back').forEach(elem => {
        elem.addEventListener('click', scrollBackward, false);
    });

}

const Presentation = () => {
    if (
        document.readyState === "complete" ||
        (document.readyState !== "loading" && !document.documentElement.doScroll)
    ) {
        setupPresentation();
    } else {
        document.addEventListener("DOMContentLoaded", setupPresentation);
    }
};

export {Presentation};
