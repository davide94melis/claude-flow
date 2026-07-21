'use strict';
/**
 * Pure per-pixel diff. No browser/node-only APIs — unit-testable.
 * @param {Uint8ClampedArray|Buffer} a RGBA bytes (len = w*h*4)
 * @param {Uint8ClampedArray|Buffer} b RGBA bytes (len = w*h*4)
 * @param {number} w
 * @param {number} h
 * @param {{threshold?:number, buildMask?:boolean}} [opts] threshold = max per-channel delta (0-255) to still count as "equal"
 * @returns {{score:number,diffCount:number,total:number,mask?:Uint8ClampedArray}}
 */
function diffCore(a, b, w, h, opts = {}) {
  const threshold = opts.threshold == null ? 12 : opts.threshold;
  const total = w * h;
  if (a.length !== total * 4 || b.length !== total * 4) {
    throw new RangeError(`diffCore: buffer length must be w*h*4 (${total * 4}), got a=${a.length} b=${b.length}`);
  }
  const mask = opts.buildMask ? new Uint8ClampedArray(total * 4) : null;
  let diffCount = 0;
  for (let p = 0; p < total; p++) {
    const i = p * 4;
    const dr = Math.abs(a[i] - b[i]);
    const dg = Math.abs(a[i + 1] - b[i + 1]);
    const db = Math.abs(a[i + 2] - b[i + 2]);
    const da = Math.abs(a[i + 3] - b[i + 3]);
    const isDiff = Math.max(dr, dg, db, da) > threshold;
    if (isDiff) diffCount++;
    if (mask) {
      // red = diff (opaque), transparent = match
      mask[i] = 255;
      mask[i + 1] = 0;
      mask[i + 2] = 0;
      mask[i + 3] = isDiff ? 255 : 0;
    }
  }
  const score = total === 0 ? 1 : 1 - diffCount / total;
  const out = { score, diffCount, total };
  if (mask) out.mask = mask;
  return out;
}

module.exports = { diffCore };
