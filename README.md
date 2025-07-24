# Viagem RPA & Enriquecimento por API

Este repositório contém dois scripts em Python para:

1. **`cometa_rpa.py`** – faz RPA via Selenium para coletar ofertas de viagens de ônibus no site da Viação Cometa e gera um CSV com os dados brutos.
2. **`matrix_api_google.py`** – lê o CSV mais recente gerado pelo RPA, chama a Google Distance Matrix API para enriquecer cada registro com distância e duração, e gera um CSV “\_enriquecido”.

---

## 📋 Pré‑requisitos

* **Python 3.12+**
* **Chrome browser** compatível
* **ChromeDriver** instalado e disponível no `PATH`
* **Conta Google Cloud** com a **Distance Matrix API** habilitada
* **Arquivo `.env`** com sua chave de API do Google

---

## 🛠️ Instalação

1. **Clone** este repositório:

   ```bash
   git clone https://seu-repo.git
   cd bnit_case
   ```

2. Crie e ative um **venv** (recomendado):

   ```bash
   python -m venv .venv
   source .venv/bin/activate    # Linux/macOS
   .venv\Scripts\activate       # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Copie o template de variáveis de ambiente e preencha sua chave:

   ```bash
   cp .env_example .env
   ```

   Edite `.env` para incluir:

   ```
   GOOGLE_API_KEY=SEU_API_KEY_AQUI
   ```

---

## ⚙️ Uso

### 1. RPA de scraping (`cometa_rpa.py`)

Executa um fluxo Selenium que:

* Abre o Chrome
* Navega em três rotas predefinidas
* Coleta ofertas para 3 dias a partir de hoje
* Gera CSV em

  ```
  raw_data/dados_viacao_cometa_rpa_DD_MM_YYYY_HH_MM.csv
  ```

```bash
python cometa_rpa.py
```

**Colunas geradas:**

* Origem
* Destino
* Data
* Tipo de assento
* Preco
* Mensagem\_rota\_indisp
* Timestamp\_Scraped

Você pode alterar `routes` e `NUM_DIAS` diretamente no script.

---

### 2. Enriquecimento por API (`matrix_api_google.py`)

Detecta automaticamente o CSV mais recente em `raw_data/` (prefixo `dados_viacao_cometa_…csv`), chama a Google Distance Matrix API e gera:

```
raw_data/dados_viacao_cometa_rpa_DD_MM_YYYY_HH_MM_enriquecido.csv
```

```bash
python matrix_api_google.py
```

* **Formata** `"X hours Y mins"` em `"HH:MM"`, ideal para dashboards.
* **Adiciona** ao CSV enriquecido as colunas:

  * `Distance` (ex: “586 km”)
  * `Duration` (ex: “10:32”)
  * `Timestamp_Scraped` (atualizado)

---

## 📁 Estrutura de pastas

```
.
├── cometa_rpa.py
├── matrix_api_google.py
├── requirements.txt
├── .env_example
└── raw_data/
    ├── dados_viacao_cometa_rpa_…csv
    └── dados_viacao_cometa_rpa_…_enriquecido.csv
```

* **`raw_data/`**: destino dos CSVs de entrada (RPA) e saída (enriquecido).
* **`.env_example`**: template para variáveis de ambiente.

---

## 🔧 Dicas

* **ChromeDriver**: verifique se a versão bate com seu Chrome.
* **Delimitador**: se seu CSV usar `;`, ajuste:

  ```python
  reader = csv.DictReader(fin, delimiter=';')
  ```
* **Headless mode** (opcional em `cometa_rpa.py`):

  ```python
  chrome_option.add_argument('--headless')
  ```

---
