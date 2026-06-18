'use strict';

function createMockUniCloud(seed) {
  const state = clone(seed);
  return {
    database() {
      return createDatabase(state);
    }
  };
}

function createDatabase(state) {
  const command = {
    in(values) {
      return { $in: values };
    }
  };
  return {
    command,
    collection(name) {
      if (!state[name]) state[name] = [];
      return new Query(state, name, state[name].slice());
    }
  };
}

class Query {
  constructor(state, name, rows) {
    this.state = state;
    this.name = name;
    this.rows = rows;
  }

  where(criteria) {
    this.rows = this.rows.filter((row) => matches(row, criteria));
    return this;
  }

  orderBy(field, direction) {
    const factor = direction === 'desc' ? -1 : 1;
    this.rows.sort((left, right) => compare(left[field], right[field]) * factor);
    return this;
  }

  limit(count) {
    this.rows = this.rows.slice(0, count);
    return this;
  }

  async get() {
    return { data: clone(this.rows) };
  }

  async add(docs) {
    const list = Array.isArray(docs) ? docs : [docs];
    this.state[this.name].push(...clone(list));
    return { ids: list.map((_, index) => `${this.name}_${index}`) };
  }
}

function matches(row, criteria) {
  for (const [key, expected] of Object.entries(criteria || {})) {
    if (expected && typeof expected === 'object' && Array.isArray(expected.$in)) {
      if (!expected.$in.includes(row[key])) return false;
    } else if (row[key] !== expected) {
      return false;
    }
  }
  return true;
}

function compare(left, right) {
  if (left === right) return 0;
  if (left === undefined || left === null) return -1;
  if (right === undefined || right === null) return 1;
  return left > right ? 1 : -1;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

module.exports = { createMockUniCloud };
