// If one header fails to parse, we still try to return the other ones
const splitResults = function (results) {
  const headers = results.filter((result) => !isError(result))
  const errors = results.filter(isError)
  return { headers, errors }
}

const isError = function (result) {
  return result instanceof Error
}

// Concatenate an array of `{ headers, erors }`
const concatResults = function (resultsArrays) {
  // eslint-disable-next-line unicorn/prefer-spread
  const headers = [].concat(...resultsArrays.map(getHeaders))
  // eslint-disable-next-line unicorn/prefer-spread
  const errors = [].concat(...resultsArrays.map(getErrors))
  return { headers, errors }
}

const getHeaders = function ({ headers }) {
  return headers
}

const getErrors = function ({ errors }) {
  return errors
}

module.exports = { splitResults, concatResults }
