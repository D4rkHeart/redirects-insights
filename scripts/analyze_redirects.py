import os
import re

# Dictionnaire pour stocker les statistiques
stats = {
    'total': 0,
    '301': 0,
    '302': 0,
    'regex': 0,
    'subdomain_to_path': 0,
    'others': 0
}

# Fonction pour analyser un fichier .htaccess
def analyze_htaccess(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if re.match(r'^\s*RewriteRule', line):
                stats['total'] += 1
                if '301' in line:
                    stats['301'] += 1
                elif '302' in line:
                    stats['302'] += 1
                elif re.search(r'\(\.\*\)', line):
                    stats['regex'] += 1
                elif re.search(r'\bsubdomain\b', line):
                    stats['subdomain_to_path'] += 1
                else:
                    stats['others'] += 1

# Parcourir les répertoires et analyser les fichiers .htaccess
for root, dirs, files in os.walk('/data'):
    for file in files:
        if file == '.htaccess':
            analyze_htaccess(os.path.join(root, file))

# Générer le rapport en Markdown
output_path = os.environ.get('ANALYSIS_OUTPUT', '/data/output.md')
with open(output_path, 'w') as output_file:
    output_file.write('# Rapport d\'analyse des redirections\n\n')
    output_file.write(f"**Total des redirections :** {stats['total']}\n\n")
    output_file.write('## Détails par type de redirection\n')
    output_file.write(f"- 301 (Permanentes) : {stats['301']}\n")
    output_file.write(f"- 302 (Temporaires) : {stats['302']}\n")
    output_file.write(f"- Regex : {stats['regex']}\n")
    output_file.write(f"- Sous-domaine vers chemin : {stats['subdomain_to_path']}\n")
    output_file.write(f"- Autres : {stats['others']}\n")
