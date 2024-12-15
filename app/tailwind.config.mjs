import colors from "tailwindcss/colors";
import forms from "@tailwindcss/forms";

export default {
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
    forms,
  ],
};
