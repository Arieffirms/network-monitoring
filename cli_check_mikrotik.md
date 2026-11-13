# Panduan CLI: Mengecek Identitas & Spesifikasi MikroTik via SNMP

Dokumen ini berisi perintah CLI untuk mengetahui **Nama Router (Identity), Tipe Model, Serial Number, Versi RouterOS, dan Jumlah Core CPU** dari router MikroTik kantor tanpa perlu membuka Winbox.

---

## 1. Perintah Cepat 1-Baris (SNMP)

Jalankan perintah berikut langsung dari terminal:

### A. Cek Nama Router (System Identity)
```bash
snmpget -v2c -c grafana-bps 192.168.2.1 1.3.6.1.2.1.1.5.0
```
**Contoh Output:**
```text
SNMPv2-MIB::sysName.0 = STRING: MikroTik
```

---

### B. Cek Model Router & Versi RouterOS
```bash
snmpget -v2c -c grafana-bps 192.168.2.1 1.3.6.1.2.1.1.1.0
```
**Contoh Output:**
```text
SNMPv2-MIB::sysDescr.0 = STRING: RouterOS RB5009UG+S+ 7.22.2 (stable)
```

---

### C. Cek Serial Number & Board Name Resmi MikroTik
```bash
# Serial Number
snmpget -v2c -c grafana-bps 192.168.2.1 1.3.6.1.4.1.14988.1.1.7.3.0

# Board Name
snmpget -v2c -c grafana-bps 192.168.2.1 1.3.6.1.4.1.14988.1.1.7.8.0
```
**Contoh Output:**
```text
SNMPv2-SMI::enterprises.14988.1.1.7.3.0 = STRING: "HK60ANJFZ8H"    # Serial Number
SNMPv2-SMI::enterprises.14988.1.1.7.8.0 = STRING: "RB5009UG+S+"    # Tipe Board
```

---

### D. Cek Jumlah CPU Core & Beban Saat Ini
```bash
snmpwalk -v2c -c grafana-bps 192.168.2.1 1.3.6.1.2.1.25.3.3.1.2
```
**Contoh Output (4 Core):**
```text
HOST-RESOURCES-MIB::hrProcessorLoad.1 = INTEGER: 3   # Core 1 (3%)
HOST-RESOURCES-MIB::hrProcessorLoad.2 = INTEGER: 3   # Core 2 (3%)
HOST-RESOURCES-MIB::hrProcessorLoad.3 = INTEGER: 4   # Core 3 (4%)
HOST-RESOURCES-MIB::hrProcessorLoad.4 = INTEGER: 3   # Core 4 (3%)
```

---

## 2. Script Ringkas: Banner Profil Lengkap

Salin dan tempel perintah berikut di terminal untuk menampilkan ringkasan rapi dalam satu tampilan:

```bash
bash -c '
IP="192.168.2.1"
COMM="grafana-bps"

NAME=$(snmpget -v2c -c $COMM -Oqv $IP 1.3.6.1.2.1.1.5.0 2>/dev/null)
DESCR=$(snmpget -v2c -c $COMM -Oqv $IP 1.3.6.1.2.1.1.1.0 2>/dev/null)
SERIAL=$(snmpget -v2c -c $COMM -Oqv $IP 1.3.6.1.4.1.14988.1.1.7.3.0 2>/dev/null)
CORES=$(snmpwalk -v2c -c $COMM -Oqv $IP 1.3.6.1.2.1.25.3.3.1.2 2>/dev/null | wc -l)
UPTIME=$(snmpget -v2c -c $COMM -Oqv $IP 1.3.6.1.2.1.1.3.0 2>/dev/null)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "        IDENTITAS & SPESIFIKASI MIKROTIK BPS       "
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Nama Router (Identity) : $NAME"
echo "🏷️  Tipe Model            : $DESCR"
echo "🔢 Serial Number          : $SERIAL"
echo "⚙️  Jumlah Core CPU       : $CORES Core"
echo "⏱️  System Uptime         : $UPTIME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
'
```

---

## 3. Cek Melalui Prometheus API (Tanpa Perlu Tools `snmpwalk`)

Jika Anda ingin mengecek langsung dari server Docker Prometheus:

```bash
# Cek Nama Router
curl -s 'http://localhost:9090/api/v1/query?query=sysIdentity' | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']['result']
for r in data:
    print('Router Identity:', r['metric'].get('sysIdentity'))
"

# Cek Model & Versi OS
curl -s 'http://localhost:9090/api/v1/query?query=sysDescr' | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']['result']
for r in data:
    print('Router Model & OS:', r['metric'].get('sysDescr'))
"
```

---

## 4. Tabel Referensi OID MikroTik Penting

| Data | OID Standar | Deskripsi |
|---|---|---|
| **sysName** | `1.3.6.1.2.1.1.5.0` | Nama identitas router (System Identity) |
| **sysDescr** | `1.3.6.1.2.1.1.1.0` | Model hardware & versi RouterOS |
| **mtxrLicSerialNumber** | `1.3.6.1.4.1.14988.1.1.7.3.0` | Nomor seri perangkat fisik MikroTik |
| **mtxrFirmwareVersion** | `1.3.6.1.4.1.14988.1.1.7.4.0` | Versi firmware RouterBOOT |
| **mtxrBoardName** | `1.3.6.1.4.1.14988.1.1.7.8.0` | Tipe board (misal `RB5009UG+S+`) |
| **hrProcessorLoad** | `1.3.6.1.2.1.25.3.3.1.2` | Beban persen tiap core prosesor |
| **sysUpTime** | `1.3.6.1.2.1.1.3.0` | Lama waktu router menyala (*uptime*) |

