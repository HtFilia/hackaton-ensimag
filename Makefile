.PHONY: help register test web clean

.DEFAULT_GOAL := help

# Auto-detect team from local .team file (written by make register)
TEAM ?= $(shell cat .team 2>/dev/null)
PYTHON := venv/bin/python3

# ══════════════════════════════════════════════════════════════════════════════
#  AIDE
# ══════════════════════════════════════════════════════════════════════════════

help:
	@echo ""
	@echo "  ┌─────────────────────────────────────────────────────────────┐"
	@echo "  │          Hackathon Flash Trading — Carnet d'Ordres          │"
	@echo "  └─────────────────────────────────────────────────────────────┘"
	@echo ""
	@printf "  \033[1;34m▸ COMMANDES\033[0m\n"
	@echo ""
	@printf "    \033[36m%-38s\033[0m %s\n" "make register" "Créer votre équipe et tout configurer"
	@printf "    \033[36m%-38s\033[0m %s\n" "make test" "Lancer les tests (sortie terminal)"
	@printf "    \033[36m%-38s\033[0m %s\n" "make test LEVEL=N" "Tester un palier spécifique (N = 1..6)"
	@printf "    \033[36m%-38s\033[0m %s\n" "make web" "Dashboard live avec résultats auto toutes les 5s"
	@printf "    \033[36m%-38s\033[0m %s\n" "make clean" "Arrêter les processus et nettoyer les caches"
	@echo ""

# ══════════════════════════════════════════════════════════════════════════════
#  COMMANDES ÉTUDIANTS
# ══════════════════════════════════════════════════════════════════════════════

register: ## Enregistrement interactif : équipe, dépendances, template, hooks
	@bash scripts/register.sh

test: ## Lancer les tests publics (sortie terminal uniquement)
	@if [ ! -f venv/bin/python3 ]; then printf "\n  Lancez 'make register' d'abord.\n\n"; exit 1; fi
	@if [ -z "$(TEAM)" ]; then printf "\n  Équipe non définie. Lancez 'make register'.\n\n"; exit 1; fi
	@if [ -n "$(LEVEL)" ]; then \
		$(PYTHON) -m pytest tests/levels/test_level$(LEVEL)_validation.py -v; \
	else \
		$(PYTHON) -m pytest tests/levels/ -v; \
	fi

web: ## Dashboard live : résultats auto toutes les 5s + serveur frontend
	@if [ ! -f venv/bin/python3 ]; then printf "\n  Lancez 'make register' d'abord.\n\n"; exit 1; fi
	@if [ -z "$(TEAM)" ]; then printf "\n  Équipe non définie. Lancez 'make register'.\n\n"; exit 1; fi
	@if [ ! -d "frontend/node_modules" ]; then printf "\n  Modules Node manquants. Relancez 'make register'.\n\n"; exit 1; fi
	@if [ -f .watch.pid ]; then \
		kill $$(cat .watch.pid) 2>/dev/null || true; \
		pkill -P $$(cat .watch.pid) 2>/dev/null || true; \
		rm -f .watch.pid; \
	fi
	@if [ -f .frontend.pid ]; then \
		kill $$(cat .frontend.pid) 2>/dev/null || true; \
		pkill -P $$(cat .frontend.pid) 2>/dev/null || true; \
		rm -f .frontend.pid; \
	fi
	@$(PYTHON) -m src.student.runner --team $(TEAM)
	@(while true; do $(PYTHON) -m src.student.runner --team $(TEAM) >/dev/null 2>&1; sleep 5; done) & echo $$! > .watch.pid
	@(cd frontend && npm run dev -- --open /) & echo $$! > .frontend.pid
	@printf "  \033[36m▸\033[0m Dashboard sur http://localhost:5173 — résultats mis à jour toutes les 5s (make clean pour arrêter)\n"

clean: ## Arrêter les processus en arrière-plan et nettoyer les caches
	@if [ -f .watch.pid ]; then \
		printf "  \033[36m▸\033[0m Arrêt du dashboard (PID $$(cat .watch.pid))...\n"; \
		kill $$(cat .watch.pid) 2>/dev/null || true; \
		pkill -P $$(cat .watch.pid) 2>/dev/null || true; \
		rm -f .watch.pid; \
	fi
	@if [ -f .frontend.pid ]; then \
		printf "  \033[36m▸\033[0m Arrêt du serveur frontend (PID $$(cat .frontend.pid))...\n"; \
		kill $$(cat .frontend.pid) 2>/dev/null || true; \
		pkill -P $$(cat .frontend.pid) 2>/dev/null || true; \
		rm -f .frontend.pid; \
	fi
	@find . -type d -name __pycache__ -not -path './venv/*' -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -not -path './venv/*' -delete 2>/dev/null || true
	@rm -rf .pytest_cache
	@rm -f frontend/public/student-results.json
	@printf "  \033[32m✓\033[0m Nettoyage terminé\n"
