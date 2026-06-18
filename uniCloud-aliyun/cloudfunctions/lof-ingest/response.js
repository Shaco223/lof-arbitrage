'use strict';

function ok(data = {}) {
  return { code: 0, message: 'ok', data };
}

function fail(code, message, data = {}) {
  return { code, message, data };
}

module.exports = { ok, fail };
