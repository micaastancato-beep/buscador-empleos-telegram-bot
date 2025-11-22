# gestor.py

class GestorSolicitudes:
    def __init__(self):
        self.parametros = {}

    def pedir_datos(self):
        print("Completa tus preferencias laborales:\n")

        rubro = input("🔹 Área o rubro de trabajo: ")
        tipo = input("🔹 Tipo de trabajo (full_time / part_time / contract / temporary): ")
        nivel = input("🔹 Nivel (internship / entry_level / associate / mid_senior_level / director): ")
        modelo = input("🔹 Modalidad (at_work / remote / hybrid): ")
        ubicacion = input("🔹 Ubicación: ")

        self.parametros = {
            "query": rubro,
            "workType": tipo,
            "experienceLevel": nivel,
            "remote": modelo,
            "location": ubicacion
        }

        return self.parametros
