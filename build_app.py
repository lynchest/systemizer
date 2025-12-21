import os
import re
import subprocess
import glob
import sys

# Konfigürasyon
PROJECT_NAME = "Systemizer"
MAIN_FILE = "main.py"
DIST_DIR = "dist"
ICON_PATH = os.path.join("assets", "icon.png")
# UPX klasörü (bu scriptin çalıştığı dizinde olduğu varsayılıyor)
UPX_DIR = os.path.join(os.getcwd(), "upx-5.0.2-win64")

def get_latest_version():
    """Dist klasöründeki dosyalara bakarak en son sürümü bulur. (Major.Minor.Patch)"""
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
        return (0, 0, 0)
    
    # Tüm .exe dosyalarını tarayalım (Systemizerv1.0.3.exe veya Systemizer_v1.0.3.exe gibi)
    pattern = os.path.join(DIST_DIR, "*.exe")
    files = glob.glob(pattern)
    
    if not files:
        return (0, 0, 0)
    
    versions = []
    # Regex: Proje adından sonra isteğe bağlı alt çizgi, v ve 3 haneli sürüm
    # Örn: Systemizerv1.0.2 veya Systemizer_v1.0.2
    regex = rf"{re.escape(PROJECT_NAME)}_?v(\d+)\.(\d+)\.(\d+)"
    
    for f in files:
        filename = os.path.basename(f)
        match = re.search(regex, filename)
        if match:
            v_tuple = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            versions.append(v_tuple)
            
    if not versions:
        return (0, 0, 0)
        
    # Sürümleri sırala ve en büyüğünü al
    versions.sort(reverse=True)
    return versions[0]

def determine_new_version(current_ver):
    """Kullanıcıdan input alarak yeni versiyonu belirler."""
    major, minor, patch = current_ver
    print(f"\nGüncel Sürüm: v{major}.{minor}.{patch}")
    print("-" * 30)
    print("1. Patch Güncelleme (v{}.{}.{}) - (Hata düzeltmeleri, küçük değişiklikler)".format(major, minor, patch + 1))
    print("2. Minor Güncelleme (v{}.{}.0) - (Yeni özellikler)".format(major, minor + 1))
    print("3. Major Güncelleme (v{}.0.0) - (Büyük değişiklikler)".format(major + 1))
    print("4. Manuel Giriş")
    print("5. İptal")
    
    while True:
        choice = input("\nSeçiminiz (1-5): ").strip()
        
        if choice == '1':
            return f"v{major}.{minor}.{patch + 1}"
        elif choice == '2':
            return f"v{major}.{minor + 1}.0"
        elif choice == '3':
            return f"v{major + 1}.0.0"
        elif choice == '4':
            custom = input("Versiyon girin (örn: v1.0.5): ").strip()
            if not custom.startswith('v'):
                custom = 'v' + custom
            return custom
        elif choice == '5':
            print("İşlem iptal edildi.")
            sys.exit(0)
        else:
            print("Geçersiz seçim.")

def build_application(version_tag):
    """PyInstaller komutunu çalıştırır."""
    print(f"\n>>> '{PROJECT_NAME} {version_tag}' için derleme başlatılıyor...")
    
    # Temel PyInstaller komutu
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        f"--name={PROJECT_NAME}",
        f"--icon={ICON_PATH}",
        "--clean",
        "--distpath", DIST_DIR,
        # Gereksiz modülleri çıkar (Boyut küçültme)
        "--exclude-module", "tkinter",
        "--exclude-module", "unittest",
        "--exclude-module", "email",
        "--exclude-module", "http",
        "--exclude-module", "xml",
        "--exclude-module", "pydoc",
        "--exclude-module", "pdb",
        MAIN_FILE
    ]
    
    # UPX Kontrolü ve Ekleme
    if os.path.exists(UPX_DIR) and os.path.exists(os.path.join(UPX_DIR, "upx.exe")):
        print(f"   [+] UPX Bulundu: {UPX_DIR} (Sıkıştırma uygulanacak)")
        cmd.extend(["--upx-dir", UPX_DIR])
    else:
        print("   [!] UPX bulunamadı veya 'upx.exe' eksik, sıkıştırma yapılmayacak.")

    try:
        # Komutu çalıştır
        subprocess.check_call(cmd)
        
        # Orijinal çıktı adı (Systemizer.exe) -> spec file name ile aynı olur genellikle
        original_output = os.path.join(DIST_DIR, f"{PROJECT_NAME}.exe")
        
        # Yeni isim (Systemizer_vX.Y.Z.exe)
        new_output = os.path.join(DIST_DIR, f"{PROJECT_NAME}_{version_tag}.exe")
        
        # Eğer eskiden kalan aynı isimli dosya varsa sil
        if os.path.exists(new_output):
            os.remove(new_output)
            
        if os.path.exists(original_output):
            os.rename(original_output, new_output)
            print(f"\n>>> BAŞARILI! Yeni sürüm oluşturuldu:")
            print(f"    Dosya: {new_output}")
            size_mb = os.path.getsize(new_output) / (1024 * 1024)
            print(f"    Boyut: {size_mb:.2f} MB")
        else:
            print("\n>>> HATA: Beklenen .exe dosyası bulunamadı.")
            
    except subprocess.CalledProcessError as e:
        print(f"\n>>> HATA: Derleme sırasında bir sorun oluştu.\n{e}")
    except Exception as e:
        print(f"\n>>> HATA: Beklenmeyen bir sorun oluştu.\n{e}")

if __name__ == "__main__":
    try:
        # 1. Mevcut sürümü bul
        current_ver = get_latest_version()
        
        # 2. Yeni sürümü belirle
        new_ver_tag = determine_new_version(current_ver)
        
        # 3. Build işlemini başlat
        build_application(new_ver_tag)
        
    except KeyboardInterrupt:
        print("\nİşlem kullanıcı tarafından durduruldu.")
