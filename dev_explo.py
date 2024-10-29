from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.metrics import dp

class FileExplorerPopup(Popup):
    def __init__(self, callback, mode='file', **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.mode = mode  # 'file' ou 'folder'
        
        self.title = "Sélectionner un fichier" if mode == 'file' else "Sélectionner un dossier"
        self.size_hint = (0.9, 0.9)
        
        layout = BoxLayout(orientation='vertical')
        
        # Créer le FileChooser
        self.file_chooser = FileChooserListView(
            path='.',  # Commence dans le dossier courant
            filters=['*.epub'] if mode == 'file' else [],
            dirselect=True if mode == 'folder' else False
        )
        
        # Boutons
        buttons = BoxLayout(
            size_hint_y=None, 
            height=dp(50),
            spacing=dp(10),
            padding=dp(10)
        )
        
        select_btn = Button(text='Sélectionner')
        cancel_btn = Button(text='Annuler')
        
        select_btn.bind(on_press=self.select_path)
        cancel_btn.bind(on_press=self.dismiss)
        
        buttons.add_widget(select_btn)
        buttons.add_widget(cancel_btn)
        
        layout.add_widget(self.file_chooser)
        layout.add_widget(buttons)
        
        self.content = layout

    def select_path(self, instance):
        if self.file_chooser.selection:
            selected = self.file_chooser.selection[0]
            self.callback(selected)
        self.dismiss()

def show_file_explorer(callback, mode='file'):
    """
    Fonction utilitaire pour afficher le sélecteur de fichiers
    
    Args:
        callback: Fonction à appeler avec le chemin sélectionné
        mode: 'file' ou 'folder'
    """
    popup = FileExplorerPopup(callback=callback, mode=mode)
    popup.open()
