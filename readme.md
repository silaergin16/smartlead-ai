# SmartLead AI - Akıllı Müşteri Adayı Toplama Asistanı

SmartLead AI, ziyaretçilerle yapay zeka üzerinden sohbet eden, hizmet/ürün hakkında bilgi veren ve potansiyel müşteri iletişim bilgilerini (lead) toplayarak SQLite veritabanında saklayan kurumsal mimariye sahip bir backend sistemidir.

## 🏗️ Mimari ve Tasarım İlkeleri (Separation of Concerns)
Proje, sorumlulukların ayrılması ilkesine (Separation of Concerns) uygun olarak katmanlı bir yapıda geliştirilmiştir:

- **`config.py`**: Uygulama ayarları ve ortam değişkenlerinin (.env) yönetimi.
- **`app/database.py`**: Yalnızca veritabanı (SQLite) işlemlerinin yürütüldüğü veri katmanı.
- **`services/ai_service.py`**: Sadece Yapay Zeka (Gemini / Groq) API çağrılarının yapıldığı servis katmanı.
- **`app/routes.py`**: HTTP isteklerini karşılayan, veritabanı ve AI servislerini koordine eden API rotaları.
- **`app/__init__.py`**: Application Factory deseni ile uygulamanın ayağa kaldırılması.

## 🚀 Uç Noktalar (API Endpoints)

| Metot | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/health` | Sunucu canlılık durum kontrolü |
| `POST` | `/api/sohbet` | Yapay zeka ile sohbet yanıtı üretme |
| `POST` | `/api/leads` | Yeni müşteri adayı (lead) kaydetme |
| `GET` | `/api/leads` | Kayıtlı tüm müşteri adaylarını listeleme |
| `GET` | `/dashboard` | Yönetim paneli arayüzü |

## 🛠️ Yerel Kurulum

1. Depoyu klonlayın:
   ```bash
   git clone <REPO_URL>
   cd smartlead_ai