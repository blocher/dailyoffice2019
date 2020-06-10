let initialized = false;
const queue = [];
const Redirector = require("./lib/redirects.js");
Redirector.onRuntimeInitialized = () => {
  initialized = true;
  queue.forEach(cb => cb.call());
};

function newParser(options) {
  if (initialized) {
    return Promise.resolve(new Redirector.RedirectParser(options));
  }
  return new Promise((resolve, reject) => {
    queue.push(() => resolve(new Redirector.RedirectParser(options)));
  });
}

module.exports = {
  parsePlain(rules, options) {
    return newParser(options).then(p => p.parsePlain(rules));
  },
  parseJSON(rules, options) {
    return newParser(options).then(p => p.parseJSON(rules));
  }
};
