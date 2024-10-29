from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.uix.progressbar import ProgressBar
from kivy.properties import StringProperty, ListProperty
from kivy.metrics import dp
from kivy.uix.filechooser import FileChooserListView
import os
from utils import ensure_dir, create_unique_filename, get_filename_without_extension, sanitize_filename
import logging
from kivy.uix.label import Label as KivyLabel

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

class ChapterLabel(KivyLabel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(40)
        self.text_size = self.width, None
        self.bind(width=self.on_width)
        self.halign = 'left'
        self.valign = 'middle'
        self.padding = (dp(10), dp(5))
        self.color = (0.2, 0.2, 0.2, 1)
        
        # Supprimer les propriétés de style bouton
        self.background_normal = ''
        self.background_color = (1, 1, 1, 0)  # Fond transparent

    def on_width(self, instance, value):
        self.text_size = (value, None)
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return True
        return super().on_touch_down(touch)

class EpubToAudioApp(App):
    def build(self):
        return MainInterface()

class MainInterface(BoxLayout):
    selected_file = StringProperty("")
    output_directory = StringProperty("")
    chapters = ListProperty([])
    
    FILE_SELECT_CODE = 1
    DIRECTORY_SELECT_CODE = 2
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.info("Initialisation de l'interface principale")
        
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Zone de sélection de fichier
        self.file_section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(100)
        )
        self.file_label = Label(
            text="Aucun fichier sélectionné",
            size_hint_y=0.5,
            text_size=(None, None),
            halign='left',
            valign='middle',
            shorten=True,
            shorten_from='right',
            color=(0, 0, 0, 1)
        )
        self.select_button = Button(
            text="Sélectionner\nfichier",
            size_hint_y=0.5,
            height=dp(50),
            on_press=self.select_file
        )
        self.file_section.add_widget(self.file_label)
        self.file_section.add_widget(self.select_button)
        self.add_widget(self.file_section)
        
        # Zone de sélection du dossier de destination
        self.output_section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(100)
        )
        self.output_label = Label(
            text="Aucun dossier de destination sélectionné",
            size_hint_y=0.5,
            text_size=(None, None),
            halign='left',
            valign='middle',
            shorten=True,
            shorten_from='right',
            color=(0, 0, 0, 1)
        )
        self.select_output_button = Button(
            text="Dossier\ndestination",
            size_hint_y=0.5,
            height=dp(50),
            on_press=self.select_output_directory
        )
        self.output_section.add_widget(self.output_label)
        self.output_section.add_widget(self.select_output_button)
        self.add_widget(self.output_section)
        
        # Sélection de la voix
        self.voice_section = BoxLayout(size_hint_y=None, height=dp(50))
        self.voice_spinner = Spinner(
            text='Sélectionner une voix',
            values=['Voix 1', 'Voix 2', 'Voix 3'],
            size_hint_x=0.7,
            color=(1, 1, 1, 1),
            background_color=(0.4, 0.4, 0.4, 1)
        )
        self.test_voice_button = Button(
            text="Tester",
            size_hint_x=0.3,
            on_press=self.test_voice
        )
        self.voice_section.add_widget(self.voice_spinner)
        self.voice_section.add_widget(self.test_voice_button)
        self.add_widget(self.voice_section)
        
        # Boutons d'action
        self.action_buttons = BoxLayout(size_hint_y=None, height=dp(50))
        self.analyze_button = Button(
            text="Analyser",
            on_press=self.analyze_document
        )
        self.convert_button = Button(
            text="Convertir",
            on_press=self.start_conversion
        )
        self.action_buttons.add_widget(self.analyze_button)
        self.action_buttons.add_widget(self.convert_button)
        self.add_widget(self.action_buttons)
        
        # Liste des chapitres (modification)
        self.chapters_scroll = ScrollView(
            size_hint_y=0.6,
            do_scroll_x=False,
            bar_width=dp(10)
        )
        self.chapters_list = GridLayout(
            cols=1, 
            spacing=dp(2), 
            size_hint_y=None,
            padding=dp(5)
        )
        self.chapters_list.bind(minimum_height=self.chapters_list.setter('height'))
        
        # Ajout d'un en-tête pour la liste des chapitres
        self.header_label = KivyLabel(
            text="Liste des chapitres",
            size_hint_y=None,
            height=dp(30),
            bold=True,
            color=(0, 0, 0, 1)
        )
        self.add_widget(self.header_label)
        
        self.chapters_scroll.add_widget(self.chapters_list)
        self.add_widget(self.chapters_scroll)
        
        # Barre de progression
        self.progress_bar = ProgressBar(max=100, size_hint_y=None, height=dp(30))
        self.add_widget(self.progress_bar)
        
        # Status
        self.status_label = Label(
            text="Prêt",
            size_hint_y=None,
            height=dp(30),
            color=(0, 0, 0, 1)
        )
        self.add_widget(self.status_label)

    def select_file(self, instance):
        try:
            logging.info("Tentative de sélection de fichier")
            # Essayer d'abord la méthode Android native
            from android.storage import primary_external_storage_path
            from android.permissions import request_permissions, Permission
            from jnius import autoclass
            
            request_permissions([Permission.READ_EXTERNAL_STORAGE])
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            
            intent = Intent(Intent.ACTION_GET_CONTENT)
            intent.setType("application/epub+zip")
            self.start_activity_for_result(intent, self.FILE_SELECT_CODE)
            
        except ImportError:
            logging.debug("Mode développement : utilisation du sélecteur de fichiers alternatif")
            # Fallback vers le sélecteur de développement
            from dev_explo import show_file_explorer
            
            def file_callback(path):
                self.selected_file = path
                self.file_label.text = get_filename_without_extension(path)
            
            show_file_explorer(callback=file_callback, mode='file')
        except Exception as e:
            logging.error(f"Erreur lors de la sélection du fichier: {str(e)}", exc_info=True)
            self.status_label.text = f"Erreur: {str(e)}"

    def select_output_directory(self, instance):
        try:
            # Essayer d'abord la méthode Android native
            from android.storage import primary_external_storage_path
            from android.permissions import request_permissions, Permission
            from jnius import autoclass
            
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            Intent = autoclass('android.content.Intent')
            
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
            self.start_activity_for_result(intent, self.DIRECTORY_SELECT_CODE)
            
        except ImportError:
            # Fallback vers le sélecteur de développement
            from dev_explo import show_file_explorer
            
            def dir_callback(path):
                self.output_directory = path
                self.output_label.text = os.path.basename(path)
            
            show_file_explorer(callback=dir_callback, mode='folder')
        except Exception as e:
            self.status_label.text = f"Erreur: {str(e)}"

    def on_activity_result(self, request_code, result_code, intent):
        # Cette méthode sera appelée après la sélection d'un fichier ou dossier
        if result_code == -1:  # RESULT_OK
            uri = intent.getData()
            
            if request_code == self.FILE_SELECT_CODE:
                # Traitement de la sélection du fichier
                self.selected_file = self.get_path_from_uri(uri)
                self.file_label.text = get_filename_without_extension(self.selected_file)
                
            elif request_code == self.DIRECTORY_SELECT_CODE:
                # Traitement de la sélection du dossier
                self.output_directory = self.get_path_from_uri(uri)
                self.output_label.text = os.path.basename(self.output_directory)

    def get_path_from_uri(self, uri):
        # Conversion de l'URI Android en chemin de fichier
        from jnius import autoclass
        ContentUris = autoclass('android.content.ContentUris')
        Cursor = autoclass('android.database.Cursor')
        Uri = autoclass('android.net.Uri')
        
        try:
            # Obtenir le contexte de l'application
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity.getApplicationContext()
            
            # Obtenir le chemin réel à partir de l'URI
            cursor = context.getContentResolver().query(uri, None, None, None, None)
            if cursor and cursor.moveToFirst():
                path_index = cursor.getColumnIndex("_data")
                if path_index != -1:
                    path = cursor.getString(path_index)
                    cursor.close()
                    return path
                
            # Si _data n'est pas disponible, utiliser une autre méthode
            document_file = autoclass('androidx.documentfile.provider.DocumentFile')
            file = document_file.fromSingleUri(context, uri)
            if file:
                return file.getUri().getPath()
                
        except Exception as e:
            print(f"Erreur lors de la conversion de l'URI: {str(e)}")
            return str(uri)
        
        return str(uri)  # Retourne l'URI en string comme fallback

    def test_voice(self, instance):
        if self.voice_spinner.text == 'Sélectionner une voix':
            self.status_label.text = "Veuillez d'abord sélectionner une voix"
            return
        
        try:
            # Initialisation du TTS Android
            from jnius import autoclass
            Locale = autoclass('java.util.Locale')
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            # Obtenir le contexte de l'application
            context = PythonActivity.mActivity.getApplicationContext()
            
            # Créer l'instance TTS
            tts = TextToSpeech(context, None)
            tts.setLanguage(Locale.FRENCH)
            
            # Texte de démonstration
            demo_text = f"Bonjour, je suis {self.voice_spinner.text}, votre narrateur, et ma voix ressemblera à peu près à ça si je vous lis un livre."
            
            # Lire le texte
            tts.speak(demo_text, TextToSpeech.QUEUE_FLUSH, None)
            
            self.status_label.text = f"Test de la voix {self.voice_spinner.text}"
            
        except ImportError:
            self.status_label.text = "TTS Android non disponible en mode développement"
        except Exception as e:
            logging.error(f"Erreur lors du test de la voix: {str(e)}", exc_info=True)
            self.status_label.text = f"Erreur lors du test de la voix: {str(e)}"

    def analyze_document(self, instance):
        if not self.selected_file:
            logging.warning("Tentative d'analyse sans fichier sélectionné")
            self.status_label.text = "Veuillez d'abord sélectionner un fichier"
            return
            
        logging.info(f"Début de l'analyse du document: {self.selected_file}")
        self.status_label.text = "Analyse du document..."
        self.chapters = []

        try:
            from epub_processor import EpubProcessor
            processor = EpubProcessor()
            epub_chapters = processor.analyze_epub(self.selected_file)
            
            for chapter in epub_chapters:
                if chapter.title and chapter.content:
                    word_count = len(chapter.content.split())
                    self.chapters.append({
                        'title': chapter.title,
                        'content': chapter.content,
                        'word_count': word_count
                    })
            
            if self.chapters:
                logging.info(f"Analyse terminée : {len(self.chapters)} chapitres trouvés")
                self.status_label.text = f"{len(self.chapters)} chapitres trouvés"
                self.status_label.color = (0, 0, 0, 1)
                self.update_chapters_list()
            else:
                logging.warning("Aucun chapitre trouvé dans le document")
                self.status_label.text = "Aucun chapitre trouvé dans le document"
                self.status_label.color = (0, 0, 0, 1)
                
        except Exception as e:
            logging.error(f"Erreur lors de l'analyse: {str(e)}", exc_info=True)
            self.status_label.text = f"Erreur lors de l'analyse: {str(e)}"

    def update_chapters_list(self):
        logging.debug("Mise à jour de la liste des chapitres")
        self.chapters_list.clear_widgets()
        
        for i, chapter in enumerate(self.chapters, 1):
            chapter_text = (
                f"{i}. {chapter['title']}\n"
                f"   {chapter['word_count']} mots"
            )
            label = ChapterLabel(
                text=chapter_text,
                on_touch_down=lambda x, c=chapter: self.preview_chapter(c)
            )
            self.chapters_list.add_widget(label)

    def preview_chapter(self, chapter):
        # Afficher un aperçu du contenu du chapitre
        preview_text = chapter['content'][:100] + "..." if len(chapter['content']) > 100 else chapter['content']
        self.status_label.text = f"{chapter['title']}: {preview_text}"

    def start_conversion(self, instance):
        if not self.selected_file:
            self.status_label.text = "Veuillez sélectionner un fichier"
            return
        if not self.output_directory:
            self.status_label.text = "Veuillez sélectionner un dossier de destination"
            return
        if not self.chapters:
            self.status_label.text = "Veuillez d'abord analyser le document"
            return
        if self.voice_spinner.text == 'Sélectionner une voix':
            self.status_label.text = "Veuillez sélectionner une voix"
            return
        
        try:
            # Création du dossier de sortie avec le nom du fichier
            book_name = get_filename_without_extension(self.selected_file)
            output_folder = os.path.join(
                self.output_directory,
                sanitize_filename(book_name)
            )
            ensure_dir(output_folder)
            
            self.status_label.text = "Conversion en cours..."
            self.progress_bar.value = 0
            
            # Initialiser le TTS Android
            try:
                from jnius import autoclass
                Locale = autoclass('java.util.Locale')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                File = autoclass('java.io.File')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                
                # Obtenir le contexte de l'application
                context = PythonActivity.mActivity.getApplicationContext()
                
                tts = TextToSpeech(context, None)
                tts.setLanguage(Locale.FRENCH)  # ou autre langue selon vos besoins
                
                # Convertir chaque chapitre
                total_chapters = len(self.chapters)
                for i, chapter in enumerate(self.chapters, 1):
                    chapter_file = os.path.join(
                        output_folder,
                        f"{sanitize_filename(chapter['title'])}.wav"
                    )
                    
                    # Conversion TTS vers fichier audio
                    tts.synthesizeToFile(
                        chapter['content'],
                        None,  # Pas de paramètres supplémentaires
                        File(chapter_file)
                    )
                    
                    # Mise à jour de la progression
                    progress = (i / total_chapters) * 100
                    self.progress_bar.value = progress
                    self.status_label.text = f"Conversion : {i}/{total_chapters} chapitres"
                    
                self.status_label.text = "Conversion terminée !"
                
            except ImportError:
                self.status_label.text = "TTS Android non disponible en mode développement"
                
        except Exception as e:
            self.status_label.text = f"Erreur lors de la conversion : {str(e)}"

    def on_size(self, *args):
        # Ajustement du texte des labels à la largeur de l'écran
        width = self.width - dp(20)  # Marge de 10dp de chaque côté
        self.file_label.text_size = (width, None)
        self.output_label.text_size = (width, None)
        
        # Ajustement de la taille du texte si nécessaire
        if width < dp(200):  # Pour les écrans très étroits
            self.file_label.font_size = '12sp'
            self.output_label.font_size = '12sp'
        else:
            self.file_label.font_size = '14sp'
            self.output_label.font_size = '14sp'

if __name__ == '__main__':
    Window.clearcolor = (0.9, 0.9, 0.9, 1)
    EpubToAudioApp().run()