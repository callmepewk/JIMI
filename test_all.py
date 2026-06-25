import logging
import os

# Garante que a raiz do projeto esteja no path para importar os módulos corretamente


from services.services_manager import services_manager
from core.brain import jimi_brain

# Configuração de log para o teste
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("JIMI.TestAll")

def run_diagnostic():
    print("\n========================================")
    print("   INICIANDO DIAGNÓSTICO DO SISTEMA")
    print("========================================\n")

    # 1. Teste de Serviços (Hardware e SO)
    print("[1/3] Testando Módulos de Serviços...")
    try:
        # Testa o contexto de sistema
        context = services_manager.execute_task("system", "get_current_context")
        print(f"  [✓] SystemService: OK -> Janela ativa detectada: '{context.get('active_window')}'")
        
        # Testa a engine de voz (Sintetizador)
        services_manager.execute_task("voice", "speak", "Sistema de testes online.")
        print("  [✓] VoiceService: OK (Áudio enviado para a fila)")
    except Exception as e:
        print(f"  [X] Falha em ServicesManager: {e}")

    # 2. Teste do Cérebro (Cognição)
    print("\n[2/3] Testando Motor Cognitivo (Llama 3)...")
    try:
        # Teste de intenção simples
        response = jimi_brain.think("Olá, JIMI. Você está operacional?")
        print(f"  [✓] Brain/Ollama: OK -> Resposta: '{response}'")
    except Exception as e:
        print(f"  [X] Falha no Brain: {e}")

    # 3. Teste de Automação (Executor)
    print("\n[3/3] Testando Executor Físico...")
    try:
        # Testa um comando de rede (ping) para garantir que o executor dispara tarefas
        resultado_rede = services_manager.execute_task("network", "ping_host", "8.8.8.8")
        print(f"  [✓] Executor/Network: OK -> Resultado: {resultado_rede}")
    except Exception as e:
        print(f"  [X] Falha no Executor: {e}")

    print("\n========================================")
    print("   DIAGNÓSTICO CONCLUÍDO")
    print("========================================\n")

if __name__ == "__main__":
    run_diagnostic()