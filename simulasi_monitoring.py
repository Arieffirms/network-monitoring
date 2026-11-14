#!/usr/bin/env python3
"""
Script Simulasi & Pengujian Monitoring MikroTik
PT Baja Perkasa Sentosa
- Simulasi Trafik Tinggi (High Bandwidth Spike)
- Simulasi Serangan Port Scan & Brute Force (Memicu Log Serangan)
- Panduan Uji CPU & RAM Load
- Live Monitor Metrik di Terminal
"""

import sys
import time
import socket
import urllib.request
import json
import threading

ROUTER_IP = "192.168.2.1"
PROMETHEUS_URL = "http://localhost:9090"

def banner():
    print("=" * 60)
    print("   SIMULASI & PENGUJIAN MONITORING MIKROTIK (PT BPS)   ")
    print("=" * 60)
    print("Target Gateway Router :", ROUTER_IP)
    print("Monitoring Prometheus :", PROMETHEUS_URL)
    print("Grafana Dashboard     : http://localhost:3000/d/mikrotik-snmp-advanced")
    print("=" * 60)

def simulate_high_traffic(duration=15):
    print(f"\n[+] Memulai Simulasi Trafik Tinggi (Durasi: {duration} detik)...")
    print("[*] Menarik stream download berkecepatan tinggi melalui WAN (ether1)...")
    
    urls = [
        "https://proof.ovh.net/files/100Mb.dat",
        "http://speedtest.tele2.net/100MB.zip"
    ]
    
    stop_event = threading.Event()
    
    def download_worker(url):
        while not stop_event.is_set():
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    while not stop_event.is_set():
                        chunk = response.read(65536)
                        if not chunk:
                            break
            except Exception:
                time.sleep(0.5)

    threads = []
    # Jalankan 3 thread download paralel untuk memaksimalkan bandwidth
    for i in range(3):
        t = threading.Thread(target=download_worker, args=(urls[i % len(urls)],))
        t.daemon = True
        t.start()
        threads.append(t)
        
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            elapsed = int(time.time() - start_time)
            print(f"\r[*] Menarik trafik... [{elapsed}/{duration}s] - Periksa lonjakan di Grafana!", end="", flush=True)
            time.sleep(1)
    finally:
        stop_event.set()
        print("\n[✓] Simulasi Trafik Tinggi Selesai!")
        print("[*] Periksa panel 'Network Traffic Basic' di Grafana, grafik akan terlihat melonjak tajam.\n")

def simulate_attack_scan():
    print(f"\n[+] Memulai Simulasi Serangan Port Scan & Brute Force ke {ROUTER_IP}...")
    print("[*] Mengirim probe TCP ke berbagai port tertutup untuk memicu Firewall Attack Rule...")
    
    ports_to_scan = [
        21, 22, 23, 25, 80, 110, 135, 139, 143, 443, 445, 1433, 1521, 
        3306, 3389, 5432, 5900, 8080, 8291, 8443, 9000, 10000
    ]
    
    print("\n--- 1. Menjalankan Port Scanning (Port Scan Attack) ---")
    detected = 0
    for p in ports_to_scan:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        res = s.connect_ex((ROUTER_IP, p))
        status = "OPEN" if res == 0 else "DROPPED (Terpicu Firewall)"
        print(f"  Target Port {p:5} -> {status}")
        s.close()
        time.sleep(0.05)
    
    print("\n--- 2. Menjalankan Percobaan Brute-Force Connection ---")
    print("[*] Mengirim rentetan percobaan koneksi cepat ke port 22 (SSH) dan 8291 (Winbox)...")
    for i in range(1, 6):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect((ROUTER_IP, 8291))
            s.send(b"\x00\x00\x00\x00FAKE_LOGIN_ATTEMPT")
            s.close()
            print(f"  Percobaan #{i} ke Port 8291 (Winbox) terkirim.")
        except Exception:
            print(f"  Percobaan #{i} ke Port 8291 (Winbox) diblokir/drop oleh Firewall.")
        time.sleep(0.1)

    print("\n[✓] Simulasi Serangan Selesai!")
    print("[*] Buka Winbox -> menu 'Log', akan muncul baris log merah deteksi serangan:")
    print("    'ATTACK-PORTSCAN: in:ether3 ... TCP ...'")
    print("    'ATTACK-BRUTEFORCE: in:ether3 ... TCP ...'\n")

def cpu_ram_guide():
    print("\n" + "=" * 60)
    print("   PANDUAN UJI BEBAN CPU & RAM LOAD DI MIKROTIK   ")
    print("=" * 60)
    print("Untuk menguji beban CPU naik ke 90–100% secara aman:")
    print("1. Buka Winbox MikroTik (192.168.2.1).")
    print("2. Buka menu 'New Terminal'.")
    print("3. Jalankan perintah internal generator beban ini:")
    print("\n   /tool bandwidth-test address=127.0.0.1 duration=20s direction=both\n")
    print("Hasil yang akan terlihat:")
    print("✓ Beban 4 Core CPU Router akan seketika naik ke ~90-100%.")
    print("✓ Di Grafana, gauge 'CPU Load' akan berubah warna menjadi MERAH.")
    print("✓ Grafik 'System Resources Trend' akan melonjak tinggi.")
    print("✓ Alert Telegram 'CPU Load Kritis' akan terpicu jika berlangsung 1 menit.")
    print("=" * 60 + "\n")

def live_monitor():
    print("\n[+] Memulai Live Monitor Metrik dari Prometheus (Tekan Ctrl+C untuk keluar)...\n")
    queries = {
        "CPU Load (%)": "avg(hrProcessorLoad{instance='mikrotik-prod'})",
        "RAM Load (%)": "(hrStorageUsed{hrStorageIndex='65536',instance='mikrotik-prod'} * 100) / (hrStorageSize{hrStorageIndex='65536',instance='mikrotik-prod'})",
        "Suhu CPU (°C)": "mtxrHlProcessorTemperature{instance='mikrotik-prod'} / 10",
        "WAN In (Mbps)": "(irate(ifHCInOctets{ifName='ether1-WAN1',instance='mikrotik-prod'}[1m]) * 8) / 1000000",
        "WAN Out (Mbps)": "(irate(ifHCOutOctets{ifName='ether1-WAN1',instance='mikrotik-prod'}[1m]) * 8) / 1000000",
        "DHCP Leases": "mtxrDHCPLeaseCount{instance='mikrotik-prod'}",
        "Packets/sec": "sum(rate(ifInUcastPkts{instance='mikrotik-prod'}[1m]))"
    }

    try:
        while True:
            row = []
            for name, q in queries.items():
                url = f"{PROMETHEUS_URL}/api/v1/query?query=" + urllib.parse.quote(q)
                try:
                    res = json.loads(urllib.request.urlopen(url, timeout=2).read())
                    val = float(res['data']['result'][0]['value'][1])
                    row.append(f"{name}: {val:.1f}")
                except Exception:
                    row.append(f"{name}: -")
            print(" | ".join(row))
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[*] Monitor dihentikan.\n")

def main():
    while True:
        banner()
        print("PILIHAN MENU PENGUJIAN:")
        print("1. Jalankan Simulasi Trafik Tinggi (Tarik Bandwidth WAN > 50-80 Mbps)")
        print("2. Jalankan Simulasi Serangan (Port Scan & Brute Force - Cek Log Winbox)")
        print("3. Lihat Panduan Uji Beban CPU & RAM Load (RouterOS)")
        print("4. Lihat Live Monitor Metrik di Terminal (CPU, RAM, Temp, Trafik, Leases)")
        print("0. Keluar")
        print("=" * 60)
        
        choice = input("Pilih menu [1/2/3/4/0]: ").strip()
        if choice == "1":
            duration = input("Masukkan durasi uji dalam detik [default: 15]: ").strip()
            duration = int(duration) if duration.isdigit() else 15
            simulate_high_traffic(duration)
        elif choice == "2":
            simulate_attack_scan()
        elif choice == "3":
            cpu_ram_guide()
        elif choice == "4":
            live_monitor()
        elif choice == "0":
            print("\nTerima kasih. Monitoring tetap berjalan normal.")
            break
        else:
            print("\n[!] Pilihan tidak valid, silakan coba lagi.\n")

if __name__ == "__main__":
    main()
