import json
import random
from pathlib import Path
from faker import Faker

SEED = 2026
OUTPUT_DIR = Path("data/catalogs")

UMBRALES_EQUIPO = {
    "camara_fria": {
        "temp_normal": (1.0, 4.0),
        "temp_adv": (0.0, 6.0),
        "hum_normal": (75.0, 85.0),
        "hum_adv": (70.0, 90.0),
    },
    "vitrina_refrigerada": {
        "temp_normal": (2.0, 5.0),
        "temp_adv": (1.0, 7.5),
        "hum_normal": (65.0, 80.0),
        "hum_adv": (60.0, 85.0),
    },
    "almacen_seco": {
        "temp_normal": (15.0, 24.0),
        "temp_adv": (12.0, 28.0),
        "hum_normal": (40.0, 60.0),
        "hum_adv": (35.0, 70.0),
    },
}


def guardar_json(nombre_archivo: str, datos: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ruta = OUTPUT_DIR / nombre_archivo
    with ruta.open("w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    print(f"[OK] {ruta} -> {len(datos)} registros")
    
    
def crear_tiendas() -> list[dict]:
    return [
        {"tienda_id": "TDA-01", "nombre": "Café Bryan's", "zona_campus": "Edificio Central"},
        {"tienda_id": "TDA-02", "nombre": "Isaí Brew & Roastery", "zona_campus": "Biblioteca / Ciencias"},
        {"tienda_id": "TDA-03", "nombre": "Angelo's Cold & Snack Bar", "zona_campus": "Área Deportiva / Labs"},
    ]


def crear_proveedores(rng: random.Random, fake: Faker) -> list[dict]:
    especialidades = [
        "Café en grano",
        "Lácteos",
        "Panadería",
        "Desechables",
        "Jarabes y Salsas",
        "Té y Matcha",
        "Alimentos Preparados",
        "Frutas y Congelados",
    ]
    proveedores = []
    for i in range(1, 9):
        proveedores.append({
            "proveedor_id": f"PROV-{i:02d}",
            "nombre": fake.company(),
            "especialidad": especialidades[i - 1],
            "lead_time_dias": rng.randint(1, 5),
        })
    return proveedores


def crear_insumos(rng: random.Random) -> list[dict]:
    base_insumos = [
        ("Café en grano tostado", "Café en grano", "kg", (240.0, 360.0)),
        ("Café espresso molido", "Café en grano", "kg", (250.0, 350.0)),
        ("Leche entera fresca", "Lácteos", "L", (22.0, 28.0)),
        ("Leche deslactosada", "Lácteos", "L", (23.0, 29.0)),
        ("Bebida de avena barista", "Lácteos", "L", (38.0, 48.0)),
        ("Bebida de almendra", "Lácteos", "L", (36.0, 46.0)),
        ("Crema batida spray", "Lácteos", "pz", (55.0, 75.0)),
        ("Croissant masa fermentada", "Panadería", "pz", (16.0, 26.0)),
        ("Dona glaseada", "Panadería", "pz", (12.0, 20.0)),
        ("Muffin chispas chocolate", "Panadería", "pz", (14.0, 22.0)),
        ("Galleta avena y pasas", "Panadería", "pz", (10.0, 18.0)),
        ("Vaso térmico 12 oz", "Desechables", "paquete", (150.0, 210.0)),
        ("Vaso frío 16 oz + tapa", "Desechables", "paquete", (170.0, 230.0)),
        ("Jarabe vainilla 1L", "Jarabes y Salsas", "L", (140.0, 195.0)),
        ("Salsa caramelo 1L", "Jarabes y Salsas", "L", (145.0, 200.0)),
        ("Polvo matcha ceremonial", "Té y Matcha", "kg", (420.0, 580.0)),
        ("Hojas té negro / chai", "Té y Matcha", "kg", (260.0, 360.0)),
        ("Sándwich jamón y queso", "Alimentos Preparados", "pz", (24.0, 36.0)),
        ("Bagel queso crema", "Alimentos Preparados", "pz", (22.0, 34.0)),
        ("Hielo / fruta congelada", "Frutas y Congelados", "kg", (18.0, 35.0)),
    ]

    insumos = []
    for i, (nombre, categoria, unidad, (c_min, c_max)) in enumerate(base_insumos, start=1):
        insumos.append({
            "insumo_id": f"INS-{i:02d}",
            "nombre": nombre,
            "categoria": categoria,
            "unidad": unidad,
            "costo_base": round(rng.uniform(c_min, c_max), 2),
        })
    return insumos


def crear_productos(rng: random.Random) -> list[dict]:
    perfiles_categoria = {
        "Café Caliente": (28.0, 56.0, [
            "Americano Clásico", "Espresso Doble", "Café del Día", "Cortado",
            "Café de Olla", "Americano Descafeinado", "Café Negro Campus",
            "Espresso Corto", "Café Filtrado", "Americano Intenso",
            "Café Caliente Suave", "Doble Carga"
        ]),
        "Bebidas Especiales": (55.0, 85.0, [
            "Latte Vainilla", "Cappuccino Clásico", "Mocha Chocolate", "Flat White",
            "Caramel Macchiato", "Matcha Latte", "Chai Latte", "Latte Avellana",
            "Mocha Blanco", "Latte Avena", "Chai Especiado", "Matcha Dulce",
            "Latte Caramelo"
        ]),
        "Bebidas Frías": (58.0, 95.0, [
            "Cold Brew Clásico", "Frappé Mocha", "Frappé Caramelo", "Iced Latte",
            "Iced Matcha", "Té Helado Frutos Rojos", "Frappé Oreo", "Cold Brew Vainilla",
            "Iced Chai", "Frappé Fresa", "Iced Americano", "Frappé Chocolate",
            "Té Helado Durazno"
        ]),
        "Panadería y Snacks": (32.0, 75.0, [
            "Croissant Mantequilla", "Dona Glaseada", "Muffin Chocolate",
            "Galleta Chispas", "Sándwich Jamón y Queso", "Bagel Queso Crema",
            "Panqué Limón", "Cuernito Relleno", "Wrap Pollo", "Biscocho Canela",
            "Ensalada Fresca", "Mini Brownie"
        ]),
    }

    productos = []
    idx = 1
    for categoria, (p_min, p_max, nombres) in perfiles_categoria.items():
        for nombre in nombres:
            if idx > 50:
                break
            productos.append({
                "producto_id": f"PROD-{idx:02d}",
                "nombre": nombre,
                "categoria": categoria,
                "precio_base": round(rng.uniform(p_min, p_max), 2),
                "permite_promo": rng.choice([True, False]),
            })
            idx += 1
        if idx > 50:
            break

    return productos


def crear_dispositivos(rng: random.Random, tiendas: list[dict]) -> list[dict]:
    tipos = ["camara_fria", "vitrina_refrigerada", "almacen_seco"]
    dispositivos = []
    idx = 1
    for tienda in tiendas:
        for _ in range(10):
            tipo = tipos[(idx - 1) % len(tipos)]
            dispositivos.append({
                "dispositivo_id": f"DISP-{idx:02d}",
                "tienda_id": tienda["tienda_id"],
                "tipo_equipo": tipo,
                "umbrales": UMBRALES_EQUIPO[tipo],
            })
            idx += 1
    return dispositivos


def main() -> None:
    rng = random.Random(SEED)
    fake = Faker("es_MX")
    fake.seed_instance(SEED)

    tiendas = crear_tiendas()
    proveedores = crear_proveedores(rng, fake)
    insumos = crear_insumos(rng)
    productos = crear_productos(rng)
    dispositivos = crear_dispositivos(rng, tiendas)

    guardar_json("tiendas.json", tiendas)
    guardar_json("proveedores.json", proveedores)
    guardar_json("insumos.json", insumos)
    guardar_json("productos.json", productos)
    guardar_json("dispositivos.json", dispositivos)


if __name__ == "__main__":
    main()
    
    