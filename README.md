# CryptoAgent: Cryptocurrency Analysis Platform

CryptoAgent is an advanced cryptocurrency analysis platform that provides real-time price data, generates visual charts, and offers financial investment advice for various cryptocurrencies. The platform utilizes AI agents powered by Google's Vertex AI to deliver comprehensive crypto insights.

## Features

- **Finance Advisor Agent**: Get personalized investment advice for cryptocurrencies including risk assessment, potential returns, and platform recommendations
- **Graph Generator Agent**: Generate visual charts showing cryptocurrency price trends and performance metrics
- **Crypto Price Agent**: Fetch real-time price data including current price, market cap, and price changes over different time periods

## Live Application

The application is deployed and available at:

```
https://cryptoirwa-frontend-1088335055755.asia-southeast1.run.app/
```

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

Create a `.env` file in the project root with the following configuration:

```env
# Vertex AI Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
PROJECT_ID=your-gcp-project-id
LOCATION=your-gcp-region

# API Keys
COINMARKETCAP_API_KEY=your_coinmarketcap_api_key

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# GCP Storage
GCS_BUCKET_NAME=your-gcs-bucket-name

# Firestore Configuration
FIRESTORE_COLLECTION_NAME=your-firestore-collection
```

### 6. Run the Application

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## Technologies Used

- **FastAPI** - Web framework
- **Google Vertex AI** - AI agent framework and models
  - **Imagen 4.0 (imagen-4.0-generate-001)** - AI image generation for NFT creation
  - **Gemini 2.5 Flash (gemini-2.5-flash)** - Advanced language model for analysis and advice
- **LangGraph** - Agent workflow orchestration and state management
- **Google Cloud Run** - Serverless deployment platform
- **Google Cloud Storage (GCS)** - File storage
- **Google Firestore** - NoSQL document database
- **Docker** - Containerization
- **JWT** - Authentication and authorization
- **CoinMarketCap API** - Cryptocurrency data
- **YFinance** - Financial data

## Architecture

- **Vertex AI Agentic System**: Uses Google's Vertex AI for intelligent cryptocurrency analysis
- **GCP Cloud Run**: Serverless deployment for scalable application hosting
- **Docker**: Containerized deployment for consistency across environments
- **GCP Bucket**: Cloud storage for static assets and generated charts
- **Firestore**: NoSQL database for storing user data and analysis results
- **JWT Authentication**: Secure token-based authentication system

## Resources

---

## Docker & Deployment

### Docker Commands

```powershell
# Build the Docker image
docker build -t cryptoagent-app .

# Run the container locally
docker run -d --name cryptoagent-container -p 8000:8000 --env-file .env cryptoagent-app

# Stop and remove the container
docker stop cryptoagent-container
docker rm cryptoagent-container

# View container logs
docker logs -f cryptoagent-container
```

### Deployment (GCP Cloud Run)

The application is deployed on Google Cloud Run with the following features:

- Automatic scaling based on traffic
- Integrated with GCP services (Vertex AI, Firestore, Cloud Storage)
- Secure JWT-based authentication
- Docker containerization for consistent deployment

#### Environment Variables for Deployment

Ensure the following environment variables are set in Cloud Run:

- `PROJECT_ID`
- `LOCATION`
- `COINMARKETCAP_API_KEY`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `GCS_BUCKET_NAME`
- `FIRESTORE_COLLECTION_NAME`

#### Service Account Configuration

- **Do NOT upload service account credentials to Cloud Run**
- Instead, select the service account that your Vertex AI uses in the Cloud Run service configuration
- GCP Cloud Run will automatically detect and use the selected service account
- Required permissions for the service account: Vertex AI User, Firestore User, Storage Object Admin

#### Other Issues & Tips

- In `.env`, do **not** wrap values (like `GOOGLE_APPLICATION_CREDENTIALS`, `ALGORITHM`, API keys) in double quotes (`""`). This causes Docker build issues.
- Keep your Dockerfile as simple as possible.
- If deployment fails, check Cloud Run logs for details.

## Migration Notes

- **Migrated from Autogen to Vertex AI**: Vertex AI provides better integration with GCP services, more model variety, and easier deployment for production environments
- **Cloud-Native Architecture**: Fully integrated with Google Cloud Platform for scalability and reliability
- **Secure Authentication**: Implemented JWT-based authentication for secure API access
