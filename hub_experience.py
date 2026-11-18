"""Shared visual tokens and localized workspace controls."""
COPY = {
    "verify_note": ("Checks the main executable against the reference saved after installation through Hub. Other application files are not scanned.", "Сравнивает основной EXE с образцом, сохранённым после установки через Hub. Другие файлы приложения не сканируются.", "Compară executabilul cu referința salvată după instalarea prin Hub. Alte fișiere nu sunt scanate.", "Prüft die Programmdatei anhand der über Hub installierten Referenz. Andere Dateien werden nicht geprüft.", "Compara el ejecutable con la referencia instalada mediante Hub. No analiza otros archivos.", "Compare l’exécutable à la référence installée via Hub. Les autres fichiers ne sont pas analysés."),
    "connect": ("Build your library", "Собери свою библиотеку", "Creează-ți biblioteca", "Deine Bibliothek aufbauen", "Crea tu biblioteca", "Créez votre bibliothèque"),
    "search": ("Search your universe…", "Поиск в твоей вселенной…", "Caută în universul tău…", "Dein Universum durchsuchen…", "Busca en tu universo…", "Rechercher dans votre univers…"),
    "favorites": ("Favorites", "Избранное", "Favorite", "Favoriten", "Favoritos", "Favoris"),
    "all": ("All products", "Все продукты", "Toate produsele", "Alle Produkte", "Todos los productos", "Tous les produits"),
    "recent": ("Recently launched", "Недавние запуски", "Lansate recent", "Zuletzt gestartet", "Abiertos recientemente", "Lancements récents"),
    "name": ("Name A–Z", "Название А–Я", "Nume A–Z", "Name A–Z", "Nombre A–Z", "Nom A–Z"),
    "activity": ("Activity", "Активность", "Activitate", "Aktivität", "Actividad", "Activité"),
    "activity_empty": ("Your installs, updates and launches will appear here.", "Здесь появятся установки, обновления и запуски.", "Instalările, actualizările și lansările vor apărea aici.", "Installationen, Updates und Starts erscheinen hier.", "Aquí aparecerán instalaciones, actualizaciones y aperturas.", "Vos installations, mises à jour et lancements apparaîtront ici."),
    "locate": ("Locate installed app", "Подключить установленное", "Găsește aplicația instalată", "Installierte App finden", "Localizar aplicación instalada", "Localiser une application installée"),
    "open_folder": ("Open folder", "Открыть папку", "Deschide folderul", "Ordner öffnen", "Abrir carpeta", "Ouvrir le dossier"),
    "verify": ("Verify app file", "Проверить файл приложения", "Verifică fișierul aplicației", "App-Datei prüfen", "Verificar archivo", "Vérifier le fichier"),
    "verified": ("The main executable matches the verified installation baseline.", "Основной исполняемый файл совпадает с проверенной установленной копией.", "Executabilul corespunde copiei instalate verificate.", "Die Programmdatei entspricht der geprüften Installation.", "El ejecutable coincide con la instalación verificada.", "L’exécutable correspond à l’installation vérifiée."),
    "no_baseline": ("No verified baseline is available. Reinstall from the official release to establish one.", "Нет проверенного образца. Переустановите приложение из официального релиза, чтобы сохранить его.", "Nu există o copie verificată. Reinstalează din versiunea oficială.", "Keine geprüfte Referenz vorhanden. Bitte offiziell neu installieren.", "No hay referencia verificada. Reinstala desde la versión oficial.", "Aucune référence vérifiée. Réinstallez la version officielle."),
    "changed": ("The app file has changed. This may be an external update; reinstall from the official release to restore a verified copy.", "Файл изменился, возможно после внешнего обновления. Переустановка из официального релиза восстановит проверенную копию.", "Fișierul s-a schimbat. Reinstalează versiunea oficială.", "Die Datei wurde geändert. Bitte die offizielle Version neu installieren.", "El archivo cambió. Reinstala la versión oficial.", "Le fichier a changé. Réinstallez la version officielle."),
    "no_results": ("No matches. Try another search or filter.", "Ничего не найдено. Измените запрос или фильтр.", "Niciun rezultat. Schimbă căutarea sau filtrul.", "Keine Treffer. Suche oder Filter ändern.", "Sin resultados. Cambia la búsqueda o el filtro.", "Aucun résultat. Modifiez la recherche ou le filtre."),
    "read": ("Read release notes", "Читать об обновлении", "Citește noutățile", "Versionshinweise lesen", "Leer novedades", "Lire les nouveautés"),
    "diagnostics": ("Export diagnostics", "Сохранить диагностику", "Exportă diagnosticul", "Diagnose exportieren", "Exportar diagnóstico", "Exporter le diagnostic"),
    "diagnostics_note": ("Exports versions and recent operation results only. No local paths or game settings are included. Nothing is uploaded.", "Сохраняются версии и результаты последних операций. Пути и настройки игр не включаются. Ничего не отправляется.", "Exportă doar versiunile și rezultatele operațiunilor. Nu trimite date.", "Exportiert Versionen und Ergebnisse ohne lokale Pfade. Kein Upload.", "Exporta versiones y resultados sin rutas locales. No se envían datos.", "Exporte les versions et résultats sans chemins locaux. Aucun envoi."),
    "cache": ("Clear downloaded installers", "Очистить загрузки установщиков", "Șterge instalatoarele descărcate", "Geladene Installer löschen", "Borrar instaladores descargados", "Effacer les installateurs téléchargés"),
    "cache_note": ("Installed apps, preferences and news remain available.", "Приложения, настройки и новости сохранятся.", "Aplicațiile, setările și știrile rămân disponibile.", "Apps, Einstellungen und Nachrichten bleiben erhalten.", "Se conservan aplicaciones, ajustes y noticias.", "Les applications, réglages et actualités sont conservés."),
    "success": ("Completed", "Готово", "Finalizat", "Abgeschlossen", "Completado", "Terminé"),
    "failed": ("Failed", "Ошибка", "Eșuat", "Fehlgeschlagen", "Error", "Échec"),
    "launch": ("Launched", "Запущено", "Lansat", "Gestartet", "Abierto", "Lancé"),
    "install": ("Installed", "Установлено", "Instalat", "Installiert", "Instalado", "Installé"),
    "update": ("Updated", "Обновлено", "Actualizat", "Aktualisiert", "Actualizado", "Mis à jour"),
    "remove": ("Removed", "Удалено", "Eliminat", "Entfernt", "Eliminado", "Supprimé"),
    "intro_toggle": ("Startup intro", "Интро при запуске", "Intro la pornire", "Startanimation", "Intro al iniciar", "Introduction au démarrage"),
    "workspace": ("YOUR WORKSPACE", "ТВОЁ ПРОСТРАНСТВО", "SPAȚIUL TĂU", "DEIN BEREICH", "TU ESPACIO", "VOTRE ESPACE"),
    "quick": ("Made for your next session.", "Всё для следующего запуска.", "Pregătit pentru următoarea sesiune.", "Bereit für deine nächste Session.", "Todo para tu próxima sesión.", "Tout pour votre prochaine session."),
}

def copy(key, language):
    return COPY[key][("en", "ru", "ro", "de", "es", "fr").index(language)]

PREMIUM_STYLE = """
QFrame#sidebar { background: #151515; border-right: 1px solid #292929; }
QFrame#topbar { background: #121212; border-bottom: 1px solid #292929; }
QPushButton#nav { padding: 12px 14px; color: #B2B2B2; }
QPushButton#navactive { padding: 12px 14px; background: #29271D; border: 1px solid #50472A; color: #FFE37A; }
QFrame#hero { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #26251F,stop:0.55 #1B1B1A,stop:1 #171717); border: 1px solid #423E30; border-radius: 20px; }
QFrame#card { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #232323,stop:1 #1A1A1A); border: 1px solid #373737; border-radius: 18px; }
QFrame#card:hover, QFrame#libraryEntry:hover { border-color: #74623A; }
QLabel#eyebrow { color: #DCC574; font-size: 10px; font-weight: 700; }
QLabel#title { font-size: 30px; font-weight: 700; }
QLabel#heroTitle { font-size: 34px; font-weight: 700; }
QLabel#productTitle { font-size: 20px; font-weight: 600; }
QLabel#body { color: #BDBDBD; font-size: 13px; }
QLabel#muted { color: #989898; font-size: 12px; }
QLabel#statValue { color: #F4F4F4; font-size: 26px; font-weight: 700; }
QFrame#stat { background: #1A1A1A; border: 1px solid #303030; border-radius: 12px; }
QFrame#libraryEntry { background: #1B1B1B; border: 1px solid #333333; border-radius: 16px; }
QPushButton#primary { background: #F4CF35; border: 1px solid #FFE590; border-radius: 9px; padding: 11px 18px; }
QPushButton#primary:hover { background: #FFE174; }
QPushButton#secondary { background: #272727; border: 1px solid #404040; border-radius: 9px; }
QPushButton#secondary:hover { background: #303030; border-color: #686052; }
QPushButton#favorite { padding: 8px; color: #B8B8B8; border: 1px solid #3D3D3D; background: #222222; }
QPushButton#favorite:checked { color: #FFD84A; border-color: #75622C; background: #302A1C; }
QPushButton#danger:hover { border-color: #C48170; color: #FFD7CB; }
QLineEdit { background: #191919; border: 1px solid #373737; border-radius: 10px; padding: 11px 14px; selection-background-color: #D5B73D; selection-color: #111111; }
QLineEdit:focus { border-color: #B69A43; background: #1E1E1C; }
QComboBox { background: #242424; color: #EBEBEB; border: 1px solid #404040; border-radius: 8px; padding: 9px 12px; min-width: 120px; }
QComboBox QAbstractItemView { background: #242424; color: #EEEEEE; selection-background-color: #4B4128; border: 1px solid #53504A; }
QToolTip { background: #302D25; color: #F5F5F5; border: 1px solid #665B3A; padding: 7px; }
QFrame#newsLead { background: #22211C; border: 1px solid #51492F; border-radius: 16px; }
QTextBrowser { background: #1B1B1B; border: 1px solid #343434; border-radius: 12px; selection-background-color: #61552F; }
QScrollBar::handle:vertical:hover { background: #8C7A42; }
"""
