"""
BotoneraFree - Bot de reacciones para canales de Telegram
Autor: La Palta / victorsteepp
"""

import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CANAL_ID  = os.environ.get("CANAL_ID")
DB_FILE   = "reacciones.json"

# ── ESTILOS DE BOTONERA ────────────────────────────────────────────────────────
# Cada estilo define qué reacciones muestra
ESTILOS = {
    "noticias": {
        "reacciones": ["🔥", "👍", "😮", "😢"],
        "etiquetas":  ["Fuego", "Like", "Sorpresa", "Triste"],
    },
    "viral": {
        "reacciones": ["❤️", "😂", "😮", "😡"],
        "etiquetas":  ["Me encanta", "Jaja", "Wow", "Enojado"],
    },
    "opinion": {
        "reacciones": ["✅", "❌", "🤔"],
        "etiquetas":  ["De acuerdo", "En desacuerdo", "No sé"],
    },
    "clasico": {
        "reacciones": ["❤️", "👍", "💔"],
        "etiquetas":  ["Me gusta", "Bueno", "No me gusta"],
    },
    "farándula": {
        "reacciones": ["😍", "💅", "🤣", "😤"],
        "etiquetas":  ["Amo", "Obvio", "Jaja", "Qué roche"],
    },
    "deportes": {
        "reacciones": ["⚽", "🔥", "😤", "👏"],
        "etiquetas":  ["Gol", "Fuego", "Indignado", "Aplausos"],
    },
}
# ──────────────────────────────────────────────────────────────────────────────


def cargar_db() -> dict:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_db(db: dict):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def construir_teclado(msg_id: str, entrada: dict) -> InlineKeyboardMarkup:
    estilo_key = entrada.get("estilo", "clasico")
    estilo     = ESTILOS.get(estilo_key, ESTILOS["clasico"])
    reacciones = estilo["reacciones"]
    contadores = entrada.get("contadores", {})
    url        = entrada.get("url", "https://lapalta.pe")

    # Fila de reacciones (máx 4 por fila)
    botones_react = []
    for emoji in reacciones:
        count = contadores.get(emoji, 0)
        label = f"{emoji} {count}" if count > 0 else emoji
        botones_react.append(
            InlineKeyboardButton(label, callback_data=f"react|{msg_id}|{emoji}")
        )

    # Dividir en filas de 4
    filas = [botones_react[i:i+4] for i in range(0, len(botones_react), 4)]

    # Botones de acción
    fila_ver       = [InlineKeyboardButton("📰 Ver nota completa", url=url)]
    fila_compartir = [
        InlineKeyboardButton(
            "🔁 Compartir",
            url=f"https://t.me/share/url?url={url}"
        ),
        InlineKeyboardButton(
            "📢 Canal",
            url=f"https://t.me/{CANAL_ID.lstrip('@')}"
        ),
    ]

    return InlineKeyboardMarkup(filas + [fila_ver, fila_compartir])


def texto_ayuda() -> str:
    estilos_lista = "\n".join(
        f"  • <code>{k}</code> → {' '.join(v['reacciones'])}"
        for k, v in ESTILOS.items()
    )
    return (
        "📋 <b>Comandos disponibles:</b>\n\n"
        "/publicar <code>&lt;URL&gt; &lt;texto&gt;</code>\n"
        "  Publica con estilo <i>clasico</i>\n\n"
        "/publicar_estilo <code>&lt;estilo&gt; &lt;URL&gt; &lt;texto&gt;</code>\n"
        "  Publica con estilo específico\n\n"
        f"<b>Estilos disponibles:</b>\n{estilos_lista}\n\n"
        "/stats <code>&lt;ID del mensaje&gt;</code>\n"
        "  Ver conteo de reacciones de una nota"
    )


# ── COMANDO /publicar ──────────────────────────────────────────────────────────
async def cmd_publicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(texto_ayuda(), parse_mode="HTML")
        return

    url   = context.args[0]
    texto = " ".join(context.args[1:])

    entrada = {
        "estilo":     "clasico",
        "url":        url,
        "contadores": {},
        "votos":      {},
    }

    teclado = construir_teclado("tmp", entrada)
    msg = await context.bot.send_message(
        chat_id=CANAL_ID, text=texto, reply_markup=teclado
    )

    msg_id = str(msg.message_id)
    db = cargar_db()
    db[msg_id] = entrada
    guardar_db(db)

    await context.bot.edit_message_reply_markup(
        chat_id=CANAL_ID,
        message_id=msg.message_id,
        reply_markup=construir_teclado(msg_id, entrada)
    )
    await update.message.reply_text(
        f"✅ Publicado con estilo <b>clásico</b>\nID del mensaje: <code>{msg_id}</code>",
        parse_mode="HTML"
    )


# ── COMANDO /publicar_estilo ───────────────────────────────────────────────────
async def cmd_publicar_estilo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(texto_ayuda(), parse_mode="HTML")
        return

    estilo_key = context.args[0].lower()
    if estilo_key not in ESTILOS:
        await update.message.reply_text(
            f"❌ Estilo <b>{estilo_key}</b> no existe.\n\n" + texto_ayuda(),
            parse_mode="HTML"
        )
        return

    url   = context.args[1]
    texto = " ".join(context.args[2:])

    entrada = {
        "estilo":     estilo_key,
        "url":        url,
        "contadores": {},
        "votos":      {},
    }

    teclado = construir_teclado("tmp", entrada)
    msg = await context.bot.send_message(
        chat_id=CANAL_ID, text=texto, reply_markup=teclado
    )

    msg_id = str(msg.message_id)
    db = cargar_db()
    db[msg_id] = entrada
    guardar_db(db)

    await context.bot.edit_message_reply_markup(
        chat_id=CANAL_ID,
        message_id=msg.message_id,
        reply_markup=construir_teclado(msg_id, entrada)
    )

    emojis = " ".join(ESTILOS[estilo_key]["reacciones"])
    await update.message.reply_text(
        f"✅ Publicado con estilo <b>{estilo_key}</b> {emojis}\n"
        f"ID del mensaje: <code>{msg_id}</code>",
        parse_mode="HTML"
    )


# ── COMANDO /stats ─────────────────────────────────────────────────────────────
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /stats <ID del mensaje>")
        return

    msg_id = context.args[0]
    db = cargar_db()

    if msg_id not in db:
        await update.message.reply_text("❌ No encontré ese mensaje en la base de datos.")
        return

    entrada    = db[msg_id]
    contadores = entrada.get("contadores", {})
    total      = sum(contadores.values())
    estilo     = entrada.get("estilo", "clasico")
    url        = entrada.get("url", "")

    lineas = [f"📊 <b>Stats del mensaje {msg_id}</b>", f"Estilo: {estilo}", f"URL: {url}", ""]
    for emoji, count in contadores.items():
        pct = round(count / total * 100) if total else 0
        barra = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lineas.append(f"{emoji} {barra} {count} ({pct}%)")

    lineas.append(f"\n👥 Total de reacciones: {total}")
    await update.message.reply_text("\n".join(lineas), parse_mode="HTML")


# ── MANEJADOR DE REACCIONES ────────────────────────────────────────────────────
async def handle_reaccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, msg_id, emoji = query.data.split("|")
    user_id = str(query.from_user.id)

    db = cargar_db()
    if msg_id not in db:
        await query.answer("❌ Este post ya no está disponible.")
        return

    entrada    = db[msg_id]
    votos      = entrada.get("votos", {})
    contadores = entrada.get("contadores", {})
    voto_ant   = votos.get(user_id)

    if voto_ant == emoji:
        # Toggle off
        contadores[emoji] = max(0, contadores.get(emoji, 0) - 1)
        del votos[user_id]
        await query.answer("Reacción quitada")
    else:
        # Cambiar voto
        if voto_ant:
            contadores[voto_ant] = max(0, contadores.get(voto_ant, 0) - 1)
        contadores[emoji] = contadores.get(emoji, 0) + 1
        votos[user_id]    = emoji
        await query.answer(f"Reaccionaste con {emoji}")

    entrada["votos"]      = votos
    entrada["contadores"] = contadores
    db[msg_id] = entrada
    guardar_db(db)

    try:
        await query.edit_message_reply_markup(
            reply_markup=construir_teclado(msg_id, entrada)
        )
    except Exception:
        pass


# ── INICIO ────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("publicar",        cmd_publicar))
    app.add_handler(CommandHandler("publicar_estilo", cmd_publicar_estilo))
    app.add_handler(CommandHandler("stats",           cmd_stats))
    app.add_handler(CallbackQueryHandler(handle_reaccion, pattern=r"^react\|"))
    print("✅ BotoneraFree corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
