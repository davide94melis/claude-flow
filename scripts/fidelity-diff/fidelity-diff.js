#!/usr/bin/env node
'use strict';
/**
 * Usage:
 *   node fidelity-diff.js --snippet <file.html> --golden <golden.png> [options]
 *   node fidelity-diff.js --image <rendered.png> --golden <golden.png> [options]
 * Options:
 *   --width N --height N        viewport for --snippet render (default 1024x768)
 *   --threshold N               per-channel delta tolerance (default 12)
 *   --region x,y,w,h            crop the golden to this region before comparing
 *   --out <diff.png>            write a red-mask diff image
 *   --pw <path>                 path to a resolvable playwright-core
 *   --cdp <ws-endpoint>         connect over CDP instead of launching
 *   --json                      print only the JSON result
 * Exit code: 0 always (score is the signal); non-zero only on hard error.
 */
const fs = require('node:fs');
const { diffCore } = require('./diff-core.js');
const { renderHtmlToPng, launchBrowser } = require('./render.js');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return def;
  const v = process.argv[i + 1];
  return (v == null || v.startsWith('--')) ? true : v;
}

// Numeric flag guard: a valueless flag makes arg() return `true`, and Number(true)===1,
// which would silently corrupt numeric options. Fall back to `def` unless a real number was given.
function numArg(name, def) {
  const v = arg(name);
  const n = Number(v);
  return (v === true || v == null || Number.isNaN(n)) ? def : n;
}

// Decode two PNG buffers to RGBA (golden scaled to rendered size) IN-BROWSER via canvas.
// Returns { w, h, a, b } where a/b are plain arrays of RGBA bytes. Zero node image deps.
// If `browser` is provided it is reused and NOT closed; otherwise one is launched+closed here.
async function decodePair(renderedPng, goldenPng, { pwPath, cdp, region, browser }) {
  const shared = !!browser;
  if (!shared) ({ browser } = await launchBrowser({ pwPath, cdp }));
  try {
    const page = await browser.newPage();
    const res = await page.evaluate(async ({ rB64, gB64, region }) => {
      function load(b64) {
        return new Promise((resolve, reject) => {
          const img = new Image();
          img.onload = () => resolve(img);
          img.onerror = () => reject(new Error('failed to decode PNG'));
          img.src = 'data:image/png;base64,' + b64;
        });
      }
      const rImg = await load(rB64);
      const gImg = await load(gB64);
      const w = rImg.naturalWidth, h = rImg.naturalHeight;
      const cr = document.createElement('canvas'); cr.width = w; cr.height = h;
      const ctxR = cr.getContext('2d'); ctxR.drawImage(rImg, 0, 0);
      const cg = document.createElement('canvas'); cg.width = w; cg.height = h;
      const ctxG = cg.getContext('2d');
      if (region) {
        const [x, y, rw, rh] = region;
        ctxG.drawImage(gImg, x, y, rw, rh, 0, 0, w, h);   // crop + scale golden to rendered size
      } else {
        ctxG.drawImage(gImg, 0, 0, gImg.naturalWidth, gImg.naturalHeight, 0, 0, w, h);
      }
      // Marshalling RGBA as a plain array across the CDP bridge is fine for small component
      // regions; it does NOT scale to full-page/high-DPI screenshots (multi-MB payloads).
      return {
        w, h,
        a: Array.from(ctxR.getImageData(0, 0, w, h).data),
        b: Array.from(ctxG.getImageData(0, 0, w, h).data),
      };
    }, {
      rB64: renderedPng.toString('base64'),
      gB64: goldenPng.toString('base64'),
      region: region || null,
    });
    return res;
  } finally { if (!shared) await browser.close(); }
}

// Encode an RGBA mask array to PNG (in-browser via canvas), return Buffer.
// If `browser` is provided it is reused and NOT closed; otherwise one is launched+closed here.
async function encodeMask(mask, w, h, { pwPath, cdp, browser }) {
  const shared = !!browser;
  if (!shared) ({ browser } = await launchBrowser({ pwPath, cdp }));
  try {
    const page = await browser.newPage();
    const dataUrl = await page.evaluate(({ mask, w, h }) => {
      const c = document.createElement('canvas'); c.width = w; c.height = h;
      const ctx = c.getContext('2d');
      const id = ctx.createImageData(w, h);
      id.data.set(mask);
      ctx.putImageData(id, 0, 0);
      return c.toDataURL('image/png');
    }, { mask: Array.from(mask), w, h });
    return Buffer.from(dataUrl.split(',')[1], 'base64');
  } finally { if (!shared) await browser.close(); }
}

(async () => {
  const pwPath = arg('pw');
  const cdp = arg('cdp');
  const threshold = numArg('threshold', 12);
  const width = numArg('width', 1024);
  const height = numArg('height', 768);
  const goldenPath = arg('golden');
  const snippet = arg('snippet');
  const image = arg('image');
  const outPath = arg('out');
  const regionRaw = arg('region');
  const region = typeof regionRaw === 'string' ? regionRaw.split(',').map(Number) : null;
  const jsonOnly = arg('json') === true;

  if (!goldenPath || (!snippet && !image)) {
    console.error('Usage: fidelity-diff.js (--snippet <html> | --image <png>) --golden <png> [--pw <path>] [--region x,y,w,h] [--out diff.png]');
    process.exit(2);
  }

  if (region && !(region.length === 4 && region.every(Number.isFinite))) {
    console.error('Invalid --region: expected x,y,w,h (4 numbers)');
    process.exit(2);
  }

  const goldenPng = fs.readFileSync(goldenPath);

  // One browser per invocation, shared across render/decode/encode and closed exactly once.
  const { browser } = await launchBrowser({ pwPath, cdp });
  try {
    let renderedPng;
    if (image) renderedPng = fs.readFileSync(image);
    else renderedPng = (await renderHtmlToPng(snippet, { width, height, pwPath, cdp, isFile: true, browser })).png;

    const { w, h, a, b } = await decodePair(renderedPng, goldenPng, { pwPath, cdp, region, browser });
    const r = diffCore(a, b, w, h, { threshold, buildMask: !!outPath });
    if (outPath && r.mask) fs.writeFileSync(outPath, await encodeMask(r.mask, w, h, { pwPath, cdp, browser }));

    const result = { score: Number(r.score.toFixed(4)), diffCount: r.diffCount, total: r.total, width: w, height: h, threshold };
    if (jsonOnly) console.log(JSON.stringify(result));
    else console.log(`fidelity: ${(result.score*100).toFixed(2)}%  (${r.diffCount}/${r.total} px differ, thr=${threshold})` + (outPath ? `  diff -> ${outPath}` : ''));
  } finally { await browser.close(); }
})().catch(e => { console.error('fidelity-diff error:', e.message); process.exit(1); });
