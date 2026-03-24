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

# ── Helper: list registered teams from teams.yaml ─────────────────────────────
get_registered_teams() {
    python3 - <<'EOF'
import yaml
with open("config/teams.yaml") as f:
    cfg = yaml.safe_load(f)
for t in (cfg.get("teams") or []):
    print(t["id"])
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

# ── 3. Sélection de l'équipe ──────────────────────────────────────────────────
header "3/4 — Identification de l'équipe"

# Fetch remote branches so we can checkout team branches
if git remote get-url origin &>/dev/null; then
    info "Récupération des branches distantes..."
    git fetch origin --quiet 2>/dev/null || warn "Impossible de contacter le serveur git"
fi

mapfile -t AVAILABLE_TEAMS < <(get_registered_teams)

if [ ${#AVAILABLE_TEAMS[@]} -eq 0 ]; then
    error "Aucune équipe disponible dans config/teams.yaml."
    error "Contactez l'organisateur pour que votre équipe soit créée."
    exit 1
fi

echo "  Équipes disponibles :"
echo ""
for i in "${!AVAILABLE_TEAMS[@]}"; do
    printf "    ${CYAN}[%d]${RESET} %s\n" "$((i+1))" "${AVAILABLE_TEAMS[$i]}"
done
echo ""
printf "  Votre équipe [1-%d] : " "${#AVAILABLE_TEAMS[@]}"
read -r CHOICE </dev/tty

if [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "${#AVAILABLE_TEAMS[@]}" ]; then
    TEAM_ID="${AVAILABLE_TEAMS[$((CHOICE-1))]}"
else
    error "Choix invalide. Relancez make register."
    exit 1
fi

success "Équipe sélectionnée : $TEAM_ID"

# ── 4. Basculement sur la branche de l'équipe ─────────────────────────────────
header "4/4 — Configuration"

if [ -d ".git" ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

    if [ "$CURRENT_BRANCH" = "$TEAM_ID" ]; then
        success "Déjà sur la branche $TEAM_ID"
    else
        info "Passage sur la branche $TEAM_ID..."
        if git show-ref --verify --quiet "refs/heads/$TEAM_ID"; then
            # Local branch already exists
            git checkout "$TEAM_ID"
        elif git show-ref --verify --quiet "refs/remotes/origin/$TEAM_ID"; then
            # Track remote branch
            git checkout -b "$TEAM_ID" "origin/$TEAM_ID"
        else
            error "La branche '$TEAM_ID' n'existe pas sur origin."
            error "Contactez l'organisateur pour qu'il lance : make -f Makefile.admin scaffold TEAM=$TEAM_ID"
            exit 1
        fi
        success "Sur la branche $TEAM_ID"
    fi

    # Install git hooks
    info "Installation des hooks git..."
    cp scripts/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    cp scripts/pre-push .git/hooks/pre-push
    chmod +x .git/hooks/pre-push
    success "Hooks pre-commit et pre-push installés"
else
    warn "Pas de dépôt git détecté — hooks non installés"
fi

# Save team name locally
printf "%s" "$TEAM_ID" > .team
success ".team mis à jour — make test / make web cibleront '$TEAM_ID'"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "  ┌─────────────────────────────────────────────────────────────┐"
printf "  │  ${GREEN}✓ Prêt !${RESET} Équipe : %-38s│\n" "$TEAM_ID "
echo "  └─────────────────────────────────────────────────────────────┘"
echo ""
echo "  Prochaines étapes :"
echo ""
printf "    ${CYAN}%-38s${RESET} %s\n" "make test" "Lancer les tests publics"
printf "    ${CYAN}%-38s${RESET} %s\n" "make test LEVEL=1" "Tester un palier spécifique"
printf "    ${CYAN}%-38s${RESET} %s\n" "make web" "Voir votre progression sur le dashboard"
printf "    ${CYAN}%-38s${RESET} %s\n" "git push origin $TEAM_ID" "Pousser vos changements"
echo ""
