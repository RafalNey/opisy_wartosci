import os
import openai
import pypandoc
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Ścieżki do katalogów
RAW_DIR = 'raw'
WARTOSCI_OPISY_DIR = 'wartosci-opisy'
WARTOSCI_DONE_DIR = 'wartosci-done'

# Upewnij się, że katalog docelowy istnieje
os.makedirs(WARTOSCI_DONE_DIR, exist_ok=True)

# Lista wartości
lista_wartosci = '''
1. Osiągnięcia (achievement)
2. Hedonizm (hedonism)
3. Stymulacja (stimulation)
4. Kierowanie sobą w działaniu (self-direction-action)
5. Kierowanie sobą w myśleniu (self-direction-thought)
6. Uniwersalizm – tolerancja (universalism-tolerance)
7. Uniwersalizm ekologiczny (universalism-nature)
8. Uniwersalizm społeczny (universalism-societalconcern)
9. Życzliwość – troskliwość (benevolence-caring)
10. Życzliwość – niezawodność (benevolence-dependability)
11. Pokora (humility)
12. Przystosowanie do ludzi (conformity-interpersonal)
13. Przystosowanie do reguł (conformity-rules)
14. Tradycja (tradition)
15. Bezpieczeństwo społeczne (security-societal)
16. Bezpieczeństwo osobiste (security-personal)
17. Prestiż (face)
18. Władza nad zasobami (power-resources)
19. Władza nad ludźmi (power-dominance)
'''


def convert_odt_to_text(odt_path):
    return pypandoc.convert_file(odt_path, 'plain', format='odt')


def ask(query):
    system_prompt = 'Jesteś specjalistą z dziedziny psychologii, który zajmuje się modelami wartości Schwartza. Doskonale opisujesz wartości w tym modelu. Znasz bardzo dobrze język angielski i polski. Doskonale posługujesz się terminologią psychologiczną i potrafisz ją wyjaśnić dobrze nawet laikowi'
    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query},
        ],
    )
    return response.choices[0].message.content


def process_files(matching_files, prompt_template):
    results = {}
    for name, file in matching_files:
        with open(file, 'r', encoding='utf-8') as f:
            file_text = f.read()
        query = f"{prompt_template}\n\n{file_text}"
        processed_text = ask(query)
        results[name] = processed_text
    return results


opis1 = convert_odt_to_text(os.path.join(WARTOSCI_OPISY_DIR, 'example1.odt'))

prompt_template = (
    f"""
    Dokonaj opisu poszczególnych wartości. Opis ma mieć charakter gradacyjnego kontinuum z podziałem na 6 poziomów. Przedstaw opis trzech najwyższych poziomów: bardzo wysokie, wysokie, umiarkowane utożsamianie się z daną wartością. Podaj jednolite opisy a nie w punktach. Dokonaj opisu takiej osoby w trzeciej osobie liczby pojedynczej. Następnie dokonaj opisu odnoszącego się do trzech najniższych poziomów: łagodne odrzucenie, znaczące odrzucenie, skrajne odrzucenie danej wartości. Dokonaj takiego opisu tej osoby, jakby ta osoba odrzucała daną wartość oraz była motywowana do przeciwstawiania się takim wartościom.
    Jako przykład posłuż się {opis1}. Opisz wszystkie wartości w taki właśnie sposób.
    """
)

matching_files = [(f, os.path.join(RAW_DIR, f)) for f in os.listdir(RAW_DIR) if f.endswith('.txt')]
processed_results = process_files(matching_files, prompt_template)

for name, processed_text in processed_results.items():
    base_name = os.path.splitext(name)[0]
    output_file_name = f"{base_name}.txt"
    output_path = os.path.join(WARTOSCI_DONE_DIR, output_file_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(processed_text)

print("Przetwarzanie zakończone.")
