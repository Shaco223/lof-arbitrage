'use strict';

function ok(data = {}) {
  return { code: 0, message: 'ok', data };
}

function fail(code, message, data = {}) {
  return { code, message, data };
}

function normalizeQuery(event) {
  if (!event) return {};
  if (event.queryStringParameters) return event.queryStringParameters;
  if (event.query) return event.query;
  if (event.rawQueryString) return parseQueryString(event.rawQueryString);
  if (event.body) return parseBody(event.body);
  return event;
}

function parseQueryString(rawQueryString) {
  const params = {};
  for (const [key, value] of new URLSearchParams(rawQueryString)) {
    params[key] = value;
  }
  return params;
}

function parseBody(body) {
  if (typeof body !== 'string') return body;
  try { return JSON.parse(body); } catch (error) { return {}; }
}

module.exports = { ok, fail, normalizeQuery };
