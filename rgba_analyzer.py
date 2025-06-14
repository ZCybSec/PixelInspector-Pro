import sys
import csv
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel, QPushButton,
    QSlider, QLineEdit, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QGroupBox, QGridLayout, QComboBox, QSpinBox,
    QDoubleSpinBox, QStyle
)
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QPen, QColor, QBrush, QFont, QIcon, QPalette,
    QLinearGradient
)
from PySide6.QtCore import Qt, QPoint, QSize, QRectF, QPointF, Signal

class ImageViewer(QGraphicsView):
    pixelSelected = Signal(int, int, QColor)
    pixelHovered = Signal(int, int, QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.pixmap_item = None
        self.image = None
        self.zoom_factor = 1.0
        self.selected_pixel = None
        self.hover_pixel = None
        self.hover_enabled = True
        
        # Setup custom cursor
        self.setCursor(Qt.CrossCursor)
        
    def load_image(self, image_path):
        self.image = QImage(image_path)
        if self.image.isNull():
            return False
            
        self.pixmap = QPixmap.fromImage(self.image)
        if self.pixmap_item:
            self.scene.removeItem(self.pixmap_item)
            
        self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.scene.clear()
        self.scene.addItem(self.pixmap_item)
        self.setSceneRect(QRectF(self.pixmap.rect()))
        
        # Reset view
        self.zoom_factor = 1.0
        self.resetTransform()
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.selected_pixel = None
        self.hover_pixel = None
        return True
        
    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        # Save the scene pos
        old_pos = self.mapToScene(event.position().toPoint())
        
        # Zoom
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
            self.zoom_factor *= zoom_in_factor
        else:
            self.scale(zoom_out_factor, zoom_out_factor)
            self.zoom_factor *= zoom_out_factor
            
        # Get the new position
        new_pos = self.mapToScene(event.position().toPoint())
        
        # Move scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.pixmap_item:
            scene_pos = self.mapToScene(event.pos())
            if self.pixmap_item.contains(scene_pos):
                pixel_pos = self.pixmap_item.mapFromScene(scene_pos)
                x = int(pixel_pos.x())
                y = int(pixel_pos.y())
                
                # Ensure we're within image bounds
                if 0 <= x < self.image.width() and 0 <= y < self.image.height():
                    self.selected_pixel = (x, y)
                    color = self.image.pixelColor(x, y)
                    self.pixelSelected.emit(x, y, color)
                    self.draw_pixel_markers()
                    
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.pixmap_item and self.hover_enabled:
            scene_pos = self.mapToScene(event.pos())
            if self.pixmap_item.contains(scene_pos):
                pixel_pos = self.pixmap_item.mapFromScene(scene_pos)
                x = int(pixel_pos.x())
                y = int(pixel_pos.y())
                
                # Ensure we're within image bounds
                if 0 <= x < self.image.width() and 0 <= y < self.image.height():
                    self.hover_pixel = (x, y)
                    color = self.image.pixelColor(x, y)
                    self.pixelHovered.emit(x, y, color)
                    self.draw_pixel_markers()
                    
        super().mouseMoveEvent(event)
        
    def draw_pixel_markers(self):
        if not self.image:
            return
            
        # Clear previous markers
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem):
                self.scene.removeItem(item)
                
        # Draw selected pixel marker
        if self.selected_pixel:
            x, y = self.selected_pixel
            rect = QRectF(x - 5, y - 5, 10, 10)
            marker = self.scene.addRect(rect, QPen(Qt.white, 1.5), QBrush(Qt.NoBrush))
            marker.setZValue(10)
            
        # Draw hover pixel marker
        if self.hover_pixel:
            x, y = self.hover_pixel
            rect = QRectF(x - 2.5, y - 2.5, 5, 5)
            marker = self.scene.addRect(rect, QPen(Qt.red, 1), QBrush(Qt.NoBrush))
            marker.setZValue(10)
            
    def set_hover_enabled(self, enabled):
        self.hover_enabled = enabled
        if not enabled and self.hover_pixel:
            self.hover_pixel = None
            self.draw_pixel_markers()
            
    def zoom_in(self):
        self.scale(1.25, 1.25)
        self.zoom_factor *= 1.25
        
    def zoom_out(self):
        self.scale(0.8, 0.8)
        self.zoom_factor *= 0.8
        
    def reset_zoom(self):
        self.resetTransform()
        self.zoom_factor = 1.0
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def clear_selection(self):
        self.selected_pixel = None
        self.draw_pixel_markers()


class RGBAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🖤 RGBA Pixel Analyzer - Advanced GUI Tool (Dark Web Themed by Z3X)")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set dark theme palette
        self.set_dark_theme()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create main tab
        self.main_tab = QWidget()
        self.tabs.addTab(self.main_tab, "RGBA Analyzer")
        self.setup_main_tab()
        
        # Create developer tab
        self.dev_tab = QWidget()
        self.tabs.addTab(self.dev_tab, "About Developer")
        self.setup_dev_tab()
        
        # Current image path
        self.image_path = None
        self.selected_pixels = []
        
    def set_dark_theme(self):
        # Create a dark palette
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(15, 15, 25))
        dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(35, 35, 45))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(40, 40, 60))
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.Button, QColor(35, 35, 50))
        dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(100, 150, 220))
        dark_palette.setColor(QPalette.Highlight, QColor(120, 80, 180))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        # Set the palette
        QApplication.setPalette(dark_palette)
        
        # Set style
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                background: #1a1a2a;
            }
            QTabBar::tab {
                background: #252540;
                color: #ddd;
                padding: 8px;
                border: 1px solid #444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3a3a60;
                color: #fff;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QTableWidget {
                background: #1a1a2a;
                gridline-color: #444;
                border: 1px solid #444;
            }
            QHeaderView::section {
                background-color: #252540;
                color: #ddd;
                padding: 4px;
                border: 1px solid #444;
            }
            QPushButton {
                background: #3a3a60;
                color: #fff;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #4a4a80;
            }
            QPushButton:pressed {
                background: #2a2a40;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background: #1a1a2a;
                color: #fff;
                border: 1px solid #555;
                padding: 3px;
                border-radius: 3px;
            }
            QLabel {
                color: #ddd;
            }
        """)
        
    def setup_main_tab(self):
        layout = QHBoxLayout(self.main_tab)
        
        # Left side - Image viewer and controls
        left_panel = QVBoxLayout()
        
        # Image viewer
        self.image_viewer = ImageViewer()
        left_panel.addWidget(self.image_viewer, 3)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Zoom controls
        zoom_group = QGroupBox("Zoom Controls")
        zoom_layout = QHBoxLayout(zoom_group)
        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_in_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        self.zoom_out_btn = QPushButton("Zoom Out")
        self.zoom_out_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        self.zoom_reset_btn = QPushButton("Reset Zoom")
        self.zoom_reset_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        
        zoom_layout.addWidget(self.zoom_in_btn)
        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(self.zoom_reset_btn)
        
        # Selection controls
        select_group = QGroupBox("Selection")
        select_layout = QHBoxLayout(select_group)
        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        
        select_layout.addWidget(self.clear_btn)
        select_layout.addWidget(self.export_btn)
        
        controls_layout.addWidget(zoom_group)
        controls_layout.addWidget(select_group)
        
        left_panel.addLayout(controls_layout)
        
        # Right side - Pixel info and controls
        right_panel = QVBoxLayout()
        
        # Pixel info group
        info_group = QGroupBox("Pixel Information")
        info_layout = QGridLayout(info_group)
        
        self.pos_label = QLabel("Position: N/A")
        self.rgba_label = QLabel("RGBA: N/A")
        self.hex_label = QLabel("Hex: N/A")
        self.color_preview = QLabel()
        self.color_preview.setMinimumSize(80, 80)
        self.color_preview.setStyleSheet("background-color: black; border: 1px solid #555;")
        
        info_layout.addWidget(QLabel("Position:"), 0, 0)
        info_layout.addWidget(self.pos_label, 0, 1)
        info_layout.addWidget(QLabel("RGBA:"), 1, 0)
        info_layout.addWidget(self.rgba_label, 1, 1)
        info_layout.addWidget(QLabel("Hex:"), 2, 0)
        info_layout.addWidget(self.hex_label, 2, 1)
        info_layout.addWidget(self.color_preview, 0, 2, 3, 1)
        
        # Manual selection
        manual_group = QGroupBox("Manual Selection")
        manual_layout = QGridLayout(manual_group)
        
        manual_layout.addWidget(QLabel("X:"), 0, 0)
        self.x_input = QSpinBox()
        self.x_input.setRange(0, 10000)
        manual_layout.addWidget(self.x_input, 0, 1)
        
        manual_layout.addWidget(QLabel("Y:"), 1, 0)
        self.y_input = QSpinBox()
        self.y_input.setRange(0, 10000)
        manual_layout.addWidget(self.y_input, 1, 1)
        
        self.select_btn = QPushButton("Select Pixel")
        manual_layout.addWidget(self.select_btn, 2, 0, 1, 2)
        
        # Filters
        filter_group = QGroupBox("Pixel Filters")
        filter_layout = QGridLayout(filter_group)
        
        filter_layout.addWidget(QLabel("R:"), 0, 0)
        self.r_filter = QSpinBox()
        self.r_filter.setRange(0, 255)
        self.r_filter.setValue(255)
        filter_layout.addWidget(self.r_filter, 0, 1)
        self.r_check = QCheckBox("Enable")
        self.r_check.setChecked(False)
        filter_layout.addWidget(self.r_check, 0, 2)
        
        filter_layout.addWidget(QLabel("G:"), 1, 0)
        self.g_filter = QSpinBox()
        self.g_filter.setRange(0, 255)
        self.g_filter.setValue(255)
        filter_layout.addWidget(self.g_filter, 1, 1)
        self.g_check = QCheckBox("Enable")
        self.g_check.setChecked(False)
        filter_layout.addWidget(self.g_check, 1, 2)
        
        filter_layout.addWidget(QLabel("B:"), 2, 0)
        self.b_filter = QSpinBox()
        self.b_filter.setRange(0, 255)
        self.b_filter.setValue(255)
        filter_layout.addWidget(self.b_filter, 2, 1)
        self.b_check = QCheckBox("Enable")
        self.b_check.setChecked(False)
        filter_layout.addWidget(self.b_check, 2, 2)
        
        filter_layout.addWidget(QLabel("A:"), 3, 0)
        self.a_filter = QSpinBox()
        self.a_filter.setRange(0, 255)
        self.a_filter.setValue(255)
        filter_layout.addWidget(self.a_filter, 3, 1)
        self.a_check = QCheckBox("Enable")
        self.a_check.setChecked(False)
        filter_layout.addWidget(self.a_check, 3, 2)
        
        self.apply_filter_btn = QPushButton("Apply Filter")
        filter_layout.addWidget(self.apply_filter_btn, 4, 0, 1, 3)
        
        # Selected pixels table
        self.pixels_table = QTableWidget()
        self.pixels_table.setColumnCount(6)
        self.pixels_table.setHorizontalHeaderLabels(["X", "Y", "R", "G", "B", "A"])
        self.pixels_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Add groups to right panel
        right_panel.addWidget(info_group)
        right_panel.addWidget(manual_group)
        right_panel.addWidget(filter_group)
        right_panel.addWidget(QLabel("Selected Pixels:"))
        right_panel.addWidget(self.pixels_table, 1)
        
        # Add left and right panels to main layout
        layout.addLayout(left_panel, 3)
        layout.addLayout(right_panel, 1)
        
        # Connect signals
        self.image_viewer.pixelSelected.connect(self.handle_pixel_selected)
        self.image_viewer.pixelHovered.connect(self.handle_pixel_hover)
        self.zoom_in_btn.clicked.connect(self.image_viewer.zoom_in)
        self.zoom_out_btn.clicked.connect(self.image_viewer.zoom_out)
        self.zoom_reset_btn.clicked.connect(self.image_viewer.reset_zoom)
        self.clear_btn.clicked.connect(self.clear_all)
        self.export_btn.clicked.connect(self.export_to_csv)
        self.select_btn.clicked.connect(self.select_manual_pixel)
        self.apply_filter_btn.clicked.connect(self.apply_filters)
        
        # Create menu bar
        self.create_menu()
        
    def create_menu(self):
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        open_action = file_menu.addAction("Open Image")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_image)
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menu_bar.addMenu("View")
        
        hover_action = view_menu.addAction("Enable Hover Tracking")
        hover_action.setCheckable(True)
        hover_action.setChecked(True)
        hover_action.toggled.connect(self.image_viewer.set_hover_enabled)
        
    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if file_path:
            if self.image_viewer.load_image(file_path):
                self.image_path = file_path
                self.setWindowTitle(f"🖤 RGBA Pixel Analyzer - {file_path}")
                self.clear_all()
            else:
                QMessageBox.critical(self, "Error", "Failed to load image")
                
    def handle_pixel_hover(self, x, y, color):
        self.pos_label.setText(f"Position: ({x}, {y})")
        self.rgba_label.setText(f"RGBA: ({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})")
        self.hex_label.setText(f"Hex: {color.name()}")
        
        # Update color preview
        self.color_preview.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #555;"
        )
        
    def handle_pixel_selected(self, x, y, color):
        # Add to selected pixels
        self.selected_pixels.append({
            "x": x,
            "y": y,
            "r": color.red(),
            "g": color.green(),
            "b": color.blue(),
            "a": color.alpha(),
            "color": color
        })
        
        # Update table
        self.update_pixels_table()
        
    def select_manual_pixel(self):
        if not self.image_viewer.image:
            return
            
        x = self.x_input.value()
        y = self.y_input.value()
        
        # Validate coordinates
        if x >= self.image_viewer.image.width() or y >= self.image_viewer.image.height():
            QMessageBox.warning(self, "Invalid Coordinates", "The specified coordinates are outside the image bounds")
            return
            
        # Simulate selection
        color = self.image_viewer.image.pixelColor(x, y)
        self.handle_pixel_selected(x, y, color)
        
        # Set as selected in viewer
        self.image_viewer.selected_pixel = (x, y)
        self.image_viewer.draw_pixel_markers()
        
    def update_pixels_table(self):
        self.pixels_table.setRowCount(len(self.selected_pixels))
        
        for row, pixel in enumerate(self.selected_pixels):
            self.pixels_table.setItem(row, 0, QTableWidgetItem(str(pixel['x'])))
            self.pixels_table.setItem(row, 1, QTableWidgetItem(str(pixel['y'])))
            self.pixels_table.setItem(row, 2, QTableWidgetItem(str(pixel['r'])))
            self.pixels_table.setItem(row, 3, QTableWidgetItem(str(pixel['g'])))
            self.pixels_table.setItem(row, 4, QTableWidgetItem(str(pixel['b'])))
            self.pixels_table.setItem(row, 5, QTableWidgetItem(str(pixel['a'])))
            
            # Set background color
            for col in range(6):
                item = self.pixels_table.item(row, col)
                item.setBackground(pixel['color'])
                
    def apply_filters(self):
        if not self.selected_pixels:
            return
            
        # Get filter values
        r_val = self.r_filter.value() if self.r_check.isChecked() else None
        g_val = self.g_filter.value() if self.g_check.isChecked() else None
        b_val = self.b_filter.value() if self.b_check.isChecked() else None
        a_val = self.a_filter.value() if self.a_check.isChecked() else None
        
        # Filter selected pixels
        filtered_pixels = []
        for pixel in self.selected_pixels:
            if r_val is not None and pixel['r'] != r_val:
                continue
            if g_val is not None and pixel['g'] != g_val:
                continue
            if b_val is not None and pixel['b'] != b_val:
                continue
            if a_val is not None and pixel['a'] != a_val:
                continue
            filtered_pixels.append(pixel)
            
        # Update selected pixels
        self.selected_pixels = filtered_pixels
        self.update_pixels_table()
        
    def clear_all(self):
        self.selected_pixels = []
        self.update_pixels_table()
        self.image_viewer.clear_selection()
        self.pos_label.setText("Position: N/A")
        self.rgba_label.setText("RGBA: N/A")
        self.hex_label.setText("Hex: N/A")
        self.color_preview.setStyleSheet("background-color: black; border: 1px solid #555;")
        
    def export_to_csv(self):
        if not self.selected_pixels:
            QMessageBox.warning(self, "No Data", "There are no pixels to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            "",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['X', 'Y', 'R', 'G', 'B', 'A', 'Hex'])
                    for pixel in self.selected_pixels:
                        hex_color = pixel['color'].name()
                        writer.writerow([
                            pixel['x'], pixel['y'], 
                            pixel['r'], pixel['g'], pixel['b'], pixel['a'],
                            hex_color
                        ])
                QMessageBox.information(self, "Success", "Data exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")
                
    def setup_dev_tab(self):
        layout = QVBoxLayout(self.dev_tab)
        layout.setAlignment(Qt.AlignCenter)
        
        # Developer info group
        dev_group = QGroupBox("About Developer")
        dev_layout = QVBoxLayout(dev_group)
        
        # Title
        title = QLabel("Z3X - RGBA Pixel Analyzer")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #a070ff;")
        
        # Developer info
        dev_info = QLabel("""
        <div style='text-align: center;'>
            <p><b>Developer:</b> Zaid Hijazi</p>
            <p><b>Alias:</b> Z3X</p>
            <p><b>Specialization:</b> Image Processing & Computer Vision</p>
            <br>
            <p>This tool was developed to provide professional-grade pixel analysis for designers, engineers, and data scientists.</p>
            <p>The dark web theme was carefully crafted to enhance user experience during extended analysis sessions.</p>
            <p>All rights reserved © 2023</p>
        </div>
        """)
        dev_info.setAlignment(Qt.AlignCenter)
        dev_info.setStyleSheet("font-size: 14px;")
        
        # Features list
        features = QLabel("""
        <div style='text-align: center;'>
            <h3>Key Features:</h3>
            <p>• High-resolution image support (PNG, JPG, BMP, TIFF)</p>
            <p>• Dynamic zoom with mouse wheel or buttons</p>
            <p>• Click-based pixel selection</p>
            <p>• Manual coordinate input</p>
            <p>• Real-time hover tracking</p>
            <p>• RGBA filtering</p>
            <p>• Visual pixel highlighting</p>
            <p>• Export to CSV</p>
        </div>
        """)
        features.setAlignment(Qt.AlignCenter)
        
        dev_layout.addWidget(title)
        dev_layout.addWidget(dev_info)
        dev_layout.addWidget(features)
        
        layout.addWidget(dev_group)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create main window
    window = RGBAnalyzer()
    window.show()
    
    sys.exit(app.exec())
