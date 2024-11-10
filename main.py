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
import traceback  # Importer traceback au début de la fonction

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
        # Initialisation des processeurs pour ePub et PDF
        self.epub_processor = EpubProcessor()
        self.pdf_processor = PdfProcessor()
        self.is_android = platform == 'android'
        
        if self.is_android:
            self.ensure_permissions()
            self.android_voices = self.get_android_tts_voices()
        else:
            self.android_voices = []

        # Initialisation de la boucle asyncio
        if not platform == 'android':
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            Logger.info('Boucle asyncio initialisée')

        self.context = None
        if platform == 'android':
            self.context = autoclass('org.kivy.android.PythonActivity').mActivity
        else:
            self.context = webview.windows[0] if webview.windows else None

        # Paramètres par défaut pour le traitement par lots
        self.batch_size = 5
        self.retry_count = 20
        self.retry_delays = {
            10: 0,      # Pas de pause jusqu'à 10 tentatives
            20: 30,     # 30 secondes de pause entre 10-20
            30: 60,     # 1 minute de pause entre 20-30
            40: 90,     # 1 minute 30 entre 30-40
            50: 120     # 2 minutes entre 40-50
        }

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

    def select_file(self, params=None):
        """Ouvre un dialogue de sélection de fichier"""
        try:
            Logger.info('='*50)
            Logger.info('DÉBUT DE LA SÉLECTION DE FICHIER')
            Logger.info(f'Paramètres reçus: {params}')
            
            if self.is_android and not self.check_storage_permission():
                self.ensure_permissions()
                return {'status': 'error', 'message': 'Permissions de stockage requises'}
            
            if self.is_android:
                return self._select_file_android()
            else:
                # Si des paramètres sont fournis, les utiliser
                if params and isinstance(params, dict):
                    return self._select_file_desktop(
                        filters=params.get('filters'),
                        default_path=params.get('defaultPath')
                    )
                else:
                    return self._select_file_desktop()
        except Exception as e:
            Logger.error(f'Error selecting file: {str(e)}')
            return {'status': 'error', 'message': str(e)}
        finally:
            Logger.info('FIN DE LA SÉLECTION DE FICHIER')
            Logger.info('='*50)

    def _select_file_desktop(self, filters=None, default_path=None):
        """Sélection de fichier pour desktop"""
        try:
            # Déterminer le système d'exploitation
            system = sys_platform.system()
            Logger.info(f'Système détecté: {system}')
            
            # Format correct pour les filtres selon l'OS
            if system == 'Darwin':  # macOS
                file_types = [
                    'ePub files (*.epub)',
                    'PDF files (*.pdf)'
                ]
                Logger.info(f'Types de fichiers configurés pour macOS: {file_types}')
            elif system == 'Windows':
                file_types = [
                    'ePub files (*.epub)',
                    'PDF files (*.pdf)'
                ]
                Logger.info(f'Types de fichiers configurés pour Windows: {file_types}')
            else:  # Linux et autres
                file_types = [
                    '*.epub',
                    '*.pdf'
                ]
                Logger.info(f'Types de fichiers configurés pour Linux: {file_types}')
            
            # Traiter le chemin par défaut
            if default_path:
                default_path = os.path.expanduser(default_path)
            else:
                if system == 'Darwin':  # macOS
                    default_path = os.path.expanduser('~/Documents')
                elif system == 'Windows':
                    default_path = os.path.expandvars('%USERPROFILE%\\Documents')
                else:  # Linux et autres
                    default_path = os.path.expanduser('~/Documents')
            
            Logger.info(f'Dossier par défaut: {default_path}')
            
            # Créer le dialogue de sélection
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                directory=default_path,
                allow_multiple=False,
                file_types=file_types
            )
            
            if result is None:
                Logger.info('Sélection annulée par l\'utilisateur')
                return {'status': 'cancelled'}
            
            if not result:
                Logger.info('Aucun fichier sélectionné')
                return {'status': 'cancelled'}
            
            file_path = result[0]
            file_name = os.path.basename(file_path)
            
            Logger.info(f'Fichier sélectionné: {file_name}')
            Logger.info(f'Chemin complet: {file_path}')
            
            return {
                'status': 'success',
                'path': file_path,
                'name': file_name
            }
            
        except Exception as e:
            Logger.error(f'Erreur lors de la sélection: {str(e)}')
            Logger.error(f'Type d\'erreur: {type(e).__name__}')
            Logger.error(f'Traceback: {traceback.format_exc()}')
            return {'status': 'error', 'message': str(e)}

    def select_folder(self, params=None):
        """Ouvre un dialogue de sélection de dossier"""
        try:
            Logger.info('='*50)
            Logger.info('DÉBUT DE LA SÉLECTION DE DOSSIER')
            Logger.info(f'Paramètres reçus: {params}')
            
            if self.is_android and not self.check_storage_permission():
                self.ensure_permissions()
                return {'status': 'error', 'message': 'Permissions de stockage requises'}
            
            if self.is_android:
                return self._select_folder_android()
            else:
                # Si des paramètres sont fournis, les utiliser
                if params and isinstance(params, dict):
                    return self._select_folder_desktop(
                        default_path=params.get('defaultPath')
                    )
                else:
                    return self._select_folder_desktop()
        except Exception as e:
            Logger.error(f'Error selecting folder: {str(e)}')
            return {'status': 'error', 'message': str(e)}
        finally:
            Logger.info('FIN DE LA SÉLECTION DE DOSSIER')
            Logger.info('='*50)

    def _select_folder_desktop(self, default_path=None):
        """Sélection de dossier pour desktop"""
        try:
            # Déterminer le système d'exploitation
            system = sys_platform.system()
            Logger.info(f'Système détecté: {system}')
            
            # Traiter le chemin par défaut
            if default_path:
                default_path = os.path.expanduser(default_path)
            else:
                if system == 'Darwin':  # macOS
                    default_path = os.path.expanduser('~/Documents')
                elif system == 'Windows':
                    default_path = os.path.expandvars('%USERPROFILE%\\Documents')
                else:  # Linux et autres
                    default_path = os.path.expanduser('~/Documents')
                
            Logger.info(f'Dossier par défaut: {default_path}')
            
            # Créer le dialogue de sélection
            result = webview.windows[0].create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=default_path
            )
            
            if result is None:
                Logger.info('Sélection annulée par l\'utilisateur')
                return {'status': 'cancelled'}
            
            if not result:
                Logger.info('Aucun dossier sélectionné')
                return {'status': 'cancelled'}
            
            folder_path = result[0]
            folder_name = os.path.basename(folder_path)
            
            Logger.info(f'Dossier sélectionné: {folder_name}')
            Logger.info(f'Chemin complet: {folder_path}')
            
            return {
                'status': 'success',
                'path': folder_path,
                'name': folder_name
            }
            
        except Exception as e:
            Logger.error(f'Erreur lors de la sélection: {str(e)}')
            Logger.error(f'Type d\'erreur: {type(e).__name__}')
            Logger.error(f'Traceback: {traceback.format_exc()}')
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
        Logger.info('='*50)
        Logger.info('DÉBUT DU TEST DE VOIX')
        Logger.info(f'Service demandé: {service}')
        Logger.info(f'Voix demandée: {voice}')
        Logger.info(f'Plateforme: {"Android" if self.is_android else "Desktop"}')
        
        # Créer un fichier temporaire qui s'auto-détruira
        temp_file = None
        
        try:
            if service == 'edge':
                Logger.info('Initialisation du service Edge TTS')
                
                try:
                    import edge_tts
                    Logger.info('Module edge-tts trouvé et importé')
                    Logger.info(f'Version edge-tts: {edge_tts.__version__}')
                except ImportError as e:
                    Logger.error(f'Module edge-tts non trouvé: {str(e)}')
                    return {'status': 'error', 'message': 'Module edge-tts non installé'}

                # Vérifier la voix
                try:
                    Logger.info('Vérification de la disponibilité de la voix...')
                    voices = asyncio.run(edge_tts.list_voices())
                    voice_exists = any(v["ShortName"] == voice for v in voices)
                    if not voice_exists:
                        Logger.error(f'La voix {voice} n\'existe pas')
                        return {'status': 'error', 'message': f'La voix {voice} n\'existe pas'}
                    Logger.info('Voix trouvée et valide')
                except Exception as e:
                    Logger.error(f'Erreur lors de la vérification de la voix: {str(e)}')
                    return {'status': 'error', 'message': str(e)}

                # Synthèse vocale
                try:
                    Logger.info('Création de la tâche de synthèse vocale')
                    
                    # Créer un fichier temporaire avec une extension .mp3
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                        temp_file = tmp.name
                        Logger.info(f'Fichier temporaire créé: {temp_file}')
                    
                    async def do_tts():
                        communicate = edge_tts.Communicate(
                            "Bonjour, je suis votre narrateur, et voilà à quoi devrait ressembler un texte lu par moi.",
                            voice
                        )
                        await communicate.save(temp_file)
                    
                    # Exécuter la synthèse de manière synchrone
                    Logger.info('Exécution de la synthèse vocale')
                    asyncio.run(do_tts())
                    
                    if os.path.exists(temp_file):
                        Logger.info(f'Fichier audio créé avec succès: {temp_file}')
                        
                        # Lecture du fichier audio selon l'OS
                        try:
                            system = sys_platform.system()
                            Logger.info(f'Système d\'exploitation détecté: {system}')
                            
                            if system == 'Darwin':  # macOS
                                Logger.info('Utilisation de afplay pour la lecture')
                                os.system(f'afplay "{temp_file}"')
                                time.sleep(2)  # Attendre la fin de la lecture
                                
                            elif system == 'Windows':
                                Logger.info('Utilisation de Windows Media Player pour la lecture')
                                try:
                                    import winsound
                                    winsound.PlaySound(temp_file, winsound.SND_FILENAME)
                                except ImportError:
                                    # Alternative avec PowerShell si winsound n'est pas disponible
                                    Logger.info('Utilisation de PowerShell pour la lecture')
                                    os.system(f'powershell -c (New-Object Media.SoundPlayer "{temp_file}").PlaySync()')
                                
                            elif system == 'Linux':
                                # Essayer plusieurs lecteurs audio courants sur Linux
                                players = ['aplay', 'paplay', 'mpg123']
                                played = False
                                
                                for player in players:
                                    try:
                                        Logger.info(f'Tentative de lecture avec {player}')
                                        exit_code = os.system(f'which {player} > /dev/null 2>&1')
                                        if exit_code == 0:  # Le lecteur est installé
                                            os.system(f'{player} "{temp_file}"')
                                            played = True
                                            Logger.info(f'Lecture réussie avec {player}')
                                            break
                                    except Exception as e:
                                        Logger.error(f'Échec de la lecture avec {player}: {str(e)}')
                                
                                if not played:
                                    Logger.error('Aucun lecteur audio disponible sur ce système Linux')
                                    return {'status': 'error', 'message': 'Aucun lecteur audio disponible'}
                                
                                else:
                                    Logger.info('Lecture audio terminée avec succès')
                                    return {'status': 'success'}
                                
                            else:
                                Logger.error(f'Système d\'exploitation non supporté: {system}')
                                return {'status': 'error', 'message': 'Système d\'exploitation non supporté'}
                                
                        except Exception as e:
                            Logger.error(f'Erreur lors de la lecture audio: {str(e)}')
                            Logger.error(f'Type d\'erreur: {type(e).__name__}')
                            Logger.error(traceback.format_exc())
                            return {'status': 'error', 'message': 'Erreur lors de la lecture audio'}
                        
                        return {'status': 'success'}
                    else:
                        Logger.error('Le fichier audio n\'a pas été créé')
                        return {'status': 'error', 'message': 'Échec de la création du fichier audio'}
                        
                except Exception as e:
                    Logger.error(f'Erreur lors de la synthèse vocale: {str(e)}')
                    return {'status': 'error', 'message': str(e)}
                
            elif service == 'google' and self.is_android:
                Logger.info('Initialisation du service Google TTS Android')
                
                try:
                    from jnius import autoclass
                    Logger.info('Import de jnius réussi')
                    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                    Logger.info('Classe TextToSpeech chargée')
                    
                    def onInit(status):
                        Logger.info(f'Callback onInit appelé avec status: {status}')
                        if status == TextToSpeech.SUCCESS:
                            Logger.info('Initialisation TTS réussie')
                            if voice:
                                Logger.info(f'Recherche de la voix: {voice}')
                                available_voices = tts.getVoices()
                                Logger.info(f'Voix disponibles: {[v.getName() for v in available_voices]}')
                                for v in available_voices:
                                    if v.getName() == voice:
                                        Logger.info(f'Voix trouvée et sélectionnée: {voice}')
                                        tts.setVoice(v)
                                        break
                            
                            Logger.info('Début de la synthèse vocale...')
                            result = tts.speak(
                                "Bonjour, je suis votre narrateur, et voilà à quoi devrait ressembler un texte lu par moi.",
                                TextToSpeech.QUEUE_FLUSH,
                                None
                            )
                            Logger.info(f'Résultat de speak(): {result}')
                        else:
                            Logger.error(f'Échec de l\'initialisation TTS Android: {status}')
                    
                    Logger.info('Création de l\'instance TextToSpeech')
                    tts = TextToSpeech(self.activity, onInit)
                    Logger.info('Instance TextToSpeech créée')
                    return {'status': 'success'}
                    
                except Exception as e:
                    Logger.error(f'Erreur lors de l\'initialisation de Google TTS: {str(e)}')
                    Logger.error(f'Type d\'erreur: {type(e).__name__}')
                    return {'status': 'error', 'message': str(e)}
            else:
                Logger.warning(f'Service non supporté: {service}')
                return {'status': 'error', 'message': 'Service non supporté'}
                
        finally:
            # Attendre un peu avant de supprimer le fichier pour s'assurer que la lecture est terminée
            time.sleep(3)
            
            # Nettoyer le fichier temporaire
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    Logger.info(f'Fichier temporaire supprimé: {temp_file}')
                except Exception as e:
                    Logger.error(f'Erreur lors de la suppression du fichier temporaire: {str(e)}')
            
            Logger.info('FIN DU TEST DE VOIX')
            Logger.info('='*50)

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

    def update_batch_settings(self, params):
        """Met à jour les paramètres de traitement par lots"""
        try:
            Logger.info('='*50)
            Logger.info('MISE À JOUR DES PARAMÈTRES DE TRAITEMENT')
            
            if 'batchSize' in params:
                self.batch_size = min(max(1, params['batchSize']), 20)
                Logger.info(f'Nouvelle taille de lot: {self.batch_size}')
                
            if 'retryCount' in params:
                self.retry_count = min(max(10, params['retryCount']), 50)
                Logger.info(f'Nouveau nombre de tentatives: {self.retry_count}')
                
                # Déterminer le délai de pause approprié
                for limit, delay in sorted(self.retry_delays.items()):
                    if self.retry_count <= limit:
                        Logger.info(f'Délai de pause configuré: {delay} secondes')
                        break
            
            return {'status': 'success'}
            
        except Exception as e:
            Logger.error(f'Erreur lors de la mise à jour des paramètres: {str(e)}')
            return {'status': 'error', 'message': str(e)}
        finally:
            Logger.info('FIN DE LA MISE À JOUR DES PARAMÈTRES')
            Logger.info('='*50)

def main():
    try:
        Logger.info('='*50)
        Logger.info('DÉMARRAGE DE L\'APPLICATION')
        
        api = ApiInterface()
        Logger.info('API Interface créée')
        
        # Chemins des fichiers
        base_dir = os.path.dirname(__file__)
        html_path = os.path.join(base_dir, 'assets', 'index.html')
        
        Logger.info(f'Chemin HTML: {html_path}')
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        Logger.info('Fichier HTML chargé')
        
        Logger.info('Création de la fenêtre...')
        window = webview.create_window(
            'ePub to Audio',
            html=html_content,
            js_api=api,
            min_size=(350, 600),
            width=350,
            resizable=True
        )
        Logger.info('Fenêtre créée')
        
        Logger.info('Démarrage de webview...')
        webview.start(debug=True)
        Logger.info('Webview démarré')
        
    except Exception as e:
        Logger.error('ERREUR CRITIQUE:')
        Logger.error(str(e))
        Logger.error(traceback.format_exc())
        raise
    finally:
        Logger.info('FIN DU PROGRAMME')
        Logger.info('='*50)

if __name__ == '__main__':
    main() 