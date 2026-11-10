# Requirements – Monitoring Stack (Prometheus + Grafana) dengan Docker

**Proyek:** IT Support – PT Baja Perkasa Sentosa & Sentosa Harmony Steel
**Tujuan:** Menyediakan sistem monitoring untuk server & jaringan kantor menggunakan **Prometheus** (pengumpul metrik) dan **Grafana** (visualisasi/dashboard), dijalankan dengan **Docker Compose**.

---

## Daftar Tugas Utama

1. Membuat Prometheus
2. Membuat Grafana

---

## 0. Prasyarat (Prerequisites)

| No | Kebutuhan | Keterangan |
|----|-----------|------------|
| 0.1 | Docker Engine | Terinstall dan berjalan (`docker --version`) |
| 0.2 | Docker Compose v2 | Plugin `docker compose` (`docker compose version`) |
| 0.3 | Port tersedia | `9090` (Prometheus), `3000` (Grafana), `9100` (Node Exporter) tidak dipakai aplikasi lain |
| 0.4 | Resource minimum host | 2 CPU, 2 GB RAM, 10 GB disk kosong |
| 0.5 | Akses jaringan | Host monitoring dapat menjangkau perangkat/server yang akan dimonitor |

---

## 1. Membuat Prometheus

### 1.1 Kebutuhan Fungsional
- [ ] **P-01** Prometheus berjalan sebagai container dari image resmi `prom/prometheus` dengan **tag versi tetap** (contoh: `v3.5.0`, jangan `latest`).
- [ ] **P-02** Konfigurasi dibaca dari file `prometheus/prometheus.yml` yang di-mount ke container (read-only).
- [ ] **P-03** Prometheus melakukan scrape terhadap dirinya sendiri (`job_name: prometheus`, target `localhost:9090`).
- [ ] **P-04** Menambahkan **Node Exporter** (`prom/node-exporter`) untuk metrik host: CPU, RAM, disk, network.
- [ ] **P-05** Prometheus melakukan scrape ke Node Exporter (`job_name: node`, target `node-exporter:9100`).
- [ ] **P-06** *(Opsional)* Menambahkan **cAdvisor** untuk metrik per-container Docker.
- [ ] **P-07** *(Opsional)* Menambahkan **Blackbox Exporter** untuk cek ping/HTTP ke perangkat jaringan kantor (router, switch, server, website) – mendukung tugas *"Setup dan Cek Jaringan Kantor"*.
- [ ] **P-08** Interval scrape global: `15s`; retensi data: `15d` (via flag `--storage.tsdb.retention.time=15d`).
- [ ] **P-09** Web UI Prometheus dapat diakses di `http://<ip-host>:9090`.

### 1.2 Kebutuhan Teknis
- Data Prometheus disimpan di **named volume** `prometheus_data` agar tidak hilang saat container di-restart/dihapus.
- Container memakai `restart: unless-stopped`.
- Semua service terhubung ke satu **Docker network** yang sama (contoh: `monitoring`).

### 1.3 Kriteria Selesai (Acceptance Criteria)
- [ ] Halaman `http://<ip-host>:9090/targets` menampilkan semua target berstatus **UP**.
- [ ] Query `up` di Prometheus mengembalikan nilai `1` untuk setiap job.
- [ ] Query `node_memory_MemAvailable_bytes` mengembalikan data.
- [ ] Setelah `docker compose down` lalu `up -d`, data historis masih ada.

---

## 2. Membuat Grafana

### 2.1 Kebutuhan Fungsional
- [ ] **G-01** Grafana berjalan sebagai container dari image resmi `grafana/grafana` dengan **tag versi tetap** (contoh: `12.1.0`).
- [ ] **G-02** Web UI Grafana dapat diakses di `http://<ip-host>:3000`.
- [ ] **G-03** Username & password admin **tidak hardcode** di `docker-compose.yml`, melainkan dari file `.env` (`GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`).
- [ ] **G-04** Datasource Prometheus dibuat **otomatis** lewat provisioning (`grafana/provisioning/datasources/datasource.yml`) dengan URL `http://prometheus:9090`.
- [ ] **G-05** Dashboard dibuat otomatis lewat provisioning (`grafana/provisioning/dashboards/`), minimal:
  - **Node Exporter Full** (Grafana Dashboard ID `1860`) – monitoring host.
  - *(Opsional)* Dashboard cAdvisor / Docker containers.
  - *(Opsional)* Dashboard Blackbox Exporter (status perangkat jaringan).
- [ ] **G-06** Sign-up user baru dimatikan (`GF_USERS_ALLOW_SIGN_UP=false`).

### 2.2 Kebutuhan Teknis
- Data Grafana disimpan di **named volume** `grafana_data`.
- Grafana `depends_on` Prometheus.
- Container memakai `restart: unless-stopped`.

### 2.3 Kriteria Selesai (Acceptance Criteria)
- [ ] Bisa login ke Grafana memakai kredensial dari `.env`.
- [ ] Menu **Connections → Data sources** menampilkan Prometheus dan tombol *Test* berhasil (hijau).
- [ ] Dashboard Node Exporter tampil dengan data CPU/RAM/Disk/Network yang terisi.
- [ ] Dashboard & datasource tetap ada setelah container dibuat ulang.

---

## 3. Struktur Folder yang Diharapkan

```
.
├── docker-compose.yml
├── .env                    # TIDAK di-commit (masukkan ke .gitignore)
├── .env.example            # Template variabel, boleh di-commit
├── prometheus/
│   └── prometheus.yml
├── blackbox/               # (opsional)
│   └── blackbox.yml
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasource.yml
        └── dashboards/
            ├── dashboard.yml
            └── node-exporter-full.json
```

> **Catatan:** File `dockerfile` **tidak diperlukan** karena semua service memakai image resmi. Konfigurasi cukup lewat `docker-compose.yml` + file config yang di-mount. File `dockerfile` kosong bisa dihapus.

---

## 4. Ringkasan Service di `docker-compose.yml`

| Service | Image | Port | Volume | Wajib? |
|---------|-------|------|--------|--------|
| prometheus | `prom/prometheus` | 9090 | `prometheus_data`, `./prometheus` | Wajib |
| node-exporter | `prom/node-exporter` | 9100 | `/proc`, `/sys`, `/` (read-only) | Wajib |
| grafana | `grafana/grafana` | 3000 | `grafana_data`, `./grafana/provisioning` | Wajib |
| cadvisor | `gcr.io/cadvisor/cadvisor` | 8080 | `/var/run`, `/sys`, `/var/lib/docker` (read-only) | Opsional |
| blackbox-exporter | `prom/blackbox-exporter` | 9115 | `./blackbox` | Opsional |

---

## 5. Kebutuhan Non-Fungsional

| Kode | Kategori | Requirement |
|------|----------|-------------|
| NF-01 | Keamanan | Password default Grafana (`admin/admin`) **wajib** diganti via `.env` |
| NF-02 | Keamanan | File `.env` masuk `.gitignore` |
| NF-03 | Keamanan | Port hanya dibuka untuk jaringan internal kantor (tidak di-expose ke internet) |
| NF-04 | Persistensi | Data Prometheus & Grafana memakai named volume |
| NF-05 | Ketersediaan | Semua container `restart: unless-stopped` (otomatis jalan setelah reboot) |
| NF-06 | Maintainability | Semua image memakai versi tetap (pinned), bukan `latest` |
| NF-07 | Dokumentasi | Langkah instalasi & cara pakai dicatat di `PROGRESS.md` / README |

---

## 6. Langkah Pengerjaan (Urutan)

1. [ ] Cek prasyarat (Docker & Compose terinstall).
2. [ ] Buat struktur folder sesuai bagian 3.
3. [ ] Buat `.env.example` & `.env`, tambahkan `.env` ke `.gitignore`.
4. [ ] Tulis `prometheus/prometheus.yml`.
5. [ ] Tulis service `prometheus` + `node-exporter` di `docker-compose.yml` → jalankan & verifikasi (Acceptance 1.3).
6. [ ] Tulis provisioning Grafana (datasource + dashboard).
7. [ ] Tambahkan service `grafana` di `docker-compose.yml` → jalankan & verifikasi (Acceptance 2.3).
8. [ ] *(Opsional)* Tambahkan cAdvisor & Blackbox Exporter.
9. [ ] Dokumentasikan hasil di `PROGRESS.md`.

---

## 7. Perintah Dasar

```bash
docker compose up -d          # Menjalankan semua service
docker compose ps             # Cek status container
docker compose logs -f grafana  # Lihat log service tertentu
docker compose down           # Menghentikan (data tetap aman di volume)
docker compose down -v        # Menghentikan + HAPUS data volume (hati-hati!)
```


---

## 0. Prasyarat (Prerequisites)

| No | Kebutuhan | Keterangan |
|----|-----------|------------|
| 0.1 | Docker Engine | Terinstall dan berjalan (`docker --version`) |
| 0.2 | Docker Compose v2 | Plugin `docker compose` (`docker compose version`) |
| 0.3 | Port tersedia | `9090` (Prometheus), `3000` (Grafana), `9100` (Node Exporter) tidak dipakai aplikasi lain |
| 0.4 | Resource minimum host | 2 CPU, 2 GB RAM, 10 GB disk kosong |
| 0.5 | Akses jaringan | Host monitoring dapat menjangkau perangkat/server yang akan dimonitor |

---

## 1. Membuat Prometheus

### 1.1 Kebutuhan Fungsional
- [ ] **P-01** Prometheus berjalan sebagai container dari image resmi `prom/prometheus` dengan **tag versi tetap** (contoh: `v3.5.0`, jangan `latest`).
- [ ] **P-02** Konfigurasi dibaca dari file `prometheus/prometheus.yml` yang di-mount ke container (read-only).
- [ ] **P-03** Prometheus melakukan scrape terhadap dirinya sendiri (`job_name: prometheus`, target `localhost:9090`).
- [ ] **P-04** Menambahkan **Node Exporter** (`prom/node-exporter`) untuk metrik host: CPU, RAM, disk, network.
- [ ] **P-05** Prometheus melakukan scrape ke Node Exporter (`job_name: node`, target `node-exporter:9100`).
- [ ] **P-06** *(Opsional)* Menambahkan **cAdvisor** untuk metrik per-container Docker.
- [ ] **P-07** *(Opsional)* Menambahkan **Blackbox Exporter** untuk cek ping/HTTP ke perangkat jaringan kantor (router, switch, server, website) – mendukung tugas *"Setup dan Cek Jaringan Kantor"*.
- [ ] **P-08** Interval scrape global: `15s`; retensi data: `15d` (via flag `--storage.tsdb.retention.time=15d`).
- [ ] **P-09** Web UI Prometheus dapat diakses di `http://<ip-host>:9090`.

### 1.2 Kebutuhan Teknis
- Data Prometheus disimpan di **named volume** `prometheus_data` agar tidak hilang saat container di-restart/dihapus.
- Container memakai `restart: unless-stopped`.
- Semua service terhubung ke satu **Docker network** yang sama (contoh: `monitoring`).

### 1.3 Kriteria Selesai (Acceptance Criteria)
- [ ] Halaman `http://<ip-host>:9090/targets` menampilkan semua target berstatus **UP**.
- [ ] Query `up` di Prometheus mengembalikan nilai `1` untuk setiap job.
- [ ] Query `node_memory_MemAvailable_bytes` mengembalikan data.
- [ ] Setelah `docker compose down` lalu `up -d`, data historis masih ada.

---

## 2. Membuat Grafana

### 2.1 Kebutuhan Fungsional
- [ ] **G-01** Grafana berjalan sebagai container dari image resmi `grafana/grafana` dengan **tag versi tetap** (contoh: `12.1.0`).
- [ ] **G-02** Web UI Grafana dapat diakses di `http://<ip-host>:3000`.
- [ ] **G-03** Username & password admin **tidak hardcode** di `docker-compose.yml`, melainkan dari file `.env` (`GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`).
- [ ] **G-04** Datasource Prometheus dibuat **otomatis** lewat provisioning (`grafana/provisioning/datasources/datasource.yml`) dengan URL `http://prometheus:9090`.
- [ ] **G-05** Dashboard dibuat otomatis lewat provisioning (`grafana/provisioning/dashboards/`), minimal:
  - **Node Exporter Full** (Grafana Dashboard ID `1860`) – monitoring host.
  - *(Opsional)* Dashboard cAdvisor / Docker containers.
  - *(Opsional)* Dashboard Blackbox Exporter (status perangkat jaringan).
- [ ] **G-06** Sign-up user baru dimatikan (`GF_USERS_ALLOW_SIGN_UP=false`).

### 2.2 Kebutuhan Teknis
- Data Grafana disimpan di **named volume** `grafana_data`.
- Grafana `depends_on` Prometheus.
- Container memakai `restart: unless-stopped`.

### 2.3 Kriteria Selesai (Acceptance Criteria)
- [ ] Bisa login ke Grafana memakai kredensial dari `.env`.
- [ ] Menu **Connections → Data sources** menampilkan Prometheus dan tombol *Test* berhasil (hijau).
- [ ] Dashboard Node Exporter tampil dengan data CPU/RAM/Disk/Network yang terisi.
- [ ] Dashboard & datasource tetap ada setelah container dibuat ulang.

---

## 3. Struktur Folder yang Diharapkan

```
.
├── docker-compose.yml
├── .env                    # TIDAK di-commit (masukkan ke .gitignore)
├── .env.example            # Template variabel, boleh di-commit
├── prometheus/
│   └── prometheus.yml
├── blackbox/               # (opsional)
│   └── blackbox.yml
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasource.yml
        └── dashboards/
            ├── dashboard.yml
            └── node-exporter-full.json
```

> **Catatan:** File `dockerfile` **tidak diperlukan** karena semua service memakai image resmi. Konfigurasi cukup lewat `docker-compose.yml` + file config yang di-mount. File `dockerfile` kosong bisa dihapus.

---

## 4. Ringkasan Service di `docker-compose.yml`

| Service | Image | Port | Volume | Wajib? |
|---------|-------|------|--------|--------|
| prometheus | `prom/prometheus` | 9090 | `prometheus_data`, `./prometheus` | Wajib |
| node-exporter | `prom/node-exporter` | 9100 | `/proc`, `/sys`, `/` (read-only) | Wajib |
| grafana | `grafana/grafana` | 3000 | `grafana_data`, `./grafana/provisioning` | Wajib |
| cadvisor | `gcr.io/cadvisor/cadvisor` | 8080 | `/var/run`, `/sys`, `/var/lib/docker` (read-only) | Opsional |
| blackbox-exporter | `prom/blackbox-exporter` | 9115 | `./blackbox` | Opsional |

---

## 5. Kebutuhan Non-Fungsional

| Kode | Kategori | Requirement |
|------|----------|-------------|
| NF-01 | Keamanan | Password default Grafana (`admin/admin`) **wajib** diganti via `.env` |
| NF-02 | Keamanan | File `.env` masuk `.gitignore` |
| NF-03 | Keamanan | Port hanya dibuka untuk jaringan internal kantor (tidak di-expose ke internet) |
| NF-04 | Persistensi | Data Prometheus & Grafana memakai named volume |
| NF-05 | Ketersediaan | Semua container `restart: unless-stopped` (otomatis jalan setelah reboot) |
| NF-06 | Maintainability | Semua image memakai versi tetap (pinned), bukan `latest` |
| NF-07 | Dokumentasi | Langkah instalasi & cara pakai dicatat di `PROGRESS.md` / README |

---

## 6. Langkah Pengerjaan (Urutan)

1. [ ] Cek prasyarat (Docker & Compose terinstall).
2. [ ] Buat struktur folder sesuai bagian 3.
3. [ ] Buat `.env.example` & `.env`, tambahkan `.env` ke `.gitignore`.
4. [ ] Tulis `prometheus/prometheus.yml`.
5. [ ] Tulis service `prometheus` + `node-exporter` di `docker-compose.yml` → jalankan & verifikasi (Acceptance 1.3).
6. [ ] Tulis provisioning Grafana (datasource + dashboard).
7. [ ] Tambahkan service `grafana` di `docker-compose.yml` → jalankan & verifikasi (Acceptance 2.3).
8. [ ] *(Opsional)* Tambahkan cAdvisor & Blackbox Exporter.
9. [ ] Dokumentasikan hasil di `PROGRESS.md`.

---

## 7. Perintah Dasar

```bash
docker compose up -d          # Menjalankan semua service
docker compose ps             # Cek status container
docker compose logs -f grafana  # Lihat log service tertentu
docker compose down           # Menghentikan (data tetap aman di volume)
docker compose down -v        # Menghentikan + HAPUS data volume (hati-hati!)
```