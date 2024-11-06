def test_imports():
    """Test les imports essentiels"""
    try:
        import kivy
        import webview
        from bs4 import BeautifulSoup
        from PyPDF2 import PdfReader
        print("✓ Tous les imports principaux fonctionnent")
        
        print(f"Version de Kivy: {kivy.__version__}")
        print(f"Version de PyWebView: {webview.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {str(e)}")
        return False

def test_epub_processor():
    """Test basique de EpubProcessor"""
    try:
        from epub_processor import EpubProcessor
        processor = EpubProcessor()
        print("✓ EpubProcessor initialisé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur avec EpubProcessor: {str(e)}")
        return False

if __name__ == "__main__":
    print("Test de l'environnement TTSenv")
    print("-" * 40)
    
    all_tests_passed = all([
        test_imports(),
        test_epub_processor()
    ])
    
    print("-" * 40)
    if all_tests_passed:
        print("✓ Tous les tests ont réussi")
    else:
        print("❌ Certains tests ont échoué") 