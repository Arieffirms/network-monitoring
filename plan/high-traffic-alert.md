# Skema Alur Deteksi & Alert Trafik Tinggi (SNMP Dummy ➔ Telegram)

Dokumen ini menjelaskan alur teknis bagaimana sistem mendeteksi lonjakan trafik internet pada router MikroTik (menggunakan simulator dummy) dan secara otomatis mengirim pesan peringatan darurat ke Telegram HP Tim IT.

---

## 1. Gambar Diagram Alur

![Skema Alert Trafik Tinggi](./high-traffic-alert-schema.png)

*(File gambar resolusi tinggi tersedia di [`high-traffic-alert-schema.png`](./high-traffic-alert-schema.png) dan versi vektor di [`high-traffic-alert-schema.svg`](./high-traffic-alert-schema.svg))*

---

## 2. Diagram Urutan Kejadian (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor User as Karyawan Kantor
    participant Router as 1. Router Dummy (tandrup/snmpsim)
    participant Prom as 2. Prometheus Engine (:9090)
    participant Grafana as 3. Grafana Alert Engine (:3000)
    participant TG_API as 4. Telegram Cloud API
    actor IT as 5. HP Tim IT Support (Telegram)

    Note over User,Router: Karyawan download file besar / streaming
    User->>Router: Trafik internet melonjak ke 95.4 Mbps
    Router->>Router: Counter OID ifHCInOctets ether1 naik cepat

    loop Tiap 15 Detik
        Prom->>Router: Poll SNMP GET (Port UDP 161)
        Router-->>Prom: Kirim angka OID trafik mentah
        Prom->>Prom: Hitung rumus PromQL:<br/>rate(ifHCInOctets[2m]) * 8 / 1e6 = 95.4 Mbps
    end

    Note over Grafana: Evaluasi Rule: Apakah Trafik > 80 Mbps?
    Prom-->>Grafana: Data metrik: 95.4 Mbps
    Grafana->>Grafana: 95.4 > 80 (True!)<br/>Status: FIRING 🚨

    Grafana->>TG_API: HTTP POST /bot9115305134:*** /sendMessage<br/>Chat ID: 1510478721
    TG_API-->>IT: 📲 Notifikasi Push: HP Berdering!

    Note over IT: Pesan Peringatan:<br/>"🚨 [ALERT] Trafik ether1-WAN: 95.4 Mbps (Melebihi Batas 80 Mbps)"

    Note over User,Router: 20 Menit Kemudian: Download selesai, trafik turun ke 14.2 Mbps
    Prom-->>Grafana: Data metrik: 14.2 Mbps (di bawah 80 Mbps)
    Grafana->>Grafana: Kondisi aman kembali<br/>Status: RESOLVED ✅
    Grafana->>TG_API: HTTP POST /sendMessage (Status Pulih)
    TG_API-->>IT: 📲 Notifikasi Hijau: "✅ [RESOLVED] Trafik Normal (14.2 Mbps)"
```

---

## 3. Penjelasan Rumus Deteksi Trafik (PromQL)

Grafana dan Prometheus mendeteksi kecepatan download dengan rumus matematika:

$$\text{Kecepatan (Mbps)} = \frac{\text{rate}(ifHCInOctets[2m]) \times 8}{1.000.000}$$

* **`ifHCInOctets`**: Counter standar SNMP 64-bit yang menghitung jumlah byte data yang masuk ke port router.
* **`rate(...[2m])`**: Menghitung rata-rata kenaikan byte per detik selama 2 menit terakhir.
* **`x 8`**: Mengubah satuan **Byte** menjadi **Bit** (karena 1 Byte = 8 Bit).
* **`/ 1.000.000`**: Mengubah satuan Bit menjadi **Megabit per second (Mbps)**.

---

## 4. Siklus Status Alert (*Alert Lifecycle*)

1. **Normal (Hijau):** Trafik di bawah 80 Mbps (misal: 15 Mbps). Tidak ada pesan yang dikirim.
2. **Pending (Kuning):** Trafik tiba-tiba melonjak ke 95 Mbps. Sistem menunggu selama 1 menit untuk memastikan ini bukan hanya lonjakan sesaat (*spike* 1 detik).
3. **Firing (Merah):** Jika dalam 1 menit trafik tetap di atas 80 Mbps, Grafana langsung mengirim pesan darurat ke Telegram HP kamu.
4. **Resolved (Hijau):** Begitu pemakaian bandwidth mereda di bawah 80 Mbps, Grafana otomatis mengirim pesan bahwa kondisi jaringan sudah pulih.

