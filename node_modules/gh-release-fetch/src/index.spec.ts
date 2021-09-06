/* eslint-disable @typescript-eslint/no-var-requires,node/global-require */
import { newerVersion, fetchLatest } from './index'

test('compare versions', () => {
  expect(newerVersion('0.1.0', '0.0.1')).toBe(true)
  expect(newerVersion('v0.1.0', 'v0.0.1')).toBe(true)
  expect(newerVersion('v0.0.1', '')).toBe(true)

  expect(newerVersion('0.0.1', '0.0.1')).toBe(false)
  expect(newerVersion('v0.0.1', 'v0.0.1')).toBe(false)
  expect(newerVersion('', '0.0.1')).toBe(false)
})

jest.mock('node-fetch')
jest.mock('download')

describe('fetchLatest', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('should throw error when api limit is reached', async () => {
    const fetch = require('node-fetch')
    const response = {
      status: 403,
      json: () =>
        Promise.resolve({
          message: 'API rate limit exceeded for ',
        }),
    }
    fetch.mockResolvedValue(response)

    await expect(
      fetchLatest({
        repository: 'netlify/test',
        package: 'test',
        destination: 'bin/test',
        version: '1.0.0',
        extract: true,
      }),
    ).rejects.toEqual(new Error('API rate limit exceeded, please try again later'))
  })

  test('should add fetch options to API call when passed as a second argument', async () => {
    const fetch = require('node-fetch')
    const response = {
      status: 200,
      json: () =>
        Promise.resolve({
          tag_name: 'v1.0.0',
        }),
    }
    fetch.mockResolvedValue(response)

    await expect(
      fetchLatest(
        {
          repository: 'netlify/test',
          package: 'test',
          destination: 'bin/test',
          version: '1.0.0',
          extract: true,
        },
        { headers: { Authorization: 'token some_token' } },
      ),
    )

    expect(fetch).toHaveBeenCalledTimes(1)
    expect(fetch).toHaveBeenCalledWith('https://api.github.com/repos/netlify/test/releases/latest', {
      headers: { Authorization: 'token some_token' },
    })
  })
})
/* eslint-enable @typescript-eslint/no-var-requires,node/global-require */
