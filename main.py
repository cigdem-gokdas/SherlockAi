"""
SherlockAI - İnteraktif Dedektif Oyunu
Agatha Christie ve Sherlock Holmes tarzında sürükleyici dedektif deneyimi
"""
import sys
import io
import time
from game_engine import DetectiveGame
from ollama import DetectiveAgent
from story_generator import MysteryGenerator
from visualize_falkor_graph import visualize_graph_data

# ----------------------------------------------------------------
# TÜRKÇE KARAKTER SORUNUNU ÇÖZEN KOD (Windows Terminal İçin)
# ----------------------------------------------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
# ----------------------------------------------------------------

class GameCLI:
    """Dedektif oyunu için sade CLI arayüzü."""
    
    def __init__(self):
        self.game = DetectiveGame(time_limit_minutes=30)
        self.agent = DetectiveAgent(model_name="gemma2")
        self.generator = MysteryGenerator(model_name="gemma2")
        self.running = True
        self.mystery_data = None
        self.current_character = None
        
    def print_header(self):
        """Oyun başlığını göster."""
        print("\n------------------------------------------------------")
        print("                   SHERLOCK AI")
        print("       Agatha Christie & Sherlock Holmes Tarzında")
        print("          Yapay Zeka Destekli Dedektif Oyunu")
        print("------------------------------------------------------")
        
    def print_timer(self):
        """Kalan süreyi göster."""
        remaining = self.game.get_remaining_time()
        mins = remaining // 60
        secs = remaining % 60
        
        if remaining < 300:
            print(f"\n[!] ZAMAN AKIYOR: {mins:02d}:{secs:02d}")
        else:
            print(f"\nKalan Süre: {mins:02d}:{secs:02d}")
        
    def print_commands(self):
        """Mevcut komutları göster."""
        print("\nKOMUTLAR:")
        print("  ara <yer>          - Bir lokasyonu ara")
        print("  konuş <kişi>       - Biriyle konuş (sorgu)")
        print("  sor <soru>         - Dedektif asistanına sor")
        print("  kanıtlar           - Toplanan kanıtları incele")
        print("  şüpheliler         - Şüphelileri listele")
        print("  mekanlar           - Gidilebilecek yerleri listele")
        print("  harita             - İlişki ağını (Grafik) oluştur")
        print("  ipucu              - Yönlendirme al")
        print("  suçla <isim>       - Son suçlamayı yap")
        print("  yardım             - Bu menüyü göster")
        print("  çık                - Oyundan çık")
        print("------------------------------------------------------")
        
    def display_intro(self):
        """Oyun girişi."""
        self.print_header()
        
        print("\nLondra, 1895... (ya da belki İstanbul?)")
        print("Şehrin en karanlık sırlarını çözen dedektiflerden")
        print("yardım istendiğinde, genelde umutsuz vakalar vardır.\n")
        
        input("[Devam etmek için ENTER'a basın...]")
        
        print("\nVaka dosyası oluşturuluyor...")
        print("(AI benzersiz bir cinayet senaryosu üretiyor...)")
        print("Lütfen bekleyin, bu işlem biraz sürebilir...\n")
        
        self.mystery_data = self.generator.create_full_mystery()
        
        case = self.mystery_data['case']
        
        print("\n------------------------------------------------------")
        print("VAKA DOSYASI")
        print("------------------------------------------------------")
        print(f"\nBAŞLIK: {case['title']}\n")
        
        print(f"KURBAN: {case['victim']['name']}")
        print(f"Kimliği: {case['victim']['background']}")
        print(f"Ölüm Zamanı: {case['victim']['killed_when']}")
        print(f"Ölüm Yeri: {case['victim']['killed_where']}")
        print("------------------------------------------------------")
        
        print(f"\nAraştırılacak Yerler: {', '.join(case['locations'])}")
        print(f"Şüpheli Sayısı: {len(case['suspects'])} kişi")
        print(f"Süreniz: {self.game.time_limit // 60} dakika")
        
        print("\nDedektif Asistanı:")
        print('"Sayın dedektif, zaman değerli. Her soruyu akıllıca')
        print(' kullanın, her kanıtı dikkatlice inceleyin.')
        print(' Sherlock Holmes\'ün dediği gibi: Olasızı elemek gerek,')
        print(' geriye ne kalırsa - ne kadar inanılmaz olsa da - gerçektir."\n')
        
        input("[Soruşturmaya başlamak için ENTER...]")
        
    def get_all_suspects(self):
        """Tüm şüphelileri listele."""
        if not self.mystery_data:
            return []
        return self.mystery_data['case']['suspects']
    
    def handle_search(self, args):
        """Lokasyon araması."""
        if not args:
            print("\nHangi yeri aramak istiyorsunuz?")
            print("Kullanım: ara <lokasyon adı>")
            return
        
        search_term = " ".join(args).lower().strip()
        actual_locations = self.mystery_data['case']['locations']
        target_location = " ".join(args)

        # İsim eşleştirme
        for loc in actual_locations:
            if search_term in loc.lower():
                target_location = loc
                break
        
        print(f"\n{target_location} aranıyor...")
        time.sleep(1)
        
        items = self.game.search_location(target_location)
        
        if items:
            print(f"\nBulunan Kanıtlar:\n")
            for item in items:
                print(f"- {item['name']}")
                print(f"  Açıklama: {item['description']}\n")
                
            print("Dedektif Asistanı:")
            comment = self.agent.comment_on_evidence(item['name'], item['description'])
            print(f'"{comment}"\n')
        else:
            print(f"\n{target_location} içinde önemli bir şey bulunamadı.")
            print("Belki başka bir yer daha verimli olabilir?\n")
            
    def handle_talk(self, args):
        """Şüpheli ile konuşma."""
        if not args:
            print("\nKiminle konuşmak istiyorsunuz?")
            return
        
        person_name_input = " ".join(args).lower().strip()
        suspects = self.mystery_data['case']['suspects']
        victim = self.mystery_data['case']['victim']
        
        character = None
        for s in suspects:
            if person_name_input in s['name'].lower():
                character = s
                break
        
        if not character:
            print(f"\n{person_name_input} isimli biri bulunamadı.")
            print(f"Şüpheliler: {', '.join([s['name'] for s in suspects])}")
            return
        
        self.game.mark_as_interviewed(character['name'])
        relationships = self.game.get_relationships(character['name'])
        
        print(f"\n------------------------------------------------------")
        print(f"{character['name']} ile konuşuyorsunuz")
        print(f"Rolü: {character['role']} | Karakter: {character['trait']}")
        print("------------------------------------------------------")
        
        print(f"\n{character['name']}:")
        intro = self.agent.character_introduction(
            character['name'], 
            character['trait'],
            character['role'],
            victim['name']
        )
        print(f'"{intro}"\n')
        
        print("Sorunuzu yazın (veya 'çık' yazın):")
        
        while True:
            question = input(f"\n[{character['name']}] > ").strip()
            
            if question.lower() in ['çık', 'cik', 'exit', 'bitti']:
                print(f"\nGörüşme sona erdi.\n")
                self.current_character = None
                break
            
            if not question:
                continue
            
            print(f"\n{character['name']}:")
            response = self.agent.character_response(
                character_name=character['name'],
                character_trait=character['trait'],
                question=question,
                relationships=relationships,
                is_killer=character.get('is_killer', False)
            )
            print(f'"{response}"\n')
            
    def handle_ask(self, args):
        """Dedektif asistanına soru sor."""
        if not args:
            print("\nSorunuzu yazın.")
            return
        
        question = " ".join(args)
        
        print(f"\nSiz: {question}")
        print("Dedektif asistanı düşünüyor...\n")
        time.sleep(1)
        
        state = self.game.get_game_summary()
        answer = self.agent.answer_question(question, state)
        
        print(f"Dedektif Asistanı:")
        print(f'"{answer}"\n')
        
    def handle_evidence(self):
        """Kanıtları göster."""
        evidence = self.game.discovered_evidence
        
        if not evidence:
            print("\nHenüz hiç kanıt toplanmadı.")
            print("Lokasyonları aramayı deneyin!\n")
            return
        
        print(f"\n------------------------------------------------------")
        print(f"TOPLANAN KANITLAR ({len(evidence)} adet)")
        print("------------------------------------------------------\n")
        
        for i, item in enumerate(evidence, 1):
            print(f"{i}. {item['name']}")
            print(f"   Yer: {item['location']}")
            print(f"   Açıklama: {item['description']}\n")
        
        print("Dedektif Asistanı - Analiz:")
        analysis = self.agent.analyze_evidence(evidence)
        print(f'"{analysis}"\n')
        
    def handle_suspects(self):
        """Şüphelileri listele."""
        suspects = self.get_all_suspects()
        
        if not suspects:
            print("\nŞüpheli listesi yüklenemedi.")
            return
        
        print(f"\n------------------------------------------------------")
        print(f"ŞÜPHELİLER ({len(suspects)} kişi)")
        print("------------------------------------------------------\n")
        
        for i, suspect in enumerate(suspects, 1):
            status = "[Görüşüldü]" if suspect['name'] in self.game.interviewed_people else "[Görüşülmedi]"
            print(f"{i}. {suspect['name']} {status}")
            print(f"   Rolü: {suspect['role']}")
            print(f"   Karakter: {suspect['trait']}")
            print(f"   Motif: {suspect['motive']}\n")
        
        print("İpucu: 'konuş <isim>' komutu ile sorgulayabilirsiniz.\n")

    def handle_locations(self):
        """Lokasyonları listele."""
        if not self.mystery_data:
            print("\nHata: Vaka verisi bulunamadı.")
            return

        locations = self.mystery_data['case']['locations']
        
        print(f"\n------------------------------------------------------")
        print(f"MEKANLAR ({len(locations)} yer)")
        print("------------------------------------------------------\n")
        
        for i, loc in enumerate(locations, 1):
            # Basit ziyaret kontrolü
            status = "[Arandı]" if loc in self.game.visited_locations else ""
            print(f"{i}. {loc} {status}")
            
        print("\nİpucu: 'ara <yer ismi>' komutu ile arama yapabilirsiniz.\n")

    def handle_graph(self):
        """İlişki ağını görselleştir."""
        print("\n🕵️‍♂️ Vaka haritası oluşturuluyor...")
        print("   Veriler FalkorDB'den çekiliyor...")
        
        try:
            visualize_graph_data()
            print("\n✅ BAŞARILI: İlişki ağı 'project_graph_visualization.png' olarak kaydedildi.")
            print("   Dosya yöneticinizden bu resmi açıp inceleyebilirsiniz.\n")
        except Exception as e:
            print(f"\n❌ Grafik oluşturulurken hata: {e}\n")
        
    def handle_hint(self):
        """İpucu al."""
        print("\nDedektif Asistanı Yardımı\n")
        state = self.game.get_game_summary()
        suggestion = self.agent.suggest_next_action(state)
        print(f'"{suggestion}"\n')
        
    def handle_accuse(self, args):
        """Son suçlama."""
        if not args:
            print("\nKimi suçluyorsunuz?")
            return
        
        suspect = " ".join(args)
        
        print("\n------------------------------------------------------")
        print(f"SUÇLAMA ZAMANI")
        print("------------------------------------------------------")
        print(f"\nSiz {suspect} isimli kişiyi katil olarak suçluyorsunuz.")
        print("\nBu karar kesindir ve soruşturma sona erecektir!")
        print("Emin misiniz? (evet/hayır)")
        
        confirm = input("\n> ").strip().lower()
        
        if confirm not in ["evet", "yes"]:
            print("\nSuçlama iptal edildi.\n")
            return
        
        print("\nVaka dosyası kapatılıyor...")
        time.sleep(1)
        print("Karar veriliyor...")
        time.sleep(1)
        
        result = self.game.make_accusation(suspect)
        
        print("\n------------------------------------------------------")
        
        if result["correct"]:
            print("TEBRİKLER! VAKA ÇÖZÜLDÜ!")
            print("------------------------------------------------------")
            print(f"\n{suspect} gerçekten katildi!")
            print("\nDedektif Asistanı:")
            print('"Muhteşem bir çıkarım efendim! Adalet yerini buldu."\n')
        else:
            print("YANLIŞ SUÇLAMA!")
            print("------------------------------------------------------")
            print(f"\nMaalesef, {suspect} masumdu.")
            print(f"Gerçek katil: {result['actual_killer']}")
            print("\nDedektif Asistanı:")
            print('"Ne yazık ki katil kaçmayı başardı."\n')
        
        print("İSTATİSTİKLER")
        print(f"- Toplanan Kanıt: {result['evidence_collected']}")
        print(f"- Gezilen Yer: {result['locations_visited']}")
        print(f"- Kalan Süre: {result['time_remaining']} saniye")
        print("------------------------------------------------------\n")
        
        self.running = False
        
    def process_command(self, command: str):
        """Komut işle."""
        parts = command.strip().split()
        
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd in ["ara", "search"]:
            self.handle_search(args)
        elif cmd in ["konuş", "konus", "talk"]:
            self.handle_talk(args)
        elif cmd in ["sor", "ask"]:
            self.handle_ask(args)
        elif cmd in ["kanıtlar", "kanitlar", "evidence"]:
            self.handle_evidence()
        elif cmd in ["şüpheliler", "supheliler", "suspects"]:
            self.handle_suspects()
        elif cmd in ["mekanlar", "yerler", "locations"]:
            self.handle_locations()
        elif cmd in ["harita", "grafik", "map", "graph"]: 
            self.handle_graph()
        elif cmd in ["ipucu", "hint"]:
            self.handle_hint()
        elif cmd in ["suçla", "sucla", "accuse"]:
            self.handle_accuse(args)
        elif cmd in ["yardım", "yardim", "help"]:
            self.print_commands()
        elif cmd in ["çık", "cik", "quit", "exit"]:
            print("\nOyundan çıkılıyor...\n")
            self.running = False
        else:
            print(f"\nBilinmeyen komut: '{cmd}'")
            print("'yardım' yazarak komutları görebilirsiniz.\n")
            
    def run(self):
        """Ana oyun döngüsü."""
        try:
            self.display_intro()
            
            # AI hikayeyi yükle
            self.generator.load_mystery_to_database(self.mystery_data)
            self.game.initialize_mystery(use_ai_generator=True, mystery_data=self.mystery_data)
            self.game.start_game()
            
            print("\n------------------------------------------------------")
            print("SORUŞTURMA BAŞLADI")
            print("------------------------------------------------------")
            print("\n'yardım' yazarak komutları görebilirsiniz.\n")
            
            while self.running:
                # Süre kontrolü
                if self.game.is_time_up():
                    print("\nSÜRE DOLDU!")
                    print("Zaman tükendi! Hemen bir suçlama yapmalısınız!")
                    suspect = input("\nKatil kimdir? > ").strip()
                    if suspect:
                        self.handle_accuse([suspect])
                    break
                
                self.print_timer()
                
                try:
                    command = input("> ").strip()
                    
                    if command:
                        print()
                        self.process_command(command)
                        
                except KeyboardInterrupt:
                    print("\n\nOyun kesildi.")
                    break
                except Exception as e:
                    print(f"\nHata: {e}")
            
            print("\n------------------------------------------------------")
            print("OYUN BİTTİ")
            print("------------------------------------------------------\n")
                    
        except Exception as e:
            print(f"\nKritik hata: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Giriş noktası."""
    try:
        game = GameCLI()
        game.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()