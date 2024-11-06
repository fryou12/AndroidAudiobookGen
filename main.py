import webview
import json
import os
from epub_processor import EpubProcessor, PdfProcessor, clean_tmp
from kivy.logger import Logger
from kivy.utils import platform
import asyncio
import edge_tts
import tempfile
import platform as sys_platform  # Renommé pour éviter la confusion avec platform de kivy
from functools import partial
from pathlib import Path
import time

# Ajout des imports pour Android
if platform == 'android':
    from jnius import autoclass, cast, PythonJavaClass, java_method
    from android.runnable import run_on_ui_thread
    from android.permissions import request_permissions, check_permission, Permission

    # Classes Java nécessaires
    Uri = autoclass('android.net.Uri')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    DocumentFile = autoclass('androidx.documentfile.provider.DocumentFile')

    class ActivityResultListener(PythonJavaClass):
        __javainterfaces__ = ['org/kivy/android/PythonActivity$ActivityResultListener']
        
        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        @java_method('(IILandroid/content/Intent;)V')
        def onActivityResult(self, requestCode, resultCode, data):
            self.callback(requestCode, resultCode, data)

class ApiInterface:
    def __init__(self):
        self.epub_processor = EpubProcessor()
        self.pdf_processor = PdfProcessor()
        self.is_android = platform == 'android'
        
        if self.is_android:
            self.ensure_permissions()
            self.android_voices = self.get_android_tts_voices()
        else:
            self.android_voices = []

        self.loop = None
        if not platform == 'android':
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def ensure_permissions(self):
        """Vérifie et demande les permissions nécessaires"""
        required_permissions = [
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ]
        
        # Vérifier chaque permission
        missing_permissions = [
            p for p in required_permissions 
            if not check_permission(p)
        ]
        
        if missing_permissions:
            request_permissions(missing_permissions)

    def check_storage_permission(self):
        """Vérifie si les permissions de stockage sont accordées"""
        if not self.is_android:
            return True
            
        return (check_permission(Permission.READ_EXTERNAL_STORAGE) and 
                check_permission(Permission.WRITE_EXTERNAL_STORAGE))

    def select_file(self):
        """Ouvre un dialogue de sélection de fichier"""
        try:
            if self.is_android and not self.check_storage_permission():
                self.ensure_permissions()
                return {'status': 'error', 'message': 'Permissions de stockage requises'}
            
            if self.is_android:
                return self._select_file_android()
            else:
                return self._select_file_desktop()
        except Exception as e:
            Logger.error(f'Error selecting file: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _select_file_desktop(self):
        """Sélection de fichier pour desktop"""
        try:
            file_types = ('ePub Files (*.epub)', 'PDF Files (*.pdf)')
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=file_types
            )
            
            if result and len(result) > 0:
                file_path = result[0]
                return {
                    'status': 'success',
                    'path': file_path,
                    'name': os.path.basename(file_path)
                }
            return {'status': 'error', 'message': 'Aucun fichier sélectionné'}
        except Exception as e:
            Logger.error(f'Error in _select_file_desktop: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def select_folder(self):
        """Ouvre un dialogue de sélection de dossier"""
        try:
            if self.is_android and not self.check_storage_permission():
                self.ensure_permissions()
                return {'status': 'error', 'message': 'Permissions de stockage requises'}
            
            if self.is_android:
                return self._select_folder_android()
            else:
                return self._select_folder_desktop()
        except Exception as e:
            Logger.error(f'Error selecting folder: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _select_folder_desktop(self):
        """Sélection de dossier pour desktop"""
        try:
            result = webview.windows[0].create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=os.path.expanduser('~')
            )
            
            if result and len(result) > 0:
                folder_path = result[0]
                return {
                    'status': 'success',
                    'path': folder_path,
                    'name': os.path.basename(folder_path)
                }
            return {'status': 'error', 'message': 'Aucun dossier sélectionné'}
        except Exception as e:
            Logger.error(f'Error in _select_folder_desktop: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _handle_activity_result(self, requestCode, resultCode, data):
        """Gère les résultats des activités Android"""
        if not self.is_android:
            return
            
        RESULT_OK = -1  # Constante Android
        
        try:
            if resultCode != RESULT_OK or data is None:
                return
                
            if requestCode == 1:  # Sélection de fichier
                uri = data.getData()
                if uri:
                    # Obtenir le chemin réel du fichier
                    file_path = self._get_real_path_from_uri(uri)
                    file_name = self._get_file_name_from_uri(uri)
                    
                    if self.pending_file_callback:
                        self.pending_file_callback({
                            'status': 'success',
                            'path': file_path,
                            'name': file_name
                        })
                        
            elif requestCode == 2:  # Sélection de dossier
                uri = data.getData()
                if uri:
                    # Obtenir le chemin réel du dossier
                    folder_path = self._get_real_path_from_uri(uri)
                    folder_name = self._get_file_name_from_uri(uri)
                    
                    if self.pending_folder_callback:
                        self.pending_folder_callback({
                            'status': 'success',
                            'path': folder_path,
                            'name': folder_name
                        })
                        
        except Exception as e:
            Logger.error(f'Error handling activity result: {str(e)}')
            if requestCode == 1 and self.pending_file_callback:
                self.pending_file_callback({
                    'status': 'error',
                    'message': str(e)
                })
            elif requestCode == 2 and self.pending_folder_callback:
                self.pending_folder_callback({
                    'status': 'error',
                    'message': str(e)
                })

    def _get_real_path_from_uri(self, uri):
        """Convertit un URI Android en chemin de fichier réel"""
        try:
            from jnius import autoclass
            ContentUris = autoclass('android.content.ContentUris')
            DocumentsContract = autoclass('android.provider.DocumentsContract')
            MediaStore = autoclass('android.provider.MediaStore')
            
            if DocumentsContract.isDocumentUri(self.activity, uri):
                # Document URI
                docId = DocumentsContract.getDocumentId(uri)
                
                if uri.getAuthority() == "com.android.externalstorage.documents":
                    # ExternalStorageProvider
                    split = docId.split(":")
                    type = split[0]
                    
                    if "primary".equalsIgnoreCase(type):
                        return f"{Environment.getExternalStorageDirectory()}/{split[1]}"
                
                # Autres providers...
                
            elif "content".equalsIgnoreCase(uri.getScheme()):
                # MediaStore (et général)
                return self._get_data_column(uri, None, None)
            elif "file".equalsIgnoreCase(uri.getScheme()):
                # File
                return uri.getPath()
                
            return None
        except Exception as e:
            Logger.error(f"Error getting real path: {str(e)}")
            return uri.getPath()

    def _get_file_name_from_uri(self, uri):
        """Obtient le nom du fichier à partir de l'URI"""
        if not self.is_android:
            return "Fichier sélectionné"
            
        context = cast('android.content.Context', self.activity)
        doc_file = DocumentFile.fromSingleUri(context, uri)
        return doc_file.getName() if doc_file else "Fichier sélectionné"

    def _select_file_android(self):
        """Sélection de fichier spécifique à Android"""
        try:
            from android.storage import primary_external_storage_path
            from jnius import autoclass
            
            Intent = autoclass('android.content.Intent')
            Environment = autoclass('android.os.Environment')
            
            # Créer l'intent pour la sélection de fichier
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.setType("*/*")
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.putExtra(Intent.EXTRA_LOCAL_ONLY, True)
            
            # Filtres pour les types de fichiers
            mime_types = ["application/epub+zip", "application/pdf"]
            intent.putExtra(Intent.EXTRA_MIME_TYPES, mime_types)
            
            # Accorder les permissions de lecture persistantes
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            
            # Lancer l'activité
            self.activity.startActivityForResult(intent, 1)
            
            return {'status': 'pending', 'message': 'Sélection en cours...'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _select_folder_android(self):
        """Sélection de dossier spécifique à Android"""
        try:
            from jnius import autoclass
            
            Intent = autoclass('android.content.Intent')
            
            # Créer l'intent pour la sélection de dossier
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            
            # Lancer l'activité
            self.activity.startActivityForResult(intent, 2)
            
            return {'status': 'pending', 'message': 'Sélection en cours...'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def analyze_file(self, file_path):
        """Analyse un fichier ePub ou PDF"""
        try:
            if not os.path.exists(file_path):
                return {'status': 'error', 'message': 'Le fichier n\'existe pas'}
                
            if file_path.lower().endswith('.epub'):
                chapters = self.epub_processor.analyze_epub(file_path)
                # Convertir les objets Chapter en dictionnaires pour JSON
                chapters_data = [
                    {
                        'title': chapter.title,
                        'content': chapter.content,
                        'content_src': chapter.content_src
                    }
                    for chapter in chapters
                ]
                return {'status': 'success', 'chapters': chapters_data}
            elif file_path.lower().endswith('.pdf'):
                chapters = self.pdf_processor.analyze_pdf(file_path)
                return {'status': 'success', 'chapters': chapters}
            else:
                return {'status': 'error', 'message': 'Format de fichier non supporté'}
        except Exception as e:
            Logger.error(f'Error analyzing file: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def convert_to_audio(self, params):
        """Convertit le fichier en audio"""
        try:
            file_path = params.get('file_path')
            output_folder = params.get('output_folder')
            service = params.get('service')
            voice = params.get('voice')
            BATCH_SIZE = 3

            if not all([file_path, output_folder, service]):
                return {'status': 'error', 'message': 'Paramètres manquants'}

            # Analyser le fichier pour obtenir les chapitres
            if file_path.lower().endswith('.epub'):
                chapters = self.epub_processor.analyze_epub(file_path)
                chapters_data = [
                    {
                        'title': chapter.title,
                        'content': chapter.content,
                        'processed': False,
                        'attempts': 0
                    }
                    for chapter in chapters
                ]
            else:
                return {'status': 'error', 'message': 'Format de fichier non supporté'}

            total_chapters = len(chapters_data)
            book_name = Path(file_path).stem
            output_dir = Path(output_folder) / book_name
            output_dir.mkdir(parents=True, exist_ok=True)

            if service == 'edge':
                # Code existant pour Edge TTS
                # ... (garder le code Edge TTS existant)
                pass
                
            elif service == 'google' and self.is_android:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                File = autoclass('java.io.File')
                HashMap = autoclass('java.util.HashMap')
                
                def process_android_tts():
                    processed_count = 0
                    
                    def onInit(status):
                        nonlocal processed_count
                        if status == TextToSpeech.SUCCESS:
                            # Configurer la voix si spécifiée
                            if voice:
                                for v in tts.getVoices():
                                    if v.getName() == voice:
                                        tts.setVoice(v)
                                        break
                            
                            # Traiter les chapitres par lots
                            for i in range(0, len(chapters_data), BATCH_SIZE):
                                batch = chapters_data[i:i + BATCH_SIZE]
                                for chapter in batch:
                                    if not chapter['processed']:
                                        try:
                                            # Préparer le fichier de sortie
                                            clean_title = "".join(x for x in chapter['title'] if x.isalnum() or x in (' ', '-', '_'))
                                            output_file = output_dir / f"{processed_count+1:02d}_{clean_title}.mp3"
                                            
                                            # Paramètres de synthèse
                                            params = HashMap()
                                            params.put(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, str(processed_count))
                                            
                                            # Synthétiser le texte
                                            result = tts.synthesizeToFile(
                                                chapter['content'],
                                                params,
                                                str(output_file)
                                            )
                                            
                                            if result == TextToSpeech.SUCCESS:
                                                chapter['processed'] = True
                                                processed_count += 1
                                                # Mettre à jour la progression
                                                progress = int((processed_count / total_chapters) * 100)
                                                self.update_progress(progress)
                                        except Exception as e:
                                            Logger.error(f"Erreur lors de la conversion du chapitre {processed_count}: {str(e)}")
                                            chapter['attempts'] += 1
                
                    tts = TextToSpeech(self.activity, onInit)
                    
                    # Attendre que tous les chapitres soient traités ou aient échoué
                    while processed_count < total_chapters:
                        time.sleep(0.1)
                    
                    tts.shutdown()
                    return processed_count
                
                # Exécuter la conversion
                successful_chapters = process_android_tts()
                failed_chapters = total_chapters - successful_chapters
                
                # Envoyer la progression finale
                self.update_progress(100 if failed_chapters == 0 else int((successful_chapters / total_chapters) * 100))
                
                if failed_chapters == 0:
                    return {'status': 'success', 'message': f'Conversion terminée. {successful_chapters} chapitres convertis.'}
                else:
                    return {
                        'status': 'partial_success',
                        'message': f'Conversion partielle. {successful_chapters} chapitres convertis, {failed_chapters} échecs.'
                    }
            else:
                return {'status': 'error', 'message': 'Service non supporté'}

        except Exception as e:
            Logger.error(f'Error converting to audio: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def update_progress(self, progress):
        """Met à jour la progression dans l'interface"""
        try:
            js_code = f"window.dispatchEvent(new CustomEvent('conversionProgress', {{detail: {progress}}}));"
            webview.windows[0].evaluate_js(js_code)
        except Exception as e:
            Logger.error(f'Error updating progress: {str(e)}')

    def clean_temp_files(self):
        """Nettoie les fichiers temporaires"""
        try:
            if self.current_test_file and os.path.exists(self.current_test_file):
                os.remove(self.current_test_file)
            clean_tmp()
            return {'status': 'success'}
        except Exception as e:
            Logger.error(f'Error cleaning temp files: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def test_voice(self, service, voice=None):
        """Teste la voix sélectionnée"""
        try:
            if service == 'edge':
                # Utiliser run_coroutine_threadsafe pour les opérations asynchrones
                async def async_test():
                    communicate = edge_tts.Communicate(
                        "Bonjour, je suis votre narrateur, et voilà à quoi devrait ressembler un texte lu par moi.",
                        voice
                    )
                    await communicate.save("test.mp3")
                
                future = asyncio.run_coroutine_threadsafe(async_test(), self.loop)
                future.result()  # Attendre le résultat
                return {'status': 'success'}
            elif service == 'google' and self.is_android:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                
                def onInit(status):
                    if status == TextToSpeech.SUCCESS:
                        if voice:
                            for v in tts.getVoices():
                                if v.getName() == voice:
                                    tts.setVoice(v)
                                    break
                        tts.speak("Bonjour, je suis votre narrateur, et voilà à quoi devrait ressembler un texte lu par moi.",
                                 TextToSpeech.QUEUE_FLUSH, None)
                
                tts = TextToSpeech(self.activity, onInit)
                return {'status': 'success'}
            else:
                return {'status': 'error', 'message': 'Service non supporté'}
            
        except Exception as e:
            Logger.error(f'Error testing voice: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def get_android_tts_voices(self):
        """Récupère les voix disponibles sur Android"""
        if not self.is_android:
            return []
            
        try:
            from jnius import autoclass
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            Context = autoclass('android.content.Context')
            Locale = autoclass('java.util.Locale')
            
            tts = TextToSpeech(self.activity, None)
            voices = tts.getVoices()
            
            available_voices = []
            for voice in voices:
                if voice.getLocale().getLanguage() == "fr":  # Filtrer les voix françaises
                    available_voices.append({
                        'id': voice.getName(),
                        'name': f"{voice.getLocale().getDisplayLanguage()} - {voice.getName()}",
                        'locale': voice.getLocale().toString()
                    })
            
            tts.shutdown()
            return available_voices
        except Exception as e:
            Logger.error(f'Error getting Android TTS voices: {str(e)}')
            return []

def main():
    api = ApiInterface()
    
    # Charger le fichier HTML
    html_path = os.path.join(os.path.dirname(__file__), 'assets', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    if platform == 'android':
        # Configuration spécifique pour Android
        from kivy.core.window import Window
        Window.softinput_mode = 'below_target'
        
    # Créer la fenêtre avec l'API exposée
    window = webview.create_window(
        'ePub to Audio',
        html=html_content,
        js_api=api,
        min_size=(350, 600),
        width=350,
        resizable=True
    )
    
    # Démarrer l'application
    webview.start(debug=True)

if __name__ == '__main__':
    main() 