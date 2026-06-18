'use strict';

function ok(data = {}) {
  return { code: 0, message: 'ok', data };
}

function fail(code, message, data = {}) {
  return { code, message, data };
}

function normalizeQuery(event) {
  if (!event) return {};
  return event.queryStringParameters || event.query || event;
}

module.exports = { ok, fail, normalizeQuery };
