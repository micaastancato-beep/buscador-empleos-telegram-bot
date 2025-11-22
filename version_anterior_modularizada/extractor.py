# extractor.py

import requests
import config

class ExtractorEmpleos:
    """
    Se conecta a la API de ScrapingDog para obtener ofertas laborales de LinkedIn.
    Documentación: https://www.scrapingdog.com/jobs-search-api/
    """

    def __init__(self):
        self.api_url = "https://api.scrapingdog.com/linkedinjobs"

    def obtener_ofertas(self, parametros):
        """
        Hace una solicitud GET a la API con los parámetros del usuario.
        """

        # Mapeo de nombres según la API real de ScrapingDog
        query_params = {
            "api_key": config.API_KEY,
            "field": parametros.get("query", ""),                # rubro o job title
            "location": parametros.get("location", ""),           # ubicación
            "geoid": "",                                          # podés dejarlo vacío si no lo tenés
            "page": 1,
            "sort_by": "week",
            "job_type": parametros.get("workType", ""),           # full_time, part_time, etc
            "exp_level": parametros.get("experienceLevel", ""),   # associate, entry_level, etc
            "work_type": parametros.get("remote", ""),            # at_work, remote, hybrid
            "filter_by_company": ""                                # por defecto vacío
        }


        try:
            print("\n🔗 Conectando con la API de ScrapingDog...\n")
            response = requests.get(self.api_url, params=query_params)
            response.raise_for_status()  # lanza error si el status_code no es 200

            data = response.json()

            # Si la respuesta es una lista, la adaptamos al formato esperado
            if isinstance(data, list):
                return {"jobs": data}
            else:
                return data

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error al conectar con la API: {e}")
            return {"jobs": []}
