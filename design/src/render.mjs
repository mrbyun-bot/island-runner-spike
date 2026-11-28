// 목업을 2배 PNG 로 찍는다.
// 실행: NODE_PATH=<playwright 가 있는 node_modules> flock -w 900 /var/tmp/claude-browser.lock node design/src/render.mjs [이름...]
import { createRequire } from 'module';
import path from 'path';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.resolve(here, '../screens');
// [파일, 결과 이름, 테마, 폭, 높이]
const jobs = [
  ['home.html', 'home-dark', 'dark', 402, 874],
  ['home.html', 'home-light', 'light', 402, 874],
  ['characters.html', 'characters-dark', 'dark', 402, 874],
  ['characters.html', 'characters-light', 'light', 402, 874],
  ['pack-sheet.html', 'characters-pack-sheet-dark', 'dark', 402, 874],
  ['settings.html', 'settings-dark', 'dark', 402, 874],
  ['settings.html', 'settings-light', 'light', 402, 874],
  ['island.html', 'island-expanded', 'dark', 402, 874],
  ['lockscreen.html', 'lockscreen-live-activity', 'dark', 402, 874],
  ['island-specs.html', 'island-states-spec', 'dark', 900, 560],
  ['widgets.html', 'widgets-small-medium', 'dark', 900, 420],
];
const only = process.argv.slice(2);
const browser = await chromium.launch();
try {
  for (const [file, name, theme, w, h] of jobs) {
    if (only.length && !only.includes(name)) continue;
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await page.goto('file://' + path.join(here, file) + (theme === 'light' ? '?theme=light' : ''));
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(out, name + '.png') });
    await page.close();
    console.log('찍음', name);
  }
} finally {
  await browser.close();
}
