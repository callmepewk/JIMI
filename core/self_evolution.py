import os
import ast

class SelfEvolutionEngine:
    def __init__(self, root_dir):
        self.root_dir = root_dir

    def read_file(self, file_path):
        with open(os.path.join(self.root_dir, file_path), 'r', encoding='utf-8') as f:
            return f.read()

    def apply_improvement(self, file_path, new_code):
        """
        O coração da auto-evolução: 
        1. Valida o novo código (evita quebrar o sistema).
        2. Aplica a alteração com segurança.
        """
        try:
            # Verifica se o código é sintaticamente correto
            ast.parse(new_code)
            
            with open(os.path.join(self.root_dir, file_path), 'w', encoding='utf-8') as f:
                f.write(new_code)
            return True
        except SyntaxError as e:
            return f"Erro de sintaxe no código gerado: {e}"

    def analyze_and_evolve(self, request):
        """
        Esta função recebe sua solicitação, analisa os arquivos 
        e decide qual parte do sistema precisa evoluir.
        """
        # Exemplo: se o pedido for sobre 'voice_engine', o motor busca o arquivo
        # e sugere uma melhoria usando a lógica que discutimos.
        pass