"""Inicializa os guardrails do NeMo e registra as actions customizadas."""
from pathlib import Path
from nemoguardrails import LLMRails, RailsConfig

from app.guardrails import actions

_CONFIG_DIR = Path(__file__).parent

_config = RailsConfig.from_path(str(_CONFIG_DIR))
rails = LLMRails(_config)

rails.register_action(actions.detectar_dados_pessoais, "detectar_dados_pessoais")
rails.register_action(actions.verificar_citacao, "verificar_citacao")
rails.register_action(actions.verificar_artigos_existem, "verificar_artigos_existem")
rails.register_action(actions.verificar_disclaimer, "verificar_disclaimer")
rails.register_action(actions.adicionar_disclaimer, "adicionar_disclaimer")
rails.register_action(actions.adicionar_aviso_sem_citacao, "adicionar_aviso_sem_citacao")
