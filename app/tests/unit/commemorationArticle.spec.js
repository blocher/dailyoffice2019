import { describe, expect, it } from 'vitest';
import {
  createCiter,
  describeUrl,
  splitParagraphs,
} from '@/views/Commemoration.vue';

const sentence = (n) =>
  `Sentence number ${n} tells a part of the story of the saint in some detail, at reasonable length[1].`;

describe('Commemoration article helpers', () => {
  it('breaks one long block into paragraphs at sentence boundaries', () => {
    const text = Array.from({ length: 20 }, (_, i) => sentence(i + 1)).join(
      ' '
    );
    const paragraphs = splitParagraphs(text);

    expect(paragraphs.length).toBeGreaterThan(2);
    expect(paragraphs.join(' ')).toBe(text);
    paragraphs.forEach((p) => expect(p).toMatch(/\[1\]\.$/));
  });

  it('does not break after abbreviations or initials', () => {
    const filler = 'x'.repeat(600);
    const text = `He met St. Francis ${filler}. Then C. S. Lewis wrote. The end came.`;
    const paragraphs = splitParagraphs(text);

    expect(paragraphs.some((p) => p.includes('St. Francis'))).toBe(true);
    expect(paragraphs.some((p) => p.includes('C. S. Lewis'))).toBe(true);
  });

  it('keeps existing paragraph breaks', () => {
    expect(splitParagraphs('<p>One.</p><p>Two.</p>')).toEqual(['One.', 'Two.']);
    expect(splitParagraphs('One.\n\nTwo.')).toEqual(['One.', 'Two.']);
    expect(splitParagraphs('')).toEqual([]);
  });

  it('numbers citations once across fields and lists the sources', () => {
    const { cite, sources } = createCiter();
    const first = cite('Alpha[1][2].', [
      'https://en.wikipedia.org/wiki/Philip_the_Evangelist',
      'https://www.britannica.com/biography/Saint-Philip',
    ]);
    const second = cite('Beta[1] gamma[9].', [
      'https://www.britannica.com/biography/Saint-Philip',
    ]);

    expect(first).toContain('>1</a></sup><sup class="cite">');
    expect(second).toContain('>2</a></sup>');
    expect(second).not.toContain('[9]');
    expect(sources.map((s) => s.number)).toEqual([1, 2]);
    expect(sources[0].label).toBe('en.wikipedia.org › Philip the Evangelist');
  });

  it('ignores non-web citation urls and strips markup', () => {
    const { cite, sources } = createCiter();
    const html = cite('<img src=x onerror=alert(1)>Hi[1]', [
      'javascript:alert(1)',
    ]);

    expect(html).not.toContain('onerror');
    expect(html).not.toContain('javascript');
    expect(sources).toEqual([]);
  });

  it('describes urls by host and last path segment', () => {
    expect(describeUrl('https://www.catholic.org/saints/')).toBe(
      'catholic.org › saints'
    );
    expect(describeUrl('https://example.com')).toBe('example.com');
  });
});
