# Buscador de Empleos Automatizado (Telegram Bot)

Este proyecto implementa un **chatbot inteligente de Telegram** que automatiza la búsqueda de empleo mediante:

- **ScrapingDog Jobs Search API** (para obtener ofertas laborales de LinkedIn)
- **Gemini AI** (para analizar y priorizar las mejores ofertas)
- **Python + Telebot**
- **Programación Orientada a Objetos**, manejo de excepciones y logging

Se desarrolló como **MVP (Producto Viable Mínimo)** para el **Trabajo Práctico Integrador – Taller de Programación II (2025)**.

## Funcionalidades principales

✔ Interacción conversacional guiada por Telegram  
✔ Recolección secuencial de 5 criterios:  
- Rubro / área  
- Tipo de trabajo  
- Nivel de experiencia  
- Modalidad  
- Ubicación  

✔ Extracción en tiempo real con ScrapingDog  
✔ Listado crudo de ofertas  
✔ Análisis inteligente con Gemini AI  
✔ Manejo robusto de errores  
✔ Arquitectura modular en POO  


## Estructura del Repositorio

/job_finder_bot/
│ └── findjob.py
│
├── requirements.txt
├── README.md
│
└── documentacion/
├── Brief.pdf
├── Instrucciones.pdf
└── TP_final_bitacora.pdf


## Instalación y ejecución

1. Clonar el repositorio
git clone https://github.com/micaastancato-beep/buscador-empleos-telegram-bot.git
cd buscador-empleos-telegram-bot

2. Instalar dependencias
Copiar código
pip install -r requirements.txt

3. Configurar claves (IMPORTANTE)
Editar dentro de:

Copiar código
/job_finder_bot/findjob.py
Estas variables:

Copiar código
TELEGRAM_BOT_TOKEN = '8418827665:AAFzoxRm_gco4kax08rWNeWFufrFNlY4dc0'
SCRAPINGDOG_API_KEY = "69035dd1a2ba049c8a36a261"
os.environ["API_KEY"] = "AIzaSyAFwR9tZt8yGtP47mFEqdCKeTczqWuoVzw"
⚠️ Para producción, se recomienda usar variables de entorno.

▶️ Ejecutar el bot

Copiar código
python job_finder_bot/findjob.py
La consola deberá mostrar:

Copiar código
🤖 Bot de Telegram iniciado. Escuchando mensajes...
Luego, en Telegram ingresá:
/start

📁 Documentación incluida (carpeta /documentacion)
Brief.pdf

Instrucciones.pdf

TP_final_bitacora.pdf

🧩 Tecnologías utilizadas
Python

Telebot (pyTelegramBotAPI)

Requests

Google Gemini (google-generativeai)

ScrapingDog Jobs Search API

Programación Orientada a Objetos

Logging + Manejo de excepciones

👩‍💻 Integrantes
Cuch, Lucía Carolina
Kaplan, Azul
Stancato, Micaela

Docente: Diego Onna
Materia: Taller de Programación II
Año: 2025

📌 Estado del proyecto
Versión: v1.0 – MVP entregable
Incluye:
✔ Búsqueda completa
✔ Integración de 2 APIs
✔ Listado crudo + análisis IA
✔ Manejo de casos borde
✔ Documentación completa


