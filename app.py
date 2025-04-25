import os
import openai
import PyPDF2
import pypandoc
import shutil
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Ścieżki do katalogów
RAW_DIR = 'raw'
RAW_POL_DIR = 'raw-pol'
WARTOSCI_DIR = 'wartosci'
WARTOSCI_OPISY_DIR = 'wartosci-opisy'
WARTOSCI_DONE_DIR = 'wartosci-done'

# Upewnij się, że katalogi docelowe istnieją
os.makedirs(RAW_POL_DIR, exist_ok=True)
os.makedirs(WARTOSCI_DONE_DIR, exist_ok=True)


def extract_pdf_values(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        values = []
        for page in reader.pages:
            text = page.extract_text().split('\n')
            values.extend(text)
        return [value.strip() for value in values if value.strip()]


def ask(query):
    system_prompt = 'Jesteś systemem do identyfikacji plików.'
    response = openai.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query},
        ],
    )
    return response.choices[0].message.content


def rename_and_copy_files(raw_dir, raw_pol_dir, values):
    raw_files = [filename for filename in os.listdir(raw_dir) if filename.endswith('.odt')]
    used_values = set()
    unmatched_count = 1

    for filename in raw_files:
        query = f"Dopasuj angielską nazwę pliku '{filename}' do jednej z tych polskich wartości: {values}"
        suggestion = ask(query)

        if suggestion in values and suggestion not in used_values:
            new_name = suggestion + '.odt'
            used_values.add(suggestion)
        else:
            new_name = f'niedopasowany{unmatched_count}.odt'
            unmatched_count += 1

        shutil.copy(os.path.join(raw_dir, filename), os.path.join(raw_pol_dir, new_name))


# Krok 1: Zmiana nazw plików
pdf_values_path = os.path.join(WARTOSCI_DIR, 'wartosci.pdf')
values = extract_pdf_values(pdf_values_path)
rename_and_copy_files(RAW_DIR, RAW_POL_DIR, values)


# Krok 2: Przetwarzanie zawartości plików
def convert_odt_to_text(odt_path):
    return pypandoc.convert_file(odt_path, 'plain', format='odt')


def process_files(matching_files, prompt_template):
    results = {}
    for name, file in matching_files:
        file_text = convert_odt_to_text(file)
        query = f"{prompt_template}\n\n{file_text}"
        processed_text = ask(query)
        results[name] = processed_text
    return results


opis1 = convert_odt_to_text(os.path.join(WARTOSCI_OPISY_DIR, 'example1.odt'))
opis2 = convert_odt_to_text(os.path.join(WARTOSCI_OPISY_DIR, 'example2.odt'))

prompt_template = (
    f"Here's how to transform specific English text into Polish based on two examples:\n\n"
    f"Example 1: {opis1}\n\nExample 2: {opis2}\n\n"
    f"Transform the following text in a similar way:"
)

matching_files = [(f, os.path.join(RAW_POL_DIR, f)) for f in os.listdir(RAW_POL_DIR) if f.endswith('.odt')]
processed_results = process_files(matching_files, prompt_template)

# Zapisz przetworzone teksty w formacie .txt
for name, processed_text in processed_results.items():
    output_file_name = f"{name}_stopni.txt"
    output_path = os.path.join(WARTOSCI_DONE_DIR, output_file_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(processed_text)

print("Przetwarzanie zakończone.")
