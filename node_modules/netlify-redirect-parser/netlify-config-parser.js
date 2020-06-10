const Result = require('./result')
const {
  isPlainObj,
  redirectMatch,
  isInvalidSource,
  isProxy,
} = require('./common')
const resolveConfig = require('@netlify/config')

async function parse(config) {
  const result = new Result()
  const {
    config: { redirects },
  } = await resolveConfig({ config })

  if (!Array.isArray(redirects)) {
    return result
  }

  redirects.forEach((obj, idx) => {
    if (!isPlainObj(obj)) {
      result.addError(idx, obj)
      return
    }

    const redirect = redirectMatch(obj)
    if (!redirect) {
      result.addError(idx, JSON.stringify(obj))
      return
    }

    if (isInvalidSource(redirect)) {
      result.addError(idx, JSON.stringify(obj), {
        reason: 'Invalid /.netlify path in redirect source',
      })
      return
    }

    if (isProxy(redirect)) {
      redirect.proxy = true
    }

    result.addSuccess(redirect)
  })

  return result
}

exports.parse = parse
