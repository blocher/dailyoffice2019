'use strict'

module.exports = function commonPathPrefix ([first, ...paths], sep) {
  if (!sep) {
    const m = /(\/|\\)/.exec(first)
    if (!m) return '' // The first path did not contain any directory components. Bail now.

    sep = m[0]
  }

  const parts = first.split(sep)

  let prefix = parts.length
  for (const p of paths) {
    const compare = p.split(sep)
    for (let i = 0; i < prefix; i++) {
      if (compare[i] !== parts[i]) {
        prefix = i
      }
    }

    if (prefix === 0) break
  }

  return prefix === 0 ? '' : parts.slice(0, prefix).join(sep) + sep
}
