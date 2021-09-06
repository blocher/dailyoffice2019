const { readFile } = require('fs')
const { promisify } = require('util')

const pathExists = require('path-exists')
const { parse: loadToml } = require('toml')

const { splitResults } = require('./results')

const pReadFile = promisify(readFile)

// Parse `redirects` field in "netlify.toml" to an array of objects.
// This field is already an array of objects so it only validates and
// normalizes it.
const parseConfigRedirects = async function (netlifyConfigPath) {
  if (!(await pathExists(netlifyConfigPath))) {
    return splitResults([])
  }

  const results = await parseConfig(netlifyConfigPath)
  return splitResults(results)
}

// Load the configuration file and parse it (TOML)
const parseConfig = async function (configPath) {
  try {
    const configString = await pReadFile(configPath, 'utf8')
    const config = loadToml(configString)
    // Convert `null` prototype objects to normal plain objects
    const { redirects = [] } = JSON.parse(JSON.stringify(config))
    if (!Array.isArray(redirects)) {
      throw new TypeError(`"redirects" must be an array`)
    }
    return redirects
  } catch (error) {
    return [new Error(`Could not parse configuration file: ${error}`)]
  }
}

module.exports = { parseConfigRedirects }
