# Bağımsız çevrimdışı harita araçları

Bu klasör, D:\maps\BIEM_Offline_Turkey altında geliştirilen indirme/görüntüleme araçlarının kaynak yedeğidir. Ana BİEM uygulaması bu tarayıcı sunucusuna bağlı değildir; native Harita sayfasını kullanır.

- serve_map.py yalnız 127.0.0.1 üzerinde, varsayılan 8766 portunda salt okunur yol haritası sunar. MBTiles dosyasını bu klasöre koyun; python serve_map.py --open ile açın. Büyük veri Git dışında kalır.
- download_map.py resmi Geofabrik Türkiye dosyasını indirip SQLite, örnek konum ve SHA-256 kontrolü yapar.
- download_satellite.py EOX 2016 uydu paketi üretir; --help ile hedef ve kapsam parametreleri görülebilir. Ülke genelinde z12 kullanıldı; sağlayıcı büyük z14 bloklarını reddettiği için şehir ayrıntısı küçük isteklerle download_city_satellite.py üzerinden tamamlandı.
- download_city_satellite.py mevcut pakete beş şehir merkezini ekleyen bu PC'ye özgü yardımcıdır; root değişkenindeki hedefi kontrol etmeden çalıştırmayın. Yeniden indirme bu yedek işleminin parçası değildir.
- CMD başlatıcıları bu PC'nin C:\Python314 yolunu kullanır; başka bilgisayarda Python yolunu uyarlayın.
- assets/ altında MapLibre GL JS modülleri ve kendi lisansı bulunur. Paket dosyalarının lisansı farklıdır: Geofabrik/OSM ODbL; EOX 2016 CC BY 4.0. Ana uygulamanın kurulum/geri yükleme adımları docs/BACKUP_2026-09-30.md içindedir.
