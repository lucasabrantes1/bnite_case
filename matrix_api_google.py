# matrix_api_google.py

import os
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv

# — Carrega e valida a chave —
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Defina GOOGLE_API_KEY no .env")

def get_distance_duration(origin: str, destination: str, departure_dt: datetime,
                          mode: str = "transit") -> dict:
    """
    Chama a Distance Matrix API e retorna:
      - distance_text (ex: "586 km")
      - duration_text (ex: "10 hours 32 mins")
    """
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
    elem = resp.json()["rows"][0]["elements"][0]
    return {
        "distance_text": elem["distance"]["text"],
        "duration_text": elem["duration"]["text"]
    }

def format_duration(duration_text: str) -> str:
    """
    Converte "X hours Y mins" ou "Y mins" em "HH:MM".
    """
    hours = 0
    mins = 0
    parts = duration_text.split()
    for i, part in enumerate(parts):
        if part.isdigit():
            num = int(part)
            unit = parts[i+1] if i+1 < len(parts) else ""
            if unit.startswith("hour"):
                hours = num
            elif unit.startswith("min"):
                mins = num
    return f"{hours:02d}:{mins:02d}"

def find_latest_csv(raw_dir: str) -> str:
    """
    Procura em raw_dir arquivos 'dados_viacao_cometa_DD_MM_YYYY_HH_MM.csv'
    e retorna o caminho do que tiver o timestamp (do nome) mais recente.
    """
    prefix = "dados_viacao_cometa_"
    suffix = ".csv"
    candidates = []
    for fname in os.listdir(raw_dir):
        if fname.startswith(prefix) and fname.endswith(suffix) and "_enriquecido" not in fname:
            ts_part = fname[len(prefix):-len(suffix)]
            try:
                dt = datetime.strptime(ts_part, "%d_%m_%Y_%H_%M")
                candidates.append((dt, fname))
            except ValueError:
                pass
    if not candidates:
        raise FileNotFoundError(f"Nenhum CSV de RPA encontrado em: {raw_dir}")
    _, latest_fname = max(candidates, key=lambda x: x[0])
    return os.path.join(raw_dir, latest_fname)

def enrich_csv(input_path: str = None, output_path: str = None):
    """
    Lê o CSV de scraping e escreve um novo CSV enriquecido com:
      Origem, Destino, Data, Tipo de assento, Preco, Mensagem_rota_indisp,
      Distance, Duration (HH:MM), Timestamp_Scraped
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir  = os.path.join(base_dir, "raw_data")

    # seleciona o CSV de RPA mais recente, se não fornecido
    if input_path is None:
        input_path = find_latest_csv(raw_dir)

    # define saída padrão
    if output_path is None:
        output_path = input_path.replace(".csv", "_enriquecido.csv")

    print(f"Enriquecendo {os.path.basename(input_path)} -> {os.path.basename(output_path)}")

    with open(input_path,  encoding='utf-8', newline='') as fin, \
         open(output_path, 'w', encoding='utf-8', newline='') as fout:

        reader = csv.DictReader(fin)

        # remove o Timestamp_Scraped que já veio no CSV original
        orig_fields = [f for f in reader.fieldnames if f != "Timestamp_Scraped"]

        # monta o header definitivo, só adicionando o novo Timestamp_Scraped uma vez
        fieldnames = orig_fields + ["Distance", "Duration", "Timestamp_Scraped"]

        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()


        for row in reader:
            data_str = row.get("Data", "")
            try:
                dt_obj = datetime.strptime(data_str, "%d/%m/%Y")
                info = get_distance_duration(
                    row["Origem"], row["Destino"], dt_obj, mode="transit"
                )
                row["Distance"] = info["distance_text"]
                row["Duration"] = format_duration(info["duration_text"])
            except Exception as e:
                row["Distance"] = ""
                row["Duration"] = ""
                print(f"[WARN] falha ao enriquecer {row['Origem']}→{row['Destino']} em {data_str}: {e}")

            row["Timestamp_Scraped"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(row)

if __name__ == "__main__":
    enrich_csv()
