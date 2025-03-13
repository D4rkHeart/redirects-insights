import os
import json
import requests
from collections import defaultdict

def load_json_files(input_folder):
    data = {}
    try:
        for file in os.listdir(input_folder):
            if file.endswith(".json"):
                file_path = os.path.join(input_folder, file)
                with open(file_path, "r") as f:
                    data[file] = json.load(f)
    except FileNotFoundError:
        print(f"X Erreur : Le répertoire spécifié '{input_folder}' est introuvable.")
    except Exception as e:
        print(f"X Une erreur s'est produite lors du chargement des fichiers : {e}")
    return data

def extract_url_parts(redirect_entry):
    base_url = "https://inside.epfl.ch" #THIS IS VERY USELESS. Todo : make it generic or 12 factored...
    data_parts = redirect_entry["data"].split(" ")

    if len(data_parts) < 2:
        return None, None

    origin_path = data_parts[0]
    destination_url = data_parts[1]
    origin_url = f"{base_url}{origin_path}"

    return origin_url, destination_url

def detect_redundant_redirects(redirects):
    redirect_map = {}

    for redirect in redirects:
        origin_url, destination_url = extract_url_parts(redirect)
        if origin_url and destination_url:
            redirect_map[origin_url] = destination_url

    redundant_redirects = set()
    checked_urls = set()

    for origin, destination in redirect_map.items():
        if destination in checked_urls:
            redundant_redirects.add(origin)
        checked_urls.add(destination)

    return redundant_redirects

def test_redirect(url):
    try:
        response = requests.get(url, allow_redirects=True, timeout=5)
        return response.status_code
    except requests.RequestException:
        return None

def validate_redirects(input_folder, output_valid, output_invalid):
    os.makedirs(output_valid, exist_ok=True)
    os.makedirs(output_invalid, exist_ok=True)

    data = load_json_files(input_folder)
    valid_redirects = defaultdict(lambda: defaultdict(list))
    invalid_redirects = defaultdict(lambda: defaultdict(list))

    total_redirects = 0
    tested_redirects = 0
    valid_count = 0
    invalid_count = 0
    redundant_count = 0

    for file, categories in data.items():
        print(f"\n- Analyse du fichier : {file}")
        
        all_redirects = [r for redirects in categories.values() for r in redirects]
        redundant_redirect_set = detect_redundant_redirects(all_redirects)

        for category, redirects in categories.items():
            for redirect in redirects:
                total_redirects += 1
                origin_url, expected_destination = extract_url_parts(redirect)

                if not origin_url or not expected_destination:
                    print(f"- Impossible d'extraire une URL valide depuis {redirect} (Fichier: {file})")
                    continue

                if origin_url in redundant_redirect_set:
                    print(f"- Redirection redondante ignorée : {origin_url} → {expected_destination}")
                    redundant_count += 1
                    continue

                tested_redirects += 1
                status_code = test_redirect(expected_destination)

                if status_code and status_code != 404:
                    print(f"O Redirection valide : {origin_url} → {expected_destination} (Code {status_code})")
                    valid_redirects[file][category].append(redirect)
                    valid_count += 1
                else:
                    print(f"X Redirection invalide : {origin_url} → {expected_destination} (Code {status_code})")
                    invalid_redirects[file][category].append(redirect)
                    invalid_count += 1

    for folder, data_dict in [("valid", valid_redirects), ("invalid", invalid_redirects)]:
        output_folder = output_valid if folder == "valid" else output_invalid
        for file, categories in data_dict.items():
            output_file = os.path.join(output_folder, file)
            with open(output_file, "w") as f:
                json.dump(categories, f, indent=4)

    print("\n- Résumé de l'analyse :")
    print(f"- Nombre total de redirections analysées : {total_redirects}")
    print(f"- Nombre total de redirections testées : {tested_redirects}")
    print(f"O Nombre total de redirections valides : {valid_count}")
    print(f"X Nombre total de redirections invalides : {invalid_count}")
    print(f"- Nombre total de redirections redondantes ignorées : {redundant_count}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    input_folder = os.path.join(script_dir, "../data/per_directory")
    output_valid = os.path.join(script_dir, "../data/valid_redirects")
    output_invalid = os.path.join(script_dir, "../data/invalid_redirects")

    input_folder = os.path.abspath(input_folder)
    output_valid = os.path.abspath(output_valid)
    output_invalid = os.path.abspath(output_invalid)

    if not os.path.exists(input_folder):
        print(f"X Erreur : Le dossier d'entrée '{input_folder}' n'existe pas.")
    else:
        validate_redirects(input_folder, output_valid, output_invalid)
        print(f"\nO Fichiers des redirections valides : {output_valid}")
        print(f"X Fichiers des redirections invalides : {output_invalid}")
