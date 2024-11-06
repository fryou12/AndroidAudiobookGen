Python 3.12.5 (v3.12.5:ff3bc82f7c9, Aug  7 2024, 05:32:06) [Clang 13.0.0 (clang-1300.0.29.30)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import nl.siegmann.epublib.domain.Book;
import nl.siegmann.epublib.domain.Resource;
import nl.siegmann.epublib.epub.EpubReader;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

public class EpubProcessor {

    public static class Chapter {
        private String title;
        private String contentSrc;
        private String content;

        public Chapter(String title, String contentSrc, String content) {
            this.title = title;
            this.contentSrc = contentSrc;
            this.content = content;
        }

        public void displayChapterDetails() {
            String chapterTitle = (title != null) ? title : "Chapitre";
            String chapterContent = (content != null) ? content : "Contenu non disponible";
            System.out.println(chapterTitle + " : " + chapterContent.substring(0, Math.min(100, chapterContent.length())));
        }
    }

    private List<Chapter> chapters;
    private Pattern validChapterPattern;

    public EpubProcessor() {
        this.chapters = new ArrayList<>();
        this.validChapterPattern = Pattern.compile("^(?:chapitre|chapter|section)\\s+\\d+", Pattern.CASE_INSENSITIVE);
    }

    public void addChapter(Chapter chapter) {
        chapters.add(chapter);
    }

    public void displayAllChapters() {
        for (Chapter chapter : chapters) {
            chapter.displayChapterDetails();
        }
    }

    public void processEpub(String filePath) {
        try (InputStream epubFileStream = new FileInputStream(filePath)) {
            Book book = (new EpubReader()).readEpub(epubFileStream);

            for (Resource resource : book.getContents()) {
                String content = new String(resource.getData());
                String title = resource.getTitle();
                addChapter(new Chapter(title, resource.getHref(), content));
            }
        } catch (Exception e) {
            System.err.println("Erreur lors du traitement de l'EPUB : " + e.getMessage());
        }
    }

    public void processPdf(String filePath) {
        try (PDDocument document = PDDocument.load(new File(filePath))) {
            PDFTextStripper pdfStripper = new PDFTextStripper();
...             String text = pdfStripper.getText(document);
...             addChapter(new Chapter("PDF Content", filePath, text));
...         } catch (Exception e) {
...             System.err.println("Erreur lors du traitement du PDF : " + e.getMessage());
...         }
...     }
... 
...     public void extractTextFromZip(String zipFilePath) {
...         try (ZipFile zipFile = new ZipFile(zipFilePath)) {
...             Enumeration<? extends ZipEntry> entries = zipFile.entries();
... 
...             while (entries.hasMoreElements()) {
...                 ZipEntry entry = entries.nextElement();
...                 if (!entry.isDirectory() && entry.getName().endsWith(".html")) {
...                     InputStream stream = zipFile.getInputStream(entry);
...                     String content = new String(stream.readAllBytes());
...                     String title = entry.getName();
...                     addChapter(new Chapter(title, entry.getName(), content));
...                     stream.close();
...                 }
...             }
...         } catch (Exception e) {
...             System.err.println("Erreur lors de l'extraction des fichiers ZIP : " + e.getMessage());
...         }
...     }
... 
...     public static void main(String[] args) {
...         EpubProcessor processor = new EpubProcessor();
... 
...         // Exemple d'utilisation
...         processor.processEpub("chemin/vers/fichier.epub");
...         processor.processPdf("chemin/vers/fichier.pdf");
...         processor.extractTextFromZip("chemin/vers/fichier.zip");
... 
...         processor.displayAllChapters();
...     }
... }
