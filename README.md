# Guia de Execução do Sistema Peer-to-Peer

Este guia descreve como configurar e executar o sistema peer-to-peer para busca distribuída. Cada nó da rede pode armazenar pares chave-valor e participar de buscas usando métodos como inundação, caminhada aleatória e busca em profundidade.

## Pré-requisitos

Antes de iniciar, certifique-se de que você tem o Python 3 instalado em sua máquina. O código foi testado em ambientes Unix-like (Linux/MacOS).

## Estrutura do Código

O sistema é composto por dois arquivos principais:

- `node.py`: Define a classe `Node`, responsável por gerenciar a lógica de cada nó na rede.
- `main.py`: Script executável que inicia um nó e aceita comandos do usuário.

Além disso, você precisará de arquivos de texto para definir os vizinhos e pares chave-valor para cada nó, se desejar iniciar a rede com dados pré-definidos.

## Configuração e Execução

### 1. Preparação dos Arquivos de Dados

Crie arquivos de texto para definir os vizinhos e pares chave-valor de cada nó. Por exemplo:

**neighbors.txt**
127.0.0.1:5002
127.0.0.1:5003

**keys.txt**
chave1 valor1
chave2 valor2

### 2. Execução dos Nós

Para iniciar um nó, abra um terminal e use o seguinte comando:

```bash
python main.py <porta> [arquivo_de_vizinhos] [arquivo_de_pares_chave_valor]
```
## Exemplo
python main.py 127.0.0.1:5001 neighbors1.txt key_value1.txt

Repita isso em diferentes terminais para cada nó que deseja executar, alterando a porta e os arquivos conforme necessário.

### 3. Interagindo com o Sistema

Após iniciar o nó, você pode digitar comandos diretamente no terminal para interagir com a rede. Os comandos disponíveis incluem:

- **list**: Lista todos os vizinhos conectados ao nó.
- **search [method] [key]**: Inicia uma busca na rede. Métodos disponíveis:
  - `flooding`
  - `random_walk`
  - `depth`
- **exit**: Encerra a execução do nó.

**Exemplos de Comandos:**

```bash
Enter command (list, search [method] [key], exit): list
Enter command (list, search [method] [key], exit): search flooding chave1
Enter command (list, search [method] [key], exit): exit
```
