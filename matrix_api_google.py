# matrix_api_google.py

import os
import re
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv

# — Carrega e valida a chave —
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Defina GOOGLE_API_KEY no .env")

# Regex para capturar o timestamp DD_MM_YYYY_HH_MM no nome do arquivo
TS_REGEX = re.compile(r"(\d{2}_\d{2}_\d{4}_\d{2}_\d{2})")

def get_distance_duration(origin: str, destination: str, departure_dt: datetime,
                          mode: str = "transit") -> dict:
    """Chama a API de matriz e retorna distance_text e duration_text."""
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "departure_time": int(departure_dt.timestamp()),
        "key": API_KEY
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    e = resp.json()["rows"][0]["elements"][0]
    return {"distance_text": e["distance"]["text"], "duration_text": e["duration"]["text"]}

def format_duration(duration_text: str) -> str:
    """Converte 'X hours Y mins' ou 'Y mins' para 'HH:MM'."""
    h = m = 0
    parts = duration_text.split()
    for i, p in enumerate(parts):
        if p.isdigit():
            n = int(p)
            u = parts[i+1] if i+1 < len(parts) else ""
            if u.startswith("hour"): h = n
            if u.startswith("min"):  m = n
    return f"{h:02d}:{m:02d}"

def find_latest_csv(raw_dir: str) -> str:
    """
    Procura em raw_dir todos os .csv (exceto os enriquecidos),
    extrai via TS_REGEX o timestamp e retorna o arquivo mais recente.
    """
    cand = []
    for fn in os.listdir(raw_dir):
        if not fn.endswith(".csv") or "_enriquecido" in fn:
            continue
        m = TS_REGEX.search(fn)
        if not m:
            continue
        try:
            dt = datetime.strptime(m.group(1), "%d_%m_%Y_%H_%M")
            cand.append((dt, fn))
        except ValueError:
            pass
    if not cand:
        raise FileNotFoundError(f"Nenhum CSV válido em {raw_dir}")
    return os.path.join(raw_dir, max(cand, key=lambda x: x[0])[1])

def enrich_csv(input_path: str = None, output_path: str = None):
    base = os.path.dirname(os.path.abspath(__file__))
    raw  = os.path.join(base, "raw_data")

    # 1) encontra o CSV
    if input_path is None:
        input_path = find_latest_csv(raw)
    print(">>> RAW DIR:", raw)
    print(">>> INPUT CSV:", input_path)

    # 2) define saída
    if output_path is None:
        output_path = input_path.replace(".csv", "_enriquecido.csv")
    print(">>> OUTPUT CSV:", output_path)

    # 3) abre e faz debug da leitura
    with open(input_path,  encoding='utf-8', newline='') as fin:
        reader = csv.DictReader(fin)
        print(">>> FIELDNAMES:", reader.fieldnames)
        rows = list(reader)
        print(">>> NÚMERO DE REGISTROS LIDOS:", len(rows))

    # 4) escreve o enriquecido
    orig = [f for f in reader.fieldnames if f != "Timestamp_Scraped"]
    header = orig + ["Distance", "Duration", "Timestamp_Scraped"]
    with open(output_path, 'w', encoding='utf-8', newline='') as fout:
        writer = csv.DictWriter(fout, fieldnames=header)
        writer.writeheader()

        for row in rows:
            ds = row.get("Data", "")
            try:
                dt_obj = datetime.strptime(ds, "%d/%m/%Y")
                info = get_distance_duration(row["Origem"], row["Destino"], dt_obj)
                row["Distance"] = info["distance_text"]
                row["Duration"] = format_duration(info["duration_text"])
            except Exception as e:
                row["Distance"] = ""
                row["Duration"] = ""
                print(f"[WARN] não enriqueceu {row['Origem']}→{row['Destino']} em {ds}: {e}")

            row["Timestamp_Scraped"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(row)

if __name__ == "__main__":
    enrich_csv()
