#!/usr/bin/env node
'use strict';
/**
 * Capture a screenshot from a running URL/POC using the verified ladder.
 * Usage: node screenshot.js --url <url> --out <png> [--width N --height N --full]
 *        [--pw <playwright-core path>] [--cdp <endpoint>] [--storage <state.json>]
 */
const fs = require('node:fs');
const { launchBrowser } = require('./render.js');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return def;
  const v = process.argv[i + 1];
  return (v == null || v.startsWith('--')) ? true : v;
}

(async () => {
  const url = arg('url');
  const out = arg('out');
  if (!url || !out) { console.error('Usage: screenshot.js --url <url> --out <png> [--width --height --full --pw --cdp --storage]'); process.exit(2); }
  const width = Number(arg('width', 1440));
  const height = Number(arg('height', 900));
  const fullPage = arg('full') === true;
  const pwPath = arg('pw');
  const cdp = arg('cdp');
  const storage = arg('storage');

  const { browser, how } = await launchBrowser({ pwPath, cdp });
  try {
    const ctx = await browser.newContext({
      viewport: { width, height },
      ...(typeof storage === 'string' ? { storageState: storage } : {}),
    });
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.screenshot({ path: out, fullPage });
    console.log(`captured ${url} via ${how} -> ${out}`);
  } finally { await browser.close(); }
})().catch(e => { console.error('screenshot error:', e.message); process.exit(1); });
