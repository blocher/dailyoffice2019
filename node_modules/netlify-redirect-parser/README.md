# Netlify Redirect Parser

[![Coverage Status](https://codecov.io/gh/netlify/netlify-redirect-parser/branch/main/graph/badge.svg)](https://codecov.io/gh/netlify/netlify-redirect-parser)
[![Tests](https://github.com/netlify/netlify-redirect-parser/workflows/Test/badge.svg)](https://github.com/netlify/netlify-redirect-parser/actions)

Parses redirect rules from both `_redirects` and `netlify.toml` and normalizes them to an array of objects.

For most users, you are not meant to use this directly, please refer to https://github.com/netlify/cli instead. However
if you are debugging issues with redirect parsing, issues and PRs are welcome.
