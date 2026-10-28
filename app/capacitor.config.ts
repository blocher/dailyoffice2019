import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.dailyoffice.dailyoffice2019',
  appName: 'daily_office',
  webDir: 'dist',
  plugins: {
    // The cover art (store/scripts/build-icons.mjs) stays up until main.js
    // hides it after the first render, or at most launchShowDuration.
    SplashScreen: {
      launchShowDuration: 4000,
      launchAutoHide: true,
      launchFadeOutDuration: 250,
      backgroundColor: '#8c1d22',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
    },
  },
};

export default config;
