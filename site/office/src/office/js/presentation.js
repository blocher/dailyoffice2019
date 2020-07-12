
const scrollPageToPosition = async function scrollToPosition(position) {
  var container = window
  position = Math.round(position);
  if (container.scrollX === position) {
    return;
  }

  let resolveFn;
  let scrollListener;
  let timeoutId;

  const promise = new Promise(resolve => {
    resolveFn = resolve;
  });

  const finished = () => {
    container.removeEventListener('scroll', scrollListener);
    resolveFn();
  };
  scrollListener = () => {
    clearTimeout(timeoutId);

    // scroll is finished when either the position has been reached, or 100ms have elapsed since the last scroll event
    if (container.scrollX === position) {
      finished();
    } else {
      timeoutId = setTimeout(finished, 10000);
    }
  };

  window.addEventListener('scroll', scrollListener);

  window.scroll({
    left: position,
    behavior: 'smooth',
  });

  return promise;
}

const showHidePaginationLinks = () => {
    const allPages  = document.getElementById('allPages').innerText
    const currentPage = document.getElementById('pageNumber').innerText
    console.log(allPages, currentPage)
    if (currentPage == "1") {
        document.getElementsByClassName('scroll-back').forEach(elem => {
            elem.classList.add("off")
        });
    } else {
        document.getElementsByClassName('scroll-back').forEach(elem => {

            elem.classList.remove("off")
        });
    }

    if (currentPage == allPages) {
        document.getElementsByClassName('scroll-forward').forEach(elem => {
            elem.classList.add("off")
        });
    } else {
        document.getElementsByClassName('scroll-forward').forEach(elem => {
            elem.classList.remove("off")
        });
    }
}

const convertRemToPixels = (rem) => {
    return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}
const scrollForward = (event) => {
        disablePaginationEventListeners();
        scrollPageToPosition(window.pageXOffset + window.innerWidth).then(() => {
            incrementPageNumber();
            showHidePaginationLinks();
            enablePaginationEventListeners();
        });
        event.stopPropagation();
        event.preventDefault();
        return false;
}

const scrollBackward = (event) => {
    disablePaginationEventListeners();
    scrollPageToPosition(window.pageXOffset - window.innerWidth).then(() => {
            deincrementPageNumber();
            showHidePaginationLinks();
            enablePaginationEventListeners();
    });
    event.stopPropagation();
    event.preventDefault();
    return false;
}

const disableClickEvent = (event) => {
    event.stopPropagation();
    event.preventDefault();
    return false;
}

const disablePaginationEventListeners = () =>  {
    document.getElementsByClassName('scroll-forward').forEach(elem => {
        elem.addEventListener('click', disableClickEvent, true);
        elem.removeEventListener('click', scrollForward, true);
    });
    document.getElementsByClassName('scroll-back').forEach(elem => {
        elem.addEventListener('click', disableClickEvent, true);
        elem.removeEventListener('click', scrollBackward, true);
    });
}

const enablePaginationEventListeners = () =>  {
    document.getElementsByClassName('scroll-forward').forEach(elem => {
        elem.removeEventListener('click', disableClickEvent, true);
        elem.addEventListener('click', scrollForward, true);
    });
    document.getElementsByClassName('scroll-back').forEach(elem => {
        elem.removeEventListener('click', disableClickEvent, true);
        elem.addEventListener('click', scrollBackward, true);
    });
}

const incrementPageNumber = () => {;
    let pageNumber = parseInt(document.getElementById('pageNumber').innerText)
    const allPages = parseInt(document.getElementById('allPages').innerText)
    pageNumber = pageNumber + 1
    document.getElementById('pageNumber').innerText = pageNumber.toString()
}

const deincrementPageNumber = () => {;
    let pageNumber = parseInt(document.getElementById('pageNumber').innerText)
    pageNumber = pageNumber - 1
    document.getElementById('pageNumber').innerText = pageNumber.toString()
}

const initialize = () => {
    document.getElementsByTagName('body')[0].classList.add("no-scroll")
    document.getElementsByClassName("no-print").forEach((elem) => {
        elem.classList.add('off');
    });
    document.getElementsByClassName("off").forEach((elem) => {
       elem.parentNode.removeChild(elem);
    });
    // document.getElementsByClassName('web').forEach(elem => {
    //     elem.addEventListener('click', scrollForward, false);
    // });
    enablePaginationEventListeners();

    const desiredWidth = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const desiredHeight = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0) - 40 - convertRemToPixels(2);
    const mainDiv = document.getElementById('web');
    const totalHeight = mainDiv.offsetHeight;
    const pageCount = Math.floor(totalHeight/desiredHeight) + 1;
    //alert("A" + pageCount)
    const width = desiredWidth * pageCount;
    mainDiv.style.margin = "20px 0";
    mainDiv.style.padding = "10px 0px"; //(optional) prevents clipped letters around the edges
    mainDiv.style.width = width + 'px';
    mainDiv.style.height = desiredHeight + 'px';
    mainDiv.style.columnWidth = window.innerWidth + 'px';
    mainDiv.style.columnCount = pageCount;
    mainDiv.style.columnFill = "auto";
    mainDiv.style.columnGap = "0px";
    document.getElementById('allPages').innerText = pageCount.toString()
    showHidePaginationLinks()
}

const reinitialize = () => {

}
const setupPresentation = () => {
    window.onbeforeunload = function () {
      window.scrollTo(0, 0);
    }
    document.getElementById("presentiation-mode-link").addEventListener('click', (event) => {
        document.getElementById("presentation-controls").classList.remove("off");
        initialize();
        event.preventDefault();
    })
    document.getElementById("exit-presentation-link").addEventListener('click', (event) => {
        location.reload();
        event.preventDefault();
    })
    //window.addEventListener('resize', reinitialize)
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
