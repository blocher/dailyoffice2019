module.exports = {
  root: true,
  extends: ["eslint:recommended"],
  parser: "babel-eslint",
  globals: {
    window: true,
    document: true,
  },
  rules: {
    "arrow-parens": [0, "as-needed"],
    "comma-dangle": [0, "never"],
    "no-mixed-spaces-and-tabs": 1,
  },
};
