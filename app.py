import os
import openai
import PyPDF2
import pypandoc
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Ścieżki do katalogów
RAW_DIR = 'raw'
WARTOSCI_DIR = 'wartosci'
WARTOSCI_OPISY_DIR = 'wartosci-opisy'
WARTOSCI_DONE_DIR = 'wartosci-done'

# Upewnij się, że katalog docelowy istnieje
os.makedirs(WARTOSCI_DONE_DIR, exist_ok=True)


def extract_pdf_values(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        values = []
        for page in reader.pages:
            text = page.extract_text().split('\n')
            values.extend(text)
        return [value.strip() for value in values if value.strip()]


def convert_odt_to_text(odt_path):
    return pypandoc.convert_file(odt_path, 'plain', format='odt')


def ask(query):
    system_prompt = 'Jesteś systemem do identyfikacji plików.'
    response = openai.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query},
        ],
    )
    return response.choices[0].message.content,
    # return response['choices'][0]['message']['content'].strip()


def get_all_raw_files(raw_dir):
    return [filename for filename in os.listdir(raw_dir) if filename.endswith('.odt')]


def process_files(matching_files, prompt_template):
    results = {}
    for name, file in matching_files:
        file_text = convert_odt_to_text(file)
        query = f"{prompt_template}\n\n{file_text}"
        processed_text = ask(query)
        results[name] = processed_text
    return results


def find_matching_file(value, raw_files):
    query = f"Znajdź najbardziej podobną nazwę pliku dla wartości: {value}"
    suggestion = ask(query)
    for filename in raw_files:
        if suggestion.lower() in filename.lower():
            return filename
    return None


# Główna logika
pdf_values_path = os.path.join(WARTOSCI_DIR, 'wartosci.pdf')
values = extract_pdf_values(pdf_values_path)

opis1 = convert_odt_to_text(os.path.join(WARTOSCI_OPISY_DIR, 'example1.odt'))
opis2 = convert_odt_to_text(os.path.join(WARTOSCI_OPISY_DIR, 'example2.odt'))

prompt_template = (
    f"Here's how to transform specific English text into Polish based on two examples:\n\n"
    f"Example 1: {opis1}\n\nExample 2: {opis2}\n\n"
    f"Transform the following text in a similar way:"
)

raw_files = get_all_raw_files(RAW_DIR)
matching_files = []

for value in values:
    matched_file = find_matching_file(value, raw_files)
    if matched_file:
        file_path = os.path.join(RAW_DIR, matched_file)
        matching_files.append((value, file_path))

processed_results = process_files(matching_files, prompt_template)

# Zapisz przetworzone teksty w formacie .txt
for name, processed_text in processed_results.items():
    output_file_name = f"{name}_stopni.txt"
    output_path = os.path.join(WARTOSCI_DONE_DIR, output_file_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(processed_text)

print("Przetwarzanie zakończone.")
