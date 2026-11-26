import csv
import hashlib
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 2026
CATALOGS_DIR = Path("data/catalogs")
OUTPUT_DIR = Path("data/lotes")
FECHA_INICIO = date(2026, 1, 5)
NUM_SEMANAS = 26


def calcular_hash(registro: dict) -> str:
    payload = json.dumps(registro, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def cargar_catalogos() -> dict:
    nombres = ["tiendas", "proveedores", "insumos", "productos", "dispositivos"]
    catalogos = {}
    for nombre in nombres:
        ruta = CATALOGS_DIR / f"{nombre}.json"
        with ruta.open("r", encoding="utf-8") as f:
            catalogos[nombre] = json.load(f)
    return catalogos

def generar_ventas_semana(
    rng: random.Random,
    batch_id: str,
    fecha_inicio_semana: date,
    tiendas: list[dict],
    productos: list[dict],
) -> list[dict]:
    filas = []
    contador_ticket = 1

    for offset_dia in range(7):
        fecha_actual = fecha_inicio_semana + timedelta(days=offset_dia)
        for tienda in tiendas:
            num_tickets = rng.randint(18, 35)
            for _ in range(num_tickets):
                ticket_id = f"{batch_id}-{tienda['tienda_id']}-T{contador_ticket:05d}"
                contador_ticket += 1
                hora = rng.randint(7, 20)
                minuto = rng.randint(0, 59)
                segundo = rng.randint(0, 59)
                fecha_hora_str = f"{fecha_actual.isoformat()} {hora:02d}:{minuto:02d}:{segundo:02d}"

                num_lineas = rng.randint(1, 3)
                for linea_num in range(1, num_lineas + 1):
                    prod = rng.choice(productos)
                    cantidad = rng.randint(1, 4)
                    precio_unitario = prod["precio_base"]

                    if prod["permite_promo"] and rng.random() < 0.25:
                        promo_id = rng.choice(["PROMO_10", "PROMO_15"])
                        pct = 0.10 if promo_id == "PROMO_10" else 0.15
                    else:
                        promo_id = "SIN_PROMO"
                        pct = 0.0

                    subtotal = round(cantidad * precio_unitario, 2)
                    descuento = round(subtotal * pct, 2)
                    total_linea = round(subtotal - descuento, 2)

                    # Inyectar ~1.5% de registros inválidos para probar cuarentena en GOV
                    if rng.random() < 0.015:
                        tipo_error = rng.choice(["precio_cero", "fecha_futura"])
                        if tipo_error == "precio_cero":
                            precio_unitario = 0.0
                            total_linea = 0.0
                        else:
                            fecha_futura = fecha_actual + timedelta(days=30)
                            fecha_hora_str = f"{fecha_futura.isoformat()} {hora:02d}:{minuto:02d}:{segundo:02d}"

                    registro = {
                        "batch_id": batch_id,
                        "ticket_id": ticket_id,
                        "linea_num": linea_num,
                        "fecha_hora": fecha_hora_str,
                        "tienda_id": tienda["tienda_id"],
                        "producto_id": prod["producto_id"],
                        "promo_id": promo_id,
                        "cantidad": cantidad,
                        "precio_unitario": precio_unitario,
                        "descuento": descuento,
                        "total_linea": total_linea,
                    }
                    registro["row_hash"] = calcular_hash(registro)
                    filas.append(registro)

    # Inyectar un par de duplicados exactos para probar deduplicación en STG/MERGE
    if len(filas) >= 2:
        filas.append(filas[0].copy())

    return filas

def generar_compras_semana(
    rng: random.Random,
    batch_id: str,
    fecha_inicio_semana: date,
    tiendas: list[dict],
    insumos: list[dict],
    proveedores: list[dict],
) -> list[dict]:
    filas = []
    contador_orden = 1

    # Agrupar proveedores por especialidad para mayor coherencia
    por_especialidad: dict[str, list[dict]] = {}
    for prov in proveedores:
        por_especialidad.setdefault(prov["especialidad"], []).append(prov)

    for offset_dia in range(7):
        fecha_actual = fecha_inicio_semana + timedelta(days=offset_dia)
        for tienda in tiendas:
            # No se compra todos los días en todas las tiendas
            if rng.random() > 0.65:
                continue

            num_ordenes = rng.randint(1, 3)
            for _ in range(num_ordenes):
                orden_id = f"{batch_id}-{tienda['tienda_id']}-C{contador_orden:05d}"
                contador_orden += 1

                num_lineas = rng.randint(1, 3)
                for linea_num in range(1, num_lineas + 1):
                    ins = rng.choice(insumos)
                    candidatos = por_especialidad.get(ins["categoria"]) or proveedores
                    prov = rng.choice(candidatos)
                    proveedor_id = prov["proveedor_id"]

                    cantidad = rng.randint(2, 15)
                    factor_variacion = rng.uniform(0.90, 1.15)
                    costo_unitario = round(ins["costo_base"] * factor_variacion, 2)
                    total_linea = round(cantidad * costo_unitario, 2)

                    # Inyectar ~1.5% de registros inválidos para probar cuarentena en GOV
                    if rng.random() < 0.015:
                        tipo_error = rng.choice(["costo_cero", "proveedor_invalido"])
                        if tipo_error == "costo_cero":
                            costo_unitario = 0.0
                            total_linea = 0.0
                        else:
                            proveedor_id = "PROV-99"

                    registro = {
                        "batch_id": batch_id,
                        "orden_id": orden_id,
                        "linea_num": linea_num,
                        "fecha_compra": fecha_actual.isoformat(),
                        "tienda_id": tienda["tienda_id"],
                        "insumo_id": ins["insumo_id"],
                        "proveedor_id": proveedor_id,
                        "cantidad": cantidad,
                        "costo_unitario": costo_unitario,
                        "total_linea": total_linea,
                    }
                    registro["row_hash"] = calcular_hash(registro)
                    filas.append(registro)

    if len(filas) >= 2:
        filas.append(filas[0].copy())

    return filas

def generar_iot_semana(
    rng: random.Random,
    batch_id: str,
    fecha_inicio_semana: date,
    dispositivos: list[dict],
) -> list[dict]:
    eventos = []
    contador_evento = 1

    for offset_dia in range(7):
        fecha_actual = fecha_inicio_semana + timedelta(days=offset_dia)
        for hora in range(24):
            timestamp_str = f"{fecha_actual.isoformat()} {hora:02d}:00:00"

            for disp in dispositivos:
                umbrales = disp["umbrales"]
                t_norm_min, t_norm_max = umbrales["temp_normal"]
                t_adv_min, t_adv_max = umbrales["temp_adv"]
                h_norm_min, h_norm_max = umbrales["hum_normal"]
                h_adv_min, h_adv_max = umbrales["hum_adv"]

                roll = rng.random()
                if roll < 0.86:
                    temp_c = rng.uniform(t_norm_min, t_norm_max)
                    hum_pct = rng.uniform(h_norm_min, h_norm_max)
                elif roll < 0.96:
                    # Zona de advertencia (por encima o por debajo de normal, dentro de adv)
                    if rng.random() < 0.5 and t_adv_min < t_norm_min:
                        temp_c = rng.uniform(t_adv_min, t_norm_min - 0.1)
                    else:
                        temp_c = rng.uniform(t_norm_max + 0.1, t_adv_max)
                    hum_pct = rng.uniform(h_adv_min, h_adv_max)
                elif roll < 0.99:
                    # Zona crítica pero plausible
                    temp_c = rng.uniform(t_adv_max + 0.5, t_adv_max + 6.0)
                    hum_pct = rng.uniform(h_norm_min, h_norm_max)
                else:
                    # Lectura imposible para probar cuarentena en GOV
                    temp_c = rng.choice([-65.0, 115.0])
                    hum_pct = 150.0

                registro = {
                    "batch_id": batch_id,
                    "evento_id": f"{batch_id}-EVT{contador_evento:07d}",
                    "timestamp_lectura": timestamp_str,
                    "dispositivo_id": disp["dispositivo_id"],
                    "tienda_id": disp["tienda_id"],
                    "temperatura_c": round(temp_c, 2),
                    "humedad_pct": round(hum_pct, 2),
                }
                registro["row_hash"] = calcular_hash(registro)
                eventos.append(registro)
                contador_evento += 1

    if len(eventos) >= 2:
        eventos.append(eventos[0].copy())

    return eventos

def guardar_csv(ruta: Path, filas: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if not filas:
        return
    columnas = list(filas[0].keys())
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)


def guardar_json_lote(ruta: Path, datos: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


def main() -> None:
    rng = random.Random(SEED)
    catalogos = cargar_catalogos()

    tiendas = catalogos["tiendas"]
    proveedores = catalogos["proveedores"]
    insumos = catalogos["insumos"]
    productos = catalogos["productos"]
    dispositivos = catalogos["dispositivos"]

    for semana_idx in range(NUM_SEMANAS):
        num_semana = semana_idx + 1
        batch_id = f"BATCH_2026_W{num_semana:02d}"
        fecha_inicio_semana = FECHA_INICIO + timedelta(weeks=semana_idx)
        carpeta_lote = OUTPUT_DIR / batch_id

        ventas = generar_ventas_semana(rng, batch_id, fecha_inicio_semana, tiendas, productos)
        compras = generar_compras_semana(rng, batch_id, fecha_inicio_semana, tiendas, insumos, proveedores)
        iot = generar_iot_semana(rng, batch_id, fecha_inicio_semana, dispositivos)

        guardar_csv(carpeta_lote / "ventas.csv", ventas)
        guardar_csv(carpeta_lote / "compras.csv", compras)
        guardar_json_lote(carpeta_lote / "iot.json", iot)

        print(
            f"[OK] {batch_id} ({fecha_inicio_semana}) -> "
            f"ventas: {len(ventas)}, compras: {len(compras)}, iot: {len(iot)}"
        )


if __name__ == "__main__":
    main()