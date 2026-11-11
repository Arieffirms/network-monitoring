# Dummy SNMP Simulator (Router MikroTik Virtual)

Folder ini berisi konfigurasi **Simulator SNMP terisolasi** untuk mensimulasikan router **MikroTik RouterOS (RB750Gr3)** di lingkungan lokal secara aman tanpa menyentuh perangkat jaringan kantor asli.

---

## 1. Data Apa Saja yang Disimulasikan?

File [data/public.snmprec](./data/public.snmprec) dan [data/mikrotik.snmprec](./data/mikrotik.snmprec) menyimulasikan metrik router riil:

| Parameter | Nilai Dummy yang Disimulasikan | Keterangan |
|---|---|---|
| **Perangkat** | RouterOS RB750Gr3 (hEX) | Nama: `Mikrotik-Kantor-BPS` |
| **Port / Interface** | `ether1-WAN`, `ether2-LAN`, `wlan1-Office` | Semua status **1 (UP)** |
| **Bandwidth (Trafik)** | `ether1`: ~28 GB In / ~25 GB Out | Counter 64-bit (`ifHCInOctets`) |
| **Beban CPU** | Core 1: 18%, Core 2: 24% | Metrik Host Resource MIB |
| **Kapasitas RAM** | Total: 256 MB, Terpakai: ~96 MB | Metrik Storage MIB |
| **Suhu Router** | Board: **42°C**, CPU: **47°C** | MIB Enterprise MikroTik |
| **Tegangan Listrik** | **24.0 Volt** | MIB Enterprise MikroTik |

---

## 2. Cara Menjalankan Secara Manual

> **Catatan:** Pastikan network utama monitoring sudah dibuat lebih dulu (dengan menjalankan `docker compose up -d` di root project minimal sekali).

Jalankan perintah ini di terminal:

```bash
# 1. Masuk ke folder dummy-snmp
cd dummy-snmp

# 2. Nyalakan simulator di background
docker compose up -d

# 3. Cek apakah container simulator aktif
docker compose ps
```

---

## 3. Cara Menguji (Testing)

Untuk memastikan simulator merespons SNMP dengan baik dari laptop kamu:

```bash
# Uji tanya System Name via snmpwalk
snmpwalk -v2c -c public 127.0.0.1 1.3.6.1.2.1.1.5.0

# Uji tanya Suhu Router MikroTik
snmpwalk -v2c -c public 127.0.0.1 1.3.6.1.4.1.14988.1.1.3.10.0
```

*(Hasilnya akan mengembalikan `Mikrotik-Kantor-BPS` dan suhu `42`).*

---

## 4. Cara Mematikan

Jika sudah selesai uji coba dan ingin menghemat RAM:

```bash
cd dummy-snmp
docker compose down
```

