from pydriller import Repository
from radon.complexity import cc_visit
from collections import defaultdict
import os
import itertools

class GitCollector:
    def __init__(self, repo_path: str, limit_commits: int = 100):
        self.repo_path = repo_path
        self.limit = limit_commits
        self.coupling_data = defaultdict(int) 
        self.total_commits_analyzed = 0
        self.all_files_metrics = {}

    def should_ignore(self, filename: str, rel_path: str = None) -> bool:
        IGNORED_FILES = {
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'composer.lock', 
            'Gemfile.lock', 'poetry.lock', 'mix.lock'
        }
        IGNORED_EXTENSIONS = (
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.css', '.map', '.min.js', '.json', '.xml'
        )
        
        if not filename:
            return True
        if filename in IGNORED_FILES:
            return True
        if filename.lower().endswith(IGNORED_EXTENSIONS):
            return True
        
        return False

    def collect_metrics(self):
        print(f"Analisando os últimos {self.limit} commits em {self.repo_path}...")
        
        churn_data = defaultdict(int)
        author_data = defaultdict(lambda: defaultdict(int))
        file_paths = {}
        seen_files = set()

        repo = Repository(self.repo_path, order='reverse')
        
        commit_count = 0
        mass_update_threshold = 50
        
        for commit in repo.traverse_commits():
            if commit_count >= self.limit:
                break
            commit_count += 1
            self.total_commits_analyzed += 1
            
            current_commit_files = []

            for modified_file in commit.modified_files:
                filename = modified_file.filename
                rel_path = modified_file.new_path
                
                if self.should_ignore(filename, rel_path):
                    continue

                if rel_path:
                    file_paths[filename] = rel_path

                churn = modified_file.added_lines + modified_file.deleted_lines
                churn_data[filename] += churn
                author_data[filename][commit.author.name] += 1
                seen_files.add(filename)
                
                current_commit_files.append(filename)

            if len(current_commit_files) > mass_update_threshold:
                continue
            
            if 1 < len(current_commit_files) <= mass_update_threshold:
                sorted_files = sorted(current_commit_files)
                for file_a, file_b in itertools.combinations(sorted_files, 2):
                    self.coupling_data[(file_a, file_b)] += 1

        print(f"Commits: {self.total_commits_analyzed}")
        print(f"Arquivos: {len(seen_files)}")

        hotspots = []
        for filename in seen_files:
            full_path = None
            if filename in file_paths:
                 full_path = os.path.join(self.repo_path, file_paths[filename])
            
            if not full_path or not os.path.exists(full_path):
                full_path = self._find_file(filename)

            if full_path and os.path.exists(full_path):
                complexity = 1
                if filename.endswith('.py'):
                    complexity = self._calc_complexity(full_path)

                total_churn = churn_data[filename]
                risk_score = total_churn * complexity
                
                hotspot = {
                    "file": filename,
                    "churn": total_churn,
                    "complexity": complexity,
                    "risk_score": risk_score,
                    "top_authors": dict(sorted(author_data[filename].items(), key=lambda x: x[1], reverse=True)[:2])
                }
                hotspots.append(hotspot)
                self.all_files_metrics[filename] = hotspot

        return sorted(hotspots, key=lambda x: x['risk_score'], reverse=True)[:10]

    def get_coupling_analysis(self, min_shared_commits=3):
        """
        Retorna os pares de arquivos com maior acoplamento lógico.
        min_shared_commits: Mínimo de vezes que devem ter mudado juntos para aparecer.
        """
        results = []
        for (file_a, file_b), count in self.coupling_data.items():
            if count >= min_shared_commits:
                strength = (count / self.total_commits_analyzed) * 100 
                
                results.append({
                    "file_a": file_a,
                    "file_b": file_b,
                    "shared_commits": count,
                    "strength": f"{strength:.1f}%"
                })
        
        return sorted(results, key=lambda x: x['shared_commits'], reverse=True)[:10]

    def get_logical_coupling(self, min_shared_commits: int = 2):
        """
        Retorna dados formatados para visualização em grafo de acoplamento lógico.
        """

        def get_file_color(filename: str) -> str:
            ext = os.path.splitext(filename)[1].lower()
            color_map = {
                '.py': '#4B8BFF',
                '.js': '#FFD700',
                '.ts': '#3178C6',    
                '.jsx': '#FFD700',     
                '.tsx': '#3178C6',     
                '.java': '#FF6B35',    
                '.cpp': '#00599C',     
                '.c': '#A8B9CC',       
                '.go': '#00ADD8',      
                '.rs': '#CE422B',      
                '.rb': '#CC342D',      
                '.php': '#777BB4',     
            }
            return color_map.get(ext, '#CCCCCC')
        
        nodes = {}
        edges = []
        
        for (file_a, file_b), count in self.coupling_data.items():
            if count >= min_shared_commits:
                for file in [file_a, file_b]:
                    if file not in nodes:
                        metrics = self.all_files_metrics.get(file, {})
                        risk_score = metrics.get('risk_score', 0)
                        
                        # Tamanho do nó - risk_score
                        min_size, max_size = 15, 50
                        all_risks = [m.get('risk_score', 0) for m in self.all_files_metrics.values()]
                        max_risk = max(all_risks) if all_risks else 1
                        node_size = min_size + (risk_score / max_risk * (max_size - min_size)) if max_risk > 0 else min_size
                        
                        nodes[file] = {
                            'id': file,
                            'label': file,
                            'title': f"{file}\nRisk Score: {risk_score:.0f}",
                            'size': node_size,
                            'color': get_file_color(file)
                        }
                
                edges.append({
                    'source': file_a,
                    'target': file_b,
                    'weight': count,
                    'title': f"{count} commits compartilhados"
                })
        
        nodes_list = list(nodes.values())
        
        stats = {
            'total_nodes': len(nodes_list),
            'total_edges': len(edges),
            'max_coupling_strength': max([e['weight'] for e in edges]) if edges else 0,
            'avg_coupling_strength': sum([e['weight'] for e in edges]) / len(edges) if edges else 0
        }
        
        return {
            'nodes': nodes_list,
            'edges': edges,
            'stats': stats
        }


    def _calc_complexity(self, file_path):
        """Calcula Complexidade Ciclomática (apenas Python)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                return sum([block.complexity for block in cc_visit(code)])
        except Exception:
            return 1 

    def _find_file(self, name):
        for root, dirs, files in os.walk(self.repo_path):
            if name in files:
                return os.path.join(root, name)
        return None