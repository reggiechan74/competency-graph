// A stand-in for the claude.ai Dashboard runtime, enough to run the competency-graph page in jsdom: datasets from a
// dashboard_build.py folder, dash.calc / dash.draw / dash.onData, and a store in memory. It also checks the type's
// one-writer rule: while scripts, onData or a drawing run, a write outside the drawing's own element may only set
// class, style, hidden, open, disabled, checked, selected, value, tabindex or aria-*.
//
//   node page_harness.js <bundle dir> <scenario.js>
// The scenario is a module exporting async (h) => {...}; h gives doc, window, click, select, type, drawAll, store,
// text, force (a data file's status), refreshed (the ids dash.refresh was asked for) and fail(). Prints JSON: {errors, violations, log}. Used by test_dashboard.py (skipped without jsdom).
const fs = require('fs');
const path = require('path');

function findJsdom() {
  const tries = [process.env.JSDOM_PATH, 'jsdom', path.join(process.env.HOME || '', '.npm-global/lib/node_modules/jsdom'),
    '/usr/lib/node_modules/jsdom', '/usr/local/lib/node_modules/jsdom'].filter(Boolean);
  for (const t of tries) { try { return require(t); } catch (e) { /* next */ } }
  return null;
}

function parseCSV(text) {
  const rows = []; let row = []; let cell = ''; let q = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (q) {
      if (ch === '"' && text[i + 1] === '"') { cell += '"'; i += 1; } else if (ch === '"') q = false; else cell += ch;
    } else if (ch === '"') q = true;
    else if (ch === ',') { row.push(cell); cell = ''; } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i += 1;
      row.push(cell); rows.push(row); row = []; cell = '';
    } else cell += ch;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows.filter((r) => r.length > 1 || r[0] !== '');
  return body.map((r) => Object.fromEntries(head.map((h, i) => [h, r[i] === '' || r[i] == null ? null : r[i]])));
}

async function main() {
  const jsdom = findJsdom();
  if (!jsdom) { console.log(JSON.stringify({ skip: 'jsdom not found' })); return; }
  const [dir, scenarioPath] = process.argv.slice(2);
  const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
  const datasets = {};
  manifest.datasets.forEach((d) => {
    const text = fs.readFileSync(path.join(dir, d.file), 'utf8');
    datasets[d.id] = d.format === 'json' ? JSON.parse(text) : parseCSV(text);
    // a list column reaches the page as JSON text, as the runtime gives it
    if (d.format === 'json') datasets[d.id].forEach((r) => Object.keys(r).forEach((k) => { if (Array.isArray(r[k])) r[k] = JSON.stringify(r[k]); }));
  });
  const errors = []; const violations = []; const log = [];
  const draws = new Map(); const calcs = new Map(); const onDatas = [];
  const forced = new Map(); const refreshed = [];   // a data file made to fail or load (h.force), and each dash.refresh
  const SKIP = new Set(['timelinechart', 'heat', 'fitchart']);   // d3 charts: the stub has no d3
  const ALLOWED = /^(class|style|hidden|open|disabled|checked|selected|value|tabindex|aria-.*)$/;
  let doc; let observer;
  const calcValue = (id) => {
    const c = calcs.get(id);
    const ins = c.inputs.map((i) => { const x = dash.data(i); return x.data; });
    return c.fn(...ins);
  };
  const audit = (where, el) => {
    if (!observer) return;
    observer.takeRecords().forEach((m) => {
      const t = m.target;
      const inside = el && (t === el || el.contains(t));
      if (m.type === 'attributes' && ALLOWED.test(m.attributeName)) return;
      if (inside) return;
      // a handler a drawing set up may write inside that drawing's element ("Inside a drawing your code may write
      // from a handler"); the runtime checks only writes made while scripts, onData and drawings run
      if (!el && (t.nodeType === 1 ? t : t.parentElement) && (t.nodeType === 1 ? t : t.parentElement).closest('[data-draw]')) return;
      violations.push(`${where}: ${m.type}${m.attributeName ? ' ' + m.attributeName : ''} on <${t.nodeName ? t.nodeName.toLowerCase() : '?'}${t.id ? ' #' + t.id : ''}>`);
    });
  };
  const runDraw = (name) => {
    const fn = draws.get(name);
    if (!fn || SKIP.has(name)) return;
    doc.querySelectorAll(`[data-draw="${name}"]`).forEach((el) => {
      if (el.closest('[hidden]')) return;
      audit('before ' + name, null);
      try { (typeof fn === 'function' ? fn : fn.update)(el); } catch (e) { errors.push(`${name}: ${e.stack.split('\n').slice(0, 3).join(' | ')}`); }
      audit('draw ' + name, el);
    });
  };
  const dash = {
    colors: ['#111', '#222', '#333', '#444', '#555', '#666', '#777', '#888'],
    data(id) {
      if (calcs.has(id)) { try { return { status: 'ok', data: calcValue(id) }; } catch (e) { errors.push(`calc ${id}: ${e.stack.split('\n')[0]}`); return { status: 'error', data: null }; } }
      if (forced.has(id)) return { status: forced.get(id), data: [] };
      if (id in datasets) return { status: 'ok', data: datasets[id], columns: Object.keys(datasets[id][0] || {}) };
      return { status: 'missing', data: [] };
    },
    calc(id, o) { calcs.set(id, o); },
    loader() {},
    draw(name, fn) { if (fn) { draws.set(name, fn); return; } runDraw(name); },
    onData(fn) { onDatas.push(fn); },
    setLink() {}, params: () => ({}), setParams() {}, resetParams() {}, refresh(id) { refreshed.push(id); },
  };
  const d3 = { utcFormat: () => (d) => d.toISOString().slice(0, 10), format: () => (v) => String(v), utcYear: { offset: (d) => d },
    sum: (a, f) => a.reduce((n, x) => n + (Number(f ? f(x) : x) || 0), 0), max: (a, f) => Math.max(...a.map((x) => Number(f ? f(x) : x))) };
  const store = new Map(); const listeners = [];
  const snap = (coll) => ({ docs: [...store].filter(([k]) => k.startsWith(coll + '/')).map(([k, v]) => ({ id: k.slice(coll.length + 1), data: () => v })) });
  const fire = (coll) => listeners.filter((l) => l.coll === coll).forEach((l) => l.cb(snap(coll)));
  const db = {
    doc: (p) => ({
      set: async (v) => { store.set(p, JSON.parse(JSON.stringify(v))); fire(p.split('/')[0]); },
      delete: async () => { store.delete(p); fire(p.split('/')[0]); },
      onSnapshot: (cb) => { cb({ exists: store.has(p), data: () => store.get(p) }); },
    }),
    collection: (c) => ({ onSnapshot: (cb) => { listeners.push({ coll: c, cb }); cb(snap(c)); } }),
  };
  // the page in one piece: each file index.html loads (its stylesheet, its scripts) back in its place
  const read = (f) => fs.readFileSync(path.join(dir, f), 'utf8');
  const page = read(manifest.page)
    .replace(/<link rel="stylesheet" href="([\w.-]+)">/g, (m, f) => `<style>\n${read(f)}</style>`)
    .replace(/<script src="([\w.-]+)"><\/script>/g, (m, f) => `<script>\n${read(f)}</script>`);
  const dom = new jsdom.JSDOM(`<!doctype html><html><body><div id="dash-root">${page}</div></body></html>`, {
    runScripts: 'dangerously', pretendToBeVisual: true,
    beforeParse(w) {
      w.dash = dash; w.d3 = d3;
      w.Element.prototype.scrollIntoView = function scrollIntoView() {};
      w.claude = { use: async (k) => (k === 'db' ? db : null) };
      w.console.error = (...a) => errors.push('console: ' + a.join(' '));
      w.addEventListener('error', (e) => errors.push('window: ' + (e.error ? e.error.stack.split('\n')[0] : e.message)));
    },
  });
  const w = dom.window; doc = w.document;
  observer = new w.MutationObserver(() => {});
  observer.observe(doc.body, { subtree: true, childList: true, attributes: true, characterData: true });
  audit('scripts', null);
  const tick = () => new Promise((r) => setTimeout(r, 0));
  await tick(); await tick();
  const drawAll = () => { onDatas.forEach((f) => { try { f(); } catch (e) { errors.push('onData: ' + e.message); } audit('onData', null); }); [...draws.keys()].forEach(runDraw); };
  drawAll();
  const h = {
    doc, window: w, store, log: (x) => log.push(x), drawAll, tick, refreshed,
    force: (id, status) => { if (status) forced.set(id, status); else forced.delete(id); },   // 'error', 'loading', or none
    fail: (m) => errors.push('scenario: ' + m),
    click: async (sel) => { const el = doc.querySelector(sel); if (!el) { h.fail('no ' + sel); return; } el.click(); audit('click ' + sel, null); await tick(); await tick(); },
    select: async (el, v) => { el.value = v; el.dispatchEvent(new w.Event('change', { bubbles: true })); audit('change', null); await tick(); },
    type: async (sel, v) => { const el = doc.querySelector(sel); el.value = v; el.dispatchEvent(new w.Event('input', { bubbles: true })); audit('input ' + sel, null); await tick(); },
    text: (sel) => [...doc.querySelectorAll(sel)].map((e) => e.textContent.replace(/\s+/g, ' ').trim()),
    openTab: async (id) => { await h.click(`#tab-${id}`); drawAll(); },
  };
  try { await require(path.resolve(scenarioPath))(h); } catch (e) { errors.push('scenario threw: ' + e.stack.split('\n').slice(0, 3).join(' | ')); }
  console.log(JSON.stringify({ errors, violations: [...new Set(violations)], log }, null, 1));
}
main();
