Python 3.12.5 (v3.12.5:ff3bc82f7c9, Aug  7 2024, 05:32:06) [Clang 13.0.0 (clang-1300.0.29.30)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
>>> import org.apache.pdfbox.pdmodel.PDDocument
... import org.apache.pdfbox.text.PDFTextStripper
... import nl.siegmann.epublib.domain.Book
... import nl.siegmann.epublib.domain.Resource
... import nl.siegmann.epublib.epub.EpubReader
... import java.io.*
... import java.util.regex.Pattern
... import java.util.zip.ZipFile
... 
... class EpubProcessor {
... 
...     data class Chapter(
...         val title: String?,
...         val contentSrc: String,
...         val content: String?
...     ) {
...         fun displayChapterDetails() {
...             val chapterTitle = title ?: "Chapitre"
...             val chapterContent = content ?: "Contenu non disponible"
...             println("$chapterTitle : ${chapterContent.take(100)}")
...         }
...     }
... 
...     private val chapters = mutableListOf<Chapter>()
...     private val validChapterPattern = Pattern.compile("^(?:chapitre|chapter|section)\\s+\\d+", Pattern.CASE_INSENSITIVE)
... 
...     fun addChapter(chapter: Chapter) {
...         chapters.add(chapter)
...     }
... 
...     fun displayAllChapters() {
...         chapters.forEach { it.displayChapterDetails() }
...     }
... 
...     fun processEpub(filePath: String) {
...         try {
            val epubFileStream = FileInputStream(filePath)
            val book: Book = EpubReader().readEpub(epubFileStream)

            for (resource: Resource in book.contents) {
                val content = resource.data.toString(Charsets.UTF_8)
                val title = resource.title
                addChapter(Chapter(title, resource.href, content))
            }
        } catch (e: Exception) {
            println("Erreur lors du traitement de l'EPUB : ${e.message}")
        }
    }

    fun processPdf(filePath: String) {
        try {
            PDDocument.load(File(filePath)).use { document ->
                val pdfStripper = PDFTextStripper()
                val text = pdfStripper.getText(document)
                addChapter(Chapter("PDF Content", filePath, text))
            }
        } catch (e: Exception) {
            println("Erreur lors du traitement du PDF : ${e.message}")
        }
    }

    fun extractTextFromZip(zipFilePath: String) {
        try {
            ZipFile(zipFilePath).use { zipFile ->
                zipFile.entries().asSequence().forEach { entry ->
                    if (!entry.isDirectory && entry.name.endsWith(".html")) {
                        val stream = zipFile.getInputStream(entry)
                        val content = stream.bufferedReader().use { it.readText() }
                        val title = entry.name
                        addChapter(Chapter(title, entry.name, content))
                    }
                }
            }
        } catch (e: Exception) {
            println("Erreur lors de l'extraction des fichiers ZIP : ${e.message}")
        }
    }

    companion object {
        @JvmStatic
        fun main(args: Array<String>) {
            val processor = EpubProcessor()

            // Exemple d'utilisation
            processor.processEpub("chemin/vers/fichier.epub")
            processor.processPdf("chemin/vers/fichier.pdf")
            processor.extractTextFromZip("chemin/vers/fichier.zip")

            processor.displayAllChapters()
        }
    }
}
