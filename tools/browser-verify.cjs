/* Read-only research and offline Edge QA. Fresh contexts, no personal profiles. */
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const root = path.resolve(__dirname, '..');
const playwright = process.env.ACA_PLAYWRIGHT_PATH || 'playwright';
const { chromium } = require(playwright);
const allowed = new Set([
  'github.com', 'docs.github.com', 'pypi.org', 'docs.unity3d.com',
  'modelcontextprotocol.io', 'code.visualstudio.com', 'packaging.python.org',
]);

async function main() {
  fs.mkdirSync(path.join(root, 'research'), { recursive: true });
  const browser = await chromium.launch({channel: 'msedge', headless: true, chromiumSandbox: true});
  try {
    const context = await browser.newContext({acceptDownloads: false, permissions: [], viewport: {width: 1440, height: 1080}, serviceWorkers: 'block'});
    const blocked = new Set();
    await context.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.protocol === 'file:' || (url.protocol === 'https:' && allowed.has(url.hostname))) return route.continue();
      blocked.add(url.hostname);
      return route.abort();
    });
    const page = await context.newPage();
    if (process.argv.includes('--research')) {
      const pages = [];
      for (const url of [
        'https://github.com/trending',
        'https://github.com/snyk/agent-scan',
        'https://pypi.org/project/check-wheel-contents/',
        'https://docs.unity3d.com/Manual/AssetDatabase.html',
      ]) {
        try {
          const response = await page.goto(url, {waitUntil: 'domcontentloaded', timeout: 20000});
          pages.push({url, status: response?.status(), title: await page.title()});
        } catch (error) { pages.push({url, error: error.message.split('\n')[0]}); }
      }
      fs.writeFileSync(path.join(root, 'research/research-pages.json'), JSON.stringify({browser: browser.version(), pages, blockedDomains: [...blocked].sort()}, null, 2));
      console.log(JSON.stringify(pages));
    } else {
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const files = ['risky', 'hardened', 'diff', 'xss'];
      const checks = [];
      for (const name of files) {
        await page.goto(pathToFileURL(path.join(root, `reports/${name}.html`)).href);
        await page.getByRole('heading', {name: 'Know what you’re about to run.'}).waitFor();
        const cardCount = await page.locator('article.finding').count();
        if (name === 'risky' && cardCount !== 8) throw new Error(`Expected 8 demo findings, got ${cardCount}`);
        if (name === 'hardened' && cardCount !== 0) throw new Error('Hardened fixture has findings');
        if (await page.locator('script, img, iframe').count()) throw new Error('Report contains active content');
        if (name === 'xss' && !await page.locator('body').innerText().then(text => text.includes('<script>'))) throw new Error('Escaped server label missing');
        const pageText = await page.locator('body').innerText();
        if (pageText.includes('synthetic-demo-token-not-a-real-secret') || pageText.includes('synthetic-demo-only')) throw new Error('Raw fixture credential leaked');
        await page.screenshot({path: path.join(root, `research/${name}-desktop.png`), fullPage: true});
        const headings = await page.locator('h1,h2,h3').allTextContents();
        fs.writeFileSync(path.join(root, `research/${name}-snapshot.txt`), headings.join('\n'));
        checks.push({name, width: 1440, cardCount, headings: headings.length});
      }
      await page.setViewportSize({width: 390, height: 844});
      await page.goto(pathToFileURL(path.join(root, 'reports/risky.html')).href);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (overflow) throw new Error('Horizontal overflow at mobile width');
      await page.screenshot({path: path.join(root, 'research/risky-mobile.png'), fullPage: true});
      if (errors.length) throw new Error(errors.join('\n'));
      fs.writeFileSync(path.join(root, 'research/verification.json'), JSON.stringify({browser: browser.version(), channel: 'msedge', chromiumSandbox: true, freshContext: true, errors, checks, mobileOverflow: overflow, blockedDomains: [...blocked]}, null, 2));
      console.log(JSON.stringify({browser: browser.version(), checks, mobileOverflow: overflow, errors}));
    }
    await context.close();
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
