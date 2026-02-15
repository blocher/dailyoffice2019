<template>
  <div v-if="variant === 'short'" class="text-center my-4 space-y-2">
    <button
      @click="openLink"
      class="inline-flex items-center px-3 py-1.5 border border-indigo-200 text-xs font-medium rounded-full text-indigo-700 bg-indigo-50 hover:bg-indigo-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
    >
      <span class="mr-1.5 text-red-500">❤</span>
      Support the Daily Office
    </button>
  </div>

  <div v-else class="max-w-3xl mx-auto my-12 px-4 sm:px-6 lg:px-8 font-sans">
    <div
      class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden"
    >
      <div class="p-6 sm:p-8">
        <div class="text-center mb-6">
          <h3 class="text-xl font-bold text-gray-900 mb-2">
            Thank you for praying with us!
          </h3>
          <p class="text-lg font-bold text-gray-900 max-w-2xl mx-auto my-2">
            If this tool has blessed your prayer life and you feel led to help
            me sustain and grow it,<br />
            your support is deeply appreciated.
          </p>
          <p class="text-gray-600 max-w-2xl mx-auto">
            This site will always be 100% free. There is no paywall, no
            obligation, and no guilt. If you have any questions or want to share
            your experience, please
            <a
              href="mailto:feedback@dailyoffice2019.com"
              class="text-indigo-600 hover:underline"
              >feedback@dailyoffice2019.com</a
            >.
          </p>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-8 text-sm text-gray-600">
          <div>
            <ul class="space-y-2 list-disc list-inside text-gray-700">
              <li>Hosting, app store fees, and bible text licensing</li>
              <li>Audio version generation and hosting</li>
              <li>Saint hagiography generation</li>
              <li>Coming soon: Spanish edition!</li>
              <li>Coming soon: Podcast!</li>
            </ul>
          </div>

          <div
            class="bg-gray-50 rounded-lg p-5 flex flex-col justify-center items-center text-center"
          >
            <button
              @click="openLink"
              class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transform hover:-translate-y-0.5 transition-all duration-200"
            >
              <span class="mr-2">☕</span>
              Support our work on Ko-fi
            </button>
          </div>
        </div>

        <div class="text-center text-xs text-gray-400">
          <p>Secure payments processed via Ko-fi</p>
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
