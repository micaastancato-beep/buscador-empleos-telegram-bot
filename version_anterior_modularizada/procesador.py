# procesador.py

class ProcesadorResultados:
    def procesar(self, data):
        if not data:
            return []

        # Si la respuesta viene como {"jobs": [...]}, la adaptamos
        if isinstance(data, dict) and "jobs" in data:
            ofertas = data["jobs"]
        else:
            ofertas = data

        resultados = []
        for oferta in ofertas:
            resultados.append({
                "titulo": oferta.get("job_position", "Sin título"),
                "empresa": oferta.get("company_name", "Desconocida"),
                "ubicacion": oferta.get("job_location", "N/A"),
                "fecha": oferta.get("job_posting_date", "Sin fecha"),
                "link": oferta.get("job_link", "#"),
                "perfil_empresa": oferta.get("company_profile", "No disponible"),
                "logo": oferta.get("company_logo_url", "No disponible")
            })
        return resultados
