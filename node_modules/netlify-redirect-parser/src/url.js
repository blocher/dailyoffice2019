// Check if a field is valid redirect URL
const isUrl = function (pathOrUrl) {
  return SCHEMES.some((scheme) => pathOrUrl.startsWith(scheme))
}

const SCHEMES = ['http://', 'https://']

module.exports = { isUrl }
