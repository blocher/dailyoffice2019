// Plain-HTTP front for the local Django API (self-signed HTTPS on :8006), which
// the in-app preview browser refuses. Used by the "app-local-api" launch config.
const http = require('http'), https = require('https');
http.createServer((req, res) => {
  const up = https.request({ host: '127.0.0.1', port: 8006, path: req.url, method: req.method,
    headers: { ...req.headers, host: '127.0.0.1:8006' }, rejectUnauthorized: false }, (r) => {
    res.writeHead(r.statusCode, r.headers); r.pipe(res);
  });
  up.on('error', (e) => { res.writeHead(502); res.end(String(e)); });
  req.pipe(up);
}).listen(8017);
