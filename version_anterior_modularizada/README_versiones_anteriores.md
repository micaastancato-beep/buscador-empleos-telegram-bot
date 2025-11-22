🗂️ Versión anterior del proyecto (en módulos)

Al comenzar el trabajo práctico, desarrollamos una primera versión del bot utilizando una estructura modular, separando el código en distintos archivos:

gestor.py

extractor.py

procesador.py

presentador.py

etc.

La intención era aplicar Programación Orientada a Objetos y dividir responsabilidades, siguiendo buenas prácticas.

Sin embargo, durante las pruebas descubrimos varias dificultades:

❗ Principales problemas de esa versión

Se hacía muy complejo rastrear errores, porque estaban repartidos en varios módulos.

Los callbacks de Telegram y los handlers no lograban sincronizarse bien entre archivos.

La API de ScrapingDog devolvía respuestas variadas y costaba mantener la comunicación entre clases.

Cualquier cambio pequeño implicaba modificar 3 o 4 archivos distintos, lo que generaba inconsistencias.

Nuestro nivel de programación es todavía básico, y mantener tanta abstracción nos terminaba confundiendo.

👉 Decisión final

Siguiendo la recomendación de nuestra profesora y para asegurar estabilidad en el proyecto, integramos todo en un único archivo.

Esto nos permitió:

Depurar más rápido

Tener control total de la lógica

Evitar errores entre módulos

Entender mejor el flujo del bot
