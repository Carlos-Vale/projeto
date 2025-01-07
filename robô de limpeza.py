import random
import heapq
import tkinter as tk
from time import sleep

# Classe base do ambiente
class Ambiente:
    def __init__(self):
        self.coisas = []

    def adicionar_coisa(self, coisa):
        self.coisas.append(coisa)

    def percepcao(self, agente):
        raise NotImplementedError

    def executar_acao(self, agente, nova_posicao):
        raise NotImplementedError

# Classe do agente
class Agente:
    def __init__(self, programa):
        self.programa = programa
        self.visitas = set()
        self.limpas = set()
        self.voltar = False

# Subclasse do ambiente com matriz e obstáculos
class AmbienteMatriz(Ambiente):
    def __init__(self, linhas, colunas):
        super().__init__()
        self.linhas = linhas
        self.colunas = colunas
        self.matriz = self.gerar_matriz()
        self.posicao_agente = (0, 0)
        self.travado = False



    def gerar_matriz(self):
        matriz = [['Limpo' for _ in range(self.colunas)] for _ in range(self.linhas)]

        # Gera sujeira aleatoriamente
        for i in range(self.linhas):
            for j in range(self.colunas):
                if (i, j) != (0, 0):
                    matriz[i][j] = random.choice(['Sujo', 'Limpo'])

        # Adiciona obstáculos em grupos equilibrados
        num_obstaculos = (self.linhas * self.colunas) // 5
        obstaculos_adicionados = 0
        max_tentativas = 1000
        raio_seguro = 1
        espaçamento = 1

        while obstaculos_adicionados < num_obstaculos and max_tentativas > 0:
            linha_inicial = random.randint(0, self.linhas - 1)
            coluna_inicial = random.randint(0, self.colunas - 1)

            if abs(linha_inicial) + abs(coluna_inicial) <= raio_seguro:
                max_tentativas -= 1
                continue

            if matriz[linha_inicial][coluna_inicial] not in ['Obstáculo', 'Casa'] and self.verificar_vizinhos(linha_inicial, coluna_inicial, matriz, espaçamento):
              tamanho_grupo = 1 # Grupos menores para espaçamento
              for i in range(tamanho_grupo):
                for j in range(tamanho_grupo):
                    linha = linha_inicial + i
                    coluna = coluna_inicial + j
                    if (
                        0 <= linha < self.linhas and 0 <= coluna < self.colunas
                        and matriz[linha][coluna] not in ['Obstáculo', 'Casa']
                        and self.verificar_vizinhos(linha, coluna, matriz, espaçamento)
                    ):
                        matriz[linha][coluna] = 'Obstáculo'
                        obstaculos_adicionados += 1
        max_tentativas -= 1

        matriz[0][0] = 'Casa'
        return matriz
    
    def verificar_vizinhos(self, linha, coluna, matriz, espaçamento):
      """Verifica se não há obstáculos muito próximos."""
      for dx in range(-espaçamento, espaçamento + 1):
        for dy in range(-espaçamento, espaçamento + 1):
            nova_linha = linha + dx
            nova_coluna = coluna + dy
            if 0 <= nova_linha < self.linhas and 0 <= nova_coluna < self.colunas:
                if matriz[nova_linha][nova_coluna] == 'Obstáculo':
                    return False
      return True

    def percepcao(self, agente):
        linha, coluna = self.posicao_agente
        estado_atual = self.matriz[linha][coluna]
        if not self.ambiente_limpo() and (linha, coluna) == (0, 0):
            estado_atual = 'Obstáculo'
        return (self.posicao_agente, estado_atual)

    def executar_acao(self, agente, nova_posicao):
        self.posicao_agente = nova_posicao
        linha, coluna = nova_posicao
        if self.matriz[linha][coluna] == 'Sujo':
            self.matriz[linha][coluna] = 'Limpo'
            agente.limpas.add((linha, coluna))

    def ambiente_limpo(self):
        return all(
            self.matriz[linha][coluna] in ['Limpo', 'Obstáculo', 'Casa']
            for linha in range(self.linhas)
            for coluna in range(self.colunas)
        )

def a_estrela(inicio, objetivo, matriz, ambiente_limpo):
    linhas, colunas = len(matriz), len(matriz[0])
    movimentos = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def heuristica(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    fila = [(0, inicio)]
    custos = {inicio: 0}
    caminho = {inicio: None}

    while fila:
        _, atual = heapq.heappop(fila)

        if atual == objetivo:
            break

        for dx, dy in movimentos:
            vizinho = (atual[0] + dx, atual[1] + dy)
            if (
                0 <= vizinho[0] < linhas and 0 <= vizinho[1] < colunas and 
                matriz[vizinho[0]][vizinho[1]] != 'Obstáculo' and
                (vizinho != (0, 0) or ambiente_limpo)
            ):
                novo_custo = custos[atual] + 1
                if vizinho not in custos or novo_custo < custos[vizinho]:
                    custos[vizinho] = novo_custo
                    prioridade = novo_custo + heuristica(vizinho, objetivo)
                    heapq.heappush(fila, (prioridade, vizinho))
                    caminho[vizinho] = atual

    if objetivo not in caminho:
        return None

    atual = objetivo
    caminho_final = []
    while atual != inicio:
        caminho_final.append(atual)
        atual = caminho[atual]
    caminho_final.reverse()

    return caminho_final

# Programa do agente
def programa_limpeza(percepcao, ambiente, agente):
    posicao, estado = percepcao

    if estado == 'Sujo':
        return posicao

    sujas = [
        (i, j)
        for i in range(ambiente.linhas)
        for j in range(ambiente.colunas)
        if ambiente.matriz[i][j] == 'Sujo'
    ]

    if not sujas:
        agente.voltar = True
        caminho_para_casa = a_estrela(posicao, (0, 0), ambiente.matriz, True)
        if caminho_para_casa:
            return caminho_para_casa[0]
        return posicao

    for suja in sujas:
        caminho = a_estrela(posicao, suja, ambiente.matriz, ambiente.ambiente_limpo())
        if caminho:
            return caminho[0]

    movimentos = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    for dx, dy in movimentos:
        vizinho = (posicao[0] + dx, posicao[1] + dy)
        if (
            0 <= vizinho[0] < ambiente.linhas
            and 0 <= vizinho[1] < ambiente.colunas
            and ambiente.matriz[vizinho[0]][vizinho[1]] != 'Obstáculo'
        ):
            return vizinho

    ambiente.travado = False
    return posicao

# Interface gráfica
class InterfaceLimpeza(tk.Tk):
    def __init__(self, linhas, colunas):
        super().__init__()
        self.linhas = linhas
        self.colunas = colunas
        self.ambiente = AmbienteMatriz(linhas, colunas)
        self.agente = Agente(programa_limpeza)
        self.ambiente.adicionar_coisa(self.agente)
        self.celulas = [[None for _ in range(colunas)] for _ in range(linhas)]
        self.criar_interface()
        self.atualizar_interface()

    def criar_interface(self):
        largura_tela = self.winfo_screenwidth() - 100
        altura_tela = self.winfo_screenheight() - 100
        largura_celula = largura_tela // self.colunas
        altura_celula = altura_tela // self.linhas

        for i in range(self.linhas):
            for j in range(self.colunas):
                celula = tk.Label(self, width=int(largura_celula / 10), height=int(altura_celula / 20), 
                                  relief="ridge", borderwidth=2, font=("Arial", 8))
                celula.grid(row=i, column=j)
                self.celulas[i][j] = celula

    def atualizar_interface(self):
        for i in range(self.linhas):
            for j in range(self.colunas):
                estado = self.ambiente.matriz[i][j]
                if (i, j) == self.ambiente.posicao_agente:
                    if estado == 'Casa':
                        self.celulas[i][j].config(
                            text="Casa🤖", 
                            bg="lightgreen"
                        )
                    else:
                        self.celulas[i][j].config(
                            text="🤖" , 
                            bg="green" 
                        )
                elif estado == 'Casa':
                    self.celulas[i][j].config(text="Casa", bg="lightgreen")
                elif estado == 'Sujo':
                    self.celulas[i][j].config(text="Sujo", bg="orange")
                elif estado == 'Limpo':
                    self.celulas[i][j].config(text="Limpo", bg="white")
                elif estado == 'Obstáculo':
                    self.celulas[i][j].config(text="🧱", bg="gray")

    def exibir_mensagem_conclusao(self):
        mensagem = tk.Label(
            self, 
            text="🎉 Limpeza Concluída! 🎉", 
            font=("Arial", 14), 
            bg="lightblue", 
            relief="solid",
            borderwidth=2
        )
        mensagem.place(relx=0.5, rely=0.5, anchor="center")

    def executar_simulacao(self):
        while True:
            if self.ambiente.travado:
                print("O agente ficou preso. Reiniciando exploração...")
                self.ambiente.travado = False
            if self.agente.voltar:
                caminho_para_casa = a_estrela(self.ambiente.posicao_agente, (0, 0), self.ambiente.matriz, True)
                if caminho_para_casa:
                    for posicao in caminho_para_casa:
                        self.ambiente.executar_acao(self.agente, posicao)
                        self.atualizar_interface()
                        self.update()
                        sleep(0)
                print("Agente concluiu a limpeza e voltou para casa.")
                self.exibir_mensagem_conclusao()
                break
            percepcao = self.ambiente.percepcao(self.agente)
            nova_posicao = self.agente.programa(percepcao, self.ambiente, self.agente)
            self.ambiente.executar_acao(self.agente, nova_posicao)
            self.atualizar_interface()
            self.update()
            sleep(0)

if __name__ == "__main__":
    app = InterfaceLimpeza(10, 20)
    app.after(1000, app.executar_simulacao)
    app.mainloop()
    
