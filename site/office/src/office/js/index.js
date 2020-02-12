import "core-js/stable";
import "regenerator-runtime/runtime";
import {setupRedirect} from "./redirect";
import {settings} from "./settings";
import {setupCalendar} from "./calendar";
import "../css/index.scss";

setupRedirect();
settings();
setupCalendar();

