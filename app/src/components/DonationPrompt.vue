<template>
  <!-- Short Variant: Compact pill for headers/navbars -->
  <div v-if="variant === 'short'" class="flex items-center justify-center my-2">
    <button
      @click="openLink"
      class="group relative inline-flex items-center gap-2 px-4 py-2 bg-white border border-indigo-100 rounded-full shadow-sm hover:shadow-md hover:border-indigo-200 transition-all duration-300 transform hover:-translate-y-0.5"
    >
      <div
        class="flex items-center justify-center w-6 h-6 rounded-full bg-red-50 text-red-500 group-hover:scale-110 transition-transform duration-300"
      >
        <font-awesome-icon :icon="['fad', 'fa-heart']" />
      </div>
      <span
        class="text-xs font-semibold text-gray-700 group-hover:text-indigo-600"
        >Support the Daily Office</span
      >
    </button>
  </div>

  <!-- Long Variant: Full feature card for detailed pages -->
  <div v-else class="max-w-4xl mx-auto my-12 px-4 font-sans">
    <div
      class="bg-white rounded-2xl shadow-xl border border-indigo-50 overflow-hidden"
    >
      <!-- Hero Header -->
      <div
        class="p-8 sm:p-10 text-center relative overflow-hidden border-b border-gray-100"
      >
        <div
          class="absolute top-0 left-0 w-full h-full opacity-5 pointer-events-none"
        >
          <font-awesome-icon
            :icon="['fad', 'fa-books']"
            class="text-9xl absolute -top-10 -left-10 transform rotate-12 text-indigo-900"
          />
          <font-awesome-icon
            :icon="['fad', 'fa-book-bible']"
            class="text-9xl absolute -bottom-10 -right-10 transform -rotate-12 text-indigo-900"
          />
        </div>

        <div class="relative z-10 max-w-2xl mx-auto">
          <div
            class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-50 mb-6 shadow-sm ring-4 ring-white"
          >
            <font-awesome-icon
              :icon="['fad', 'fa-gift']"
              class="text-3xl text-indigo-600"
            />
          </div>
          <h3 class="text-3xl font-extrabold tracking-tight mb-4 text-gray-900">
            Support the Daily Office
          </h3>
          <p class="text-gray-600 text-lg sm:text-x leading-relaxed">
            Your generosity helps us sustain this ministry, generate audio
            daily, and keep these resources free for everyone.
          </p>
        </div>
      </div>

      <div class="p-8 sm:p-10">
        <div class="grid md:grid-cols-2 gap-10 items-center">
          <!-- Left Column: Impact List -->
          <div class="space-y-6">
            <h4
              class="text-lg font-bold text-gray-900 border-b border-gray-100 pb-2"
            >
              Your support makes this possible:
            </h4>
            <ul class="space-y-4">
              <li class="flex items-start gap-4">
                <div
                  class="shrink-0 w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600"
                >
                  <font-awesome-icon
                    :icon="['fad', 'fa-server']"
                    class="text-lg"
                  />
                </div>
                <div>
                  <span class="block font-semibold text-gray-900"
                    >Infrastructure & Licensing</span
                  >
                  <span class="text-sm text-gray-500"
                    >Servers, app store fees, and Bible text royalties.</span
                  >
                </div>
              </li>
              <li class="flex items-start gap-4">
                <div
                  class="shrink-0 w-10 h-10 rounded-lg bg-pink-50 flex items-center justify-center text-pink-600"
                >
                  <font-awesome-icon
                    :icon="['fad', 'fa-microphone']"
                    class="text-lg"
                  />
                </div>
                <div>
                  <span class="block font-semibold text-gray-900"
                    >Audio Production</span
                  >
                  <span class="text-sm text-gray-500"
                    >Daily audio generation, hosting, and podcast
                    distribution.</span
                  >
                </div>
              </li>
              <li class="flex items-start gap-4">
                <div
                  class="shrink-0 w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600"
                >
                  <font-awesome-icon
                    :icon="['fad', 'fa-book-bible']"
                    class="text-lg"
                  />
                </div>
                <div>
                  <span class="block font-semibold text-gray-900"
                    >Content Creation</span
                  >
                  <span class="text-sm text-gray-500"
                    >Saint hagiographies and the upcoming Podcast and Spanish
                    editions</span
                  >
                </div>
              </li>
            </ul>
          </div>

          <!-- Right Column: CTA & Info -->
          <div
            class="bg-gray-50 rounded-xl p-8 text-center border border-gray-100 shadow-inner"
          >
            <p class="text-gray-600 mb-6 italic">
              "This site will always be 100% free. There is no paywall, no
              obligation, and no guilt."
            </p>

            <button
              @click="openLink"
              class="w-full inline-flex items-center justify-center px-6 py-4 border border-transparent text-lg font-bold rounded-xl shadow-lg text-white bg-linear-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 transform hover:-translate-y-1 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <font-awesome-icon
                :icon="['fad', 'fa-mug-hot']"
                class="mr-3 text-xl"
              />
              Support on Ko-fi
            </button>

            <p
              class="mt-4 text-xs text-gray-400 flex items-center justify-center gap-1.5"
            >
              <font-awesome-icon
                :icon="['fad', 'fa-octagon-check']"
                class="text-green-500"
              />
              Secure payments processed via Ko-fi
            </p>
            <div class="mt-6 pt-6 border-t border-gray-200">
              <p class="text-xs text-gray-500">
                Questions?
                <a
                  href="mailto:feedback@dailyoffice2019.com"
                  class="text-indigo-600 hover:underline font-medium"
                  >Contact us</a
                >
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Browser } from '@capacitor/browser';

export default {
  name: 'DonationPrompt',
  props: {
    variant: {
      type: String,
      default: 'short', // 'short' or 'long'
      validator: (value) => ['short', 'long'].includes(value),
    },
  },
  setup() {
    const openLink = async () => {
      await Browser.open({ url: 'https://ko-fi.com/dailyoffice' });
    };

    return {
      openLink,
    };
  },
};
</script>

<style scoped>
/* Scoped styles if needed, mainly relying on Tailwind */
</style>
