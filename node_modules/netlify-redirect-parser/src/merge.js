const { isDeepStrictEqual } = require('util')

const { splitResults } = require('./results')

// Merge redirects from `_redirects` with the ones from `netlify.toml`.
// When both are specified, both are used and `_redirects` has priority.
// Since in both `netlify.toml` and `_redirects`, only the first matching rule
// is used, it is possible to merge `_redirects` to `netlify.toml` by prepending
// its rules to `netlify.toml` `redirects` field.
const mergeRedirects = function ({ fileRedirects, configRedirects }) {
  const results = [...fileRedirects, ...configRedirects]
  const { redirects, errors } = splitResults(results)
  const mergedRedirects = redirects.filter(isUniqueRedirect)
  return { redirects: mergedRedirects, errors }
}

// Remove duplicates. This is especially likely considering `fileRedirects`
// might have been previously merged to `configRedirects`, which happens when
// `netlifyConfig.redirects` is modified by plugins.
// The latest duplicate value is the one kept.
const isUniqueRedirect = function (redirect, index, redirects) {
  return !redirects.slice(index + 1).some((otherRedirect) => isDeepStrictEqual(redirect, otherRedirect))
}

module.exports = { mergeRedirects }
