#!/usr/bin/env python3
"""
AIF369 Operations Dashboard — BigQuery metrics, CLI
Usage: python backend/dashboard.py [--days 30]
Requires: pip install google-cloud-bigquery rich
"""
import argparse
import json
from datetime import datetime, timezone
from google.cloud import bigquery
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from rich.text import Text
from rich.rule import Rule

console = Console()
PROJECT_ID = "aif369-backend"
DATASET   = "aif369_analytics"
BQ = bigquery.Client(project=PROJECT_ID)

def q(sql):
    return list(BQ.query(sql).result())

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def delta(a, b):
    """Return colored delta string (a = current, b = previous)."""
    if b == 0:
        return Text("  —", style="dim")
    diff = a - b
    pct  = round(diff / b * 100)
    if diff > 0:
        return Text(f"  ▲{pct}%", style="green")
    elif diff < 0:
        return Text(f"  ▼{abs(pct)}%", style="red")
    return Text("  ±0%", style="dim")


# ─────────────────────────────────────────────────────────────────────────────
# QUERIES
# ─────────────────────────────────────────────────────────────────────────────

def chat_summary(days):
    rows = q(f"""
        SELECT
            DATE(timestamp, 'America/Santiago') as fecha,
            COUNT(*) as mensajes,
            COUNT(DISTINCT session_id) as sesiones,
            COUNTIF(provider='gemini') as via_gemini,
            COUNTIF(provider='none') as fallback,
            COUNTIF(language='en') as en_ingles
        FROM `{PROJECT_ID}.{DATASET}.chat_conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY 1 ORDER BY 1 DESC
    """)
    return rows

def chat_intents(days):
    return q(f"""
        SELECT intent_detected, COUNT(*) as n,
               COUNT(DISTINCT session_id) as sesiones
        FROM `{PROJECT_ID}.{DATASET}.chat_conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY 1 ORDER BY 2 DESC
    """)

def chat_top_questions(days):
    return q(f"""
        SELECT user_message, intent_detected, source_page,
               FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', timestamp, 'America/Santiago') as hora
        FROM `{PROJECT_ID}.{DATASET}.chat_conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
          AND turn_number = 1
        ORDER BY timestamp DESC
        LIMIT 20
    """)

def forms_summary(days):
    return q(f"""
        SELECT
            DATE(timestamp, 'America/Santiago') as fecha,
            COUNT(*) as forms,
            COUNT(DISTINCT email) as emails
        FROM `{PROJECT_ID}.{DATASET}.contact_form_submissions`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY 1 ORDER BY 1 DESC
    """)

def forms_leads(days):
    return q(f"""
        SELECT name, email, company, role,
               FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', timestamp, 'America/Santiago') as hora,
               source_page
        FROM `{PROJECT_ID}.{DATASET}.contact_form_submissions`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY timestamp DESC
        LIMIT 20
    """)

def scorecard_summary(days):
    return q(f"""
        SELECT
            DATE(timestamp, 'America/Santiago') as fecha,
            COUNT(*) as n,
            ROUND(AVG(total_score), 1) as score_prom,
            MIN(total_score) as score_min,
            MAX(total_score) as score_max
        FROM `{PROJECT_ID}.{DATASET}.scorecard_submissions`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY 1 ORDER BY 1 DESC
    """)

def scorecard_by_maturity(days):
    return q(f"""
        SELECT maturity_level, COUNT(*) as n, ROUND(AVG(total_score),1) as score_prom
        FROM `{PROJECT_ID}.{DATASET}.scorecard_submissions`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY 1 ORDER BY 2 DESC
    """)

def scorecard_leads(days):
    return q(f"""
        SELECT name, email, company, role, total_score, maturity_level,
               FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', timestamp, 'America/Santiago') as hora
        FROM `{PROJECT_ID}.{DATASET}.scorecard_submissions`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY timestamp DESC
        LIMIT 20
    """)

def totals_kpi(days):
    chats     = q(f"SELECT COUNT(*) n, COUNT(DISTINCT session_id) s FROM `{PROJECT_ID}.{DATASET}.chat_conversations` WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)")
    forms     = q(f"SELECT COUNT(*) n FROM `{PROJECT_ID}.{DATASET}.contact_form_submissions` WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)")
    scorecards= q(f"SELECT COUNT(*) n FROM `{PROJECT_ID}.{DATASET}.scorecard_submissions` WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)")
    # Previous period for delta
    chats_p   = q(f"SELECT COUNT(DISTINCT session_id) s FROM `{PROJECT_ID}.{DATASET}.chat_conversations` WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days*2} DAY) AND timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)")
    forms_p   = q(f"SELECT COUNT(*) n FROM `{PROJECT_ID}.{DATASET}.contact_form_submissions` WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days*2} DAY) AND timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)")
    scores_p  = q(f"SELECT COUNT(*) n FROM `{PROJECT_ID}.{DATASET}.scorecard_submissions` WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days*2} DAY) AND timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)")
    return {
        "chat_msgs": chats[0].n, "chat_sessions": chats[0].s,
        "forms": forms[0].n,
        "scorecards": scorecards[0].n,
        "chat_sessions_prev": chats_p[0].s,
        "forms_prev": forms_p[0].n,
        "scorecards_prev": scores_p[0].n,
    }

def pages_activity(days):
    return q(f"""
        SELECT source_page, COUNT(*) as interacciones,
               COUNT(DISTINCT session_id) as sesiones_unicas
        FROM `{PROJECT_ID}.{DATASET}.chat_conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
          AND source_page != ''
        GROUP BY 1 ORDER BY 2 DESC LIMIT 10
    """)

def token_usage(days):
    return q(f"""
        SELECT
            DATE(timestamp, 'America/Santiago') as fecha,
            COUNT(*) as llamadas,
            SUM(COALESCE(input_tokens, 0))  as tokens_in,
            SUM(COALESCE(output_tokens, 0)) as tokens_out,
            SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)) as tokens_total
        FROM `{PROJECT_ID}.{DATASET}.chat_conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
          AND provider = 'gemini'
        GROUP BY 1 ORDER BY 1 DESC
    """)

def suspicious_requests(days):
    return q(f"""
        SELECT
            DATE(timestamp, 'America/Santiago') as fecha,
            ip_address, origin_header,
            COUNT(*) as n,
            STRING_AGG(DISTINCT user_message ORDER BY user_message LIMIT 3) as sample_msgs
        FROM `{PROJECT_ID}.{DATASET}.chat_conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
          AND suspicious = TRUE
        GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 20
    """)

def token_summary(days):
    rows = q(f"""
        SELECT
            COALESCE(SUM(input_tokens), 0)  as total_in,
            COALESCE(SUM(output_tokens), 0) as total_out,
            COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens,
            COUNT(*) as llamadas_gemini,
            COUNTIF(suspicious = TRUE) as llamadas_sospechosas
        FROM `{PROJECT_ID}.{DATASET}.chat_conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
          AND provider = 'gemini'
    """)
    return rows[0] if rows else None


# ─────────────────────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render_kpis(kpi, days):
    console.print()
    console.print(Rule(f"[bold cyan]AIF369 Dashboard — últimos {days} días[/bold cyan]"))
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    console.print(f"[dim]Generado: {now}[/dim]\n")

    panels = [
        Panel(
            Text.assemble(
                Text(str(kpi["chat_sessions"]), style="bold cyan", justify="center"),
                Text(" sesiones\n", style="dim"),
                Text(str(kpi["chat_msgs"]), style="bold white"),
                Text(" mensajes", style="dim"),
                delta(kpi["chat_sessions"], kpi["chat_sessions_prev"]),
            ),
            title="💬 Chat", border_style="cyan", width=28
        ),
        Panel(
            Text.assemble(
                Text(str(kpi["scorecards"]), style="bold yellow", justify="center"),
                Text(" scorecards\n", style="dim"),
                Text("AI Readiness", style="dim"),
                delta(kpi["scorecards"], kpi["scorecards_prev"]),
            ),
            title="📊 Scorecard", border_style="yellow", width=28
        ),
        Panel(
            Text.assemble(
                Text(str(kpi["forms"]), style="bold green", justify="center"),
                Text(" leads\n", style="dim"),
                Text("Contact forms", style="dim"),
                delta(kpi["forms"], kpi["forms_prev"]),
            ),
            title="📋 Formularios", border_style="green", width=28
        ),
    ]
    console.print(Columns(panels))


def render_chat_daily(rows):
    if not rows:
        console.print("[dim]Sin datos de chat[/dim]")
        return
    t = Table(title="💬 Chat por día", box=box.SIMPLE_HEAVY, show_header=True)
    t.add_column("Fecha", style="dim")
    t.add_column("Sesiones", justify="right", style="cyan")
    t.add_column("Mensajes", justify="right")
    t.add_column("Gemini", justify="right", style="green")
    t.add_column("Fallback", justify="right", style="red")
    t.add_column("EN", justify="right", style="dim")
    for r in rows:
        t.add_row(
            str(r.fecha), str(r.sesiones), str(r.mensajes),
            str(r.via_gemini), str(r.fallback), str(r.en_ingles)
        )
    console.print(t)


def render_intents(rows):
    if not rows:
        return
    t = Table(title="🎯 Intenciones detectadas", box=box.SIMPLE_HEAVY)
    t.add_column("Intención")
    t.add_column("Mensajes", justify="right", style="cyan")
    t.add_column("Sesiones", justify="right")
    for r in rows:
        t.add_row(r.intent_detected or "—", str(r.n), str(r.sesiones))
    console.print(t)


def render_pages(rows):
    if not rows:
        return
    t = Table(title="📄 Páginas con más actividad (chat)", box=box.SIMPLE_HEAVY)
    t.add_column("Página", max_width=50, style="dim")
    t.add_column("Interacciones", justify="right", style="cyan")
    t.add_column("Sesiones únicas", justify="right")
    for r in rows:
        page = (r.source_page or "—").replace("https://aif369.com", "")
        t.add_row(page or "/", str(r.interacciones), str(r.sesiones_unicas))
    console.print(t)


def render_top_questions(rows):
    if not rows:
        return
    t = Table(title="❓ Primeras preguntas (últimas 20 sesiones)", box=box.SIMPLE_HEAVY)
    t.add_column("Hora", style="dim", width=16)
    t.add_column("Pregunta", max_width=55)
    t.add_column("Intención", width=12, style="yellow")
    t.add_column("Página", max_width=20, style="dim")
    for r in rows:
        page = (r.source_page or "—").replace("https://aif369.com", "")
        msg  = r.user_message[:80] + ("…" if len(r.user_message) > 80 else "")
        t.add_row(r.hora, msg, r.intent_detected or "—", page or "/")
    console.print(t)


def render_scorecard_maturity(rows):
    if not rows:
        return
    t = Table(title="📊 Scorecard por nivel de madurez", box=box.SIMPLE_HEAVY)
    t.add_column("Nivel")
    t.add_column("Cantidad", justify="right", style="yellow")
    t.add_column("Score promedio", justify="right")

    colors = {
        "Inicial": "red", "Exploratorio": "yellow",
        "Definido": "blue", "Integrado": "green", "Lider": "magenta"
    }
    for r in rows:
        c = colors.get(r.maturity_level, "white")
        t.add_row(
            Text(r.maturity_level, style=c),
            str(r.n), str(r.score_prom)
        )
    console.print(t)


def render_scorecard_leads(rows):
    if not rows:
        return
    t = Table(title="📊 Últimos scorecards (leads)", box=box.SIMPLE_HEAVY)
    t.add_column("Hora", style="dim", width=16)
    t.add_column("Nombre")
    t.add_column("Email", style="cyan")
    t.add_column("Empresa")
    t.add_column("Rol")
    t.add_column("Score", justify="right", style="yellow")
    t.add_column("Nivel")
    for r in rows:
        t.add_row(
            r.hora, r.name or "—", r.email or "—",
            r.company or "—", r.role or "—",
            str(r.total_score), r.maturity_level or "—"
        )
    console.print(t)


def render_form_leads(rows):
    if not rows:
        return
    t = Table(title="📋 Últimos leads (formularios)", box=box.SIMPLE_HEAVY)
    t.add_column("Hora", style="dim", width=16)
    t.add_column("Nombre")
    t.add_column("Email", style="green")
    t.add_column("Empresa")
    t.add_column("Rol")
    t.add_column("Página", style="dim", max_width=20)
    for r in rows:
        page = (r.source_page or "—").replace("https://aif369.com", "")
        t.add_row(
            r.hora, r.name or "—", r.email or "—",
            r.company or "—", r.role or "—", page or "/"
        )
    console.print(t)


def render_token_usage(rows, summary):
    console.print()
    console.print(Rule("[bold yellow]🔐 Seguridad & Tokens Gemini[/bold yellow]"))

    if summary:
        # Gemini-2.5-flash pricing: input $0.15/1M, output $0.60/1M (as of 2026)
        cost_in  = summary.total_in  / 1_000_000 * 0.15
        cost_out = summary.total_out / 1_000_000 * 0.60
        total_cost = cost_in + cost_out

        status = "[green]✓ NORMAL[/green]" if summary.llamadas_sospechosas == 0 else f"[red]⚠ {summary.llamadas_sospechosas} SOSPECHOSAS[/red]"
        console.print(Panel(
            f"""[bold]RESUMEN DE TOKENS GEMINI[/bold]

Llamadas totales a Gemini:  [cyan]{summary.llamadas_gemini}[/cyan]
Tokens de entrada (input):  [white]{summary.total_in:,}[/white]
Tokens de salida (output):  [white]{summary.total_out:,}[/white]
Tokens totales:             [bold white]{summary.total_tokens:,}[/bold white]

Costo estimado (USD):       [yellow]${total_cost:.4f}[/yellow]  (in: ${cost_in:.4f} | out: ${cost_out:.4f})
Llamadas sospechosas:       {status}

[dim]Precio Gemini-2.5-Flash: $0.15/1M tokens in · $0.60/1M tokens out[/dim]""",
            title="💰 Token Usage", border_style="yellow"
        ))

    if rows:
        t = Table(title="Tokens por día (solo llamadas Gemini)", box=box.SIMPLE_HEAVY)
        t.add_column("Fecha", style="dim")
        t.add_column("Llamadas", justify="right", style="cyan")
        t.add_column("Tokens IN", justify="right")
        t.add_column("Tokens OUT", justify="right")
        t.add_column("Total", justify="right", style="yellow")
        for r in rows:
            t.add_row(
                str(r.fecha), str(r.llamadas),
                f"{r.tokens_in:,}", f"{r.tokens_out:,}", f"{r.tokens_total:,}"
            )
        console.print(t)


def render_suspicious(rows):
    if not rows:
        console.print("[green]✓ Sin requests sospechosos en el período.[/green]")
        return
    t = Table(title="⚠ Requests sospechosos (origin inválido)", box=box.SIMPLE_HEAVY, border_style="red")
    t.add_column("Fecha", style="dim")
    t.add_column("IP", style="red")
    t.add_column("Origin", style="dim", max_width=40)
    t.add_column("Requests", justify="right")
    t.add_column("Mensajes (muestra)", max_width=50)
    for r in rows:
        t.add_row(
            str(r.fecha), r.ip_address or "—",
            r.origin_header or "(sin origin)", str(r.n),
            r.sample_msgs or "—"
        )
    console.print(t)


def render_funnel(kpi):
    console.print()
    console.print(Panel(
        f"""[bold]FUNNEL DE CONVERSIÓN[/bold]

[cyan]Chat sessions[/cyan]    →  {kpi['chat_sessions']:>4}  (100%)
[yellow]Scorecards[/yellow]      →  {kpi['scorecards']:>4}  ({round(kpi['scorecards']/max(kpi['chat_sessions'],1)*100)}% del chat)
[green]Leads (forms)[/green]   →  {kpi['forms']:>4}  ({round(kpi['forms']/max(kpi['chat_sessions'],1)*100)}% del chat)

[dim]⚠  Tráfico web (visitas de página) no trackeado todavía.
   Agrega Vercel Analytics para ver el top of funnel.[/dim]""",
        title="🔽 Funnel", border_style="dim"
    ))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AIF369 Operations Dashboard")
    parser.add_argument("--days", type=int, default=30, help="Ventana de análisis en días (default: 30)")
    parser.add_argument("--leads", action="store_true", help="Mostrar tabla detallada de leads")
    parser.add_argument("--questions", action="store_true", help="Mostrar primeras preguntas del chat")
    args = parser.parse_args()

    days = args.days

    console.print(f"\n[dim]Consultando BigQuery ({PROJECT_ID}.{DATASET})...[/dim]")

    kpi        = totals_kpi(days)
    chat_daily = chat_summary(days)
    intents    = chat_intents(days)
    pages      = pages_activity(days)
    sc_maturity= scorecard_by_maturity(days)
    sc_daily   = scorecard_summary(days)
    tok_daily  = token_usage(days)
    tok_sum    = token_summary(days)
    suspicious = suspicious_requests(days)

    render_kpis(kpi, days)
    render_funnel(kpi)
    console.print()
    render_chat_daily(chat_daily)
    render_intents(intents)
    render_pages(pages)
    render_scorecard_maturity(sc_maturity)
    render_token_usage(tok_daily, tok_sum)
    render_suspicious(suspicious)

    if args.leads:
        render_scorecard_leads(scorecard_leads(days))
        render_form_leads(forms_leads(days))

    if args.questions:
        render_top_questions(chat_top_questions(days))

    console.print(Rule("[dim]Fin del reporte[/dim]"))
    console.print(f"[dim]Tip: usa --leads para ver emails, --questions para ver primeras preguntas[/dim]\n")


if __name__ == "__main__":
    main()
