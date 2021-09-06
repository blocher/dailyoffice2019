const fetch = require('node-fetch')

const { CONTENT_TYPE } = require('./consts')

/**
 * @typedef {{ sha: string, handlers: string[], content_length: number, content_type: string }} BundleInfo
 */

/**
 * Uploads a prepared handler bundle to the API
 *
 * @param {Buffer} buf UTF-8 encoded handler bundle
 * @param {BundleInfo} info metadata about the bundle
 * @param {string} deployId id of the deploy the bundle is deployed for
 * @param {string} apiHost  host of the Netlify API
 * @param {string} apiToken token for authorizing on the API
 * @returns {Promise<boolean>} Whether the bundle was newly uploaded (and did not already exist)
 */
async function uploadBundle(buf, info, deployId, apiHost, apiToken) {
  if (!apiToken) {
    throw new Error('API token is missing')
  }

  const resp = await fetch(`https://${apiHost}/api/v1/deploys/${deployId}/edge_handlers`, {
    method: 'POST',
    body: JSON.stringify(info),
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiToken}`,
    },
  })

  if (!resp.ok) {
    throw new Error(`Invalid status: ${resp.status}`)
  }

  const { error, exists, upload_url: uploadUrl } = await resp.json()
  if (error) {
    throw new Error(`Failed to upload: ${error}`)
  }
  if (exists) {
    return false
  }
  if (!uploadUrl) {
    throw new Error('Missing upload url')
  }

  await fetch(uploadUrl, {
    method: 'PUT',
    body: buf,
    headers: {
      'Content-Type': CONTENT_TYPE,
    },
  })

  return true
}

module.exports = uploadBundle
