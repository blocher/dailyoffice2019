import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Settings from "../views/Settings.vue";

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
    meta: {
      title: "Today | The Daily Office",
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
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
