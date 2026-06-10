# versão simples (sem embeddings ainda)

class VectorStore:
    def __init__(self):
        self.data = []

    def add(self, text):
        self.data.append(text)

    def search(self, query):
        # busca simples por similaridade básica
        results = []

        for item in self.data:
            if query.lower() in item.lower():
                results.append(item)

        return results[-5:]


# instância global
vector_store = VectorStore()