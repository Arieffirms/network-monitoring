# PROGRESS.md – Status Monitoring Stack PT Baja Perkasa Sentosa

Status Terakhir: **Aktif & Terverifikasi (Production Mode / Router Fisik PT Baja Perkasa Sentosa)**  
Diperbarui oleh: **Romi (Senior DevOps Engineer)**  
Tanggal: **13 November 2026**

---

## 1. Ringkasan Sistem Saat Ini

Stack monitoring difokuskan penuh untuk **Analisa & Monitoring Router MikroTik Fisik Kantor (RB5009UG+S+)** secara riil dan live:

| Service | Container Name | Image Version | Port Binding | Status |
|---|---|---|---|---|
| **Prometheus** | `prometheus` | `prom/prometheus:v3.2.1` | `0.0.0.0:9090` | ✅ Up & Scraping (15s) |
| **SNMP Exporter** | `snmp-exporter` | `prom/snmp-exporter:v0.26.0` | Internal (`9116`) | ✅ Up |
| **Grafana OSS** | `grafana` | `grafana/grafana:11.5.2` | `0.0.0.0:3000` | ✅ Up & Healthy |
| **Router Fisik MikroTik** | `192.168.2.1:161` | `RouterOS 7.22.2 (RB5009)` | `UDP 161` | ✅ Up & Streaming Real Metrics |

*(Seluruh simulator dummy dan script pengacak nilai telah dihapus permanen demi efisiensi dan keamanan sistem produksi).*

---

## 2. Arsitektur & Fitur Monitoring Produksi

### A. Alur Pengumpulan Metrik Jaringan

```mermaid
flowchart LR
    ROUTER["Router MikroTik Fisik BPS (192.168.2.1:161 UDP)"] -->|"SNMP v2c (community: grafana-bps)"| EXP["snmp-exporter :9116"]
    EXP -->|"HTTP /snmp?module=mikrotik"| PROM["Prometheus (scrape 15s)"]
    PROM -->|"PromQL"| GRAF["Grafana OSS :3000"]
    GRAF -->|"Alert > 80 Mbps"| TG["Telegram IT Support Bot"]
```

### B. Interface Fisik PT Baja Perkasa Sentosa yang Termonitor:
- **`ether1-WAN1`** (ISP Utama - Trafik Terakumulasi > 18.3 TB)
- **`ether2-WAN2`** (ISP Cadangan)
- **`ether3-LAN-Office`** (Jaringan Kantor Pusat - Trafik Terakumulasi > 2.2 TB)
- **`ether4-CCTV`** (Jaringan Kamera Keamanan Pabrik)
- **`ether5-SAP`** (Server ERP SAP Manufaktur)
- **`ether6-MES`** (Manufacturing Execution System)
- **`ether7`** & **`ether8-Config`** (Port Manajemen & Cadangan)
- **`sfp-sfpplus1`** (Uplink Fiber Optic 10G)
- **`wg-bps`** (VPN WireGuard Antar-Site BPS)

### C. Dashboard MikroTik Streamlined & Zero "No Data" (Full Advanced)
Dashboard tunggal di folder `Infrastructure` (`uid: mikrotik-snmp-advanced`) dirancang presisi dengan 23 panel aktif berbasis data riil dari Gateway MikroTik RB5009UG+S+:
1. **Router & System Information:** Uptime router, Device Status, Device Errors, System Identity (`MikroTik`), Serial Number, dan Model Router (`RB5009UG+S+ 7.22.2 stable`).
2. **Gateway Specific Metrics:**
   - **Active DHCP Leases:** Jumlah sewa IP aktif perangkat kantor (221 leases).
   - **Board & Package Version:** Versi firmware dan paket RouterOS.
   - **Board Name & Software ID:** Detail lisensi pabrikan.
   - **CPU Temperature:** Sensor suhu CPU aktual onboard (~53°C).
   - **Gateway SNMP Status:** Indikator visual kesehatan koneksi SNMP (UP/DOWN).
3. **Hardware & Resource Utilization:**
   - Gauge indikator CPU Load: Menampilkan rata-rata total beban prosesor serta rincian pemakaian per-core (**Core 1, Core 2, Core 3, Core 4**).
   - Gauge RAM Load (%) dan System Disk Load (%).
   - Grafik timeseries `System Resources Trend`: Menganalisis kurva 4 individual CPU Cores (`CPU Core 1 (%)` s/d `CPU Core 4 (%)`), rata-rata total CPU, RAM, Disk, dan Suhu CPU dengan ringkasan tabel Last & Max.
4. **Network Traffic & Interfaces:**
   - **Network Traffic Basic:** Grafik In/Out bandwidth (bps) dengan variabel `$Interface` otomatis `All` (`.*`) mencakup 11 interface fisik/virtual.
   - **Interface Errors & Discards:** Grafik packet rate errors & drops (pps).
   - **Interfaces Details Table:** Tabel status port, MAC address, link speed, MTU, RX/TX bytes total, link flaps, dan deskripsi/alias port tanpa metrik kosong.

### D. Auto-Provisioning Alerting Telegram
- Rule lonjakan bandwidth `ether1` **> 80 Mbps** aktif di scheduler Grafana (`for: 30s`).
- Target query PromQL menggunakan label `ifName=~"ether1.*"`.
- Format pesan Telegram dirapikan secara profesional menggunakan pemisah rapi, emoji indikator (🚨 / ✅), ringkasan detail unduhan, batas aman, rekomendasi tindakan IT Support, serta direct link ke dashboard.
- Rute koneksi Telegram dikunci menggunakan IPv4 langsung di `docker-compose.yml` (`extra_hosts`) untuk mencegah *timeout* IPv6.

---

## 3. Checklist Validasi & Quality Gates

- [x] **Docker Compose Syntax:** Valid (`docker compose config --quiet`).
- [x] **Prometheus Configuration Syntax:** Valid (`promtool check config` $\rightarrow$ `SUCCESS`).
- [x] **Koneksi Router MikroTik Produksi:** 100% aktif dan sehat (`health: up`, IP `192.168.2.1:161`, auth `grafana_bps`).
- [x] **Dummy Components Removed:** Folder `dummy-snmp` dan seluruh konfigurasi dummy simulator telah dibersihkan.
- [x] **Grafana JSON Syntax:** Semua file `.json` valid sintaks JSON tanpa error schema.
- [x] **Kredensial Grafana:** Teruji dan aktif (`admin` / `Admin123!`).
- [x] **Folder Dashboards Bersih:** Folder kosong `MikroTik Alerts` telah dihapus; aturan alert disatukan ke dalam folder `Infrastructure` bersama dashboard.
- [x] **PromQL Queries:** 100% valid membaca data real-time router RB5009.
- [x] **Live Streaming Timeseries:** Mengalir secara *real-time* dengan `liveNow: true` dan interval refresh 5s.
- [x] **Single Streamlined Dashboard:** Dashboard lama `MikroTik Router Monitoring` telah dihapus; kini hanya menggunakan 1 dashboard utama `MikroTik Monitoring (Full Advanced)` yang telah dirapikan (menghapus seluruh panel No Data seperti Wireless, CAPsMAN, W60G, Modem, Queue, dan POE).
- [x] **SNMP Timeout Hardened:** Scrape timeout disetel ke 25s dan interval 30s untuk menjamin walk SNMP stabil tanpa *context deadline exceeded*.
- [x] **Zero "No Data" Resolution:** Variabel `$Interface` diperbaiki dengan `includeAll: true`, `allValue: ".*"`, dan default `All` sehingga grafik traffic langsung merender 11 interface. Seluruh panel yang tidak didukung hardware RB5009 diganti dengan metrik gateway riil (Active DHCP Leases, CPU Temperature, dan Gateway SNMP Status).
- [x] **Comprehensive Alerting Suite:** Menambahkan 4 aturan alert otomatis di `grafana/provisioning/alerting/rules.yaml`:
  1. *Trafik Tinggi ether1-WAN:* > 80 Mbps
  2. *CPU Load Kritis:* > 80% (rata-rata 4 core)
  3. *RAM Load Kritis:* > 85%
  4. *Indikasi Serangan Flooding (DoS/SYN Flood):* Laju paket masuk > 25.000 pps
- [x] **Dynamic Telegram Notification Template:** Notifikasi Telegram diperbarui di `alerting.yaml` dengan format dinamis menampilkan nama insiden, kategori (Traffic / Resource / Security), tingkat keparahan (Severity), deskripsi metrik, dan tombol akses cepat dashboard.
- [x] **Security Attack Logging & Simulation Guide:** Menyediakan panduan firewall filter MikroTik untuk logging serangan (Port Scan `psd`, Brute-Force SSH/Winbox, TCP SYN Flood) beserta script interaktif [`simulasi_monitoring.py`](file:///home/rapiets/Documents/intern/PT-BAJA-PERKASA-SENTOSA-AND-SENTOSA-HARMONY-STELL/simulasi_monitoring.py) untuk uji lonjakan trafik, port scan attack, dan live terminal monitor.



