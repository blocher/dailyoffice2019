import { Agent } from 'http'

import download from 'download'
import makeDir from 'make-dir'
import fetch, { RequestInit } from 'node-fetch'
import { gt } from 'semver'

type DownloadOptions = Pick<RequestInit, 'agent'>

export interface Release {
  repository: string
  package: string
  destination: string
  version: string
  extract: boolean
}

export async function fetchLatest(release: Release, fetchOptions?: RequestInit): Promise<void> {
  // eslint-disable-next-line no-param-reassign
  release.version = await resolveRelease(release.repository, fetchOptions)
  const agent = fetchOptions && fetchOptions.agent
  return fetchVersion(release, { agent })
}

export async function fetchVersion(release: Release, { agent }: DownloadOptions = {}): Promise<void> {
  validateRelease(release)
  await downloadFile(release, { agent })
}

export async function updateAvailable(
  repository: string,
  currentVersion: string,
  fetchOptions?: RequestInit,
): Promise<boolean> {
  const latestVersion = await resolveRelease(repository, fetchOptions)
  return newerVersion(latestVersion, currentVersion)
}

async function resolveRelease(repository: string, fetchOptions?: RequestInit): Promise<string> {
  const res = await fetch(`https://api.github.com/repos/${repository}/releases/latest`, fetchOptions)
  const json = await res.json()
  if (res.status === 403 && typeof json.message === 'string' && json.message.includes('API rate limit exceeded')) {
    throw new Error('API rate limit exceeded, please try again later')
  }
  return json.tag_name
}

async function downloadFile(release: Release, { agent }: DownloadOptions) {
  const url = `https://github.com/${release.repository}/releases/download/${release.version}/${release.package}`
  await makeDir(release.destination)
  await download(url, release.destination, {
    extract: release.extract,
    agent: agent as Agent,
  })
}

function validateRelease(release: Release) {
  if (!release.repository) {
    throw new Error('Missing release repository')
  }

  if (!release.package) {
    throw new Error('Missing release package name')
  }

  if (!release.destination) {
    throw new Error('Missing release destination')
  }

  if (!release.version) {
    throw new Error('Missing release version')
  }
}

export function newerVersion(latestVersion: string, currentVersion: string): boolean {
  if (!latestVersion) {
    return false
  }

  if (!currentVersion) {
    return true
  }

  const normalizedLatestVersion = latestVersion.replace(/^v/, '')
  const normalizedCurrentVersion = currentVersion.replace(/^v/, '')

  return gt(normalizedLatestVersion, normalizedCurrentVersion)
}
