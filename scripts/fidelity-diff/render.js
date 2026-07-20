'use strict';
const fs = require('node:fs');

/** Resolve playwright-core from --pw arg, env, or normal require. */
function loadPlaywright(pwPath) {
  const candidates = [
    pwPath,
    process.env.PLAYWRIGHT_CORE,
    'playwright-core',
  ].filter(Boolean);
  for (const c of candidates) {
    try { return require(c); } catch (_) { /* next */ }
  }
  throw new Error('playwright-core not found. Pass --pw <path-to-playwright-core> (e.g. a frontend repo node_modules).');
}

/**
 * Launch a browser. Resolution order:
 *   1) if `cdp` is given, connect over CDP (Chrome DevTools Protocol) and use that
 *   2) otherwise try system Chrome (channel:'chrome', no CDN download)
 *   3) falling back to bundled chromium
 */
async function launchBrowser({ pwPath, cdp } = {}) {
  const { chromium } = loadPlaywright(pwPath);
  if (cdp) return { browser: await chromium.connectOverCDP(cdp), how: 'cdp' };
  try { return { browser: await chromium.launch({ headless: true, channel: 'chrome' }), how: 'chrome-channel' }; }
  catch (_) { /* fall through */ }
  return { browser: await chromium.launch({ headless: true }), how: 'bundled-chromium' };
}

/**
 * Render an HTML string (or file) to a PNG buffer at a fixed viewport.
 * If `opts.browser` is provided it is reused and NOT closed (the caller owns it);
 * otherwise a browser is launched via the ladder and closed here.
 */
async function renderHtmlToPng(htmlOrFile, { width = 1024, height = 768, pwPath, cdp, isFile = false, browser } = {}) {
  const html = isFile ? fs.readFileSync(htmlOrFile, 'utf8') : htmlOrFile;
  const shared = !!browser;
  let how = 'shared';
  if (!shared) ({ browser, how } = await launchBrowser({ pwPath, cdp }));
  try {
    const page = await browser.newPage({ viewport: { width, height } });
    await page.setContent(html, { waitUntil: 'networkidle' });
    const buf = await page.screenshot({ type: 'png' });
    return { png: buf, how };
  } finally { if (!shared) await browser.close(); }
}

module.exports = { loadPlaywright, launchBrowser, renderHtmlToPng };
