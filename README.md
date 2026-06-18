This is a project to extract 2FA codes from emails from Bambu Labs to share with a wider team over discord

To use this on your system you must change run.sh to have the correct PROJECT_DIR

Additionally you must create a systemd service and a systemd timer

Example Service and Timer Below

---

**bambu-code-sender.service**


[Unit]
Description=Bambu Code Sender

[Service]
Type=oneshot
WorkingDirectory=/home/mx/xProject/bambu_code_sender
ExecStart=/home/mx/xProject/bambu_code_sender/venv/bin/python /home/mx/xProject/bambu_code_sender/main.py
User=mx
Group=mx

---

**bambu-code-sender.timer**


[Unit]
Description=Run Bambu Code Sender every 10 seconds

[Timer]
OnBootSec=30
OnUnitActiveSec=10
AccuracySec=1
Unit=bambu-code-sender.service

[Install]
WantedBy=timers.target
