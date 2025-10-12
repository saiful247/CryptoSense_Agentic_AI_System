# CryptoAgent: Cryptocurrency Analysis Platform

CryptoAgent is an advanced cryptocurrency analysis platform that provides real-time price data, generates visual charts, and offers financial investment advice for various cryptocurrencies. The platform utilizes AI agents powered by Google's Gemini to deliver comprehensive crypto insights.

## Features

- **Finance Advisor Agent**: Get personalized investment advice for cryptocurrencies including risk assessment, potential returns, and platform recommendations
- **Graph Generator Agent**: Generate visual charts showing cryptocurrency price trends and performance metrics
- **Crypto Price Agent**: Fetch real-time price data including current price, market cap, and price changes over different time periods

## API Documentation

Access the interactive API documentation:

```
http://127.0.0.1:8000/docs
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/saiful247/CryptoIRWA.git
cd CryptoAgent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Environment Configuration

Create a `.env` file in the project root with the following API keys:

```
GEMINI_API_KEY="your_gemini_api_key"
COINMARKETCAP_API_KEY="your_coinmarketcap_api_key"
```

### 6. Run the Application

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## API Endpoints

- **GET /** - Root endpoint with welcome message
- **POST /api/get-crypto-graph** - Generate cryptocurrency price charts
- **POST /api/get-crypto-price** - Get real-time cryptocurrency price data
- **POST /api/get-finance-advice** - Get investment advice for cryptocurrencies

## Technologies Used

- FastAPI - Web framework
- Autogen - AI agent framework
- Google Gemini - AI model
- CoinMarketCap API - Cryptocurrency data
- YFinance - Financial data

## Resources

---

## Docker & Deployment

### Docker Commands

```powershell
# Build the Docker image
docker build -t cryptoagent-app .

# Run the container (mount keys, set env file, expose port)
docker run -d --name cryptoagent-container -p 8000:8000 -v "/e/IRWA/Project/CryptoAgent/keys:/app/keys:ro" --env-file .env cryptoagent-app

# Stop and remove the container
docker stop cryptoagent-container
docker rm cryptoagent-container

# View container logs
docker logs -f cryptoagent-container
```

### Deployment (GCP Cloud Run)

- Deployed via GitHub repo branch with Dockerfile.
- Faced build errors due to `GOOGLE_APPLICATION_CREDENTIALS` usage for Firestore/Vertex AI.

#### Other Issues & Tips

- In `.env`, do **not** wrap values (like `GOOGLE_APPLICATION_CREDENTIALS`, `ALGORITHM`, API keys) in double quotes (`""`). This causes Docker build issues.
- Keep your Dockerfile as simple as possible.
- If deployment fails, check Cloud Run logs for details.

#### Migration Note

- Migrated from Autogen to Vertex AI for broader use cases and model variety. Vertex AI is easier to use for multiple models and scenarios. Autogen is best for chat-like applications, but Vertex AI better fits project needs.
