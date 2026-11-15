"""Runs a built dashboard page outside claude.ai: one HTML file with the page's parts joined, the data files inlined,
d3 from tests/vendor and a small stand-in for the Dashboard runtime (datasets, calcs, drawings, params, a store).
test_page_browser.py opens it in Chromium to check the page works and fits; render_page.py screenshots it, with the
Dashboard type's real stylesheet when given one. The colours and sizes here (TOKENS) are plain values for the tokens
the type guarantees, and carry none of its resets."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import dashboard_build as db  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
D3 = os.path.join(HERE, "vendor", "d3.min.js")

# the tokens the Dashboard type guarantees (its reference/design-defaults.md), with plain values
TOKENS = """
:root { --color-fg:#141413; --color-fg-muted:#6f6e69; --color-bg:#faf9f5; --color-panel:#fff; --color-border-line:#e5e3da;
  --color-ok:#2f7d32; --color-warn:#b26a00; --color-bad:#b3261e; --font-anthropic-sans:system-ui,sans-serif;
  --font-anthropic-serif:Georgia,serif; --cds-font-size-caption:.75rem; --cds-font-size-body:.875rem;
  --cds-font-size-heading:.9375rem; --cds-font-size-title:1.375rem; --cds-font-weight-medium:500;
  --cds-gap-xs:.25rem; --cds-gap-sm:.5rem; --cds-gap-md:.75rem; --cds-gap-lg:1rem; --cds-gap-xl:2rem;
  --cds-pad-xs:.25rem; --cds-pad-sm:.5rem; --cds-pad-md:.75rem; --cds-pad-lg:1rem; --cds-pad-xl:1.5rem; --cds-radius:.5rem;
  --cds-chart-muted:#d1cfc5; --cds-chart-reference:#9c9a92; --cds-chart-grid:#0000000f; --cds-surface-popover:#fff;
  --cds-border:#00000014; --cds-shadow-popover:0 8px 24px #0000001f; --cds-text-secondary:#5e5d59; --cds-dur-slow:.45s;
  --cds-ease-out:ease-out; }
body { margin:0; background:var(--color-bg); }
#dash-root { color:var(--color-fg); font:14px/1.45 var(--font-anthropic-sans); padding:1rem; }
.dash-select { font:inherit; font-size:.8125rem; padding:.35em 2em .35em .75em; border:1px solid var(--color-border-line);
  border-radius:var(--cds-radius); background-color:var(--color-panel); max-width:100%; }
"""

# enough of the Dashboard runtime to run the page: datasets, calcs, drawings (not under `hidden`), params, a store
RUNTIME = r"""
const datasets = {};
function parseCSV(text){const rows=[];let row=[],cell='',q=false;for(let i=0;i<text.length;i++){const ch=text[i];
  if(q){if(ch==='"'&&text[i+1]==='"'){cell+='"';i++;}else if(ch==='"')q=false;else cell+=ch;}
  else if(ch==='"')q=true;else if(ch===','){row.push(cell);cell='';}
  else if(ch==='\n'||ch==='\r'){if(ch==='\r'&&text[i+1]==='\n')i++;row.push(cell);rows.push(row);row=[];cell='';}
  else cell+=ch;}
  if(cell||row.length){row.push(cell);rows.push(row);}
  const [head,...body]=rows.filter(r=>r.length>1||r[0]!=='');
  return body.map(r=>Object.fromEntries(head.map((h,i)=>[h,r[i]===''||r[i]==null?null:r[i]])));}
for (const [id, d] of Object.entries(RAW)) {
  datasets[id] = d.format === 'json' ? JSON.parse(d.text) : parseCSV(d.text);
  if (d.format === 'json') datasets[id].forEach(r => Object.keys(r).forEach(k => { if (Array.isArray(r[k])) r[k] = JSON.stringify(r[k]); }));
}
const draws = new Map(), calcs = new Map(), onDatas = [], cache = new Map();
let params = {};
window.__errors = [];
window.addEventListener('error', e => window.__errors.push(String(e.message)));
const runDraw = (name) => { const fn = draws.get(name); if (!fn) return;
  document.querySelectorAll('[data-draw="' + name + '"]').forEach(el => { if (el.closest('[hidden]')) return;
    try { (typeof fn === 'function' ? fn : fn.update)(el); } catch (e) { window.__errors.push(name + ': ' + e.message); } }); };
window.dash = {
  colors: ['#3b78d8', '#8e5bd0', '#2f9e8f', '#e69f00', '#c2410c', '#0e8a16', '#b3261e', '#6b7280'],
  data(id) {
    if (calcs.has(id)) {
      if (!cache.has(id)) { const c = calcs.get(id);
        try { cache.set(id, c.fn(...c.inputs.map(i => dash.data(i).data))); }
        catch (e) { window.__errors.push('calc ' + id + ': ' + e.message); return { status: 'error', data: null }; } }
      return { status: 'ok', data: cache.get(id) };
    }
    return id in datasets ? { status: 'ok', data: datasets[id], columns: Object.keys(datasets[id][0] || {}) } : { status: 'missing', data: [] };
  },
  calc(id, o) { calcs.set(id, o); }, loader() {},
  draw(name, fn) { if (fn) { draws.set(name, fn); return; } runDraw(name); },
  onData(fn) { onDatas.push(fn); }, setLink() {}, params: () => ({ ...params }),
  setParams(p) { Object.assign(params, p); }, resetParams() { params = {}; }, refresh() {},
};
window.__drawAll = () => { onDatas.forEach(f => { try { f(); } catch (e) { window.__errors.push('onData: ' + e.message); } }); [...draws.keys()].forEach(runDraw); };
const store = new Map(), listeners = [];
const snap = (c) => ({ docs: [...store].filter(([k]) => k.startsWith(c + '/')).map(([k, v]) => ({ id: k.slice(c.length + 1), data: () => v })) });
const fire = (p) => { listeners.filter(l => l.coll === p.split('/')[0]).forEach(l => l.cb(snap(l.coll)));
  listeners.filter(l => l.doc === p).forEach(l => l.cb({ exists: store.has(p), data: () => store.get(p) })); };
window.claude = { use: async (k) => k === 'db' ? {
  doc: (p) => ({ set: async (v) => { store.set(p, JSON.parse(JSON.stringify(v))); fire(p); }, delete: async () => { store.delete(p); fire(p); },
    onSnapshot: (cb) => { listeners.push({ doc: p, cb }); cb({ exists: store.has(p), data: () => store.get(p) }); } }),
  collection: (c) => ({ onSnapshot: (cb) => { listeners.push({ coll: c, cb }); cb(snap(c)); } }) } : null };
"""

AFTER = """
window.__drawAll();
new MutationObserver((ms) => { if (ms.some((m) => m.target.classList.contains('sp-panel'))) window.__drawAll(); })
  .observe(document.body, { subtree: true, attributes: true, attributeFilter: ['hidden'] });
let w = innerWidth; addEventListener('resize', () => { if (innerWidth !== w) { w = innerWidth; window.__drawAll(); } });
"""


def shim(bundle, target, css=None):
    """One HTML file that runs the built page: the page's parts joined, each script in a scope of its own, as the
    runtime runs them. `css` is the Dashboard type's own stylesheet (its text), used in place of the stand-in tokens:
    the page then looks as it does on claude.ai, resets and all."""
    with open(os.path.join(bundle, "manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    read = lambda f: open(os.path.join(bundle, f), encoding="utf-8").read()  # noqa: E731
    page = db.join_page({f["name"]: read(f["name"]) for f in man["files"]})
    page = re.sub(r"<script>(.*?)</script>", lambda m: "<script>{" + m.group(1) + "\n}</script>", page, flags=re.S)
    raw = json.dumps({d["id"]: {"format": d["format"], "text": read(d["file"])} for d in man["datasets"]}).replace("</", "<\\/")
    # the type styles `.cds-root` and mounts the page in #dash-root; its sheet sets the page's own background
    root = ' class="cds-root"' if css else ""
    style = css.replace("</style", "<\\/style") + "\nbody { margin: 0; background: var(--color-bg); }" if css else TOKENS
    html = (f'<!doctype html><html{root}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, '
            f'initial-scale=1"><style>{style}</style><script>{open(D3, encoding="utf-8").read()}</script>'
            f"<script>const RAW = {raw};{RUNTIME}</script></head><body{root}><div id=\"dash-root\">{page}</div>"
            f"<script>{AFTER}</script></body></html>")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(html)
    return target
