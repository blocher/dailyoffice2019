// A QR code at error-correction level L holds at most 2953 bytes; the
// encoder throws "Data too long" beyond that.
const QR_MAX_BYTES = 2953;

/** Whether this text can be encoded as a level-L QR code. */
export function fitsInQrCode(text) {
  return new window.TextEncoder().encode(text || '').length <= QR_MAX_BYTES;
}
