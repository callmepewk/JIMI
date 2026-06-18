import cv2
import os
import logging
import platform
import time
from datetime import datetime

logger = logging.getLogger("JIMI.CameraService")

class CameraService:
    def __init__(self, output_dir="media"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def handle(self, action: str, payload=None) -> str:
        """
        Ponto de entrada unificado para o ServicesManager do JIMI.
        Orquestra comandos de captura de foto e gravação de vídeo espelhados.
        """
        if action in ["capture", "take_photo"]:
            return self.take_photo()
            
        elif action in ["record", "record_video"]:
            duration = 5
            if isinstance(payload, (int, float)):
                duration = int(payload)
            elif isinstance(payload, dict):
                duration = int(payload.get("duration", 5))
                
            return self.record_video(duration=duration)
            
        return f"Ação '{action}' não é suportada pelo módulo de Câmera."

    def take_photo(self) -> str:
        """Captura uma foto espelhada da webcam padrão (visão de espelho)."""
        logger.info("Ativando hardware da câmera para foto espelhada...")
        
        if platform.system().lower() == "windows":
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            logger.error("Não foi possível acessar a webcam física.")
            return "Erro: Câmera indisponível ou sendo usada por outro aplicativo."

        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        cap.release()

        if ret:
            # Inverte o frame horizontalmente para dar o efeito de espelho real
            frame = cv2.flip(frame, 1)
            
            filename = f"jimi_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            full_path = os.path.join(self.output_dir, filename)
            cv2.imwrite(full_path, frame)
            logger.info(f"Foto espelhada capturada com sucesso: {full_path}")
            return f"Foto capturada e salva em: {full_path}"
        
        return "Erro: Falha ao registrar o frame da câmera."

    def record_video(self, duration: int = 5) -> str:
        """Grava um vídeo espelhado da webcam por um número X de segundos."""
        logger.info(f"Ativando hardware da câmera para vídeo espelhado ({duration}s)...")
        
        if platform.system().lower() == "windows":
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(0)
            
        if not cap.isOpened():
            logger.error("Não foi possível acessar a webcam física.")
            return "Erro: Câmera indisponível ou sendo usada por outro aplicativo."

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            fps = 20

        filename = f"jimi_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        full_path = os.path.join(self.output_dir, filename)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(full_path, fourcc, fps, (frame_width, frame_height))

        for _ in range(5):
            cap.read()

        logger.info(f"Gravação espelhada iniciada. Salvando em {full_path}...")
        start_time = time.time()
        
        try:
            while (time.time() - start_time) < duration:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Inverte o frame capturado antes de escrever no arquivo
                frame = cv2.flip(frame, 1)
                out.write(frame)
                
                time.sleep(1 / fps)
                
        except Exception as e:
            logger.error(f"Erro durante a gravação: {e}")
            return f"Erro durante a gravação do vídeo: {e}"
        finally:
            cap.release()
            out.release()

        logger.info(f"Vídeo espelhado finalizado com sucesso: {full_path}")
        return f"Vídeo de {duration} segundos gravado e salva em: {full_path}"


# Instanciação global necessária para o circuito do ServicesManager
camera_service = CameraService()