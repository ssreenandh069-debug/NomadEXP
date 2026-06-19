import sys
import os
import subprocess
from PySide6.QtWidgets import QApplication , QDialog , QListWidgetItem , QFileIconProvider , QMenu , QGraphicsDropShadowEffect , QSystemTrayIcon , QStyle
from PySide6.QtCore import Qt, Signal, QObject, QThread , QFileInfo , QTimer , QPropertyAnimation, QEasingCurve, QSize , QEvent 
from PySide6.QtGui import QColor , QAction
import keyboard
import ctypes
import datetime

from quick_search_ui import Ui_quick_search

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

""" searcher dll variables """
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

class ScoredListItem(QListWidgetItem):
    def __init__(self, file_name, full_path, score):
        super().__init__(file_name)
        self.setToolTip(full_path)
        self.score = score
    # sorts items based on extensions
    def __lt__(self, other):
        return self.score > other.score

class SearchWorker(QThread):
    search_finished_signal = Signal(int, list) 

    def __init__(self, search_id, target_name, ext_filter):
        super().__init__()
        self.search_id = search_id
        self.target_name = target_name
        self.ext_filter = ext_filter

    def run(self):
        found_files = []

        def on_found(file_name, full_path):
            found_files.append((file_name, full_path))

        c_callback_ptr = check_callbacl(on_found)
        
        scanner_dll.RunSearch(self.target_name, self.ext_filter, c_callback_ptr)

        # 5. When C is completely done, emit the massive list to the UI exactly once
        self.search_finished_signal.emit(self.search_id, found_files)

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
        
        # Create the animation engine
        self.anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim.setDuration(200) # 200ms smooth transition
        
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

class QuickSearchWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_quick_search()
        self.ui.setupUi(self)
        self.setMinimumWidth(850)
        self.ui.right_panel.setMinimumWidth(300)
        self.ui.right_panel.setMaximumWidth(350)
        #to hide the window frame to make it sleek
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        #hide program when closed
        self.ui.exit_program.clicked.connect(self.hide)
        #hotkey trigger
        self.hotkeypressed = HotkeyPressed()
        self.hotkeypressed.toggle_signal.connect(self.window_toggle)
        self.ui.result_list.setSortingEnabled(True)
        #add hotkey
        keyboard.add_hotkey('alt+space',self.triggerHotkey)
        #animations
        self.dropdown_anim = QPropertyAnimation(self, b"size")
        self.dropdown_anim.setDuration(250) # 250ms animation
        self.dropdown_anim.setEasingCurve(QEasingCurve.OutExpo)
        self.icon_pop = HoverPopEffect(self.ui.icon, hover_blur=40, base_blur=0)
        self.btn_pop = HoverPopEffect(self.ui.open_file, hover_blur=25, base_blur=5)
        #lazy loading things and delta caching
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.background_sync)
        self.sync_timer.start(2000)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(scanner_dll.BuildIndex)
        self.refresh_timer.start(900000)
        self.pending_results = []
        self.results_loaded = 0 
        scrollbar = self.ui.result_list.verticalScrollBar()
        scrollbar.valueChanged.connect(self.check_scroll)
        #search trigger when user presses enter
        self.ui.bottom_split.hide()
        
        #debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.start_search)
        
        # resert timer when text
        self.ui.search_bar_2.textChanged.connect(self.on_text_changed)

        self.search_thread = None
        self.current_search_id = 0

        self.ui.result_list.itemClicked.connect(self.show_details)
        self.ui.open_file.clicked.connect(self.open_file)
        self.ui.open_file_location.clicked.connect(self.open_file_location)

        filter_buttons = [self.ui.All, self.ui.Apps, self.ui.pdfs, self.ui.docs, self.ui.Images, self.ui.Folders]
        for btn in filter_buttons:
            btn.clicked.connect(self.force_search)

        # Right click actions
        self.ui.result_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.result_list.customContextMenuRequested.connect(self.show_context_menu)

    def background_sync(self):
        delta_count = scanner_dll.SyncDeltas()
        
        if delta_count >= 500:
            print(f"Delta cache reached {delta_count} files. Triggering master rebuild to clear RAM.")
            scanner_dll.BuildIndex()

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
        # So that enter key doesnt kill the dialogue
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
            if self.search_thread and self.search_thread.isRunning():
                self.search_thread.wait() 
            scanner_dll.BuildIndex()
            self.ui.title.setText("Cache Updated!")
            self.start_search()
        else:
            super().keyPressEvent(event)    

    def force_search(self):
        if self.ui.search_bar_2.text().strip():
            self.start_search()

    def show_context_menu(self, position):
        item = self.ui.result_list.itemAt(position)
        if not item: return
        
        full_path = item.toolTip()
        
        # Create a sleek dark-themed menu
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background-color: #1A1A1A; color: white; border: 1px solid #333333; border-radius: 4px; }
            QMenu::item { padding: 8px 25px; }
            QMenu::item:selected { background-color: #0078D4; }
        """)
        
        # Add Actions
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
            self.search_thread.wait() 
        raw_query = self.ui.search_bar_2.text().strip()
        if not raw_query:
            return

        if self.ui.bottom_split.isHidden():
            self.ui.bottom_split.show()
            self.dropdown_anim.setStartValue(QSize(self.width(), 70)) # Collapsed height (approx)
            self.dropdown_anim.setEndValue(QSize(self.width(), 550))  # Expanded height (approx)
            self.dropdown_anim.start()
        self.ui.result_list.clear() 

        self.required_path = ""
        self.actual_query = raw_query.lower()
        
        if "\\" in raw_query or ":/" in raw_query:
            # Split by the last slash
            if "\\" in raw_query:
                parts = raw_query.rsplit("\\", 1)
            else:
                parts = raw_query.rsplit("/", 1)
                
            self.required_path = parts[0].lower().replace('/', '\\')
            self.actual_query = parts[1].lower()

        extension_filter = ""
        if hasattr(self.ui, 'pdfs') and self.ui.pdfs.isChecked(): extension_filter = ".pdf"
        elif hasattr(self.ui, 'Apps') and self.ui.Apps.isChecked(): extension_filter = ".exe"

        self.current_search_id += 1
        self.search_thread = SearchWorker(self.current_search_id, self.actual_query, extension_filter)
        self.search_thread.search_finished_signal.connect(self.process_batch_results)
        self.search_thread.start()
    
    def on_text_changed(self, text):
        scanner_dll.CancelSearch()
        self.current_search_id += 1
        # iIf nothing is in the text box
        if text.strip() == "":
            self.ui.result_list.clear()
            self.ui.title.setText("")
            self.ui.icon.clear()
            
            self.dropdown_anim.setStartValue(QSize(self.width(), self.height()))
            self.dropdown_anim.setEndValue(QSize(self.width(), 70)) # Shrink back to search bar
            self.dropdown_anim.start()
            
            QTimer.singleShot(250, self.ui.bottom_split.hide)
        else:
            self.search_timer.start(200)

    def process_batch_results(self, search_id, results_list):
        if search_id != self.current_search_id: return
        
        scored_results = []
        
        # --- THE HARD BAN LIST ---
        # Folders that we NEVER want to see in our search results
        hard_ban_dirs = [
            '\\appdata\\roaming\\microsoft\\windows\\recent\\', 
            '\\windows\\prefetch\\', 
            '\\windows\\winsxs\\', 
            '\\windows\\temp\\',
            '\\$recycle.bin\\'
        ]
        
        for file_name, full_path in results_list:
            path_lower = full_path.lower()
            
            # 1. Skip banned directories instantly
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
            
            # 3. Base Match Scoring
            score = 0
            if self.actual_query == name_no_ext: score += 100000
            elif name_no_ext.startswith(self.actual_query): score += 50000
            elif self.actual_query in name_no_ext: score += 5000
            else: continue
                
            # 4. Depth Penalty
            depth = full_path.count('\\')
            score -= (depth * 2000)

            # 5. Folder Filter
            is_folder_filter = hasattr(self.ui, 'Folders') and self.ui.Folders.isChecked()
            if is_folder_filter and not os.path.isdir(full_path): continue
                
            # 6. Type and Location Boosts
            if ext == '.exe': score += 500000
            elif ext == '.lnk': score += 400000
            elif ext == '': score -= 50000 
                
            if "desktop" in path_lower or "downloads" in path_lower: score += 15000
            
            scored_results.append( (score, file_name, full_path) )

        scored_results.sort(reverse=True, key=lambda x: x[0])
        
        if len(scored_results) == 0:
            self.ui.title.setText("No results found")
            self.ui.icon.clear()
            self.ui.location_value.setText("")
            self.ui.date_modified_value.setText("")
            self.ui.size_value.setText("")
            
        self.pending_results = scored_results
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
            file_info = QFileInfo(full_path)
            item.setIcon(QFileIconProvider().icon(file_info))
            self.ui.result_list.addItem(item)
            
            items_drawn += 1

        if self.ui.result_list.count() > 0 and self.ui.result_list.currentRow() == -1:
            top_item = self.ui.result_list.item(0)
            self.ui.result_list.setCurrentItem(top_item)
            self.show_details(top_item)

    def check_scroll(self, value):
        scrollbar = self.ui.result_list.verticalScrollBar()
        if value == scrollbar.maximum():
            self.load_more_results()

    def show_details(self, item):
        if not item: return 

        file_name = item.text()
        full_path = item.toolTip()
        
        self.ui.title.setText(file_name) 
        
        file_info = QFileInfo(full_path)
        icon_provider = QFileIconProvider()
        icon = icon_provider.icon(file_info)
        
        base_pixmap = icon.pixmap(32, 32)
        
        stretched_pixmap = base_pixmap.scaled(
            64, 64, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.ui.icon.setPixmap(stretched_pixmap)
        self.ui.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        try:
            parent_dir = os.path.dirname(full_path)
            
            metrics = self.ui.location_value.fontMetrics()
            elided_path = metrics.elidedText(parent_dir, Qt.TextElideMode.ElideLeft, 180)
            
            self.ui.location_value.setText(elided_path) 
            self.ui.location_value.setToolTip(parent_dir)

            timestamp = os.path.getmtime(full_path)
            date_obj = datetime.datetime.fromtimestamp(timestamp)
            formatted_date = date_obj.strftime("%b %d, %Y") 
            self.ui.date_modified_value.setText(formatted_date)

            size_bytes = os.path.getsize(full_path)
            if size_bytes >= 1073741824: 
                size_str = f"{size_bytes / 1073741824:.2f} GB"
            elif size_bytes >= 1048576:  
                size_str = f"{size_bytes / 1048576:.2f} MB"
            else:                        
                size_str = f"{size_bytes / 1024:.0f} KB"
            
            self.ui.size_value.setText(size_str)
            
        except Exception as e:
            self.ui.location_value.setText("Unknown")
            self.ui.date_modified_value.setText("Unknown")
            self.ui.size_value.setText("Unknown")

    def open_file(self):
        item = self.ui.result_list.currentItem()
        if item:
            full_path = item.toolTip()
            if os.path.exists(full_path):
                #open up the file 
                os.startfile(full_path) 
                self.hide()

    def open_file_location(self):
        item = self.ui.result_list.currentItem()
        if item:
            full_path = item.toolTip()
            if os.path.exists(full_path):
                #open windows explorer for now
                subprocess.Popen(f'explorer /select,"{full_path}"')
                self.hide()



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
    
    # Force the app to stay alive even when our search window is hidden
    app.setQuitOnLastWindowClosed(False) 
    scanner_dll.BuildIndex()
    window = QuickSearchWindow()
    
    tray_icon = QSystemTrayIcon(app)
    standard_icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    tray_icon.setIcon(standard_icon)
    
    tray_menu = QMenu()
    
    show_action = QAction("Open Search (Alt+Space)", app)
    show_action.triggered.connect(window.window_toggle)
    tray_menu.addAction(show_action)
    
    tray_menu.addSeparator()
    
    quit_action = QAction("Quit Nomad Search", app)
    quit_action.triggered.connect(app.quit)
    tray_menu.addAction(quit_action)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    
    tray_icon.showMessage("Nomad Search is Active", "Press Alt+Space to search your PC at lightning speed.", QSystemTrayIcon.MessageIcon.Information, 3000)

    sys.exit(app.exec())