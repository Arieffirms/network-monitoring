# PROGRESS.md – Status Monitoring Stack PT Baja Perkasa Sentosa

Status Terakhir: **Aktif & Terverifikasi (Testing Mode / SNMP Dummy Dinamis)**  
Diperbarui oleh: **Romi (Senior DevOps Engineer)**  
Tanggal: **11 November 2026**

---

## 1. Ringkasan Sistem Saat Ini

Stack monitoring difokuskan penuh untuk **Analisa & Monitoring Router MikroTik (RB750Gr3)** menggunakan simulasi SNMP (*snmp-simulator*) dengan data trafik dinamis (*live counters*) sebelum dihubungkan ke router fisik kantor:

| Service | Container Name | Image Version | Port Binding | Status |
|---|---|---|---|---|
| **Prometheus** | `prometheus` | `prom/prometheus:v3.2.1` | `127.0.0.1:9090` | ✅ Up & Scraping (15s) |
| **SNMP Exporter** | `snmp-exporter` | `prom/snmp-exporter:v0.26.0` | Internal (`9116`) | ✅ Up |
| **Grafana OSS** | `grafana` | `grafana/grafana:11.5.2` | `127.0.0.1:3000` | ✅ Up & Healthy |
| **SNMP Simulator** | `snmp-simulator` | `tandrup/snmpsim:v0.4` | `127.0.0.1:161/udp` | ✅ Up & Serving Live Counters |

---

## 2. Fitur Baru & Peningkatan Layout (Sesuai Referensi Gambar)

### A. Dashboard MikroTik Modern (`/grafana/dashboards/mikrotik.json`)
Mengadopsi tata letak profesional sesuai referensi visual:
1. **Banner Identitas Router:** Hijau penuh di bagian atas menampilkan: `7.14 (stable) RouterOS RB750Gr3 (hEX) • PT Baja Perkasa Sentosa`.
2. **System Overview (4 Panel Sejajar):**
   - **CPU Load (Gauge):** Indikator setengah lingkaran persentase beban CPU dengan ambang batas warna.
   - **Memory Usage (Gauge):** Indikator setengah lingkaran persentase RAM terpakai.
   - **System Uptime (Stat):** Durasi aktif router dengan grafik tren di latar belakang.
   - **Scrape Status (Stat):** Kartu status hijau `OK`.
3. **System History (2 Grafik Sejajar):**
   - **CPU Load History:** Tren persentase CPU dengan tabel legend (*Last, Min, Mean, Max*).
   - **Memory Usage History:** Grafik perbandingan *Used* vs *Free Memory*.
4. **Network Interfaces (Tabel & Trafik Dinamis):**
   - **Tabel Status Port:** Rincian port (`ether1`, `ether2`, `wlan1`), kecepatan link, dan badge hijau status `Up`.
   - **Interface Traffic (RX):** Grafik gelombang download (*smooth line gradient fill*) dengan pembedaan warna tiap port.
   - **Interface Traffic (TX):** Grafik gelombang upload (*smooth line gradient fill*).
   - **Interface Packets (RX & TX):** Grafik tren paket per detik (*pps*).
5. **Variabel Dinamis:** Dropdown filter `$interface` (*All / ether1 / ether2 / wlan1*).

### B. Simulasi SNMP Dinamis — Arsitektur Generator + Simulator

```mermaid
flowchart LR
    GEN["snmp-generator (update tiap 5s)"] -->|"tulis file nilai"| VOL[("volume bps_snmp_dynamic")]
    VOL -->|"cat via subprocess (ro)"| SIM["snmp-simulator :161/udp"]
    SIM --> EXP["snmp-exporter :9116"]
    EXP --> PROM["Prometheus (scrape 15s)"]
    PROM --> GRAF["Grafana (live 5s)"]
    GRAF -->|"alert > 80 Mbps"| TG["Telegram IT Support"]
```

| Komponen | Fungsi |
|---|---|
| **SNMP Simulator** | Menyediakan data OID virtual (`dummy-snmp/data/public.snmprec`). OID statis ditulis langsung; OID dinamis memakai `subprocess` → `cat /usr/local/snmpsim/dynamic/<metric>`. |
| **Dynamic Data Generator** | `dummy-snmp/generator/generator.py` — mengubah nilai dummy tiap 5 detik (random walk halus + pola harian). |
| **SNMP Exporter** | Mengambil OID dari simulator (`module: mikrotik`). |
| **Prometheus** | Scraping setiap 15 detik. |
| **Grafana** | Menampilkan monitoring secara live + alert Telegram. |

Pola data dari generator:
- `ether1` download normal ~15–60 Mbps (bergelombang), upload ~5–15 Mbps.
- Lonjakan acak `ether1` ~85–97 Mbps selama 1,5–4 menit (rata-rata tiap ~5–6 menit) → alert **FIRING** lalu **RESOLVED** sendiri.
- `ether2` (LAN) mengikuti trafik WAN; `wlan1` independen.
- CPU berkorelasi dengan total trafik; RAM, suhu, dan tegangan berfluktuasi pelan.
- Uji manual lonjakan: `docker exec snmp-generator touch /dynamic/FORCE_SPIKE`.

### C. Auto-Provisioning Alerting Telegram
- Rule lonjakan bandwidth `ether1` **> 80 Mbps** aktif di scheduler Grafana (`for: 30s`).
- Target query PromQL diperbaiki menggunakan label `ifName=~"ether1.*"` sesuai standar MIB MikroTik.
- Rute koneksi Telegram dikunci menggunakan IPv4 langsung di `docker-compose.yml` (`extra_hosts`) untuk mencegah *timeout* IPv6.
- Status alert sebelumnya **Firing** terus (trafik dummy konstan ~95 Mbps). Setelah generator aktif, alert hanya firing saat ada lonjakan. Notifikasi ke Telegram IT Support (Chat ID `1510478721`).

### D. Skema Lengkap 40-Panel MikroTik Monitoring (`bps/network-monitoring`)
- Terpasang dashboard komprehensif `MikroTik Monitoring (Full Advanced)` (`mikrotik-monitoring.json`) yang mencakup:
  - Total SNMP Walk time & Scrape PDUs
  - System Info: Board ver, Package ver, Serial Number, CPU Frequency, POE Status/Current/Voltage
  - 4 Panel Gauges: CPU Load, RAM Load, Disk Load, CPU Temperature
  - Comprehensive Network Interfaces Table & Basic Traffic
  - Wireless (Wi-Fi client count, Tx CCQ, Noise, Signal-to-Noise Heatmap)
  - CAPsMAN & W60G Panels
  - Simple Queue & Tree Queue Monitoring

---

## 3. Checklist Validasi & Quality Gates

- [x] **Docker Compose Syntax:** Valid (`docker compose config --quiet`).
- [x] **SNMP OID Order:** Terurut rapi secara numerik (`snmpsim` tidak ada error *OID not increasing*).
- [x] **Grafana JSON Syntax:** Semua file `.json` valid sintaks JSON tanpa error schema.
- [x] **Kredensial Grafana:** Teruji dan aktif (`Admin` / `Admin123!`).
- [x] **PromQL Queries:** 100% valid tanpa fungsi `sin()` yang menyebabkan error/tanda seru `!`.
- [x] **Live Streaming Timeseries:** Mengalir secara *real-time* dengan `liveNow: true` dan interval refresh 5s.
- [x] **Alert Triggering:** Status `Alerting` berhasil terpicu dari lonjakan data dummy ~95 Mbps.

