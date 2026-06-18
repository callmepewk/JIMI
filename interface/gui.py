import sys
import os
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTextEdit, QLineEdit, QPushButton, QSystemTrayIcon, 
                             QMenu, QAction)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import pyqtSignal, QObject, Qt

# Conexão nativa com a esteira de automações do JIMI
from core.automation import jimi_core

logger = logging.getLogger("JIMI.GUI")


class JimiSignals(QObject):
    """Canal neural de comunicação para injetar textos na interface de qualquer parte do sistema."""
    update_text_signal = pyqtSignal(str)


# Instância global de sinais para que o voice_jimi.py ou o web_server.py possam atualizar a tela
ui_signals = JimiSignals()


class JimiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configurações de Identidade Visual da Janela Principal
        self.setWindowTitle("JIMI - Painel de Controle")
        self.setGeometry(100, 100, 480, 640)
        self.setStyleSheet("background-color: #0d1117; color: #c9d1d9;") 
        
        # Amarração do barramento de sinais interno
        ui_signals.update_text_signal.connect(self.append_to_chat)

        self.init_ui()
        self.init_system_tray()

    def init_ui(self):
        # Widget Central e Layout estrutural
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Tela de Transcrições / Logs do Sistema (Chat Display)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        self.chat_display.setStyleSheet(
            "background-color: #161b22; "
            "border: 1px solid #30363d; "
            "border-radius: 6px; "
            "padding: 12px; "
            "color: #8b949e;"
        )
        layout.addWidget(self.chat_display)

        # Campo de Entrada de Texto (Prompt Manual)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Envie um comando por texto para o JIMI...")
        self.input_field.setFont(QFont("Segoe UI", 10))
        self.input_field.setStyleSheet(
            "background-color: #21262d; "
            "border: 1px solid #30363d; "
            "border-radius: 6px; "
            "padding: 10px; "
            "color: #c9d1d9;"
        )
        self.input_field.returnPressed.connect(self.send_command)
        layout.addWidget(self.input_field)

        # Botão de Execução manual via clique
        self.send_button = QPushButton("Executar Ordem")
        self.send_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.setStyleSheet(
            "QPushButton {"
            "   background-color: #238636; "
            "   color: white; "
            "   padding: 12px; "
            "   border-radius: 6px; "
            "   border: none;"
            "}"
            "QPushButton:hover {"
            "   background-color: #2ea043;"
            "}"
            "QPushButton:pressed {"
            "   background-color: #227e32;"
            "}"
        )
        self.send_button.clicked.connect(self.send_command)
        layout.addWidget(self.send_button)

        self.append_to_chat("SISTEMA: Canais neurais da interface gráfica ativos.")

    def init_system_tray(self):
        """Inicializa e gerencia o ícone invisível na barra de tarefas (ao lado do relógio)."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Autodetecta um ícone customizado se existir, caso contrário usa o padrão do SO
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "assets", "jimi_icon.png")
        
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Fallback seguro usando o ícone de monitor do próprio Sistema Operacional
            self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        # Menu contextual de clique direito na bandeja
        tray_menu = QMenu()
        tray_menu.setStyleSheet("background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d;")
        
        show_action = QAction("Exibir Painel", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Recolher para Background", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Encerrar JIMI OS", self)
        quit_action.triggered.connect(self.close_system)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Vincula clique no ícone para restaurar a janela
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.raise_()
                self.activateWindow()

    def send_command(self):
        command = self.input_field.text().strip()
        if command:
            self.append_to_chat(f"Pedro: {command}")
            self.input_field.clear()
            
            # Envia para a Worker Thread de automação. O retorno cai direto no sinal da UI.
            jimi_core.submit_command(command, callback=ui_signals.update_text_signal.emit)

    def append_to_chat(self, text):
        """Escreve na tela e força a rolagem para acompanhar as novidades."""
        if text.startswith("Pedro:"):
            # Colore o texto do usuário de forma diferenciada para facilitar leitura
            self.chat_display.append(f"<span style='color: #58a6ff;'><b>&gt; {text}</b></span>")
        elif text.startswith("SISTEMA:") or text.startswith("["):
            self.chat_display.append(f"<span style='color: #8b949e;'><i>&gt; {text}</i></span>")
        else:
            self.chat_display.append(f"<span style='color: #ff7b72;'><b>&gt; JIMI:</b></span> {text}")
            
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """Intercepta o clique no 'X' da janela para não fechar o app, apenas minimizar."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "JIMI Operando de Fundo",
            "O núcleo cognitivo continua ativo na sua barra de tarefas.",
            QSystemTrayIcon.Information,
            2500
        )

    def close_system(self):
        """Protocolo de encerramento global com persistência de memória."""
        logger.info("[SHUTDOWN] Desligando módulos centrais...")
        
        # 1. Desliga as threads de automação com segurança
        jimi_core.shutdown_jimi()
        
        # 2. Força o salvamento instantâneo do banco vetorial local (Evita perda de dados)
        try:
            from core.vector_store import vector_store
            vector_store.save()
        except Exception as e:
            logger.error(f"Não foi possível salvar o banco semântico no desligamento: {e}")
            
        # 3. Mata a aplicação PyQt5 de forma limpa
        QApplication.quit()


# Inicializador estruturado do app
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Impede que o fechamento da janela mate o processo (essencial para apps de System Tray)
    app.setQuitOnLastWindowClosed(False) 
    
    jimi_gui = JimiWindow()
    jimi_gui.show()
    
    sys.exit(app.exec_())