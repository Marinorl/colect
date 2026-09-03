import csv
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

URL = "https://cuandosubo.sube.gob.ar/onebusaway-webapp/where/iphone/stop.action?id=14_204577"
CSV_FILE = "llegadas_colectivos.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
}

def inicializar_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp_captura",
                "linea",
                "route_id",
                "destino",
                "trip_id",
                "texto_prefijo_tiempo",
                "hora_arribo",
                "valor_status",
                "clases_css_status"
            ])

def extraer_parametro(url, param):
    if not url:
        return ""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    return qs.get(param, [""])[0]

def scrapear():
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registros = []

    try:
        res = requests.get(URL, headers=HEADERS, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        filas = soup.select("tr.arrivalsRow")

        for fila in filas:
            # 1. Línea y Route ID
            route_td = fila.select_one("td.arrivalsRouteEntry")
            route_a = route_td.find("a") if route_td else None
            linea = route_td.get_text(strip=True) if route_td else ""
            route_id = extraer_parametro(route_a.get("href", ""), "route") if route_a else ""

            # 2. Destino y Trip ID
            dest_div = fila.select_one("div.arrivalsDestinationEntry")
            dest_a = dest_div.find("a") if dest_div else None
            destino = dest_div.get_text(strip=True) if dest_div else ""
            trip_id = extraer_parametro(dest_a.get("href", ""), "id") if dest_a else ""

            # 3. Horario y prefijo ("Llegando a las", etc.)
            stop_num_span = fila.select_one(".arrivalsStopNumber")
            prefijo = stop_num_span.get_text(strip=True) if stop_num_span else ""

            time_span = fila.select_one(".arrivalsTimeEntry")
            hora_arribo = time_span.get_text(strip=True) if time_span else ""

            # 4. Status (minutos / indicador) y clases CSS crudas
            status_td = fila.select_one("td.arrivalsStatusEntry")
            valor_status = status_td.get_text(strip=True) if status_td else ""
            
            # Normalizamos espacios para que quede un string limpio de clases
            clases_css = " ".join(status_td.get("class", [])) if status_td else ""
            clases_css = re.sub(r"\s+", " ", clases_css).strip()

            if linea or hora_arribo:
                registros.append([
                    ahora,
                    linea,
                    route_id,
                    destino,
                    trip_id,
                    prefijo,
                    hora_arribo,
                    valor_status,
                    clases_css
                ])

        if registros:
            with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(registros)
            print(f"[{ahora}] Registrados {len(registros)} arribos.")
        else:
            print(f"[{ahora}] Sin arribos disponibles en la parada.")

    except Exception as e:
        print(f"[{ahora}] Error en la captura: {e}")

if __name__ == "__main__":
    inicializar_csv()
    scrapear()
