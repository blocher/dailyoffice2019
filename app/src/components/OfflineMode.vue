<template>
  <p>Offline mode is here</p>
</template>

<script>
// @ is an alias to /src

export default {
  name: "Offline Mode",
  components: {},
  props: [],
  computed: {},
  async created() {
    this.cache = await caches.open("offline-cache");
    const urls = this.getPreLoadAPIEndpoints();
    urls.forEach(url => {
      this.cache.add(url);
      console.log("url added to cache:" + url)
      // if (!this.isInCache(url)) {
      //   this.cache.add(url);
      //   console.log("url added to cache:" + url)
      // } else {
      //   console.log("url already in cache:" + url)
      // }
    });
    console.log("Offline Mode created");
  },
  methods: {
    async isInCache(url) {
      const cachedResponse = await this.cache.match(url);

      if (cachedResponse?.ok) {
        return true;
      }

      return false;
    },
    getPreLoadAPIEndpoints() {
      const settings = this.$store.state.settings;
      const queryString = Object.keys(settings)
          .map((key) => key + "=" + settings[key])
          .join("&");

      const base_routes = [
        "api/v1/office/morning_prayer/",
        "api/v1/office/midday_prayer/",
        "api/v1/office/evening_prayer/",
        "api/v1/office/compline/",
        "api/v1/family/morning_prayer/",
        "api/v1/family/midday_prayer/",
        "api/v1/family/early_evening_prayer/",
        "api/v1/family/close_of_day_prayer/",
      ]

      const dates_to_cache = function () {
        const dates = [];
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();
        const date = today.getDate();
        // for (let i = -2; i < 31; i++) {
        for (let i = -1; i < 3; i++) {
          const day = new Date(year, month, date + i);
          dates.push(day.toISOString().split("T")[0]);
        }
        return dates;
      };

      const office_routes = [];
      for (let day of dates_to_cache()) {
        for (let route of base_routes) {
          office_routes.push(`${route}${day}?${queryString}`);
        }
      }

      const calendar_routes = function () {
        const dates = [];
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();
        const date = today.getDate();
        for (let i = -13; i < 13; i++) {
          const day = new Date(year, month + i, date)
          const parts = day.toISOString().split("-")
          const date_str = parts[0] + "-" + parts[1]
          dates.push(`/api/v1/calendar/${date_str}`);
        }
        return dates;
      }

      const psalm_routes = function () {
        const routes = ['/api/v1/psalms/', '/api/v1/psalms/topics/']
        for (let i = 1; i < 151; i++) {
          routes.push(`/api/v1/psalms/${i}`);
        }
        return routes;
      }

      let urls = [
        '/api/v1/available_settings/',
        '/api/v1/about',
        '/api/v1/collect_categories/',
        '/collects',
        '/api/v1/collects',
      ].concat(office_routes).concat(calendar_routes()).concat(psalm_routes());
      urls = urls.map(url => `${process.env.VUE_APP_API_URL}${url}`);
      urls = urls.map(url => url.replace("//api", "/api").replace("//api", "/api"))
      return urls;
    },
  }
};
</script>

<style>
.extra-space-before {
  margin-top: 0.7em;
}
</style>
