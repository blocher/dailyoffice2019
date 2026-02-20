<template>
  <!-- Short Variant: Compact pill for headers/navbars -->
  <div v-if="variant === 'short'" class="flex items-center justify-center my-2">
    <button
      @click="openLink"
      class="group donation-short-button relative inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border rounded-full shadow-sm hover:shadow-md transition-all duration-300 transform hover:-translate-y-0.5"
    >
      <div
        class="flex items-center justify-center w-6 h-6 rounded-full bg-red-50 dark:bg-red-900/30 text-red-500 dark:text-red-400 group-hover:scale-110 transition-transform duration-300"
      >
        <font-awesome-icon :icon="['fad', 'fa-heart']" />
      </div>
      <span
        class="donation-short-label text-xs font-semibold text-gray-700 dark:text-gray-200"
        >Support the Daily Office</span
      >
    </button>
  </div>

  <!-- Long Variant: Full feature card for detailed pages -->
  <div
    v-else
    class="mx-auto font-sans"
    :class="compact ? 'max-w-none my-0 px-0' : 'max-w-4xl my-12 px-4'"
  >
    <div
      class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden h-full flex flex-col"
      :class="{
        'rounded-2xl shadow-xl donation-surface-accent': !compact,
      }"
    >
      <!-- Hero Header -->
      <div
        class="text-center relative overflow-hidden border-b border-gray-100 dark:border-gray-700"
        :class="compact ? 'p-6' : 'p-8 sm:p-10'"
      >
        <div
          class="absolute top-0 left-0 w-full h-full opacity-5 pointer-events-none"
        >
          <font-awesome-icon
            :icon="['fad', 'fa-books']"
            class="donation-bg-glyph text-9xl absolute -top-10 -left-10 transform rotate-12"
          />
          <font-awesome-icon
            :icon="['fad', 'fa-book-bible']"
            class="donation-bg-glyph text-9xl absolute -bottom-10 -right-10 transform -rotate-12"
          />
        </div>

        <div
          class="relative z-10 mx-auto"
          :class="compact ? 'max-w-full' : 'max-w-2xl'"
        >
          <div
            class="donation-gift-badge inline-flex items-center justify-center rounded-full mb-4 shadow-sm ring-4 ring-white dark:ring-gray-800"
            :class="compact ? 'w-12 h-12' : 'w-16 h-16 mb-6'"
          >
            <font-awesome-icon
              :icon="['fad', 'fa-gift']"
              class="donation-accent-text"
              :class="compact ? 'text-xl' : 'text-3xl'"
            />
          </div>
          <h3
            class="font-bold tracking-tight text-gray-900 dark:text-gray-100"
            :class="compact ? 'text-xl mb-2' : 'text-3xl font-extrabold mb-4'"
          >
            Support the Daily Office
          </h3>
          <p
            class="text-gray-600 dark:text-gray-300 leading-relaxed"
            :class="compact ? 'text-sm' : 'text-lg sm:text-x'"
          >
            Your generosity helps us sustain this ministry, generate audio
            daily, and keep these resources free for everyone.
          </p>
        </div>
      </div>

      <div
        :class="
          compact ? 'p-6 flex-grow flex flex-col justify-end' : 'p-8 sm:p-10'
        "
      >
        <div
          :class="
            compact ? 'space-y-6' : 'grid md:grid-cols-2 gap-10 items-center'
          "
        >
          <!-- Left Column: Impact List -->
          <div :class="compact ? 'space-y-4' : 'space-y-6'" v-if="!compact">
            <!-- Hide impact list on compact mode to save space, or simplify it -->
            <h4
              class="text-lg font-bold text-gray-900 dark:text-gray-100 border-b border-gray-100 dark:border-gray-700 pb-2"
            >
              Your support makes this possible:
            </h4>
            <ul class="space-y-4">
              <li class="flex items-start gap-4">
                <div
                  class="donation-icon-tile shrink-0 w-10 h-10 rounded-lg flex items-center justify-center"
                >
                  <font-awesome-icon
                    :icon="['fad', 'fa-server']"
                    class="text-lg"
                  />
                </div>
                <div>
                  <span
                    class="block font-semibold text-gray-900 dark:text-gray-100"
                    >Hosting & Bibe Licensing</span
                  >
                  <span class="text-sm text-gray-500 dark:text-gray-400"
                    >Servers, app store fees, and Bible text royalties.</span
                  >
                </div>
              </li>
              <li class="flex items-start gap-4">
                <div
                  class="shrink-0 w-10 h-10 rounded-lg bg-pink-50 dark:bg-pink-900/30 flex items-center justify-center text-pink-600 dark:text-pink-400"
                >
                  <font-awesome-icon
                    :icon="['fad', 'fa-microphone']"
                    class="text-lg"
                  />
                </div>
                <div>
                  <span
                    class="block font-semibold text-gray-900 dark:text-gray-100"
                    >Audio Production</span
                  >
                  <span class="text-sm text-gray-500 dark:text-gray-400"
                    >Daily audio generation, hosting, and podcast
                    distribution.</span
                  >
                </div>
              </li>
              <li class="flex items-start gap-4">
                <div
                  class="shrink-0 w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 dark:text-amber-400"
                >
                  <font-awesome-icon
                    :icon="['fad', 'fa-book-bible']"
                    class="text-lg"
                  />
                </div>
                <div>
                  <span
                    class="block font-semibold text-gray-900 dark:text-gray-100"
                    >Content Creation</span
                  >
                  <span class="text-sm text-gray-500 dark:text-gray-400"
                    >Saint hagiographies and the upcoming Podcast and Spanish
                    editions</span
                  >
                </div>
              </li>
            </ul>
          </div>

          <!-- Simplified Impact List for Compact Mode -->
          <div
            v-if="compact"
            class="text-sm text-gray-600 dark:text-gray-300 space-y-3"
          >
            <p class="font-medium text-gray-800 dark:text-gray-200">
              Your support funds:
            </p>
            <ul class="space-y-2">
              <li
                class="flex items-center gap-2 text-gray-600 dark:text-gray-300"
              >
                <font-awesome-icon
                  :icon="['fad', 'fa-server']"
                  class="donation-accent-text"
                />
                <span>Infrastructure & bible licensing</span>
              </li>
              <li
                class="flex items-center gap-2 text-gray-600 dark:text-gray-300"
              >
                <font-awesome-icon
                  :icon="['fad', 'fa-microphone']"
                  class="text-pink-400"
                />
                <span>Audio and hagiography production & hosting</span>
              </li>
              <li
                class="flex items-center gap-2 text-gray-600 dark:text-gray-300"
              >
                <font-awesome-icon
                  :icon="['fad', 'fa-book-bible']"
                  class="text-amber-400"
                />
                <span>Coming soon: Spanish and podcasts</span>
              </li>
            </ul>
          </div>

          <!-- Right Column: CTA & Info -->
          <div
            class="bg-gray-50 dark:bg-gray-700/50 rounded-xl text-center border border-gray-100 dark:border-gray-600 shadow-inner"
            :class="compact ? 'p-4 mt-auto' : 'p-8'"
          >
            <p
              class="text-gray-600 dark:text-gray-300 italic"
              :class="compact ? 'text-xs mb-4' : 'mb-6'"
            >
              "This site will always be 100% free. There is no paywall, no
              obligation, and no guilt."
            </p>

            <button
              @click="openLink"
              class="donation-cta w-full inline-flex items-center justify-center border font-bold rounded-xl shadow-lg transform hover:-translate-y-1 transition-all duration-200 focus-visible:outline-none"
              :class="compact ? 'px-4 py-3 text-sm' : 'px-6 py-4 text-lg'"
            >
              <font-awesome-icon
                :icon="['fad', 'fa-mug-hot']"
                class="mr-3"
                :class="compact ? 'text-lg' : 'text-xl'"
              />
              Support on Ko-fi
            </button>

            <p
              class="mt-4 text-xs text-gray-400 dark:text-gray-500 flex items-center justify-center gap-1.5"
            >
              <font-awesome-icon
                :icon="['fad', 'fa-octagon-check']"
                class="text-green-500"
              />
              Secure payments processed via Ko-fi
            </p>
            <div
              class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-600"
            >
              <p class="text-xs text-gray-500 dark:text-gray-400">
                Questions?
                <a
                  href="mailto:feedback@dailyoffice2019.com"
                  class="donation-accent-link hover:underline font-medium"
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
    compact: {
      type: Boolean,
      default: false,
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
.donation-short-button {
  border-color: var(--el-border-color-light);
}

.donation-short-button:hover {
  border-color: var(--accent-color);
}

.group:hover .donation-short-label {
  color: var(--accent-color);
}

.donation-surface-accent {
  border-color: var(--accent-color);
}

.donation-bg-glyph {
  color: var(--accent-color);
  opacity: 0.28;
}

.donation-gift-badge {
  background-color: var(--el-fill-color-light);
}

.donation-icon-tile {
  background-color: var(--el-fill-color-light);
  color: var(--accent-color);
}

.donation-accent-text {
  color: var(--accent-color);
}

.donation-cta {
  background-color: var(--accent-color);
  border-color: var(--accent-color);
  color: var(--accent-contrast);
}

.donation-cta:hover {
  filter: brightness(0.95);
}

.donation-cta:focus-visible {
  box-shadow: 0 0 0 2px var(--accent-color);
}

.donation-accent-link {
  color: var(--accent-color);
}
</style>
