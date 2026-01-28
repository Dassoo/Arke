from rich.console import Console
from rich.traceback import install

console = Console()

install(
    console=console,
    show_locals=True,
    suppress=["pydantic", "langchain", "langgraph"]
)

def agent_output(text: str):
    """Outputs agent responses to the console with the defined styling."""
    console.print(
        text,
        style="bold blue",
        soft_wrap=True,
    )