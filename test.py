import sys
import os
import argparse
from typing import List, Tuple

# --- CONFIGURATION VISUELLE ---
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

# --- LE COEUR DU PROGRAMME (MODULE) ---
class DockerAuditor:
    def __init__(self, target_path: str, verbose: bool = False):
        self.target_path = target_path
        self.verbose = verbose
        self.files_scanned = 0
        self.total_errors = 0
        self.scanned_files_list = []

    def _log(self, level: str, message: str):
        """Gestionnaire de logs centralisé."""
        if level == "FAIL":
            print(f"{Colors.RED}[FAIL] {message}{Colors.RESET}")
        elif level == "WARN":
            print(f"{Colors.YELLOW}[WARN] {message}{Colors.RESET}")
        elif level == "OK":
            if self.verbose: # On affiche les OK seulement si verbose est activé
                print(f"{Colors.GREEN}[OK] {message}{Colors.RESET}")
        elif level == "INFO":
            print(f"{Colors.BLUE}[INFO] {message}{Colors.RESET}")
        elif level == "DEBUG":
            if self.verbose:
                print(f"[DEBUG] {message}")

    def _check_line_skip(self, line: str) -> bool:
        """Vérifie si la ligne doit être ignorée (commentaires ou # nosec)."""
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("#"):
            return True
        if "# nosec" in line.lower():
            return True
        return False

    def _analyze_dockerfile(self, content: List[str]) -> int:
        errors = 0
        user_found = False
        
        for i, line in enumerate(content):
            if self._check_line_skip(line): continue

            # Règle 1: USER
            if line.strip().upper().startswith("USER"):
                user_found = True
            
            # Règle 2: Latest
            if line.strip().upper().startswith("FROM"):
                if "latest" in line.lower() or ":" not in line:
                    self._log("WARN", f"Ligne {i+1}: Tag 'latest' ou manquant -> {line.strip()}")

        if not user_found:
            self._log("FAIL", "Aucun USER défini (Risque Root).")
            errors += 1
        else:
            self._log("OK", "USER est bien défini.")

        return errors

    def _analyze_compose(self, content: List[str]) -> int:
        errors = 0
        keywords = ["PASSWORD", "SECRET", "KEY", "TOKEN", "MYSQL_ROOT_PASSWORD"]
        
        for i, line in enumerate(content):
            if self._check_line_skip(line): continue

            # Règle 3: Secrets en clair
            line_upper = line.upper()
            for key in keywords:
                if key in line_upper and (":" in line or "=" in line):
                    self._log("FAIL", f"Ligne {i+1}: Secret potentiel détecté -> {line.strip()}")
                    errors += 1
                    break
        return errors

    def run_scan(self):
        """Lance le scan récursif."""
        self._log("INFO", f"Démarrage de l'audit sur : {os.path.abspath(self.target_path)}")

        if not os.path.exists(self.target_path):
            self._log("FAIL", "Le dossier cible n'existe pas.")
            return False

        # Parcours du dossier
        for root, _, files in os.walk(self.target_path):
            for file in files:
                file_lower = file.lower()
                
                # Détection des fichiers cibles
                is_dockerfile = (file_lower == "dockerfile")
                is_compose = ("docker-compose" in file_lower and file_lower.endswith((".yml", ".yaml")))

                if is_dockerfile or is_compose:
                    full_path = os.path.join(root, file)
                    self._log("INFO", f"Analyse de : {full_path}")
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.readlines()

                        file_errors = 0
                        if is_dockerfile:
                            file_errors = self._analyze_dockerfile(content)
                        elif is_compose:
                            file_errors = self._analyze_compose(content)

                        self.total_errors += file_errors
                        self.files_scanned += 1
                        self.scanned_files_list.append(full_path)

                    except Exception as e:
                        self._log("FAIL", f"Erreur lecture fichier : {e}")

        self._print_report()
        return self.total_errors == 0 and self.files_scanned > 0

    def _print_report(self):
        """Affiche le résumé final."""
        print("-" * 50)
        if self.files_scanned == 0:
            self._log("WARN", "Aucun fichier de configuration Docker trouvé !")
            print(f"{Colors.YELLOW}Conseil : Vérifiez que vous êtes dans le bon dossier.{Colors.RESET}")
        else:
            print(f"Fichiers scannés : {self.files_scanned}")
            if self.total_errors > 0:
                print(f"{Colors.RED}RÉSULTAT : ÉCHEC ({self.total_errors} problèmes trouvés){Colors.RESET}")
            else:
                print(f"{Colors.GREEN}RÉSULTAT : SUCCÈS (Aucun problème critique){Colors.RESET}")

# --- POINT D'ENTRÉE (CLI) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit de sécurité Docker simple.")
    parser.add_argument("path", nargs='?', default=".", help="Chemin du dossier à scanner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Afficher les détails (debug)")
    
    args = parser.parse_args()

    # Instanciation de la classe et lancement
    auditor = DockerAuditor(args.path, verbose=args.verbose)
    success = auditor.run_scan()

    # Code de sortie pour CI/CD (0 = OK, 1 = Erreur)
    sys.exit(0 if success else 1)
