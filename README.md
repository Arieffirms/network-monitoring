# Monitoring MikroTik Router

Sistem monitoring real-time untuk **Router Gateway MikroTik (RB5009UG+S+)** menggunakan **Prometheus**, **SNMP Exporter**, dan **Grafana OSS** berbasis Docker Compose.

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
| **Telegram Alerting** | **Opsional** (bisa dikosongkan di `.env` jika hanya ingin visual monitoring) |

> [!IMPORTANT]
> **Catatan Pengaturan IP MikroTik (`192.168.2.175`):**
> * Router MikroTik dikonfigurasi pada menu **IP > SNMP > Communities > grafana-bps**.
> * Kolom **Addresses** diisi **`192.168.2.175`** (IP kabel LAN laptop/server monitoring).
> * *Tips:* Jika ingin monitoring tetap bisa berjalan saat berpindah ke Wi-Fi kantor, ubah kolom **Addresses** di Winbox menjadi **`192.168.2.0/24`** atau `0.0.0.0/0`.

---

## 2. Cara Menjalankan Sistem

### A. Persiapan File Environment (.env)
Bagi pengguna baru atau setelah *clone* repositori, salin file template `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```
*(Sesuaikan `HOST_LAN_IP` jika IP kabel LAN Anda berbeda, dan isi token Telegram jika ingin notifikasi bot aktif).*

### B. Menjalankan Monitoring (Background)
Pastikan service Docker aktif, lalu jalankan:
```bash
docker compose up -d
```

### C. Mengecek Status Container
```bash
docker compose ps
```
Pastikan 3 container berstatus **Up**:
* `grafana` (Port 3000)
* `prometheus` (Port 9090)
* `snmp-exporter` (Internal 9116)

### D. Menghentikan Monitoring
```bash
docker compose down
```

---

## 3. Panduan Penggunaan Sehari-hari (Step-by-Step)

### Langkah 1: Sambungkan Kabel LAN
* Pastikan kabel LAN laptop/server tercolok ke jaringan kantor (mendapatkan IP **`192.168.2.175`**).
* *(Opsional)* Jika menggunakan Wi-Fi, pastikan opsi **Addresses** di Winbox sudah diubah ke `192.168.2.0/24`.

### Langkah 2: Nyalakan Stack Container
Buka terminal dan jalankan:
```bash
sudo systemctl start docker && docker compose up -d
```

### Langkah 3: Buka & Login ke Grafana
1. Buka browser (Chrome/Firefox/Edge) dan akses:
   👉 **[http://localhost:3000](http://localhost:3000)** *(atau `http://192.168.2.175:3000` dari PC lain)*.
2. Masukkan kredensial:
   * **Username:** `admin`
   * **Password:** `Admin123!`
3. Buka menu **Dashboards** $\rightarrow$ buka folder **Infrastructure** $\rightarrow$ klik **MikroTik Monitoring (Full Advanced)**.

### Langkah 4: Cara Membaca & Menganalisis Dashboard
* **1. Memeriksa Status Kesehatan Gateway (Header Atas):**
  * Pastikan kotak **Gateway SNMP Status** berwarna **HIJAU (UP)**.
  * Periksa **CPU Temperature** (normal di rentang 50–60 °C).
  * Periksa **Active DHCP Leases** untuk melihat total perangkat yang sedang terhubung.
* **2. Memantau Beban Hardware (System Resources Trend):**
  * Perhatikan kurva pemakaian 4 Core CPU (`Core 1` s/d `Core 4`) dan RAM. Jika salah satu core naik $> 80\%$, cek proses router via Winbox.
* **3. Memantau Bandwidth Jaringan (Network Traffic Basic):**
  * Gunakan dropdown **Interface** di kiri atas untuk memilih port tertentu (misal: `ether1-WAN1` untuk internet utama, `ether3-LAN-Office`, atau `ether5-SAP`).
  * Ganti rentang waktu di pojok kanan atas (*Last 30m*, *Last 1h*, *Last 6h*) untuk melihat tren grafik unduhan/unggahan.
* **4. Deteksi Dini Kerusakan & Serangan (Network Anomaly & Errors):**
  * Perhatikan garis **Physical Link Errors / CRC**: Nilai normal adalah **0**. Jika naik $> 0$, segera cek fisik kabel LAN atau switch kantor karena ada indikasi kabel terjepit/rusak.
  * Perhatikan garis **Total Ingress Packet Rate**: Jika melonjak drastis ke puluhan ribu paket/detik, ada indikasi serangan flood/DoS.

---

## 4. Fitur Utama Dashboard Grafana

Dashboard **`MikroTik Monitoring (Full Advanced)`** terdiri dari:
1. **5 KPI Utama:** Model RouterOS, Uptime, Status SNMP (UP/DOWN), Suhu CPU (56°C), dan Active DHCP Leases (214+ perangkat).
2. **System Resources Trend:** Grafik pemakaian 4 Core CPU individual (`Core 1` s/d `Core 4`), RAM, Disk, dan Suhu CPU.
3. **Network Traffic Basic:** Grafik unduhan dan unggahan bandwidth (bps) untuk seluruh 11 interface fisik/virtual.
4. **Network Anomaly & Security Threats:** Deteksi dini lonjakan paket (DoS/SYN Flood), broadcast storm, paket drop, dan error kabel fisik (CRC).
5. **Interfaces Table:** Detail status port up/down, MAC address, link speed, MTU, dan link flaps.

---

## 5. Script Uji Coba & Simulasi

Untuk menguji lonjakan trafik atau log serangan firewall secara aman:
```bash
python3 simulasi_monitoring.py
```
Pilihan menu:
* `1` : Simulasi Trafik Tinggi (> 80 Mbps)
* `2` : Simulasi Serangan Port Scan (Cek log di Winbox)
* `3` : Panduan Beban CPU 100%
* `4` : Live Monitor Metrik di Terminal

