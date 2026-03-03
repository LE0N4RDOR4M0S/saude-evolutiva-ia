import streamlit as st
import pandas as pd
import plotly.express as px
from collections import defaultdict, deque
import time
import uuid
from datetime import datetime
from src.collector import GitCollector
from src.analyzer import AIAnalyzer
from src.config import Config
from src.repo_source import RepositoryPreparationError, RepositorySourceManager
from src.exporters import build_export_payload, build_markdown_export, build_pdf_export
import google.generativeai as genai
from pyvis.network import Network
import tempfile
import streamlit.components.v1 as components

RATE_LIMIT_BUCKETS = defaultdict(deque)


def get_client_key() -> str:
    if "client_session_id" not in st.session_state:
        st.session_state.client_session_id = str(uuid.uuid4())

    headers = {}
    context = getattr(st, "context", None)
    if context is not None:
        headers = getattr(context, "headers", {}) or {}

    forwarded_ip = None
    if hasattr(headers, "get"):
        forwarded_ip = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
        if forwarded_ip:
            forwarded_ip = str(forwarded_ip).split(",")[0].strip()

    return f"{forwarded_ip or 'session'}:{st.session_state.client_session_id}"


def consume_rate_limit(client_key: str, max_requests: int, window_seconds: int):
    now = time.time()
    window_start = now - window_seconds
    bucket = RATE_LIMIT_BUCKETS[client_key]

    while bucket and bucket[0] < window_start:
        bucket.popleft()

    if len(bucket) >= max_requests:
        retry_after = max(1, int(window_seconds - (now - bucket[0])))
        return False, retry_after

    bucket.append(now)
    return True, 0

st.set_page_config(
    page_title="Repo Health AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(show_spinner=False)
def analyze_repository(repo_path: str, num_commits: int, cache_key: str):
    """
    Minera o repositório Git e retorna métricas.
    Cache é essencial pois o processo pode ser demorado.
    """
    try:
        collector = GitCollector(repo_path, limit_commits=num_commits)
        metrics = collector.collect_metrics()
        coupling = collector.get_coupling_analysis(min_shared_commits=3)
        logical_coupling = collector.get_logical_coupling(min_shared_commits=2)
        return metrics, coupling, logical_coupling, None
    except Exception as e:
        return None, None, None, str(e)


def prepare_repository(source_mode: str, local_path: str, remote_url: str, num_commits: int):
    manager = RepositorySourceManager(
        git_timeout=Config.GIT_TIMEOUT_SECONDS,
        cache_ttl_hours=Config.REPO_CACHE_TTL_HOURS,
    )
    manager.cleanup_stale_cache()

    #Local if source_mode == "Local":
    #Local     prepared = manager.prepare_local_repository(local_path)
    #Local     return prepared, local_path

    prepared = manager.prepare_remote_repository(remote_url, depth=num_commits)
    return prepared, remote_url


def get_file_extension(filename: str) -> str:
    """Extrai a extensão do arquivo."""
    if '.' in filename:
        return filename.split('.')[-1].lower()
    return 'unknown'


def render_coupling_network(logical_coupling_data, filtered_file_types=None):
    if not logical_coupling_data['nodes']:
        return None
    
    net = Network(
        height="700px",
        width="100%",
        directed=False,
        notebook=True
    )
    
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "stabilization": {
                "iterations": 200
            },
            "barnesHut": {
                "gravitationalConstant": -40000,
                "centralGravity": 0.3,
                "springLength": 300,
                "springConstant": 0.04
            }
        }
    }
    """)
    
    nodes_to_add = logical_coupling_data['nodes']
    if filtered_file_types and len(filtered_file_types) > 0:
        nodes_to_add = [
            node for node in logical_coupling_data['nodes']
            if get_file_extension(node['label']) in filtered_file_types
        ]
    
    node_ids_to_add = {node['id'] for node in nodes_to_add}
    
    for node in nodes_to_add:
        net.add_node(
            node['id'],
            label=node['label'],
            size=node['size'],
            color=node['color'],
            title=node['title']
        )
    
    max_weight = logical_coupling_data['stats']['max_coupling_strength']
    
    for edge in logical_coupling_data['edges']:
        if edge['source'] in node_ids_to_add and edge['target'] in node_ids_to_add:
            weight = edge['weight']
            thickness = 1 + (weight / max_weight * 9) if max_weight > 0 else 1
            
            net.add_edge(
                edge['source'],
                edge['target'],
                weight=weight,
                title=edge['title'],
                width=thickness,
                color='rgba(75, 139, 255, 0.6)'
            )
    
    html_str = net.generate_html()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_str)
        return f.name



def format_authors(authors_dict):
    """Formata dicionário de autores para exibição."""
    if not authors_dict:
        return "N/A"
    return ", ".join([f"{name} ({count})" for name, count in authors_dict.items()])


def calculate_kpis(df):
    """Calcula KPIs principais do dashboard."""
    total_files = len(df)
    avg_risk = df["risk_score"].mean() if not df.empty else 0
    
    bus_factor = 0
    for _, row in df.iterrows():
        authors = row["top_authors"]
        if authors:
            total_changes = sum(authors.values())
            top_author_changes = max(authors.values())
            if (top_author_changes / total_changes) > 0.8:
                bus_factor += 1
    
    return total_files, avg_risk, bus_factor


@st.dialog("Exportar Análise")
def render_export_modal(export_ts: str, export_json_content: str, export_markdown_content: str, export_pdf_content, pdf_export_error: str = None):
    st.markdown("Escolha o formato de exportação:")

    st.download_button(
        label="JSON",
        data=export_json_content,
        file_name=f"repo_health_analysis_{export_ts}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.download_button(
        label="Markdown",
        data=export_markdown_content,
        file_name=f"repo_health_analysis_{export_ts}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    if export_pdf_content:
        st.download_button(
            label="PDF",
            data=export_pdf_content,
            file_name=f"repo_health_analysis_{export_ts}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    elif pdf_export_error:
        st.warning(f"PDF indisponível: {pdf_export_error}")

    if st.button("Fechar", use_container_width=True):
        st.session_state["show_export_modal"] = False
        st.rerun()


st.sidebar.title("Configurações")
st.sidebar.markdown("---")

cloud_mode = Config.APP_CLOUD_MODE

source_mode = "Remoto"
#Local if cloud_mode:
#Local     st.sidebar.info("Modo cloud ativo: entrada por URL Git remota.")
#Local     source_mode = "Remoto"
#Local else:
#Local     source_mode = st.sidebar.radio(
#Local         "Fonte do Repositório",
#Local         options=["Local", "Remoto"],
#Local         horizontal=True,
#Local         help="Use Local para desenvolvimento e Remoto para análise via URL Git."
#Local     )

repo_path = ""
repo_url = ""

repo_url = st.sidebar.text_input(
    "URL do Repositório Git",
    value="",
    placeholder="https://github.com/org/projeto.git",
    help="Informe uma URL Git pública ou com acesso permitido no ambiente."
)
#Local if source_mode == "Local":
#Local     repo_path = st.sidebar.text_input(
#Local         "Caminho do Repositório (Local)",
#Local         value="",
#Local         placeholder="C:/Users/seu-nome/seu-repo",
#Local         help="Digite o caminho completo do repositório Git local"
#Local     )
#Local else:
#Local     repo_url = st.sidebar.text_input(
#Local         "URL do Repositório Git",
#Local         value="",
#Local         placeholder="https://github.com/org/projeto.git",
#Local         help="Informe uma URL Git pública ou com acesso permitido no ambiente."
#Local     )

api_key_input = st.sidebar.text_input(
    "API Key do Google (Gemini)",
    type="password",
    placeholder="Cole sua chave aqui",
    help="Obtenha em: https://aistudio.google.com/app/apikey"
)
active_api_key = api_key_input.strip() if api_key_input else (Config.GOOGLE_API_KEY or "")

if not active_api_key:
    st.sidebar.warning("GOOGLE_API_KEY não configurada no ambiente. O consultor IA ficará indisponível.")

num_commits = st.sidebar.slider(
    "Número de Commits a Analisar",
    min_value=10,
    max_value=500,
    value=100,
    step=10,
    help="Mais commits = análise mais completa, mas mais lenta"
)

st.sidebar.markdown("---")

if st.sidebar.button("Limpar Cache e Recarregar"):
    st.cache_data.clear()
    st.session_state.pop("analysis_result", None)
    st.rerun()

run_analysis = st.sidebar.button("Analisar Repositório", type="primary")

st.sidebar.markdown("---")

st.title("Repo Health AI")
st.markdown(
    "**Dashboard de Análise de Saúde de Repositórios Git** | "
    "Identifique Hotspots, Acoplamento e Riscos de Manutenção"
)
st.markdown("---")

#Local if source_mode == "Local" and not repo_path:
#Local     st.warning("Configure o caminho do repositório na barra lateral para começar.")
#Local     st.stop()

if source_mode == "Remoto" and not repo_url:
    st.warning("Configure a URL do repositório Git na barra lateral para começar.")
    st.stop()

if active_api_key:
    genai.configure(api_key=active_api_key)

if run_analysis:
    client_key = get_client_key()
    allowed, retry_after = consume_rate_limit(
        client_key,
        Config.RATE_LIMIT_MAX_REQUESTS,
        Config.RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        st.error(
            f"Rate limit atingido. Tente novamente em aproximadamente {retry_after}s."
        )
        st.stop()

    try:
        prepared_repo, repository_identifier = prepare_repository(
            source_mode=source_mode,
            local_path=repo_path,
            remote_url=repo_url,
            num_commits=num_commits,
        )
    except RepositoryPreparationError as e:
        st.error(f"Erro ao preparar repositório: {str(e)}")
        st.stop()

    with st.spinner(f"Analisando os últimos {num_commits} commits... (pode levar alguns minutos)"):
        metrics, coupling, logical_coupling, error = analyze_repository(
            prepared_repo.path,
            num_commits,
            cache_key=f"{prepared_repo.source_id}:{prepared_repo.revision}:{num_commits}",
        )

    st.session_state.analysis_result = {
        "metrics": metrics,
        "coupling": coupling,
        "logical_coupling": logical_coupling,
        "error": error,
        "repository_identifier": repository_identifier,
    }

if "analysis_result" not in st.session_state:
    st.info("Configure os parâmetros e clique em 'Analisar Repositório'.")
    st.stop()

metrics = st.session_state.analysis_result["metrics"]
coupling = st.session_state.analysis_result["coupling"]
logical_coupling = st.session_state.analysis_result["logical_coupling"]
error = st.session_state.analysis_result["error"]
repository_identifier = st.session_state.analysis_result["repository_identifier"]

if error:
    st.error(f"Erro ao analisar o repositório: {error}")
    st.stop()

if not metrics:
    st.warning("Nenhuma métrica foi coletada. Verifique se o repositório possui commits.")
    st.stop()

df = pd.DataFrame(metrics)

threshold = df["risk_score"].quantile(0.7)
df["is_hotspot"] = df["risk_score"] > threshold

df["authors_display"] = df["top_authors"].apply(format_authors)

total_files, avg_risk, bus_factor = calculate_kpis(df)

export_json_content = build_export_payload(
    repository_identifier=repository_identifier,
    num_commits=num_commits,
    total_files=total_files,
    avg_risk=avg_risk,
    bus_factor=bus_factor,
    metrics=metrics,
    coupling=coupling,
    logical_coupling=logical_coupling,
    ai_report=st.session_state.get("last_ai_report"),
)

export_markdown_content = build_markdown_export(
    repository_identifier=repository_identifier,
    num_commits=num_commits,
    total_files=total_files,
    avg_risk=avg_risk,
    bus_factor=bus_factor,
    metrics=metrics,
    coupling=coupling,
    ai_report=st.session_state.get("last_ai_report"),
)

pdf_export_error = None
export_pdf_content = None
try:
    export_pdf_content = build_pdf_export(
        repository_identifier=repository_identifier,
        num_commits=num_commits,
        total_files=total_files,
        avg_risk=avg_risk,
        bus_factor=bus_factor,
        metrics=metrics,
        coupling=coupling,
    )
except Exception as e:
    pdf_export_error = str(e)

export_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
st.sidebar.markdown("### Exportar Análise")

if st.sidebar.button("Exportar Análise", type="primary"):
    st.session_state["show_export_modal"] = True

if st.session_state.get("show_export_modal", False):
    render_export_modal(
        export_ts=export_ts,
        export_json_content=export_json_content,
        export_markdown_content=export_markdown_content,
        export_pdf_content=export_pdf_content,
        pdf_export_error=pdf_export_error,
    )

st.markdown("### Indicadores Principais")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total de Arquivos Analisados",
        value=f"{total_files}",
        help="Quantidade de arquivos únicos com mudanças"
    )

with col2:
    st.metric(
        label="Risco Médio",
        value=f"{avg_risk:,.0f}",
        help="Média do Risk Score (Churn × Complexidade)"
    )

with col3:
    st.metric(
        label="Bus Factor",
        value=f"{bus_factor}",
        delta="Arquivos em risco de autoria",
        delta_color="inverse",
        help="Arquivos onde >80% das mudanças vêm de 1 pessoa"
    )

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Visão Geral",
    "Matriz de Risco",
    "Acoplamento Lógico",
    "Diagrama de Rede",
    "Consultor IA"
])

with tab1:
    st.markdown("### Resumo Estatístico")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Distribuição de Risco:**")
        st.dataframe(
            df[["risk_score"]].describe().T,
        )
    
    with col2:
        st.markdown("**Distribuição de Complexidade:**")
        st.dataframe(
            df[["complexity"]].describe().T,
        )
    
    st.markdown("---")
    st.markdown("### Top 10 Arquivos com Maior Risco")
    
    top_10 = df.nlargest(10, "risk_score")[["file", "churn", "complexity", "risk_score", "authors_display"]]
    
    st.dataframe(
        top_10,
        column_config={
            "file": st.column_config.TextColumn("Arquivo", width="medium"),
            "churn": st.column_config.NumberColumn("Churn", format="%d"),
            "complexity": st.column_config.NumberColumn("Complexidade", format="%d"),
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score",
                format="%d",
                min_value=0,
                max_value=int(df["risk_score"].max())
            ),
            "authors_display": st.column_config.TextColumn("Principais Autores", width="medium")
        },
        hide_index=True,
    )

with tab2:
    st.markdown("### Matriz de Risco: Churn vs Complexidade")
    st.markdown(
        "**Interpretação:** Quanto maior a bolha e mais à direita/acima, maior o risco. "
        "Hotspots (vermelho) exigem atenção imediata."
    )
    
    fig = px.scatter(
        df,
        x="complexity",
        y="churn",
        size="risk_score",
        color="is_hotspot",
        hover_data={
            "file": True,
            "churn": True,
            "complexity": True,
            "risk_score": True,
            "authors_display": True,
            "is_hotspot": False
        },
        labels={
            "complexity": "Complexidade Ciclomática",
            "churn": "Churn (Frequência de Mudanças)",
            "risk_score": "Risk Score",
            "is_hotspot": "Hotspot",
            "authors_display": "Autores Principais"
        },
        color_discrete_map={True: "#FF4B4B", False: "#4B8BFF"},
        title="",
        height=600
    )
    
    fig.update_layout(
        xaxis_title="Complexidade Ciclomática",
        yaxis_title="Churn (Frequência de Mudanças)",
        showlegend=True,
        legend_title_text="Hotspot?",
        hovermode="closest"
    )
    
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='white'),
            opacity=0.8
        )
    )
    
    st.plotly_chart(fig)
    
    st.markdown("---")
    st.markdown("### Tabela Interativa com Filtros")
    
    col1, col2 = st.columns(2)
    
    with col1:
        show_only_hotspots = st.checkbox("Mostrar apenas Hotspots", value=False)
    
    with col2:
        min_risk = st.slider(
            "Risco Mínimo",
            min_value=0,
            max_value=int(df["risk_score"].max()),
            value=0
        )
    
    filtered_df = df.copy()
    
    if show_only_hotspots:
        filtered_df = filtered_df[filtered_df["is_hotspot"]]
    
    filtered_df = filtered_df[filtered_df["risk_score"] >= min_risk]
    
    st.dataframe(
        filtered_df[["file", "churn", "complexity", "risk_score", "authors_display", "is_hotspot"]],
        column_config={
            "file": st.column_config.TextColumn("Arquivo", width="large"),
            "churn": st.column_config.NumberColumn("Churn", format="%d"),
            "complexity": st.column_config.NumberColumn("Complexidade", format="%d"),
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score",
                format="%d",
                min_value=0,
                max_value=int(df["risk_score"].max())
            ),
            "authors_display": st.column_config.TextColumn("Principais Autores"),
            "is_hotspot": st.column_config.CheckboxColumn("Hotspot")
        },
        hide_index=True,
        height=400
    )

with tab3:
    st.markdown("### Análise de Acoplamento Lógico")
    st.markdown(
        "**Acoplamento Lógico:** Arquivos que mudam frequentemente juntos podem indicar "
        "violação do princípio de responsabilidade única (SRP) ou dependências ocultas."
    )
    
    if coupling:
        coupling_df = pd.DataFrame(coupling)
        
        st.dataframe(
            coupling_df,
            column_config={
                "file_a": st.column_config.TextColumn("Arquivo A", width="medium"),
                "file_b": st.column_config.TextColumn("Arquivo B", width="medium"),
                "shared_commits": st.column_config.NumberColumn(
                    "Commits Compartilhados",
                    format="%d"
                ),
                "strength": st.column_config.TextColumn("Força do Acoplamento")
            },
            hide_index=True
        )
        
        st.markdown("---")
        st.markdown("### Top 5 Acoplamentos Mais Fortes")
        
        top_5_coupling = coupling_df.nlargest(5, "shared_commits")
        
        fig_coupling = px.bar(
            top_5_coupling,
            x="shared_commits",
            y=[f"{row['file_a']} ↔ {row['file_b']}" for _, row in top_5_coupling.iterrows()],
            orientation="h",
            labels={
                "x": "Número de Commits Compartilhados",
                "y": "Par de Arquivos"
            },
            title="",
            color="shared_commits",
            color_continuous_scale="Reds"
        )
        
        fig_coupling.update_layout(
            showlegend=False,
            height=400,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_coupling)
        
    else:
        st.info("ℹNenhum acoplamento significativo detectado (mínimo: 3 commits compartilhados).")

with tab4:
    st.markdown("### Diagrama de Rede de Acoplamento Lógico")
    st.markdown(
        "Visualização interativa dos arquivos e suas dependências implícitas. "
        "**Nós:** arquivos | **Arestas:** co-ocorrência em commits | **Tamanho:** risk score | **Cor:** tipo de arquivo"
    )
    
    if logical_coupling and logical_coupling['nodes']:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Arquivos Acoplados", logical_coupling['stats']['total_nodes'])
        
        with col2:
            st.metric("Conexões Detectadas", logical_coupling['stats']['total_edges'])
        
        with col3:
            st.metric("Força Máxima", int(logical_coupling['stats']['max_coupling_strength']))
        
        st.markdown("---")
        
        file_types = set()
        for node in logical_coupling['nodes']:
            ext = get_file_extension(node['label'])
            file_types.add(ext)
        
        file_types = sorted(file_types)
        
        st.markdown("### Filtrar por Tipo de Arquivo")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_file_types = st.multiselect(
                "Selecione os tipos de arquivo para exibir",
                options=file_types,
                default=file_types,
                help="Desmarque os tipos que deseja ocultar do diagrama"
            )
        
        with col2:
            if st.button("Mostrar Todos"):
                st.session_state.selected_types = file_types
                st.rerun()
        
        st.markdown("---")
        
        html_file = render_coupling_network(logical_coupling, selected_file_types if selected_file_types else None)
        
        if html_file:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            components.html(html_content, height=750)
            
            st.markdown("---")
            st.markdown("#### Legenda de Cores")
            
            color_legend = {
                "🔵 Python": "#4B8BFF",
                "🟡 JavaScript": "#FFD700",
                "🟦 TypeScript": "#3178C6",
                "🟠 Java": "#FF6B35",
                "🔶 Go": "#00ADD8",
                "⚫ Outro": "#CCCCCC"
            }
            
            col1, col2, col3 = st.columns(3)
            for i, (label, color) in enumerate(color_legend.items()):
                col = [col1, col2, col3][i % 3]
                with col:
                    st.markdown(
                        f"<span style='color: {color};'>●</span> {label}",
                        unsafe_allow_html=True
                    )
        else:
            st.warning("Não foi possível gerar o diagrama. Nenhum acoplamento significativo detectado.")
    else:
        st.info("Nenhum acoplamento lógico detectado com a métrica atual (mínimo: 2 commits compartilhados).")

with tab5:
    st.markdown("### Consultor IA Gemini")
    st.markdown(
        "Use a IA para obter insights avançados sobre a saúde do repositório. "
        "A análise considera Hotspots, Bus Factor e Acoplamento Lógico."
    )
    
    if not active_api_key:
        st.warning("Configure a API Key do Google Gemini na barra lateral para usar esta funcionalidade.")
    else:
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            top_n = st.number_input(
                "Número de arquivos top para análise:",
                min_value=3,
                max_value=20,
                value=5,
                step=1
            )
        
        with col2:
            include_coupling = st.checkbox(
                "Incluir análise de acoplamento",
                value=True
            )
        
        if st.button("Analisar com IA", type="primary"):
            top_files = df.nlargest(top_n, "risk_score").to_dict(orient="records")
            
            data_for_ai = {
                "repository_path": repository_identifier,
                "total_commits_analyzed": num_commits,
                "total_files": total_files,
                "bus_factor": bus_factor,
                "avg_risk_score": float(avg_risk),
                "top_hotspots": top_files
            }
            
            if include_coupling and coupling:
                data_for_ai["logical_coupling"] = coupling[:5]
            
            with st.spinner("Consultando Gemini... (pode levar alguns segundos)"):
                try:
                    analyzer = AIAnalyzer()
                    analysis = analyzer.analyze_health(data_for_ai)
                    st.session_state["last_ai_report"] = analysis
                    
                    st.markdown("---")
                    st.markdown("### Relatório de Análise")
                    st.markdown(analysis)
                    
                except Exception as e:
                    st.error(f"Erro ao consultar a IA: {str(e)}")
                    st.info(
                        "Verifique se:\n"
                        "- A API Key está correta\n"
                        "- Você tem créditos disponíveis no Google AI Studio\n"
                        "- Sua conexão com a internet está ativa"
                    )

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Repo Health AI v2.0"
    "</div>",
    unsafe_allow_html=True
)
