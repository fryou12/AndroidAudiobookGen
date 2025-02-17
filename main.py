import os
import sys
import time
import json
import asyncio
import platform as sys_platform
import traceback
import tempfile
from threading import Thread
from pathlib import Path
from functools import partial

import webview
import edge_tts
from epub_processor import EpubProcessor, PdfProcessor, clean_tmp

# Imports pour Android
platform = sys_platform.system().lower()
is_android = platform == 'android'

if is_android:
    from jnius import autoclass, cast, PythonJavaClass, java_method
    from android.runnable import run_on_ui_thread
    from android.permissions import request_permissions, check_permission, Permission

    # Classes Java nécessaires
    Uri = autoclass('android.net.Uri')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    DocumentFile = autoclass('androidx.documentfile.provider.DocumentFile')

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
                print('Boucle asyncio initialisée')

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
            print('='*50)
            print('DÉBUT DE LA SÉLECTION DE FICHIER')
            print(f'Paramètres reçus: {params}')
            
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
            print(f'Error selecting file: {str(e)}')
            return {'status': 'error', 'message': str(e)}
        finally:
            print('FIN DE LA SÉLECTION DE FICHIER')
            print('='*50)

    def _select_file_desktop(self, filters=None, default_path=None):
        """Sélection de fichier pour desktop"""
        try:
            # Déterminer le système d'exploitation
            system = sys_platform.system()
            print(f'Système détecté: {system}')
            
            # Format correct pour les filtres selon l'OS
            if system == 'Darwin':  # macOS
                file_types = [
                    'ePub files (*.epub)',
                    'PDF files (*.pdf)'
                ]
                print(f'Types de fichiers configurés pour macOS: {file_types}')
            elif system == 'Windows':
                file_types = [
                    'ePub files (*.epub)',
                    'PDF files (*.pdf)'
                ]
                print(f'Types de fichiers configurés pour Windows: {file_types}')
            else:  # Linux et autres
                file_types = [
                    '*.epub',
                    '*.pdf'
                ]
                print(f'Types de fichiers configurés pour Linux: {file_types}')
            
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
            
            print(f'Dossier par défaut: {default_path}')
            
            # Créer le dialogue de sélection
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                directory=default_path,
                allow_multiple=False,
                file_types=file_types
            )
            
            if result is None:
                print('Sélection annulée par l\'utilisateur')
                return {'status': 'cancelled'}
            
            if not result:
                print('Aucun fichier sélectionné')
                return {'status': 'cancelled'}
            
            file_path = result[0]
            file_name = os.path.basename(file_path)
            
            print(f'Fichier sélectionné: {file_name}')
            print(f'Chemin complet: {file_path}')
            
            return {
                'status': 'success',
                'path': file_path,
                'name': file_name
            }
            
        except Exception as e:
            print(f'Erreur lors de la sélection: {str(e)}')
            print(f'Type d\'erreur: {type(e).__name__}')
            print(f'Traceback: {traceback.format_exc()}')
            return {'status': 'error', 'message': str(e)}

    def select_folder(self, params=None):
        """Ouvre un dialogue de sélection de dossier"""
        try:
            print('='*50)
            print('DÉBUT DE LA SÉLECTION DE DOSSIER')
            print(f'Paramètres reçus: {params}')
            
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
            print(f'Error selecting folder: {str(e)}')
            return {'status': 'error', 'message': str(e)}
        finally:
            print('FIN DE LA SÉLECTION DE DOSSIER')
            print('='*50)

    def _select_folder_desktop(self, default_path=None):
        """Sélection de dossier pour desktop"""
        try:
            # Déterminer le système d'exploitation
            system = sys_platform.system()
            print(f'Système détecté: {system}')
            
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
                
            print(f'Dossier par défaut: {default_path}')
            
            # Créer le dialogue de sélection
            result = webview.windows[0].create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=default_path
            )
            
            if result is None:
                print('Sélection annulée par l\'utilisateur')
                return {'status': 'cancelled'}
            
            if not result:
                print('Aucun dossier sélectionné')
                return {'status': 'cancelled'}
            
            folder_path = result[0]
            folder_name = os.path.basename(folder_path)
            
            print(f'Dossier sélectionné: {folder_name}')
            print(f'Chemin complet: {folder_path}')
            
            return {
                'status': 'success',
                'path': folder_path,
                'name': folder_name
            }
            
        except Exception as e:
            print(f'Erreur lors de la sélection: {str(e)}')
            print(f'Type d\'erreur: {type(e).__name__}')
            print(f'Traceback: {traceback.format_exc()}')
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
            print(f'Error handling activity result: {str(e)}')
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
            print(f"Error getting real path: {str(e)}")
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

    async def get_edge_voices(self):
        """Récupère la liste des voix edge-tts de manière asynchrone"""
        try:
            print('Récupération des voix edge-tts...')
            voices = await edge_tts.list_voices()
            print(f'Structure d\'une voix: {voices[0] if voices else "Aucune voix trouvée"}')
            
            # Filtrer les voix françaises et créer un mapping des noms courts
            fr_voices = []
            voice_mapping = {}
            
            for voice in voices:
                if voice['Locale'].startswith('fr'):
                    voice_info = {
                        'id': voice['ShortName'],
                        'name': voice['FriendlyName'],
                        'locale': voice['Locale'],
                        'gender': voice['Gender']
                    }
                    fr_voices.append(voice_info)
                    
                    # Créer un mapping pour les versions non-multilingues
                    if 'Multilingual' in voice['ShortName']:
                        base_name = voice['ShortName'].replace('Multilingual', '')
                        voice_mapping[base_name] = voice['ShortName']
            
            print(f'Voix françaises trouvées: {len(fr_voices)}')
            for voice in fr_voices:
                print(f"Voix disponible: {voice['id']} ({voice['gender']}) - {voice['name']}")
            
            print('Mapping des voix:')
            for old_name, new_name in voice_mapping.items():
                print(f"{old_name} -> {new_name}")
            
            return {'status': 'success', 'voices': fr_voices, 'mapping': voice_mapping}
        except Exception as e:
            print(f'Erreur lors de la récupération des voix: {str(e)}')
            print(f'Type d\'erreur: {type(e).__name__}')
            print(f'Traceback: {traceback.format_exc()}')
            return {'status': 'error', 'message': str(e)}

    def convert_voice_id(self, voice_id):
        """Convertit l'ancien format d'ID de voix vers le nouveau format avec Multilingual si nécessaire"""
        voice_mapping = {
            'fr-FR-VivienneNeural': 'fr-FR-VivienneMultilingualNeural',
            'fr-FR-RemyNeural': 'fr-FR-RemyMultilingualNeural'
        }
        return voice_mapping.get(voice_id, voice_id)

    def get_voices(self, service):
        """Récupère la liste des voix disponibles pour un service donné"""
        try:
            print('='*50)
            print('RÉCUPÉRATION DES VOIX')
            print(f'Service demandé: {service}')

            if service == 'edge':
                if not platform == 'android':
                    # Exécuter de manière asynchrone
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(self.get_edge_voices())
                    loop.close()
                    print('Récupération des voix terminée')
                    return result
                else:
                    return {'status': 'error', 'message': 'Edge TTS non disponible sur Android'}
            elif service == 'google' and self.is_android:
                voices = self.get_android_tts_voices()
                return {'status': 'success', 'voices': voices}
            else:
                return {'status': 'error', 'message': 'Service non supporté'}
        except Exception as e:
            print(f'Erreur lors de la récupération des voix: {str(e)}')
            return {'status': 'error', 'message': str(e)}
        finally:
            print('FIN DE LA RÉCUPÉRATION DES VOIX')
            print('='*50)

    async def do_tts(self, text, voice, output_file):
        """Effectue la synthèse vocale de manière asynchrone"""
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)
            return True
        except Exception as e:
            print(f'Erreur lors de la synthèse vocale: {str(e)}')
            return False

    def test_voice(self, service, voice=None):
        """Teste la voix sélectionnée"""
        print('='*50)
        print('DÉBUT DU TEST DE VOIX')
        print(f'[Service demandé] {service}')
        print(f'[Voix demandée] {voice}')
        print(f'[Plateforme  ] {"Android" if self.is_android else "Desktop"}')
        
        # Convertir l'ID de la voix si nécessaire
        if voice:
            voice = self.convert_voice_id(voice)
            print(f'[ID de voix converti] {voice}')
        
        temp_file = None
        
        try:
            if service == 'edge':
                if self.is_android:
                    return {'status': 'error', 'message': 'Edge TTS non disponible sur Android'}
                
                print('Initialisation du service Edge TTS')
                print('Module edge-tts trouvé et importé')
                print(f'[Version edge-tts] {edge_tts.__version__}')
                
                # Vérifier la voix
                voices_result = self.get_voices('edge')
                print(f'Résultat get_voices: {voices_result}')
                
                if voices_result['status'] == 'error':
                    return voices_result
                    
                voice_exists = any(v["id"] == voice for v in voices_result['voices'])
                if not voice_exists:
                    print(f'La voix {voice} n\'existe pas')
                    return {'status': 'error', 'message': f'La voix {voice} n\'existe pas'}
                
                # Synthèse vocale
                try:
                    # Créer un fichier temporaire avec une extension .mp3
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                        temp_file = tmp.name
                        print(f'Fichier temporaire créé: {temp_file}')
                    
                    # Texte de présentation
                    presentation_text = "Bonjour, je suis votre narrateur, et voilà à quoi devrait ressembler un texte lu par moi."
                    print('Texte de présentation prêt')
                    
                    # Créer un nouveau loop pour la synthèse
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(self.do_tts(presentation_text, voice, temp_file))
                    loop.close()
                    
                    if not success:
                        return {'status': 'error', 'message': 'Échec de la synthèse vocale'}
                    
                    print('Synthèse vocale terminée')
                    
                    if os.path.exists(temp_file):
                        file_size = os.path.getsize(temp_file)
                        print(f'Fichier audio créé avec succès: {temp_file} ({file_size} octets)')
                        
                        # Lecture du fichier audio
                        system = sys_platform.system()
                        print(f'Système d\'exploitation détecté: {system}')
                        
                        if system == 'Darwin':  # macOS
                            cmd = f'afplay "{temp_file}"'
                            print(f'Exécution de la commande: {cmd}')
                            result = os.system(cmd)
                            print(f'Résultat de la commande: {result}')
                            time.sleep(5)  # Attendre la fin de la lecture
                            return {'status': 'success'}
                        
                        elif system == 'Windows':
                            try:
                                import winsound
                                winsound.PlaySound(temp_file, winsound.SND_FILENAME)
                            except ImportError:
                                os.system(f'powershell -c (New-Object Media.SoundPlayer "{temp_file}").PlaySync()')
                            return {'status': 'success'}
                        
                        elif system == 'Linux':
                            for player in ['aplay', 'paplay', 'mpg123']:
                                try:
                                    if os.system(f'which {player} > /dev/null 2>&1') == 0:
                                        os.system(f'{player} "{temp_file}"')
                                        return {'status': 'success'}
                                except Exception as e:
                                    print(f'Échec avec {player}: {str(e)}')
                            return {'status': 'error', 'message': 'Aucun lecteur audio disponible'}
                        
                        else:
                            return {'status': 'error', 'message': 'Système non supporté'}
                    else:
                        return {'status': 'error', 'message': 'Fichier audio non créé'}
                
                except Exception as e:
                    print(f'Erreur lors de la synthèse/lecture: {str(e)}')
                    return {'status': 'error', 'message': str(e)}
            
            elif service == 'google' and self.is_android:
                # Code Android inchangé...
                pass
            
            else:
                return {'status': 'error', 'message': 'Service non supporté'}
                
        finally:
            # Nettoyage
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    print('Fichier temporaire supprimé')
                except Exception as e:
                    print(f'Erreur lors de la suppression du fichier temporaire: {str(e)}')
            
            print('FIN DU TEST DE VOIX')
            print('='*50)

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
            print(f'Error analyzing file: {str(e)}')
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
                                            print(f"Erreur lors de la conversion du chapitre {processed_count}: {str(e)}")
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
            print(f'Error converting to audio: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def update_progress(self, progress):
        """Met à jour la progression dans l'interface"""
        try:
            js_code = f"window.dispatchEvent(new CustomEvent('conversionProgress', {{detail: {progress}}}));"
            webview.windows[0].evaluate_js(js_code)
        except Exception as e:
            print(f'Error updating progress: {str(e)}')

    def clean_temp_files(self):
        """Nettoie les fichiers temporaires"""
        try:
            if self.current_test_file and os.path.exists(self.current_test_file):
                os.remove(self.current_test_file)
            clean_tmp()
            return {'status': 'success'}
        except Exception as e:
            print(f'Error cleaning temp files: {str(e)}')
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
            print(f'Error getting Android TTS voices: {str(e)}')
            return []

    def update_batch_settings(self, params):
        """Met à jour les paramètres de traitement par lots"""
        try:
            print('='*50)
            print('MISE À JOUR DES PARAMÈTRES DE TRAITEMENT')
            
            if 'batchSize' in params:
                self.batch_size = min(max(1, params['batchSize']), 20)
                print(f'Nouvelle taille de lot: {self.batch_size}')
                
            if 'retryCount' in params:
                self.retry_count = min(max(10, params['retryCount']), 50)
                print(f'Nouveau nombre de tentatives: {self.retry_count}')
                
                # Déterminer le délai de pause approprié
                for limit, delay in sorted(self.retry_delays.items()):
                    if self.retry_count <= limit:
                        print(f'Délai de pause configuré: {delay} secondes')
                        break
            
            return {'status': 'success'}
            
        except Exception as e:
            print(f'Erreur lors de la mise à jour des paramètres: {str(e)}')
            return {'status': 'error', 'message': str(e)}
        finally:
            print('FIN DE LA MISE À JOUR DES PARAMÈTRES')
            print('='*50)

def main():
    try:
        print('='*50)
        print('DÉMARRAGE DE L\'APPLICATION')
        
        api = ApiInterface()
        print('API Interface créée')
        
        # Chemins des fichiers
        base_dir = os.path.dirname(__file__)
        html_path = os.path.join(base_dir, 'assets', 'index.html')
        icon_path = os.path.join(base_dir, 'assets', 'icons', 'iconset', 'icon_256x256.png')
        
        print(f'Chemin HTML: {html_path}')
        print(f'Chemin icône: {icon_path}')
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        print('Fichier HTML chargé')
        
        print('Création de la fenêtre...')
        
        # Configuration de webview
        webview.WINDOW_TITLE_MIN_LENGTH = 1  # Permettre des titres courts
        
        # Définir l'icône selon la plateforme
        if sys_platform.system() == 'Darwin':  # macOS
            import webview.platforms.cocoa as cocoa
            if hasattr(cocoa, 'BrowserView'):
                cocoa.BrowserView.app_icon = icon_path
            
            # Configuration NSApplication
            from AppKit import NSApplication, NSImage
            app = NSApplication.sharedApplication()
            if os.path.exists(icon_path):
                image = NSImage.alloc().initWithContentsOfFile_(icon_path)
                app.setApplicationIconImage_(image)
        
        # Créer la fenêtre
        window = webview.create_window(
            'ePub to Audio',
            html=html_content,
            js_api=api,
            width=360,
            height=650,
        )
        
        print('Fenêtre créée')
        
        print('Démarrage de webview...')
        webview.start(debug=True)
        print('Webview démarré')
        
    except Exception as e:
        print('ERREUR CRITIQUE')
        print(str(e))
        print(traceback.format_exc())
    finally:
        print('FIN DU PROGRAMME')
        print('='*50)

if __name__ == '__main__':
    main()