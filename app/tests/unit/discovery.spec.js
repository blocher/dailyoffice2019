import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  DISPLAY_FEATURES_VERSION,
  discoveryState,
  dismissDisplayCard,
  loadDiscovery,
  markDisplaySeen,
} from '@/helpers/discovery';
import { DynamicStorage } from '@/helpers/storage';

vi.mock('@/helpers/storage', () => ({
  DynamicStorage: { getItem: vi.fn(), setItem: vi.fn() },
}));

function stubStorage(values) {
  DynamicStorage.getItem.mockImplementation(async (key) => values[key] ?? null);
}

describe('discovery nudges', () => {
  beforeEach(() => {
    DynamicStorage.setItem.mockReset().mockResolvedValue();
  });

  it('shows the Display dot and the card to someone new', async () => {
    stubStorage({});
    await loadDiscovery();
    expect(discoveryState.displayNew).toBe(true);
    expect(discoveryState.showDisplayCard).toBe(true);
  });

  it('clears the dot once the panel is opened, until the next new feature', async () => {
    stubStorage({});
    await loadDiscovery();
    await markDisplaySeen();
    expect(discoveryState.displayNew).toBe(false);
    expect(DynamicStorage.setItem).toHaveBeenCalledWith(
      'displaySeenVersion',
      String(DISPLAY_FEATURES_VERSION)
    );

    stubStorage({ displaySeenVersion: String(DISPLAY_FEATURES_VERSION - 1) });
    await loadDiscovery();
    expect(discoveryState.displayNew).toBe(true);

    stubStorage({ displaySeenVersion: String(DISPLAY_FEATURES_VERSION) });
    await loadDiscovery();
    expect(discoveryState.displayNew).toBe(false);
  });

  it('keeps the card away once dismissed', async () => {
    stubStorage({});
    await loadDiscovery();
    await dismissDisplayCard();
    expect(discoveryState.showDisplayCard).toBe(false);
    expect(DynamicStorage.setItem).toHaveBeenCalledWith(
      'displayCardDismissed',
      'true'
    );
    stubStorage({ displayCardDismissed: 'true' });
    await loadDiscovery();
    expect(discoveryState.showDisplayCard).toBe(false);
  });
});
