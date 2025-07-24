import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# 1) Carrega e valida a chave
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Defina GOOGLE_API_KEY no .env")

# 2) Função para buscar distância e duração
def get_distance_duration(origin: str, destination: str, departure_dt: datetime,
                          mode: str = "transit") -> dict:
    """
    Retorna {'distance_text', 'duration_text'} para o trecho indicado.
    """
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    # departure_time em segundos desde epoch
    departure_time = int(departure_dt.timestamp())
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "departure_time": departure_time,
        "key": API_KEY
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    elem = data["rows"][0]["elements"][0]
    return {
        "distance_text": elem["distance"]["text"],
        "duration_text": elem["duration"]["text"]
    }

# 3) Uso de exemplo
if __name__ == "__main__":
    origem = "Belo Horizonte - MG"
    destino = "São Paulo - SP"
    agora = datetime.now()
    resultado = get_distance_duration(origem, destino, agora)
    print(f"Distância: {resultado['distance_text']}")
    print(f"Duração:   {resultado['duration_text']}")
