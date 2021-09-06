const path = require('path')
const process = require('process')

module.exports.LOCAL_OUT_DIR = path.join(process.cwd(), '.netlify', 'edge-handlers')
module.exports.MANIFEST_FILE = 'manifest.json'
module.exports.MAIN_FILE = '__netlifyMain.ts'
module.exports.CONTENT_TYPE = 'application/javascript'
