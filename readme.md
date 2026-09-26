# SmartLead AI - Transilation Akıllı Müşteri Adayı Toplama Asistanı

SmartLead AI, **Transilation** markası için geliştirilmiş, yapay zekâ destekli bir çeviri satış asistanıdır. Sistem, ziyaretçilerle sohbet ederek çeviri ihtiyaçlarını anlamaya, gerekli bilgileri toplamaya ve potansiyel müşterilerin iletişim bilgilerini (lead) SQLite veritabanında saklamaya yardımcı olur.

Proje; Python, Flask, SQLite, yapay zekâ API'si ve Wix kullanılarak geliştirilmiştir.

## 🏗️ Mimari ve Tasarım İlkeleri

Proje, **Separation of Concerns (Sorumlulukların Ayrılması)** ilkesine uygun katmanlı bir mimari kullanır.

```text
smartlead_ai/
│
├── run.py
├── config.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
└── app/
    ├── __init__.py
    ├── database.py
    ├── routes.py
    │
    └── services/
        ├── __init__.py
        └── ai_service.py
```

### Dosyaların Görevleri

* **`config.py`**: Uygulama ayarlarını ve ortam değişkenlerini yönetir.
* **`app/database.py`**: SQLite veritabanı işlemlerini gerçekleştirir.
* **`app/services/ai_service.py`**: Yapay zekâ API çağrılarını gerçekleştirir.
* **`app/routes.py`**: HTTP isteklerini karşılar ve ilgili servisleri çağırır.
* **`app/__init__.py`**: Flask Application Factory yapısını oluşturur.
* **`run.py`**: Uygulamayı başlatan giriş dosyasıdır.
* **`templates/`**: Kullanıcı ve yönetim arayüzlerinin HTML dosyalarını içerir.

Veritabanı işlemleri `database.py`, yapay zekâ işlemleri ise `ai_service.py` katmanında izole edilmiştir.

## 🤖 Yapay Zekâ Asistanı

Transilation AI asistanı, çeviri hizmeti almak isteyen kullanıcılarla Türkçe olarak iletişim kurar.

Örnek kullanıcı akışı:

1. Kullanıcı çeviri talebini belirtir.
2. Asistan yaklaşık kelime veya sayfa sayısını öğrenir.
3. Kullanıcı teslim tarihini belirtir.
4. Asistan gerekli bilgilerin tamamlandığını bildirir.
5. Kullanıcı teklif almak için iletişim formuna yönlendirilir.
6. İsim ve telefon bilgileri lead olarak kaydedilir.

Asistanın davranışı `BUSINESS_CONTEXT` yapılandırması üzerinden belirlenir.

## 🚀 API Endpoints

| Metot  | Uç Nokta      | Açıklama                                 |
| ------ | ------------- | ---------------------------------------- |
| `GET`  | `/health`     | Sunucunun canlılık durumunu kontrol eder |
| `POST` | `/api/sohbet` | Yapay zekâ ile sohbet başlatır           |
| `POST` | `/api/leads`  | Yeni müşteri adayı kaydeder              |
| `GET`  | `/api/leads`  | Kayıtlı müşteri adaylarını listeler      |
| `GET`  | `/dashboard`  | Yönetim panelini görüntüler              |

### Sohbet İsteği

`POST /api/sohbet`

Örnek:

```json
{
  "mesaj": "5000 kelimelik İngilizce akademik bir metni Türkçeye çevirmek istiyorum.",
  "gecmis": []
}
```

### Lead Kaydı

`POST /api/leads`

Örnek:

```json
{
  "isim": "Sıla",
  "telefon": "05550000000",
  "mesaj": "5000 kelimelik akademik çeviri, Cuma teslim."
}
```

## 🛠️ Yerel Kurulum

### 1. Projeyi indirin

```bash
git clone <REPO_URL>
cd smartlead_ai
```

### 2. Sanal ortam oluşturun

```bash
python3 -m venv venv
```

Sanal ortamı aktif edin:

```bash
source venv/bin/activate
```

### 3. Gerekli paketleri yükleyin

```bash
pip install -r requirements.txt
```

### 4. Ortam değişkenlerini oluşturun

Proje klasöründe `.env` dosyası oluşturun.

Örnek:

```env
SECRET_KEY=your-secret-key
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
AI_PROVIDER=groq
BUSINESS_CONTEXT=Sen Transilation'ın kibar ve yardımsever Türkçe satış asistanısın.
CORS_ORIGINS=*
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

**Önemli:** `.env` dosyası GitHub'a yüklenmemelidir.

### 5. Uygulamayı çalıştırın

```bash
python3 run.py
```

Uygulama varsayılan olarak şu adreste çalışır:

```text
http://127.0.0.1:5001
```

## 🧪 Test

Sunucu çalışırken sağlık kontrolü:

```text
GET /health
```

Başarılı bir yanıt örneği:

```json
{
  "status": "ok",
  "service": "Transilation Smart Sales Assistant",
  "durum": "canli"
}
```

Sohbet endpoint'i:

```text
POST /api/sohbet
```

Lead kaydetme:

```text
POST /api/leads
```

Lead listesini görüntüleme:

```text
GET /api/leads
```

Yönetim paneli:

```text
GET /dashboard
```

Yönetim paneli ve lead listesinin görüntülenmesi için kimlik doğrulama kullanılır.

## 🔐 Güvenlik

Projede temel güvenlik önlemleri uygulanmıştır:

* API anahtarları `.env` üzerinden okunur.
* `.env` dosyası GitHub'a dahil edilmez.
* SQL sorgularında parametreli sorgular (`?`) kullanılır.
* Yönetim paneli kimlik doğrulaması ile korunur.
* `GET /api/leads` endpoint'i kimlik doğrulaması gerektirir.
* AI servis hataları kontrollü şekilde ele alınır.
* Eksik API verileri için uygun HTTP durum kodları döndürülür.

## 🌐 Wix Entegrasyonu

Frontend tarafında Wix üzerinde oluşturulan Transilation arayüzü backend API'sine bağlanır.

Wix arayüzü:

* Kullanıcı mesajını `/api/sohbet` endpoint'ine gönderir.
* AI yanıtını kullanıcıya gösterir.
* Kullanıcı isim ve telefon bilgilerini `/api/leads` endpoint'ine gönderir.
* Backend tarafından kaydedilen lead bilgileri yönetim panelinden görüntülenebilir.

## ☁️ Render Deployment

Backend, Render üzerinde yayınlanmıştır.

Production ortamında Flask uygulaması Gunicorn ile çalıştırılır:

```bash
gunicorn run:app
```

Render ortam değişkenlerinde gerekli API anahtarları ve uygulama ayarları tanımlanır.

Deployment sonrasında `/health` endpoint'i kullanılarak backend'in çalışıp çalışmadığı kontrol edilir.

## 📊 Proje Akışı

```text
Kullanıcı
   │
   ▼
Wix / Transilation
   │
   ▼
/api/sohbet
   │
   ▼
AI Service
   │
   ▼
Yapay Zekâ API
   │
   ▼
AI Yanıtı
   │
   ▼
Kullanıcı
   │
   ▼
Teklif Al / Lead Formu
   │
   ▼
/api/leads
   │
   ▼
SQLite
   │
   ▼
Yönetim Paneli
```

## 🧰 Kullanılan Teknolojiler

* **Python 3**
* **Flask**
* **SQLite**
* **Flask-CORS**
* **Python-dotenv**
* **Yapay Zekâ API**
* **Wix**
* **Git / GitHub**
* **Render**
* **Gunicorn**

## 🎯 Projenin Amacı

Projenin amacı, gerçek bir çeviri hizmeti senaryosunda yapay zekâ destekli bir satış asistanının nasıl geliştirilebileceğini göstermektir.

Sistem, kullanıcıyla doğal bir sohbet kurarak çeviri ihtiyacını anlamayı, gerekli bilgileri toplamayı ve potansiyel müşterileri işletme sahibinin takip edebileceği şekilde kaydetmeyi hedefler.

## 📌 Proje Durumu

* Backend: ✅ Çalışıyor
* AI sohbet sistemi: ✅ Çalışıyor
* SQLite lead sistemi: ✅ Çalışıyor
* Yönetim paneli: ✅ Çalışıyor
* Dashboard güvenliği: ✅ Aktif
* Wix entegrasyonu: ✅ Çalışıyor
* Render deployment: ✅ Aktif
* GitHub: ✅ Aktif
* Uçtan uca test: ✅ Tamamlandı
