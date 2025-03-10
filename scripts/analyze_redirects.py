import os
import paramiko
import re
import json
from collections import defaultdict

def create_ssh_client(host, port, user):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=user)
    return client

def find_htaccess_files(ssh_client, remote_path):
    stdin, stdout, stderr = ssh_client.exec_command(f'find {remote_path} -type f -name ".htaccess" ! -path "*/.snapshot/*"')
    return stdout.read().decode().splitlines()

def extract_parent_directory(path):
    parts = path.strip("/").split("/")
    if "subdomain" in parts:
        return "subdomains_redirect"
    return parts[-2] if len(parts) > 1 else parts[-1]

def parse_htaccess(ssh_client, htaccess_files):
    per_directory = defaultdict(lambda: defaultdict(list))
    subdomains_redirects = defaultdict(lambda: defaultdict(list))
    wordpress_blocks = defaultdict(list)
    debug_info = {"total_htaccess": 0, "total_lines_processed": 0, "total_redirects": 0}

    for file in htaccess_files:
        parent_dir = extract_parent_directory(file)
        stdin, stdout, stderr = ssh_client.exec_command(f'cat "{file}"')
        lines = stdout.read().decode().splitlines()
        debug_info["total_htaccess"] += 1

        inside_wordpress_block = False
        wordpress_block = []  

        for line in lines:
            line = line.strip()
            debug_info["total_lines_processed"] += 1

            if not line or line.startswith("#"):
                continue

            if re.search(r"(?i)<IfModule", line):
                inside_wordpress_block = True
                wordpress_block.append(line)
                continue  
            
            if inside_wordpress_block:
                wordpress_block.append(line)
                if re.search(r"(?i)</IfModule>", line):
                    inside_wordpress_block = False
                    wordpress_blocks[parent_dir].append({"location": file, "data": wordpress_block})
                    wordpress_block = []
                continue

            rule_data = re.sub(r"(?i)Redirect\s+\d{3}\s+", "", line)
            rule_data = re.sub(r"(?i)RewriteRule\s+", "", rule_data)
            rule_data = rule_data.strip()

            if re.search(r"(?i)Redirect\s+301|RewriteRule.*\[R=301\]", line):
                if parent_dir == "subdomains_redirect":
                    subdomains_redirects[parent_dir]["301 Permanent"].append({"location": file, "data": rule_data})
                else:
                    per_directory[parent_dir]["301 Permanent"].append({"location": file, "data": rule_data})
                debug_info["total_redirects"] += 1
            elif re.search(r"(?i)Redirect\s+302|RewriteRule.*\[R=302\]", line):
                if parent_dir == "subdomains_redirect":
                    subdomains_redirects[parent_dir]["302 Temporary"].append({"location": file, "data": rule_data})
                else:
                    per_directory[parent_dir]["302 Temporary"].append({"location": file, "data": rule_data})
                debug_info["total_redirects"] += 1
            elif re.search(r"(?i)RedirectMatch", line):
                if parent_dir == "subdomains_redirect":
                    subdomains_redirects[parent_dir]["RedirectMatch"].append({"location": file, "data": rule_data})
                else:
                    per_directory[parent_dir]["RedirectMatch"].append({"location": file, "data": rule_data})
                debug_info["total_redirects"] += 1
            elif re.search(r"(?i)RewriteRule.*\[R=(301|302)\]", line):
                if parent_dir == "subdomains_redirect":
                    subdomains_redirects[parent_dir]["RewriteRules"].append({"location": file, "data": rule_data})
                debug_info["total_redirects"] += 1

    return per_directory, subdomains_redirects, wordpress_blocks, debug_info

def save_json(data, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for directory, categories in data.items():
        output_file = os.path.join(output_folder, f"{directory}.json")
        with open(output_file, "w") as f:
            json.dump(categories, f, indent=4)

def save_summary(per_directory, output_file):
    with open(output_file, "w") as f:
        f.write("# Nombre de Redirections par Dossier\n\n")
        total_redirects = 0
        for directory, categories in per_directory.items():
            f.write(f"## {directory}\n")
            for category, rules in categories.items():
                count = len(rules)
                total_redirects += count
                f.write(f"- **{category}** : {count} redirections\n")
            f.write("\n")
        f.write(f"**Total général de redirections détectées : {total_redirects}**\n")

def save_debug_info(debug_info, output_file):
    with open(output_file, "w") as f:
        f.write("# Debug du Script d'Analyse\n\n")
        f.write(f"- **Nombre total de fichiers .htaccess trouvés** : {debug_info['total_htaccess']}\n")
        f.write(f"- **Nombre total de lignes analysées** : {debug_info['total_lines_processed']}\n")
        f.write(f"- **Nombre total de redirections détectées** : {debug_info['total_redirects']}\n")

if __name__ == "__main__":
    ssh_host = os.getenv('SSH_HOST')
    ssh_port = int(os.getenv('SSH_PORT', 22))
    ssh_user = os.getenv('SSH_USER')
    remote_path = os.getenv('REMOTE_PATH', '/srv/')
    output_folder_directory = "/data/per_directory"
    output_subdomains = "/data/subdomains_redirects.json"
    output_wordpress = "/data/wordpress_blocks.json"
    output_summary = "/data/summary.md"
    output_debug = "/data/debug.md"

    ssh_client = create_ssh_client(ssh_host, ssh_port, ssh_user)
    htaccess_files = find_htaccess_files(ssh_client, remote_path)
    per_directory, subdomains_redirects, wordpress_blocks, debug_info = parse_htaccess(ssh_client, htaccess_files)
    ssh_client.close()

    save_json(per_directory, output_folder_directory)
    save_json(subdomains_redirects, output_subdomains)
    save_json(wordpress_blocks, output_wordpress)
    save_summary(per_directory, output_summary)
    save_debug_info(debug_info, output_debug)

    print(f"Structure JSON des RewriteRules et redirections : {output_folder_directory}")
    print(f"Redirections Subdomains : {output_subdomains}")
    print(f"Blocs WordPress : {output_wordpress}")
    print(f"Rapport des redirections : {output_summary}")
    print(f"Fichier de debug : {output_debug}")
