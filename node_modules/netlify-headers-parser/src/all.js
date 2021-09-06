const { parseFileHeaders } = require('./line_parser')
const { mergeHeaders } = require('./merge')
const { parseConfigHeaders } = require('./netlify_config_parser')
const { normalizeHeaders } = require('./normalize')
const { splitResults, concatResults } = require('./results')

// Parse all headers from `netlify.toml` and `_headers` file, then normalize
// and validate those.
const parseAllHeaders = async function ({ headersFiles = [], netlifyConfigPath, configHeaders = [], minimal = false }) {
  const [
    { headers: fileHeaders, errors: fileParseErrors },
    { headers: parsedConfigHeaders, errors: configParseErrors },
  ] = await Promise.all([getFileHeaders(headersFiles), getConfigHeaders(netlifyConfigPath)])
  const { headers: normalizedFileHeaders, errors: fileNormalizeErrors } = normalizeHeaders(fileHeaders, minimal)
  const { headers: normalizedConfigParseHeaders, errors: configParseNormalizeErrors } = normalizeHeaders(
    parsedConfigHeaders,
    minimal,
  )
  const { headers: normalizedConfigHeaders, errors: configNormalizeErrors } = normalizeHeaders(configHeaders, minimal)
  const { headers, errors: mergeErrors } = mergeHeaders({
    fileHeaders: normalizedFileHeaders,
    configHeaders: [...normalizedConfigParseHeaders, ...normalizedConfigHeaders],
  })
  const errors = [
    ...fileParseErrors,
    ...fileNormalizeErrors,
    ...configParseErrors,
    ...configParseNormalizeErrors,
    ...configNormalizeErrors,
    ...mergeErrors,
  ]
  return { headers, errors }
}

const getFileHeaders = async function (headersFiles) {
  const resultsArrays = await Promise.all(headersFiles.map(parseFileHeaders))
  return concatResults(resultsArrays)
}

const getConfigHeaders = async function (netlifyConfigPath) {
  if (netlifyConfigPath === undefined) {
    return splitResults([])
  }

  return await parseConfigHeaders(netlifyConfigPath)
}

module.exports = { parseAllHeaders }
