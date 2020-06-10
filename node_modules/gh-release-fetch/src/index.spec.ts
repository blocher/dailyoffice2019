import { newerVersion } from './index'

test('compare versions', () => {
  expect(newerVersion("0.1.0", "0.0.1")).toBe(true)
  expect(newerVersion("v0.1.0", "v0.0.1")).toBe(true)
  expect(newerVersion("v0.0.1", "")).toBe(true)

  expect(newerVersion("0.0.1", "0.0.1")).toBe(false)
  expect(newerVersion("v0.0.1", "v0.0.1")).toBe(false)
  expect(newerVersion("", "0.0.1")).toBe(false)
})
