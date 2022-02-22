const colors = require("tailwindcss/colors");

module.exports = {
  content: ["./public/**/*.html", "./src/**/*.{html,js,jsx,ts,tsx,vue}"],
  // darkMode: "class", // or 'media' or 'class'
  theme: {
    extend: {
      colors: {
        sky: colors.sky,
      },
    },
  },
  plugins: [
    // ...
    require("@tailwindcss/forms"),
  ],
};
