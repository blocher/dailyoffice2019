// A tiny command relay for driving the app in a simulator or emulator.
//   node store/scripts/remote/remote.mjs            (listens on :9999)
//   curl -s localhost:9999/run --data-binary 'return location.href'
// The injected driver.js long-polls /next, runs the JavaScript, and posts
// the result to /done, which answers the waiting /run request.
import http from 'node:http';

const queue = [];
const waiting = new Map();
let pollers = [];
let nextId = 1;

function send(res, status, body) {
  res.writeHead(status, {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Content-Type': 'application/json',
  });
  res.end(JSON.stringify(body));
}

function dispatch() {
  while (queue.length && pollers.length) send(pollers.shift(), 200, queue.shift());
}

http
  .createServer((req, res) => {
    let body = '';
    req.on('data', (c) => (body += c));
    if (process.env.REMOTE_LOG) console.log(req.method, req.url);
    req.on('end', () => {
      if (req.method === 'OPTIONS') return send(res, 204, null);
      if (req.url === '/next') {
        pollers.push(res);
        res.on('close', () => (pollers = pollers.filter((p) => p !== res)));
        setTimeout(() => {
          if (pollers.includes(res)) {
            pollers = pollers.filter((p) => p !== res);
            send(res, 200, {});
          }
        }, 25000);
        return dispatch();
      }
      if (req.url === '/done') {
        const { id, result } = JSON.parse(body || '{}');
        const w = waiting.get(id);
        if (w) {
          clearTimeout(w.timer);
          waiting.delete(id);
          send(w.res, 200, { result });
        }
        return send(res, 200, {});
      }
      if (req.url === '/run') {
        const id = nextId++;
        const timer = setTimeout(() => {
          waiting.delete(id);
          send(res, 504, { error: 'timeout: is the app running with driver.js?' });
        }, 60000);
        waiting.set(id, { res, timer });
        queue.push({ id, js: body });
        return dispatch();
      }
      if (req.url === '/status') return send(res, 200, { pollers: pollers.length, queued: queue.length });
      send(res, 404, {});
    });
  })
  .listen(9999, () => console.log('remote listening on :9999'));
