"""Enigma Hub — multilingual Windows desktop launcher and product manager."""
import ctypes
import faulthandler
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime
import webbrowser
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from hub_update import VERSION as HUB_VERSION, HubUpdateWorker, digest_file
from hub_experience import copy as workspace_copy, PREMIUM_STYLE
from hub_safety import reject_reparse

from PyQt5.QtCore import Qt, QRectF, QThread, QTimer, QElapsedTimer, QVariantAnimation, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QFont, QIcon, QImage, QLinearGradient, QPainter, QPainterPath, QPixmap, QTextDocument
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWidgets import (
    QApplication, QBoxLayout, QDialog, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QPushButton, QProgressBar, QTextBrowser,
    QScrollArea, QStackedWidget, QVBoxLayout, QWidget, QSizePolicy, QComboBox, QShortcut,
)

ROOT = Path(__file__).resolve().parent
APPDATA = Path(os.environ.get("APPDATA", tempfile.gettempdir())) / "EnigmaHub"
STATE_FILE = APPDATA / "settings.json"
REPO = "d4rv1n17/Enigma-Cube"
PRODUCTS = [
    {"id": "cube", "name": "Enigma Cube", "kind": "APP", "version": "3.2.1", "tag": "Тренировка · Таймер · Умный куб", "desc": "Всё для спидкубинга: точный таймер, курсы, скрамблы и поддержка умных кубов.", "color": "#303030", "repo": "d4rv1n17/Enigma-Cube", "asset": "EnigmaCube-Setup-{version}.exe", "exe": "EnigmaCube.exe", "url": "https://github.com/d4rv1n17/Enigma-Cube/releases/latest", "folder": "Enigma Cube"},
    {"id": "disk", "name": "Enigma Disk", "kind": "APP", "version": "2.0", "tag": "Анализ · История · Очистка", "desc": "Узнайте, какие папки растут, сравнивайте снимки дисков и находите, что занимает место.", "color": "#303030", "repo": "d4rv1n17/Enigma-Disk", "asset": "EnigmaDisk-portable.exe", "exe": "EnigmaDisk.exe", "url": "https://github.com/d4rv1n17/Enigma-Disk/releases/latest", "folder": "Enigma Disk"},
]
GAMES = [
    {"id": "veil-of-fear", "name": "Veil of Fear", "genre": "SURVIVAL HORROR", "desc": "Погрузитесь в мир, где страх скрывается за каждой дверью.", "mark": "◉", "tint": "#27282d"},
    {"id": "twins-hunt", "name": "Twins’ Hunt", "genre": "HORROR · STORY", "desc": "Две судьбы. Одна охота. История Enigma Studio.", "mark": "Ⅱ", "tint": "#29292c"},
    {"id": "last-signal", "name": "Last Signal", "genre": "PSYCHOLOGICAL HORROR", "desc": "Когда сигнал затихает, остаётся только идти вперёд.", "mark": "⌁", "tint": "#24262b"},
]
DEFAULTS = {
    "lang": "en", "paths": {p["id"]: str(Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "Programs" / p["folder"]) for p in PRODUCTS},
    "games": {}, "installed": {}, "auto_check": True, "motion": True, "hub_auto_update": True,
    "favorites": [], "recent": {}, "history": [], "hashes": {}, "intro": True,
}
TEXT = {
    "ru": {"overview":"Обзор","catalog":"Каталог","library":"Моя библиотека","news":"Новости","settings":"Настройки","welcome":"ТВОЯ ВСЕЛЕННАЯ ENIGMA","hero":"Открой для себя Enigma.","intro":"Приложения студии — в одном месте. Игры запускаются здесь, покупка проходит в Steam и других магазинах.","explore":"Открыть каталог","featured":"В центре внимания","apps":"Приложения","games":"Игры студии","view":"Все продукты","installed":"УСТАНОВЛЕНО","not_installed":"В КАТАЛОГЕ","launch":"Запустить","install":"Установить","update":"Обновить","remove":"Удалить","details":"Подробнее","buy":"Купить / страница магазина ↗","configure":"Настроить","choose_folder":"Папка установки","choose":"Выбрать папку","ready":"Готово к установке","running":"Выполняется…","checking":"Проверяем выпуск…","news_title":"Новости студии","news_desc":"Последние обновления и заметки о продуктах.","support":"Поддержка","support_desc":"Документация, ответы и сообщения об ошибках.","check_updates":"Проверить обновления","auto_check":"Проверять обновления при запуске","language":"Язык интерфейса","preferences":"Параметры","about":"О Enigma Hub","footer":"ENIGMA STUDIO  ·  Всё необходимое в одном месте","choose_title":"Выберите папку для установки","folder_saved":"Папка установки обновлена.","folder_installed":"Сначала удалите продукт, чтобы изменить папку установки.","uninstall_confirm":"Удалить {name} из папки установки? Пользовательские данные приложения будут сохранены.","uninstalled":"{name} удалён.","installed_ok":"{name} установлен. Можно запускать.","updated_ok":"{name} обновлён до {version}.","integrity":"Файл загружен и проверен по SHA-256.","unsupported":"Этот продукт пока недоступен для установки на этой системе.","game_not_found":"Игра не найдена. Настройте .exe или Steam App ID.","setup_game":"Настроить запуск","game_exe":"Исполняемый файл игры","steam_id":"Steam App ID (можно оставить пустым)","store_url":"Ссылка на страницу магазина","save":"Сохранить","cancel":"Отмена","no_news":"Свежих новостей пока нет.","loading_news":"Загружаем новости…","checksum_missing":"В выпуске отсутствует SHA-256. Загрузка отменена.","failed":"Не удалось выполнить операцию","progress_download":"Загрузка и проверка файла…","progress_install":"Установка продукта…","progress_remove":"Удаление продукта…","install_path":"Путь","release":"Релиз","open_site":"Сайт студии ↗","news_empty":"Новостей пока нет","support_email":"Сообщить об ошибке","installation":"Установка","integrity_title":"Целостность файлов","updates":"Обновления","language_note":"Изменение применяется сразу.","external":"Покупка и установка игр выполняются в выбранном магазине. Enigma Hub не принимает платежи.","open_release":"Открыть страницу релиза ↗","no_products":"Здесь появятся установленные продукты студии.","game_installed":"Установлена · Steam","up_to_date":"актуальная версия","update_available":"доступно обновление","not_installed_state":"не установлено","latest_version":"Последняя версия"},
    "en": {"overview":"Home","catalog":"Discover","library":"My library","news":"News","settings":"Settings","welcome":"YOUR ENIGMA UNIVERSE","hero":"Find your next Enigma.","intro":"Studio apps in one place. Launch your games here; purchases stay on Steam and other stores.","explore":"Explore catalog","featured":"Featured","apps":"Applications","games":"Studio games","view":"View all products","installed":"INSTALLED","not_installed":"IN CATALOG","launch":"Launch","install":"Install","update":"Update","remove":"Uninstall","details":"Details","buy":"Buy / store page ↗","configure":"Configure","choose_folder":"Install folder","choose":"Choose folder","ready":"Ready to install","running":"Working…","checking":"Checking release…","news_title":"Studio news","news_desc":"Latest product updates and release notes.","support":"Support","support_desc":"Documentation, answers and bug reports.","check_updates":"Check for updates","auto_check":"Check for updates on launch","language":"Interface language","preferences":"Preferences","about":"About Enigma Hub","footer":"ENIGMA STUDIO  ·  Everything you need, in one place","choose_title":"Choose installation folder","folder_saved":"Installation folder updated.","folder_installed":"Uninstall the product before changing its folder.","uninstall_confirm":"Remove {name} from its install folder? App data will be kept.","uninstalled":"{name} removed.","installed_ok":"{name} is installed and ready.","updated_ok":"{name} updated to {version}.","integrity":"Download verified with SHA-256.","unsupported":"This product is not available on this system yet.","game_not_found":"Game not found. Configure an executable or Steam App ID.","setup_game":"Configure launch","game_exe":"Game executable","steam_id":"Steam App ID (optional)","store_url":"Store page link","save":"Save","cancel":"Cancel","no_news":"No recent news yet.","loading_news":"Loading news…","checksum_missing":"Release has no SHA-256 digest. Download cancelled.","failed":"Operation failed","progress_download":"Downloading and verifying…","progress_install":"Installing…","progress_remove":"Removing…","install_path":"Path","release":"Release","open_site":"Studio website ↗","news_empty":"No news yet","support_email":"Report a problem","installation":"Installation","integrity_title":"File integrity","updates":"Updates","language_note":"Changes apply immediately.","external":"Games are purchased and installed through their storefront. Enigma Hub does not process payments.","open_release":"Open release page ↗","no_products":"Installed studio products will appear here.","game_installed":"Installed · Steam","up_to_date":"up to date","update_available":"update available","not_installed_state":"not installed","latest_version":"Latest version"},
    "ro": {"overview":"Acasă","catalog":"Catalog","library":"Biblioteca mea","news":"Noutăți","settings":"Setări","welcome":"UNIVERSUL TĂU ENIGMA","hero":"Descoperă Enigma.","intro":"Aplicațiile studioului într-un singur loc. Jocurile se lansează aici; cumpărarea rămâne pe Steam și alte magazine.","explore":"Vezi catalogul","featured":"Recomandat","apps":"Aplicații","games":"Jocuri studio","view":"Vezi toate produsele","installed":"INSTALAT","not_installed":"ÎN CATALOG","launch":"Lansează","install":"Instalează","update":"Actualizează","remove":"Dezinstalează","details":"Detalii","buy":"Cumpără / pagina magazinului ↗","configure":"Configurează","choose_folder":"Dosar de instalare","choose":"Alege dosarul","ready":"Gata de instalare","running":"Se execută…","checking":"Se verifică versiunea…","news_title":"Noutăți studio","news_desc":"Ultimele actualizări și note de lansare.","support":"Asistență","support_desc":"Documentație, răspunsuri și raportarea erorilor.","check_updates":"Verifică actualizările","auto_check":"Verifică actualizările la pornire","language":"Limba interfeței","preferences":"Preferințe","about":"Despre Enigma Hub","footer":"ENIGMA STUDIO  ·  Tot ce ai nevoie, într-un singur loc","choose_title":"Alege dosarul de instalare","folder_saved":"Dosarul de instalare a fost actualizat.","folder_installed":"Dezinstalează produsul înainte de a schimba dosarul.","uninstall_confirm":"Elimini {name} din dosarul de instalare? Datele aplicației vor fi păstrate.","uninstalled":"{name} a fost eliminat.","installed_ok":"{name} este instalat și gata.","updated_ok":"{name} a fost actualizat la {version}.","integrity":"Descărcarea a fost verificată cu SHA-256.","unsupported":"Produsul nu este încă disponibil pe acest sistem.","game_not_found":"Jocul nu a fost găsit. Configurează executabilul sau Steam App ID.","setup_game":"Configurează lansarea","game_exe":"Executabilul jocului","steam_id":"Steam App ID (opțional)","store_url":"Link către magazin","save":"Salvează","cancel":"Anulează","no_news":"Nu sunt noutăți recente.","loading_news":"Se încarcă noutățile…","checksum_missing":"Lipsește SHA-256. Descărcarea a fost anulată.","failed":"Operațiunea a eșuat","progress_download":"Descărcare și verificare…","progress_install":"Se instalează…","progress_remove":"Se elimină…","install_path":"Cale","release":"Versiune","open_site":"Site-ul studioului ↗","news_empty":"Încă nu sunt noutăți","support_email":"Raportează o problemă","installation":"Instalare","integrity_title":"Integritatea fișierelor","updates":"Actualizări","language_note":"Modificările se aplică imediat.","external":"Jocurile se cumpără și se instalează prin magazinul ales. Enigma Hub nu procesează plăți.","open_release":"Deschide versiunea ↗","no_products":"Produsele instalate vor apărea aici."},
    "de": {"overview":"Start","catalog":"Entdecken","library":"Meine Bibliothek","news":"Neuigkeiten","settings":"Einstellungen","welcome":"DEIN ENIGMA UNIVERSUM","hero":"Entdecke Enigma.","intro":"Studio-Apps an einem Ort. Spiele startest du hier; Käufe erfolgen bei Steam und anderen Shops.","explore":"Katalog öffnen","featured":"Im Fokus","apps":"Anwendungen","games":"Studio-Spiele","view":"Alle Produkte","installed":"INSTALLIERT","not_installed":"IM KATALOG","launch":"Starten","install":"Installieren","update":"Aktualisieren","remove":"Deinstallieren","details":"Details","buy":"Kaufen / Shopseite ↗","configure":"Einrichten","choose_folder":"Installationsordner","choose":"Ordner wählen","ready":"Installationsbereit","running":"Wird ausgeführt…","checking":"Version wird geprüft…","news_title":"Studio-Neuigkeiten","news_desc":"Aktuelle Updates und Versionshinweise.","support":"Support","support_desc":"Dokumentation, Antworten und Fehlerberichte.","check_updates":"Updates suchen","auto_check":"Beim Start nach Updates suchen","language":"Sprache","preferences":"Einstellungen","about":"Über Enigma Hub","footer":"ENIGMA STUDIO  ·  Alles an einem Ort","choose_title":"Installationsordner wählen","folder_saved":"Installationsordner aktualisiert.","folder_installed":"Produkt zuerst deinstallieren, um den Ordner zu ändern.","uninstall_confirm":"{name} aus dem Installationsordner entfernen? App-Daten bleiben erhalten.","uninstalled":"{name} entfernt.","installed_ok":"{name} ist installiert und startbereit.","updated_ok":"{name} auf {version} aktualisiert.","integrity":"Download mit SHA-256 geprüft.","unsupported":"Dieses Produkt ist auf diesem System noch nicht verfügbar.","game_not_found":"Spiel nicht gefunden. EXE oder Steam App ID einrichten.","setup_game":"Start einrichten","game_exe":"Spiel-EXE","steam_id":"Steam App ID (optional)","store_url":"Shop-Link","save":"Speichern","cancel":"Abbrechen","no_news":"Noch keine Neuigkeiten.","loading_news":"Neuigkeiten werden geladen…","checksum_missing":"SHA-256 fehlt. Download abgebrochen.","failed":"Vorgang fehlgeschlagen","progress_download":"Wird geladen und geprüft…","progress_install":"Wird installiert…","progress_remove":"Wird entfernt…","install_path":"Pfad","release":"Version","open_site":"Studio-Website ↗","news_empty":"Noch keine Neuigkeiten","support_email":"Problem melden","installation":"Installation","integrity_title":"Dateiintegrität","updates":"Updates","language_note":"Änderungen gelten sofort.","external":"Spiele werden im jeweiligen Shop gekauft und installiert. Enigma Hub verarbeitet keine Zahlungen.","open_release":"Release öffnen ↗","no_products":"Installierte Produkte erscheinen hier."},
    "es": {"overview":"Inicio","catalog":"Catálogo","library":"Mi biblioteca","news":"Noticias","settings":"Ajustes","welcome":"TU UNIVERSO ENIGMA","hero":"Descubre Enigma.","intro":"Aplicaciones del estudio en un solo lugar. Los juegos se lanzan aquí; las compras se realizan en Steam y otras tiendas.","explore":"Explorar catálogo","featured":"Destacado","apps":"Aplicaciones","games":"Juegos del estudio","view":"Ver productos","installed":"INSTALADO","not_installed":"EN CATÁLOGO","launch":"Iniciar","install":"Instalar","update":"Actualizar","remove":"Desinstalar","details":"Detalles","buy":"Comprar / página de tienda ↗","configure":"Configurar","choose_folder":"Carpeta de instalación","choose":"Elegir carpeta","ready":"Listo para instalar","running":"En curso…","checking":"Comprobando versión…","news_title":"Noticias del estudio","news_desc":"Últimas actualizaciones y notas de versión.","support":"Soporte","support_desc":"Documentación, respuestas e informes de errores.","check_updates":"Buscar actualizaciones","auto_check":"Buscar actualizaciones al iniciar","language":"Idioma de la interfaz","preferences":"Preferencias","about":"Acerca de Enigma Hub","footer":"ENIGMA STUDIO  ·  Todo lo que necesitas, en un solo lugar","choose_title":"Elige la carpeta de instalación","folder_saved":"Carpeta actualizada.","folder_installed":"Desinstala el producto antes de cambiar la carpeta.","uninstall_confirm":"¿Eliminar {name} de su carpeta? Se conservarán los datos de la aplicación.","uninstalled":"{name} eliminado.","installed_ok":"{name} está instalado y listo.","updated_ok":"{name} actualizado a {version}.","integrity":"Descarga verificada con SHA-256.","unsupported":"Este producto aún no está disponible en este sistema.","game_not_found":"No se encontró el juego. Configura el ejecutable o Steam App ID.","setup_game":"Configurar inicio","game_exe":"Ejecutable del juego","steam_id":"Steam App ID (opcional)","store_url":"Enlace de la tienda","save":"Guardar","cancel":"Cancelar","no_news":"Aún no hay noticias.","loading_news":"Cargando noticias…","checksum_missing":"Falta SHA-256. Descarga cancelada.","failed":"No se pudo completar","progress_download":"Descargando y verificando…","progress_install":"Instalando…","progress_remove":"Eliminando…","install_path":"Ruta","release":"Versión","open_site":"Sitio del estudio ↗","news_empty":"Aún no hay noticias","support_email":"Informar de un problema","installation":"Instalación","integrity_title":"Integridad de archivos","updates":"Actualizaciones","language_note":"Los cambios se aplican al instante.","external":"Los juegos se compran e instalan desde su tienda. Enigma Hub no procesa pagos.","open_release":"Abrir versión ↗","no_products":"Aquí aparecerán los productos instalados."},
    "fr": {"overview":"Accueil","catalog":"Découvrir","library":"Ma bibliothèque","news":"Actualités","settings":"Paramètres","welcome":"VOTRE UNIVERS ENIGMA","hero":"Découvrez Enigma.","intro":"Les applications du studio réunies. Lancez vos jeux ici ; achetez-les sur Steam ou d’autres boutiques.","explore":"Voir le catalogue","featured":"À la une","apps":"Applications","games":"Jeux du studio","view":"Tous les produits","installed":"INSTALLÉ","not_installed":"CATALOGUE","launch":"Lancer","install":"Installer","update":"Mettre à jour","remove":"Désinstaller","details":"Détails","buy":"Acheter / boutique ↗","configure":"Configurer","choose_folder":"Dossier d’installation","choose":"Choisir un dossier","ready":"Prêt à installer","running":"En cours…","checking":"Vérification…","news_title":"Actualités du studio","news_desc":"Dernières mises à jour et notes de version.","support":"Assistance","support_desc":"Documentation, réponses et signalement de bugs.","check_updates":"Rechercher des mises à jour","auto_check":"Rechercher au démarrage","language":"Langue de l’interface","preferences":"Préférences","about":"À propos d’Enigma Hub","footer":"ENIGMA STUDIO  ·  Tout au même endroit","choose_title":"Choisir le dossier d’installation","folder_saved":"Dossier d’installation modifié.","folder_installed":"Désinstallez le produit avant de changer de dossier.","uninstall_confirm":"Supprimer {name} de son dossier ? Les données de l’application seront conservées.","uninstalled":"{name} supprimé.","installed_ok":"{name} est installé et prêt.","updated_ok":"{name} mis à jour vers {version}.","integrity":"Téléchargement vérifié par SHA-256.","unsupported":"Ce produit n’est pas encore disponible sur ce système.","game_not_found":"Jeu introuvable. Configurez son exécutable ou Steam App ID.","setup_game":"Configurer le lancement","game_exe":"Exécutable du jeu","steam_id":"Steam App ID (facultatif)","store_url":"Lien de la boutique","save":"Enregistrer","cancel":"Annuler","no_news":"Pas encore d’actualités.","loading_news":"Chargement des actualités…","checksum_missing":"SHA-256 manquant. Téléchargement annulé.","failed":"Échec de l’opération","progress_download":"Téléchargement et vérification…","progress_install":"Installation…","progress_remove":"Suppression…","install_path":"Chemin","release":"Version","open_site":"Site du studio ↗","news_empty":"Pas encore d’actualités","support_email":"Signaler un problème","installation":"Installation","integrity_title":"Intégrité des fichiers","updates":"Mises à jour","language_note":"Les changements sont immédiats.","external":"Les jeux sont achetés et installés via leur boutique. Enigma Hub ne traite aucun paiement.","open_release":"Ouvrir la version ↗","no_products":"Les produits installés apparaîtront ici."},
}
TEXT["ro"].update({"game_installed":"Instalat · Steam","up_to_date":"la zi","update_available":"actualizare disponibilă","not_installed_state":"neinstalat","latest_version":"Versiunea recentă"})
TEXT["de"].update({"game_installed":"Installiert · Steam","up_to_date":"aktuell","update_available":"Update verfügbar","not_installed_state":"nicht installiert","latest_version":"Neueste Version"})
TEXT["es"].update({"game_installed":"Instalado · Steam","up_to_date":"actualizado","update_available":"actualización disponible","not_installed_state":"no instalado","latest_version":"Última versión"})
TEXT["fr"].update({"game_installed":"Installé · Steam","up_to_date":"à jour","update_available":"mise à jour disponible","not_installed_state":"non installé","latest_version":"Dernière version"})
TEXT["ru"]["workspace"]="ПРОСТРАНСТВО СТУДИИ"; TEXT["en"]["workspace"]="STUDIO SPACE"; TEXT["ro"]["workspace"]="SPAȚIUL STUDIOULUI"; TEXT["de"]["workspace"]="STUDIOBEREICH"; TEXT["es"]["workspace"]="ESPACIO DEL ESTUDIO"; TEXT["fr"]["workspace"]="ESPACE DU STUDIO"
TEXT["ru"]["ideas"]="Идеи обретают форму."; TEXT["en"]["ideas"]="Ideas made real."; TEXT["ro"]["ideas"]="Ideile prind viață."; TEXT["de"]["ideas"]="Ideen werden Wirklichkeit."; TEXT["es"]["ideas"]="Ideas que se hacen realidad."; TEXT["fr"]["ideas"]="Les idées prennent vie."
TEXT["ru"]["preview"]="ПРЕДВАРИТЕЛЬНАЯ ВЕРСИЯ"; TEXT["en"]["preview"]="PREVIEW"; TEXT["ro"]["preview"]="PREZENTARE"; TEXT["de"]["preview"]="VORSCHAU"; TEXT["es"]["preview"]="VISTA PREVIA"; TEXT["fr"]["preview"]="APERÇU"
METADATA = {
    "ru": {"cube":("Тренировка · Таймер · Умный куб","Всё для спидкубинга: точный таймер, курсы, скрамблы и поддержка умных кубов."),"disk":("Анализ · История · Очистка","Узнайте, какие папки растут, сравнивайте снимки дисков и находите, что занимает место."),"veil-of-fear":("ХОРРОР НА ВЫЖИВАНИЕ","Погрузитесь в мир, где страх скрывается за каждой дверью."),"twins-hunt":("ХОРРОР · ИСТОРИЯ","Две судьбы. Одна охота. История Enigma Studio."),"last-signal":("ПСИХОЛОГИЧЕСКИЙ ХОРРОР","Когда сигнал затихает, остаётся только идти вперёд.")},
    "en": {"cube":("Timer · Training · Smart Cube","Everything for speedcubing: a precise timer, guided courses, scrambles, and smart cube support."),"disk":("Analyze · Track · Clean","See which folders are growing, compare drive snapshots, and find what takes up space."),"veil-of-fear":("SURVIVAL HORROR","Enter a world where fear waits behind every door."),"twins-hunt":("HORROR · STORY","Two fates. One hunt. An Enigma Studio story."),"last-signal":("PSYCHOLOGICAL HORROR","When the signal fades, there is only one way forward.")},
    "ro": {"cube":("Cronometru · Antrenament · Cub inteligent","Tot ce ai nevoie pentru speedcubing: cronometru precis, cursuri, scramble-uri și suport pentru cuburi inteligente."),"disk":("Analiză · Istoric · Curățare","Vezi ce foldere cresc, compară instantanee ale discului și află ce ocupă spațiu."),"veil-of-fear":("HORROR DE SUPRAVIEȚUIRE","Pășește într-o lume în care frica se ascunde după fiecare ușă."),"twins-hunt":("HORROR · POVESTE","Două destine. O singură vânătoare. O poveste Enigma Studio."),"last-signal":("HORROR PSIHOLOGIC","Când semnalul se stinge, rămâne doar drumul înainte.")},
    "de": {"cube":("Timer · Training · Smart Cube","Alles fürs Speedcubing: präziser Timer, Kurse, Scrambles und Smart-Cube-Unterstützung."),"disk":("Analyse · Verlauf · Bereinigung","Sieh, welche Ordner wachsen, vergleiche Laufwerk-Snapshots und finde Platzfresser."),"veil-of-fear":("SURVIVAL-HORROR","Eine Welt, in der hinter jeder Tür die Angst lauert."),"twins-hunt":("HORROR · STORY","Zwei Schicksale. Eine Jagd. Eine Geschichte von Enigma Studio."),"last-signal":("PSYCHOLOGISCHER HORROR","Wenn das Signal verstummt, bleibt nur der Weg nach vorn.")},
    "es": {"cube":("Temporizador · Entrenamiento · Cubo inteligente","Todo para el speedcubing: temporizador preciso, cursos, scrambles y compatibilidad con cubos inteligentes."),"disk":("Análisis · Historial · Limpieza","Descubre qué carpetas crecen, compara instantáneas de disco y encuentra qué ocupa espacio."),"veil-of-fear":("TERROR DE SUPERVIVENCIA","Adéntrate en un mundo donde el miedo se esconde tras cada puerta."),"twins-hunt":("TERROR · HISTORIA","Dos destinos. Una cacería. Una historia de Enigma Studio."),"last-signal":("TERROR PSICOLÓGICO","Cuando la señal se apaga, solo queda seguir adelante.")},
    "fr": {"cube":("Minuteur · Entraînement · Cube connecté","Tout pour le speedcubing : minuteur précis, cours, mélanges et prise en charge des cubes connectés."),"disk":("Analyse · Historique · Nettoyage","Repérez les dossiers qui grossissent, comparez les instantanés et trouvez ce qui occupe l’espace."),"veil-of-fear":("SURVIE · HORREUR","Entrez dans un monde où la peur se cache derrière chaque porte."),"twins-hunt":("HORREUR · RÉCIT","Deux destins. Une chasse. Une histoire d’Enigma Studio."),"last-signal":("HORREUR PSYCHOLOGIQUE","Quand le signal s’éteint, il ne reste qu’à avancer.")},
}


def meta(item):
    return METADATA.get(Hub.lang,METADATA["en"]).get(item["id"],(item.get("tag",item.get("genre","")),item["desc"]))

GAME_PAGES = {
    "veil-of-fear": "https://enigmastudioo.com/veil-of-fear.html",
    "twins-hunt": "https://play.google.com/store/apps/details?id=com.EnigmaStudio.TwinsHunt",
    "last-signal": "https://enigmastudioo.com/last-signal.html",
}
GAME_PAGE_LABELS = {
    "en": "Game page ↗", "ru": "Страница игры ↗", "ro": "Pagina jocului ↗",
    "de": "Spielseite ↗", "es": "Página del juego ↗", "fr": "Page du jeu ↗",
}
UPDATE_COPY = {
    "en": ("Installed", "Latest release", "Could not check", "Done"),
    "ru": ("Установлено", "Последний выпуск", "Не удалось проверить", "Готово"),
    "ro": ("Instalat", "Ultima versiune", "Verificare eșuată", "Gata"),
    "de": ("Installiert", "Neueste Version", "Prüfung fehlgeschlagen", "Fertig"),
    "es": ("Instalada", "Última versión", "No se pudo comprobar", "Listo"),
    "fr": ("Installée", "Dernière version", "Vérification impossible", "Terminé"),
}
ICONS = {
    "search": "M10 3a7 7 0 1 0 0 14 7 7 0 1 0 0-14z M15 15l6 6",
    "star": "M12 3l3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z",
    "play": "M8 4l12 8-12 8z",
    "activity": "M3 12h4l3-8 4 16 3-8h4",
    "language": "M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18z M3 12h18 M12 3c5 5 5 13 0 18-5-5-5-13 0-18z",
    "home": "M3 10l9-7 9 7v10H3z M9 20v-7h6v7",
    "catalog": "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
    "library": "M4 4v16 M9 4v16 M14 5l5-1 3 15-5 1z",
    "news": "M4 4h16v16H4z M8 8h8 M8 12h8 M8 16h5",
    "settings": "M4 6h16 M4 12h16 M4 18h16 M8 4v4 M15 10v4 M10 16v4",
    "folder": "M3 6h7l2 2h9v12H3z",
    "motion": "M3 15h4l4-8 4 10 3-4h3",
    "updates": "M20 10a8 8 0 0 0-14-4L3 9 M3 4v5h5 M4 14a8 8 0 0 0 14 4l3-3 M16 15h5v5",
    "support": "M4 4h16v12H9l-5 4z M8 9h8 M8 12h5",
    "external": "M13 4h7v7 M10 14l10-10 M20 13v7H4V4h7",
    "shield": "M12 3l8 3v6c0 4-3 7-8 9-5-2-8-5-8-9V6z M8 12l3 3 5-6",
    "check": "M5 12l4 4 10-10",
    "download": "M12 3v11 M7 10l5 5 5-5 M4 17v4h16v-4",
    "info": "M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18z M12 11v5 M12 8v.2",
}

SLOGANS = {
    "en": "One hub. More to discover.",
    "ru": "Один хаб. Больше открытий.",
    "ro": "Un singur hub. Mai multe de descoperit.",
    "de": "Ein Hub. Mehr zu entdecken.",
    "es": "Un hub. Más por descubrir.",
    "fr": "Un hub. Plus à découvrir.",
}

MOTION_LABELS = {
    "en": "Interface animations", "ru": "Анимации интерфейса", "ro": "Animații ale interfeței",
    "de": "Oberflächenanimationen", "es": "Animaciones de la interfaz", "fr": "Animations de l’interface",
}
FORM_ERROR = {
    "en": "Enter an existing .exe, a numeric Steam ID, or a valid web address in the corresponding fields.",
    "ru": "Проверьте поля: существующий .exe, числовой Steam ID и корректная ссылка.",
    "ro": "Verifică executabilul, ID-ul Steam numeric și adresa web.",
    "de": "Bitte EXE-Datei, numerische Steam-ID und Webadresse prüfen.",
    "es": "Comprueba el ejecutable, el ID numérico de Steam y la dirección web.",
    "fr": "Vérifiez l’exécutable, l’identifiant Steam numérique et l’adresse web.",
}
NEWS_OFFLINE = {
    "en": "Could not refresh all news from GitHub. Showing available releases.",
    "ru": "Не удалось обновить всю ленту с GitHub. Показаны доступные релизы.",
    "ro": "Nu s-au putut actualiza toate noutățile GitHub. Sunt afișate versiunile disponibile.",
    "de": "GitHub konnte nicht vollständig aktualisiert werden. Verfügbare Releases werden angezeigt.",
    "es": "No se pudieron actualizar todas las noticias de GitHub. Se muestran las versiones disponibles.",
    "fr": "Impossible d’actualiser toutes les actualités GitHub. Les versions disponibles sont affichées.",
}
NEWS_REFRESH = {
    "en": "Refresh news", "ru": "Обновить новости", "ro": "Actualizează noutățile",
    "de": "Neuigkeiten laden", "es": "Actualizar noticias", "fr": "Actualiser les actualités",
}
STORE_LABELS = {
    "ru": "В магазин ↗", "en": "Store ↗", "ro": "Magazin ↗",
    "de": "Zum Shop ↗", "es": "Tienda ↗", "fr": "Boutique ↗",
}

STYLE = """
* { font-family: 'Segoe UI Variable Text', 'Segoe UI'; }
QMainWindow, QWidget#root, QStackedWidget, QWidget#page { background: #121212; color: #F5F5F5; }
QFrame#sidebar { background: #1B1B1B; border-right: 1px solid #303030; }
QFrame#railDivider { background: #343434; max-height: 1px; }
QFrame#topbar { background: #161616; border-bottom: 1px solid #2B2B2B; }
QStatusBar { background: #131313; color: #D0D0D0; }
QLabel#brand { color: #F5F5F5; font-size: 19px; font-weight: 700; }
QLabel#eyebrow { color: #D6BD56; font-size: 11px; font-weight: 600; }
QLabel#title { color: #F7F7F7; font-size: 32px; font-weight: 700; }
QLabel#heroTitle { color: #F7F7F7; font-size: 36px; font-weight: 700; }
QLabel#subtitle { color: #C3C3C3; font-size: 15px; }
QLabel#muted { color: #AEAEAE; font-size: 12px; }
QLabel#body { color: #C3C3C3; font-size: 14px; }
QLabel#badge { color: #DADADA; background: #2B2B2B; border-radius: 5px; padding: 5px 8px; font-size: 10px; font-weight: 700; }
QLabel#productTitle { font-size: 21px; font-weight: 650; color: #F5F5F5; }
QLabel#section { font-size: 19px; font-weight: 650; color: #F5F5F5; }
QPushButton { font-size: 13px; background: transparent; color: #CECECE; border: 1px solid transparent; border-radius: 8px; padding: 10px 13px; text-align: left; }
QPushButton:hover { background: #292929; color: #FFFFFF; }
QPushButton:pressed { background: #363636; }
QPushButton:focus { border-color: #A0A0A0; }
QPushButton#nav { min-height: 19px; }
QPushButton#navactive { min-height: 19px; background: #353024; border: 1px solid #66582A; color: #FFE16A; font-weight: 650; }
QPushButton#primary { background: #FFD200; color: #111111; border: 1px solid #FFE36B; padding: 10px 17px; font-weight: 700; text-align: center; }
QPushButton#primary:hover { background: #FFE04D; }
QPushButton#primary:pressed { background: #D7B100; }
QPushButton#secondary, QPushButton#danger { background: #232323; color: #F0F0F0; border-color: #393939; font-weight: 600; }
QPushButton#secondary:hover, QPushButton#danger:hover { background: #303030; border-color: #616161; }
QPushButton#primary:focus, QPushButton#secondary:focus, QPushButton#danger:focus { border-color: #888888; }
QPushButton:disabled, QPushButton#primary:disabled, QPushButton#secondary:disabled { color: #8F8F8F; background: #202020; }
QFrame#hero { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #292720,stop:1 #1B1B1B); border: 1px solid #4B4536; border-radius: 18px; }
QFrame#card, QFrame#tile { background: #1D1D1D; border: 1px solid #3B3B3B; border-radius: 16px; }
QFrame#card:hover { border-color: #59544A; }
QFrame#sectionPanel { background: #1B1B1B; border: 1px solid #353535; border-radius: 14px; }
QPushButton#segment { font-weight: 700; padding: 8px 14px; border-color: #383838; background: #1B1B1B; }
QPushButton#segment:hover { border-color: #777777; }
QPushButton#segment:checked { background: #383122; color: #FFE16A; border-color: #786332; }
QLabel#topTitle { font-size: 15px; font-weight: 650; color: #EAEAEA; }
QTextBrowser { background: #191919; color: #ECECEC; border: 1px solid #333333; border-radius: 12px; padding: 15px; }
QDialog { background: #171717; color: #F4F4F4; }
QFrame#dialogHeader { background: #252525; border: 1px solid #373737; border-radius: 12px; }
QFrame#releaseCard { background: #1F1F1F; border: 1px solid #383838; border-radius: 12px; }
QFrame#releaseReady { background: #242217; border: 1px solid #50451C; border-radius: 12px; }
QLabel#releaseName { color: #F5F5F5; font-size: 16px; font-weight: 700; }
QLabel#releaseStatus { color: #D0D0D0; font-size: 12px; font-weight: 600; }
QLabel#dialogTitle { color: #F5F5F5; font-size: 23px; font-weight: 700; }
QLabel#taskLabel { color: #E9E9E9; padding: 4px 7px; }
QWidget#taskStrip { background: #232323; border: 1px solid #383838; border-radius: 8px; }
QFileDialog QAbstractItemView, QFileDialog QTreeView { background: #202020; color: #EFEFEF; selection-background-color: #FFD200; selection-color: #141414; }
QFileDialog QHeaderView::section { background: #282828; color: #D0D0D0; border: 0; padding: 6px; }
QFileDialog QLabel { color: #EEEEEE; }
QLineEdit { background: #222222; color: #F4F4F4; border: 1px solid #4A4A4A; border-radius: 6px; padding: 8px; }
QFrame#art { background: #181818; border: 1px solid #363636; border-radius: 10px; }
QProgressBar { border: 0; background: #292929; height: 6px; border-radius: 3px; text-align: center; }
QProgressBar::chunk { background: #FFD200; border-radius: 3px; }
QPushButton#language { padding: 9px 12px; background: #232323; border: 1px solid #393939; color: #EEEEEE; }
QPushButton#language:hover, QPushButton#language:pressed { border-color: #8A741C; background: #2B281B; }
QMenu { background: #202020; color: #F3F3F3; border: 1px solid #4A4A4A; padding: 6px; }
QMenu::item { padding: 9px 27px 9px 29px; border-radius: 6px; }
QMenu::item:selected { background: #393322; color: #FFD200; }
QMenu::item:checked { color: #FFD200; }
QFrame#newsLead { background: #1E1D19; border: 1px solid #4A4430; border-radius: 14px; }
QFrame#libraryEntry { background: #1D1D1D; border: 1px solid #3D3D3D; border-radius: 14px; }
QFrame#libraryEntry:hover { border-color: #57513D; }
QLabel#libraryCount { background: #292518; border: 1px solid #514522; border-radius: 8px; padding: 6px 9px; color: #FFD200; font-weight: 700; }
QFrame#newsStory { background: #1C1C1C; border: 1px solid #373737; border-radius: 14px; }
QLabel#newsTitle { color: #F6F6F6; font-size: 24px; font-weight: 700; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: #101010; width: 9px; margin: 0; }
QScrollBar::handle:vertical { background: #484848; border-radius: 4px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def tr(key):
    return TEXT.get(Hub.lang, TEXT["en"]).get(key, TEXT["en"].get(key, key))


class ProductWorker(QThread):
    progress = pyqtSignal(int, str)
    done = pyqtSignal(str, str, str, str)

    def __init__(self, product, action, install_dir, expected_hash=None):
        super().__init__()
        self.product, self.action, self.install_dir = product, action, Path(install_dir)
        self.expected_hash = expected_hash

    def run(self):
        temporary = None
        try:
            reject_reparse(self.install_dir)
            reject_reparse(self.install_dir / self.product["exe"])
            reject_reparse(self.install_dir / (self.product["exe"] + ".new"))
            if self.action == "verify":
                self.progress.emit(35, workspace_copy("verify", Hub.lang))
                if not self.expected_hash:
                    raise ValueError(workspace_copy("no_baseline", Hub.lang))
                if digest_file(self.install_dir / self.product["exe"]) != self.expected_hash:
                    raise ValueError(workspace_copy("changed", Hub.lang))
                self.done.emit("verify", "", "", str(self.install_dir))
                return
            if self.action in ("install", "update"):
                self.progress.emit(5, tr("progress_download"))
                repo = self.product["repo"]
                req = Request(f"https://api.github.com/repos/{repo}/releases/latest", headers={"User-Agent": "EnigmaHub/1.0", "Accept": "application/vnd.github+json"})
                with urlopen(req, timeout=25) as resp:
                    release = json.loads(resp.read(2 * 1024 * 1024))
                version = str(release.get("tag_name", "")).lstrip("v")
                wanted = self.product["asset"].format(version=version) if self.product["id"] == "cube" else self.product["asset"]
                asset = next((a for a in release.get("assets", []) if a.get("name") == wanted), None)
                if not asset:
                    raise ValueError(f"Release asset not found: {wanted}")
                digest = str(asset.get("digest", ""))
                if not digest.startswith("sha256:"):
                    raise ValueError(tr("checksum_missing"))
                url = str(asset.get("browser_download_url", ""))
                if not url.startswith(f"https://github.com/{repo}/releases/download/"):
                    raise ValueError("Unexpected release download URL")
                expected = digest.split(":", 1)[1].lower()
                size = int(asset.get("size", 0))
                if size <= 0 or size > (1500 * 1024 * 1024) or len(expected) != 64:
                    raise ValueError("Invalid release metadata")
                downloads = APPDATA / "downloads"
                reject_reparse(downloads)
                downloads.mkdir(parents=True, exist_ok=True)
                target = downloads / wanted
                temporary = target.with_suffix(".part")
                reject_reparse(target)
                reject_reparse(temporary)
                h, received = hashlib.sha256(), 0
                with urlopen(Request(url, headers={"User-Agent": "EnigmaHub/" + HUB_VERSION}), timeout=35) as response, temporary.open("wb") as out:
                    while True:
                        block = response.read(1024 * 128)
                        if not block:
                            break
                        out.write(block); h.update(block); received += len(block)
                        if received > size:
                            raise ValueError("Downloaded file exceeds release size")
                        self.progress.emit(min(75, 5 + int(received * 70 / size)), tr("progress_download"))
                if received != size or h.hexdigest() != expected:
                    raise ValueError("SHA-256 verification failed; installation cancelled")
                os.replace(temporary, target)
                self.progress.emit(80, tr("integrity"))
                self.install_dir.parent.mkdir(parents=True, exist_ok=True)
                if self.product["id"] == "cube":
                    args = [str(target), "--quiet", "--dir", str(self.install_dir)]
                    if self.action == "update":
                        args.insert(1, "--update")
                    self.progress.emit(85, tr("progress_install"))
                    result = subprocess.run(args, cwd=str(downloads), timeout=600, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    if result.returncode != 0:
                        raise RuntimeError(f"Enigma Cube setup exited with code {result.returncode}")
                else:
                    self.progress.emit(85, tr("progress_install"))
                    self.install_dir.mkdir(parents=True, exist_ok=True)
                    executable = self.install_dir / self.product["exe"]
                    staged = executable.with_suffix(executable.suffix + ".new")
                    shutil.copy2(target, staged)
                    os.replace(staged, executable)
                    create_shortcuts(self.product["name"], executable)
                if not (self.install_dir / self.product["exe"]).is_file():
                    raise RuntimeError("The installer finished without creating the application file.")
                self.progress.emit(100, tr("installed_ok"))
                self.done.emit(self.action, version, "", str(self.install_dir))
            elif self.action == "remove":
                self.progress.emit(25, tr("progress_remove"))
                if self.product["id"] == "cube":
                    executable = self.install_dir / self.product["exe"]
                    result = subprocess.run(
                        [str(executable), "--uninstall", "--quiet"],
                        cwd=str(self.install_dir),
                        timeout=120,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    if result.returncode != 0:
                        raise RuntimeError(f"Uninstaller exited with code {result.returncode}")
                    deadline = time.monotonic() + 45
                    while executable.exists() and time.monotonic() < deadline:
                        time.sleep(0.25)
                    if executable.exists():
                        raise RuntimeError("Enigma Cube did not finish uninstalling.")
                else:
                    exe = self.install_dir / self.product["exe"]
                    try:
                        if exe.exists():
                            exe.unlink()
                        if self.install_dir.exists() and not any(self.install_dir.iterdir()):
                            self.install_dir.rmdir()
                    except PermissionError as exc:
                        raise RuntimeError("Close Enigma Disk and try again.") from exc
                    remove_shortcuts(self.product["name"])
                self.done.emit("remove", "", "", str(self.install_dir))
        except Exception as exc:
            self.done.emit(self.action, "", str(exc), str(self.install_dir))
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)


NEWS_FIELDS = ("name", "tag", "title", "body", "url", "date")


def read_news_file(path):
    try:
        rows = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    if not isinstance(rows, list):
        return []
    return [
        row for row in rows
        if isinstance(row, dict)
        and all(isinstance(row.get(key), str) for key in NEWS_FIELDS)
        and row["url"].startswith("https://github.com/d4rv1n17/")
    ]


class NewsWorker(QThread):
    loaded = pyqtSignal(dict, list)

    def run(self):
        results = {}
        errors = []
        for product in PRODUCTS:
            name = product["name"]
            try:
                repo = product["repo"]
                request = Request(
                    f"https://api.github.com/repos/{repo}/releases?per_page=3",
                    headers={"User-Agent": "EnigmaHub/1.0", "Accept": "application/vnd.github+json"},
                )
                with urlopen(request, timeout=8) as response:
                    releases = json.load(response)
                if not isinstance(releases, list):
                    raise ValueError("Unexpected release response")
                results[name] = [
                    {
                        "name": name,
                        "tag": release["tag_name"],
                        "title": release.get("name") or release["tag_name"],
                        "body": release.get("body") or "",
                        "url": release.get("html_url") or product["url"],
                        "date": (release.get("published_at") or "")[:10],
                    }
                    for release in releases[:3]
                    if not release.get("draft") and not release.get("prerelease")
                ]
            except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
                errors.append(f"{name}: {error}")
        self.loaded.emit(results, errors)


class UpdateCheckWorker(QThread):
    checked = pyqtSignal(dict, str)
    def run(self):
        results = {}
        errors = []
        for product in PRODUCTS:
            try:
                req = Request(f"https://api.github.com/repos/{product['repo']}/releases/latest", headers={"User-Agent": "EnigmaHub/1.0"})
                with urlopen(req, timeout=15) as response:
                    data = json.loads(response.read(1024 * 1024))
                results[product["id"]] = str(data.get("tag_name", "")).lstrip("v")
            except Exception as exc:
                errors.append(product["name"] + ": " + str(exc))
        self.checked.emit(results, "\n".join(errors))


def create_shortcuts(name, executable):
    if os.name != "nt": return
    escaped_name = name.replace("'", "''")
    escaped_exe = str(executable).replace("'", "''")
    script = "$s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Programs')) '" + escaped_name + ".lnk')); $s.TargetPath='" + escaped_exe + "'; $s.WorkingDirectory='" + str(executable.parent).replace("'", "''") + "'; $s.Save()"
    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def remove_shortcuts(name):
    if os.name != "nt": return
    for base in (Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs", Path(os.environ.get("USERPROFILE", "")) / "Desktop"):
        path = base / f"{name}.lnk"
        try: path.unlink(missing_ok=True)
        except OSError: pass


@lru_cache(maxsize=64)
def ui_icon(name, color="#C2C2C2"):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
        f'<path d="{ICONS[name]}" fill="none" stroke="{color}" stroke-width="1.65" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(svg.encode()).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


def dark_caption(widget):
    """Color the native title bar and retain Windows snap, resize and system controls."""
    if sys.platform != "win32":
        return
    try:
        hwnd = ctypes.c_void_p(int(widget.winId()))
        set_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        dark = ctypes.c_int(1)
        if set_attribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark)) != 0:
            set_attribute(hwnd, 19, ctypes.byref(dark), ctypes.sizeof(dark))
        caption = ctypes.c_uint(0x00161616)
        text = ctypes.c_uint(0x00F5F5F5)
        set_attribute(hwnd, 35, ctypes.byref(caption), ctypes.sizeof(caption))
        set_attribute(hwnd, 36, ctypes.byref(text), ctypes.sizeof(text))
    except (AttributeError, OSError):
        pass


def center_on_screen(widget, screen):
    frame = widget.frameGeometry()
    frame.moveCenter(screen.availableGeometry().center())
    widget.move(frame.topLeft())


class PageTransition(QWidget):
    """A single cached frame, composited over the live destination page."""

    def __init__(self, parent, outgoing, duration=225, opacity=1.0):
        super().__init__(parent)
        self.outgoing = outgoing
        self.duration = duration
        self.opacity = opacity
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.NoFocus)
        self.clock = QElapsedTimer()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        screen = self.window().screen()
        refresh = screen.refreshRate() if screen else 60.0
        self.timer.setInterval(max(4, round(1000 / max(60.0, refresh))))
        self.timer.timeout.connect(self.tick)
        self.phase = 0.0
        self.clock.start()
        self.show()
        self.raise_()
        self.timer.start()

    def tick(self):
        elapsed = self.clock.elapsed() / self.duration
        if elapsed >= 1:
            self.timer.stop()
            self.hide()
            self.deleteLater()
            return
        self.phase = 1 - (1 - elapsed) ** 3
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self.opacity * (1 - self.phase))
        if self.outgoing.isNull():
            painter.fillRect(self.rect(), QColor("#101010"))
        else:
            painter.drawPixmap(-int(self.phase * 24), 0, self.outgoing)


class StartupIntro(QWidget):
    def __init__(self, language, motion):
        super().__init__(None, Qt.SplashScreen | Qt.FramelessWindowHint)
        self.setFixedSize(480, 266)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAccessibleName("Enigma Hub")
        self.slogan = SLOGANS[language]
        self.brand = QPixmap(str(ROOT / "assets" / "hub-fold-koulen.png"))
        self.phase = 0.0 if motion else 1.0
        self.reveal = QVariantAnimation(self)
        self.reveal.setDuration(1560)
        self.reveal.setStartValue(0.0)
        self.reveal.setEndValue(1.0)
        self.reveal.valueChanged.connect(self.advance)
        if motion:
            self.reveal.start()

    def advance(self, phase):
        self.phase = phase
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        rect = QRectF(self.rect())
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor("#28251A"))
        gradient.setColorAt(0.55, QColor("#171717"))
        gradient.setColorAt(1, QColor("#101010"))
        painter.fillRect(rect, gradient)
        painter.setPen(QColor("#34332D"))
        for x in range(0, self.width(), 24):
            painter.drawLine(x, 0, x, self.height())
        painter.fillRect(0, 0, self.width(), 2, QColor("#FFD200"))

        reveal = min(1.0, self.phase * 2.6)
        reveal = 1.0 - (1.0 - reveal) ** 3
        painter.setOpacity(reveal)
        width = 306.0
        height = width * self.brand.height() / max(1, self.brand.width())
        logo_box = QRectF((self.width() - width) / 2, 78 + 13 * (1 - reveal), width, height)
        painter.drawPixmap(logo_box, self.brand, QRectF(self.brand.rect()))
        painter.setOpacity(min(1.0, max(0.0, (self.phase - 0.12) * 3.7)))
        painter.setFont(QFont("Segoe UI", 11))
        painter.setPen(QColor("#E0E0E0"))
        painter.drawText(QRectF(31, 155, 418, 52), Qt.AlignCenter | Qt.TextWordWrap, self.slogan)
        painter.setOpacity(1.0)
        painter.fillRect(32, 230, 416, 2, QColor("#333333"))
        painter.fillRect(QRectF(32, 230, 416 * self.phase, 2), QColor("#FFD200"))


class Cover(QWidget):
    """Cropped cover art with a short hover zoom that does not change the layout."""

    def __init__(self, filename, height, icon=None):
        super().__init__()
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        assets = ROOT / "assets"
        picture = QImage(str(assets / filename)) if filename else QImage()
        self.art = QPixmap.fromImage(picture)
        self.icon = QPixmap(str(assets / icon)) if icon else QPixmap()
        self.motion = QVariantAnimation(self)
        self.motion.setDuration(240)
        self.motion.setEasingCurve(QEasingCurve.OutCubic)
        self.motion.valueChanged.connect(self.on_motion)
        self.zoom = 0.0

    def on_motion(self, value):
        self.zoom = value
        self.update()

    def animate(self, target):
        if not getattr(self.window(), "state", {}).get("motion", True):
            return
        self.motion.stop()
        self.motion.setStartValue(self.zoom)
        self.motion.setEndValue(target)
        self.motion.start()

    def enterEvent(self, event):
        self.animate(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        clip = QPainterPath()
        clip.addRoundedRect(bounds, 12, 12)
        painter.setClipPath(clip)
        painter.fillRect(bounds, QColor("#242424"))
        if not self.art.isNull():
            scale = max(bounds.width() / self.art.width(), bounds.height() / self.art.height())
            scale *= 1 + 0.085 * self.zoom
            width = self.art.width() * scale
            height = self.art.height() * scale
            target = QRectF((bounds.width() - width) / 2, (bounds.height() - height) / 2, width, height)
            painter.drawPixmap(target, self.art, QRectF(self.art.rect()))
        else:
            painter.setPen(QColor("#333333"))
            for x in range(0, self.width(), 24):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 24):
                painter.drawLine(0, y, self.width(), y)
        shade = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        shade.setColorAt(0, QColor(18, 18, 18, 16))
        shade.setColorAt(1, QColor(12, 12, 12, 70 - int(self.zoom * 32)))
        painter.fillRect(bounds, shade)
        if not self.icon.isNull():
            size = min(bounds.height() * 0.61, 153) * (1 + 0.035 * self.zoom)
            icon_bounds = QRectF((bounds.width() - size) / 2, (bounds.height() - size) / 2, size, size)
            painter.drawPixmap(icon_bounds, self.icon, QRectF(self.icon.rect()))
        painter.setClipping(False)
        painter.setPen(QColor(60 + int(self.zoom * 95), 60 + int(self.zoom * 72), 60 + int(self.zoom * 10)))
        painter.drawPath(clip)


class Hub(QMainWindow):
    lang = "en"
    def __init__(self):
        super().__init__()
        self.state = self.load_state()
        Hub.lang = self.state.get("lang", "en")
        self.setWindowTitle("Enigma Hub")
        self.setMinimumSize(820, 600)
        self.adaptive_rows = []
        self.resize(1040, 625)
        ico = ROOT / "assets" / "hub-icon.ico"
        if ico.exists(): self.setWindowIcon(QIcon(str(ico)))
        self.setStyleSheet(STYLE + PREMIUM_STYLE)
        self.workers = []
        self.hub_release = None
        self.latest_versions = {}
        self.closing = False
        self.path_labels = {}
        self.product_controls = {}
        self.catalog_query = ""
        self.library_query = ""
        self.library_filter = "all"
        self.library_sort = "recent"
        self.build_shell()
        self.pages = [self.page_home(), self.page_catalog(), self.page_library(), self.page_news(), self.page_settings()]
        for page in self.pages: self.stack.addWidget(page)
        self.install_shortcuts()
        self.navigate(0, animate=False)
        self.hub_update_timer = QTimer(self)
        self.hub_update_timer.setInterval(4 * 60 * 60 * 1000)
        self.hub_update_timer.timeout.connect(self.check_hub_update)
        self.hub_update_timer.start()
        QTimer.singleShot(5000, self.check_hub_update)
        if self.state.get("auto_check", True):
            QTimer.singleShot(1300, self.load_news)
            QTimer.singleShot(3200, lambda:self.check_updates(silent=True))

    def load_state(self):
        try:
            result = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            result = {}
        if not isinstance(result, dict):
            result = {}
        state = {**DEFAULTS, **result}
        paths = result.get("paths")
        state["paths"] = dict(DEFAULTS["paths"])
        if isinstance(paths, dict):
            for key in state["paths"]:
                path = paths.get(key)
                if isinstance(path, str) and path and "\x00" not in path:
                    state["paths"][key] = path
        games = result.get("games")
        state["games"] = {}
        if isinstance(games, dict):
            for key, config in games.items():
                if isinstance(config, dict):
                    state["games"][key] = {
                        field: value for field, value in config.items()
                        if isinstance(value, str) and "\x00" not in value
                    }
        if not isinstance(state.get("installed"), dict):
            state["installed"] = {}
        if not isinstance(state.get("lang"), str) or state["lang"] not in TEXT:
            state["lang"] = DEFAULTS["lang"]
        for key in ("recent", "hashes"):
            state[key] = {k: v for k, v in result.get(key, {}).items() if isinstance(k, str) and isinstance(v, str)} if isinstance(result.get(key), dict) else {}
        state["installed"] = {k: v for k, v in state["installed"].items() if isinstance(k, str) and isinstance(v, str)}
        state["favorites"] = [v for v in result.get("favorites", []) if isinstance(v, str)] if isinstance(result.get("favorites"), list) else []
        state["history"] = [v for v in result.get("history", []) if isinstance(v, dict) and all(isinstance(v.get(k), str) for k in ("name", "action", "date", "status"))][-100:] if isinstance(result.get("history"), list) else []
        for key in ("auto_check", "motion", "hub_auto_update", "intro"):
            state[key] = result.get(key, DEFAULTS[key]) if isinstance(result.get(key, DEFAULTS[key]), bool) else DEFAULTS[key]
        return state

    def wc(self, key):
        return workspace_copy(key, Hub.lang)

    def install_shortcuts(self):
        self.keyboard_shortcuts = []
        for index in range(5):
            shortcut = QShortcut("Ctrl+" + str(index + 1), self)
            shortcut.activated.connect(lambda i=index: self.navigate(i))
            self.keyboard_shortcuts.append(shortcut)
        search = QShortcut("Ctrl+K", self)
        search.activated.connect(self.focus_search)
        self.keyboard_shortcuts.append(search)

    def focus_search(self):
        self.navigate(1)
        self.catalog_search.setFocus()
        self.catalog_search.selectAll()

    def record_activity(self, item, action, status="success"):
        self.state["history"].append({"name": item["name"], "action": action, "status": status, "date": datetime.now().isoformat(timespec="seconds")})
        self.state["history"] = self.state["history"][-100:]
        if action == "launch" and status == "success":
            self.state["recent"][item["id"]] = datetime.now().isoformat(timespec="seconds")
        self.save_state()

    def favorite_button(self, item):
        button = QPushButton(objectName="favorite")
        button.setCheckable(True)
        button.setChecked(item["id"] in self.state["favorites"])
        button.setIcon(ui_icon("star", "#E2C867" if button.isChecked() else "#A3A3A3"))
        button.setToolTip(self.wc("favorites"))
        button.setAccessibleName(self.wc("favorites") + " · " + item["name"])
        def toggle(checked):
            favorites = self.state["favorites"]
            if checked and item["id"] not in favorites:
                favorites.append(item["id"])
            elif not checked and item["id"] in favorites:
                favorites.remove(item["id"])
            button.setIcon(ui_icon("star", "#E2C867" if checked else "#A3A3A3"))
            self.save_state()
            self.refresh_library()
        button.toggled.connect(toggle)
        return button

    def save_state(self):
        APPDATA.mkdir(parents=True, exist_ok=True)
        temporary = STATE_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(STATE_FILE)

    def dialog_panel(self, title, message="", icon=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(min(620, self.width() - 56), 300)
        dialog.setMinimumWidth(min(460, self.width() - 56))
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(16)
        header = QFrame(objectName="dialogHeader")
        heading = QHBoxLayout(header)
        heading.setContentsMargins(14, 13, 14, 13)
        heading.addWidget(self.icon_label(icon, "#FFD200", 25) if icon else self.asset_image("hub-icon.png", 32))
        heading.addWidget(self.copy_label(title, "dialogTitle"), 1)
        layout.addWidget(header)
        if message:
            copy = self.copy_label(message, "body")
            copy.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(copy)
        return dialog, layout

    def dialog_actions(self, dialog, layout, accept_label, cancel=False):
        row = QHBoxLayout()
        row.addStretch()
        if cancel:
            dismiss = QPushButton(tr("cancel"), objectName="secondary")
            dismiss.clicked.connect(dialog.reject)
            dismiss.setAutoDefault(False)
            row.addWidget(dismiss)
            dismiss.setFocus()
        accept = QPushButton(accept_label, objectName="primary")
        accept.clicked.connect(dialog.accept)
        accept.setDefault(not cancel)
        accept.setAutoDefault(not cancel)
        row.addWidget(accept)
        layout.addLayout(row)

    def present_dialog(self, dialog):
        dark_caption(dialog)
        if self.state.get("motion", True):
            dialog.setWindowOpacity(0.76)
            fade = QPropertyAnimation(dialog, b"windowOpacity", dialog)
            fade.setDuration(155)
            fade.setStartValue(0.76)
            fade.setEndValue(1.0)
            fade.setEasingCurve(QEasingCurve.OutCubic)
            fade.start()
        try:
            return dialog.exec_()
        finally:
            dialog.deleteLater()

    def notify(self, title, message):
        dialog, layout = self.dialog_panel(title)
        text = QTextBrowser()
        text.setPlainText(message)
        text.setFrameShape(QFrame.NoFrame)
        text.setMinimumHeight(100)
        text.setMaximumHeight(210)
        layout.addWidget(text)
        self.dialog_actions(dialog, layout, "OK")
        self.present_dialog(dialog)

    def pick_path(self, title, path, directory, parent=None):
        picker = QFileDialog(parent or self, title, path)
        picker.setOption(QFileDialog.DontUseNativeDialog)
        picker.setFileMode(QFileDialog.Directory if directory else QFileDialog.ExistingFile)
        if directory:
            picker.setOption(QFileDialog.ShowDirsOnly)
        else:
            picker.setNameFilter("Windows (*.exe)")
        dark_caption(picker)
        try:
            return picker.selectedFiles()[0] if picker.exec_() == QDialog.Accepted and picker.selectedFiles() else ""
        finally:
            picker.deleteLater()

    def scroll(self, widget):
        if not widget.objectName():
            widget.setObjectName("page")
        widget.setAttribute(Qt.WA_StyledBackground, True)
        area = QScrollArea(); area.setWidgetResizable(True); area.setFrameShape(QFrame.NoFrame); area.setStyleSheet("QScrollArea { background:#121212; border:0; }"); area.viewport().setObjectName("hubScrollViewport"); area.viewport().setStyleSheet("QWidget#hubScrollViewport { background:#121212; border:0; }"); area.setWidget(widget)
        return area

    @staticmethod
    def icon_label(name, color="#C2C2C2", size=19):
        label = QLabel()
        label.setPixmap(ui_icon(name, color).pixmap(size, size))
        return label

    def build_shell(self):
        root = QWidget(objectName="root"); shell = QHBoxLayout(root); shell.setContentsMargins(0,0,0,0); shell.setSpacing(0)
        side = QFrame(objectName="sidebar"); side.setFixedWidth(190); sl = QVBoxLayout(side); sl.setContentsMargins(14,26,14,18); sl.setSpacing(8)
        brand_row = QHBoxLayout()
        brand = self.asset_image("hub-fold-koulen.png", 162)
        brand.setAccessibleName("Enigma Hub")
        brand_row.addWidget(brand)
        brand_row.addStretch()
        sl.addLayout(brand_row)
        sl.addSpacing(16)
        sl.addWidget(QFrame(objectName="railDivider"))
        sl.addSpacing(10)
        sl.addWidget(self.copy_label(self.wc("workspace"), "eyebrow"))
        self.nav_buttons=[]; self.stack=QStackedWidget()
        for index, key in enumerate(("overview", "catalog", "library", "news")):
            button = QPushButton(tr(key))
            button.clicked.connect(lambda checked=False, page=index: self.navigate(page))
            sl.addWidget(button)
            self.nav_buttons.append(button)
        sl.addStretch()
        activity = QPushButton(self.wc("activity"))
        activity.setIcon(ui_icon("activity"))
        activity.clicked.connect(self.show_activity)
        sl.addWidget(activity)
        sl.addWidget(self.copy_label("ENIGMA HUB  /  " + HUB_VERSION, "muted"))
        sl.addWidget(QFrame(objectName="railDivider")); self.nav_settings=QPushButton(tr("settings")); self.nav_settings.clicked.connect(lambda:self.navigate(4)); sl.addWidget(self.nav_settings)
        shell.addWidget(side)
        right=QVBoxLayout(); right.setContentsMargins(0,0,0,0); right.setSpacing(0)
        top=QFrame(objectName="topbar"); tl=QHBoxLayout(top); tl.setContentsMargins(28,13,28,13); self.top_title = QLabel(objectName="topTitle"); tl.addWidget(self.top_title); tl.addStretch()
        site=QPushButton(tr("open_site").rstrip(" ↗"),objectName="secondary"); site.setIcon(ui_icon("external")); site.clicked.connect(lambda:webbrowser.open("https://enigmastudioo.com")); tl.addWidget(site)
        languages = (("English", "en"), ("Русский", "ru"), ("Română", "ro"), ("Deutsch", "de"), ("Español", "es"), ("Français", "fr"))
        language = QPushButton(dict((code, name) for name, code in languages)[Hub.lang], objectName="language")
        language.setAccessibleName(tr("language"))
        language.setIcon(ui_icon("language"))
        menu = QMenu(language)
        for name, code in languages:
            action = menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(code == Hub.lang)
            action.triggered.connect(lambda checked=False, value=code: self.change_language(value))
        language.setMenu(menu)
        tl.addWidget(language)
        right.addWidget(top); right.addWidget(self.stack,1); shell.addLayout(right,1); self.setCentralWidget(root)

    def adaptive_row(self, breakpoint, parent=None):
        row = QBoxLayout(QBoxLayout.LeftToRight, parent)
        row.setSpacing(14)
        self.adaptive_rows.append((row, breakpoint))
        self.arrange_rows()
        return row

    def arrange_rows(self):
        for row, breakpoint in list(self.adaptive_rows):
            direction = QBoxLayout.TopToBottom if self.width() < breakpoint else QBoxLayout.LeftToRight
            try:
                if row.direction() != direction:
                    row.setDirection(direction)
            except RuntimeError:
                self.adaptive_rows.remove((row, breakpoint))

    @staticmethod
    def copy_label(text, role):
        label = QLabel(text, objectName=role)
        label.setTextFormat(Qt.PlainText)
        label.setWordWrap(True)
        return label

    def path_label(self, path):
        label = self.copy_label("", "muted")
        self.set_path_text(label, path)
        return label

    @staticmethod
    def set_path_text(label, path):
        import re
        display = re.sub(r"([^\\/]{24})(?=[^\\/])", "\\1" + "\u200b", path)
        display = display.replace("\\", "\\" + "\u200b").replace("/", "/\u200b")
        label.setText(f"{tr('install_path')}: {display}")
        label.setToolTip(path)

    def page_base(self, kicker, title, subtitle):
        page = QWidget(objectName="page")
        box = QVBoxLayout(page)
        box.setContentsMargins(30, 28, 30, 30)
        box.setSpacing(12)
        if kicker != title:
            box.addWidget(self.copy_label(kicker.upper(), "eyebrow"))
        box.addWidget(self.copy_label(title, "title"))
        if subtitle:
            box.addWidget(self.copy_label(subtitle, "subtitle"))
        box.addSpacing(6)
        return page, box

    @staticmethod
    def asset_image(filename, size):
        label = QLabel()
        image = QPixmap(str(ROOT / "assets" / filename))
        label.setPixmap(image.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return label

    def add_product_card(self, layout, product, compact=False):
        frame=QFrame(objectName="card"); frame.setMinimumWidth(245); box=QVBoxLayout(frame); box.setContentsMargins(16,16,16,16); box.setSpacing(12)
        box.addWidget(Cover(product["id"] + "-surface.svg", 110 if compact else 150, product["id"] + ".png"))
        row=QHBoxLayout(); row.addStretch(); state=QLabel("",objectName="muted"); self.product_badges=getattr(self,"product_badges",{}); self.product_badges.setdefault(product["id"], []).append(state); row.addWidget(state); box.addLayout(row)
        tagline,description=meta(product)
        name=QLabel(product["name"],objectName="productTitle"); box.addWidget(name); tag=self.copy_label(tagline,"eyebrow"); box.addWidget(tag)
        desc=QLabel(description,objectName="body"); desc.setWordWrap(True); box.addWidget(desc); version=QLabel(f"{tr('release')}   {product['version']}   ·   Windows",objectName="muted"); box.addWidget(version)
        box.addStretch()
        actions=QHBoxLayout(); main=QPushButton(tr("launch") if self.is_installed(product) else tr("install"),objectName="primary"); main.clicked.connect(lambda checked=False,p=product:self.primary_product_action(p)); actions.addWidget(main,2)
        detail=QPushButton(tr("details"),objectName="secondary"); detail.clicked.connect(lambda checked=False,p=product:self.show_product_detail(p)); actions.addWidget(detail,1); box.addLayout(actions)
        self.product_cards = getattr(self, "product_cards", {})
        self.product_cards.setdefault(product["id"], []).append((main, version))
        if not compact:
            self.catalog_tiles[product["id"]] = (frame, product)
        main.setIcon(ui_icon("play" if self.is_installed(product) else "download", "#171717"))
        layout.addWidget(frame,1)

    def page_home(self):
        page = QWidget(objectName="page")
        box = QVBoxLayout(page)
        box.setContentsMargins(26, 22, 26, 26)
        box.setSpacing(14)
        hero = QFrame(objectName="hero")
        hb = self.adaptive_row(950, hero)
        hb.setContentsMargins(21, 17, 21, 17)
        left = QVBoxLayout()
        left.addWidget(self.copy_label("ENIGMA STUDIO", "eyebrow"))
        left.addWidget(self.copy_label(SLOGANS[Hub.lang], "heroTitle"))
        left.addWidget(self.copy_label(tr("intro"), "subtitle"))
        left.addSpacing(6)
        go = QPushButton(tr("explore"), objectName="primary")
        go.setIcon(ui_icon("catalog", "#141414"))
        go.clicked.connect(lambda: self.navigate(1))
        actions = self.adaptive_row(990)
        actions.addWidget(go)
        library = QPushButton(tr("library"), objectName="secondary")
        library.setIcon(ui_icon("library"))
        library.clicked.connect(lambda: self.navigate(2))
        actions.addWidget(library)
        actions.addStretch()
        left.addLayout(actions)
        hb.addLayout(left, 3)
        art = Cover("hub-universe.svg", 180)
        hb.addWidget(art, 2)
        box.addWidget(hero)
        stats = self.adaptive_row(900)
        for icon, title, value in (("catalog", tr("apps"), str(len(PRODUCTS))), ("library", tr("games"), str(len(GAMES))), ("shield", tr("integrity_title"), "SHA-256")):
            panel = QFrame(objectName="stat")
            content = QHBoxLayout(panel)
            content.setContentsMargins(14, 12, 14, 12)
            content.addWidget(self.icon_label(icon, "#DCC574", 22))
            copy = QVBoxLayout()
            copy.addWidget(self.copy_label(value, "statValue"))
            copy.addWidget(self.copy_label(title, "muted"))
            content.addLayout(copy, 1)
            stats.addWidget(panel, 1)
        box.addLayout(stats)
        section=self.adaptive_row(880); section.addWidget(QLabel(tr("featured"),objectName="section")); section.addStretch(); all_btn=QPushButton(tr("view")); all_btn.clicked.connect(lambda:self.navigate(1)); section.addWidget(all_btn); box.addLayout(section)
        cards = self.adaptive_row(945)
        for p in PRODUCTS: self.add_product_card(cards,p,compact=True)
        box.addLayout(cards)
        box.addStretch()
        return self.scroll(page)

    def page_catalog(self):
        page, box = self.page_base(self.wc("workspace"), tr("catalog"), self.wc("quick"))
        self.catalog_tiles = {}
        self.catalog_search = QLineEdit()
        self.catalog_search.setPlaceholderText(self.wc("search") + "  Ctrl+K")
        self.catalog_search.setClearButtonEnabled(True)
        self.catalog_search.setAccessibleName(self.wc("search"))
        self.catalog_search.textChanged.connect(self.search_catalog)
        box.addWidget(self.catalog_search)
        tabs = self.adaptive_row(880)
        self.catalog_filters = []
        for index, label in enumerate((tr("view"), tr("apps"), tr("games"))):
            tab = QPushButton(label, objectName="segment")
            tab.setCheckable(True)
            tab.ensurePolished()
            tab.setMinimumWidth(tab.sizeHint().width() + 6)
            tab.clicked.connect(lambda checked=False, selection=index: self.filter_catalog(selection))
            self.catalog_filters.append(tab)
            tabs.addWidget(tab)
        tabs.addStretch()
        box.addLayout(tabs)

        self.catalog_sections = []
        self.game_states = {}
        self.game_launch_buttons = {}
        for key, entries, add in (
            ("apps", PRODUCTS, self.add_product_card),
            ("games", GAMES, self.add_game_card),
        ):
            section = QWidget()
            content = QVBoxLayout(section)
            content.setContentsMargins(0, 6, 0, 0)
            content.setSpacing(13)
            content.addWidget(self.copy_label(tr(key), "section"))
            cards = self.adaptive_row(1110 if key == "apps" else 1260)
            for entry in entries:
                add(cards, entry)
            content.addLayout(cards)
            if key == "games":
                content.addWidget(self.copy_label(tr("external"), "muted"))
            self.catalog_sections.append(section)
            box.addWidget(section)
        box.addStretch()
        self.catalog_empty = self.copy_label(self.wc("no_results"), "body")
        box.insertWidget(box.count() - 1, self.catalog_empty)
        self.catalog_empty.hide()
        self.filter_catalog(0)
        return self.scroll(page)

    def filter_catalog(self, selection):
        previous = getattr(self, "catalog_selection", None)
        self.catalog_selection = selection
        for index, button in enumerate(self.catalog_filters):
            button.setChecked(index == selection)
        self.stop_page_animation()
        visible = []
        for index, section in enumerate(self.catalog_sections, 1):
            show = selection in (0, index)
            section.setVisible(show)
            if show:
                visible.append(section)
        page = self.stack.currentWidget()
        if isinstance(page, QScrollArea) and self.stack.currentIndex() == 1:
            page.widget().layout().activate()
            page.verticalScrollBar().setValue(0)
        self.search_catalog(self.catalog_search.text())

    def search_catalog(self, text):
        query = text.casefold().strip()
        count = 0
        for tile, item in self.catalog_tiles.values():
            selected = self.catalog_selection in (0, 1 if item in PRODUCTS else 2)
            matches = query in " ".join((item["name"], *meta(item))).casefold()
            tile.setVisible(matches and selected)
            count += bool(matches and selected)
        if hasattr(self, "catalog_empty"):
            self.catalog_empty.setVisible(count == 0)

    def add_game_card(self, layout, game):
        frame = QFrame(objectName="card")
        box = QVBoxLayout(frame)
        box.setContentsMargins(16, 16, 16, 16)
        box.setSpacing(10)
        box.addWidget(Cover(game["id"] + "-cover.webp", 155))
        genre, description = meta(game)
        box.addWidget(self.copy_label(genre, "eyebrow"))
        box.addWidget(self.copy_label(game["name"], "productTitle"))
        box.addWidget(self.copy_label(description, "body"))
        status = self.copy_label("", "muted")
        self.game_states.setdefault(game["id"], []).append(status)
        box.addWidget(status)
        box.addStretch()
        launch = QPushButton(tr("launch"), objectName="primary")
        launch.clicked.connect(lambda checked=False: self.launch_game(game))
        self.game_launch_buttons.setdefault(game["id"], []).append(launch)
        box.addWidget(launch)
        store = QPushButton(self.game_link_label(game), objectName="secondary")
        store.clicked.connect(lambda checked=False: self.open_game_store(game))
        box.addWidget(store)
        detail = QPushButton(tr("details"))
        detail.clicked.connect(lambda checked=False: self.show_game_detail(game))
        box.addWidget(detail)
        self.catalog_tiles[game["id"]] = (frame, game)
        layout.addWidget(frame, 1)

    def page_library(self):
        page, box = self.page_base(tr("library"), tr("library"), "")
        hero = QFrame(objectName="hero")
        hero.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        heading = self.adaptive_row(925, hero)
        heading.setContentsMargins(18, 16, 18, 16)
        details = QVBoxLayout()
        details.setSpacing(8)
        details.addWidget(self.icon_label("library", "#FFD200", 25), 0, Qt.AlignLeft)
        self.library_heading = self.copy_label("", "section")
        details.addWidget(self.library_heading)
        counts = QHBoxLayout()
        self.library_counts = []
        for _ in range(2):
            count = self.copy_label("", "libraryCount")
            count.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            self.library_counts.append(count)
            counts.addWidget(count)
        counts.addStretch()
        details.addLayout(counts)
        heading.addLayout(details, 3)
        heading.addWidget(Cover("hub-collection.svg", 128), 2)
        box.addWidget(hero)
        tools = self.adaptive_row(1000)
        self.library_search = QLineEdit()
        self.library_search.setClearButtonEnabled(True)
        self.library_search.setPlaceholderText(self.wc("search"))
        self.library_search.textChanged.connect(lambda text: self.set_library_option("query", text))
        tools.addWidget(self.library_search, 2)
        for option, values in (("filter", ("all", "favorites", "apps", "games")), ("sort", ("recent", "name"))):
            combo = QComboBox()
            for value in values:
                combo.addItem(tr(value) if value in ("apps", "games") else self.wc(value), value)
            combo.setAccessibleName(self.wc("favorites") if option == "filter" else self.wc("recent"))
            combo.currentIndexChanged.connect(lambda index, c=combo, key=option: self.set_library_option(key, c.currentData()))
            tools.addWidget(combo, 1)
        box.addLayout(tools)
        self.library_area = QVBoxLayout()
        self.library_area.setSpacing(12)
        box.addLayout(self.library_area)
        box.addStretch()
        return self.scroll(page)

    def set_library_option(self, key, value):
        setattr(self, "library_" + key, value)
        self.refresh_library()

    def page_news(self):
        page = QWidget(objectName="page")
        box = QVBoxLayout(page)
        box.setContentsMargins(28, 24, 28, 28)
        box.setSpacing(15)
        banner = QFrame(objectName="hero")
        banner_layout = self.adaptive_row(920, banner)
        banner_layout.setContentsMargins(18, 16, 18, 16)
        intro = QVBoxLayout()
        intro.setSpacing(9)
        intro.addWidget(self.copy_label(tr("news_title"), "title"))
        intro.addWidget(self.copy_label(tr("news_desc"), "subtitle"))
        self.news_refresh = QPushButton(NEWS_REFRESH[Hub.lang], objectName="secondary")
        self.news_refresh.setIcon(ui_icon("updates"))
        self.news_refresh.clicked.connect(self.load_news)
        intro.addWidget(self.news_refresh, 0, Qt.AlignLeft)
        banner_layout.addLayout(intro, 3)
        banner_layout.addWidget(Cover("hub-bulletin.svg", 145), 2)
        box.addWidget(banner)
        self.news_status = self.copy_label(tr("no_news"), "muted")
        box.addWidget(self.news_status)
        self.news_content = QVBoxLayout()
        self.news_content.setSpacing(12)
        box.addLayout(self.news_content)
        box.addStretch()
        seed = read_news_file(ROOT / "assets" / "news-seed.json")
        cached = read_news_file(APPDATA / "news-cache.json")
        cached_names = {item["name"] for item in cached}
        self.news_items = sorted(cached + [item for item in seed if item["name"] not in cached_names],
                                 key=lambda item: item["date"], reverse=True)
        self.show_news(self.news_items)
        return self.scroll(page)

    def section_panel(self, title, icon=None):
        panel = QFrame(objectName="sectionPanel")
        content = QVBoxLayout(panel)
        content.setContentsMargins(19, 17, 19, 17)
        content.setSpacing(12)
        if title:
            heading = QHBoxLayout()
            if icon:
                heading.addWidget(self.icon_label(icon, "#FFD200", 21))
            heading.addWidget(self.copy_label(title, "section"), 1)
            content.addLayout(heading)
        return panel, content

    def page_settings(self):
        page, box = self.page_base(tr("settings"), tr("preferences"), "")
        folders, folder_content = self.section_panel(tr("choose_folder"), "folder")
        for product in PRODUCTS:
            row = self.adaptive_row(1040)
            labels = QVBoxLayout()
            labels.addWidget(self.copy_label(product["name"], "productTitle"))
            path = self.path_label(self.state["paths"][product["id"]])
            self.path_labels.setdefault(product["id"], []).append(path)
            labels.addWidget(path)
            row.addLayout(labels, 1)
            choose = QPushButton(tr("choose"), objectName="secondary")
            choose.setIcon(ui_icon("folder"))
            choose.clicked.connect(lambda checked=False, item=product: self.choose_install_folder(item))
            row.addWidget(choose)
            folder_content.addLayout(row)
        box.addWidget(folders)

        preferences, preference_content = self.section_panel(tr("preferences"), "motion")
        motion = QPushButton(MOTION_LABELS[Hub.lang], objectName="segment")
        motion.setCheckable(True)
        motion.setChecked(self.state.get("motion", True))
        def save_motion(enabled):
            self.state["motion"] = enabled
            if not enabled:
                self.stop_page_animation()
                for cover in self.findChildren(Cover):
                    cover.motion.stop()
                    cover.on_motion(0.0)
            self.save_state()
        motion.toggled.connect(save_motion)
        preference_content.addWidget(motion, 0, Qt.AlignLeft)
        intro = QPushButton(self.wc("intro_toggle"), objectName="segment")
        intro.setCheckable(True)
        intro.setChecked(self.state["intro"])
        def set_intro(enabled):
            self.state["intro"] = enabled
            self.save_state()
        intro.toggled.connect(set_intro)
        preference_content.addWidget(intro, 0, Qt.AlignLeft)
        box.addWidget(preferences)

        updates, update_content = self.section_panel(tr("updates"), "updates")
        self.auto_check_button = QPushButton(objectName="segment")
        self.auto_check_button.setCheckable(True)
        self.auto_check_button.setChecked(self.state.get("auto_check", True))
        self.auto_check_button.setText(tr("auto_check"))
        self.auto_check_button.clicked.connect(self.toggle_auto_check)
        update_content.addWidget(self.auto_check_button, 0, Qt.AlignLeft)
        check = QPushButton(tr("check_updates"), objectName="secondary")
        check.setIcon(ui_icon("updates"))
        check.clicked.connect(self.check_updates)
        update_content.addWidget(check, 0, Qt.AlignLeft)
        hub_auto = QPushButton("Enigma Hub · " + tr("auto_check"), objectName="segment")
        hub_auto.setCheckable(True)
        hub_auto.setChecked(self.state.get("hub_auto_update", True))
        hub_auto.setIcon(ui_icon("download"))
        def set_hub_auto(enabled):
            self.state["hub_auto_update"] = enabled
            self.save_state()
            if enabled:
                self.check_hub_update()
        hub_auto.toggled.connect(set_hub_auto)
        update_content.addWidget(hub_auto, 0, Qt.AlignLeft)
        update_content.addWidget(self.copy_label("Enigma Hub " + HUB_VERSION, "muted"))
        box.addWidget(updates)

        support, support_content = self.section_panel(tr("support"), "support")
        support_content.addWidget(self.copy_label(tr("support_desc"), "body"))
        actions = self.adaptive_row(1050)
        for label, url in (
            (tr("support_email"), "https://github.com/d4rv1n17/Enigma-Hub/issues/new"),
            (tr("open_site"), "https://enigmastudioo.com"),
        ):
            button = QPushButton(label, objectName="secondary")
            button.clicked.connect(lambda checked=False, link=url: webbrowser.open(link))
            actions.addWidget(button)
        support_content.addLayout(actions)
        diagnostics = QPushButton(self.wc("diagnostics"), objectName="secondary")
        diagnostics.setIcon(ui_icon("shield"))
        diagnostics.clicked.connect(self.export_diagnostics)
        support_content.addWidget(diagnostics, 0, Qt.AlignLeft)
        support_content.addWidget(self.copy_label(self.wc("diagnostics_note"), "muted"))
        box.addWidget(support)
        storage, storage_content = self.section_panel(self.wc("cache"), "folder")
        storage_content.addWidget(self.copy_label(self.wc("cache_note"), "body"))
        clear = QPushButton(self.wc("cache"), objectName="secondary")
        clear.clicked.connect(self.clear_downloads)
        storage_content.addWidget(clear, 0, Qt.AlignLeft)
        box.addWidget(storage)
        box.addStretch()
        return self.scroll(page)

    def clear_downloads(self):
        if self.product_busy():
            self.status_message(tr("running"))
            return
        dialog, content = self.dialog_panel(self.wc("cache"), self.wc("cache_note"), "folder")
        self.dialog_actions(dialog, content, self.wc("cache"), cancel=True)
        if self.present_dialog(dialog) != QDialog.Accepted:
            return
        try:
            folder = APPDATA / "downloads"
            reject_reparse(folder)
            count = 0
            for file in folder.glob("*"):
                if file.is_file() and file.suffix in (".exe", ".part"):
                    reject_reparse(file)
                    file.unlink()
                    count += 1
            self.status_message(self.wc("success") + f" · {count}")
        except (OSError, ValueError) as error:
            self.notify(tr("failed"), str(error))

    def export_diagnostics(self):
        picker = QFileDialog(self, self.wc("diagnostics"), str(Path.home() / "EnigmaHub-diagnostics.json"))
        picker.setOption(QFileDialog.DontUseNativeDialog)
        picker.setAcceptMode(QFileDialog.AcceptSave)
        picker.setNameFilter("JSON (*.json)")
        picker.setDefaultSuffix("json")
        dark_caption(picker)
        if picker.exec_() == QDialog.Accepted and picker.selectedFiles():
            try:
                report = {"hub": HUB_VERSION, "python": sys.version.split()[0], "platform": sys.platform, "language": Hub.lang, "installed_versions": self.state["installed"], "recent_operations": self.state["history"][-30:]}
                Path(picker.selectedFiles()[0]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                self.status_message(self.wc("success"))
            except OSError as error:
                self.notify(tr("failed"), str(error))
        picker.deleteLater()

    def show_activity(self):
        dialog, content = self.dialog_panel(self.wc("activity"), icon="activity")
        dialog.resize(650, 520)
        panel = QWidget()
        timeline = QVBoxLayout(panel)
        timeline.setContentsMargins(0, 0, 0, 0)
        timeline.setSpacing(10)
        if self.product_busy():
            timeline.addWidget(self.copy_label(tr("running"), "eyebrow"))
        for item in reversed(self.state["history"][-50:]):
            card, row = self.section_panel("", None)
            header = QHBoxLayout()
            header.addWidget(self.icon_label("check" if item["status"] == "success" else "info", "#DCC574"))
            header.addWidget(self.copy_label(item["name"], "releaseName"), 1)
            row.addLayout(header)
            action = workspace_copy(item["action"], Hub.lang) if item["action"] in ("launch", "install", "update", "remove", "verify") else item["action"]
            row.addWidget(self.copy_label(action + " · " + self.wc("success" if item["status"] == "success" else "failed") + " · " + item["date"].replace("T", " ")[:16], "muted"))
            timeline.addWidget(card)
        if not self.state["history"]:
            timeline.addWidget(self.copy_label(self.wc("activity_empty"), "body"))
        timeline.addStretch()
        content.addWidget(self.scroll(panel), 1)
        self.dialog_actions(dialog, content, "OK")
        self.present_dialog(dialog)

    def locate_product(self, product):
        if self.product_busy():
            return
        selected = self.pick_path(self.wc("locate"), self.state["paths"][product["id"]], False)
        if not selected:
            return
        path = Path(selected)
        if path.name.casefold() != product["exe"].casefold():
            self.notify(tr("failed"), product["exe"])
            return
        self.state["paths"][product["id"]] = str(path.parent)
        self.state["installed"].pop(product["id"], None)
        self.state["hashes"].pop(product["id"], None)
        self.save_state()
        self.refresh_product_states()

    def open_product_folder(self, product):
        folder = Path(self.state["paths"][product["id"]])
        if folder.is_dir():
            try:
                os.startfile(folder)
            except OSError as error:
                self.notify(tr("failed"), str(error))

    def is_installed(self, product):
        folder=Path(self.state["paths"][product["id"]]); exe=folder/product["exe"]
        if exe.is_file(): return True
        try:
            import winreg
            key=r"Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaCube" if product["id"]=="cube" else r"Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaDisk"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as handle:
                location,_=winreg.QueryValueEx(handle,"InstallLocation")
            if (Path(location)/product["exe"]).is_file():
                self.state["paths"][product["id"]]=location
                return True
        except (ImportError,OSError): pass
        return False

    def refresh_product_states(self):
        for p in PRODUCTS:
            installed=self.is_installed(p)
            for badge in getattr(self,"product_badges",{}).get(p["id"], []):
                badge.setText(tr("installed") if installed else tr("not_installed"))
            if p["id"] in getattr(self,"product_cards",{}):
                for main,version in self.product_cards[p["id"]]:
                    main.setText(tr("launch") if installed else tr("install"))
                    main.setIcon(ui_icon("play" if installed else "download", "#171717"))
                    displayed = self.state["installed"].get(p["id"], "—") if installed else self.latest_versions.get(p["id"], p["version"])
                    version.setText(f"{tr('release')}  {displayed}  ·  Windows")
            for control in self.product_controls.get(p["id"], []):
                control.setVisible(installed)
            for label in self.path_labels.get(p["id"], []):
                self.set_path_text(label, self.state["paths"][p["id"]])
        self.refresh_game_states(); self.refresh_library()

    def refresh_game_states(self):
        for g in GAMES:
            installed = self.find_game_exe(g)
            for button in self.game_launch_buttons.get(g["id"], []):
                button.setVisible(bool(installed))
            for status in self.game_states.get(g["id"], []):
                status.setText(tr("installed") if installed else tr("not_installed"))

    def refresh_library(self):
        if not hasattr(self, "library_area"):
            return
        apps = [product for product in PRODUCTS if self.is_installed(product)]
        games = [game for game in GAMES if self.find_game_exe(game)]
        def included(item, kind):
            return (self.library_filter in ("all", kind) or self.library_filter == "favorites" and item["id"] in self.state["favorites"]) and self.library_query.casefold().strip() in " ".join((item["name"], *meta(item))).casefold()
        def order(item):
            return self.state["recent"].get(item["id"], "") if self.library_sort == "recent" else item["name"].casefold()
        groups = tuple((key, sorted([item for item in entries if included(item, key)], key=order, reverse=self.library_sort == "recent")) for key, entries in (("apps", apps), ("games", games)))
        signature = (Hub.lang, self.library_filter, self.library_query, self.library_sort, tuple(self.state["favorites"]), tuple((item["id"], self.state["installed"].get(item["id"]), self.state["recent"].get(item["id"]), self.state["paths"].get(item["id"])) for _, entries in groups for item in entries))
        if signature == getattr(self, "library_signature", None):
            return
        self.library_signature = signature
        self.library_heading.setText(self.wc("quick"))
        for badge, (key, entries) in zip(self.library_counts, (("apps", apps), ("games", games))):
            badge.setText(f"{len(entries)}  {tr(key)}")
        while self.library_area.count():
            widget = self.library_area.takeAt(0).widget()
            if widget:
                widget.hide()
                widget.deleteLater()
        for key, entries in groups:
            if not entries:
                continue
            self.library_area.addWidget(self.copy_label(tr(key), "section"))
            for item in entries:
                self.library_area.addWidget(self.library_entry(item, is_app=key == "apps"))
        if not any(entries for _, entries in groups):
            if not apps and not games:
                panel, content = self.section_panel(self.wc("connect"), "library")
                content.addWidget(self.copy_label(tr("no_products"), "body"))
                for product in PRODUCTS:
                    row = self.adaptive_row(1020)
                    row.addWidget(self.asset_image(product["id"] + ".png", 35))
                    row.addWidget(self.copy_label(product["name"], "releaseName"), 1)
                    locate = QPushButton(self.wc("locate"), objectName="secondary")
                    locate.setIcon(ui_icon("search"))
                    locate.clicked.connect(lambda checked=False, p=product: self.locate_product(p))
                    row.addWidget(locate)
                    content.addLayout(row)
                self.library_area.addWidget(panel)
            else:
                self.library_area.addWidget(self.copy_label(self.wc("no_results"), "body"))
            explore = QPushButton(tr("explore"), objectName="primary")
            explore.setIcon(ui_icon("catalog", "#141414"))
            explore.clicked.connect(lambda: self.navigate(1))
            self.library_area.addWidget(explore, 0, Qt.AlignLeft)

    def library_entry(self, item, is_app):
        tile = QFrame(objectName="libraryEntry")
        row = self.adaptive_row(980, tile)
        row.setContentsMargins(12, 12, 14, 12)
        row.setSpacing(14)
        art = Cover(item["id"] + "-surface.svg", 100, item["id"] + ".png") if is_app else Cover(item["id"] + "-cover.webp", 100)
        art.setFixedWidth(132)
        row.addWidget(art, 0, Qt.AlignTop)
        info = QVBoxLayout()
        info.setSpacing(5)
        info.addWidget(self.copy_label(item["name"], "productTitle"))
        subtitle, description = meta(item)
        info.addWidget(self.copy_label(subtitle, "eyebrow"))
        info.addWidget(self.copy_label(description, "body"))
        recent = self.state["recent"].get(item["id"])
        if recent:
            info.addWidget(self.copy_label(self.wc("recent") + " · " + recent.replace("T", " ")[:16], "muted"))
        if is_app:
            version = self.state["installed"].get(item["id"], "—")
            info.addWidget(self.copy_label(f"{tr('release')}  {version}  ·  Windows", "muted"))
        row.addLayout(info, 1)
        actions = QVBoxLayout()
        favorite = self.favorite_button(item)
        actions.addWidget(favorite, 0, Qt.AlignRight)
        launch = QPushButton(tr("launch"), objectName="primary")
        launch.setIcon(ui_icon("play", "#141414"))
        launch_action = self.launch_product if is_app else self.launch_game
        launch.clicked.connect(lambda: launch_action(item))
        actions.addWidget(launch)
        details = QPushButton(tr("details"), objectName="secondary")
        details.setIcon(ui_icon("info"))
        detail_action = self.show_product_detail if is_app else self.show_game_detail
        details.clicked.connect(lambda: detail_action(item))
        actions.addWidget(details)
        row.addLayout(actions)
        return tile

    def stop_page_animation(self):
        for transition in self.stack.findChildren(PageTransition):
            transition.timer.stop()
            transition.hide()
            transition.deleteLater()

    def fade_page(self, page, outgoing=None):
        self.stop_page_animation()
        if self.state.get("motion", True) and page is not None and page.isVisible():
            PageTransition(self.stack, outgoing if outgoing is not None else QPixmap())

    def navigate(self,index,animate=True):
        self.stop_page_animation()
        previous = self.stack.currentWidget()
        outgoing = None
        if animate and self.state.get("motion", True) and previous and previous.isVisible() and index != self.stack.currentIndex():
            outgoing = self.stack.grab()
        self.stack.setCurrentIndex(index)
        sections = ("overview", "catalog", "library", "news", "settings")
        self.top_title.setText(tr(sections[index if index < len(sections) else 1]))
        buttons = self.nav_buttons + [self.nav_settings]
        for i, (button, icon) in enumerate(zip(buttons, ("home", "catalog", "library", "news", "settings"))):
            active = i == index or (index >= 5 and i == 1)
            button.setObjectName("navactive" if active else "nav")
            button.setIcon(ui_icon(icon, "#FFD200" if active else "#BCBCBC"))
            button.style().unpolish(button)
            button.style().polish(button)
        if index == 3 and isinstance(self.stack.currentWidget(), QScrollArea):
            self.stack.currentWidget().verticalScrollBar().setValue(0)
        if outgoing is not None:
            self.fade_page(self.stack.currentWidget(), outgoing)
        if index == 3 and not getattr(self, "news_requested", False):
            self.load_news()
        if index in (0, 1, 2, 4) or index >= 5:
            self.refresh_product_states()

    def change_language(self, code):
        if not code or code==Hub.lang:return
        if self.product_busy():
            self.status_message(tr("running"))
            return
        index = min(self.stack.currentIndex(), 4)
        self.stop_page_animation()
        old = self.takeCentralWidget()
        self.state["lang"] = code
        Hub.lang = code
        self.save_state()
        self.adaptive_rows = []
        for name in ("path_labels", "product_controls", "product_cards", "product_badges", "detail_pages", "game_detail_pages"):
            setattr(self, name, {})
        self.library_signature = None
        self.catalog_selection = None
        self.library_query, self.library_filter, self.library_sort = "", "all", "recent"
        self.build_shell()
        self.pages = [self.page_home(), self.page_catalog(), self.page_library(), self.page_news(), self.page_settings()]
        for page in self.pages:
            self.stack.addWidget(page)
        self.navigate(index, animate=False)
        old.deleteLater()

    def product_busy(self):
        return self.closing or any(isinstance(worker, ProductWorker) and worker.isRunning() for worker in self.workers)

    def choose_install_folder(self,product):
        if self.product_busy():
            return
        if self.is_installed(product):self.notify(tr("installation"),tr("folder_installed"));return
        chosen = self.pick_path(tr("choose_title"), self.state["paths"][product["id"]], directory=True)
        if chosen:
            target = Path(chosen)
            if target.name.casefold() != product["folder"].casefold():
                target /= product["folder"]
            self.state["paths"][product["id"]]=str(target); self.save_state()
            self.refresh_product_states()

    def primary_product_action(self,product):
        if self.product_busy():
            return
        if self.is_installed(product):self.launch_product(product)
        else:self.start_task(product,"install")

    def launch_product(self,product):
        exe=Path(self.state["paths"][product["id"]])/product["exe"]
        if not exe.is_file():self.notify(product["name"],tr("unsupported"));return
        try:
            subprocess.Popen([str(exe)],cwd=str(exe.parent))
            self.record_activity(product, "launch")
        except OSError as error:self.notify(tr("failed"),str(error))

    def start_task(self,product,action):
        if self.product_busy():
            return
        if action=="update" and not self.is_installed(product):action="install"
        for cards in getattr(self,"product_cards",{}).values():
            for button,_ in cards:button.setEnabled(False)
        for controls in getattr(self,"product_controls",{}).values():
            for button in controls:button.setEnabled(False)
        self.task_strip = QWidget(objectName="taskStrip")
        progress_row = QHBoxLayout(self.task_strip)
        progress_row.setContentsMargins(7, 3, 9, 3)
        self.task_label = QLabel(product["name"], objectName="taskLabel")
        progress_row.addWidget(self.task_label)
        self.progress = QProgressBar()
        progress_row.addWidget(self.progress)
        self.progress.setFixedWidth(130)
        self.progress.setValue(0)
        self.progress_motion = QPropertyAnimation(self.progress, b"value", self.progress)
        self.progress_motion.setDuration(180)
        self.progress_motion.setEasingCurve(QEasingCurve.OutCubic)
        self.progress.setAccessibleName(tr("running"))
        self.statusBar().addPermanentWidget(self.task_strip)
        self.status_message(tr("running"))
        worker=ProductWorker(product,action,self.state["paths"][product["id"]],self.state["hashes"].get(product["id"])); worker.progress.connect(self.task_progress); worker.done.connect(lambda a,v,e,d,p=product:self.task_done(p,a,v,e,d)); worker.finished.connect(lambda:self.workers.remove(worker) if worker in self.workers else None); self.workers.append(worker); worker.start()

    def status_message(self,message):self.statusBar().showMessage(message,5000)

    def task_progress(self,value,message):
        self.task_strip.setToolTip(message)
        if not self.state.get("motion", True):
            self.progress.setValue(value)
            self.status_message(message)
            return
        self.progress_motion.stop()
        self.progress_motion.setStartValue(self.progress.value())
        self.progress_motion.setEndValue(value)
        self.progress_motion.start()
        self.status_message(message)

    def task_done(self,product,action,version,error,directory):
        for cards in getattr(self,"product_cards",{}).values():
            for button,_ in cards:button.setEnabled(True)
        for controls in getattr(self,"product_controls",{}).values():
            for button in controls:button.setEnabled(True)
        self.progress_motion.stop()
        self.statusBar().removeWidget(self.task_strip)
        self.task_strip.deleteLater()
        if error:
            self.record_activity(product, action, "failed")
            self.notify(tr("failed"),error); self.status_message(error[:150]); return
        self.record_activity(product, action)
        if action == "verify":
            self.notify(tr("integrity_title"), self.wc("verified"))
            return
        if action=="remove":
            self.state["hashes"].pop(product["id"], None)
            self.state["installed"].pop(product["id"],None); remove_shortcuts(product["name"]); self.notify(product["name"],tr("uninstalled").format(name=product["name"]))
        else:
            executable = Path(directory) / product["exe"]
            if executable.is_file():
                self.state["hashes"][product["id"]] = digest_file(executable)
            self.state["paths"][product["id"]]=directory; self.state["installed"][product["id"]]=version; self.notify(product["name"],(tr("updated_ok").format(name=product["name"],version=version) if action=="update" else tr("installed_ok").format(name=product["name"]))+"\n\n"+tr("integrity"))
        self.save_state(); self.refresh_product_states()

    def confirm_remove(self,product):
        if self.product_busy():
            return
        dialog, layout = self.dialog_panel(tr("remove"), tr("uninstall_confirm").format(name=product["name"]))
        self.dialog_actions(dialog, layout, tr("remove"), cancel=True)
        if self.present_dialog(dialog) == QDialog.Accepted:
            self.start_task(product, "remove")

    def show_product_detail(self,product):
        cache=getattr(self,"detail_pages",{})
        if product["id"] in cache:
            self.navigate(cache[product["id"]]); return
        page,box=self.page_base(tr("apps"),product["name"],meta(product)[0])
        back=QPushButton("←     "+tr("catalog")); back.clicked.connect(lambda:self.navigate(1)); box.addWidget(back,0,Qt.AlignLeft)
        tagline,description=meta(product); hero=QFrame(objectName="hero"); row=self.adaptive_row(1170, hero); row.setContentsMargins(25,23,25,23)
        art = Cover(product["id"] + "-surface.svg", 190, product["id"] + ".png")
        row.addWidget(art, 1)
        info = QVBoxLayout()
        info.addWidget(self.copy_label(description, "subtitle"))
        version = self.copy_label("", "muted")
        info.addWidget(version)
        path = self.path_label(self.state["paths"][product["id"]])
        self.path_labels.setdefault(product["id"], []).append(path)
        info.addWidget(path)
        actions = self.adaptive_row(1190)
        primary = QPushButton(objectName="primary")
        primary.clicked.connect(lambda: self.primary_product_action(product))
        actions.addWidget(primary)
        folder = QPushButton(tr("choose_folder"), objectName="secondary")
        folder.clicked.connect(lambda: self.choose_install_folder(product))
        actions.addWidget(folder)
        update = QPushButton(tr("update"), objectName="secondary")
        update.clicked.connect(lambda: self.start_task(product, "update"))
        actions.addWidget(update)
        remove = QPushButton(tr("remove"), objectName="danger")
        remove.clicked.connect(lambda: self.confirm_remove(product))
        actions.addWidget(remove)
        self.product_cards.setdefault(product["id"], []).append((primary, version))
        self.product_controls.setdefault(product["id"], []).extend((update, remove))
        info.addLayout(actions)
        row.addLayout(info, 1)
        box.addWidget(hero)
        self.refresh_product_states()
        management, tools = self.section_panel(tr("installation"), "settings")
        for label, icon, callback in ((self.wc("locate"), "search", lambda: self.locate_product(product)), (self.wc("open_folder"), "folder", lambda: self.open_product_folder(product)), (self.wc("verify"), "shield", lambda: self.start_task(product, "verify"))):
            button = QPushButton(label, objectName="secondary")
            button.setIcon(ui_icon(icon))
            button.clicked.connect(callback)
            tools.addWidget(button, 0, Qt.AlignLeft)
        tools.addWidget(self.copy_label(self.wc("verify_note"), "muted"))
        box.addWidget(management)
        guide = QTextBrowser()
        guide.setOpenExternalLinks(True)
        guide.setMinimumHeight(360)
        guide.setStyleSheet("QTextBrowser { background: #191919; color: #ededed; border: 1px solid #363636; padding: 16px; }")
        guide_path = ROOT / "assets" / (product["id"] + "." + Hub.lang + ".md")
        if not guide_path.is_file():
            guide_path = ROOT / "assets" / (product["id"] + ".en.md")
        if guide_path.is_file():
            content = guide_path.read_text(encoding="utf-8")
            if hasattr(guide, "setMarkdown"):
                guide.setMarkdown(content)
            else:
                guide.setPlainText(content)
            box.addWidget(guide)
        release=QPushButton(tr("open_release")); release.clicked.connect(lambda:webbrowser.open(product["url"])); box.addWidget(release,0,Qt.AlignLeft); box.addStretch()
        index=self.stack.addWidget(self.scroll(page)); cache[product["id"]]=index; self.detail_pages=cache; self.navigate(index)

    def configure_game(self, game):
        cfg = self.state["games"].get(game["id"], {})
        dialog, layout = self.dialog_panel(tr("setup_game"), game["name"])
        executable = QLineEdit(cfg.get("exe", ""))
        app_id = QLineEdit(cfg.get("steam_app_id", ""))
        store = QLineEdit(cfg.get("store_url", ""))
        store.setPlaceholderText(GAME_PAGES[game["id"]])
        for key, field in (("game_exe", executable), ("steam_id", app_id), ("store_url", store)):
            label = self.copy_label(tr(key), "body")
            label.setBuddy(field)
            layout.addWidget(label)
            row = QHBoxLayout()
            row.addWidget(field, 1)
            if field is executable:
                browse = QPushButton("…", objectName="secondary")
                browse.setAccessibleName(tr("game_exe"))
                def browse_exe():
                    path = self.pick_path(tr("game_exe"), executable.text(), directory=False, parent=dialog)
                    if path:
                        executable.setText(path)
                browse.clicked.connect(browse_exe)
                row.addWidget(browse)
            layout.addLayout(row)
        problem = self.copy_label(FORM_ERROR[Hub.lang], "eyebrow")
        problem.hide()
        layout.addWidget(problem)
        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton(tr("cancel"), objectName="secondary")
        cancel.clicked.connect(dialog.reject)
        row.addWidget(cancel)
        save = QPushButton(tr("save"), objectName="primary")
        save.setDefault(True)
        row.addWidget(save)
        layout.addLayout(row)

        def save_game():
            path, steam_id, url = (field.text().strip() for field in (executable, app_id, store))
            try:
                address = urlsplit(url)
                bad_url = bool(url) and (address.scheme not in ("https", "http") or not address.hostname)
                bad_path = bool(path) and (Path(path).suffix.lower() != ".exe" or not Path(path).is_file())
            except (OSError, ValueError):
                problem.show()
                return
            if bad_url or bad_path or (steam_id and (not steam_id.isascii() or not steam_id.isdecimal())):
                problem.show()
                return
            self.state["games"][game["id"]] = {"exe": path, "steam_app_id": steam_id, "store_url": url}
            self.save_state()
            dialog.accept()

        save.clicked.connect(save_game)
        if self.present_dialog(dialog) == QDialog.Accepted:
            self.refresh_product_states()

    def find_game_exe(self,game):
        cfg=self.state["games"].get(game["id"],{}); custom=Path(cfg["exe"]) if cfg.get("exe") else None
        if custom and custom.is_file():return custom
        appid=str(cfg.get("steam_app_id",""))
        if not appid.isdigit():return None
        roots=[Path(os.environ.get("ProgramFiles(x86)",r"C:\Program Files (x86)"))/"Steam",Path(os.environ.get("ProgramFiles",r"C:\Program Files"))/"Steam"]
        import re
        for root in list(roots):
            try:
                raw=re.findall(r'"path"\s+"([^"]+)"',(root/"steamapps/libraryfolders.vdf").read_text(encoding="utf-8",errors="ignore")); roots.extend(Path(x.replace("\\\\","\\")) for x in raw)
            except OSError:pass
        for root in roots:
            manifest=root/"steamapps"/f"appmanifest_{appid}.acf"
            try:
                data=manifest.read_text(encoding="utf-8",errors="ignore"); install=re.search(r'"installdir"\s+"([^"]+)"',data)
                if install and (root/"steamapps/common"/install.group(1)).is_dir():return manifest
            except OSError:pass
        return None

    def launch_game(self,game):
        result = self.find_game_exe(game)
        if result is None:
            self.notify( game["name"], tr("game_not_found"))
            return
        try:
            if result.suffix.lower() == ".acf":
                appid = self.state["games"][game["id"]]["steam_app_id"]
                os.startfile("steam://run/" + appid)
            else:
                subprocess.Popen([str(result)], cwd=str(result.parent))
            self.record_activity(game, "launch")
        except OSError as error:
            self.notify( tr("failed"), str(error))

    def game_link_label(self, game):
        configured = self.state["games"].get(game["id"], {}).get("store_url")
        if configured or game["id"] == "twins-hunt":
            return STORE_LABELS[Hub.lang]
        return GAME_PAGE_LABELS[Hub.lang]

    def open_game_store(self, game):
        configured = self.state["games"].get(game["id"], {}).get("store_url")
        webbrowser.open(configured or GAME_PAGES[game["id"]])

    def show_game_detail(self,game):
        cache=getattr(self,"game_detail_pages",{})
        if game["id"] in cache:self.navigate(cache[game["id"]]);return
        genre,description=meta(game); page,box=self.page_base(genre,game["name"],"")
        back=QPushButton("←     "+tr("catalog")); back.clicked.connect(lambda:self.navigate(1)); box.addWidget(back,0,Qt.AlignLeft)
        hero=QFrame(objectName="hero"); row=self.adaptive_row(1170, hero); row.setContentsMargins(25,23,25,23)
        poster = Cover(game["id"] + "-cover.webp", 220)
        poster.setMinimumWidth(230)
        row.addWidget(poster, 1)
        info=QVBoxLayout(); info.addWidget(self.copy_label(description,"subtitle"))
        status=QLabel("",objectName="muted"); self.game_states.setdefault(game["id"], []).append(status); info.addWidget(status)
        actions=self.adaptive_row(1180); launch=QPushButton(tr("launch"),objectName="primary"); launch.clicked.connect(lambda:self.launch_game(game)); self.game_launch_buttons.setdefault(game["id"], []).append(launch); actions.addWidget(launch); buy=QPushButton(self.game_link_label(game),objectName="secondary"); buy.clicked.connect(lambda:self.open_game_store(game)); actions.addWidget(buy); info.addLayout(actions)
        configure=QPushButton(tr("setup_game")); configure.clicked.connect(lambda:self.configure_game(game)); info.addWidget(configure,0,Qt.AlignLeft); info.addStretch(); row.addLayout(info,1); box.addWidget(hero)
        explain=QLabel(tr("external"),objectName="body"); explain.setWordWrap(True); box.addWidget(explain); box.addStretch()
        index=self.stack.addWidget(self.scroll(page)); cache[game["id"]]=index; self.game_detail_pages=cache; self.navigate(index)

    def load_news(self):
        if self.closing or any(isinstance(worker, NewsWorker) for worker in self.workers):
            return
        self.news_requested = True
        self.news_refresh.setEnabled(False)
        self.news_status.setText(tr("loading_news"))
        self.news_status.show()
        worker = NewsWorker()
        worker.loaded.connect(self.finish_news_refresh)
        self.workers.append(worker)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        worker.start()

    def finish_news_refresh(self, refreshed, errors):
        if self.closing:
            return
        if refreshed:
            items = [item for item in self.news_items if item["name"] not in refreshed]
            for releases in refreshed.values():
                items.extend(releases)
            self.news_items = sorted(items, key=lambda item: item["date"], reverse=True)
            try:
                APPDATA.mkdir(parents=True, exist_ok=True)
                cache = APPDATA / "news-cache.json"
                temporary = cache.with_suffix(".tmp")
                temporary.write_text(json.dumps(self.news_items, ensure_ascii=False), encoding="utf-8")
                temporary.replace(cache)
            except OSError as error:
                print(f"News cache: {error}", file=sys.stderr)
        self.show_news(self.news_items)
        self.news_status.setToolTip(chr(10).join(errors))
        if errors:
            self.news_status.setText(NEWS_OFFLINE[Hub.lang])
            self.news_status.show()
            for error in errors:
                print(f"News refresh: {error}", file=sys.stderr)

    @staticmethod
    def news_excerpt(markdown):
        import re
        document = QTextDocument()
        paragraphs = []
        for block in re.split(r"\n\s*\n", markdown.replace("\r\n", "\n")):
            lines = [line.strip() for line in block.splitlines()]
            lines = [line for line in lines if line and not line.startswith(("#", "|", "![", "<", "```"))]
            if not lines or any(line.startswith(("- ", "* ")) for line in lines):
                continue
            document.setMarkdown(" ".join(lines), QTextDocument.MarkdownNoHTML)
            copy = " ".join(document.toPlainText().split())
            if copy:
                paragraphs.append(copy)
            if len(paragraphs) == 2:
                break
        copy = " ".join(paragraphs)
        return copy if len(copy) <= 245 else copy[:245].rsplit(" ", 1)[0] + "…"

    def show_news(self, items):
        if self.closing:
            return
        self.news_refresh.setEnabled(True)
        self.news_status.setText(tr("no_news"))
        self.news_status.setVisible(not items)
        while self.news_content.count():
            child = self.news_content.takeAt(0).widget()
            if child:
                child.deleteLater()
        for index, item in enumerate(items):
            featured = index == 0
            tile = QFrame(objectName="newsLead" if featured else "newsStory")
            row = QHBoxLayout(tile)
            row.setContentsMargins(17, 15, 17, 15)
            row.setSpacing(13)
            product = next((product for product in PRODUCTS if product["name"] == item["name"]), None)
            thumbnail = self.asset_image(product["id"] + ".png", 52 if featured else 38) if product else self.icon_label("news", "#FFD200", 29)
            row.addWidget(thumbnail, 0, Qt.AlignTop)
            story = QVBoxLayout()
            story.setSpacing(7)
            info = QHBoxLayout()
            info.addWidget(self.copy_label(item["name"], "eyebrow"), 1)
            info.addWidget(self.copy_label(item["date"], "muted"), 0, Qt.AlignRight)
            story.addLayout(info)
            story.addWidget(self.copy_label(item["title"], "newsTitle" if featured else "productTitle"))
            excerpt = self.news_excerpt(item["body"])
            if excerpt:
                story.addWidget(self.copy_label(excerpt, "body"))
            link = QPushButton(self.wc("read"), objectName="secondary")
            link.setIcon(ui_icon("news"))
            link.clicked.connect(lambda checked=False, article=item: self.read_article(article))
            story.addWidget(link, 0, Qt.AlignLeft)
            row.addLayout(story, 1)
            self.news_content.addWidget(tile)

    def read_article(self, item):
        dialog, content = self.dialog_panel(item["title"], item["name"] + " · " + item["date"], "news")
        dialog.resize(680, 560)
        body = QTextBrowser()
        document = body.document()
        document.setDefaultStyleSheet("body { color:#DFDFDF; font-size:14px; } h1,h2,h3 { color:#F4DA7D; } a { color:#E8CA69; } td,th { padding:6px; }")
        document.setMarkdown(item["body"], QTextDocument.MarkdownNoHTML)
        body.setOpenLinks(False)
        body.anchorClicked.connect(lambda url: webbrowser.open(url.toString()) if url.scheme() in ("https", "http") else None)
        content.addWidget(body, 1)
        release = QPushButton(tr("open_release"), objectName="secondary")
        release.setIcon(ui_icon("external"))
        release.clicked.connect(lambda: webbrowser.open(item["url"]))
        content.addWidget(release, 0, Qt.AlignLeft)
        self.dialog_actions(dialog, content, "OK")
        self.present_dialog(dialog)

    def check_hub_update(self, manual=False):
        if self.closing or not getattr(sys, "frozen", False):
            return
        if not manual and not self.state.get("hub_auto_update", True):
            return
        if any(isinstance(worker, HubUpdateWorker) and worker.isRunning() for worker in self.workers):
            return
        worker = HubUpdateWorker(APPDATA / "hub-updates")
        worker.completed.connect(lambda release, error: self.hub_update_ready(release, error, manual))
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.workers.append(worker)
        worker.start()

    def hub_update_ready(self, release, error, manual=False):
        if self.closing:
            return
        if error:
            print("Hub update: " + error, file=sys.stderr)
            if manual:
                self.notify(tr("updates"), error)
            return
        if not release:
            if manual:
                self.notify(tr("updates"), "Enigma Hub " + HUB_VERSION + " · " + tr("up_to_date"))
            return
        self.hub_release = release
        if not hasattr(self, "hub_update_button"):
            self.hub_update_button = QPushButton(objectName="primary")
            self.hub_update_button.setIcon(ui_icon("updates", "#141414"))
            self.hub_update_button.clicked.connect(self.restart_for_hub_update)
            self.statusBar().addPermanentWidget(self.hub_update_button)
        labels = {"en":"Restart to update Hub", "ru":"Перезапустить и обновить Hub", "ro":"Repornește și actualizează Hub", "de":"Hub neu starten und aktualisieren", "es":"Reiniciar y actualizar Hub", "fr":"Redémarrer et mettre à jour Hub"}
        self.hub_update_button.setText(labels[Hub.lang] + " · " + release["version"])

    def restart_for_hub_update(self):
        if self.product_busy():
            self.status_message(tr("running"))
            return
        try:
            release = self.hub_release
            if not release or digest_file(release["path"]) != release["sha256"]:
                raise ValueError("Downloaded Hub update is missing or damaged.")
            target = Path(sys.executable).parent
            if not (target / ".enigma-hub-install.json").is_file():
                self.notify(tr("updates"), "Install Enigma Hub with EnigmaHubSetup.exe to enable automatic installation.")
                return
            subprocess.Popen([
                release["path"], "--quiet", "--dir", str(target),
                "--wait-pid", str(os.getpid()), "--launch",
            ], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, ValueError) as error:
            self.notify(tr("updates"), str(error))
            return
        self.close()

    def check_updates(self,silent=False):
        if not silent:
            self.check_hub_update(manual=True)
        if self.closing or any(isinstance(worker, UpdateCheckWorker) for worker in self.workers):
            return
        self.status_message(tr("checking")); worker=UpdateCheckWorker(); worker.checked.connect(lambda versions,error,s=silent:self.show_update_results(versions,error,s)); self.workers.append(worker); worker.finished.connect(lambda:self.workers.remove(worker) if worker in self.workers else None); worker.start()

    def show_update_results(self, versions, error, silent=False):
        if self.closing:
            return
        self.latest_versions.update(versions)
        self.refresh_product_states()
        rows = []
        for product in PRODUCTS:
            latest = versions.get(product["id"])
            installed = self.is_installed(product)
            current = self.state["installed"].get(product["id"], "—") if installed else None
            update = bool(current and latest and self.version_tuple(latest) > self.version_tuple(current))
            rows.append((product, current, latest, update))
        if silent:
            if any(update for _, _, _, update in rows):
                self.status_message(tr("update_available"))
            return
        if error and not versions and not silent:
            self.notify(tr("updates"), error)
            return

        dialog, content = self.dialog_panel(tr("updates"), icon="updates")
        installed_label, latest_label, failed_label, done_label = UPDATE_COPY[Hub.lang]
        selected = []
        for product, current, latest, update in rows:
            card = QFrame(objectName="releaseReady" if update else "releaseCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 12, 15, 12)
            header = QHBoxLayout()
            header.addWidget(self.asset_image(product["id"] + ".png", 38))
            summary = QVBoxLayout()
            summary.setSpacing(4)
            summary.addWidget(self.copy_label(product["name"], "releaseName"))
            versions_line = f"{installed_label}: {current or '—'}   /   {latest_label}: {latest or '—'}"
            summary.addWidget(self.copy_label(versions_line, "muted"))
            header.addLayout(summary, 1)
            if update:
                action = QPushButton(tr("update"), objectName="primary")
                action.setIcon(ui_icon("download", "#141414"))

                def select(checked=False, item=product):
                    selected.append(item)
                    dialog.accept()

                action.clicked.connect(select)
                header.addWidget(action)
            card_layout.addLayout(header)
            status_key = "update_available" if update else ("up_to_date" if current else "not_installed_state")
            status = QHBoxLayout()
            icon = "download" if update else ("check" if latest and current else "info")
            status.addWidget(self.icon_label(icon, "#FFD200" if update else "#BFBFBF", 16))
            status.addWidget(self.copy_label(tr(status_key) if latest else failed_label, "eyebrow" if update else "releaseStatus"), 1)
            card_layout.addLayout(status)
            content.addWidget(card)
        if error:
            content.addWidget(self.copy_label(error, "muted"))
        trust = QHBoxLayout()
        trust.addWidget(self.icon_label("shield"))
        trust.addWidget(self.copy_label(tr("integrity_title") + " · SHA-256", "muted"), 1)
        content.addLayout(trust)
        self.dialog_actions(dialog, content, done_label)
        if self.present_dialog(dialog) == QDialog.Accepted and selected:
            self.start_task(selected[0], "update")

    @staticmethod
    def version_tuple(value):
        import re
        parts = tuple(int(part) for part in re.findall(r"\d+", str(value))[:4])
        return parts + (0,) * (4 - len(parts)) if parts else ()

    def toggle_auto_check(self):
        self.state["auto_check"]=not self.state.get("auto_check",True); self.save_state(); self.auto_check_button.setChecked(self.state["auto_check"])

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.arrange_rows()
        if hasattr(self, "stack"):
            self.stop_page_animation()

    def closeEvent(self, event):
        if self.product_busy() and not self.closing:
            self.status_message(tr("running"))
            event.ignore()
            return
        self.closing = True
        if any(worker.isRunning() for worker in self.workers):
            event.ignore()
            self.centralWidget().setEnabled(False)
            QTimer.singleShot(150, self.close)
            return
        super().closeEvent(event)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setApplicationName("Enigma Hub")
    app.setOrganizationName("Enigma Studio")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    identity = "EnigmaHub-" + hashlib.sha256(str(APPDATA).casefold().encode()).hexdigest()[:16]
    client = QLocalSocket()
    client.connectToServer(identity)
    if client.waitForConnected(250):
        client.write(b"activate")
        client.flush()
        client.waitForBytesWritten(250)
        client.disconnectFromServer()
        return 0
    server = QLocalServer(app)
    server.setSocketOptions(QLocalServer.UserAccessOption)
    if not server.listen(identity):
        return 1
    screen = app.screenAt(QCursor.pos()) or app.primaryScreen()
    window = Hub()
    def activate_existing():
        connection = server.nextPendingConnection()
        if connection:
            connection.disconnectFromServer()
            connection.deleteLater()
        window.showNormal()
        window.raise_()
        window.activateWindow()
    server.newConnection.connect(activate_existing)
    available = screen.availableGeometry()
    window.resize(min(1040, available.width() - 24), min(625, available.height() - 46))
    dark_caption(window)
    center_on_screen(window, screen)
    motion = window.state.get("motion", True)
    intro = StartupIntro(Hub.lang, motion)
    center_on_screen(intro, screen)
    if window.state["intro"]:
        intro.show()

    def open_window():
        window.show()
        center_on_screen(window, screen)
        intro.close()
        if motion:
            window.fade_page(window.stack.currentWidget())

    QTimer.singleShot((1900 if motion else 450) if window.state["intro"] else 0, open_window)
    return app.exec_()


if __name__ == "__main__":
    log_path = APPDATA / "startup.log"
    try:
        APPDATA.mkdir(parents=True, exist_ok=True)
        crash_log = log_path.open("w", encoding="utf-8", buffering=1)
    except OSError:
        crash_log = None

    if crash_log is not None:
        print(f"Enigma Hub starting with Python {sys.version.split()[0]}", file=crash_log)
        faulthandler.enable(crash_log)

        def log_exception(kind, value, frames):
            traceback.print_exception(kind, value, frames, file=crash_log)
            sys.__excepthook__(kind, value, frames)

        sys.excepthook = log_exception
    sys.exit(main())
