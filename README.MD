# 🎵 FNF Rhythm Game (Python)

Protótipo de jogo de ritmo inspirado em Friday Night Funkin', desenvolvido em **Python** utilizando a biblioteca **Pygame**.

O objetivo do jogo é pressionar as teclas corretas no ritmo da música enquanto as notas caem na tela.

Este projeto foi desenvolvido como **trabalho acadêmico para o curso de Ciência da Computação**.

---

# 🎮 Funcionalidades

* Menu simples para iniciar o jogo
* Sistema de notas sincronizadas com a música
* Controles utilizando teclado
* Sistema básico de acerto de notas
* Estrutura simples para adicionar novas músicas
* Script para criação de charts (mapa de notas)

---

# 🕹️ Controles

| Tecla  | Ação          |
| ------ | ------------- |
| A ou ← | Nota esquerda |
| S ou ↓ | Nota baixo    |
| W ou ↑ | Nota cima     |
| D ou → | Nota direita  |

Pressione a tecla quando a nota atingir a área de acerto.

---

# 📁 Estrutura do Projeto

```
fnf-anhanguera-guilherme/

main.py
chart_maker.py

songs/
   musica1/
      som.mp3
      data.json

assets/
   seta.png
```

### Arquivos principais

| Arquivo        | Função                                |
| -------------- | ------------------------------------- |
| main.py        | Executa o jogo                        |
| chart_maker.py | Script para gravar as notas da música |
| songs/         | Pasta contendo todas as músicas       |
| assets/        | Recursos visuais do jogo              |

---

# ▶️ Como executar o projeto

### 1️⃣ Criar ambiente virtual

```
python -m venv venv
```

Ativar no Windows:

```
venv\Scripts\activate
```

---

### 2️⃣ Instalar dependências

```
pip install pygame
```

---

### 3️⃣ Executar o jogo

```
python main.py
```

---

# 🎼 Como adicionar uma nova música

1️⃣ Crie uma pasta dentro de `songs`

Exemplo:

```
songs/minha_musica/
```

2️⃣ Coloque o arquivo da música com o nome:

```
som.mp3
```

3️⃣ Gere o mapa de notas:

```
python chart_maker.py
```

Digite o nome da pasta da música e pressione as teclas no ritmo.

O sistema criará automaticamente o arquivo:

```
data.json
```

---

# 📄 Formato do arquivo de notas

Exemplo de `data.json`:

```json
{
  "notes": [
    {"time": 1000, "lane": 0},
    {"time": 1500, "lane": 1},
    {"time": 2000, "lane": 2},
    {"time": 2500, "lane": 3}
  ]
}
```

### Explicação

| Campo | Significado                    |
| ----- | ------------------------------ |
| time  | Tempo da nota em milissegundos |
| lane  | Coluna da nota                 |

---

# 🚀 Melhorias futuras

* Sistema de pontuação
* Barra de vida
* Animações
* Interface gráfica melhor
* Implementar personagens e cenários

---

# 👨‍💻 Autor

**Guilherme Souza Dionizio**

Estudante de Ciência da Computação
Interesse em desenvolvimento backend, jogos e segurança da informação.

---

# 📜 Licença

Este projeto foi desenvolvido para fins educacionais.
