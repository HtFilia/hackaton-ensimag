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
	@printf "    \033[36m%-38s\033[0m %s\n" "make test" "Lancer les tests (et garder à jour le dashboard)"
	@printf "    \033[36m%-38s\033[0m %s\n" "make test LEVEL=N" "Tester un palier spécifique (N = 1..6)"
	@printf "    \033[36m%-38s\033[0m %s\n" "make web" "Ouvrir le dashboard dans le navigateur"
	@printf "    \033[36m%-38s\033[0m %s\n" "make clean" "Arrêter les processus et nettoyer les caches"
	@echo ""

# ══════════════════════════════════════════════════════════════════════════════
#  COMMANDES ÉTUDIANTS
# ══════════════════════════════════════════════════════════════════════════════

register: ## Enregistrement interactif : équipe, dépendances, template, hooks
	@bash scripts/register.sh

test: ## Lancer les tests publics et démarrer le dashboard en arrière-plan
	@# Redémarrer le processus de mise à jour du dashboard si déjà actif
	@if [ -f .watch.pid ]; then \
		kill $$(cat .watch.pid) 2>/dev/null || true; \
		pkill -P $$(cat .watch.pid) 2>/dev/null || true; \
		rm -f .watch.pid; \
	fi
	@# Lancer les tests
	@if [ -n "$(LEVEL)" ]; then \
		$(PYTHON) -m pytest tests/levels/test_level$(LEVEL)_validation.py -v; \
	else \
		$(PYTHON) -m pytest tests/levels/ -v; \
	fi
	@# Démarrer la mise à jour automatique du dashboard en arrière-plan
	@if [ -n "$(TEAM)" ]; then \
		(while true; do $(PYTHON) -m src.student.runner --team $(TEAM) >/dev/null 2>&1; sleep 5; done) & \
		echo $$! > .watch.pid; \
		printf "\n  \033[36m▸\033[0m Dashboard mis à jour toutes les 5s en arrière-plan (make clean pour arrêter)\n\n"; \
	fi

web: ## Calculer les résultats et ouvrir le dashboard étudiant
	@if [ -z "$(TEAM)" ]; then \
		echo ""; \
		echo "  Équipe non définie. Lancez 'make register' ou passez TEAM=nom."; \
		echo ""; \
		exit 1; \
	fi
	@# Arrêter le serveur frontend si déjà actif
	@if [ -f .frontend.pid ]; then \
		kill $$(cat .frontend.pid) 2>/dev/null || true; \
		pkill -P $$(cat .frontend.pid) 2>/dev/null || true; \
		rm -f .frontend.pid; \
	fi
	$(PYTHON) -m src.student.runner --team $(TEAM)
	@(cd frontend && npm run dev -- --open /) & echo $$! > .frontend.pid
	@printf "  \033[36m▸\033[0m Dashboard lancé sur http://localhost:5173 (make clean pour arrêter)\n"

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
