// Check a nexpatch page: run its own script (without the DOM part) on a .z80, compare every version with
// its .nex, check an option, and make sure a changed .z80 is refused.
// Usage: node test_page.js PAGE.html GAME.z80 VERSION1.nex [VERSION2.nex ...] [--option K VERSION_N WITH.nex]
const fs = require('fs');
const args = process.argv.slice(2), page = args[0], z80p = args[1];
const oi = args.indexOf('--option'), nexes = args.slice(2, oi < 0 ? undefined : oi);
const html = fs.readFileSync(page, 'utf8');
let js = html.split('<script>')[1].split('// ---- the page ----')[0];
js += '\nmodule.exports = { applyPatch, DATA, nexName };';
const m = new module.constructor(); m._compile(js, 'page.js');
const { applyPatch, DATA, nexName } = m.exports;
const z80 = new Uint8Array(fs.readFileSync(z80p)), b64 = s => Uint8Array.from(Buffer.from(s, 'base64'));
DATA.variants.forEach((v, i) => {
  const t0 = Date.now(), out = applyPatch(z80, b64(v.patch));
  const same = nexes[i] ? Buffer.compare(Buffer.from(out), fs.readFileSync(nexes[i])) === 0 : 'no .nex given';
  console.log('version', i, v.label, out.length, 'bytes in', Date.now() - t0, 'ms; identical:', same);
});
if (oi >= 0) {
  const k = +args[oi + 1], vi = +args[oi + 2], want = fs.readFileSync(args[oi + 3]);
  const out = applyPatch(z80, b64(DATA.variants[vi].patch));
  for (const [off, bytes] of DATA.options[k].edits) out.set(bytes, off);
  console.log('option', k, DATA.options[k].label, 'on version', vi, 'identical:', Buffer.compare(Buffer.from(out), want) === 0);
}
console.log('name:', nexName(require('path').basename(z80p)));
const bad = z80.slice(); bad[100] ^= 1;
try { applyPatch(bad, b64(DATA.variants[0].patch)); console.log('WRONG: changed file accepted'); }
catch (e) { console.log('changed file refused:', e.message); }
