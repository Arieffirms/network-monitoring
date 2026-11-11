#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dynamic Data Generator - MikroTik RB750Gr3 (Dummy)
PT Baja Perkasa Sentosa & Sentosa Harmony Steel

Alur:
  [Generator] --tulis file nilai tiap N detik--> [shared volume]
  [SNMP Simulator] --baca file (subprocess: cat)--> jawab request SNMP
  [SNMP Exporter] -> [Prometheus 15s] -> [Grafana live]

Setiap metrik ditulis ke satu file (nama = key di bawah). Penulisan atomik
(tulis ke file .tmp lalu os.replace) sehingga simulator tidak pernah
membaca file setengah jadi.

Kompatibel Python 3.4+ (berjalan di image tandrup/snmpsim:v0.4) dan hanya
memakai standard library.

Environment variable:
  DYNAMIC_DIR        Folder output (default: /dynamic)
  TICK_SECONDS       Interval update nilai (default: 5)
  SPIKE_PROBABILITY  Peluang lonjakan trafik ether1 per tick (default: 0.015
                     -> rata-rata 1 lonjakan tiap ~5-6 menit pada tick 5s)
  SPIKE_MIN_SECONDS  Durasi minimum lonjakan (default: 90)
  SPIKE_MAX_SECONDS  Durasi maksimum lonjakan (default: 240)

Trigger lonjakan manual (untuk uji alert Telegram):
  docker exec snmp-generator touch /dynamic/FORCE_SPIKE
"""

import math
import os
import random
import signal
import sys
import time

DYNAMIC_DIR = os.environ.get("DYNAMIC_DIR", "/dynamic")
TICK = float(os.environ.get("TICK_SECONDS", "5"))
SPIKE_PROBABILITY = float(os.environ.get("SPIKE_PROBABILITY", "0.015"))
SPIKE_MIN = float(os.environ.get("SPIKE_MIN_SECONDS", "90"))
SPIKE_MAX = float(os.environ.get("SPIKE_MAX_SECONDS", "240"))
FORCE_SPIKE_FILE = os.path.join(DYNAMIC_DIR, "FORCE_SPIKE")
READY_FILE = os.path.join(DYNAMIC_DIR, "READY")
LOG_EVERY_TICKS = 6

COUNTER64_MAX = 2 ** 64
COUNTER32_MAX = 2 ** 32 - 1

# Kapasitas link (Mbps) - sesuai ifSpeed di public.snmprec
LINK_MBPS = {"1": 1000.0, "2": 1000.0, "3": 300.0}

# Nilai awal counter (byte) bila belum ada file sebelumnya
INITIAL_COUNTERS = {
    "ifHCInOctets.1": 10000000000,
    "ifHCInOctets.2": 10000000000,
    "ifHCInOctets.3": 5000000000,
    "ifHCOutOctets.1": 10000000000,
    "ifHCOutOctets.2": 10000000000,
    "ifHCOutOctets.3": 5000000000,
    "simpleQueueBytesIn.1": 150000000,
    "simpleQueueBytesIn.2": 95000000,
    "simpleQueueBytesOut.1": 85000000,
    "simpleQueueBytesOut.2": 65000000,
    "treeQueueBytes.1": 150000000,
}

RUNNING = True


def _stop(signum, frame):
    global RUNNING
    RUNNING = False


def clamp(value, low, high):
    return max(low, min(high, value))


def write_value(key, value):
    """Tulis nilai secara atomik ke DYNAMIC_DIR/key."""
    path = os.path.join(DYNAMIC_DIR, key)
    tmp = path + ".tmp"
    with open(tmp, "w") as handle:
        handle.write(str(int(value)))
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def read_counter(key):
    """Lanjutkan counter dari file lama agar tidak reset saat restart."""
    path = os.path.join(DYNAMIC_DIR, key)
    try:
        with open(path) as handle:
            return int(handle.read().strip())
    except (IOError, OSError, ValueError):
        return INITIAL_COUNTERS[key]


class Wander(object):
    """Random walk mean-reverting (Ornstein-Uhlenbeck) -> fluktuasi halus."""

    def __init__(self, mean, sigma, low, high, reversion=0.15):
        self.mean = mean
        self.sigma = sigma
        self.low = low
        self.high = high
        self.reversion = reversion
        self.value = mean

    def step(self, target=None):
        goal = self.mean if target is None else target
        self.value += self.reversion * (goal - self.value)
        self.value += random.gauss(0, self.sigma)
        self.value = clamp(self.value, self.low, self.high)
        return self.value


class Generator(object):
    def __init__(self):
        self.counters = dict((k, read_counter(k)) for k in INITIAL_COUNTERS)
        # Trafik dasar (Mbps)
        self.wan_down = Wander(mean=35, sigma=4.0, low=8, high=70)
        self.wan_up = Wander(mean=9, sigma=1.5, low=2, high=25)
        self.wlan_down = Wander(mean=18, sigma=3.0, low=2, high=60)
        self.wlan_up = Wander(mean=5, sigma=1.0, low=0.5, high=20)
        # Sistem
        self.cpu_noise = Wander(mean=0, sigma=2.0, low=-8, high=8, reversion=0.3)
        self.ram_kb = Wander(mean=100000, sigma=900, low=88000, high=125000, reversion=0.05)
        self.temp_board = Wander(mean=42, sigma=0.25, low=36, high=55, reversion=0.03)
        self.voltage = Wander(mean=240, sigma=0.6, low=236, high=244, reversion=0.2)
        self.spike_until = 0.0
        self.spike_level = 0.0
        self.tick_count = 0
        self.started = time.time()

    def _spike_active(self, now):
        if os.path.exists(FORCE_SPIKE_FILE):
            try:
                os.remove(FORCE_SPIKE_FILE)
            except OSError:
                pass
            self._start_spike(now, manual=True)
        elif now >= self.spike_until and random.random() < SPIKE_PROBABILITY:
            self._start_spike(now, manual=False)
        return now < self.spike_until

    def _start_spike(self, now, manual):
        duration = random.uniform(SPIKE_MIN, SPIKE_MAX)
        self.spike_until = now + duration
        self.spike_level = random.uniform(85, 97)
        print("[generator] SPIKE %s ether1 ~%.0f Mbps selama %.0f detik" % (
            "MANUAL" if manual else "ACAK", self.spike_level, duration))
        sys.stdout.flush()

    def step(self, dt):
        now = time.time()
        self.tick_count += 1
        spiking = self._spike_active(now)

        # Pola harian halus (siang lebih ramai) - periode 24 jam
        hour = time.localtime(now).tm_hour + time.localtime(now).tm_min / 60.0
        daily = 1.0 + 0.25 * math.sin((hour - 9) / 24.0 * 2 * math.pi)

        wan_down_target = self.wan_down.mean * daily
        if spiking:
            wan_down_target = self.spike_level
            self.wan_down.high = 99
        else:
            self.wan_down.high = 70
        wan_down = self.wan_down.step(wan_down_target)
        if spiking:
            # Kunci di sekitar level spike agar alert stabil terpicu
            wan_down = self.wan_down.value = clamp(
                self.spike_level + random.gauss(0, 1.5), 82, 99)
        wan_up = self.wan_up.step(self.wan_up.mean * daily)
        wlan_down = self.wlan_down.step(self.wlan_down.mean * daily)
        wlan_up = self.wlan_up.step()

        # ether2 = sisi LAN switch: download WAN mengalir keluar ke LAN
        lan_out = wan_down * random.uniform(0.82, 0.9)
        lan_in = wan_up * random.uniform(0.85, 0.95)

        mbps = {
            "ifHCInOctets.1": wan_down,
            "ifHCOutOctets.1": wan_up,
            "ifHCInOctets.2": lan_in,
            "ifHCOutOctets.2": lan_out,
            "ifHCInOctets.3": wlan_up,
            "ifHCOutOctets.3": wlan_down,
        }
        for key, rate in mbps.items():
            idx = key.split(".")[1]
            rate = clamp(rate, 0, LINK_MBPS[idx])
            delta = int(rate * 1000000 / 8 * dt)
            self.counters[key] = (self.counters[key] + delta) % COUNTER64_MAX
            write_value(key, self.counters[key])

        # Simple & Tree Queue (32-bit counters, max 4.29 GB)
        sq_in_delta = int(wan_down * 1000000 / 8 * dt)
        sq_out_delta = int(wan_up * 1000000 / 8 * dt)
        self.counters["simpleQueueBytesIn.1"] = (self.counters["simpleQueueBytesIn.1"] + sq_in_delta) % COUNTER32_MAX
        self.counters["simpleQueueBytesIn.2"] = (self.counters["simpleQueueBytesIn.2"] + int(lan_in * 1000000 / 8 * dt)) % COUNTER32_MAX
        self.counters["simpleQueueBytesOut.1"] = (self.counters["simpleQueueBytesOut.1"] + sq_out_delta) % COUNTER32_MAX
        self.counters["simpleQueueBytesOut.2"] = (self.counters["simpleQueueBytesOut.2"] + int(lan_out * 1000000 / 8 * dt)) % COUNTER32_MAX
        self.counters["treeQueueBytes.1"] = (self.counters["treeQueueBytes.1"] + sq_in_delta) % COUNTER32_MAX

        write_value("simpleQueueBytesIn.1", self.counters["simpleQueueBytesIn.1"])
        write_value("simpleQueueBytesIn.2", self.counters["simpleQueueBytesIn.2"])
        write_value("simpleQueueBytesOut.1", self.counters["simpleQueueBytesOut.1"])
        write_value("simpleQueueBytesOut.2", self.counters["simpleQueueBytesOut.2"])
        write_value("treeQueueBytes.1", self.counters["treeQueueBytes.1"])

        # CPU: berkorelasi dengan total trafik yang diproses router
        total = wan_down + wan_up + wlan_down + wlan_up
        cpu1 = clamp(6 + total * 0.35 + self.cpu_noise.step(), 1, 100)
        cpu2 = clamp(cpu1 * random.uniform(0.75, 0.95) + random.gauss(0, 2), 1, 100)
        write_value("hrProcessorLoad.1", round(cpu1))
        write_value("hrProcessorLoad.2", round(cpu2))

        # RAM terpakai (unit 1024 byte, total 262144 = 256 MB)
        write_value("hrStorageUsed.1", self.ram_kb.step())

        # Suhu (0.1 °C -> 420 = 42.0 °C agar cocok dengan query PromQL /10) & tegangan (0.1 V -> 240 = 24.0 V)
        board = self.temp_board.step(40 + cpu1 * 0.12)
        write_value("mtxrHlTemperature", round(board * 10))
        write_value("mtxrHlProcessorTemperature", round((board + 5 + cpu1 * 0.05) * 10))
        write_value("mtxrHlVoltage", round(self.voltage.step()))

        # Wi-Fi Client Count & CCQ (%)
        wifi_clients = round(clamp(7 + wlan_down * 0.2 + random.gauss(0, 1), 3, 20))
        wifi_ccq = round(clamp(94 + random.gauss(0, 2), 85, 99))
        write_value("mtxrWlRtabEntryCount", wifi_clients)
        write_value("mtxrWlApOverallTxCCQ", wifi_ccq)

        if self.tick_count % LOG_EVERY_TICKS == 0:
            print("[generator] ether1 RX %.1f / TX %.1f Mbps | ether2 out %.1f | "
                  "wlan1 %.1f | CPU %d%% | RAM %d KB | %d C%s" % (
                      wan_down, wan_up, lan_out, wlan_down, cpu1,
                      self.ram_kb.value, board, " | SPIKE" if spiking else ""))
            sys.stdout.flush()


def main():
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    if not os.path.isdir(DYNAMIC_DIR):
        os.makedirs(DYNAMIC_DIR)
    os.chmod(DYNAMIC_DIR, 0o755)

    gen = Generator()
    gen.step(TICK)  # isi semua file sebelum simulator mulai membaca
    write_value("READY", 1)
    print("[generator] siap - menulis ke %s tiap %.0f detik" % (DYNAMIC_DIR, TICK))
    sys.stdout.flush()

    last = time.time()
    while RUNNING:
        time.sleep(TICK)
        now = time.time()
        gen.step(now - last)
        last = now
    print("[generator] berhenti")


if __name__ == "__main__":
    main()

