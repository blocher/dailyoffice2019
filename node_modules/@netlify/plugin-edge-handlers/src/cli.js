#!/usr/bin/env node

const path = require('path')
const process = require('process')

const { isDirectory } = require('path-type')

const { assemble, bundleFunctionsForCli } = require('./lib')

const build = async ({ EDGE_HANDLERS_SRC }) => {
  const srcDir = path.resolve(EDGE_HANDLERS_SRC)

  if (!(await isDirectory(srcDir))) {
    console.log(
      JSON.stringify({
        code: 'directory-not-found',
        dir: srcDir,
        success: false,
      }),
    )
    return
  }

  let mainFile
  let handlers
  try {
    const result = await assemble(srcDir)
    // eslint-disable-next-line prefer-destructuring
    mainFile = result.mainFile
    // eslint-disable-next-line prefer-destructuring
    handlers = result.handlers
  } catch (error) {
    console.log(
      JSON.stringify({
        code: 'unknown',
        msg: `Failed discovering Edge Handlers: ${error.message}`,
        success: false,
      }),
    )
    return
  }

  if (handlers.length === 0) {
    console.log(JSON.stringify({ bundle: null, bundled: srcDir, handlers: [], success: true }))
    return
  }

  try {
    const bundle = await bundleFunctionsForCli(mainFile)
    console.log(JSON.stringify({ bundle, bundled: srcDir, handlers, success: true }))
  } catch (error) {
    console.log(JSON.stringify(error))
  }
}

const main = async () => {
  const [, bin, command, EDGE_HANDLERS_SRC] = process.argv

  const USAGE = `Usage: ${bin} build <Edge Handlers directory>`

  if (command !== 'build') {
    console.log(
      JSON.stringify({
        code: 'cli',
        msg: `'${command}' is not a valid CLI command\n\n${USAGE}`,
        success: false,
      }),
    )
    return
  }
  if (!EDGE_HANDLERS_SRC) {
    console.log(
      JSON.stringify({
        code: 'cli',
        msg: `You must specify the Edge Handlers source directory\n\n${USAGE}`,
        success: false,
      }),
    )
    return
  }

  await build({ EDGE_HANDLERS_SRC })
}

main()
