"""
Elle derlenmiş temel noktalar ve çizgiler.

OpenStreetMap'te bazı önemli yerler eksik/etiketsiz olabilir; fay hatları
OSM'de neredeyse hiç yoktur. Bu liste her veri çekişinde OSM verisiyle
birleştirilir (aynı isimli ve yakın OSM kaydı varsa onunla birleşir).
Koordinatlar ondalık derece (lat, lon). Kendi notlarını "desc" alanına
ekleyebilirsin – rehber anlatımın burada durur.
"""

# layer anahtarları: antik, tarihi, dini, muze, doga, ulasim
POINTS = [
    # ---- Antik kentler, ören yerleri, höyükler ----
    dict(layer="antik", name="İznik (Nikaia) Antik Kenti", lat=40.4292, lon=29.7211,
         wiki="tr:İznik",
         desc="Roma ve Bizans döneminin önemli kenti Nikaia. MS 325'te I. Ekümenik Konsil burada toplandı. "
              "Yaklaşık 5 km uzunluğundaki surları, dört ana kapısı ve tiyatrosuyla açık hava müzesi gibidir."),
    dict(layer="antik", name="Apollonia ad Rhyndacum (Gölyazı)", lat=40.1830, lon=28.6835,
         wiki="tr:Gölyazı, Nilüfer",
         desc="Uluabat Gölü'ne uzanan yarımadadaki antik Apollonia kenti. Bugünkü Gölyazı köyü, "
              "antik sur kalıntıları ve tarihi çınarlarıyla ünlüdür; gün batımı manzarası meşhurdur."),
    dict(layer="antik", name="Kios (Gemlik) Antik Kenti", lat=40.4320, lon=29.1560,
         wiki="tr:Gemlik",
         desc="Gemlik, antik çağda Kios adıyla bilinen bir Miletos kolonisidir. Efsaneye göre Argonotların "
              "uğrak yeridir; Gemlik Körfezi'nin doğal limanı kentin kaderini belirlemiştir."),
    dict(layer="antik", name="Apameia Myrleia (Mudanya)", lat=40.3780, lon=28.8800,
         wiki="tr:Mudanya",
         desc="Mudanya çevresindeki antik Myrleia, Bithynia Kralı I. Prusias tarafından eşinin adına "
              "Apameia olarak yeniden adlandırılmıştır."),
    dict(layer="antik", name="Tirilye (Zeytinbağı)", lat=40.3925, lon=28.7910,
         wiki="tr:Zeytinbağı, Mudanya",
         desc="Bizans döneminden kalma kiliseleri, taş evleri ve dar sokaklarıyla korunmuş bir kıyı kasabası. "
              "Rum ve Türk mimarisinin iç içe geçtiği nadir yerlerdendir."),
    dict(layer="antik", name="Aktopraklık Höyüğü", lat=40.1600, lon=28.7550, approx=True,
         desc="Nilüfer ilçesinde, MÖ 6400'lere uzanan Neolitik ve Kalkolitik yerleşim. "
              "Arkeopark olarak düzenlenmiş, yeniden inşa edilmiş evleriyle ziyaret edilebilir."),
    dict(layer="antik", name="Barcın Höyük", lat=40.2560, lon=29.6020, approx=True,
         desc="Yenişehir Ovası'nda MÖ 6600'lere tarihlenen Neolitik yerleşim; Anadolu'dan Avrupa'ya "
              "tarımın yayılmasını anlamak için kilit bir kazı alanıdır."),
    dict(layer="antik", name="Ilıpınar Höyüğü", lat=40.4740, lon=29.3020, approx=True,
         desc="Orhangazi yakınında, İznik Gölü'nün batı ucunda Neolitik dönem yerleşimi (MÖ ~6000)."),
    dict(layer="tarihi", name="Cumalıkızık (UNESCO)", lat=40.1758, lon=29.1711,
         wiki="tr:Cumalıkızık",
         desc="Osmanlı'nın kuruluş dönemine uzanan vakıf köyü. 2014'te 'Bursa ve Cumalıkızık: Osmanlı "
              "İmparatorluğu'nun Doğuşu' adıyla UNESCO Dünya Mirası listesine girdi."),

    # ---- Tarihi yapılar: kaleler, surlar, hanlar, medreseler ----
    dict(layer="tarihi", name="Bursa Kalesi (Hisar) ve Tophane", lat=40.1876, lon=29.0571,
         wiki="tr:Bursa Kalesi",
         desc="Bithynia döneminden kalma, Bizans ve Osmanlı'da genişletilen kale. Orhan Gazi 1326'da "
              "kenti buradan fethetti. Tophane Saat Kulesi ve Osman–Orhan Gazi türbeleri burada."),
    dict(layer="tarihi", name="Tophane Saat Kulesi", lat=40.1877, lon=29.0587,
         desc="1905'te inşa edilen, şehre hâkim tepedeki 6 katlı saat kulesi; Bursa'nın simgelerinden."),
    dict(layer="tarihi", name="Koza Han", lat=40.1838, lon=29.0624, wiki="tr:Koza Han",
         desc="1491'de II. Bayezid tarafından yaptırılan, ipek böcekçiliği ticaretinin merkezi olan han. "
              "Avlusunun ortasında küçük bir mescit bulunur; bugün hâlâ ipek satılır."),
    dict(layer="tarihi", name="Emir Han", lat=40.1835, lon=29.0614, approx=True,
         desc="Orhan Gazi döneminde (14. yy) yapılan, Bursa'nın en eski hanlarından."),
    dict(layer="tarihi", name="Yeşil Medrese", lat=40.1814, lon=29.0745,
         desc="Çelebi Mehmed'in Yeşil Külliyesi'nin medresesi; bugün Türk-İslam Eserleri Müzesi."),
    dict(layer="tarihi", name="İznik Lefke Kapısı", lat=40.4304, lon=29.7302,
         desc="Nikaia surlarının doğu kapısı; Roma döneminden kalma zafer takı biçiminde üç katlı kapı."),
    dict(layer="tarihi", name="İznik İstanbul Kapısı", lat=40.4363, lon=29.7203,
         desc="Surların kuzey kapısı; İmparator Hadrianus'un ziyareti anısına yapılmış anıtsal girişin yeri."),
    dict(layer="tarihi", name="İznik Roma Tiyatrosu", lat=40.4262, lon=29.7176, approx=True,
         desc="MS 2. yüzyılda Trajan döneminde yapılan, kazıları süren Roma tiyatrosu."),
    dict(layer="tarihi", name="Irgandı Köprüsü", lat=40.1866, lon=29.0697,
         desc="1442 tarihli, üzerinde dükkânlar bulunan çarşılı köprü; Gökdere üzerindedir. "
              "Dünyada üstünde çarşı olan az sayıdaki köprüden biri."),

    # ---- Dini yapılar ----
    dict(layer="dini", name="Ulu Cami", lat=40.1840, lon=29.0616, wiki="tr:Bursa Ulu Camii",
         desc="Yıldırım Bayezid'in Niğbolu zaferi sonrası 1396–1400 arasında yaptırdığı 20 kubbeli cami. "
              "İçindeki şadırvan ve 192 hat levhasıyla erken Osmanlı mimarisinin başyapıtıdır."),
    dict(layer="dini", name="Yeşil Cami", lat=40.1817, lon=29.0741, wiki="tr:Yeşil Camii (Bursa)",
         desc="Çelebi Mehmed'in 1419–1421'de yaptırdığı, çinileriyle ünlü cami. Adını minaresini kaplayan "
              "yeşil çinilerden alır."),
    dict(layer="dini", name="Yeşil Türbe", lat=40.1822, lon=29.0750, wiki="tr:Yeşil Türbe",
         desc="Çelebi Mehmed'in türbesi (1421). Dışı turkuaz, içi Tebrizli ustaların çinileriyle kaplıdır."),
    dict(layer="dini", name="Osman Gazi ve Orhan Gazi Türbeleri", lat=40.1879, lon=29.0563,
         desc="Osmanlı Devleti'nin kurucusu Osman Gazi ile oğlu Orhan Gazi'nin türbeleri, Tophane'de."),
    dict(layer="dini", name="Muradiye Külliyesi", lat=40.1906, lon=29.0450, wiki="tr:Muradiye Külliyesi",
         desc="II. Murad'ın külliyesi (1424–1426). Bahçesindeki 12 hanedan türbesiyle 'Sultan mezarlığı' olarak da bilinir."),
    dict(layer="dini", name="Emir Sultan Camii", lat=40.1872, lon=29.0848,
         desc="Yıldırım Bayezid'in damadı Emir Sultan adına yapılan cami ve türbe; servili hazire içinde."),
    dict(layer="dini", name="Yıldırım Bayezid Külliyesi", lat=40.1903, lon=29.0816,
         desc="1390–1395 yıllarında yapılan, cami, medrese, darüşşifa ve türbeden oluşan külliye."),
    dict(layer="dini", name="Orhan Gazi Camii", lat=40.1842, lon=29.0640,
         desc="1339'da Orhan Gazi tarafından yaptırılan, Bursa'nın ticaret merkezini başlatan külliyenin camisi."),
    dict(layer="dini", name="Hüdavendigar (I. Murad) Camii", lat=40.1951, lon=29.0283,
         desc="Çekirge'de, alt katı cami üst katı medrese olarak tasarlanmış özgün yapı (1366–1385)."),
    dict(layer="dini", name="İznik Ayasofya (Orhan Camii)", lat=40.4291, lon=29.7197,
         wiki="tr:İznik Ayasofya Camii",
         desc="6. yüzyıl Bizans bazilikası; 787'deki II. İznik Konsili burada toplandı. 1331'de camiye çevrildi."),
    dict(layer="dini", name="İznik Yeşil Cami", lat=40.4300, lon=29.7282,
         desc="Çandarlı Kara Halil Hayreddin Paşa'nın yaptırdığı (1378–1391) erken Osmanlı camisi."),
    dict(layer="dini", name="Tirilye Fatih Camii (Ayios Stefanos)", lat=40.3922, lon=28.7920, approx=True,
         desc="Bizans dönemi Hagios Stefanos Kilisesi; 1560'tan bu yana cami olarak kullanılıyor."),

    # ---- Müzeler ----
    dict(layer="muze", name="Bursa Kent Müzesi", lat=40.1828, lon=29.0640,
         desc="Eski Adliye binasında; Bursa'nın tarihini, zanaatlarını ve gündelik yaşamını anlatan müze."),
    dict(layer="muze", name="Bursa Arkeoloji Müzesi", lat=40.1932, lon=29.0384,
         desc="Kültürpark içinde; Bithynia, Roma ve Bizans dönemlerine ait heykel, sikke ve mezar stelleri."),
    dict(layer="muze", name="Türk İslam Eserleri Müzesi", lat=40.1814, lon=29.0745,
         desc="Yeşil Medrese'de; çini, el yazması, Karagöz figürleri ve yöresel kıyafetler sergilenir."),
    dict(layer="muze", name="Panorama 1326 Bursa Fetih Müzesi", lat=40.1886, lon=29.0585, approx=True,
         desc="Bursa'nın 1326'daki fethini 360° panoramik resim ve ses efektleriyle anlatan müze."),
    dict(layer="muze", name="İznik Müzesi (Nilüfer Hatun İmareti)", lat=40.4298, lon=29.7228,
         desc="1388 tarihli imaret binasında; İznik çinileri ve Roma–Bizans eserleri."),
    dict(layer="muze", name="Karagöz Müzesi", lat=40.1945, lon=29.0330, approx=True,
         desc="Bursa kökenli gölge oyunu Karagöz ve Hacivat'a adanmış müze."),

    # ---- Doğal güzellikler ----
    dict(layer="doga", name="Uludağ – Kartaltepe Zirvesi (2543 m)", lat=40.0708, lon=29.2214,
         wiki="tr:Uludağ", ele="2543",
         desc="Marmara Bölgesi'nin en yüksek noktası. Antik çağdaki adı Mysia Olympos'tur. "
              "Granit çekirdekli bir horst dağıdır: kuzeyindeki Bursa Ovası çöküntüsüyle birlikte "
              "fay hatlarının şekillendirdiği tipik bir yer şeklidir."),
    dict(layer="doga", name="Uludağ Milli Parkı – Oteller Bölgesi", lat=40.1050, lon=29.1210,
         desc="1961'de milli park ilan edildi. Türkiye'nin en eski kayak merkezlerinden; yazın yayla ve trekking."),
    dict(layer="doga", name="İznik Gölü", lat=40.4300, lon=29.5300, wiki="tr:İznik Gölü",
         desc="Marmara Bölgesi'nin en büyük gölü (~300 km²). Tektonik kökenlidir: Kuzey Anadolu Fayı'nın "
              "güney kolu üzerinde oluşmuş bir çöküntü gölüdür."),
    dict(layer="doga", name="Uluabat (Apolyont) Gölü", lat=40.1700, lon=28.5800, wiki="tr:Uluabat Gölü",
         desc="Sığ bir tatlı su gölü; Ramsar alanıdır. Pelikan ve karabatak gibi kuşların önemli üreme alanı."),
    dict(layer="doga", name="Suuçtu Şelalesi", lat=39.9452, lon=28.8197, approx=True,
         desc="Mustafakemalpaşa'da, yaklaşık 37 m yükseklikten dökülen şelale ve tabiat anıtı."),
    dict(layer="doga", name="Oylat Mağarası", lat=39.8930, lon=29.6930, approx=True,
         desc="İnegöl'de, sarkıt ve dikitleriyle ünlü mağara; yakınında Oylat kaplıcaları bulunur."),
    dict(layer="doga", name="İnkaya Çınarı", lat=40.1720, lon=29.1350, approx=True,
         desc="Yaklaşık 600 yaşında olduğu tahmin edilen anıt çınar; gövde çevresi 10 m'yi aşar."),
    dict(layer="doga", name="Çekirge Kaplıcaları", lat=40.1970, lon=29.0300, approx=True,
         desc="Uludağ'ın eteklerindeki fay hatlarından çıkan sıcak sular Roma'dan beri şifa için kullanılıyor. "
              "Eski Kaplıca ve Yeni Kaplıca tarihi hamamlardır."),
    dict(layer="doga", name="Kirazlıyayla", lat=40.1100, lon=29.0850, approx=True,
         desc="Uludağ yolu üzerinde, milli park girişine yakın yayla ve piknik alanı."),

    # ---- Ulaşım ----
    dict(layer="ulasim", name="Bursa Teleferik – Teferrüç İstasyonu", lat=40.1780, lon=29.0890, approx=True,
         desc="Dünyanın en uzun teleferik hatlarından biri (~9 km). Teferrüç'ten Sarıalan ve Oteller bölgesine çıkar."),
    dict(layer="ulasim", name="Yenişehir Havalimanı", lat=40.2552, lon=29.5626,
         desc="Bursa Yenişehir Havalimanı (YEI); Bursa'nın sivil havalimanı."),
    dict(layer="ulasim", name="Mudanya İskelesi", lat=40.3757, lon=28.8840, approx=True,
         desc="İstanbul'a deniz otobüsü seferlerinin yapıldığı iskele; 1922 Mudanya Mütarekesi de bu kasabada imzalandı."),
]

# Fay hatları – MTA Diri Fay Haritası'ndan sadeleştirilmiş, ŞEMATİK güzergâhlar.
# Rehber anlatımı içindir; mühendislik/afet amaçlı kullanılmamalıdır.
LINES = [
    dict(layer="fay", name="Kuzey Anadolu Fayı – Güney Kolu (Geyve–İznik–Gemlik)",
         desc="Kuzey Anadolu Fay Zonu'nun güney kolu. İznik Gölü'nün güney kıyısını ve Gemlik Körfezi'ni "
              "izleyerek batıya uzanır. İznik Gölü ve Gemlik Körfezi bu fayın oluşturduğu çöküntülerdir. "
              "(Şematik güzergâh)",
         coords=[(40.470, 30.000), (40.420, 29.820), (40.385, 29.700), (40.385, 29.560),
                 (40.395, 29.420), (40.420, 29.270), (40.415, 29.140), (40.395, 29.020),
                 (40.390, 28.900), (40.395, 28.760), (40.385, 28.600), (40.360, 28.400),
                 (40.330, 28.200), (40.320, 28.050)]),
    dict(layer="fay", name="Bursa Fayı (Uludağ kuzey eteği)",
         desc="Uludağ'ı Bursa Ovası'ndan ayıran normal fay. Dağın dik kuzey yamacı ve şehrin altındaki "
              "kaplıcalar bu fayla ilişkilidir. 1855 Bursa depremi bu bölgede olmuştur. (Şematik güzergâh)",
         coords=[(40.205, 28.880), (40.195, 28.980), (40.180, 29.060), (40.170, 29.150),
                 (40.155, 29.250), (40.135, 29.330)]),
    dict(layer="fay", name="İnegöl Fayı",
         desc="İnegöl Ovası'nın güney kenarını sınırlayan fay. (Şematik güzergâh)",
         coords=[(40.060, 29.330), (40.045, 29.450), (40.040, 29.560), (40.050, 29.680)]),
    dict(layer="fay", name="Yenişehir Fayı",
         desc="Yenişehir Ovası'nın kuzey kenarı boyunca uzanan fay. (Şematik güzergâh)",
         coords=[(40.300, 29.450), (40.290, 29.570), (40.280, 29.700), (40.270, 29.820)]),
    dict(layer="fay", name="Uluabat Fayı",
         desc="Uluabat Gölü'nün güneyinden geçen, Manyas–Mustafakemalpaşa fay sistemiyle bağlantılı fay. "
              "(Şematik güzergâh)",
         coords=[(40.080, 28.250), (40.105, 28.400), (40.120, 28.550), (40.130, 28.700)]),

    dict(layer="ulasim", name="Bursa Teleferik Hattı (Teferrüç–Sarıalan–Oteller)",
         desc="~9 km uzunluğundaki teleferik; Teferrüç (alt istasyon), Kadıyayla, Sarıalan ve Oteller "
              "istasyonlarını bağlar. (Yaklaşık güzergâh)",
         coords=[(40.1780, 29.0890), (40.1560, 29.0990), (40.1300, 29.1080), (40.1150, 29.1150),
                 (40.1050, 29.1210)]),
]

# İlçe merkezleri (etiket olarak gösterilir)
DISTRICTS = [
    ("Osmangazi", 40.1953, 29.0600), ("Nilüfer", 40.2140, 28.9870), ("Yıldırım", 40.1900, 29.0900),
    ("Gemlik", 40.4320, 29.1560), ("İnegöl", 40.0780, 29.5130), ("Mudanya", 40.3755, 28.8828),
    ("M.Kemalpaşa", 40.0380, 28.4110), ("Karacabey", 40.2150, 28.3600), ("Orhangazi", 40.4890, 29.3090),
    ("Yenişehir", 40.2640, 29.6530), ("Gürsu", 40.2170, 29.1920), ("Kestel", 40.1980, 29.2120),
    ("İznik", 40.4292, 29.7211), ("Orhaneli", 39.9030, 28.9890), ("Keles", 39.9140, 29.2290),
    ("Büyükorhan", 39.7680, 28.8900), ("Harmancık", 39.6780, 29.1510),
]
