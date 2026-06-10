import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";

const root = "D:/React_python_Mysql";
const assetsDir = path.join(root, "docs", "assets");
const baseUrl = "http://127.0.0.1:5173";
const chromePath = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const userDataDir = "C:/tmp/react-python-mysql-doc-chrome";
const debugPort = 9333;

await fs.mkdir(assetsDir, { recursive: true });

const chrome = spawn(chromePath, [
  "--headless=new",
  `--remote-debugging-port=${debugPort}`,
  `--user-data-dir=${userDataDir}`,
  "--window-size=1440,900",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
  "about:blank",
], {
  stdio: "ignore",
  windowsHide: true,
});

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getJson(url, retries = 40) {
  for (let index = 0; index < retries; index += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) return await response.json();
    } catch {
      await sleep(250);
    }
  }
  throw new Error(`Unable to fetch ${url}`);
}

class Cdp {
  constructor(socketUrl) {
    this.id = 0;
    this.pending = new Map();
    this.events = [];
    this.socket = new WebSocket(socketUrl);
  }

  async open() {
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", reject, { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) reject(new Error(JSON.stringify(message.error)));
        else resolve(message.result || {});
      } else if (message.method) {
        this.events.push(message);
      }
    });
  }

  send(method, params = {}) {
    const id = ++this.id;
    this.socket.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
  }

  async waitEvent(method, timeout = 10000) {
    const started = Date.now();
    while (Date.now() - started < timeout) {
      const index = this.events.findIndex((event) => event.method === method);
      if (index >= 0) return this.events.splice(index, 1)[0];
      await sleep(100);
    }
    throw new Error(`Timed out waiting for ${method}`);
  }

  close() {
    this.socket.close();
  }
}

async function main() {
  try {
    const tabs = await getJson(`http://127.0.0.1:${debugPort}/json`);
    const tab = tabs[0];
    const cdp = new Cdp(tab.webSocketDebuggerUrl);
    await cdp.open();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 900,
      deviceScaleFactor: 1,
      mobile: false,
    });

    async function navigate(url) {
      await cdp.send("Page.navigate", { url });
      await sleep(1800);
    }

    async function evaluate(expression) {
      return cdp.send("Runtime.evaluate", {
        expression,
        awaitPromise: true,
        userGesture: true,
      });
    }

    async function screenshot(name) {
      const result = await cdp.send("Page.captureScreenshot", {
        format: "png",
        fromSurface: true,
      });
      const file = path.join(assetsDir, name);
      await fs.writeFile(file, Buffer.from(result.data, "base64"));
      return file;
    }

    await navigate(`${baseUrl}/accessories`);
    await evaluate(`
      (() => {
        const input = Array.from(document.querySelectorAll('input'))
          .find((el) => el.placeholder && el.placeholder.includes('搜索配件'));
        if (input) {
          const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
          setter.call(input, 'Intel');
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
      })()
    `);
    await sleep(700);
    const productShot = await screenshot("06-01-product-query.png");

    await navigate(`${baseUrl}/purchases`);
    await evaluate(`
      (() => {
        const button = Array.from(document.querySelectorAll('button'))
          .find((el) => el.textContent.includes('新建采购单'));
        if (!button) throw new Error('新建采购单按钮不存在');
        button.click();
      })()
    `);
    await sleep(800);
    const purchaseCreateShot = await screenshot("06-02-purchase-create.png");

    await navigate(`${baseUrl}/purchases`);
    await evaluate(`
      (() => {
        const row = Array.from(document.querySelectorAll('tr'))
          .find((el) => el.textContent.includes('PO20260609001'));
        if (!row) throw new Error('采购演示单不存在');
        const button = Array.from(row.querySelectorAll('button'))
          .find((el) => el.textContent.includes('查看'));
        if (!button) throw new Error('采购查看按钮不存在');
        button.click();
      })()
    `);
    await sleep(900);
    const purchaseDetailShot = await screenshot("06-03-purchase-detail.png");

    await navigate(`${baseUrl}/sales`);
    await evaluate(`
      (() => {
        const button = Array.from(document.querySelectorAll('button'))
          .find((el) => el.textContent.includes('新建销售单'));
        if (!button) throw new Error('新建销售单按钮不存在');
        button.click();
      })()
    `);
    await sleep(800);
    const salesCreateShot = await screenshot("06-04-sales-create.png");

    await navigate(`${baseUrl}/sales`);
    await evaluate(`
      (() => {
        const row = Array.from(document.querySelectorAll('tr'))
          .find((el) => el.textContent.includes('SO20260609001'));
        if (!row) throw new Error('销售演示单不存在');
        const button = Array.from(row.querySelectorAll('button'))
          .find((el) => el.textContent.includes('查看'));
        if (!button) throw new Error('销售查看按钮不存在');
        button.click();
      })()
    `);
    await sleep(900);
    const salesDetailShot = await screenshot("06-05-sales-detail.png");

    cdp.close();
    console.log(JSON.stringify({
      screenshots: [
        productShot,
        purchaseCreateShot,
        purchaseDetailShot,
        salesCreateShot,
        salesDetailShot,
      ],
    }, null, 2));
  } finally {
    chrome.kill();
  }
}

await main();
