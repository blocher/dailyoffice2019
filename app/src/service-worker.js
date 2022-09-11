// workbox functions from the workbox CDN (version 4.3.1)
// Vue 3 PWA automatically adds the CDN
import {registerRoute, Route} from 'workbox-routing';
import {NetworkFirst} from 'workbox-strategies';

const imageRoute = new Route(({request, sameOrigin}) => {
    return sameOrigin
}, new NetworkFirst());

// Register the new route
registerRoute(imageRoute);

const cacheName = 'daily_office';

self.addEventListener("message", (event) => {
    if (event.data && event.data.type === "SKIP_WAITING") {
        self.skipWaiting();
    }
});

self.addEventListener('fetch', function (event) {
    // Open the cache
    event.respondWith(caches.open(cacheName).then((cache) => {
        // Go to the network first
        console.log('going to network first');
        return fetch(event.request.url).then((fetchedResponse) => {
            cache.put(event.request, fetchedResponse.clone());
            return fetchedResponse;
        }).catch(() => {
            console.log('fallilng back to cache');
            // If the network is unavailable, get
            return cache.match(event.request.url);
        });
    }));
})

// const dates_to_cache = function () {
//     const dates = [];
//     const today = new Date();
//     const year = today.getFullYear();
//     const month = today.getMonth();
//     const date = today.getDate();
//     for (let i = -2; i < 31; i++) {
//         const day = new Date(year, month, date + i);
//         dates.push(day);
//         console.log(day.toISOString().split("T")[0]);
//     }
// };
// /**
//  * The workboxSW.precacheAndRoute() method efficiently caches and responds to
//  * requests for URLs in the manifest.
//  */
// self.__precacheManifest = [].concat(self.__precacheManifest || []);
// const urls = [
//     "https://127.0.0.1:8000/api/v1/available_settings/",
//     "https://127.0.0.1:8000/api/v1/office/morning_prayer/",
//     "https://127.0.0.1:8000/api/v1/office/midday_prayer/2022-8-28?language_style=contemporary&bible_translation=esv&psalter=60&reading_cycle=1&reading_length=full&reading_audio=off&canticle_rotation=default&lectionary=daily-office-readings&confession=long-on-fast&absolution=lay&morning_prayer_invitatory=invitatory_traditional&reading_headings=off&language_style_for_our_father=traditional&national_holidays=all&suffrages=rotating&collects=rotating&pandemic_prayers=pandemic_yes&mp_great_litany=mp_litany_off&ep_great_litany=ep_litany_off&general_thanksgiving=on&chrysostom=on&grace=rotating&o_antiphons=literal&family_readings=brief&family_reading_audio=off&family_collect=time_of_day&family-opening-sentence=family-opening-sentence-fixed&family-creed=family-creed-no",
//     "https://127.0.0.1:8000/api/v1/office/evening_prayer/2022-8-28?language_style=contemporary&bible_translation=esv&psalter=60&reading_cycle=1&reading_length=full&reading_audio=off&canticle_rotation=default&lectionary=daily-office-readings&confession=long-on-fast&absolution=lay&morning_prayer_invitatory=invitatory_traditional&reading_headings=off&language_style_for_our_father=traditional&national_holidays=all&suffrages=rotating&collects=rotating&pandemic_prayers=pandemic_yes&mp_great_litany=mp_litany_off&ep_great_litany=ep_litany_off&general_thanksgiving=on&chrysostom=on&grace=rotating&o_antiphons=literal&family_readings=brief&family_reading_audio=off&family_collect=time_of_day&family-opening-sentence=family-opening-sentence-fixed&family-creed=family-creed-no",
//     "https://127.0.0.1:8000/api/v1/office/compline/2022-8-28?language_style=contemporary&bible_translation=esv&psalter=60&reading_cycle=1&reading_length=full&reading_audio=off&canticle_rotation=default&lectionary=daily-office-readings&confession=long-on-fast&absolution=lay&morning_prayer_invitatory=invitatory_traditional&reading_headings=off&language_style_for_our_father=traditional&national_holidays=all&suffrages=rotating&collects=rotating&pandemic_prayers=pandemic_yes&mp_great_litany=mp_litany_off&ep_great_litany=ep_litany_off&general_thanksgiving=on&chrysostom=on&grace=rotating&o_antiphons=literal&family_readings=brief&family_reading_audio=off&family_collect=time_of_day&family-opening-sentence=family-opening-sentence-fixed&family-creed=family-creed-no",
//     "https://127.0.0.1:8000/api/v1/readings/2022-8-28?translation=esv&psalms=contemporary",
//     "https://127.0.0.1:8000/api/v1/readings/2022-8-28?translation=esv&psalms=contemporary",
//     "https://127.0.0.1:8000/api/v1/readings/2022-8-28?translation=esv&psalms=contemporary",
//     "https://127.0.0.1:8000/api/v1/readings/2022-8-28?translation=esv&psalms=contemporary",
//     "https://127.0.0.1:8000/api/v1/readings/2022-8-28?translation=esv&psalms=contemporary",
//
// ]
// precacheAndRoute(self.__precacheManifest, {});

