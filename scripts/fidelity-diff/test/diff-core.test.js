const assert = require('node:assert');
const { diffCore } = require('../diff-core.js');

// helper: build a WxH RGBA buffer filled with one color
function fill(w, h, [r, g, b, a = 255]) {
  const buf = new Uint8ClampedArray(w * h * 4);
  for (let i = 0; i < w * h; i++) { buf[i*4]=r; buf[i*4+1]=g; buf[i*4+2]=b; buf[i*4+3]=a; }
  return buf;
}

// 1) identical -> score 1, 0 diffs
(() => {
  const a = fill(2, 2, [10, 20, 30]);
  const b = fill(2, 2, [10, 20, 30]);
  const r = diffCore(a, b, 2, 2, { threshold: 10 });
  assert.strictEqual(r.total, 4);
  assert.strictEqual(r.diffCount, 0);
  assert.strictEqual(r.score, 1);
})();

// 2) all different -> score 0
(() => {
  const a = fill(2, 2, [0, 0, 0]);
  const b = fill(2, 2, [255, 255, 255]);
  const r = diffCore(a, b, 2, 2, { threshold: 10 });
  assert.strictEqual(r.diffCount, 4);
  assert.strictEqual(r.score, 0);
})();

// 3) half different -> score 0.5
(() => {
  const a = fill(2, 2, [0, 0, 0]);       // 4 black px
  const b = fill(2, 2, [0, 0, 0]);
  b[0]=255; b[1]=255; b[2]=255;          // px0 -> white
  b[4]=255; b[5]=255; b[6]=255;          // px1 -> white
  const r = diffCore(a, b, 2, 2, { threshold: 10 });
  assert.strictEqual(r.diffCount, 2);
  assert.strictEqual(r.score, 0.5);
})();

// 4) below threshold not counted
(() => {
  const a = fill(1, 1, [100, 100, 100]);
  const b = fill(1, 1, [105, 103, 108]); // max delta 8
  const r = diffCore(a, b, 1, 1, { threshold: 10 });
  assert.strictEqual(r.diffCount, 0);
})();

// 5) mask marks differing pixels red, matching pixels transparent
(() => {
  const a = fill(1, 2, [0,0,0]);
  const b = fill(1, 2, [0,0,0]);
  b[4]=255; b[5]=255; b[6]=255;          // px1 differs
  const r = diffCore(a, b, 1, 2, { threshold: 10, buildMask: true });
  assert.strictEqual(r.mask[3], 0);      // px0 alpha transparent (match)
  assert.strictEqual(r.mask[7], 255);    // px1 alpha opaque (diff)
  assert.strictEqual(r.mask[4], 255);    // px1 red channel
})();

// 6) threshold boundary: delta == threshold not counted, delta == threshold+1 counted
(() => {
  const a = fill(1, 1, [100, 100, 100]);
  const bEq = fill(1, 1, [110, 100, 100]);   // delta exactly 10 == threshold
  const rEq = diffCore(a, bEq, 1, 1, { threshold: 10 });
  assert.strictEqual(rEq.diffCount, 0);
  const bOver = fill(1, 1, [111, 100, 100]); // delta 11 == threshold+1
  const rOver = diffCore(a, bOver, 1, 1, { threshold: 10 });
  assert.strictEqual(rOver.diffCount, 1);
})();

// 7) default threshold (opts.threshold omitted, default 12)
(() => {
  const a = fill(1, 1, [100, 100, 100]);
  const bOver = fill(1, 1, [113, 100, 100]); // delta 13 > 12
  const rOver = diffCore(a, bOver, 1, 1, {});
  assert.strictEqual(rOver.diffCount, 1);
  const bEq = fill(1, 1, [112, 100, 100]);   // delta 12, not > 12
  const rEq = diffCore(a, bEq, 1, 1, {});
  assert.strictEqual(rEq.diffCount, 0);
})();

// 8) Buffer input (not only Uint8ClampedArray)
(() => {
  const a = Buffer.from([10, 20, 30, 255]);
  const b = Buffer.from([10, 20, 30, 255]);
  const r = diffCore(a, b, 1, 1, { threshold: 10 });
  assert.strictEqual(r.diffCount, 0);
  assert.strictEqual(r.score, 1);
})();

// 9) zero-size
(() => {
  const r = diffCore(new Uint8ClampedArray(0), new Uint8ClampedArray(0), 0, 0, {});
  assert.strictEqual(r.total, 0);
  assert.strictEqual(r.score, 1);
  assert.strictEqual(r.diffCount, 0);
})();

// 10) mask absence when buildMask omitted
(() => {
  const a = fill(1, 1, [0, 0, 0]);
  const b = fill(1, 1, [0, 0, 0]);
  const r = diffCore(a, b, 1, 1, { threshold: 10 });
  assert.strictEqual(r.mask, undefined);
})();

console.log('diff-core: all tests passed');
