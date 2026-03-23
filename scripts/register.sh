#!/usr/bin/env bash
# scripts/register.sh — Interactive team registration for the hackathon.
# Called by: make register

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
BOLD='\033[1m'
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
RESET='\033[0m'

info()    { printf "  ${CYAN}▸${RESET} %s\n" "$*"; }
success() { printf "  ${GREEN}✓${RESET} %s\n" "$*"; }
warn()    { printf "  ${YELLOW}⚠${RESET}  %s\n" "$*"; }
error()   { printf "  ${RED}✗${RESET} %s\n" "$*" >&2; }
header()  { printf "\n  ${BOLD}%s${RESET}\n\n" "$*"; }

# ── Rollback state ────────────────────────────────────────────────────────────
CREATED_SUBMISSION=""   # path created by this run, removed on error
YAML_BACKUP=""          # backup of teams.yaml, restored on error

cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo ""
        error "Une erreur est survenue. Annulation des modifications..."
        if [ -n "$CREATED_SUBMISSION" ] && [ -d "$CREATED_SUBMISSION" ]; then
            rm -rf "$CREATED_SUBMISSION"
            warn "submissions/ nettoyé"
        fi
        if [ -n "$YAML_BACKUP" ] && [ -f "$YAML_BACKUP" ]; then
            cp "$YAML_BACKUP" config/teams.yaml
            warn "config/teams.yaml restauré"
        fi
        echo ""
    fi
    [ -n "$YAML_BACKUP" ] && rm -f "$YAML_BACKUP"
}
trap cleanup EXIT

# ── Helper: check if team id is in teams.yaml ─────────────────────────────────
team_in_yaml() {
    python3 - "$1" <<'EOF'
import yaml, sys
with open("config/teams.yaml") as f:
    cfg = yaml.safe_load(f)
ids = [t["id"] for t in (cfg.get("teams") or [])]
sys.exit(0 if sys.argv[1] in ids else 1)
EOF
}

# ── Helper: list registered teams (source of truth = teams.yaml) ──────────────
get_registered_teams() {
    python3 - <<'EOF'
import yaml
with open("config/teams.yaml") as f:
    cfg = yaml.safe_load(f)
for t in (cfg.get("teams") or []):
    tid = t["id"]
    if tid not in ("example_team",):
        print(tid)
EOF
}

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo "  ┌─────────────────────────────────────────────────────────────┐"
echo "  │     Hackathon Flash Trading — Enregistrement d'équipe       │"
echo "  └─────────────────────────────────────────────────────────────┘"
echo ""

# ── 1. Python check ───────────────────────────────────────────────────────────
header "1/4 — Vérification de Python"
if ! command -v python3 &>/dev/null; then
    error "python3 est introuvable. Installez Python 3.11+ et relancez."
    exit 1
fi
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
success "Python $PYTHON_VERSION détecté"

# ── 2. Virtual environment + dependencies ─────────────────────────────────────
header "2/4 — Environnement Python"
if [ ! -d "venv" ]; then
    info "Création du virtualenv..."
    python3 -m venv venv
    success "venv/ créé"
else
    success "venv/ déjà présent"
fi

info "Installation des dépendances..."
. venv/bin/activate
pip install --quiet -r requirements.txt
success "Dépendances installées"

# ── 3. Team identification ────────────────────────────────────────────────────
header "3/4 — Identification de l'équipe"

mapfile -t EXISTING_TEAMS < <(get_registered_teams)

TEAM_ID=""
IS_NEW=false

if [ ${#EXISTING_TEAMS[@]} -gt 0 ]; then
    echo "  Des équipes sont déjà enregistrées dans ce dépôt :"
    echo ""
    for i in "${!EXISTING_TEAMS[@]}"; do
        printf "    \033[36m[%d]\033[0m %s\n" "$((i+1))" "${EXISTING_TEAMS[$i]}"
    done
    printf "    \033[36m[N]\033[0m Créer une nouvelle équipe\n"
    echo ""
    printf "  Votre choix : "
    read -r CHOICE </dev/tty

    if [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "${#EXISTING_TEAMS[@]}" ]; then
        TEAM_ID="${EXISTING_TEAMS[$((CHOICE-1))]}"
    elif [[ "$CHOICE" =~ ^[Nn]$ ]]; then
        IS_NEW=true
    else
        error "Choix invalide. Relancez make register."
        exit 1
    fi
else
    IS_NEW=true
fi

if $IS_NEW; then
    while true; do
        printf "  Choisissez un identifiant d'équipe (lettres, chiffres, _) : "
        read -r TEAM_ID </dev/tty

        if [[ ! "$TEAM_ID" =~ ^[a-zA-Z0-9][a-zA-Z0-9_]*$ ]]; then
            error "Identifiant invalide : commencez par une lettre ou un chiffre, puis lettres/chiffres/_"
            continue
        fi

        if team_in_yaml "$TEAM_ID" || [ -d "submissions/$TEAM_ID" ]; then
            error "L'équipe '$TEAM_ID' existe déjà. Choisissez un autre nom."
            continue
        fi

        break
    done
fi

success "Équipe sélectionnée : $TEAM_ID"

# ── 4. Scaffold + config + hook ───────────────────────────────────────────────
header "4/4 — Configuration"

if $IS_NEW; then
    # Ask for members
    echo "  Entrez les noms des membres (un par ligne, ligne vide pour terminer) :"
    echo ""
    MEMBERS=()
    while true; do
        printf "  Membre %d : " "$((${#MEMBERS[@]} + 1))"
        read -r MEMBER </dev/tty
        if [ -z "$MEMBER" ]; then
            [ ${#MEMBERS[@]} -eq 0 ] && { warn "Entrez au moins un membre."; continue; }
            break
        fi
        MEMBERS+=("$MEMBER")
    done
    echo ""

    # Backup yaml before modifying
    YAML_BACKUP=$(mktemp)
    cp config/teams.yaml "$YAML_BACKUP"

    # Copy template
    info "Création de submissions/$TEAM_ID/ ..."
    cp -r submissions/_template "submissions/$TEAM_ID"
    CREATED_SUBMISSION="submissions/$TEAM_ID"
    success "submissions/$TEAM_ID/ créé depuis le template"

    # Append to config/teams.yaml
    info "Ajout dans config/teams.yaml..."
    {
        printf "  - id: %s\n    members:\n" "$TEAM_ID"
        for m in "${MEMBERS[@]}"; do
            printf '      - "%s"\n' "$m"
        done
    } >> config/teams.yaml
    success "Équipe ajoutée dans config/teams.yaml"
else
    success "Dossier submissions/$TEAM_ID/ existant chargé"
fi

# Save team name locally
printf "%s" "$TEAM_ID" > .team
success ".team mis à jour — make test / dev / watch cibleront '$TEAM_ID'"

# Install git pre-commit hook
if [ -d ".git" ]; then
    info "Installation du hook pre-commit..."
    cp scripts/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    success "Hook pre-commit installé"
else
    warn "Pas de dépôt git détecté — hook non installé"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "  ┌─────────────────────────────────────────────────────────────┐"
printf "  │  ${GREEN}✓ Prêt !${RESET} Équipe : %-38s│\n" "$TEAM_ID "
echo "  └─────────────────────────────────────────────────────────────┘"
echo ""
echo "  Prochaines étapes :"
echo ""
printf "    \033[36m%-38s\033[0m %s\n" "make test" "Lancer les tests publics"
printf "    \033[36m%-38s\033[0m %s\n" "make test LEVEL=1" "Tester un palier spécifique"
printf "    \033[36m%-38s\033[0m %s\n" "make web" "Voir votre progression sur le dashboard"
printf "    \033[36m%-38s\033[0m %s\n" "make watch" "Relancer les tests automatiquement (5s)"
echo ""
