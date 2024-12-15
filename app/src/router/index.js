import Settings from "../views/Settings.vue";
import Pray from "../views/Pray.vue";
import { createRouter, createWebHistory } from "vue-router";
import Today from "@/views/Today.vue";
import Calendar from "@/views/Calendar.vue";
import Day from "@/views/Day.vue";
import PageNotFound from "@/views/PageNotFound.vue";
import Readings from "@/views/Readings.vue";
import Scripture from "@/views/Scripture.vue";
import Litany from "@/views/Litany.vue";

const routes = [
  {
    path: "/readings/",
    name: "readings",
    component: Readings,
    children: [
      {
        path: "/readings/:service/",
        component: Readings,
        name: "readingsByService",
      },
      {
        path: "/readings/:service/:year/:month/:day",
        component: Readings,
        name: "readingsByServiceAndDate",
      },
      {
        path: "/readings/:service/:position/:year/:month/:day",
        component: Readings,
        name: "readingsByServicePositionAndDate",
      },
      {
        path: "/readings/:year/:month/:day",
        component: Readings,
        name: "readingsByDate",
      },
    ],
    meta: {
      title: "Readings | The Daily Office",
    },
  },
  {
    path: "/litany/",
    name: "litany",
    component: Litany,
    meta: {
      title: "The Great Litany | The Daily Office",
    },
  },
  {
    path: "/calendar",
    name: "calendar",
    component: Calendar,
    meta: {
      title: "Calendar | The Daily Office",
    },
  },
  {
    path: "/calendar/:year?/:month?/",
    name: "calendar",
    component: Calendar,
    meta: {
      title: "Calendar | The Daily Office",
    },
  },
  {
    path: "/:serviceType/:office/:forward?/",
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
    path: "/:serviceType/:office/:year/:month:/:day",
    name: "Family Prayer",
    component: Pray,
    meta: {
      title: "Pray | Family Prayer",
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
    path: "/collects",
    name: "Collects",
    meta: {
      title: "Collects | The Daily Office",
    },
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/CollectsNew.vue"),
  },
  {
    path: "/psalms",
    name: "Psalms",
    meta: {
      title: "Psalms | The Daily Office",
    },
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/Psalms.vue"),
  },
  {
    path: "/psalm/:number/",
    name: "Psalm",
    meta: {
      title: "Psalms | The Daily Office",
    },
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/Psalm.vue"),
  },
  {
    path: "/day/:year/:month/:day/",
    name: "day",
    component: Day,
    meta: {
      title: "Day | The Daily Office",
    },
  },
  {
    path: "/scripture/:passage",
    name: "scripture",
    component: Scripture,
    meta: {
      title: "Scripture | The Daily Office",
    },
  },
  { path: "/:pathMatch(.*)", component: PageNotFound, name: "not_found" },
];

const routesToNotScrollToTop = [
  "readingsByServiceAndDate",
  "readingsByServicePositionAndDate",
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (routesToNotScrollToTop.includes(to.name)) {
      return false;
    } else {
      // always scroll to top
      return { top: 0 };
    }
  },
});

export default router;
