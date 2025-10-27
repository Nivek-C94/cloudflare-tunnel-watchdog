# 🌐 Cloudflare Tunnel Watchdog

A **self-healing watchdog** that monitors a local Cloudflare tunnel and your PM2 services. Automatically reconnects Wi-Fi and restarts services if the tunnel or site goes down.

---

## 🚀 Features

- Detects local site downtime via HTTP checks
- Restarts `cloudflared` tunnel and `pm2` services when down
- Detects and recovers from internet loss by reconnecting Wi-Fi
- Periodically rechecks connection and restores services
- Logs all events to both console and file (`watchdog.log`)
- Dynamic config reloading — edit `config.yaml` without restarting

---

## 🧩 Configuration

Edit **`config.yaml`**:

```yaml
target_url: "http://localhost:8787"
check_interval: 30  # seconds
failure_threshold: 3
wifi_network: "YourWiFiSSID"
actions:
  on_internet_down:
    - "nmcli device wifi connect YourWiFiSSID"
    - "sleep 10"
  on_site_down:
    - "pm2 restart all"
    - "cloudflared tunnel restart mytunnel"
  on_recovery:
    - "echo '✅ Services recovered successfully.'"
```

---

## ⚙️ Setup

```bash
git clone https://github.com/Nivek-C94/cloudflare-tunnel-watchdog.git
cd cloudflare-tunnel-watchdog
pip install -r requirements.txt
```

---

## ▶️ Run

```bash
python watchdog.py
```

You can also run it persistently via PM2 or systemd:

```bash
pm2 start watchdog.py --name tunnel-watchdog --interpreter python3
```

---

## 🧠 Logs

Logs are stored in `watchdog.log` with timestamps and also printed to console.

---

## 🧰 Dependencies

- Python 3.8+
- `requests`
- `pyyaml`
- PM2 & Cloudflared installed on system

---

## 📜 License

MIT License © 2025 Kevin Carlisle