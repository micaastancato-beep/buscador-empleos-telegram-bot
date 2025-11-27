import requests
import sys
import telebot
from telebot import types
import google.generativeai as genai
import os
import time
import datetime

# ======================================================================
# CONFIGURACIÓN
# ======================================================================

# Configuración de la API de Google Gemini (requerida para mostrar_analisis_ia)
# La clave se obtiene del entorno.
os.environ["API_KEY"] = "API_KEY"
genai.configure(api_key=os.environ["API_KEY"])
# Inicialización del modelo de IA que se usará para el análisis de resultados.
model = genai.GenerativeModel('gemini-2.5-flash')

# Token del bot de Telegram y configuración de parse_mode para usar HTML.
TELEGRAM_BOT_TOKEN = '8418827665:AAFzoxRm_gco4kax08rWNeWFufrFNlY4dc0'
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode='HTML')

# Clave de la API de ScrapingDog para la extracción de ofertas de LinkedIn.
SCRAPINGDOG_API_KEY = "69035dd1a2ba049c8a36a261"

# Diccionario global para almacenar los datos de la solicitud de cada usuario
# (chat_id: {query, workType, experienceLevel, remote, location}).
user_data = {}


# ======================================================================
# LOG DE ERRORES
# ======================================================================

def log_error(msg):
    """
    Registra mensajes de error con timestamp en la consola y en un archivo.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR:", msg)
    try:
        # Intenta escribir el error en un archivo 'log_errores.txt'
        with open("log_errores.txt", "a") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        # Evita que el propio log de errores cause un error fatal.
        pass


# ======================================================================
# GESTOR GENERAL DEL FLUJO
# ======================================================================

class GestorSolicitudes:
    """
    Clase que maneja el flujo de la conversación con el usuario
    para recolectar los parámetros de búsqueda de empleo paso a paso.
    """

    # Opciones predefinidas para los menús inline de Telegram
    OPCIONES_TIPO = {
        "🧑‍💼 Full-time": "full_time",
        "⏱ Part-time": "part_time",
        "📄 Contrato": "contract",
        "📆 Temporal": "temporary"
    }

    OPCIONES_NIVEL = {
        "🎓 Internship": "internship",
        "🚀 Entry-level": "entry_level",
        "👥 Associate": "associate",
        "⭐ Mid-Senior": "mid_senior_level",
        "📌 Director": "director"
    }

    OPCIONES_REMOTO = {
        "🏢 Presencial": "at_work",
        "🏡 Remoto": "remote",
        "🔄 Híbrido": "hybrid"
    }

    def pedir_rubro(self, message):
        """Inicia el proceso, pide el rubro y guarda el chat_id."""
        chat_id = message.chat.id
        # Inicializa el diccionario de datos para el nuevo usuario/búsqueda.
        user_data[chat_id] = {}

        msg = bot.send_message(
            chat_id,
            "👋 ¡Hola! Vamos a buscarte trabajos.\n\n"
            "✍️ <b>Primero contame el rubro o área que te interesa</b>.\n"
            "<i>Ejemplo: Comunicación, Marketing, Programación, Diseño…</i>"
        )
        # Registra el siguiente paso: esperar el texto del rubro.
        bot.register_next_step_handler(msg, self.get_rubro)

    def get_rubro(self, message):
        """Guarda el rubro (query) y pide el tipo de trabajo (inline keyboard)."""
        chat_id = message.chat.id
        # Almacena el texto ingresado por el usuario como el parámetro 'query'.
        user_data[chat_id]['query'] = message.text

        # Crea un teclado inline para el tipo de trabajo.
        markup = types.InlineKeyboardMarkup()
        for label, val in self.OPCIONES_TIPO.items():
            # El callback_data se formatea para ser manejado en `callbacks`.
            markup.add(types.InlineKeyboardButton(label, callback_data=f"tipo:{val}"))

        bot.send_message(chat_id, "📌 <b>Elegí el tipo de trabajo:</b>", reply_markup=markup)

    def pedir_nivel(self, call):
        """Pide el nivel de experiencia (se llama después de elegir el tipo)."""
        chat_id = call.message.chat.id

        # Crea un teclado inline para el nivel de experiencia.
        markup = types.InlineKeyboardMarkup()
        for label, val in self.OPCIONES_NIVEL.items():
            markup.add(types.InlineKeyboardButton(label, callback_data=f"nivel:{val}"))

        bot.send_message(chat_id, "🎯 <b>¿Qué nivel de experiencia buscás?</b>", reply_markup=markup)

    def pedir_modalidad(self, call):
        """Pide la modalidad (remoto, presencial, híbrido)."""
        chat_id = call.message.chat.id

        # Crea un teclado inline para la modalidad de trabajo.
        markup = types.InlineKeyboardMarkup()
        for label, val in self.OPCIONES_REMOTO.items():
            markup.add(types.InlineKeyboardButton(label, callback_data=f"modalidad:{val}"))

        bot.send_message(chat_id, "🌍 <b>Elegí la modalidad de trabajo:</b>", reply_markup=markup)

    def pedir_ubicacion(self, call):
        """Pide la ubicación y registra el siguiente paso para la ejecución."""
        chat_id = call.message.chat.id

        msg = bot.send_message(
            chat_id,
            "📍 <b>¿En qué lugar querés trabajar?</b>\n"
            "<i>Ejemplo: Buenos Aires, Argentina</i>"
        )
        # Registra el siguiente paso: esperar el texto de la ubicación y ejecutar.
        bot.register_next_step_handler(msg, self.get_ubicacion_y_ejecutar)

    def get_ubicacion_y_ejecutar(self, message):
        """Guarda la ubicación, ejecuta la búsqueda y limpia los datos."""
        chat_id = message.chat.id
        # Almacena el texto ingresado por el usuario como el parámetro 'location'.
        user_data[chat_id]["location"] = message.text

        # Llama a la función principal de búsqueda con todos los parámetros recopilados.
        self.ejecutar_busqueda(chat_id, user_data[chat_id])

        # Limpia los datos del usuario después de la búsqueda para liberar memoria.
        if chat_id in user_data:
            del user_data[chat_id]

    def ejecutar_busqueda(self, chat_id, parametros):
        """
        Coordina la extracción, procesamiento y presentación de los resultados.
        """

        bot.send_message(
            chat_id,
            "🔎 <b>Buscando ofertas laborales…</b>\n"
            "<i>Esto puede tardar unos segundos.</i>"
        )

        # Inicialización de las clases de trabajo (Extractor, Procesador, Presentador)
        extractor = ExtractorEmpleos()
        procesador = ProcesadorResultados()
        presentador = Presentador()

        try:
            # 1. Extracción de datos de la API externa
            data = extractor.obtener_ofertas(parametros)
            # 2. Normalización de los datos extraídos
            ofertas = procesador.procesar(data)

            # 3. Presentación de los resultados al usuario
            presentador.mostrar_listado_crudo(chat_id, ofertas)
            # 4. Presentación del análisis generado por la IA
            presentador.mostrar_analisis_ia(chat_id, ofertas)

        except Exception as e:
            # Manejo de errores durante el proceso de búsqueda (e.g., error de red, API)
            log_error(e)
            bot.send_message(
                chat_id,
                "❌ <b>Ocurrió un error inesperado al procesar tu búsqueda.</b>"
            )


# ======================================================================
# EXTRACTOR — DEBUG
# ======================================================================

class ExtractorEmpleos:
    """
    Clase encargada de comunicarse con la API de ScrapingDog para obtener
    las ofertas de empleo. Incluye logging de debug y manejo de excepciones.
    """

    def __init__(self):
        # URL base de la API de ScrapingDog para búsqueda de empleos de LinkedIn.
        self.api_url = "https://api.scrapingdog.com/linkedinjobs"

    def obtener_ofertas(self, parametros):
        """
        Construye la URL con parámetros y realiza la solicitud GET a la API.
        """

        # Mapeo de los parámetros internos a los nombres esperados por la API.
        query_params = {
            "api_key": SCRAPINGDOG_API_KEY,
            "field": parametros.get("query", ""),
            "location": parametros.get("location", ""),
            "job_type": parametros.get("workType", ""),
            "exp_level": parametros.get("experienceLevel", ""),
            "work_type": parametros.get("remote", ""),
            "page": 1,
            "sort_by": "week",  # Ordenar por las más recientes
        }

        # Impresión de debug de la solicitud a enviar.
        print("\n==============================")
        print("📤 DEBUG → Enviando solicitud a ScrapingDog")
        print("Parámetros:", query_params)
        print("==============================\n")

        # Ejecución de la solicitud HTTP con un timeout.
        start = time.time()
        response = requests.get(self.api_url, params=query_params, timeout=40)
        end = time.time()

        print(f"⏱️ DEBUG → Tiempo de respuesta: {end - start:.2f} segundos")
        print("📥 DEBUG → status code:", response.status_code)

        try:
            # Intenta parsear la respuesta como JSON.
            data = response.json()
            print("📦 DEBUG → JSON recibido:")
            # Muestra el contenido JSON (puede ser grande, se asume que es manejable).
            print(data)
        except Exception:
            # Si falla el parseo JSON (ej: error 500 de la API sin JSON).
            print("❌ DEBUG → La API NO devolvió JSON")
            print("🔍 Respuesta cruda:")
            print(response.text[:1500]) # Muestra el inicio de la respuesta para debug.
            raise # Re-lanza la excepción para que sea manejada por `ejecutar_busqueda`.

        print("==============================\n")
        return data


# ======================================================================
# PROCESADOR — FUNCIONA CON LISTAS
# ======================================================================

class ProcesadorResultados:
    """
    Clase para transformar los datos crudos de la API a un formato estándar
    y limpio, listo para ser presentado o analizado.
    """

    def procesar(self, data):
        """
        Normaliza la lista de ofertas extrayendo solo los campos necesarios.
        """

        print("🔧 DEBUG Procesador recibió:", data)

        # Validación para asegurar que el input es una lista no vacía.
        if not data or not isinstance(data, list):
            print("⚠️ DEBUG → Formato inesperado o lista vacía.")
            return []

        resultados = []
        for oferta in data:
            # Mapeo de los nombres de campo de la API (ej: job_position)
            # a nombres internos limpios (ej: titulo) y uso de valores por defecto.
            resultados.append({
                "titulo": oferta.get("job_position", "Sin título"),
                "empresa": oferta.get("company_name", "Desconocida"),
                "ubicacion": oferta.get("job_location", "N/A"),
                "fecha": oferta.get("job_posting_date", "Sin fecha"),
                "link": oferta.get("job_link", "#"),
            })

        return resultados


# ======================================================================
# PRESENTADOR — HTML SEGURO
# ======================================================================

class Presentador:
    """
    Clase responsable de enviar los resultados al chat de Telegram
    en un formato legible y seguro (HTML).
    """

    def mostrar_listado_crudo(self, chat_id, ofertas):
        """
        Muestra las primeras 5 ofertas de la lista en mensajes individuales.
        """

        print("📊 DEBUG Ofertas procesadas:", ofertas)

        if not ofertas:
            # Mensaje si no se encontraron ofertas.
            bot.send_message(
                chat_id,
                "🙁 No encontramos ofertas con esos criterios.\n"
                "Podés intentar otra búsqueda con /start."
            )
            return

        bot.send_message(chat_id, "<b>💼 Estas son algunas de las ofertas más recientes:</b>")

        # Itera sobre las primeras 5 ofertas (o menos si hay menos de 5).
        for i, job in enumerate(ofertas[:5], start=1):

            # Construcción del mensaje en formato HTML.
            mensaje = (
                f"<b>{i}. {job['titulo']}</b>\n"
                f"🏢 <i>{job['empresa']}</i>\n"
                f"📍 {job['ubicacion']}\n"
                f"🗓 {job['fecha']}\n"
                # Se usa <a href> para el enlace, compatible con parse_mode='HTML'.
                f"<a href='{job['link']}'>🔗 Ver en LinkedIn</a>"
            )

            # Envía cada oferta como un mensaje separado.
            # `disable_web_page_preview=True` evita que Telegram genere previsualizaciones de enlaces.
            bot.send_message(chat_id, mensaje, disable_web_page_preview=True)

    def mostrar_analisis_ia(self, chat_id, ofertas):
        """
        Genera un análisis de las ofertas usando el modelo Gemini y lo envía.
        """

        if not ofertas:
            return

        bot.send_message(chat_id, "<b>🧠 Analizando las ofertas con Gemini...</b>")

        # Prepara un texto simple con las 10 primeras ofertas para el prompt.
        texto = "\n".join([
            f"- {o['titulo']} en {o['empresa']} ({o['ubicacion']})"
            for o in ofertas[:10]
        ])

        # Define el prompt para el modelo de IA.
        prompt = (
            "Analizá estas ofertas laborales y dame un resumen claro, breve (menos de 3000 caracteres) y útil para el usuario.\n\n"
            + texto
        )

        try:
            # Llama a la API de Google Gemini para generar el contenido.
            resp = model.generate_content(prompt)
            respuesta = resp.text or ""

            # ---------- 🚨 NUEVO: Manejo de límite de caracteres de Telegram ----------
            max_len = 3500  # Límite seguro (Telegram permite ~4096, pero 3500 es más robusto).

            if len(respuesta) <= max_len:
                # Si es corta, se envía en un solo mensaje.
                bot.send_message(chat_id, respuesta)
            else:
                # Si es demasiado larga, se divide en partes para evitar fallos.
                partes = [respuesta[i:i + max_len] for i in range(0, len(respuesta), max_len)]
                for p in partes:
                    bot.send_message(chat_id, p)

        except Exception as e:
            # Manejo de errores de la API de IA (ej: timeout, contenido bloqueado).
            log_error(e)
            bot.send_message(chat_id, "⚠️ <b>Hubo un problema al procesar la respuesta con IA.</b>")


# ======================================================================
# HANDLERS
# ======================================================================

# Instancia del gestor de flujo.
gestor = GestorSolicitudes()

@bot.message_handler(commands=['start', 'help'])
def start(message):
    """Handler para los comandos /start y /help. Inicia el flujo de solicitud."""
    gestor.pedir_rubro(message)

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    """
    Handler para las interacciones con los botones inline (callback queries).
    Maneja el paso entre las preguntas de tipo, nivel y modalidad.
    """

    chat_id = call.message.chat.id
    data = call.data

    # Edita el mensaje original para remover el teclado inline (limpieza de interfaz).
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)

    if chat_id not in user_data:
        # Manejo de sesión expirada (ej: si se reinicia el bot o pasa mucho tiempo).
        bot.send_message(chat_id, "⚠️ La sesión expiró. Usá /start para comenzar de nuevo.")
        return

    # Lógica para determinar qué opción se eligió y continuar el flujo.
    if data.startswith("tipo:"):
        # Guarda el valor (ej: "full_time") y pasa al siguiente paso.
        user_data[chat_id]['workType'] = data.split(":")[1]
        gestor.pedir_nivel(call)

    elif data.startswith("nivel:"):
        # Guarda el valor (ej: "entry_level") y pasa al siguiente paso.
        user_data[chat_id]['experienceLevel'] = data.split(":")[1]
        gestor.pedir_modalidad(call)

    elif data.startswith("modalidad:"):
        # Guarda el valor (ej: "remote") y pasa al paso final (ubicación).
        user_data[chat_id]['remote'] = data.split(":")[1]
        gestor.pedir_ubicacion(call)


# ======================================================================
# EJECUCIÓN DEL BOT
# ======================================================================

def run_bot():
    """Función principal para iniciar el bot de Telegram."""
    print("🤖 Bot iniciado.")
    # Inicia el loop de polling para escuchar nuevos mensajes.
    bot.polling(none_stop=True, interval=0, timeout=20)


if __name__ == "__main__":
    # Asegura que la función se ejecute solo si el script se corre directamente.

    run_bot()
