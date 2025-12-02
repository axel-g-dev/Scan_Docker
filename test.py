import sys
import os

# --- COULEURS (Codes ANSI standards pour Linux) ---
# Pas besoin de librairie externe, c'est natif.
C_RED     = "\033[91m"
C_GREEN   = "\033[92m"
C_YELLOW  = "\033[93m"
C_BLUE    = "\033[94m"
C_RESET   = "\033[0m"

def print_log(type_log, message):
    """Fonction utilitaire pour afficher des messages colorés."""
    if type_log == "FAIL":
        print(f"{C_RED}[FAIL] {message}{C_RESET}")
    elif type_log == "WARN":
        print(f"{C_YELLOW}[WARN] {message}{C_RESET}")
    elif type_log == "OK":
        print(f"{C_GREEN}[PASS] {message}{C_RESET}")
    elif type_log == "INFO":
        print(f"{C_BLUE}[INFO] {message}{C_RESET}")

# --- FONCTIONS DE VÉRIFICATION ---

def scan_dockerfile(lignes):
    errors = 0
    
    # 1. Vérification de l'utilisateur (Ne pas être root)
    user_found = False
    for ligne in lignes:
        if ligne.strip().upper().startswith("USER"):
            user_found = True
    
    if user_found:
        print_log("OK", "Instruction USER présente.")
    else:
        print_log("FAIL", "Aucun USER défini (Le conteneur tourne en root).")
        errors += 1

    # 2. Vérification des versions (Pas de latest)
    latest_found = False
    for ligne in lignes:
        if ligne.strip().upper().startswith("FROM"):
            if "latest" in ligne.lower() or ":" not in ligne:
                latest_found = True
                print_log("WARN", f"Tag 'latest' détecté : {ligne.strip()}")
    
    if not latest_found:
        print_log("OK", "Image de base bien versionnée.")

    return errors

def scan_compose(lignes):
    errors = 0
    
    # 1. Recherche de mots de passe en clair
    keywords = ["PASSWORD", "SECRET", "KEY", "TOKEN"]
    for i, ligne in enumerate(lignes):
        ligne_clean = ligne.strip().upper()
        # On ignore les commentaires
        if ligne_clean.startswith("#"): continue
        
        for key in keywords:
            # On cherche motif "CLE: VALEUR" ou "CLE=VALEUR"
            if key in ligne_clean and (":" in ligne or "=" in ligne):
                print_log("FAIL", f"Secret potentiel (Ligne {i+1}) : {ligne.strip()}")
                errors += 1
                break # On ne flag pas 2 fois la même ligne

    return errors

# --- MOTEUR PRINCIPAL ---

def main():
    path = "."
    if len(sys.argv) > 1:
        path = sys.argv[1]
    
    print(f"{C_BLUE}--- DÉBUT DE L'AUDIT DE SÉCURITÉ ---{C_RESET}")
    print(f"Dossier cible : {os.path.abspath(path)}\n")

    files_scanned = 0
    total_errors = 0

    # On parcourt le dossier récursivement (os.walk)
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            filename = file.lower()
            
            # On lit le fichier seulement si c'est un Dockerfile ou Compose
            if filename == "dockerfile" or "docker-compose" in filename:
                print(f"{C_BLUE}Analyse de : {file_path}{C_RESET}")
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.readlines()
                        
                    if filename == "dockerfile":
                        total_errors += scan_dockerfile(content)
                    else:
                        total_errors += scan_compose(content)
                        
                    files_scanned += 1
                    print("-" * 40) # Séparateur visuel
                    
                except Exception as e:
                    print_log("FAIL", f"Impossible de lire le fichier : {e}")

    # Résumé final
    print(f"\n{C_BLUE}--- RAPPORT TERMINÉ ---{C_RESET}")
    print(f"Fichiers analysés : {files_scanned}")
    if total_errors > 0:
        print(f"{C_RED}Résultat : {total_errors} problèmes de sécurité trouvés.{C_RESET}")
        sys.exit(1) # Code erreur pour la CI/CD
    else:
        print(f"{C_GREEN}Résultat : Tout semble correct.{C_RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
