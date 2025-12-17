"""
SherlockAI - İnteraktif Dedektif Oyunu
Agatha Christie ve Sherlock Holmes tarzında sürükleyici dedektif deneyimi
"""
import sys
import time
from game_engine import DetectiveGame
from ollama import DetectiveAgent
from story_generator import MysteryGenerator

class GameCLI:
    """Dedektif oyunu için sürükleyici CLI arayüzü."""
    
    def __init__(self):
        self.game = DetectiveGame(time_limit_minutes=30)
        self.agent = DetectiveAgent(model_name="llama3.2")
        self.generator = MysteryGenerator(model_name="llama3.2")
        self.running = True
        self.mystery_data = None
        self.current_character = None  # Hangi karakterle konuşuyor
        
    def print_header(self):
        """Oyun başlığını göster."""
        print("\n" + "="*70)
        print("🔍                    SHERLOCK AI                        🔍")
        print("        Agatha Christie & Sherlock Holmes Tarzında")
        print("              Yapay Zeka Destekli Dedektif Oyunu")
        print("="*70)
        
    def print_timer(self):
        """Kalan süreyi göster."""
        remaining = self.game.get_remaining_time()
        mins = remaining // 60
        secs = remaining % 60
        
        if remaining < 300:  # Son 5 dakika
            print(f"\n⚠️  ZAMAN AKIYOR: {mins:02d}:{secs:02d} ⚠️")
        else:
            print(f"\n⏰ Kalan Süre: {mins:02d}:{secs:02d}")
        
    def print_commands(self):
        """Mevcut komutları göster."""
        print("\n╔════════════════════════════════════════════════════════╗")
        print("║                   KOMUTLAR                             ║")
        print("╠════════════════════════════════════════════════════════╣")
        print("║  ara <yer>          - Bir lokasyonu ara               ║")
        print("║  konuş <kişi>       - Biriyle konuş (sorgu)           ║")
        print("║  sor <soru>         - Dedektif asistanına sor         ║")
        print("║  kanıtlar           - Toplanan kanıtları incele       ║")
        print("║  şüpheliler         - Şüphelileri listele             ║")
        print("║  ipucu              - Yönlendirme al                  ║")
        print("║  suçla <isim>       - Son suçlamayı yap               ║")
        print("║  yardım             - Bu menüyü göster                ║")
        print("╚════════════════════════════════════════════════════════╝")
        
    def display_intro(self):
        """Oyun girişi."""
        self.print_header()
        
        print("\n📜 Londra, 1895...")
        print("   Şehrin en karanlık sırlarını çözen dedektiflerden")
        print("   yardım istendiğinde, genelde umutsuz vakalar vardır.\n")
        
        input("   [Devam etmek için ENTER'a basın...]")
        
        print("\n🤖 Vaka dosyası oluşturuluyor...")
        print("   (AI benzersiz bir cinayet senaryosu üretiyor...)")
        print("   ⏳ Lütfen bekleyin, bu 30-60 saniye sürebilir...\n")
        
        self.mystery_data = self.generator.create_full_mystery()
        
        case = self.mystery_data['case']
        
        print("\n" + "="*70)
        print("📰 VAKA DOSYASI")
        print("="*70)
        print(f"\n🔍 {case['title']}\n")
        
        print("─" * 70)
        print(f"💀 KURBAN: {case['victim']['name']}")
        print(f"   Kimliği: {case['victim']['background']}")
        print(f"   Ölüm Zamanı: {case['victim']['killed_when']}")
        print(f"   Ölüm Yeri: {case['victim']['killed_where']}")
        print("─" * 70)
        
        print(f"\n📍 Araştırılacak Yerler: {', '.join(case['locations'])}")
        print(f"🕵️  Şüpheli Sayısı: {len(case['suspects'])} kişi")
        print(f"⏰ Süreniz: {self.game.time_limit // 60} dakika")
        
        print("\n💬 Dedektif Asistanı:")
        print('   "Sayın dedektif, zaman değerli. Her soruyu akıllıca')
        print('    kullanın, her kanıtı dikkatlice inceleyin.')
        print('    Sherlock Holmes\'ün dediği gibi: Olasızı elemek gerek,')
        print('    geriye ne kalırsa - ne kadar inanılmaz olsa da - gerçektir."\n')
        
        input("   [Soruşturmaya başlamak için ENTER...]")
        
    def get_all_suspects(self):
        """Tüm şüphelileri listele."""
        if not self.mystery_data:
            return []
        return [s for s in self.mystery_data['case']['suspects'] if not s.get('is_killer')]
    
    def handle_search(self, args):
        """Lokasyon araması."""
        if not args:
            print("\n❌ Hangi yeri aramak istiyorsunuz?")
            print("   Kullanım: ara <lokasyon adı>")
            return
        
        location = " ".join(args)
        
        print(f"\n🔦 {location} dikkatle aranıyor...")
        time.sleep(1)  # Atmosfer için
        
        items = self.game.search_location(location)
        
        if items:
            print(f"\n✨ Bulduğunuz kanıtlar:\n")
            for item in items:
                print(f"📦 {item['name']}")
                print(f"   └─ {item['description']}\n")
                
            # AI yorumu
            print("💬 Dedektif Asistanı:")
            comment = self.agent.comment_on_evidence(item['name'], item['description'])
            print(f'   "{comment}"\n')
        else:
            print(f"\n🤷 {location} içinde önemli bir şey bulamadınız.")
            print("   Belki başka bir yer daha verimli olabilir?\n")
            
    def handle_talk(self, args):
        """Şüpheli ile konuşma (rol yapma modu)."""
        if not args:
            print("\n❌ Kiminle konuşmak istiyorsunuz?")
            print("   Kullanım: konuş <kişi adı>")
            return
        
        person_name = " ".join(args)
        self.current_character = person_name
        
        # Kişiyi bul
        suspects = self.mystery_data['case']['suspects']
        victim = self.mystery_data['case']['victim']
        
        character = None
        for s in suspects:
            if s['name'].lower() == person_name.lower():
                character = s
                break
        
        if not character:
            print(f"\n❌ {person_name} isimli birini bulamadınız.")
            print(f"   Şüpheliler: {', '.join([s['name'] for s in suspects])}")
            return
        
        # Mark as interviewed
        self.game.mark_as_interviewed(character['name'])
        
        # İlişkileri al
        relationships = self.game.get_relationships(person_name)
        
        print(f"\n" + "─"*70)
        print(f"👤 {character['name']} ile konuşuyorsunuz")
        print(f"   Rolü: {character['role']} | Karakter: {character['trait']}")
        print("─"*70)
        
        print(f"\n💬 {character['name']}:")
        # AI karaktere bürünür
        intro = self.agent.character_introduction(
            character['name'], 
            character['trait'],
            character['role'],
            victim['name']
        )
        print(f'   "{intro}"\n')
        
        print("❓ Sormak istediğiniz soruyu yazın (veya 'çık' yazın):")
        
        while True:
            question = input(f"\n🔍 [{character['name']}'e] > ").strip()
            
            if question.lower() in ['çık', 'exit', 'bitti']:
                print(f"\n👋 {character['name']} ile görüşmeniz sona erdi.\n")
                self.current_character = None
                break
            
            if not question:
                continue
            
            # AI karakterin cevabını üretir
            print(f"\n💬 {character['name']}:")
            response = self.agent.character_response(
                character_name=character['name'],
                character_trait=character['trait'],
                question=question,
                relationships=relationships,
                is_killer=character.get('is_killer', False)
            )
            print(f'   "{response}"\n')
            
    def handle_ask(self, args):
        """Dedektif asistanına soru sor."""
        if not args:
            print("\n❌ Sorunuzu yazın.")
            print("   Kullanım: sor <sorunuz>")
            return
        
        question = " ".join(args)
        
        print(f"\n🤔 Siz: {question}")
        print("\n💭 Dedektif asistanı düşünüyor...\n")
        time.sleep(1)
        
        state = self.game.get_game_summary()
        answer = self.agent.answer_question(question, state)
        
        print(f"💬 Dedektif Asistanı:")
        print(f'   "{answer}"\n')
        
    def handle_evidence(self):
        """Kanıtları göster."""
        evidence = self.game.discovered_evidence
        
        if not evidence:
            print("\n📭 Henüz hiç kanıt toplamadınız.")
            print("   Lokasyonları aramayı deneyin!\n")
            return
        
        print(f"\n" + "═"*70)
        print(f"📚 TOPLANAN KANITLAR ({len(evidence)} adet)")
        print("═"*70 + "\n")
        
        for i, item in enumerate(evidence, 1):
            print(f"{i}. 📦 {item['name']}")
            print(f"   Bulunduğu Yer: {item['location']}")
            print(f"   Açıklama: {item['description']}\n")
        
        print("🔬 Dedektif Asistanı - Kanıt Analizi:")
        analysis = self.agent.analyze_evidence(evidence)
        print(f'   "{analysis}"\n')
        
    def handle_suspects(self):
        """Şüphelileri listele."""
        suspects = self.get_all_suspects()
        
        if not suspects:
            print("\n❌ Şüpheli listesi yüklenemedi.")
            return
        
        print(f"\n" + "═"*70)
        print(f"🕵️  ŞÜPHELİLER ({len(suspects)} kişi)")
        print("═"*70 + "\n")
        
        for i, suspect in enumerate(suspects, 1):
            interviewed = "✓" if suspect['name'] in self.game.interviewed_people else "✗"
            print(f"{i}. 👤 {suspect['name']} [{interviewed}]")
            print(f"   Rolü: {suspect['role']}")
            print(f"   Karakter: {suspect['trait']}")
            print(f"   Potansiyel Motif: {suspect['motive']}\n")
        
        print("💡 İpucu: 'konuş <isim>' komutu ile şüphelileri sorgulayın.\n")
        
    def handle_hint(self):
        """İpucu al."""
        print("\n💡 Dedektif Asistanı Yardımı\n")
        
        state = self.game.get_game_summary()
        suggestion = self.agent.suggest_next_action(state)
        
        print(f"💬 Dedektif Asistanı:")
        print(f'   "{suggestion}"\n')
        
    def handle_accuse(self, args):
        """Son suçlama."""
        if not args:
            print("\n❌ Kimi suçluyorsunuz?")
            print("   Kullanım: suçla <şüpheli ismi>")
            return
        
        suspect = " ".join(args)
        
        print("\n" + "═"*70)
        print(f"⚖️  SUÇLAMA")
        print("═"*70)
        print(f"\n🎯 Siz {suspect} isimli kişiyi katil olarak suçluyorsunuz.")
        print("\n⚠️  Bu kararınız kesinleşecek ve soruşturma sona erecek!")
        print("   Emin misiniz? (evet/hayır)")
        
        confirm = input("\n> ").strip().lower()
        
        if confirm not in ["evet", "yes"]:
            print("\n↩️  Suçlama iptal edildi. Soruşturma devam ediyor...\n")
            return
        
        # Dramatik bekleme
        print("\n" + "."*70)
        print("📜 Vaka dosyası kapatılıyor...")
        time.sleep(1)
        print("🔍 Son deliller değerlendiriliyor...")
        time.sleep(1)
        print("⚖️  Karar veriliyor...")
        time.sleep(1)
        
        result = self.game.make_accusation(suspect)
        
        print("\n" + "═"*70)
        
        if result["correct"]:
            print("✅ TEBRIKLER! VAKA ÇÖZÜLDÜ!")
            print("═"*70)
            print(f"\n🎉 {suspect} gerçekten katildi!")
            print("\n💬 Dedektif Asistanı:")
            print('   "Muhteşem bir çıkarım, sayın dedektif!')
            print('    Sherlock Holmes bile bu çözümü takdir ederdi.')
            print('    Adalet yerini buldu!"\n')
        else:
            print("❌ YANLIŞ SUÇLAMA!")
            print("═"*70)
            print(f"\n💔 Maalesef, {suspect} katil değildi.")
            print(f"   Gerçek katil: {result['actual_killer']}")
            print("\n💬 Dedektif Asistanı:")
            print('   "Ne yazık ki, deliller başka birini işaret ediyordu.')
            print('    "Belki daha dikkatli inceleseydiniz...')
            print('    Adalet bu sefer kaçtı."\n')
        
        print("─"*70)
        print("📊 SORUŞTURMA İSTATİSTİKLERİ")
        print("─"*70)
        print(f"   🔍 Toplanan Kanıt: {result['evidence_collected']}")
        print(f"   📍 Ziyaret Edilen Yer: {result['locations_visited']}")
        print(f"   ⏰ Kalan Süre: {result['time_remaining']} saniye")
        print("═"*70 + "\n")
        
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
        elif cmd in ["konuş", "konuş", "talk"]:
            self.handle_talk(args)
        elif cmd in ["sor", "ask"]:
            self.handle_ask(args)
        elif cmd in ["kanıtlar", "evidence", "kanitlar"]:
            self.handle_evidence()
        elif cmd in ["şüpheliler", "suspects", "supheliler"]:
            self.handle_suspects()
        elif cmd in ["ipucu", "hint"]:
            self.handle_hint()
        elif cmd in ["suçla", "accuse", "sucla"]:
            self.handle_accuse(args)
        elif cmd in ["yardım", "yardim", "help"]:
            self.print_commands()
        elif cmd in ["çık", "quit", "exit", "cik"]:
            print("\n👋 Soruşturmadan ayrılıyorsunuz...")
            print("   Gizem çözülmemiş olarak kalacak.\n")
            self.running = False
        else:
            print(f"\n❌ Bilinmeyen komut: '{cmd}'")
            print("   'yardım' yazarak komutları görebilirsiniz.\n")
            
    def run(self):
        """Ana oyun döngüsü."""
        try:
            self.display_intro()
            
            # AI hikayeyi yükle
            self.generator.load_mystery_to_database(self.mystery_data)
            self.game.initialize_mystery(use_ai_generator=True, mystery_data=self.mystery_data)
            self.game.start_game()
            
            print("\n" + "═"*70)
            print("🔍 SORUŞTURMA BAŞLADI")
            print("═"*70)
            print("\n💡 'yardım' yazarak komutları görebilirsiniz.\n")
            
            while self.running:
                # Süre kontrolü
                if self.game.is_time_up():
                    print("\n" + "⏰"*35)
                    print("⏰ SÜRE DOLDU!")
                    print("⏰"*35)
                    print("\nZaman tükendi! Hemen bir suçlama yapmalısınız!")
                    suspect = input("\n🎯 Katil kimdir? > ").strip()
                    if suspect:
                        self.handle_accuse([suspect])
                    break
                
                self.print_timer()
                
                try:
                    command = input("🔍 > ").strip()
                    
                    if command:
                        print()  # Boşluk için
                        self.process_command(command)
                        
                except KeyboardInterrupt:
                    print("\n\n👋 Oyun kesildi. Hoşça kalın!")
                    break
                except Exception as e:
                    print(f"\n❌ Hata: {e}")
                    print("   Lütfen tekrar deneyin.\n")
            
            print("\n" + "═"*70)
            print("🎭 OYUN BİTTİ")
            print("═"*70)
            print("\n   Oynamak için teşekkürler, dedektif!\n")
                    
        except Exception as e:
            print(f"\n💥 Kritik hata: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Giriş noktası."""
    try:
        game = GameCLI()
        game.run()
    except KeyboardInterrupt:
        print("\n\n👋 Görüşmek üzere!")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()