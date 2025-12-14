from pydriller import Repository
from radon.complexity import cc_visit
from collections import defaultdict
import os

class GitCollector:
    def __init__(self, repo_path: str, limit_commits: int = 100):
        self.repo_path = repo_path
        self.limit = limit_commits

    def collect_metrics(self):
        print(f"📡 Analisando os últimos {self.limit} commits em {self.repo_path}...")
        
        churn_data = defaultdict(int)
        author_data = defaultdict(lambda: defaultdict(int))
        file_paths = {}
        seen_files = set()

        IGNORED_FILES = {
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'composer.lock', 
            'Gemfile.lock', 'poetry.lock', 'mix.lock'
        }
        IGNORED_EXTENSIONS = (
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', 
            '.css', '.map', '.min.js', '.json', '.xml'
        )

        repo = Repository(self.repo_path, order='reverse')
        
        commit_count = 0
        commits_analyzed = 0
        
        for commit in repo.traverse_commits():
            if commit_count >= self.limit:
                break
            commit_count += 1
            commits_analyzed += 1
            
            for modified_file in commit.modified_files:
                filename = modified_file.filename
                rel_path = modified_file.new_path
                
                if not filename: 
                    continue

                if filename in IGNORED_FILES:
                    continue
                if filename.lower().endswith(IGNORED_EXTENSIONS):
                    continue

                if rel_path:
                    file_paths[filename] = rel_path

                churn = modified_file.added_lines + modified_file.deleted_lines
                churn_data[filename] += churn
                
                author_data[filename][commit.author.name] += 1
                seen_files.add(filename)

        print(f"📊 Commits analisados: {commits_analyzed}")
        print(f"📂 Arquivos únicos relevantes: {len(seen_files)}")

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
                
                hotspots.append({
                    "file": filename,
                    "churn": total_churn,
                    "complexity": complexity,
                    "risk_score": risk_score,
                    "top_authors": dict(sorted(author_data[filename].items(), key=lambda x: x[1], reverse=True)[:2])
                })

        return sorted(hotspots, key=lambda x: x['risk_score'], reverse=True)[:10]

    def _calc_complexity(self, file_path):
        """Calcula Complexidade Ciclomática (apenas Python)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                return sum([block.complexity for block in cc_visit(code)])
        except Exception:
            return 1 

    def _find_file(self, name):
        """Busca recursiva caso o path do git não bata com o sistema de arquivos"""
        for root, dirs, files in os.walk(self.repo_path):
            if name in files:
                return os.path.join(root, name)
        return None