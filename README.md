# Monitoring MikroTik Router – PT Baja Perkasa Sentosa

Sistem monitoring real-time untuk **Router Gateway MikroTik (RB5009UG+S+)** kantor PT Baja Perkasa Sentosa menggunakan **Prometheus**, **SNMP Exporter**, dan **Grafana OSS** berbasis Docker Compose.

---

## 1. Spesifikasi Jaringan & IP Host

| Parameter | Keterangan / Nilai |
|---|---|
| **IP Host Monitoring (Kabel LAN)** | **`192.168.2.175`** (Interface `enp7s0`) |
| **IP Gateway MikroTik** | **`192.168.2.1`** (Port UDP `161`) |
| **Model Router** | RouterOS RB5009UG+S+ (v7.22.2 stable) |
| **SNMP Community** | `grafana-bps` (SNMP v2c) |
| **Web UI Grafana** | [http://localhost:3000](http://localhost:3000) atau `http://192.168.2.175:3000` |
| **Login Grafana** | Username: `admin` \| Password: `Admin123!` |

> [!IMPORTANT]
> **Catatan Pengaturan IP MikroTik (`192.168.2.175`):**
> * Router MikroTik dikonfigurasi pada menu **IP > SNMP > Communities > grafana-bps**.
> * Kolom **Addresses** diisi **`192.168.2.175`** (IP kabel LAN laptop/server monitoring).
> * *Tips:* Jika ingin monitoring tetap bisa berjalan saat berpindah ke Wi-Fi kantor, ubah kolom **Addresses** di Winbox menjadi **`192.168.2.0/24`** atau `0.0.0.0/0`.

---

## 2. Cara Menjalankan Sistem

### A. Menjalankan Monitoring (Background)
Pastikan service Docker aktif, lalu jalankan:
```bash
sudo systemctl start docker
docker compose up -d
```

### B. Mengecek Status Container
```bash
docker compose ps
```
Pastikan 3 container berstatus **Up**:
* `grafana` (Port 3000)
* `prometheus` (Port 9090)
* `snmp-exporter` (Internal 9116)

### C. Menghentikan Monitoring
```bash
docker compose down
```

---

## 3. Fitur Utama Dashboard Grafana

Dashboard **`MikroTik Monitoring (Full Advanced)`** terdiri dari:
1. **5 KPI Utama:** Model RouterOS, Uptime, Status SNMP (UP/DOWN), Suhu CPU (56°C), dan Active DHCP Leases (214+ perangkat).
2. **System Resources Trend:** Grafik pemakaian 4 Core CPU individual (`Core 1` s/d `Core 4`), RAM, Disk, dan Suhu CPU.
3. **Network Traffic Basic:** Grafik unduhan dan unggahan bandwidth (bps) untuk seluruh 11 interface fisik/virtual.
4. **Network Anomaly & Security Threats:** Deteksi dini lonjakan paket (DoS/SYN Flood), broadcast storm, paket drop, dan error kabel fisik (CRC).
5. **Interfaces Table:** Detail status port up/down, MAC address, link speed, MTU, dan link flaps.

---

## 4. Script Uji Coba & Simulasi

Untuk menguji lonjakan trafik atau log serangan firewall secara aman:
```bash
python3 simulasi_monitoring.py
```
Pilihan menu:
* `1` : Simulasi Trafik Tinggi (> 80 Mbps)
* `2` : Simulasi Serangan Port Scan (Cek log di Winbox)
* `3` : Panduan Beban CPU 100%
* `4` : Live Monitor Metrik di Terminal
