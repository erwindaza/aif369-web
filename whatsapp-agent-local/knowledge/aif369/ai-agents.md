# Agentes de IA, automatización y productos de AIF369

## Agentes y copilotos de IA (servicio de implementación)
Asistentes conversacionales y agentes autónomos que automatizan procesos de clientes y backoffice: agentes para atención al cliente, copilotos internos para equipos, automatización de documentos e integración con CRM y ERP. Se construyen en sprints de 2–4 semanas con equipos de 2–5 personas y transferencia de conocimiento continua.
<!-- fuente: service-implementacion.html -->

## Sistemas RAG y orquestación multi-agente
Arquitecturas RAG con bases vectoriales, orquestación multi-agente e integración con sistemas empresariales en GCP. Declarado en producción: POC con GPU (NVIDIA Tesla T4), embeddings con Word2Vec y Vertex AI, matching semántico one-to-one, deduplicación inteligente y recomendación por similitud vectorial. Roadmap publicado: Kong AI Gateway, LangGraph multi-agente y Vector Search nativo.
<!-- fuente: services.html -->

## Automatización de datos con Airflow
Apache Airflow como estándar de orquestación: DAGs, operadores, conexiones, variables y secretos, ingesta desde APIs, transformación con pandas y SQL, carga a data warehouse, integración de modelos ML, clasificación automática, enriquecimiento con IA generativa, testing con pytest, Docker, Cloud Composer / MWAA, CI/CD y monitoreo.
<!-- fuente: automatizacion-airflow.html -->

## Chatbots y automatización de atención al cliente
Solución del catálogo "Automatización Inteligente de Atención al Cliente": dominio Servicio; industrias retail, banca, salud y educación; estructura semi-estructurada; patrón Chatbot/Copiloto + RAG + Handoff a humano. Datos necesarios: FAQ, base de conocimiento, tickets, políticas, manuales e historial conversacional. Modo de entrega: PoC → MVP → Producción.
<!-- fuente: catalogo-soluciones-ia.html -->

## Observabilidad LLM
Tracing de prompts, respuestas, costos, latencia y calidad con alertas automáticas mediante Langfuse. Regla declarada: "si Langfuse cae, el pipeline se detiene. No operamos sin trazabilidad". Incluye prompts versionados con labels (production/staging), monitoreo de costos por modelo y pipeline, alertas Teams por webhook y backoff exponencial. Langfuse opera en más de 5 pipelines de producción.
<!-- fuente: services.html -->

## Migración a AI Gateways corporativos
Planificación y ejecución de migración con control de costos, rate limiting y failover automático, "sin downtime y con rollback automático": análisis de impacto, estrategia de failover y callback, estimación de costos bajo el nuevo modelo, coordinación con arquitectos y Tech Leads, y testing gradual de procesos críticos. Destino declarado: Kong AI Gateway y Kairos Agentic Platform.
<!-- fuente: services.html -->

## Compliance-CL (herramienta de código)
Skill de Claude Code que analiza el repositorio y genera documentos legales en la carpeta `.compliance/`: RAT, Política de Privacidad, DPA, Plan de Brechas, Código de Ética y Matriz de Riesgos; además propone controles (MFA, cifrado en reposo, audit logs, endpoints ARCO y alertas de brechas). Cubre Ley 21.719 y Ley 21.595. Documentación en GitHub. Precio no publicado.
<!-- fuente: compliance-tool.html --> <!-- verificar -->

## Asesoría con IA: Gemini CAIO y Consultor CAIO
Asesor CAIO con Gemini: USD $100 por sesión; analiza el problema, recomienda solución del catálogo, orienta arquitectura, riesgo y roadmap; no escribe código. Consultor CAIO de AIF369: precio a medida, hands-off (estrategia, gobierno y dirección), tampoco escribe código. El desarrollo se ejecuta con talento especializado del partner BeJoby, con precio según alcance, perfil y duración.
<!-- fuente: catalogo-soluciones-ia.html -->

## Capacidades de agentes en producción
AI Content Factory: generación de contenido de marketing a escala con LLMs gobernados, evaluación de calidad con LLM-as-judge, selección automática del mejor candidato, observabilidad end-to-end con Langfuse y compliance integrado. Bias detection con 6 tipos de sesgo controlados: género, regional, marca, precio, alucinación y selección.
<!-- fuente: services.html -->

## Cursos de automatización e IA
"IA y Automatización de Datos con Airflow": USD $300, intermedio, 8 semanas (16 horas), online en vivo con grabaciones, proyecto final de pipeline Airflow + IA, certificado AIF369. "Big Data + Inteligencia Artificial": USD $400, intermedio, 8 semanas (16 horas), incluye RAG, embeddings, gobernanza y proyecto final de pipeline Big Data + IA.
<!-- fuente: automatizacion-airflow.html, big-data-ia.html -->

## Términos clave
agentes de IA, agentes inteligentes, copilotos, chatbot, asistente virtual, RAG, LLM, LLMs en producción, LangGraph, multi-agente, Airflow, orquestación, DAG, automatización, MLOps, LLMOps, Langfuse, observabilidad LLM, bias detection, sesgos, AI Gateway, Kong, Compliance-CL, Gemini CAIO, BeJoby.
