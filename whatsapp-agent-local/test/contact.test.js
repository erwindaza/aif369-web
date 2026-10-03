import { test } from 'node:test';
import assert from 'node:assert/strict';
import { contactFooter, withContactFooter, CONTACT_TRIGGER, footerForces } from '../src/contact.js';
import { contactMessage } from '../src/prompt.js';
import { buildMessages } from '../src/agent.js';
import { getTenant } from '../src/tenants.js';

const aif = getTenant('aif369');
const clim = getTenant('priceclima');

test('footer trae los datos de cada empresa', () => {
  const a = contactFooter(aif);
  assert.match(a, /https:\/\/aif369\.com/);
  assert.match(a, /wa\.me\/56997547192/);
  assert.match(a, /edaza@aif369\.com/);
  assert.match(a, /calendly\.com\/edaza-aif369\/30min/);

  const c = contactFooter(clim);
  assert.match(c, /https:\/\/priceclima\.com/);
  assert.match(c, /wa\.me\/56997547192/);
  assert.match(c, /Morandé 835/);
  assert.match(c, /priceclima\.com\/contacto/);
  assert.doesNotMatch(c, /calendly/);
});

test('el pie solo se agrega cuando aporta', () => {
  const cualquiera = 'Entonces necesitas proyecto de datos e IA. ¿En que empresa trabajas?';
  assert.equal(withContactFooter(cualquiera, aif, { route: 'conversacion_general', model: 'state_machine' }), cualquiera);

  const conGatillo = 'Podemos agendar una llamada con el equipo.';
  const out = withContactFooter(conGatillo, aif, { route: 'conversacion_general', model: 'ollama' });
  assert.match(out, /Podemos agendar/);
  assert.match(out, /calendly\.com/);
  assert.equal(CONTACT_TRIGGER.test('¿Cuánto cuesta?'), false);
});

test('solo agenda fuerza pie; saludo, cotización y handoff no lo repiten por defecto', () => {
  for (const route of ['saludo', 'cotizacion', 'human_handoff']) {
    assert.equal(footerForces(route, null), false, route);
    const out = withContactFooter('Te ayudo con eso.', aif, { route, model: 'instant_rule' });
    assert.doesNotMatch(out, /aif369\.com/);
  }
  for (const route of ['agenda']) {
    assert.equal(footerForces(route, null), true, route);
    const out = withContactFooter('Te ayudo con eso.', aif, { route, model: 'instant_rule' });
    assert.match(out, /aif369\.com/);
  }
});

test('opt-out, ping y estado tecnico no llevan pie', () => {
  for (const route of ['opt_out', 'healthcheck', 'estado_tecnico']) {
    const out = withContactFooter('Entendido, agendar cuando quieras.', aif, { route, model: 'instant_rule', force: true });
    assert.equal(out, 'Entendido, agendar cuando quieras.', route);
  }
});

test('no duplica links que la respuesta ya trae', () => {
  const reply = `Agenda aquí: ${aif.contact.cta.url} o escribe a ${aif.contact.email}`;
  const out = withContactFooter(reply, aif, { route: 'cotizacion', model: 'ollama', force: true });
  assert.equal((out.match(/calendly/g) || []).length, 1);
  assert.equal((out.match(/edaza@aif369\.com/g) || []).length, 1);
  assert.match(out, /wa\.me\/56997547192/);
});

test('el prompt del modelo incluye los datos de contacto', () => {
  const note = contactMessage(aif);
  assert.match(note, /DATOS DE CONTACTO DE AIF369/);
  assert.match(note, /https:\/\/aif369\.com/);
  assert.match(note, /wa\.me\/56997547192/);
  assert.match(contactMessage(clim), /Morandé 835/);

  const messages = buildMessages({
    context: 'servicios',
    history: [],
    summary: 'estado=QUALIFYING',
    suggestedQuestion: '¿En que empresa trabajas?',
    tenant: clim,
  });
  const notes = messages.find((m) => m.role === 'system' && m !== messages[0]);
  assert.match(notes.content, /DATOS DE CONTACTO DE PriceClima/);
  assert.match(notes.content, /priceclima\.com\/contacto/);
});
