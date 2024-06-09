
# Sistema de Busca Peer-to-Peer Não Estruturado

## Descrição
Este projeto é parte da disciplina de Desenvolvimento de Sistemas de Informação Distribuídos (DSID) da Universidade de São Paulo. O objetivo é implementar um sistema de busca peer-to-peer não estruturado com métodos de busca como inundação (flooding), caminhada aleatória (random walk) e busca em profundidade.

## Instalação
Para rodar este projeto, você precisará de Python 3.x instalado em sua máquina. 

Clone o repositório:
```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

Instale as dependências necessárias:
```bash
pip install -r requirements.txt
```

## Uso
Para iniciar um nó, use o seguinte comando:
```bash
python node.py <endereco>:<porta> [vizinhos.txt [lista_chave_valor.txt]]
```
Exemplo:
```bash
python node.py 127.0.0.1:5001 vizinhos.txt key_value1.txt
```

## Estrutura dos Arquivos
- `gerar_arquivos.py`: Script para gerar arquivos de exemplo.
- `node.py`: Implementação do nó do sistema peer-to-peer.
- `start_nodes.ps1`: Script para iniciar múltiplos nós em PowerShell.
- `key_value1.txt`, `key_value2.txt`, `key_value3.txt`: Arquivos de exemplo contendo pares chave-valor.
- `1.txt`, `2.txt`, `3.txt`: Arquivos de exemplo contendo listas de vizinhos.

## Comandos e Funcionalidades
Após iniciar um nó, o seguinte menu será exibido:

```plaintext
Escolha o comando
[0] Listar vizinhos
[1] HELLO
[2] SEARCH (flooding)
[3] SEARCH (random walk)
[4] SEARCH (busca em profundidade)
[5] Estatisticas
[6] Alterar valor padrao de TTL
[9] Sair
```

### Descrição dos Comandos
- **Listar Vizinhos**: Lista todos os vizinhos conectados.
- **HELLO**: Envia uma mensagem HELLO para um vizinho.
- **SEARCH (flooding)**: Realiza uma busca na rede usando o método de inundação.
- **SEARCH (random walk)**: Realiza uma busca na rede usando o método de caminhada aleatória.
- **SEARCH (busca em profundidade)**: Realiza uma busca na rede usando o método de busca em profundidade.
- **Estatisticas**: Exibe estatísticas das buscas realizadas.
- **Alterar valor padrao de TTL**: Altera o valor padrão do TTL.
- **Sair**: Encerra o nó.

## Exemplos de Uso
### Listar Vizinhos
```plaintext
Escolha o comando
[0] Listar vizinhos
[1] HELLO
...
0

Ha 3 vizinhos na tabela:
[0] 127.0.0.1 5001
[1] 127.0.0.1 5004
[2] 127.0.0.1 5005
```

### Enviar HELLO
```plaintext
Escolha o comando
[0] Listar vizinhos
[1] HELLO
...
1

Escolha o vizinho:
Ha 3 vizinhos na tabela:
[0] 127.0.0.1 5001
[1] 127.0.0.1 5004
[2] 127.0.0.1 5005

0
Encaminhando mensagem "127.0.0.1:5002 4 1 HELLO" para 127.0.0.1:5001
Envio feito com sucesso: "127.0.0.1:5002 4 1 HELLO"
```

## Testes
Os testes devem ser realizados em topologias simples e complexas. Sugere-se alguns testes:

- Verificação das operações HELLO e BYE.
- Lógica do TTL aplicada corretamente.
- Busca por flooding encontrando chaves.
- Busca por random walk em redes com e sem ciclos.
- Busca em profundidade em redes com e sem ciclos.
- Coleta e exibição de estatísticas.

## Detalhes de Implementação
### Paradigma de Programação
Este projeto utiliza programação orientada a objetos para modularizar as funcionalidades dos nós da rede.

### Comunicação entre Nós
A comunicação é realizada através de sockets TCP. Utiliza-se operações bloqueantes para simplicidade.

### Organização do Código
O código está dividido em módulos para facilitar a manutenção e testes. As mensagens são codificadas em texto puro para facilitar a depuração.

## Autores
- Nome do Autor 1
- Nome do Autor 2

## Licença
Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

