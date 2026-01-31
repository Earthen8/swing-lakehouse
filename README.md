# 📈 Swing Lakehouse: Automated Trading Pipeline

A quantitative data engineering pipeline that automates the search for swing trading opportunities in the Indonesian Stock Market (IDX).

## 🏗 Architecture
* **Orchestrator:** Dagster (Schedules & Assets)
* **Ingestion:** `yfinance` (Scrapes IDX Data)
* **Transformation:** Pandas (Calculates RSI, MACD, Signal Lines)
* **Storage:** PostgreSQL (Data Warehouse)
* **Visualization:** Metabase (Dashboard & Charts)
* **Alerting:** Telegram Bot (Push Notifications)

## 🚀 Features
* **Auto-Ingest:** Runs Mon-Fri at 16:15 WIB.
* **Sector Scanning:** Monitors 35+ High-Alpha stocks (LQ45, Barito Group, etc.).
* **Sniper Mode:** Filters for `RSI < 35` (Oversold) opportunities.
* **Push Alerts:** Sends a Telegram message only when buy signals are found.

## 🛠 Setup
1.  Clone repository.
2.  Create `.env` file with credentials (TELEGRAM_BOT_TOKEN, POSTGRES_USER, etc.).
3.  Run `docker compose up -d`.
4.  Access Dagster at `localhost:3000` and Metabase at `localhost:3001`.
