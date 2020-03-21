const scrollStop =  (callback) => {

	// Make sure a valid callback was provided
	if (!callback || typeof callback !== 'function') return;

	// Setup scrolling variable
	let isScrolling;

	// Listen for scroll events
	window.addEventListener('scroll', function (event) {

		// Clear our timeout throughout the scroll
		window.clearTimeout(isScrolling);

		// Set a timeout to run after scrolling ends
		isScrolling = setTimeout(function() {

			// Run the callback
			callback();

		}, 5);

	}, false);

};

const  scrollTop = () => {
	return window.pageYOffset || (document.documentElement || document.body.parentNode || document.body).scrollTop
}

const handleScrolling = () => {

		scrollStop(function () {
			if (document.getElementById("main-footer")) {
				if (scrollTop() > 10) {
					document.getElementById("main-footer").classList.remove("footer-fixed");
				} else {
					document.getElementById("main-footer").classList.add("footer-fixed");
				}
			}
		});

};
export {handleScrolling};
