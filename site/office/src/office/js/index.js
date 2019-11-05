import "core-js/stable";
import "regenerator-runtime/runtime";
import { setupRedirect } from "./redirect";
import { settings } from "./settings";
import "../css/index.scss";

setupRedirect();
settings();
