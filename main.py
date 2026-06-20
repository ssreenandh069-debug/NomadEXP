import sys
import os
import subprocess
import threading
from PySide6.QtWidgets import QApplication , QDialog , QListWidgetItem , QFileIconProvider , QMenu , QGraphicsDropShadowEffect , QSystemTrayIcon , QStyle
from PySide6.QtCore import Qt, Signal, QObject, QThread , QFileInfo , QTimer , QPropertyAnimation, QEasingCurve, QSize , QEvent 
from PySide6.QtGui import QColor , QAction
import keyboard
import ctypes
import datetime
import json
import time
import re
from rapidfuzz import fuzz, process as fuzz_process
from quick_search_ui import Ui_quick_search
from nomad_ai import NomadAI
import string

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_ai_scan_targets():
    sys_drive = os.environ.get('SystemDrive', 'C:')
    user_profile = os.environ.get('USERPROFILE', '')
    local_appdata = os.environ.get('LOCALAPPDATA', '')
    roaming_appdata = os.environ.get('APPDATA', '')
    
    dirs = [
        os.path.join(user_profile, 'Desktop'),
        os.path.join(user_profile, 'Documents'),
        os.path.join(user_profile, 'Downloads'),
        os.path.join(user_profile, 'Pictures'),
        os.path.join(user_profile, 'Videos'),
        os.path.join(sys_drive, '\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs'),
        os.path.join(sys_drive, '\\Program Files'),
        os.path.join(sys_drive, '\\Program Files (x86)'),
        os.path.join(sys_drive, '\\Games'),
        os.path.join(local_appdata, 'Discord'),
        os.path.join(local_appdata, 'Programs'),
        os.path.join(roaming_appdata, 'Microsoft', 'Windows', 'Start Menu', 'Programs')
    ]
    
    available_drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\") and f"{d}:" != sys_drive]
    common_folders = ['Games', 'SteamLibrary', 'Steam', 'Epic Games', 'Projects', 'Codes', 'Work']
    
    for drive in available_drives:
        for folder in common_folders:
            test_path = os.path.join(drive, folder)
            if os.path.exists(test_path):
                dirs.append(test_path)
                
    exts = [
        '.pdf', '.docx', '.txt', '.xlsx', '.csv', '.md', '.pptx',
        '.py', '.c', '.cpp', '.js', '.html', '.css', '.java', '.go', '.rs', '.sh', '.bat', '.ps1', '.json', '.yaml', '.xml',
        '.exe', '.lnk', '.url', '.app', '.msi',
        '.jpg', '.png', '.mp4', '.gif', '.svg', '.ai', '.psd', '.mp3', '.wav', '.mkv', '.avi',
        '.zip', '.rar', '.7z', '.iso', '.sql', '.db', '.sqlite',
        '.stl', '.obj', '.fbx'
    ]
    return dirs, exts

scanner_dll = ctypes.CDLL('./nomadexp.dll')

check_callbacl = ctypes.CFUNCTYPE(None , ctypes.c_wchar_p , ctypes.c_wchar_p)
scanner_dll.BuildIndex.argtypes = []
scanner_dll.BuildIndex.restype = None
scanner_dll.RunSearch.argtypes = [ctypes.c_wchar_p , ctypes.c_wchar_p , check_callbacl]
scanner_dll.RunSearch.restype = None
scanner_dll.CancelSearch.argtypes = []
scanner_dll.CancelSearch.restype = None
scanner_dll.SyncDeltas.argtypes = []
scanner_dll.SyncDeltas.restype = ctypes.c_int

_no_cancel = threading.Event()

class ScoredListItem(QListWidgetItem):
    def __init__(self, file_name, full_path, score):
        super().__init__(file_name)
        self.setToolTip(full_path)
        self.score = score

    def __lt__(self, other):
        return self.score > other.score

class SearchWorker(QThread):
    search_finished_signal = Signal(int, list, list)

    def __init__(self, search_id, target_name, ext_filter, ai_core, actual_query, cancel_event):
        super().__init__()
        self.search_id = search_id
        self.target_name = target_name
        self.ext_filter = ext_filter
        self.ai_core = ai_core
        self.actual_query = actual_query
        self.cancel_event = cancel_event
        self.found_files = []

    def run(self):
        def on_found(file_name, full_path):
            if os.path.exists(full_path):
                self.found_files.append((file_name, full_path))

        c_callback_ptr = check_callbacl(on_found)
        scanner_dll.RunSearch(self.target_name, self.ext_filter, c_callback_ptr)

        ai_results = []
        if self.ai_core is not None and len(self.actual_query) > 2 and not self.cancel_event.is_set():
            try:
                with self.ai_core.ai_lock:
                    paths_snapshot = list(self.ai_core.paths)

                if not self.cancel_event.is_set() and paths_snapshot:
                    basenames = [os.path.basename(p) for p in paths_snapshot]
                    matches = fuzz_process.extract(
                        self.actual_query, basenames,
                        scorer=fuzz.WRatio,
                        limit=30,
                        score_cutoff=65
                    )
                    for _match_str, score, idx in matches:
                        if self.cancel_event.is_set():
                            break
                        ai_results.append(('typo', score, paths_snapshot[idx]))

                if not self.cancel_event.is_set():
                    semantic = self.ai_core.search(self.actual_query, top_results=5)
                    for score, path in semantic:
                        if score > 0.25:
                            ai_results.append(('ai', score, path))
            except Exception:
                pass

        self.search_finished_signal.emit(self.search_id, self.found_files, ai_results)


class FileDetailWorker(QThread):
    details_ready = Signal(str, str, str)

    def __init__(self, full_path):
        super().__init__()
        self.full_path = full_path

    def run(self):
        try:
            timestamp = os.path.getmtime(self.full_path)
            date_str = datetime.datetime.fromtimestamp(timestamp).strftime("%b %d, %Y")
            size_bytes = os.path.getsize(self.full_path)
            if size_bytes >= 1073741824:
                size_str = f"{size_bytes / 1073741824:.2f} GB"
            elif size_bytes >= 1048576:
                size_str = f"{size_bytes / 1048576:.2f} MB"
            else:
                size_str = f"{size_bytes / 1024:.0f} KB"
            self.details_ready.emit(date_str, size_str, self.full_path)
        except Exception:
            self.details_ready.emit("Unknown", "Unknown", self.full_path)

class SyncWorker(QThread):
    delta_ready = Signal(int)
    def run(self):
        count = scanner_dll.SyncDeltas()
        self.delta_ready.emit(count)

class HotkeyPressed(QObject):
    toggle_signal = Signal()

class HoverPopEffect(QObject):
    def __init__(self, widget, hover_blur=30, base_blur=0):
        super().__init__(widget)
        self.widget = widget
        self.base_blur = base_blur
        self.hover_blur = hover_blur
        
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(self.base_blur)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.shadow.setOffset(0, 4)
        self.widget.setGraphicsEffect(self.shadow)
        
        self.anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim.setDuration(200)
        
        self.widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.widget:
            if event.type() == QEvent.Type.Enter:
                self.anim.setStartValue(self.shadow.blurRadius())
                self.anim.setEndValue(self.hover_blur)
                self.anim.start()
            elif event.type() == QEvent.Type.Leave:
                self.anim.setStartValue(self.shadow.blurRadius())
                self.anim.setEndValue(self.base_blur)
                self.anim.start()
        return super().eventFilter(obj, event)

class AILoader(QThread):
    ai_loaded = Signal(object)

    def run(self):
        ai = NomadAI()
        ai.load_database()
        print(f"AI Engine Online. Memories: {len(ai.paths)}")
        self.ai_loaded.emit(ai)


class AIHarvestWorker(QThread):
    harvest_done = Signal()

    def __init__(self, ai_core):
        super().__init__()
        self.ai_core = ai_core

    def run(self):
        print("AI Memory empty — starting background first-time harvest...")
        target_dirs, allowed_exts = get_ai_scan_targets()
        self.ai_core.update_database(target_dirs, allowed_exts)
        self.harvest_done.emit()


class AIUpdaterThread(QThread):
    def __init__(self, ai_core, target_dirs, allowed_exts):
        super().__init__()
        self.ai_core = ai_core
        self.target_dirs = target_dirs
        self.allowed_exts = allowed_exts

    def run(self):
        self.ai_core.update_database(self.target_dirs, self.allowed_exts)

class IndexRebuildWorker(QThread):
    def run(self):
        scanner_dll.BuildIndex()

class QuickSearchWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_quick_search()
        self.ui.setupUi(self)
        self.setMinimumWidth(850)
        self.ui.right_panel.setMinimumWidth(300)
        self.ui.right_panel.setMaximumWidth(350)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.ui.exit_program.clicked.connect(self.hide)
        self.hotkeypressed = HotkeyPressed()
        self.hotkeypressed.toggle_signal.connect(self.window_toggle)
        self.ui.result_list.setSortingEnabled(True)
        keyboard.add_hotkey('alt+space',self.triggerHotkey)
        self.dropdown_anim = QPropertyAnimation(self, b"size")
        self.dropdown_anim.setDuration(250)
        self.dropdown_anim.setEasingCurve(QEasingCurve.OutExpo)
        self.icon_pop = HoverPopEffect(self.ui.icon, hover_blur=40, base_blur=0)
        self.btn_pop = HoverPopEffect(self.ui.open_file, hover_blur=25, base_blur=5)
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.background_sync)
        self.sync_timer.start(2000)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.start_rebuild)
        self.refresh_timer.start(900000)
        self.pending_results = []
        self.results_loaded = 0 
        scrollbar = self.ui.result_list.verticalScrollBar()
        scrollbar.valueChanged.connect(self.check_scroll)
        self.ui.bottom_split.hide()
        self.ai_core = None
        self.ai_thread = AILoader()
        self.ai_thread.ai_loaded.connect(self.on_ai_loaded)
        self.ai_thread.start()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.start_search)
        
        self.ui.search_bar_2.textChanged.connect(self.on_text_changed)

        self.search_thread = None
        self.current_search_id = 0
        self._running_threads = []

        self.ui.result_list.itemClicked.connect(self.show_details)
        self.ui.open_file.clicked.connect(self.open_file)
        self.ui.open_file_location.clicked.connect(self.open_file_location)

        filter_buttons = [self.ui.All, self.ui.Apps, self.ui.pdfs, self.ui.docs, self.ui.Images, self.ui.Folders]
        for btn in filter_buttons:
            btn.clicked.connect(self.force_search)

        self.ui.result_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.result_list.customContextMenuRequested.connect(self.show_context_menu)

        self.extension_icon_cache = {}
        self.icon_provider = QFileIconProvider()

    def get_cached_icon(self, full_path):
        ext = os.path.splitext(full_path)[1].lower()
        if ext in ['.exe', '.lnk', '.url', '.ico'] or not ext:
            return self.icon_provider.icon(QFileInfo(full_path))
        
        if ext not in self.extension_icon_cache:
            self.extension_icon_cache[ext] = self.icon_provider.icon(QFileInfo(full_path))
            
        return self.extension_icon_cache[ext]

    def extract_time_intent(self, query):
        temporal_boost = None
        time_threshold_min = 0
        time_threshold_max = float('inf')
        
        now = time.time()
        days_in_sec = 86400
        
        if "today" in query:
            time_threshold_min = now - days_in_sec
            query = query.replace("today", "").strip()
            temporal_boost = "newest"
        elif "yesterday" in query:
            time_threshold_min = now - (2 * days_in_sec)
            time_threshold_max = now - days_in_sec
            query = query.replace("yesterday", "").strip()
            temporal_boost = "newest"
        elif "last week" in query or "past week" in query:
            time_threshold_min = now - (7 * days_in_sec)
            query = query.replace("last week", "").replace("past week", "").strip()
            temporal_boost = "newest"
        elif "last month" in query or "past month" in query:
            time_threshold_min = now - (30 * days_in_sec)
            query = query.replace("last month", "").replace("past month", "").strip()
            temporal_boost = "newest"
        elif "last year" in query or "past year" in query:
            time_threshold_min = now - (365 * days_in_sec)
            query = query.replace("last year", "").replace("past year", "").strip()
            temporal_boost = "newest"
            
        keywords_newest = ["recent", "latest", "new", "newest"]
        keywords_oldest = ["oldest", "old", "earliest"]
        
        words = query.split()
        for kw in keywords_newest:
            if kw in words:
                temporal_boost = "newest"
                query = re.sub(rf'\b{kw}\b', '', query).strip()
                
        for kw in keywords_oldest:
            if kw in words:
                temporal_boost = "oldest"
                query = re.sub(rf'\b{kw}\b', '', query).strip()
                
        query = re.sub(' +', ' ', query)
        return query, temporal_boost, time_threshold_min, time_threshold_max

    def start_rebuild(self):
        if not hasattr(self, 'rebuild_worker') or not self.rebuild_worker.isRunning():
            self.rebuild_worker = IndexRebuildWorker()
            self.rebuild_worker.start()

    def background_sync(self):
        if not hasattr(self, '_sync_worker') or not self._sync_worker.isRunning():
            self._sync_worker = SyncWorker()
            self._sync_worker.delta_ready.connect(self._on_sync_done)
            self._sync_worker.start()

    def _on_sync_done(self, delta_count):
        if delta_count >= 5000:
            print(f"Delta cache reached {delta_count} files. Triggering master rebuild to clear RAM.")
            self.start_rebuild()

    def triggerHotkey(self):
        self.hotkeypressed.toggle_signal.emit()
    
    def window_toggle(self):
        if self.isVisible():
            self.hide()
            scanner_dll.CancelSearch() 
            return
            
        self.showNormal()
        self.activateWindow()
        self.raise_()

        QTimer.singleShot(10, self.ui.search_bar_2.setFocus)
        QTimer.singleShot(10, self.ui.search_bar_2.selectAll)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            event.accept()
            if self.ui.result_list.count() > 0:
                self.open_file()
        elif event.key() == Qt.Key_Down:
            event.accept()
            current_row = self.ui.result_list.currentRow()
            if current_row < self.ui.result_list.count() - 1:
                self.ui.result_list.setCurrentRow(current_row + 1)
                self.show_details(self.ui.result_list.currentItem())
        elif event.key() == Qt.Key_Up:
            event.accept()
            current_row = self.ui.result_list.currentRow()
            if current_row > 0:
                self.ui.result_list.setCurrentRow(current_row - 1)
                self.show_details(self.ui.result_list.currentItem())
        elif event.key() == Qt.Key_F5:
            event.accept()
            self.ui.title.setText("Refreshing Cache...")
            scanner_dll.CancelSearch()
            self.start_rebuild()
            if self.ai_core:
                target_dirs, allowed_exts = get_ai_scan_targets()
                updater_thread = AIUpdaterThread(self.ai_core, target_dirs, allowed_exts)
                self._running_threads.append(updater_thread)
                updater_thread.start()
            self.ui.title.setText("Cache Updated!")
            self.start_search()
        else:
            super().keyPressEvent(event)    

    def load_telemetry(self):
        self.telemetry_file = "user_clicks.json"
        try:
            with open(self.telemetry_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def record_click(self, filepath):
        filepath_lower = filepath.lower()
        if not hasattr(self, 'click_history'):
            self.click_history = self.load_telemetry()
            
        self.click_history[filepath_lower] = self.click_history.get(filepath_lower, 0) + 1
        QTimer.singleShot(0, self._flush_telemetry)

    def _flush_telemetry(self):
        try:
            with open(self.telemetry_file, 'w') as f:
                json.dump(self.click_history, f)
        except Exception:
            pass

    def force_search(self):
        if self.ui.search_bar_2.text().strip():
            self.start_search()

    def show_context_menu(self, position):
        item = self.ui.result_list.itemAt(position)
        if not item: return
        
        full_path = item.toolTip()
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background-color: #1A1A1A; color: white; border: 1px solid #333333; border-radius: 4px; }
            QMenu::item { padding: 8px 25px; }
            QMenu::item:selected { background-color: #0078D4; }
        """)
        
        run_admin_action = menu.addAction("Run as Administrator")
        copy_path_action = menu.addAction("Copy Path")
        open_loc_action = menu.addAction("Open File Location")
        
        action = menu.exec(self.ui.result_list.mapToGlobal(position))
        
        if action == run_admin_action:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", full_path, None, None, 1)
            self.hide()
        elif action == copy_path_action:
            QApplication.clipboard().setText(full_path)
            self.hide()
        elif action == open_loc_action:
            subprocess.Popen(f'explorer /select,"{full_path}"')
            self.hide()

    def start_search(self):
        scanner_dll.CancelSearch()
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.quit()
        raw_query = self.ui.search_bar_2.text().strip()
        if not raw_query:
            return

        stripped_query, self.temporal_boost, self.time_min, self.time_max = self.extract_time_intent(raw_query)

        if self.ui.bottom_split.isHidden():
            self.ui.bottom_split.show()
            self.dropdown_anim.setStartValue(QSize(self.width(), 70))
            self.dropdown_anim.setEndValue(QSize(self.width(), 550))
            self.dropdown_anim.start()
        self.ui.result_list.clear() 

        self.required_path = ""
        self.actual_query = stripped_query.lower()
        if not self.actual_query and self.temporal_boost:
            self.actual_query = raw_query.lower()
            
        if "\\" in self.actual_query or ":/" in self.actual_query:
            if "\\" in self.actual_query:
                parts = self.actual_query.rsplit("\\", 1)
            else:
                parts = self.actual_query.rsplit("/", 1)
                
            self.required_path = parts[0].lower().replace('/', '\\')
            self.actual_query = parts[1].lower()

        extension_filter = ""
        if hasattr(self.ui, 'pdfs') and self.ui.pdfs.isChecked(): extension_filter = ".pdf"
        elif hasattr(self.ui, 'Apps') and self.ui.Apps.isChecked(): extension_filter = ".exe"

        self.current_search_id += 1
        self._running_threads = [t for t in self._running_threads if t.isRunning()]
        
        if self.search_thread and self.search_thread.isRunning():
            self._running_threads.append(self.search_thread)
        
        new_cancel_event = threading.Event()
        
        self.search_thread = SearchWorker(
            self.current_search_id,
            self.actual_query,
            extension_filter,
            self.ai_core,
            self.actual_query,
            new_cancel_event
        )
        self.search_thread.search_finished_signal.connect(self.process_batch_results)
        self.search_thread.start()
    
    def on_text_changed(self, text):
        self.search_timer.stop()
        scanner_dll.CancelSearch()
        
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.cancel_event.set()
            
        self.current_search_id += 1
        if text.strip() == "":
            self.ui.result_list.clear()
            self.ui.title.setText("")
            self.ui.icon.clear()
            
            self.dropdown_anim.setStartValue(QSize(self.width(), self.height()))
            self.dropdown_anim.setEndValue(QSize(self.width(), 70))
            self.dropdown_anim.start()
            
            QTimer.singleShot(250, self.ui.bottom_split.hide)
        else:
            self.search_timer.start(200)

    def process_batch_results(self, search_id, results_list, ai_results):
        if search_id != self.current_search_id: return
        
        scored_results = []
        seen_paths = set()
        
        if not hasattr(self, 'click_history'):
            self.click_history = self.load_telemetry()
        
        hard_ban_dirs = [
            '\\appdata\\roaming\\microsoft\\windows\\recent\\', 
            '\\windows\\prefetch\\', 
            '\\windows\\winsxs\\', 
            '\\windows\\temp\\',
            '\\$recycle.bin\\'
        ]
        
        for file_name, full_path in results_list:
            path_lower =os.path.normpath(full_path).lower()
            
            is_banned = False
            for banned_dir in hard_ban_dirs:
                if banned_dir in path_lower:
                    is_banned = True
                    break
            if is_banned:
                continue

            if self.required_path and self.required_path not in path_lower:
                continue

            name_no_ext, ext = os.path.splitext(file_name.lower())
            
            score = 0
            if self.actual_query == name_no_ext: score += 100000
            elif name_no_ext.startswith(self.actual_query): score += 50000
            elif self.actual_query in file_name.lower(): score += 5000
            else: continue
                
            depth = full_path.count('\\')
            score -= (depth * 2000)

            is_folder_filter = hasattr(self.ui, 'Folders') and self.ui.Folders.isChecked()
            if is_folder_filter and not os.path.isdir(full_path): continue
                
            if ext == '.exe': score += 500000
            elif ext == '.lnk': score += 400000
            elif ext == '': score -= 50000 
                
            if "desktop" in path_lower or "downloads" in path_lower: score += 15000
            
            clicks = self.click_history.get(path_lower, 0)
            score += (clicks * 50000) 
            
            scored_results.append( (score, file_name, full_path) )
            seen_paths.add(path_lower)

        is_folder_filter = hasattr(self.ui, 'Folders') and self.ui.Folders.isChecked()
        is_pdf_filter = hasattr(self.ui, 'pdfs') and self.ui.pdfs.isChecked()
        is_app_filter = hasattr(self.ui, 'Apps') and self.ui.Apps.isChecked()
        is_img_filter = hasattr(self.ui, 'Images') and self.ui.Images.isChecked()
        is_doc_filter = hasattr(self.ui, 'docs') and self.ui.docs.isChecked()

        def passes_ui_filters(path):
            if is_folder_filter and not os.path.isdir(path): return False
            ext = os.path.splitext(path)[1].lower()
            if is_pdf_filter and ext != '.pdf': return False
            if is_app_filter and ext not in ['.exe', '.lnk', '.url']: return False
            if is_img_filter and ext not in ['.jpg', '.jpeg', '.png', '.gif', '.svg']: return False
            if is_doc_filter and ext not in ['.docx', '.txt', '.md', '.csv', '.xlsx']: return False
            return True

        for kind, raw_score, filepath in ai_results:
            filepath_lower = os.path.normpath(filepath).lower()
            if filepath_lower in seen_paths: continue
            if not passes_ui_filters(filepath): continue
            
            file_name_display = os.path.basename(filepath)
            clicks = self.click_history.get(filepath_lower, 0)

            if kind == 'typo':
                mapped_score = int(raw_score * 1000) + (clicks * 50000)
                display_name = file_name_display
            else:
                mapped_score = int(300000 + (raw_score * 200000)) + (clicks * 50000)
                display_name = file_name_display

            scored_results.append((mapped_score, display_name, filepath))
            seen_paths.add(filepath_lower)

        final_results = []
        for score, display_name, filepath in scored_results:
            if self.temporal_boost or self.time_min > 0 or self.time_max < float('inf'):
                try:
                    mtime = os.path.getmtime(filepath)
                except:
                    mtime = 0
                    
                if mtime < self.time_min or mtime > self.time_max:
                    continue
                    
                if self.temporal_boost == "newest":
                    score += int(mtime / 10000)
                elif self.temporal_boost == "oldest":
                    score += int((2000000000 - mtime) / 10000)
                    
            final_results.append((score, display_name, filepath))

        final_results.sort(reverse=True, key=lambda x: x[0])
        
        if len(final_results) == 0:
            self.ui.title.setText("No results found")
            self.ui.icon.clear()
            self.ui.location_value.setText("")
            self.ui.date_modified_value.setText("")
            self.ui.size_value.setText("")
            
        self.pending_results = final_results
        self.results_loaded = 0
        self.load_more_results()

    def load_more_results(self):
        ITEMS_PER_BATCH = 15
        if self.results_loaded >= len(self.pending_results):
            return 
            
        items_drawn = 0
        while items_drawn < ITEMS_PER_BATCH and self.results_loaded < len(self.pending_results):
            score, file_name, full_path = self.pending_results[self.results_loaded]
            self.results_loaded += 1
            
            if not os.path.exists(full_path):
                continue

            item = ScoredListItem(file_name, full_path, score)
            item.setIcon(self.get_cached_icon(full_path))
            self.ui.result_list.addItem(item)
            items_drawn += 1

        if self.ui.result_list.count() > 0 and self.ui.result_list.currentRow() == -1:
            top_item = self.ui.result_list.item(0)
            self.ui.result_list.setCurrentItem(top_item)
            self.show_details(top_item)
        elif self.ui.result_list.count() == 0:
            self.ui.title.setText("No results found")
            self.ui.icon.clear()
            self.ui.location_value.setText("")
            self.ui.date_modified_value.setText("")
            self.ui.size_value.setText("")

    def check_scroll(self, value):
        scrollbar = self.ui.result_list.verticalScrollBar()
        if value == scrollbar.maximum():
            self.load_more_results()

    def show_details(self, item):
        if not item: return 

        file_name = item.text()
        full_path = item.toolTip()
        
        self.ui.title.setText(file_name) 
        
        icon = self.get_cached_icon(full_path)
        base_pixmap = icon.pixmap(32, 32)
        stretched_pixmap = base_pixmap.scaled(
            64, 64, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.ui.icon.setPixmap(stretched_pixmap)
        self.ui.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        parent_dir = os.path.dirname(full_path)
        metrics = self.ui.location_value.fontMetrics()
        elided_path = metrics.elidedText(parent_dir, Qt.TextElideMode.ElideLeft, 180)
        self.ui.location_value.setText(elided_path) 
        self.ui.location_value.setToolTip(parent_dir)

        self.ui.date_modified_value.setText("...")
        self.ui.size_value.setText("...")
        
        if hasattr(self, 'detail_worker') and self.detail_worker.isRunning():
            self._running_threads.append(self.detail_worker)
            
        self.detail_worker = FileDetailWorker(full_path)
        self.detail_worker.details_ready.connect(self._on_details_ready)
        self.detail_worker.start()

    def _on_details_ready(self, date_str, size_str, path_requested):
        item = self.ui.result_list.currentItem()
        if item and item.toolTip() == path_requested:
            self.ui.date_modified_value.setText(date_str)
            self.ui.size_value.setText(size_str)


    def open_file(self):
        item = self.ui.result_list.currentItem()
        if item:
            full_path = item.toolTip()
            if os.path.exists(full_path):
                self.record_click(full_path)
                os.startfile(full_path) 
                self.hide()

    def open_file_location(self):
        item = self.ui.result_list.currentItem()
        if item:
            full_path = item.toolTip()
            if os.path.exists(full_path):
                subprocess.Popen(f'explorer /select,"{full_path}"')
                self.hide()


    def on_ai_loaded(self , loaded_core):
        self.ai_core = loaded_core
        if len(self.ai_core.paths) == 0:
            self.harvest_worker = AIHarvestWorker(self.ai_core)
            self.harvest_worker.start()

def force_shutdown(app_instance):
    scanner_dll.CancelSearch()
    app_instance.quit()
    sys.exit(0)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
        
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) 
    window = QuickSearchWindow()
    window.start_rebuild()
    
    tray_icon = QSystemTrayIcon(app)
    standard_icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    tray_icon.setIcon(standard_icon)
    
    tray_menu = QMenu()
    
    show_action = QAction("Open Search (Alt+Space)", app)
    show_action.triggered.connect(window.window_toggle)
    tray_menu.addAction(show_action)
    
    tray_menu.addSeparator()
    
    quit_action = QAction("Quit Nomad Search", app)
    quit_action.triggered.connect(lambda: force_shutdown(app))
    tray_menu.addAction(quit_action)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    
    tray_icon.showMessage("Nomad Search is Active", "Press Alt+Space to search your PC at lightning speed.", QSystemTrayIcon.MessageIcon.Information, 3000)

    sys.exit(app.exec())