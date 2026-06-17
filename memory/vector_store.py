import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Inicializa o store com um modelo de linguagem leve para embeddings.
        'all-MiniLM-L6-v2' é rápido e altamente preciso para português.
        """
        print(f"[VECTOR] Carregando modelo de embeddings: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.data = []  # Armazena dicionários: {"text": str, "embedding": np.array}

    def add(self, text):
        """Converte texto em vetor semântico e armazena."""
        embedding = self.model.encode(text)
        self.data.append({"text": text, "embedding": embedding})

    def search(self, query, top_k=3):
        """Busca os itens mais semanticamente similares à query."""
        if not self.data:
            return []
        
        # Converte a query para vetor
        query_embedding = self.model.encode(query)
        
        # Calcula a similaridade de cosseno para todos os itens
        results = []
        for item in self.data:
            similarity = np.dot(query_embedding, item["embedding"])
            results.append((item["text"], similarity))
        
        # Ordena pelo maior score de similaridade
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [r[0] for r in results[:top_k]]

    def get_all(self):
        return [item["text"] for item in self.data]

# Instância global otimizada
vector_store = VectorStore()