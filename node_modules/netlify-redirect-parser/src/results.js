// If one redirect fails to parse, we still try to return the other ones
const splitResults = function (results) {
  const redirects = results.filter((result) => !isError(result))
  const errors = results.filter(isError)
  return { redirects, errors }
}

const isError = function (result) {
  return result instanceof Error
}

// Concatenate an array of `{ redirects, erors }`
const concatResults = function (resultsArrays) {
  // eslint-disable-next-line unicorn/prefer-spread
  const redirects = [].concat(...resultsArrays.map(getRedirects))
  // eslint-disable-next-line unicorn/prefer-spread
  const errors = [].concat(...resultsArrays.map(getErrors))
  return { redirects, errors }
}

const getRedirects = function ({ redirects }) {
  return redirects
}

const getErrors = function ({ errors }) {
  return errors
}

module.exports = { splitResults, concatResults }
