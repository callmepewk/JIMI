import time
import os
import hashlib
import logging
import traceback
from core.services_manager import services_manager

# Configuração robusta de log
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] - %(message)s')
logger = logging.getLogger("JIMI.MobileBridge")

# --- PORTABILIDADE (Preparação para o Pen Drive) ---
# Descobre dinamicamente a pasta onde este script está rodando
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_COMANDO = os.path.join(BASE_DIR, "comando_ios.txt")
ARQUIVO_MEMORIA = os.path.join(BASE_DIR, ".ultima_hash")

def obter_hash_arquivo(caminho):
    """Cria uma assinatura digital do arquivo de forma segura."""
    if not os.path.exists(caminho):
        return None
    try:
        with open(caminho, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"Erro ao ler hash de {caminho}: {e}")
        return None

def ler_ultima_hash():
    if os.path.exists(ARQUIVO_MEMORIA):
        try:
            with open(ARQUIVO_MEMORIA, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            return ""
    return ""

def salvar_nova_hash(nova_hash):
    try:
        with open(ARQUIVO_MEMORIA, 'w', encoding='utf-8') as f:
            f.write(nova_hash)
    except Exception as e:
        logger.error(f"Erro ao salvar hash na memoria: {e}")

def iniciar_vigilancia():
    logger.info("[MobileBridge] Sistema online. Vigiando comandos do iOS via GitHub...")
    
    while True:
        try:
            # 1. Puxa as novidades do repositório
            # Assumimos que o sync_github tem seu próprio try/except interno
            sincronizado = services_manager.sync_github()
            
            if sincronizado:
                hash_atual = obter_hash_arquivo(ARQUIVO_COMANDO)
                hash_antiga = ler_ultima_hash()
                
                # 2. Verifica mudança
                if hash_atual and hash_atual != hash_antiga:
                    with open(ARQUIVO_COMANDO, 'r', encoding='utf-8') as f:
                        comando_texto = f.read().strip()
                    
                    if comando_texto:
                        logger.info(f"\n[!] NOVO COMANDO DO IOS DETECTADO: '{comando_texto}'")
                        
                        # -------------------------------------------------------------
                        # AQUI ENTRA A MÁGICA DA IA
                        # Exemplo futuro: ollama_service.traduzir_e_executar(comando_texto)
                        # -------------------------------------------------------------
                        
                        # 3. Salva a hash somente se tudo deu certo
                        salvar_nova_hash(hash_atual)
                        logger.info("[MobileBridge] Comando processado com sucesso.")
        
        except Exception as e:
            # Se qualquer coisa bizarra acontecer, o script não morre.
            logger.error(f"Erro inesperado no loop de vigilancia: {e}")
            logger.debug(traceback.format_exc())
            
        finally:
            # Garante que sempre vai dormir, mesmo se der erro, para não fritar a CPU
            # Nota: Para automação residencial (acender luz), 60s pode parecer lento.
            # Considere baixar para 15s ou 30s se a bateria do celular aguentar.
            time.sleep(30)

if __name__ == "__main__":
    iniciar_vigilancia()