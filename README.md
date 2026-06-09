# Agentic AI Travel Planner

Agentic AI Travel Planner, kullanıcının seçtiği şehir ve tarih aralığı için güncel hava durumu verilerini analiz eden, günleri matematiksel olarak skorlayan ve buna göre kişiselleştirilmiş seyahat planı oluşturan otonom bir AI ajan uygulamasıdır.

Proje iki farklı kullanım yolu sunar:

- Streamlit ile web arayüzü
- Terminal üzerinden CLI modu

Uygulama LangChain tabanlı ReAct / tool-calling mimarisi kullanır. Planlayıcı ajan önce hava durumu aracını çağırır, ardından skor aracını çalıştırır ve son olarak Groq üzerinde çalışan LLM ile günlük seyahat planı üretir. Üretilen plan ayrıca ikinci bir LLM ajanı tarafından değerlendirilir.

## Temel Özellikler

- Gerçek hava durumu verisi: OpenWeatherMap 5-Day / 3-Hour Forecast API kullanılır.
- ReAct ajan akışı: Ajan araçları sırayla çağırarak karar verir.
- Matematiksel gün skorlama: Sıcaklık, yağmur, rüzgar, bulutluluk ve nem değerleri 10 üzerinden puana çevrilir.
- Kişiselleştirilmiş plan: Outdoor, indoor veya karma aktivite tercihleri desteklenir.
- Persona desteği: Standart rehber, gurme şef, tarih profesörü ve bütçe dostu gezgin rolleri bulunur.
- LLM-as-a-Judge değerlendirme: Plan ayrı bir değerlendirme ajanıyla 0-10 arasında puanlanır.
- Yerel hafıza: Son aramalar `user_memory.json` içinde yerel olarak saklanır.
- Web ve CLI desteği: Aynı ajan mantığı iki farklı arayüzden kullanılabilir.

## Mimari

```text
Kullanıcı
   |
   |-- Streamlit UI veya CLI
   |
Planner Agent
   |
   |-- get_weather tool
   |      |
   |      |-- OpenWeatherMap API
   |
   |-- score_days tool
   |      |
   |      |-- Python tabanlı deterministik skorlama
   |
   |-- Groq LLM
   |      |
   |      |-- Günlük seyahat planı üretimi
   |
Evaluation Agent
   |
   |-- Groq LLM
   |-- Hava-plan uyumu, çeşitlilik ve pratiklik değerlendirmesi
```

## Çalışma Akışı

1. Kullanıcı şehir, başlangıç tarihi, bitiş tarihi ve aktivite tercihini girer.
2. `run_planner_agent` fonksiyonu LangChain agent executor oluşturur.
3. Planner Agent önce `get_weather` aracını çağırır.
4. `get_weather`, OpenWeatherMap API'den 3 saatlik tahminleri alır.
5. Hava verileri günlük ortalama / toplam değerlere dönüştürülür.
6. Planner Agent `score_days` aracını çağırır.
7. `score_days`, son hava durumu verisini okuyup her günü 10 üzerinden skorlar.
8. Planner Agent skorları ve hava durumunu yorumlayarak plan üretir.
9. Evaluation Agent, planı hava durumu ve skorlarla karşılaştırarak kalite puanı verir.
10. UI veya CLI sonucu kullanıcıya gösterir.

## Skorlama Sistemi

| Kriter | Maksimum Puan | Açıklama |
| --- | ---: | --- |
| Sıcaklık | 4.0 | 20-26 derece ideal kabul edilir. |
| Yağmur | 3.0 | Yağış arttıkça açık hava puanı düşer. |
| Rüzgar | 1.5 | Hafif rüzgar yüksek puan alır. |
| Bulutluluk | 1.0 | Açık gökyüzü daha yüksek puan getirir. |
| Nem | 0.5 | %40-60 arası ideal kabul edilir. |
| Toplam | 10.0 | Günlük açık hava uygunluk puanı. |

Skora göre öneri kategorileri:

- 8 ve üzeri: Mükemmel, outdoor aktiviteler için çok uygun.
- 6-7.9: İyi, outdoor aktiviteler için uygun.
- 4-5.9: Orta, karma plan önerilir.
- 2-3.9: Kötü, indoor aktiviteler daha uygundur.
- 2 altı: Çok kötü, indoor odaklı plan yapılmalıdır.

## Proje Yapısı

```text
planner_agent/
├── agent/
│   ├── __init__.py
│   ├── memory.py          # Yerel kullanıcı hafızası
│   ├── planner.py         # LangChain ReAct / tool-calling planner agent
│   └── prompts.py         # Planner ve evaluator sistem promptları
├── evaluation/
│   ├── __init__.py
│   └── evaluator.py       # LLM-as-a-Judge değerlendirme ajanı
├── tools/
│   ├── __init__.py
│   ├── scoring.py         # Günlük hava durumu skorlama aracı
│   └── weather.py         # OpenWeatherMap tahmin aracı
├── ui/
│   ├── __init__.py
│   └── app.py             # Streamlit web arayüzü
├── .env.example           # Ortam değişkenleri örneği
├── .gitignore             # GitHub'a gönderilmeyecek dosyalar
├── DOCUMENTATION.md       # Ek proje raporu
├── main.py                # CLI giriş noktası
├── requirements.txt       # Python bağımlılıkları
└── user_memory.example.json
```

## Kullanılan Teknolojiler

- Python 3.12
- Streamlit
- LangChain
- LangChain Groq
- Groq API
- OpenWeatherMap API
- python-dotenv
- requests

## Kurulum

Önce projeyi bilgisayarınıza alın:

```bash
git clone https://github.com/kullanici-adiniz/planner_agent.git
cd planner_agent
```

Sanal ortam oluşturun:

```bash
python -m venv venv
source venv/bin/activate
```

Windows kullanıyorsanız:

```bash
venv\Scripts\activate
```

Bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

## Ortam Değişkenleri

`.env.example` dosyasını `.env` olarak kopyalayın:

```bash
cp .env.example .env
```

`.env` dosyasını kendi API anahtarlarınızla doldurun:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key_here
```

Gerekli anahtarlar:

- Groq API Key: https://console.groq.com/keys
- OpenWeatherMap API Key: https://openweathermap.org/api

Önemli: `.env` dosyası GitHub'a yüklenmemelidir. Bu projede `.gitignore` içine alınmıştır. Sadece `.env.example` paylaşılır.

## Çalıştırma

Web arayüzünü başlatmak için:

```bash
streamlit run ui/app.py
```

Terminal modunu çalıştırmak için:

```bash
python main.py
```

## Modüller

### `agent/planner.py`

Ana planlayıcı ajanın bulunduğu dosyadır. Groq LLM ayarlarını yapar, LangChain tool-calling agent oluşturur ve `get_weather` ile `score_days` araçlarını ajana bağlar.

Ana fonksiyonlar:

- `_create_llm`: Groq LLM nesnesini oluşturur.
- `_create_agent_executor`: LangChain agent executor kurulumunu yapar.
- `run_planner_agent`: Seyahat planlama sürecini başlatır.
- `format_react_steps`: Ara ajan adımlarını UI için okunabilir hale getirir.

### `tools/weather.py`

OpenWeatherMap API ile hava durumu tahmini alır. 3 saatlik tahminleri günlük verilere dönüştürür.

Dönen günlük alanlar:

- Tarih
- Ortalama / minimum / maksimum sıcaklık
- Toplam yağış
- Ortalama rüzgar hızı
- Ortalama bulutluluk
- Ortalama nem
- Ana hava durumu

### `tools/scoring.py`

Hava durumu verilerini deterministik bir puana çevirir. Bu araç LLM tahminine bağlı değildir; doğrudan Python hesaplaması yapar.

### `evaluation/evaluator.py`

Oluşturulan planı ikinci bir LLM ile değerlendirir. Değerlendirme kriterleri:

- Hava ve aktivite uyumu
- Gün sıralamasının doğruluğu
- Aktivite çeşitliliği
- Planın pratikliği

### `agent/memory.py`

Son kullanıcı aramalarını yerel `user_memory.json` dosyasında tutar. Bu dosya kişisel kullanım verisi içerdiği için GitHub'a gönderilmez.

### `ui/app.py`

Streamlit arayüzüdür. Şehir, tarih, tercih ve persona seçimini alır; planı, hava özetini, skorları ve değerlendirme sonucunu gösterir.

## Sınırlamalar

- OpenWeatherMap ücretsiz 5 günlük tahmin API'si kullanıldığı için tarih aralığı en fazla yakın gelecek ile sınırlıdır.
- Şehir adlarının API tarafından tanınacak biçimde girilmesi gerekir.
- Plan kalitesi kullanılan LLM modeline ve API yanıtlarına bağlıdır.
- Yerel hafıza dosyası çok kullanıcılı üretim ortamı için tasarlanmamıştır.

## Geliştirme Fikirleri

- Harita entegrasyonu
- Otel ve uçuş önerileri
- Günlük rota optimizasyonu
- Çok kullanıcılı veritabanı desteği
- Dockerfile ve deployment pipeline
- Test kapsamının artırılması

