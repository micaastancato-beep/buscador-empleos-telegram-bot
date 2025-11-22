# main.py

from gestor import GestorSolicitudes
from extractor import ExtractorEmpleos
from procesador import ProcesadorResultados
from presentador import Presentador

def main():
    print("🤖 Bienvenido al Buscador de Empleos Automatizado 💼\n")

    gestor = GestorSolicitudes()
    extractor = ExtractorEmpleos()
    procesador = ProcesadorResultados()
    presentador = Presentador()

    parametros = gestor.pedir_datos()
    data = extractor.obtener_ofertas(parametros)
    ofertas = procesador.procesar(data)
    presentador.mostrar(ofertas)

if __name__ == "__main__":
    main()
