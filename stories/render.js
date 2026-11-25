// Gera os PNGs 1080x1920 dos stories: node stories/render.js
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const src = 'file://' + path.join(__dirname, 'src', 'stories.html');
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 2000 }, deviceScaleFactor: 1 });
  await p.goto(src, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const ids = await p.$$eval('.story', els => els.map(e => e.id));
  for (const id of ids) {
    const el = await p.$('#' + id);
    const out = path.join(__dirname, `ableton-express-story-${id.slice(1)}.png`);
    await el.screenshot({ path: out });
    console.log(out);
  }
  await b.close();
})();
