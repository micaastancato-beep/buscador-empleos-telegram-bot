# presentador.py

class Presentador:
    def mostrar(self, ofertas):
        if not ofertas:
            print("❌ No se encontraron ofertas laborales.")
            return

        print("\n💼 Ofertas laborales encontradas:\n")

        for i, job in enumerate(ofertas, start=1):
            print(f"{i}. {job['titulo']}")
            print(f"   🏢 Empresa: {job['empresa']}")
            print(f"   📍 Ubicación: {job['ubicacion']}")
            print(f"   📅 Publicado: {job['fecha']}")
            print(f"   🔗 Oferta: {job['link']}")
            print(f"   🌐 Perfil empresa: {job['perfil_empresa']}")
            print(f"   🖼️ Logo: {job['logo']}")
            print("-" * 90)
