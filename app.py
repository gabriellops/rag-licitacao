"""Entrypoint esperado pelo Hugging Face Spaces (SDK Gradio).
O app de verdade está em ui/gradio_app.py — mantemos a estrutura de pastas
do projeto e só expomos o objeto `demo` aqui na raiz.
"""
from ui.gradio_app import demo

if __name__ == "__main__":
    demo.launch(show_api=False)
