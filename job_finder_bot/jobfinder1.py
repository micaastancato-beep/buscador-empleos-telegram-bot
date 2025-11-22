import requests
import sys
import telebot
from telebot import types   
import google.generativeai as genai
import os
import time
import datetime

# ==============================================================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN DE SERVICIOS
# ==============================================================================

# Configuración de Gemini AI
# Se recomienda usar variables de entorno para las claves en producción.
os.environ["API_KEY"] = "AIzaSyAZ4pvgZ8AcKY_QOthvQGcype9vm8URTXg"  
genai.configure(api_key=os.environ["API_KEY"])
# Inicialización del modelo de IA generativa
model = genai.GenerativeModel('gemini-2.5-flash') 

# Configuración de Telegram Bot
TELEGRAM_BOT_TOKEN = '8418827665:AAFzoxRm_gco4kax08rWNeWFufrFNlY4dc0'
# Inicialización del bot. parse_mode='Markdown' se usa para dar formato 
# a los mensajes de bienvenida y a los listados de ofertas.
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode='Markdown') 

# Clave de ScrapingDog para la extracción de datos
SCRAPINGDOG_API_KEY = "68ffe7a87a7ad738e895e3ae" 

# Diccionario global para almacenar el estado de la conversación (parámetros)
# de cada usuario (identificado por chat_id).
user_data = {} 


# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def log_error(mensaje):
    """
    Registra un mensaje de error con marca de tiempo en la consola y en un archivo de logs.
    Implementación de Manejo de Excepciones robusto.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("log_errores.txt", "a") as f:
            f.write(f"[{timestamp}] {mensaje}\n")
    except IOError:
        print(f"ERROR: No se pudo escribir en log_errores.txt")
    print(f"LOG: {mensaje}") 


# ==============================================================================
# 2. MÓDULOS DE POO (CLASES)
# ==============================================================================

class GestorSolicitudes:
    """
    Módulo Gestor. Controla el flujo conversacional del bot (Telegram), 
    recolectando los 5 parámetros del usuario de forma secuencial.
    A diferencia de la versión de consola, utiliza 'telebot' para manejar estados.
    """
    
    # Definición de las opciones y su valor para los botones (Callback Data)
    OPCIONES_TIPO = {"Full-time": "full_time", "Part-time": "part_time", "Contrato": "contract", "Temporal": "temporary"}
    OPCIONES_NIVEL = {"Internship": "internship", "Entry-level": "entry_level", "Associate": "associate", "Mid-Senior": "mid_senior_level", "Director": "director"}
    OPCIONES_REMOTO = {"Presencial (At work)": "at_work", "Remoto": "remote", "Híbrido": "hybrid"}

    def pedir_rubro(self, message):
        """Inicia la conversación. Usa register_next_step_handler para la respuesta."""
        chat_id = message.chat.id
        user_data[chat_id] = {}
        
        msg = bot.send_message(chat_id, 
                               "🤖 **Bienvenido al Buscador de Empleos.**\n\n"
                               "🔹 Ingresa el **Área o rubro de trabajo** (ej: Python Developer):")
        bot.register_next_step_handler(msg, self.get_rubro)

    def get_rubro(self, message):
        """Guarda el rubro y genera los botones para el Tipo de Trabajo."""
        chat_id = message.chat.id
        if message.text in ['/start', '/cancel']:
             bot.send_message(chat_id, "Búsqueda cancelada.")
             return
             
        user_data[chat_id]['query'] = message.text
        
        # Uso de InlineKeyboard: Mejor UX y asegura valores válidos para la API.
        markup = types.InlineKeyboardMarkup()
        for label, data_value in self.OPCIONES_TIPO.items():
            # El callback_data se usa para encadenar el flujo en handle_callback_query
            markup.add(types.InlineKeyboardButton(label, callback_data=f"tipo:{data_value}"))
            
        bot.send_message(chat_id, "🔹 Ahora, selecciona el **Tipo de trabajo**:", reply_markup=markup)

    def pedir_nivel(self, call):
        """Pide el nivel de experiencia (con botones). Es llamado desde el callback."""
        chat_id = call.message.chat.id
        markup = types.InlineKeyboardMarkup()
        for label, data_value in self.OPCIONES_NIVEL.items():
            markup.add(types.InlineKeyboardButton(label, callback_data=f"nivel:{data_value}"))
            
        bot.send_message(chat_id, "🔹 ¿Cuál es tu **Nivel de experiencia**?", reply_markup=markup)

    def pedir_modalidad(self, call):
        """Pide la modalidad de trabajo (con botones)."""
        chat_id = call.message.chat.id
        markup = types.InlineKeyboardMarkup()
        for label, data_value in self.OPCIONES_REMOTO.items():
            markup.add(types.InlineKeyboardButton(label, callback_data=f"modalidad:{data_value}"))
            
        bot.send_message(chat_id, "🔹 ¿Cuál es la **Modalidad** de trabajo?", reply_markup=markup)

    def pedir_ubicacion(self, call):
        """Pide la ubicación (vuelve a ser texto libre)."""
        chat_id = call.message.chat.id
        
        msg = bot.send_message(chat_id, "🔹 Por último, la **Ubicación** (ej: Madrid, Spain, o deja vacío para global):")
        bot.register_next_step_handler(msg, self.get_ubicacion_y_ejecutar)

    def get_ubicacion_y_ejecutar(self, message):
        """Guarda la ubicación y ejecuta el flujo principal (Extractor -> Procesador -> Presentador)."""
        chat_id = message.chat.id
        user_data[chat_id]['location'] = message.text
        
        self.ejecutar_busqueda(chat_id, user_data[chat_id])
        
        # Limpieza de estado: fundamental para liberar memoria y evitar cruces de datos.
        if chat_id in user_data:
            del user_data[chat_id]

    def ejecutar_busqueda(self, chat_id, parametros):
        """Coordina la ejecución de los otros módulos."""
        bot.send_message(chat_id, "🔎 **Buscando ofertas...** Esto puede tardar unos segundos.")
        
        extractor = ExtractorEmpleos()
        procesador = ProcesadorResultados()
        presentador = Presentador()

        try:
            # 1. Extracción de datos
            data = extractor.obtener_ofertas(parametros)
            # 2. Procesamiento/Normalización
            ofertas = procesador.procesar(data)
            
            # 3. Presentación (doble formato: lista cruda y análisis IA)
            presentador.mostrar_listado_crudo(chat_id, ofertas)
            presentador.mostrar_analisis_ia(chat_id, ofertas)

        except requests.exceptions.HTTPError as e:
            # Manejo de excepción HTTP: errores 4xx o 5xx de la API externa.
            log_error(f"Error HTTP en chat {chat_id} con API: {e}")
            bot.send_message(chat_id, "❌ Error al conectar con la API de empleos. La cuota puede haberse agotado.")
        except Exception as e:
            # Manejo de excepción genérica: otros errores (conexión, JSON inválido).
            log_error(f"Error inesperado en chat {chat_id}: {e}")
            bot.send_message(chat_id, "❌ Ha ocurrido un error inesperado al buscar ofertas.")


class ExtractorEmpleos:
    """
    Módulo Extractor. Encapsula la lógica de conexión con la API externa (ScrapingDog).
    """
    def __init__(self):
        self.api_url = "https://api.scrapingdog.com/linkedinjobs"

    def obtener_ofertas(self, parametros):
        """Realiza la solicitud GET a la API con los parámetros mapeados."""
        query_params = {
            "api_key": SCRAPINGDOG_API_KEY,
            "field": parametros.get("query", ""),
            "location": parametros.get("location", ""),
            "job_type": parametros.get("workType", ""),
            "exp_level": parametros.get("experienceLevel", ""),
            "work_type": parametros.get("remote", ""),
            "page": 1,
            "sort_by": "week"
            # Campos opcionales omitidos para simplificar
        }
        
        response = requests.get(self.api_url, params=query_params)
        response.raise_for_status() # Lanza requests.exceptions.HTTPError si falla
        return response.json()


class ProcesadorResultados:
    """
    Módulo Procesador. Normaliza y filtra los datos obtenidos de la API.
    Asegura que la estructura de los resultados sea consistente.
    """
    def procesar(self, data):
        """Extrae los campos relevantes de la respuesta JSON."""
        if not data or not isinstance(data, dict) or "jobs" not in data:
            return []

        ofertas = data["jobs"]
        resultados = []
        for oferta in ofertas:
            resultados.append({
                "titulo": oferta.get("job_position", "Sin título"),
                "empresa": oferta.get("company_name", "Desconocida"),
                "ubicacion": oferta.get("job_location", "N/A"),
                "fecha": oferta.get("job_posting_date", "Sin fecha"),
                "link": oferta.get("job_link", "#"),
            })
        return resultados


class Presentador:
    """
    Módulo Presentador. Muestra los resultados al usuario final (Telegram).
    Utiliza el motor de IA (Gemini) para análisis avanzado.
    """
    
    def mostrar_listado_crudo(self, chat_id, ofertas):
        """Muestra las primeras 5 ofertas en formato de lista (cumple requisito básico de devolución)."""
        if not ofertas:
            return 
            
        bot.send_message(chat_id, f"💼 **Primeras {min(len(ofertas), 5)} de {len(ofertas)} ofertas encontradas:**")
        
        for i, job in enumerate(ofertas[:5], start=1):
            mensaje = (
                f"**{i}. {job['titulo']}**\n"
                f"🏢 Empresa: `{job['empresa']}`\n"
                f"📍 Ubicación: `{job['ubicacion']}`\n"
                f"🔗 [Ver Oferta]({job['link']})"
            )
            bot.send_message(chat_id, mensaje, disable_web_page_preview=True)
            
        if len(ofertas) > 5:
             bot.send_message(chat_id, f"*Se omitieron {len(ofertas) - 5} resultados del listado crudo.*")


    def mostrar_analisis_ia(self, chat_id, ofertas):
        """Genera un prompt con las ofertas y envía el análisis detallado de la IA (Gemini)."""
        if not ofertas:
            return

        bot.send_message(chat_id, f"🧠 Ahora, el análisis de las ofertas por **Gemini AI**...")
        
        # Se limitan las ofertas para el prompt por razones de costo y token.
        texto_ofertas = "\n".join(
            [f"ID {i}: {o['titulo']} | {o['empresa']} | {o['ubicacion']}" for i, o in enumerate(ofertas[:10], start=1)]
        )

        prompt = (
            "Eres un analista de talento. Evalúa la siguiente lista de ofertas laborales "
            "y crea un resumen claro. Indica de 3 a 5 de las mejores opciones (mencionando su ID) "
            "basándote en el título, empresa y ubicación. Explica brevemente por qué las elegiste."
            f"\n\n--- Lista de Ofertas ---\n{texto_ofertas}"
            "\n\nFormatea tu respuesta usando negritas y listas (no uses bloques de código ```), solo texto y asteriscos."
        )

        try:
            respuesta = model.generate_content(prompt)
            
            # FIX CRÍTICO: parse_mode=None se usa para evitar el error 400 
            # de Telegram causado por el Markdown inconsistente generado por la IA.
            bot.send_message(chat_id, 
                             "🤖 **Análisis de Empleos por Gemini:**\n\n" + respuesta.text,
                             parse_mode=None) 
            
            bot.send_message(chat_id, "\n\n✅ **Búsqueda finalizada.** Usa /start para comenzar de nuevo.")

        except Exception as e:
            log_error(f"Error en llamada a Gemini: {e}")
            bot.send_message(chat_id, "⚠️ No se pudo contactar al módulo de Inteligencia Artificial para el análisis.")


# ==============================================================================
# 3. HANDLERS DE TELEGRAM (CONTROLADORES)
# ==============================================================================

gestor_telegram = GestorSolicitudes()

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """Manejador para iniciar el proceso de recolección de datos."""
    gestor_telegram.pedir_rubro(message)

@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    """Manejador para cancelar el proceso en cualquier momento."""
    chat_id = message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]
    bot.send_message(chat_id, "Búsqueda cancelada. Usa /start para comenzar de nuevo.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """
    Manejador principal para las respuestas de los botones inline (callback_query).
    Controla el flujo secuencial de los 3 pasos de selección (Tipo, Nivel, Modalidad).
    """
    chat_id = call.message.chat.id
    data = call.data
    
    # Se edita el mensaje para quitar los botones y limpiar la interfaz.
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    
    if chat_id not in user_data:
        bot.send_message(chat_id, "La sesión expiró o hubo un error. Usa /start para comenzar.")
        return

    # Lógica de encadenamiento de la conversación (Estado)
    if data.startswith("tipo:"):
        _, valor = data.split(":")
        user_data[chat_id]['workType'] = valor
        gestor_telegram.pedir_nivel(call) 

    elif data.startswith("nivel:"):
        _, valor = data.split(":")
        user_data[chat_id]['experienceLevel'] = valor
        gestor_telegram.pedir_modalidad(call) 

    elif data.startswith("modalidad:"):
        _, valor = data.split(":")
        user_data[chat_id]['remote'] = valor
        gestor_telegram.pedir_ubicacion(call) 


# ==============================================================================
# 4. ARRANQUE DEL SISTEMA
# ==============================================================================

def run_bot():
    """Función principal que inicia el polling del bot y lo mantiene en línea."""
    print("🤖 Bot de Telegram iniciado. Escuchando mensajes...")
    try:
        # bot.polling() mantiene el programa escuchando eventos de Telegram.
        bot.polling(none_stop=True, interval=0, timeout=20) 
    except Exception as e:
        # Si el bot cae, lo registra y lo intenta reiniciar.
        log_error(f"Error fatal en el polling del bot: {e}")
        time.sleep(5)
        run_bot() 

if __name__ == "__main__":
    # Asegura que el bot solo se ejecute al iniciar el script directamente.
    run_bot()