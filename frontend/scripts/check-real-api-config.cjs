const fs = require('node:fs')
const path = require('node:path')

const envExample = fs.readFileSync(path.resolve('.env.example'), 'utf8')
const apiSource = fs.readFileSync(path.resolve('src/api/index.ts'), 'utf8')

const expected = {
  VITE_API_FN_LIST: 'lof-list',
  VITE_API_FN_DETAIL: 'lof-detail',
  VITE_API_FN_HISTORY: 'lof-history',
  VITE_API_FN_INGEST: 'lof-ingest'
}

const missing = []
for (const [key, value] of Object.entries(expected)) {
  if (!envExample.includes(`${key}=${value}`)) missing.push(`${key}=${value}`)
  if (!apiSource.includes(key)) missing.push(`api uses ${key}`)
}

for (const fnName of ['getLofList', 'getLofDetail', 'getLofHistory']) {
  if (!apiSource.includes(`export async function ${fnName}`)) missing.push(fnName)
}

if (missing.length) {
  console.error('真实 API 配置检查失败：')
  for (const item of missing) console.error(`- ${item}`)
  process.exit(1)
}

console.log('真实 API 配置检查通过：默认函数名映射到 lof-list / lof-detail / lof-history / lof-ingest')
