const lineParser = require('./line-parser')
const NetlifyConfigParser = require('./netlify-config-parser')

exports.parseRedirectsFormat = lineParser.parse
exports.parseNetlifyConfig = NetlifyConfigParser.parse
