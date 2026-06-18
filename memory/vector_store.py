import os
import pickle
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("JIMI.VectorStore")

class VectorStore:
    def __init__(self, model_name='all-MiniLM-L6-v2', storage_path='data/vector_store.pkl'):
        """
        Banco de Dados Vetorial Local Otimizado para o JIMI.
        Usa computação matricial via NumPy para buscas semânticas instantâneas.
        """
        self.storage_path = storage_path
        
        # Cria o diretório de dados se não existir
        os.makedirs(os.path.dirname(self.storage_path) if os.path.dirname(self.storage_path) else '.', exist_ok=True)
        
        logger.info(f"[VECTOR] Carregando modelo de embeddings: {model_name}...")
        self.model = SentenceTransformer(model_name)
        
        # Memória RAM do banco
        self.documents = []  # Lista de dicionários: {"text": str, "metadata": dict}
        self.embeddings_matrix = None  # Matriz NumPy de formato (N, Vetor_Dim)
        
        # Tenta restaurar dados anteriores automaticamente
        self.load()

    def add(self, text: str, metadata: dict = None):
        """
        Converte o texto em vetor semântico e injeta na matriz de dados.
        """
        if not text or not text.strip():
            return
            
        # Gera o embedding e força a normalização L2 (essencial para similaridade de cosseno direta)
        embedding = self.model.encode(text, convert_to_numpy=True)
        embedding = embedding / np.linalg.norm(embedding)
        
        self.documents.append({
            "text": text.strip(),
            "metadata": metadata or {}
        })
        
        # Atualiza a matriz de embeddings na memória
        if self.embeddings_matrix is None:
            self.embeddings_matrix = np.array([embedding], dtype=np.float32)
        else:
            self.embeddings_matrix = np.vstack([self.embeddings_matrix, embedding])

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Busca os itens mais semanticamente similares usando multiplicação de matrizes.
        Retorna uma lista de dicionários contendo o texto, score e metadados.
        """
        if not self.documents or self.embeddings_matrix is None:
            return []
            
        # Converte a query e normaliza seu tamanho
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm
            
        # MULTIPLICAÇÃO MATRICIAL: Calcula a similaridade de cosseno de todos os vetores de uma só vez!
        # (N, Dim) x (Dim,) -> (N,)
        scores = np.dot(self.embeddings_matrix, query_embedding)
        
        # Obtém os índices dos top_k maiores scores de forma eficiente
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            # Filtro de corte mínimo de confiança semântica (opcional)
            if scores[idx] < 0.25:
                continue
                
            results.append({
                "text": self.documents[idx]["text"],
                "score": float(scores[idx]),
                "metadata": self.documents[idx]["metadata"]
            })
            
        return results

    def save(self):
        """Salva o estado atual da memória semântica em disco."""
        try:
            state = {
                "documents": self.documents,
                "embeddings_matrix": self.embeddings_matrix
            }
            with open(self.storage_path, 'wb') as f:
                pickle.dump(state, f)
            logger.info(f"[VECTOR] Banco semântico salvo com sucesso em '{self.storage_path}'.")
        except Exception as e:
            logger.error(f"[VECTOR ERROR] Falha ao persistir dados: {e}")

    def load(self):
        """Carrega a base de dados vetorial do disco para a memória RAM."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'rb') as f:
                    state = pickle.load(f)
                self.documents = state.get("documents", [])
                self.embeddings_matrix = state.get("embeddings_matrix", None)
                logger.info(f"[VECTOR] Memória restaurada. {len(self.documents)} documentos carregados.")
            except Exception as e:
                logger.error(f"[VECTOR ERROR] Erro ao carregar arquivo de índice: {e}. Inicializando banco limpo.")

    def clear(self):
        """Reseta completamente o banco de dados."""
        self.documents = []
        self.embeddings_matrix = None
        if os.path.exists(self.storage_path):
            try:
                os.remove(self.storage_path)
            except Exception:
                pass


# Instância global otimizada para o ecossistema JIMI
vector_store = VectorStore()