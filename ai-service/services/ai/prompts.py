from services.ai.base import AIProvider


def summarize(provider: AIProvider, text: str) -> str:
    prompt = (
        "Riassumi il seguente testo in modo chiaro e conciso:\n\n"
        f"{text}"
    )
    return provider.complete(prompt)


def analyze_record(provider: AIProvider, record_data: dict) -> str:
    formatted = "\n".join(f"- {k}: {v}" for k, v in record_data.items())
    prompt = (
        "Analizza i seguenti dati di un record CRM e fornisci osservazioni utili:\n\n"
        f"{formatted}"
    )
    return provider.complete(prompt)


def generate_report(provider: AIProvider, records: list[dict], context: str = "") -> str:
    formatted = "\n\n".join(
        "\n".join(f"- {k}: {v}" for k, v in record.items())
        for record in records
    )
    header = f"{context}\n\n" if context else ""
    prompt = f"{header}Genera un report dettagliato basato sui seguenti dati CRM:\n\n{formatted}"
    return provider.complete(prompt)


def chat(provider: AIProvider, records: list[dict], question: str) -> str:
    formatted = "\n\n".join(
        "\n".join(f"- {k}: {v}" for k, v in record.items())
        for record in records
    )
    prompt = (
        "Sei un assistente CRM. Rispondi in modo diretto e conversazionale alla domanda dell'utente "
        "basandoti sui dati forniti. Se la domanda non riguarda i dati, rispondi comunque in modo utile.\n\n"
        f"Dati rilevanti:\n{formatted}\n\n"
        f"Domanda: {question}"
    )
    return provider.complete(prompt)


def suggest_actions(provider: AIProvider, record_data: dict) -> str:
    formatted = "\n".join(f"- {k}: {v}" for k, v in record_data.items())
    prompt = (
        "In base ai seguenti dati CRM, suggerisci le prossime azioni commerciali più efficaci:\n\n"
        f"{formatted}"
    )
    return provider.complete(prompt)
