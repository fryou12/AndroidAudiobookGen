import os
import zipfile
import shutil
import re
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTTextLine, LTChar
import re
from collections import defaultdict, OrderedDict
import logging
import tempfile
from pathlib import Path

class EpubProcessor:
    class Chapter:
        def __init__(self, title, content_src, content=''):
            self.title = title
            self.content_src = content_src
            self.content = content

        def display_chapter_details(self):
            title = self.title if self.title else "Chapitre"
            content = self.content if self.content else "Contenu non disponible"
            print(f"{title} : {content[:100]}")  # Affiche les 100 premiers caractères du contenu

    def __init__(self):
        self.chapters = []
        # Modèle de titre de chapitre valide
        self.valid_chapter_pattern = re.compile(r'^(?:chapitre|chapter)\s+\d+\.?$', re.IGNORECASE)

    def is_valid_chapter_title(self, title):
        """Vérifie si le titre correspond à un format de chapitre valide."""
        # Nettoyer le titre
        clean_title = title.strip().lower()
        return bool(self.valid_chapter_pattern.match(clean_title))

    def clean_chapters(self, chapters):
        """Nettoie la liste des chapitres en supprimant les doublons et faux positifs."""
        logging.info("Nettoyage des chapitres détectés")
        
        # Grouper les chapitres par nombre de mots
        chapters_by_words = defaultdict(list)
        for chapter in chapters:
            word_count = len(chapter.content.split())
            chapters_by_words[word_count].append(chapter)
        
        cleaned_chapters = []
        for word_count, chapter_group in chapters_by_words.items():
            if len(chapter_group) > 1:
                # S'il y a plusieurs chapitres avec le même nombre de mots
                logging.warning(f"Chapitres en doublon détectés ({word_count} mots): {[c.title for c in chapter_group]}")
                
                # Garder uniquement le chapitre avec un titre valide
                valid_chapters = [c for c in chapter_group if self.is_valid_chapter_title(c.title)]
                
                if valid_chapters:
                    cleaned_chapters.extend(valid_chapters)
                else:
                    # Si aucun titre valide, prendre le premier par défaut
                    cleaned_chapters.append(chapter_group[0])
                    logging.warning(f"Aucun titre valide trouvé parmi les doublons: {[c.title for c in chapter_group]}")
            else:
                cleaned_chapters.append(chapter_group[0])
        
        # Trier les chapitres par numéro
        def extract_chapter_number(chapter):
            match = re.search(r'\d+', chapter.title)
            return int(match.group()) if match else float('inf')
        
        cleaned_chapters.sort(key=extract_chapter_number)
        
        return cleaned_chapters

    def extract_metadata(self, epub_path):
        chapters = []
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('ncx'):
                    with zip_ref.open(file, 'r') as ncx_file:
                        soup = BeautifulSoup(ncx_file, 'xml')
                        nav_points = soup.find_all('navPoint')
                        for nav_point in nav_points:
                            title = nav_point.find('text').text.strip()
                            if not title.endswith('.'):
                                title += '.'
                            content_src = nav_point.find('content').get('src')
                            chapters.append(self.Chapter(title, content_src))
        return chapters

    def extract_content_from_archive(self, epub_path):
        # Créer un dossier temporaire unique dans le dossier temp du système
        temp_dir = os.path.join(tempfile.gettempdir(), 'epub_temp_' + str(os.getpid()))
        os.makedirs(temp_dir, exist_ok=True)
        
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return temp_dir

    def extract_text_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                text_content = soup.get_text(separator='\n', strip=True)
                text_content = re.sub(r'(?<!\n)\n(?!\n)', ' ', text_content)  # Merge single newlines
                return text_content
        except Exception as e:
            logging.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
            return ''

    def analyze_epub(self, epub_path):
        self.chapters = self.extract_metadata(epub_path)
        temp_dir = self.extract_content_from_archive(epub_path)
        text_by_file = {}

        try:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(('.html', '.htm', '.xhtml')):
                        file_path = os.path.join(root, file)
                        text_content = self.extract_text_from_file(file_path)
                        text_by_file[file] = text_content.strip()

            for chapter in self.chapters:
                content_src = chapter.content_src
                if content_src:
                    file_name = os.path.basename(content_src.split('#')[0])
                    file_candidates = [file for file in text_by_file if file_name in file]

                    if file_candidates:
                        chapter.content = text_by_file.get(file_candidates[0], '')
                        if len(file_candidates) > 1:
                            logging.warning(f"Plusieurs fichiers correspondent à content_src {content_src}: {file_candidates}")
                    else:
                        logging.warning(f"Aucun fichier ne correspond à content_src {content_src}")
                        chapter.content = ''

                    if not chapter.content.strip():
                        logging.warning(f"Attention: le chapitre '{chapter.title}' est vide. Vérifiez le fichier source {content_src}.")

                chapter.content = re.sub(r'\s+', ' ', chapter.content).strip()

            # Nettoyer les chapitres avant de les retourner
            self.chapters = self.clean_chapters(self.chapters)

        finally:
            shutil.rmtree(temp_dir)

        return self.chapters

import re

def clean_and_format_text(text):
    # Supprimer les sauts de ligne multiples
    text = re.sub(r'\n{2,}', '\n\n', text)
    
    # Joindre les lignes qui ne se terminent pas par un point, sauf si la ligne suivante commence par une majuscule
    lines = text.split('\n')
    formatted_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if not line.endswith(('.', '!', '?', ':', '"', "'")) and (not next_line or not next_line[0].isupper()):
                formatted_lines.append(line + ' ')
            else:
                formatted_lines.append(line + '\n')
        else:
            formatted_lines.append(line)
    
    formatted_text = ''.join(formatted_lines)
    
    # Supprimer les espaces multiples
    formatted_text = re.sub(r' {2,}', ' ', formatted_text)
    
    return formatted_text.strip()

class PdfProcessor:
    def __init__(self):
        pass

    def extract_text_and_fonts_from_pdf(self, pdf_path):
        laparams = LAParams()
        text_content = []

        # Extract text and font information from each page
        for page_layout in extract_pages(pdf_path, laparams=laparams):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        if isinstance(text_line, LTTextLine):
                            line_text = text_line.get_text().strip()
                            font_sizes = [char.size for char in text_line if isinstance(char, LTChar)]
                            if font_sizes:
                                max_font_size = max(font_sizes)
                                text_content.append((line_text, max_font_size))

        return text_content

    def detect_chapters(self, text_content):
        chapters = []
        chapter_pattern = re.compile(r'^(Chapter|Chapitre|Part|Section|Titre)\s+\d+.*$', re.IGNORECASE)
        
        current_chapter = None
        chapter_content = []

        # Define a threshold for font size to consider it as a chapter title
        if text_content:
            title_font_size_threshold = max(font_size for _, font_size in text_content) * 0.9
        else:
            title_font_size_threshold = 0

        for line, font_size in text_content:
            if chapter_pattern.match(line) or font_size >= title_font_size_threshold:
                if current_chapter:
                    chapter_text = '\n'.join(chapter_content)
                    # Appliquer le nettoyage et la mise en forme ici
                    chapter_text = clean_and_format_text(chapter_text)
                    chapters.append({'title': current_chapter, 'content': chapter_text})
                    chapter_content = []
                current_chapter = line
            else:
                if current_chapter:  # Only add content if we have a current chapter
                    chapter_content.append(line)

        # Add the last chapter
        if current_chapter:
            chapter_text = '\n'.join(chapter_content)
            # Appliquer le nettoyage et la mise en forme ici
            chapter_text = clean_and_format_text(chapter_text)
            chapters.append({'title': current_chapter, 'content': chapter_text})

        if not chapters:
            print("Aucun chapitre détecté. Vérifiez l'expression régulière ou la structure du texte.")
        
        return chapters

    def analyze_pdf(self, pdf_path):
        text_content = self.extract_text_and_fonts_from_pdf(pdf_path)
        return self.detect_chapters(text_content)

def clean_tmp():
    # Nettoyer tous les dossiers temporaires créés par l'application
    temp_base = tempfile.gettempdir()
    patterns = ['epub_temp_*', 'audiobook_temp*']
    
    for pattern in patterns:
        for temp_dir in Path(temp_base).glob(pattern):
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logging.info(f"Dossier temporaire supprimé : {temp_dir}")
            except Exception as e:
                logging.error(f"Erreur lors de la suppression du dossier temporaire {temp_dir}: {e}")

# Assurez-vous que clean_tmp est exportée si vous utilisez __all__
__all__ = ['EpubProcessor', 'PdfProcessor', 'clean_tmp']