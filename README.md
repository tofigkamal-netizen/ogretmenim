# Öyrət Platforması — İmtahan sistemi (demo)

Python (Flask) + JavaScript ilə yazılmış imtahan platforması. Admin veb brauzerdən
idarə edir, şagird/valideyn hissəsi isə veb-də **telefon çərçivəsi (mobile frame)**
içində göstərilir — gələcəkdə əsl mobil tətbiqə (React Native / Flutter) keçəndə
görünüş demək olar ki, eyni qalacaq.

## Rollar

| Rol | Giriş | Nə edir |
|---|---|---|
| **Admin** | istifadəçi adı `admin`, şifrə `1234` | imtahan yaradır (sual sayı, vaxt, başlama tarixi, suallar, şəkillər, doğru cavablar), şagird/valideyn hesabları yaradır, nəticələrə baxır |
| **Şagird** | admin tərəfindən yaradılan hesab | açıq imtahanları görür, imtahana başlayır, cavablandırır, öz nəticəsinə (doğru/yanlış/faiz) baxır |
| **Valideyn** | admin tərəfindən yaradılan hesab, avtomatik şagirdə bağlanır | bağlı olduğu şagirdin bütün imtahan nəticələrini və ümumi orta faizini görür |

Giriş səhifəsinin yuxarısındakı **Admin / Şagird-Valideyn** düyməsi ilə rejim seçilir
(referans şəkillərdəki "admin seç / şagird seç" məntiqinin veb qarşılığı).

## Qurulum

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python3 seed.py                 # demo hesablar + 5 sualdan ibarət riyaziyyat imtahanı yaradır
python3 app.py                  # http://localhost:5000
```

Demo hesablar (`seed.py` işlədəndən sonra):

- Admin: `admin` / `1234`
- Şagird: `nezrin` / `1234`
- Valideyn: `ana1` / `1234`

Admin panelindən `+ Şagird və valideyn əlavə et` düyməsi ilə özünüz üçün əsl
hesablar yarada bilərsiniz.

## Layihə strukturu

```
exam_platform/
├── app.py                  # bütün marşrutlar (login, admin, şagird, valideyn)
├── models.py                # SQLAlchemy modelləri (User, Exam, Question, Attempt, Answer)
├── seed.py                   # demo məlumat generatoru
├── requirements.txt
├── static/
│   ├── css/style.css         # dizayn (rəng, tipoqrafiya, telefon çərçivəsi)
│   ├── js/                   # (boş saxlanılıb, JS şablonların içindədir)
│   └── uploads/questions/    # sual şəkilləri buraya yüklənir
└── templates/
    ├── base.html              # admin/desktop layout
    ├── base_mobile.html        # şagird/valideyn telefon çərçivəsi layout
    ├── login.html
    ├── admin_dashboard.html, admin_exam_new.html, admin_users_new.html, admin_exam_results.html
    ├── student_dashboard.html, student_exam_warning.html, student_exam_take.html, student_exam_result.html
    └── parent_dashboard.html
```

Verilənlər bazası `exam.db` (SQLite) ilk işə düşəndə avtomatik yaradılır.

## Necə işləyir

1. **Admin** → `+ Yeni imtahan yarat`: başlıq, mövzu, başlama tarixi/saatı, sual
   sayı (5/10/25/digər) və vaxt (10/60/limitsiz/digər) seçilir → "Sualları
   formalaşdır" düyməsi seçilən say qədər sual bloku yaradır → hər sual üçün
   mətn, (istəyə bağlı) şəkil, A-E cavab variantları və doğru cavab daxil edilir.
2. **Şagird** girişdən sonra yalnız başlama vaxtı çatmış imtahanları görür.
   "Başla" → xəbərdarlıq ekranı ("İmtahan ərzində çıxmayın!") → START →
   sual+cavab ekranı, yuxarıda qırmızı geri sayım.
3. İmtahan bitəndə (vaxt bitdi / özü göndərdi / tətbiqdən çıxdı) cavablar
   avtomatik yoxlanılır, doğru/yanlış sayı və faiz hesablanıb göstərilir.
4. **Valideyn** öz panelində bağlı olduğu şagirdin bütün imtahan nəticələrini
   və ümumi orta faizini görür.

## Vacib qeyd: "vay-fay/blutuz bağlansın" haqqında

Referans şəkillərdə olan xəbərdarlıq ("Wi-Fi və Bluetooth-u bağlı saxlayın,
əks halda imtahan sonlandırılacaq") əsil mobil tətbiqlərdə cihazın sistem
səviyyəli icazələri ilə mümkündür. **Veb brauzer JavaScript-i heç vaxt cihazın
Wi-Fi/Bluetooth-unu söndürə bilməz və ya başqa tətbiqi bağlaya bilməz** — bu,
təhlükəsizlik səbəbindən bütün brauzerlərdə qadağandır (həm masaüstü, həm mobil).

Bunun əvəzinə bu layihədə real işləyən veb-ekvivalenti quraşdırılıb:
- şagird səhifəni tərk edəndə / başqa tab-a keçəndə (`visibilitychange`)
- brauzer pəncərəsi fokusunu itirəndə (`blur` — adətən tətbiqi dəyişəndə baş verir)
- vaxt bitəndə

bu hallarda imtahan **avtomatik və dərhal** göndərilir və mövcud cavablar
yadda saxlanılır — məntiq eynidir ("çıxsan, imtahan bitir"), sadəcə mexanizm
şəbəkəni söndürmək deyil, tərk etməni aşkarlamaqdır. Əsl mobil tətbiqə (React
Native/Flutter/Kotlin/Swift) keçəndə isə arxa fonda işləməni məhdudlaşdırmaq,
ekranı sabitləmək (Android-də "Screen Pinning" / "Lock Task Mode") kimi daha
güclü, sistemə əsaslanan üsullar əlavə etmək mümkündür.

## GitHub-a yükləmək

```bash
git init
git add .
git commit -m "İlk versiya: Öyrət Platforması"
git branch -M main
git remote add origin https://github.com/<istifadeci-adiniz>/<repo-adi>.git
git push -u origin main
```

`exam.db` və yüklənmiş şəkillər `.gitignore`-da istisna edilib, ona görə hər
kloz edən `python3 seed.py` ilə öz demo məlumatını yarada bilər.

## Gələcək üçün genişləndirmə fikirləri

- Açıq tipli və uyğunluq tipli suallar (hazırkı versiya yalnız qapalı A-E test sualını dəstəkləyir)
- Real mobil tətbiq (React Native) — eyni Flask backend-ə REST API kimi qoşulur
- Admin üçün Excel/CSV ilə toplu sual yükləmə
- Şəkilli sualların ölçüsünü avtomatik sıxma
