# Netlify Redirect Parser

This is a small node library for parsing Netlify's redirect rules.

It works with `_redirect`, `netlify.toml`, `netlify.yml` and `netlify.json` files and will
turn the rules into a canonical list of object literals representing
the parsed rules

Published as https://www.npmjs.com/package/netlify-redirect-parser. For most users, you are not meant to use this directly, please refer to https://github.com/netlify/cli instead. However if you are debugging issues with redirect parsing, issues and PRs are welcome.
