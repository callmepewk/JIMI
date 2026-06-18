import os
import ast
import re
import logging
import requests

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JIMI.SelfEvolution")

class SelfEvolutionEngine:
    def __init__(self, root_dir=None):
        # Se não passar diretório, assume a raiz do projeto JIMI
        self.root_dir = root_dir if root_dir else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.ollama_url = "http://127.0.0.1:11434/api/generate"
        self.model_name = "llama3"

    def read_file(self, file_path):
        """Lê o conteúdo de um arquivo do sistema com segurança."""
        full_path = os.path.join(self.root_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Arquivo não encontrado no circuito: {file_path}")
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    def apply_improvement(self, file_path, new_code):
        """
        Aplica a alteração no código após validar a integridade da sintaxe.
        """
        try:
            # Garante que a IA não gerou um código quebrado
            ast.parse(new_code)
            
            full_path = os.path.join(self.root_dir, file_path)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_code)
            logger.info(f"[EVOLUÇÃO] {file_path} foi reescrito e atualizado com sucesso!")
            return True
        except SyntaxError as e:
            logger.error(f"[EVOLUÇÃO FALHOU] Sintaxe inválida gerada para {file_path}: {e}")
            return f"Erro de sintaxe no código gerado: {e}"

    def _extract_clean_code(self, raw_response):
        """Remove marcações de Markdown (```python) e comentários externos da LLM."""
        # Procura por blocos de código markdown
        code_block_match = re.search(r"```python\s*(.*?)\s*```", raw_response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        generic_block_match = re.search(r"```\s*(.*?)\s*```", raw_response, re.DOTALL)
        if generic_block_match:
            return generic_block_match.group(1).strip()
            
        return raw_response.strip()

    def analyze_and_evolve(self, target_file, request_details):
        """
        Coleta o arquivo-alvo, envia para análise semântica do Ollama 
        e reescreve o script local se a validação do AST aprovar.
        """
        logger.info(f"Iniciando ciclo de auto-evolução no arquivo: {target_file}")
        
        try:
            # 1. Recupera o estado atual do código
            current_code = self.read_file(target_file)
        except Exception as e:
            return f"Sr. Pedro, falhei ao acessar o módulo físico: {e}"

        # 2. Constrói o prompt técnico restritivo para a LLM
        prompt = (
            f"Você é o Engenheiro de Auto-Evolução do JIMI. Sua tarefa é modificar o código do arquivo '{target_file}' "
            f"com base estrita na solicitação do desenvolvedor.\n\n"
            f"Solicitação do Sr. Pedro: {request_details}\n\n"
            f"=== CÓDIGO ATUAL DE {target_file} ===\n"
            f"{current_code}\n"
            f"=====================================\n\n"
            f"Instruções cruciais:\n"
            f"1. Retorne o código INTEIRO modificado, funcional e completo.\n"
            f"2. Coloque o código obrigatoriamente dentro de um bloco markdown ```python e ```.\n"
            f"3. Não adicione explicações de texto antes ou depois do código. Apenas gere o código modificado.\n"
            f"Resposta do Engenheiro JIMI:"
        )

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            # Timeout estendido para dar tempo à LLM de reescrever arquivos inteiros
            response = requests.post(self.ollama_url, json=payload, timeout=90)
            response.raise_for_status()
            raw_text = response.json().get("response", "")
            
            # 3. Limpa e isola o script retornado
            clean_code = self._extract_clean_code(raw_text)
            
            if not clean_code or clean_code == raw_text:
                if "import" not in clean_code and "def" not in clean_code:
                    return "Sr. Pedro, a resposta gerada pelo motor de evolução não parece conter um código Python válido."

            # 4. Tenta aplicar o novo código através do validador AST
            result = self.apply_improvement(target_file, clean_code)
            
            if result is True:
                return f"Evolução concluída, Sr. Pedro! O arquivo '{target_file}' foi atualizado e passou nos testes de integridade sintática."
            else:
                return f"Sr. Pedro, o motor gerou a atualização, mas ela foi rejeitada pelo validador: {result}"

        except Exception as e:
            logger.error(f"Erro na comunicação com o motor evolutivo local: {e}")
            return f"Não foi possível processar a auto-evolução. Erro na chamada do motor: {e}"

# Instância unificada para o ecossistema
evolution_engine = SelfEvolutionEngine()