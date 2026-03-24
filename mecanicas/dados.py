import random

class SistemaDados:
    @staticmethod
    def rolar_d20():
        """Gera um número aleatório entre 1 e 20[cite: 12]."""
        return random.randint(1, 20)

    @staticmethod
    def rolar_d6():
        """Gera um número aleatório entre 1 e 6 para o cálculo de dano."""
        return random.randint(1, 6)
    
    @staticmethod
    def rolar_d8():
        """Gera um número aleatório entre 1 e 8 para o cálculo de dano."""
        return random.randint(1, 8)
    
    @staticmethod
    def rolar_d10():
        """Gera um número aleatório entre 1 e 10 para o cálculo de dano."""
        return random.randint(1, 10)
    
    @staticmethod
    def rolar_d12():
        """Gera um número aleatório entre 1 e 12 para o cálculo de dano."""
        return random.randint(1, 12)
    
    @staticmethod
    def rolar_d4():
        """Gera um número aleatório entre 1 e 4 para o cálculo de dano."""
        return random.randint(1, 4)
    
    @staticmethod
    def rolar_d100():
        """Gera um número aleatório entre 1 e 100 para testes de porcentagem."""
        return random.randint(1, 100)

    @staticmethod
    def rolar_personalizado(minimo: int, maximo: int) -> int:
        """Rola um dado com qualquer faixa de valores."""
        return random.randint(minimo, maximo)