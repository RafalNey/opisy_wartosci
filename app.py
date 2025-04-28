import os
import openai
import pypandoc
from dotenv import load_dotenv
from difflib import get_close_matches

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


def normalize_name(name):
    return name.lower().replace('-', ' ').replace('_', ' ')


def convert_odt_to_text(odt_path):
    return pypandoc.convert_file(odt_path, 'plain', format='odt')


def ask(query):
    system_prompt = "Jesteś specjalistą z dziedziny psychologii zajmującym się modelami wartości Schwartza. Używaj dokładnych nazw wartości z listy, nie modyfikuj ich i nie stosuj zamienników. Zawsze posługuj się wartościami w języku polskim zgodnie z oficjalną terminologią."
    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query},
        ],
    )
    return response.choices[0].message.content


def find_best_match(name):
    # Wyciągnij listę nazw z wartości
    name = normalize_name(name)
    value_names = [normalize_name(v.split('. ')[1].strip()) for v in lista_wartosci.strip().split('\n')]
    # Znajdź najlepsze dopasowanie
    match = get_close_matches(name, value_names, n=1, cutoff=0.5)
    return match[0] if match else None


def process_files(matching_files, prompt_template):
    results = {}
    for name, file in matching_files:
        with open(file, 'r', encoding='utf-8') as f:
            file_text = f.read()

        base_name = os.path.splitext(name)[0]
        closest_match = find_best_match(base_name)
        if not closest_match:
            print(f"Nie znaleziono dopasowania dla pliku: {name}")
            continue

        query = f"{prompt_template}\n\n{file_text}"
        processed_text = ask(query)
        results[closest_match] = processed_text.replace(base_name, closest_match)
    return results


opis1 = convert_odt_to_text(os.path.join(WARTOSCI_OPISY_DIR, 'example1.odt'))

prompt_template = (
    f"""
    Dokonaj opisu poszczególnych wartości według modelu Schwartza. Użyj w swoich opisach dokładnych nazw tych wartości według listy, nie stosuj zamienników. Opis ma mieć charakter gradacyjnego kontinuum z podziałem na 6 poziomów. Przedstaw opis trzech najwyższych poziomów: bardzo wysokie, wysokie, umiarkowane utożsamianie się z daną wartością. Podaj jednolite opisy, a nie w punktach. Dokonaj opisu takiej osoby w trzeciej osobie liczby pojedynczej. Następnie dokonaj opisu odnoszącego się do trzech najniższych poziomów: łagodne odrzucenie, znaczące odrzucenie, skrajne odrzucenie danej wartości. Dokonaj takiego opisu tej osoby, jakby ta osoba odrzucała daną wartość oraz była motywowana do przeciwstawiania się jej.
    Opisz wszystkie wartości w sposób przykładowy: {opis1}.
    """
)

matching_files = [(f, os.path.join(RAW_DIR, f)) for f in os.listdir(RAW_DIR) if f.endswith('.txt')]
processed_results = process_files(matching_files, prompt_template)

for name, processed_text in processed_results.items():
    output_file_name = f"{name}.txt"
    output_path = os.path.join(WARTOSCI_DONE_DIR, output_file_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(processed_text)
    print(f"Zapisano przetworzony plik: {output_file_name}")

print("Przetwarzanie zakończone.")
