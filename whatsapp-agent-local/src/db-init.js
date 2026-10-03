import { pool, ensureSchema } from './db.js';

await ensureSchema();
console.log('Esquema aplicado en la base de datos local.');
await pool.end();
