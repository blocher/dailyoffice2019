const { parseFileRedirects } = require('./line_parser')
const { mergeRedirects } = require('./merge')
const { parseConfigRedirects } = require('./netlify_config_parser')
const { normalizeRedirects } = require('./normalize')
const { splitResults, concatResults } = require('./results')

// Parse all redirects given programmatically via the `configRedirects` property, `netlify.toml` and `_redirects` files, then normalize
// and validate those.
const parseAllRedirects = async function ({ redirectsFiles = [], netlifyConfigPath, configRedirects = [], ...opts }) {
  const [
    { redirects: fileRedirects, errors: fileParseErrors },
    { redirects: parsedConfigRedirects, errors: configParseErrors },
  ] = await Promise.all([getFileRedirects(redirectsFiles), getConfigRedirects(netlifyConfigPath)])
  const { redirects: normalizedFileRedirects, errors: fileNormalizeErrors } = normalizeRedirects(fileRedirects, opts)
  const { redirects: normalizedParsedConfigRedirects, errors: parsedConfigNormalizeErrors } = normalizeRedirects(
    parsedConfigRedirects,
    opts,
  )
  const { redirects: normalizedConfigRedirects, errors: configNormalizeErrors } = normalizeRedirects(
    configRedirects,
    opts,
  )
  const { redirects, errors: mergeErrors } = mergeRedirects({
    fileRedirects: normalizedFileRedirects,
    configRedirects: [...normalizedParsedConfigRedirects, ...normalizedConfigRedirects],
  })
  const errors = [
    ...fileParseErrors,
    ...fileNormalizeErrors,
    ...configParseErrors,
    ...parsedConfigNormalizeErrors,
    ...configNormalizeErrors,
    ...mergeErrors,
  ]
  return { redirects, errors }
}

const getFileRedirects = async function (redirectsFiles) {
  const resultsArrays = await Promise.all(redirectsFiles.map(parseFileRedirects))
  return concatResults(resultsArrays)
}

const getConfigRedirects = async function (netlifyConfigPath) {
  if (netlifyConfigPath === undefined) {
    return splitResults([])
  }

  return await parseConfigRedirects(netlifyConfigPath)
}

module.exports = { parseAllRedirects }
