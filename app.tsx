import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetFooter } from "@/components/ui/sheet"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Menu, Book, FolderOpen, Volume2, Sun, Moon, Palette } from "lucide-react"

export default function Component() {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [theme, setTheme] = useState('normal')
  const chapters = Array.from({ length: 20 }, (_, i) => ({
    title: `Chapitre ${i + 1}: ${i % 3 === 0 ? 'Introduction' : i % 3 === 1 ? 'Développement' : 'Conclusion'}`,
    wordCount: Math.floor(Math.random() * 3000) + 500
  }))

  const themes = {
    normal: 'bg-white text-gray-900',
    night: 'bg-gray-900 text-white',
    sepia: 'bg-[#f1e7d0] text-gray-900',
    blue: 'bg-blue-100 text-gray-900',
    green: 'bg-green-100 text-gray-900',
    red: 'bg-red-100 text-gray-900'
  }

  const headerThemes = {
    normal: 'bg-gray-100',
    night: 'bg-gray-900',
    sepia: 'bg-[#e6d7b8]',
    blue: 'bg-blue-200',
    green: 'bg-green-200',
    red: 'bg-red-200'
  }

  const borderThemes = {
    normal: 'border-gray-100',
    night: 'border-gray-800',
    sepia: 'border-[#e6d7b8]',
    blue: 'border-blue-200',
    green: 'border-green-200',
    red: 'border-red-200'
  }

  const themeIcons = {
    normal: <Sun className="h-4 w-4 mr-2" />,
    night: <Moon className="h-4 w-4 mr-2" />,
    sepia: <Palette className="h-4 w-4 mr-2" />,
    blue: <Palette className="h-4 w-4 mr-2" />,
    green: <Palette className="h-4 w-4 mr-2" />,
    red: <Palette className="h-4 w-4 mr-2" />
  }

  const isNightTheme = theme === 'night'

  return (
    <div className={`flex flex-col h-screen ${themes[theme]}`}>
      <Sheet open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
        <header className={`border-b flex-none ${headerThemes[theme]}`}>
          <div className="flex items-center h-14 px-4">
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className={`mr-2 ${isNightTheme ? 'hover:bg-gray-800' : ''}`}>
                <Menu className="h-5 w-5" />
                <span className="sr-only">Menu</span>
              </Button>
            </SheetTrigger>
            <div className="flex items-center">
              <Book className={`h-6 w-6 mr-2 ${isNightTheme ? 'text-white' : 'text-primary'}`} />
              <span className="font-semibold">ePub to Audio</span>
            </div>
          </div>
        </header>
        <SheetContent side="left" className={`${themes[theme]} ${isNightTheme ? 'border-r border-gray-700' : ''} flex flex-col`}>
          <SheetHeader>
            <SheetTitle className={isNightTheme ? 'text-white' : ''}>Paramètres</SheetTitle>
          </SheetHeader>
          <div className="py-4 space-y-6 flex-grow">
            <div className="space-y-2">
              <Label htmlFor="tts-service" className={isNightTheme ? 'text-white' : ''}>Service TTS</Label>
              <Select onValueChange={(value) => console.log(value)}>
                <SelectTrigger id="tts-service" className={isNightTheme ? 'bg-gray-800 text-white border-gray-700' : ''}>
                  <SelectValue placeholder="Choisir un service TTS" />
                </SelectTrigger>
                <SelectContent className={isNightTheme ? 'bg-gray-800 text-white border-gray-700' : ''}>
                  <SelectItem value="google">Google TTS</SelectItem>
                  <SelectItem value="amazon">Amazon Polly</SelectItem>
                  <SelectItem value="microsoft">Microsoft Azure</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button 
              className="w-full" 
              variant={isNightTheme ? 'outline' : 'default'}
              onClick={() => alert("Test de la voix")}
              style={isNightTheme ? { backgroundColor: 'black', color: 'white', borderColor: 'white' } : {}}
            >
              <Volume2 className="mr-2 h-4 w-4" />
              Tester la voix
            </Button>
            <div className="space-y-2">
              <Label htmlFor="audio-format" className={isNightTheme ? 'text-white' : ''}>Format d'export audio</Label>
              <Select onValueChange={(value) => console.log(value)}>
                <SelectTrigger id="audio-format" className={isNightTheme ? 'bg-gray-800 text-white border-gray-700' : ''}>
                  <SelectValue placeholder="Choisir un format audio" />
                </SelectTrigger>
                <SelectContent className={isNightTheme ? 'bg-gray-800 text-white border-gray-700' : ''}>
                  <SelectItem value="mp3">MP3</SelectItem>
                  <SelectItem value="wav">WAV</SelectItem>
                  <SelectItem value="ogg">OGG</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="app-style" className={isNightTheme ? 'text-white' : ''}>Style de l'application</Label>
              <Select onValueChange={setTheme} defaultValue={theme}>
                <SelectTrigger id="app-style" className={isNightTheme ? 'bg-gray-800 text-white border-gray-700' : ''}>
                  <SelectValue placeholder="Choisir un style" />
                </SelectTrigger>
                <SelectContent className={isNightTheme ? 'bg-gray-800 text-white border-gray-700' : ''}>
                  <SelectItem value="normal">
                    {themeIcons.normal}
                    Normal
                  </SelectItem>
                  <SelectItem value="night">
                    {themeIcons.night}
                    Mode nuit
                  </SelectItem>
                  <SelectItem value="sepia">
                    {themeIcons.sepia}
                    Sépia
                  </SelectItem>
                  <SelectItem value="blue">
                    {themeIcons.blue}
                    Bleu clair
                  </SelectItem>
                  <SelectItem value="green">
                    {themeIcons.green}
                    Vert clair
                  </SelectItem>
                  <SelectItem value="red">
                    {themeIcons.red}
                    Rouge clair
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <SheetFooter>
            <p className={`text-sm ${isNightTheme ? 'text-white' : 'text-black'} w-full text-center pb-4`}>
              Version 0.1.10
            </p>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      <main className="flex-1 p-4 overflow-hidden">
        <div className="h-full max-w-2xl mx-auto flex flex-col">
          <div className={`border-2 border-dashed rounded-lg p-4 space-y-4 flex-1 overflow-hidden flex flex-col relative ${borderThemes[theme]}`}>
            <div 
              className="absolute inset-0 pointer-events-none" 
              style={{
                backgroundImage: `radial-gradient(${borderThemes[theme].replace('border-', '')} 1px, transparent 1px)`,
                backgroundSize: '20px 20px',
                opacity: 0.2,
              }}
            />
            <div className="space-y-4 flex-none relative">
              <div>
                <Label htmlFor="file" className={isNightTheme ? 'text-white' : ''}>Sélectionner un fichier ePub/PDF</Label>
                <div className="flex items-center gap-3 mt-1.5">
                  <Button 
                    size="sm" 
                    variant={isNightTheme ? 'outline' : 'default'} 
                    className="h-8"
                    style={isNightTheme ? { backgroundColor: 'black', color: 'white', borderColor: 'white' } : {}}
                  >
                    <FolderOpen className="mr-2 h-4 w-4" />
                    Choisir un fichier
                  </Button>
                  <span className={`text-sm ${isNightTheme ? 'text-gray-300' : 'text-muted-foreground'}`}>Les Immortelles - Thomas Bonicel.epub</span>
                </div>
              </div>

              <div>
                <Label htmlFor="folder" className={isNightTheme ? 'text-white' : ''}>Sélectionner un dossier d'export</Label>
                <div className="flex items-center gap-3 mt-1.5">
                  <Button 
                    size="sm" 
                    variant={isNightTheme ? 'outline' : 'default'} 
                    className="h-8"
                    style={isNightTheme ? { backgroundColor: 'black', color: 'white', borderColor: 'white' } : {}}
                  >
                    <FolderOpen className="mr-2 h-4 w-4" />
                    Choisir un dossier
                  </Button>
                  <span className={`text-sm ${isNightTheme ? 'text-gray-300' : 'text-muted-foreground'}`}>Aucun dossier sélectionné</span>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button 
                  variant={isNightTheme ? 'outline' : 'default'} 
                  className={isNightTheme ? 'bg-black text-white hover:bg-gray-800' : 'bg-black text-white hover:bg-black/90'}
                  style={isNightTheme ? { borderColor: 'white' } : {}}
                >
                  Analyser
                </Button>
                <Button variant={isNightTheme ? 'secondary' : 'secondary'}>Convertir</Button>
              </div>
            </div>

            <div className="flex-1 overflow-hidden flex flex-col min-h-0 relative">
              <h3 className={`font-medium mb-2 ${isNightTheme ? 'text-white' : ''}`}>Chapitres extraits</h3>
              <ScrollArea className={`flex-1 border rounded-md ${isNightTheme ? 'border-gray-700' : ''}`}>
                <div className="p-2 space-y-2">
                  {chapters.map((chapter, index) => (
                    <div key={index} className={`flex items-center justify-between rounded-lg px-4 py-2 text-sm ${isNightTheme ? 'bg-gray-800 text-white' : 'bg-white'}`}>
                      <span>{chapter.title}</span>
                      <span className={isNightTheme ? 'text-gray-300' : 'text-muted-foreground'}>{chapter.wordCount} mots</span>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}