// Screenshot driver: injected into local screenshot builds only (never shipped).
// Long-polls the Mac's remote.mjs server for JavaScript to run in the app.
(function () {
  const base = window.__REMOTE_BASE__ || 'http://localhost:9999';
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function loop() {
    for (;;) {
      try {
        const res = await fetch(`${base}/next`, { cache: 'no-store' });
        const cmd = await res.json();
        if (!cmd || !cmd.js) continue;
        let result;
        try {
          result = await (0, eval)(`(async () => { ${cmd.js} })()`);
        } catch (e) {
          result = `ERR ${e && e.message}`;
        }
        await fetch(`${base}/done`, {
          method: 'POST',
          body: JSON.stringify({ id: cmd.id, result: result === undefined ? null : result }),
        });
      } catch {
        await sleep(1000);
      }
    }
  }
  loop();
})();
