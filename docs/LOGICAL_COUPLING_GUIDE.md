# 🕸️ Guia Rápido: Diagrama de Acoplamento Lógico

## Iniciando

```bash
# 1. Instalar dependências (se não fez ainda)
pip install -r requirements.txt

# 2. Executar o dashboard
streamlit run app.py
```

## Navegação

1. **Barra Lateral** (esquerda)

   - `Caminho do Repositório`: Cole o caminho absoluto do seu repo Git
   - `API Key do Google`: (opcional) Para análise IA
   - `Número de Commits`: Quantos commits analisar (padrão: 100)
2. **Dashboard Principal**

   - **Aba 1 - Visão Geral**: Top 10 arquivos com maior risco
   - **Aba 2 - Matriz de Risco**: Scatter plot Churn vs Complexidade
   - **Aba 3 - Acoplamento Lógico**: Tabela e gráfico de pares
   - **Aba 4 - 🕸️ Diagrama de Rede** ← **NOVA FEATURE**
   - **Aba 5 - Consultor IA**: Análise com Gemini

## Entendendo o Diagrama de Rede

### Componentes Visuais

```
     auth.py (grande, azul)
        /|\
       / | \
      /  |  \ (espessas = frequência alta)
     /   |   \
 user.py role.py permission.py
(nó)    (nó)        (nó)
```


| Elemento          | Significa                                           |
| ----------------- | --------------------------------------------------- |
| 🔵**Nó Grande**  | Arquivo com alto risk score (churn × complexidade) |
| 🔵**Nó Pequeno** | Arquivo com baixo risco                             |
| 🟡**Cor Amarela** | Arquivo JavaScript/JSX                              |
| 🔵**Cor Azul**    | Arquivo Python                                      |
| **Linha Grossa**  | Dois arquivos mudam juntos frequentemente           |
| **Linha Fina**    | Dois arquivos mudam juntos raramente                |

### Cores

```
🔵 Python         #4B8BFF
🟡 JavaScript     #FFD700
🟦 TypeScript     #3178C6
🟠 Java           #FF6B35
🔶 Go             #00ADD8
⚫ Outro           #CCCCCC
```

## Exemplos de Interpretação

### Cenário 1: Baixo Acoplamento ✅

```
auth.py -------- permission.py
        (1 conexão)

Interpretação: Arquivos raramente mudam juntos.
Ação: Nenhuma necessária.
```

### Cenário 2: Acoplamento Moderado ⚠️

```
user.py ======== email.py
        (5 conexões)

Interpretação: Mudam juntos em ~5 commits.
Ação: Considere adicionar testes integrados.
```

### Cenário 3: Acoplamento Alto 🔴

```
main.py ========== config.py
        (20 conexões, nós grandes)

Interpretação: Mudam juntos frequentemente.
Violam SRP (Single Responsibility Principle).
Ação: Refatore para separar responsabilidades.
```

## Usando a Interatividade

### Mouse

- **Hover (passar sobre nó)**: Vê nome e risk score
- **Hover (passar sobre aresta)**: Vê quantos commits compartilhados
- **Clicar e Arrastar**: Move os nós para organizar melhor
- **Scroll (roda do mouse)**: Zoom in/out

### Física Dinâmica

O grafo se reorganiza automaticamente com "físicas":

- Nós se repelem (como imãs iguais)
- Arestas os atraem (como molas)
- Depois de alguns segundos estabiliza

## KPIs da Aba

```
┌─────────────────────────────────────────┐
│  Total de Arquivos  │  Conexões  │ Força │
│       Acoplados     │ Detectadas │ Máx.  │
│         12          │     18     │   7   │
└─────────────────────────────────────────┘
```

- **12 Arquivos**: Quantos arquivos tem acoplamento ≥2
- **18 Conexões**: Total de pares acoplados
- **7**: Força máxima (commits mais freqüentes)

## Configurações Avançadas

### Aumentar Precisão

```python
# Em src/collector.py
min_shared_commits = 3  # Só mostrar acoplamentos > 3
```

### Melhorar Layout

```python
# Em app.py, função render_coupling_network()
"gravitationalConstant": -50000,  # Mais repulsão
"springLength": 400,              # Nós mais afastados
"iterations": 300                 # Mais iterações (mais lento mas melhor)
```

### Ignorar Mais Arquivos

```python
# Em src/collector.py, método should_ignore()
IGNORED_EXTENSIONS = (
    '.ts.map',    # Adicionar mapas TypeScript
    '.test.js',   # Ignorar testes
    # ...
)
```

## Troubleshooting

### "Nenhum acoplamento detectado"

- ✅ Aumente `num_commits` (100 → 200)
- ✅ Diminua `min_shared_commits` (2 → 1)
- ✅ Verifique se o repo tem múltiplos commits

### Grafo muito denso/confuso

- ✅ Aumente `min_shared_commits` para 3-5
- ✅ Reduza `num_commits`
- ✅ Clique e arraste para reorganizar manualmente

### Diagrama não carrega

- ✅ Atualize Streamlit: `pip install --upgrade streamlit`
- ✅ Limpe cache: Botão "Limpar Cache e Recarregar"
- ✅ Verifique console para erros

## Formato de Saída

A função `get_logical_coupling()` retorna:

```json
{
  "nodes": [
    {
      "id": "src/auth/user.py",
      "label": "user.py",
      "title": "user.py\nRisk Score: 1250",
      "size": 35,
      "color": "#4B8BFF"
    }
  ],
  "edges": [
    {
      "source": "src/auth/user.py",
      "target": "src/email/notifier.py",
      "weight": 7,
      "title": "7 commits compartilhados"
    }
  ],
  "stats": {
    "total_nodes": 12,
    "total_edges": 18,
    "max_coupling_strength": 7,
    "avg_coupling_strength": 3.2
  }
}
```

## API de Programação

Se quiser usar a função diretamente:

```python
from src.collector import GitCollector

collector = GitCollector(
    repo_path="C:/seu/repo",
    limit_commits=100
)

# Coletar métricas
metrics = collector.collect_metrics()

# Obter dados para grafo
coupling_data = collector.get_logical_coupling(min_shared_commits=2)

# Usar dados
print(f"Total de nós: {coupling_data['stats']['total_nodes']}")
print(f"Total de arestas: {coupling_data['stats']['total_edges']}")

for edge in coupling_data['edges'][:5]:
    print(f"{edge['source']} <-> {edge['target']}: {edge['weight']} commits")
```

## Métricas de Referência

Para ajudar a interpretar resultados:


| Métrica          | Baixo | Médio | Alto  | Crítico |
| ----------------- | ----- | ------ | ----- | -------- |
| **Nós**          | <5    | 5-15   | 15-30 | >30      |
| **Arestas**       | <5    | 5-20   | 20-50 | >50      |
| **Força Máx.**  | <3    | 3-7    | 7-15  | >15      |
| **Força Média** | <2    | 2-5    | 5-10  | >10      |

---

**Versão**: Repo Health AI v1.1
**Última Atualização**: Janeiro 2026
**Status**: ✅ Pronto para Uso
