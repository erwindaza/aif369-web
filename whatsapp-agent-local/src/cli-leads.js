import { pool, ensureSchema, query, listLeads, listOpportunities } from './db.js';

const fmt = (row) => {
  const when = new Date(row.created_at).toLocaleString('es-CL', { timeZone: 'America/Santiago' });
  const body = (row.body || '[sin texto]').replace(/\s+/g, ' ').slice(0, 90);
  return `${when}  ${row.direction === 'out' ? 'AGENTE' : 'CLIENTE'} ${body}`;
};

const [, , command = 'leads'] = process.argv;

await ensureSchema();

if (command === 'leads') {
  const leads = await listLeads({ limit: 40 });
  console.log(`\n=== LEADS (${leads.length}) ===`);
  for (const l of leads) {
    const q = l.qualification || {};
    console.log(
      `${l.phone}  ${(l.push_name || l.display_name || '-').padEnd(16)} ` +
        `status=${(l.lead_status || 'NEW').padEnd(14)} score=${String(l.lead_score ?? '-').padStart(3)} ` +
        `intent=${(l.last_intent || '-').padEnd(16)} handoff=${l.human_handoff ? 'SI' : 'no'} ` +
        `optout=${l.opted_out ? 'SI' : 'no'}`
    );
    if (Object.keys(q).length) console.log(`    calificacion: ${JSON.stringify(q)}`);
    if (l.summary) console.log(`    resumen: ${l.summary}`);
  }

  const opps = await listOpportunities({ limit: 40 });
  console.log(`\n=== OPORTUNIDADES (${opps.length}) ===`);
  for (const o of opps) {
    const when = new Date(o.updated_at).toLocaleString('es-CL', { timeZone: 'America/Santiago' });
    console.log(
      `${when}  stage=${(o.stage || '-').padEnd(10)} score=${String(o.lead_score ?? '-').padStart(3)} ` +
        `${(o.service_label || o.service_key || '-').padEnd(26)} intent=${o.intent || '-'} ${o.human_handoff ? '[HUMAN]' : ''}`
    );
  }

  const { rows: handoffs } = await query(
    `SELECT phone, push_name, lead_status, summary FROM contacts WHERE human_handoff = TRUE ORDER BY last_seen DESC`
  );
  console.log(`\n=== PENDIENTES DE ASESOR HUMANO (${handoffs.length}) ===`);
  for (const h of handoffs) console.log(`${h.phone}  ${h.push_name || '-'}  ${h.lead_status}`);

  const { rows: stats } = await query(
    `SELECT count(*)::int AS chats, sum(message_count)::int AS msgs,
            count(*) FILTER (WHERE lead_status <> 'NEW')::int AS leads
     FROM contacts`
  );
  const { rows: lat } = await query(
    `SELECT count(*)::int AS n,
            round(avg(total_ms)) AS avg_total,
            round(percentile_cont(0.5) WITHIN GROUP (ORDER BY total_ms)) AS p50,
            round(max(total_ms)) AS max_total,
            round(avg(llm_ms)) AS avg_llm,
            round(avg(retrieval_ms)) AS avg_retrieval
     FROM messages WHERE direction = 'out' AND total_ms IS NOT NULL`
  );
  console.log(
    `\nTotal: ${stats[0].chats} contactos, ${stats[0].msgs} mensajes, ${stats[0].leads} leads\n` +
      `Latencia salida: n=${lat[0].n} avg=${lat[0].avg_total ?? '-'}ms p50=${lat[0].p50 ?? '-'}ms max=${lat[0].max_total ?? '-'}ms ` +
      `| llm avg=${lat[0].avg_llm ?? '-'}ms retrieval avg=${lat[0].avg_retrieval ?? '-'}ms\n`
  );
} else if (command === 'chat') {
  const jid = process.argv[3];
  if (!jid) {
    console.error('uso: npm run chat -- <jid>');
    process.exit(1);
  }
  const { rows } = await query(
    `SELECT * FROM messages WHERE chat_jid = $1 ORDER BY created_at DESC LIMIT 30`,
    [jid]
  );
  rows.reverse().forEach((r) => console.log(fmt(r)));
} else if (command === 'latency') {
  const { rows } = await query(
    `SELECT route, intent, model, count(*)::int AS n,
            round(avg(retrieval_ms)) AS avg_retrieval,
            round(avg(llm_ms)) AS avg_llm,
            round(avg(total_ms)) AS avg_total,
            round(max(total_ms)) AS max_total
     FROM messages
     WHERE direction = 'out'
     GROUP BY route, intent, model
     ORDER BY avg_total DESC NULLS LAST`
  );
  console.log('\nroute                 intent             model          n   retrieval  llm   total  max');
  for (const r of rows) {
    console.log(
      `${String(r.route || '-').padEnd(20)} ${String(r.intent || '-').padEnd(17)} ${String(r.model || '-').padEnd(13)} ` +
        `${String(r.n).padStart(3)} ${String(r.avg_retrieval ?? '-').padStart(9)} ${String(r.avg_llm ?? '-').padStart(5)} ` +
        `${String(r.avg_total ?? '-').padStart(6)} ${String(r.max_total ?? '-').padStart(5)}`
    );
  }
  console.log('');
} else {
  console.error(`comando desconocido: ${command} (disponibles: leads, chat, latency)`);
  process.exit(1);
}

await pool.end();
