# ⚙️ Installation Guide — Cloudflare Tunnel Watchdog

This guide explains how to install, configure, and enable the **Cloudflare Tunnel Watchdog** service to automatically run on boot.

---

## 🧰 Prerequisites

Make sure you have:
- Python 3.8 or later
- `pip` installed
- `pm2` and `cloudflared` installed
- A configured `config.yaml` (edit your Wi-Fi SSID, commands, etc.)

---

## 📦 1. Clone and Set Up

```bash
git clone https://github.com/Nivek-C94/cloudflare-tunnel-watchdog.git
cd cloudflare-tunnel-watchdog
pip install -r requirements.txt
```

---

## 🧠 2. Test It Manually

Before enabling it as a service, make sure it runs correctly:

```bash
python watchdog.py
```

You should see logs similar to:

```
💡 Reminder: This service is set to auto-run on boot via systemd (cloudflare-watchdog.service).
🔍 Checking system status...
✅ Site is healthy.
```

If everything works, stop it with `Ctrl + C`.

---

## 🔧 3. Install as a Systemd Service

Copy the included service file to your systemd directory:

```bash
sudo cp cloudflare-watchdog.service /etc/systemd/system/
```

Then edit the service file to use your correct paths and username:

```bash
sudo nano /etc/systemd/system/cloudflare-watchdog.service
```

Modify the following lines:

```
ExecStart=/usr/bin/python3 /home/youruser/cloudflare-tunnel-watchdog/watchdog.py
WorkingDirectory=/home/youruser/cloudflare-tunnel-watchdog
User=youruser
```

---

## 🚀 4. Enable and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflare-watchdog.service
sudo systemctl start cloudflare-watchdog.service
```

To check its status:

```bash
sudo systemctl status cloudflare-watchdog.service
```

---

## 🧾 5. View Logs

Logs are written to both console and file:

```bash
cat /home/youruser/cloudflare-tunnel-watchdog/watchdog.log
```

---

## 🧹 6. Manage the Service

Stop or restart anytime:

```bash
sudo systemctl stop cloudflare-watchdog.service
sudo systemctl restart cloudflare-watchdog.service
```

To disable autostart:

```bash
sudo systemctl disable cloudflare-watchdog.service
```

---

✅ The watchdog will now **automatically monitor your Cloudflare tunnel** and **restart it with PM2 if it fails**, ensuring uptime and Wi-Fi reconnection.