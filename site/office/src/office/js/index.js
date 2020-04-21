import "core-js/stable";
import "regenerator-runtime/runtime";
import {setupRedirect} from "./redirect";
import {settings} from "./settings";
import {voice} from "./voice";
import {setupCalendar} from "./calendar";
import "../css/index.scss";
import {handleScrolling} from "./scrolling";
import {setupAnalytics} from "./analytics";

setupAnalytics();
setupRedirect();
settings();
voice();
setupCalendar();
handleScrolling();
