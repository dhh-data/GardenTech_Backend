# Smart Garden Backend

Backend FastAPI untuk dashboard Smart Garden Kit (ESP32 + sensor + MQTT HiveMQ).
Strukturnya mengikuti pola dari contoh dosen (FastAPI + SQLAlchemy, folder
`app/database`, `app/models`, `app/schemas`, `app/api`, `app/core`), tapi
field & endpoint sudah disesuaikan supaya cocok langsung dengan frontend
dashboard (GardenTech) yang sudah dibuat sebelumnya.

## 1. Persiapan database (MySQL via phpMyAdmin)

Backend ini pakai MySQL, dikelola lewat phpMyAdmin (asumsi kamu pakai
XAMPP atau Laragon yang sudah terinstall).

1. Buka phpMyAdmin (biasanya di `http://localhost/phpmyadmin`).
2. Buat database baru bernama `smart_garden_db` (klik "New" di sidebar kiri,
   isi nama, klik "Create"). **Tabel-tabel di dalamnya tidak perlu dibuat
   manual** — nanti otomatis dibuat oleh backend saat pertama kali dijalankan.
3. Pastikan MySQL server (Apache + MySQL di XAMPP, atau MySQL di Laragon)
   statusnya "Running".

## 2. Setup environment Python

```bash
cd SmartGardenBackend

# buat virtual environment
python -m venv venv

# aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# install semua dependency
pip install -r requirements.txt
```

## 3. Konfigurasi `.env`

Buka file `.env` di folder ini, sesuaikan dengan setting MySQL kamu.
Default-nya sudah cocok untuk XAMPP standar (user `root`, password kosong):

```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=smart_garden_db
DB_USER=root
DB_PASSWORD=
```

Kalau MySQL kamu pakai password (misal di Laragon biasanya juga kosong,
tapi kalau kamu set manual), isi `DB_PASSWORD` sesuai itu.

## 4. Isi data awal (seed)

Jalankan sekali untuk membuat tabel-tabel di database dan mengisi data awal
(akun admin default + 6 device default sesuai daftar komponen project):

```bash
python seed.py
```

Kalau berhasil, kamu akan lihat pesan seperti:
```
Akun admin default dibuat (username: admin, password: admin123)
Device dev001 (ESP32 DevKit V1) ditambahkan.
...
Seeding selesai.
```

Setelah ini, buka phpMyAdmin lagi dan refresh database `smart_garden_db` —
kamu akan lihat tabel `users`, `devices`, `sensor_readings`, `activity_logs`,
dan `pump_settings` sudah otomatis terbentuk.

## 5. Jalankan server

```bash
uvicorn app.main:app --reload
```

Kalau berhasil, server jalan di `http://localhost:8000`. Buka
`http://localhost:8000/docs` di browser untuk melihat dokumentasi API
otomatis (Swagger UI) — di sana kamu bisa coba semua endpoint langsung
tanpa perlu Postman.

## 6. Hubungkan ke frontend

Buka file `js/config.js` di folder frontend (GardenTech), ubah:

```javascript
USE_DUMMY_DATA: false,   // dari true jadi false
```

Pastikan `API_BASE_URL` di file yang sama sudah sesuai:

```javascript
API_BASE_URL: "http://localhost:8000/api/v1",
```

Login dengan akun default: **username `admin`, password `admin123`**.

## Struktur folder

```
SmartGardenBackend/
├── .env                      <- konfigurasi database, JWT, MQTT, CORS
├── requirements.txt
├── seed.py                    <- jalankan sekali untuk isi data awal
└── app/
    ├── main.py                  <- entry point, daftar semua router
    ├── database/
    │   └── database.py           <- koneksi MySQL via SQLAlchemy
    ├── models/                    <- definisi tabel (SQLAlchemy ORM)
    │   ├── user.py
    │   ├── device.py
    │   ├── sensor_reading.py
    │   ├── log.py
    │   └── pump_setting.py
    ├── schemas/                    <- validasi request/response (Pydantic)
    ├── core/
    │   ├── security.py               <- hash password, JWT
    │   └── dependencies.py             <- proteksi endpoint (login/Admin)
    └── api/                              <- semua endpoint, per-domain
        ├── auth.py                         <- POST /auth/login, /auth/register
        ├── users.py                          <- manajemen user (khusus Admin)
        ├── sensors.py                          <- data sensor dari ESP32
        ├── devices.py                            <- daftar device & kontrol aktuator
        ├── logs.py                                <- riwayat aktivitas
        └── settings.py                              <- mode otomatis & threshold pompa
```

## Daftar endpoint penting

| Method | Endpoint                              | Keterangan                                  | Login? |
|--------|----------------------------------------|----------------------------------------------|--------|
| POST   | `/api/v1/auth/register`                | Daftar akun baru                              | Tidak  |
| POST   | `/api/v1/auth/login`                   | Login, dapat JWT token                        | Tidak  |
| GET    | `/api/v1/users/`                       | List semua user                               | Admin  |
| PUT    | `/api/v1/users/{username}/role`        | Ubah role user                                | Admin  |
| DELETE | `/api/v1/users/{username}`             | Hapus user                                    | Admin  |
| POST   | `/api/v1/sensors/`                     | **ESP32 kirim data sensor ke sini**            | Tidak  |
| GET    | `/api/v1/sensors/latest`               | Data sensor terbaru (dipakai Dashboard)        | Tidak  |
| GET    | `/api/v1/sensors/history/moisture`     | Grafik kelembapan 24 jam                       | Tidak  |
| GET    | `/api/v1/sensors/history/voltage-current` | Grafik voltage/current (halaman Charts)     | Tidak  |
| GET    | `/api/v1/sensors/list`                 | Daftar sensor + nilai (halaman Sensors)        | Tidak  |
| GET    | `/api/v1/devices/`                     | Daftar device (halaman Devices)                | Tidak  |
| POST   | `/api/v1/devices/{device_code}/command`| Kontrol ON/OFF aktuator                        | Tidak  |
| GET    | `/api/v1/logs/`                        | Riwayat aktivitas                              | Tidak  |
| GET    | `/api/v1/settings/pump`                | Lihat mode otomatis & threshold                | Tidak  |
| PUT    | `/api/v1/settings/pump`                | Ubah mode otomatis & threshold                 | Tidak  |

Catatan: endpoint sensor/device/logs/settings sengaja **tidak diwajibkan
login** dulu di tahap ini supaya gampang ditest dan disambungkan ke ESP32.
Kalau dosen kamu mensyaratkan semua endpoint harus pakai token, tinggal
tambahkan `current_user: User = Depends(get_current_user)` di parameter
function-nya (contohnya sudah ada di `api/users.py`).

## Tentang MQTT (sudah aktif)

Koneksi ke HiveMQ Cloud sudah aktif dan berjalan saat backend distart.
Konfigurasi ada di `.env`:

```
MQTT_BROKER=1f604e26fc2a4f8982309a874cfac63b.s1.eu.hivemq.cloud
MQTT_PORT=8883   # TLS — wajib untuk HiveMQ Cloud
MQTT_USERNAME=GardenTech_Server
MQTT_PASSWORD=Nichfier_123
MQTT_TOPIC_SENSOR=gardenkit/+/sensor
MQTT_TOPIC_CONTROL=gardenkit/+/control
```

**Cara kerja:**

Backend akan subscribe ke `gardenkit/+/sensor`. Setiap kali ESP32 publish
data sensor, backend otomatis menyimpannya ke database persis seperti
`POST /sensors/`. Frontend dashboard tinggal polling `GET /sensors/latest`
seperti biasa.

Ketika admin klik ON/OFF di halaman Actuators atau tombol "Siram manual"
di Dashboard, backend akan publish perintah ke `gardenkit/dev002/control`
sehingga ESP32 menerima perintah tersebut secara real-time.

**Format payload dari ESP32 (publish ke gardenkit/{device_code}/sensor):**

```json
{
  "soil_moisture": 38.5,
  "air_temp": 29.2,
  "pump_voltage": 4.97,
  "pump_current": 0.62,
  "ultrasonic_detected": false
}
```

**Format payload ke ESP32 (backend publish ke gardenkit/{device_code}/control):**

```json
{
  "command": "ON",
  "device": "dev002"
}
```

**Cek status MQTT:** `GET /api/v1/mqtt/status`
**Test publish manual:** `POST /api/v1/mqtt/publish?device_code=dev002&command=ON`
(tersedia juga di Swagger UI: `http://localhost:8000/docs`)

## Troubleshooting

**Error `Can't connect to MySQL server`**
Pastikan MySQL (di XAMPP: klik "Start" pada baris MySQL; di Laragon: klik
"Start All") sedang berjalan, dan `DB_HOST`/`DB_PORT` di `.env` sudah benar.

**Error `Unknown database 'smart_garden_db'`**
Database belum dibuat di phpMyAdmin. Lihat langkah 1 di atas.

**Error CORS di browser (saat frontend coba akses backend)**
Cek `CORS_ORIGINS` di `.env`, tambahkan origin frontend kamu (misal kalau
pakai Live Server VS Code yang biasanya `http://127.0.0.1:5500`).

**Password lama lupa diubah, mau reset semua data**
Hapus saja database `smart_garden_db` di phpMyAdmin, buat lagi yang baru
dengan nama sama, lalu jalankan `python seed.py` lagi.
