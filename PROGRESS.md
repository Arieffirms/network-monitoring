# PROGRESS – Implementasi Monitoring Stack (PT Baja Perkasa Sentosa & Sentosa Harmony Steel)

**Penanggung Jawab (Agent):** Romi (Senior DevOps Engineer)  
**Dokumen Acuan:** [requirments.md](./requirments.md) & [AGENTS.md](./AGENTS.md)  
**Status Terkini:** Tahap 1 Selesai (Prometheus & Node Exporter Berjalan dan Terverifikasi)

---

## Ringkasan Progres

| No | Komponen / Tahapan | Status | Tanggal / Waktu | Catatan |
|---|---|---|---|---|
| 0 | Setup Git & Secrets (`.gitignore`, `.env`, `.env.example`) | ✅ Selesai | 2026-11-10 | `.env` diamankan dari Git |
| 1 | Konfigurasi Prometheus (`prometheus/prometheus.yml`) | ✅ Selesai | 2026-11-10 | Scrape prometheus (localhost) & node-exporter |
| 2 | Setup Service Compose Tahap 1 (`docker-compose.yml`) | ✅ Selesai | 2026-11-10 | Pinned version, custom network, named volume |
| 3 | Quality Gate 1: Linting Compose & Promtool | ✅ Selesai | 2026-11-10 | `promtool check config` SUCCESS |
| 4 | Deploy Tahap 1: Prometheus + Node Exporter | ✅ Selesai | 2026-11-10 | Container `prometheus` & `node-exporter` UP |
| 5 | Verifikasi Metrik & Target Prometheus | ✅ Selesai | 2026-11-10 | Target `up` (1), `node_memory_MemAvailable_bytes` OK |
| 6 | Tahap 2: Setup Grafana & Auto-Provisioning | ⏳ Siap Dikerjakan | - | Menunggu konfirmasi lanjut |

---

## Log Detail Pengerjaan

### Tahap 1: Prometheus & Node Exporter (2026-11-10)

1. **Pengamanan Secrets & Environment:**
   - Dibuat file [.env.example](./.env.example) sebagai template variabel.
   - Dibuat file [.env](./.env) untuk menyimpan port dan kredensial admin.
   - Dipastikan [.gitignore](./.gitignore) mengabaikan file `.env` agar kredensial tidak bocor ke Git.

2. **Konfigurasi Prometheus:**
   - File [prometheus/prometheus.yml](./prometheus/prometheus.yml) dibuat dengan:
     - `scrape_interval: 15s`
     - Target 1: `localhost:9090` (Job `prometheus`)
     - Target 2: `node-exporter:9100` (Job `node`)

3. **Infrastruktur Docker Compose:**
   - Image yang digunakan berversi pasti (bukan `:latest`):
     - `prom/prometheus:v3.2.1`
     - `prom/node-exporter:v1.9.0`
   - Diterapkan keamanan container: `security_opt: [no-new-privileges:true]` dan `restart: unless-stopped`.
   - Data persisten menggunakan named volume `prometheus_data`.

4. **Pengujian & Linting (Quality Gates):**
   - `docker compose config --quiet` -> **Exit code 0 (Valid)**
   - `promtool check config` -> **SUCCESS: /etc/prometheus/prometheus.yml is valid prometheus config file syntax**

5. **Hasil Health-Check & Pengujian Metrik:**
   - Target status (`/api/v1/targets`):
     - `prometheus`: **UP** (`"health":"up"`)
     - `node`: **UP** (`"health":"up"`)
   - PromQL Query `up`: Mengembalikan nilai `1` untuk kedua target.
   - PromQL Query `node_memory_MemAvailable_bytes`: Mengembalikan nilai metrik memory host (`~7.4 GB`).

---

## Langkah Selanjutnya (Tahap 2)

- Menambahkan service `grafana:11.5.2` ke [docker-compose.yml](./docker-compose.yml).
- Mengintegrasikan auto-provisioning datasource Prometheus ([datasource.yml](./grafana/provisioning/datasources/datasource.yml)).
- Mengintegrasikan dashboard monitoring host Node Exporter.
- Menjalankan health check Grafana (`/api/health`) dan API datasource.

