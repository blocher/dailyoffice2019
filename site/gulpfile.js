// Gulpfile
const autoprefixer = require('gulp-autoprefixer');
const babel = require('gulp-babel');
const cleanCss = require('gulp-clean-css');
const color = require('gulp-util').colors;
// const path = require('../config/config').paths;
const eslint = require('gulp-eslint');
const flexbugsFixes = require('postcss-flexbugs-fixes');
const gulp = require('gulp');
const gutil = require('gulp-util');
const postcss = require('gulp-postcss');
const rename = require('gulp-rename');
const sass = require('gulp-sass');
const sourcemaps = require('gulp-sourcemaps');
const uglify = require('gulp-uglify');
const rollup     = require('gulp-rollup');
const babelify = require("babelify");
const browserify = require("browserify");
const source = require('vinyl-source-stream');

const path = {
	src: {
		css: "office/src/office/css/*",
		js: "office/src/office/js/*",
		js_entry: "office/src/office/js/default.js"
	},
	dist: {
		css: "office/static/office/css",
		js: "office/static/office/js",
		js_exit: "office/static/office/js/default.min.js",
	}
}

function logError(err) {
	gutil.log(color.red('Error') + ' in plugin \'' + color.cyan(err.plugin) + '\'\n' + err.message.toString());
	this.emit('end');
}


function styles() {
	return gulp.src( path.src.css )
		.pipe( sourcemaps.init() )
		.pipe( sass().on('error', sass.logError ) )
		.pipe( postcss( [
		  flexbugsFixes()
		] ) )
		.pipe( autoprefixer( {
			cascade: false
		} ) )
		.pipe( cleanCss( { compatibility: 'ie9' } ) )
		.pipe( rename( { suffix: '.min' } ) )
		.pipe( sourcemaps.write( './' ) )
		.pipe( gulp.dest( path.dist.css ) );
}

function scripts() {

    // return gulp.src( path.src.js )
	return browserify({entries: path.src.js_entry, extensions: ['.js','es6','jsx'], debug: "true"})
		.transform(babelify, {presets: ["@babel/preset-env", "@babel/preset-react"]})
		.bundle()
		.pipe(source(path.src.js_entry))
    	// .pipe( sourcemaps.init() )
    	// .pipe( eslint({
    	// 	configFile: './eslint.config.js'
    	// }))
	    // .pipe( eslint.format() )
        //.pipe( uglify() )
        // .pipe( rename({ suffix: '.min' }) )
        // .pipe( sourcemaps.write('./') )
        .pipe( gulp.dest( path.dist.js ) );
}

function watch() {
	// Main Styles
	gulp.watch([
        path.src.css
    ], styles );

    // JS Files
    gulp.watch( path.src.js, scripts );
}

gulp.task( 'scripts', scripts );
gulp.task( 'styles', styles );
gulp.task( 'default', watch );
