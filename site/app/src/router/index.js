import Settings from "../views/Settings.vue";
import Pray from "../views/Pray.vue";
import { createRouter, createWebHistory } from "vue-router";
import Today from "@/views/Today";
import Calendar from "@/views/Calendar";
import Day from "@/views/Day";
import PageNotFound from "@/views/PageNotFound";

const routes = [
  {
    path: "/calendar/:year?/:month?/",
    name: "calendar",
    component: Calendar,
    meta: {
      title: "Calendar | The Daily Office",
    },
  },
  {
    path: "/:office/:forward?",
    name: "Today",
    component: Today,
    meta: {
      title: "Pray | The Daily Office",
    },
  },
  {
    path: "/:office/:year/:month:/:day",
    name: "Pray",
    component: Pray,
    meta: {
      title: "Pray | The Daily Office",
    },
  },

  {
    path: "/settings",
    name: "Settings",
    component: Settings,
    meta: {
      title: "Settings | The Daily Office",
    },
  },
  {
    path: "/",
    name: "Home",
    component: Today,
    meta: {
      title: "Today | The Daily Office",
    },
  },
  {
    path: "/about",
    name: "About",
    meta: {
      title: "About | The Daily Office",
    },
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/About.vue"),
  },
  {
    path: "/day/:year/:month/:day/",
    name: "day",
    component: Day,
    meta: {
      title: "Day | The Daily Office",
    },
  },
  { path: "/:pathMatch(.*)*", component: PageNotFound, name: "not_found" },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
