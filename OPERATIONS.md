# 📘 Operator's Manual: Swing Lakehouse

**System Status:** Production ✅  
**Server:** `terra` (Ubuntu)  
**Timezone:** UTC (Code) / WIB (Server)

This document serves as the comprehensive guide for maintaining, configuring, and troubleshooting the Swing Lakehouse trading system.

---

## 🔐 1. System Access & Security

The system uses a "Split Access" architecture for security.

### **A. Visualization Dashboard (Read-Only)**
* **URL:** `https://bi.earthen.my.id`
* **Platform:** Metabase
* **Use for:** Viewing charts, RSI tables, and historical signals.
* **Access:** Private (Requires Metabase Admin Login).

### **B. Admin Control Plane (Private)**
* **URL:** `http://localhost:3000` (Via Tunnel)
* **Platform:** Dagster
* **Use for:** Manually triggering runs, debugging logs, changing assets.
* **Security:** Hidden behind a firewall. You **must** use an SSH tunnel to access it.

#### **Dagster Access Method:**
The primary workstation is configured to automatically establish the port forwarding tunnel upon connection.

1.  **Open Terminal:**
    Run the standard connection command:
    ```bash
    ssh terra
    ```
    *(This command automatically maps Server Port 3008 -> Local Port 3000).*

2.  **Open Browser:**
    Navigate to [http://localhost:3000](http://localhost:3000).

#### **Configuration Reference (`~/.ssh/config`)**
For reference, the automatic tunneling is handled via the SSH configuration file on the client machine:

```text
Host terra
    HostName 100.xx.xx.xx      # Tailscale IP
    User earthen
    LocalForward 3000 127.0.0.1:3008

---

## ⚙️ 2. Configuration Guide

### **A. Managing the Watchlist**
**Goal:** Add new stock tickers (e.g., `BBCA.JK`) to the scanner.

1.  **Edit the Asset File:**
    ```bash
    nano ~/projects/swing-lakehouse/ingestion/assets.py
    ```
2.  **Modify the List:**
    Find `TARGET_TICKERS = [...]` and add your stock string.
    * *Requirement:* Must end with `.JK` (Indonesian market).
3.  **Apply Changes:**
    * Go to Dagster UI (`localhost:3000`).
    * Click **"Reload Definitions"** (Top Right corner).
    * *No server restart required.*

### **B. Changing the Schedule**
**Goal:** Change the auto-run time (Default: Mon-Fri at 16:15 WIB).

1.  **Edit the Repo File:**
    ```bash
    nano ~/projects/swing-lakehouse/repository.py
    ```
2.  **Update Cron Schedule:**
    Find `cron_schedule="15 9 * * 1-5"`.
    * **Important:** This uses **UTC Time**.
    * *Formula:* Desired WIB Time - 7 Hours = UTC Time.
    * *Example:* 16:15 WIB = 09:15 UTC.
3.  **Apply Changes:**
    * Go to Dagster UI -> **Overview** -> **Schedules**.
    * Toggle the switch **OFF**, wait 5 seconds, then toggle **ON**.

### **C. Adjusting Strategy (RSI Logic)**
**Goal:** Make the scanner more aggressive (e.g., RSI < 40) or conservative (RSI < 30).

1.  **Edit the Logic:**
    ```bash
    nano ~/projects/swing-lakehouse/ingestion/assets.py
    ```
2.  **Find the Trigger:**
    Scroll to the `telegram_alerts` function.
3.  **Modify SQL:**
    Change the line: `WHERE "RSI" < 35` to your desired threshold.
4.  **Apply Changes:**
    * Click **"Reload Definitions"** in Dagster UI.

---

## 🔑 3. Managing Secrets

**Goal:** Update Telegram Tokens or Database Passwords.

1.  **Edit the Environment File:**
    ```bash
    nano ~/projects/swing-lakehouse/.env
    ```
2.  **Update Values:**
    * `TELEGRAM_BOT_TOKEN=...`
    * `TELEGRAM_CHAT_ID=...`
3.  **Restart System (Required):**
    Secrets are loaded only on startup. You must restart the containers.
    ```bash
    docker compose restart
    ```

---

## 🛠 4. Maintenance & Troubleshooting

### **Check System Health**
**Goal:** To see if containers are alive and which ports they are using ->
    ```bash
    cd ~/projects/swing-lakehouse
    docker compose ps
    ```
* **Expected Output:** lake_bi (Port 3007), dagster_webserver (Port 3008), timescaledb (Port 5432).

### **View Error Logs**
**Goal:** If the Telegram bot is silent or data is missing ->
    ```bash
    docker compose logs -f dagster_daemon
    ```
* **Tip:** Press Ctrl+C to exit the logs.

### **Common Issues & Fixes**
| Issue | Cause | Fix |
| :----- | :----- | :----- |
| **"Unsynced" in UI** | Code changed but Dagster didn't reload. | Click "Reload Definitions" in UI. |
| **Bad Gateway (502)** | Cloudflare lost track of Metabase. | Check if `lake_bi` is running. Ensure Cloudflare tunnel points to `localhost:3007`. |
| **Connection Refused** | SSH Tunnel is closed. | Re-run the `ssh -L` command on your laptop. |
| **Bot Silent** | Market rally (No RSI < 35). | Check "Runs" tab in Dagster. If green, system is fine, just no opportunities. |

---

## 🛑 5. Emergency Stop/Start

### **To Completely Stop the System:**
```bash
docker compose down
```

### **To Start/Rebuild the System:** (Use this if you change the Python code structure or add new libraries).
```bash
docker compose up -d --build
```