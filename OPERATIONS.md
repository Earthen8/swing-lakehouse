# 📘 Operator's Manual: Swing Lakehouse

This document explains how to maintain, configure, and troubleshoot the trading system.

---

## 1. Managing the Watchlist (Stocks)
**Goal:** Add or remove stocks from the scanner.

1.  **Open the file:**
    `nano ingestion/assets.py`
2.  **Find the list:**
    Look for the variable `TARGET_TICKERS = [...]`.
3.  **Edit:**
    Add new tickers ending in `.JK` (e.g., `"BBCA.JK"`).
4.  **Apply Changes:**
    * Go to Dagster UI (`bi.earthen.my.id`).
    * Click **"Reload Definitions"** (Top Right).
    * *No server restart required.*

---

## 2. Changing the Schedule
**Goal:** Change when the system runs (Default: Mon-Fri at 16:15 WIB).

1.  **Open the file:**
    `nano repository.py`
2.  **Find the Schedule:**
    Look for `cron_schedule="15 9 * * 1-5"`.
    * *Note: This is in UTC time.* (09:15 UTC = 16:15 WIB).
3.  **Update the Cron String:**
    * Example (8:00 AM WIB): `"0 1 * * 1-5"`
4.  **Apply Changes:**
    * Go to Dagster UI -> **Overview** -> **Schedules**.
    * Toggle the switch **OFF** and then **ON** again.

---

## 3. Adjusting Strategy (RSI Limits)
**Goal:** Change the "Oversold" threshold (e.g., from 35 to 30).

1.  **Open the file:**
    `nano ingestion/assets.py`
2.  **Find the Alert Asset:**
    Scroll to the bottom function `def telegram_alerts():`.
3.  **Edit the SQL Query:**
    Change `WHERE "RSI" < 35` to your desired number.
4.  **Apply Changes:**
    * Click **"Reload Definitions"** in Dagster UI.

---

## 4. Server Maintenance
**Goal:** Restart or check the health of the system.

* **Check Status:**
    ```bash
    docker compose ps
    ```
* **Restart Everything:**
    (Use this if the server acts weird or after editing `.env` secrets).
    ```bash
    docker compose restart
    ```
* **View Logs (Debug):**
    ```bash
    docker compose logs -f dagster_daemon
    ```

---

## 5. Troubleshooting
* **"Unsynced" in Dagster:**
    * **Fix:** Click "Reload Definitions" in the UI.
* **Telegram not sending:**
    * **Check:** Is the market open? Did any stock actually hit RSI < 35?
    * **Test:** Manually materialize the `telegram_alerts` asset in Dagster to see the output log.
