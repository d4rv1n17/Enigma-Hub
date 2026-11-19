"""Shared visual tokens and localized workspace controls."""
COPY = {
    "version_unknown": ("Could not determine the installed version. Reconnect the installed app or use its official installer.", "Не удалось определить установленную версию. Подключите приложение заново или используйте официальный установщик.", "Versiunea instalată nu a putut fi determinată. Reconectează aplicația.", "Installierte Version unbekannt. App erneut verbinden oder offiziellen Installer nutzen.", "No se pudo determinar la versión instalada. Vuelve a conectar la aplicación.", "Version installée inconnue. Reconnectez l’application ou utilisez l’installateur officiel."),
    "general": ("General", "Общие", "Generale", "Allgemein", "General", "Général"),
    "settings_intro": ("Your workspace, your preferences.", "Твоё пространство — твои настройки.", "Spațiul tău, preferințele tale.", "Dein Bereich, deine Einstellungen.", "Tu espacio, tus preferencias.", "Votre espace, vos préférences."),
    "motion_note": ("Smooth page transitions and artwork hover effects.", "Плавные переходы между страницами и эффекты иллюстраций.", "Tranziții line și efecte pentru ilustrații.", "Sanfte Seitenwechsel und Effekte für Grafiken.", "Transiciones suaves y efectos en ilustraciones.", "Transitions fluides et effets des illustrations."),
    "intro_note": ("Show the Enigma welcome screen when Hub starts.", "Показывать приветствие Enigma при запуске хаба.", "Afișează ecranul Enigma la pornire.", "Enigma-Begrüßung beim Start anzeigen.", "Mostrar la bienvenida de Enigma al iniciar.", "Afficher l’accueil Enigma au démarrage."),
    "product_updates_note": ("Check Cube and Disk releases when you open Hub.", "Проверять выпуски Cube и Disk при открытии хаба.", "Verifică versiunile Cube și Disk la pornire.", "Cube- und Disk-Versionen beim Start prüfen.", "Buscar versiones de Cube y Disk al abrir Hub.", "Vérifier les versions Cube et Disk au démarrage."),
    "hub_updates_note": ("Download verified Hub updates in the background. You choose when to restart.", "Скачивать проверенные обновления Hub в фоне. Когда перезапустить — решаешь ты.", "Descarcă actualizările verificate în fundal. Alegi când repornești.", "Geprüfte Hub-Updates im Hintergrund laden. Du bestimmst den Neustart.", "Descargar actualizaciones verificadas en segundo plano. Tú decides cuándo reiniciar.", "Télécharger les mises à jour vérifiées en arrière-plan. Vous choisissez le redémarrage."),
    "continue": ("Jump back in", "Продолжить работу", "Continuă de unde ai rămas", "Direkt weitermachen", "Continúa donde estabas", "Reprenez votre activité"),
    "preparing": ("Preparing download…", "Подготовка загрузки…", "Se pregătește descărcarea…", "Download wird vorbereitet…", "Preparando descarga…", "Préparation du téléchargement…"),
    "cancelling": ("Cancelling download…", "Отмена загрузки…", "Se anulează descărcarea…", "Download wird abgebrochen…", "Cancelando descarga…", "Annulation du téléchargement…"),
    "cancelled": ("Cancelled", "Отменено", "Anulat", "Abgebrochen", "Cancelado", "Annulé"),
    "remaining": ("Remaining", "Осталось", "Rămas", "Verbleibend", "Restante", "Restant"),
    "disk_space": ("Not enough free disk space for this download or installation.", "Недостаточно свободного места для загрузки или установки.", "Spațiu insuficient pentru descărcare sau instalare.", "Nicht genügend Speicherplatz für Download oder Installation.", "No hay espacio suficiente para descargar o instalar.", "Espace insuffisant pour le téléchargement ou l’installation."),
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
QLabel#railVersion { color: #89877F; font-size: 10px; padding: 5px 14px; }
QLabel#settingTitle { color: #F0EEE7; font-size: 15px; font-weight: 600; }
QFrame#settingRow { border-bottom: 1px solid #33322C; }
QPushButton#settingsTab { color: #B1AFA7; background: #1A1A18; border: 1px solid #36352F; border-radius: 8px; padding: 10px 12px; text-align: center; }
QPushButton#settingsTab:hover { background: #26251F; color: #F0EEE7; }
QPushButton#settingsTab:checked { background: #2C2818; color: #F4CC0C; border-color: #6D5C20; }
QFrame#transferPanel { background: #1C1B18; border-top: 1px solid #5B4D22; }
QFrame#sidebar { background: #151515; border-right: 1px solid #292929; }
QFrame#topbar { background: #121212; border-bottom: 1px solid #292929; }
QPushButton#nav { min-height: 24px; max-height: 24px; padding: 10px 14px; font-size: 14px; color: #BDBDBD; border: 1px solid transparent; border-radius: 9px; text-align: left; }
QPushButton#nav:hover { background: #202020; border-color: #303030; }
QPushButton#nav:focus { border-color: #70633A; }
QPushButton#navactive { min-height: 24px; max-height: 24px; padding: 10px 14px 10px 12px; font-size: 14px; background: #292619; border: 1px solid #5C4D19; border-left: 3px solid #F4CC0C; border-radius: 9px; color: #F4CC0C; text-align: left; }
QPushButton#navactive:hover { background: #302B19; }
QPushButton#railUtility { padding: 12px 14px; color: #AAA79F; }
QPushButton#railUtility:hover { background: #202020; color: #F4CC0C; }
QPushButton#choice { background: #202020; border: 1px solid #3A3A36; border-radius: 10px; padding: 10px 38px 10px 14px; color: #E4E2DA; text-align: left; min-width: 120px; }
QPushButton#choice:hover { background: #292821; border-color: #756531; }
QPushButton#choice:focus { border-color: #F4CC0C; }
QPushButton#choice::menu-indicator { image: none; width: 0; height: 0; }
QMenu { background: #1C1C1B; border: 1px solid #4B4634; padding: 7px; }
QMenu::item { padding: 11px 30px 11px 30px; border-radius: 6px; }
QMenu::item:selected { background: #35301D; color: #F4CC0C; }
QWidget#activityCanvas { background: #171717; }
QFrame#dialogHeader { background: #1E1E1C; border: 1px solid #403B2C; border-radius: 12px; }
QFrame#hero { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #26251F,stop:0.55 #1B1B1A,stop:1 #171717); border: 1px solid #423E30; border-radius: 20px; }
QFrame#card { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #232323,stop:1 #1A1A1A); border: 1px solid #373737; border-radius: 18px; }
QFrame#card:hover, QFrame#libraryEntry:hover { border-color: #74623A; }
QLabel#eyebrow { color: #F4CC0C; font-size: 11px; font-weight: 700; }
QLabel#title { font-size: 30px; font-weight: 700; }
QLabel#heroTitle { font-size: 34px; font-weight: 700; }
QLabel#productTitle { font-size: 20px; font-weight: 600; }
QLabel#body { color: #BDBDBD; font-size: 13px; }
QLabel#muted { color: #989898; font-size: 12px; }
QLabel#statValue { color: #F4F4F4; font-size: 26px; font-weight: 700; }
QFrame#stat { background: #1A1A1A; border: 1px solid #303030; border-radius: 12px; }
QFrame#libraryEntry { background: #1B1B1B; border: 1px solid #333333; border-radius: 16px; }
QPushButton#primary { background: #F4CC0C; border: 1px solid #F4CC0C; border-radius: 9px; padding: 11px 18px; }
QPushButton#primary:hover { background: #FFDA66; }
QPushButton#secondary { background: #272727; border: 1px solid #404040; border-radius: 9px; }
QPushButton#secondary:hover { background: #303030; border-color: #686052; }
QPushButton#favorite { padding: 8px; color: #B8B8B8; border: 1px solid #3D3D3D; background: #222222; }
QPushButton#favorite:checked { color: #F4CC0C; border-color: #75622C; background: #302A1C; }
QPushButton#danger:hover { border-color: #C48170; color: #FFD7CB; }
QLineEdit { background: #191919; border: 1px solid #373737; border-radius: 10px; padding: 11px 14px; selection-background-color: #F4CC0C; selection-color: #111111; }
QLineEdit:focus { border-color: #B69A43; background: #1E1E1C; }
QComboBox { background: #242424; color: #EBEBEB; border: 1px solid #404040; border-radius: 8px; padding: 9px 12px; min-width: 120px; }
QComboBox QAbstractItemView { background: #242424; color: #EEEEEE; selection-background-color: #4B4128; border: 1px solid #53504A; }
QToolTip { background: #302D25; color: #F5F5F5; border: 1px solid #665B3A; padding: 7px; }
QFrame#newsLead { background: #22211C; border: 1px solid #51492F; border-radius: 16px; }
QTextBrowser { background: #1B1B1B; border: 1px solid #343434; border-radius: 12px; selection-background-color: #61552F; }
QScrollBar::handle:vertical:hover { background: #8C7A42; }
"""
