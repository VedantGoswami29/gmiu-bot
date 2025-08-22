import os
from dotenv import load_dotenv
from DataBase import create_table, insert_faq

load_dotenv()

FAQ_PATH = os.getenv("FAQ_PATH", "faq_data")
FILES = [f"{FAQ_PATH}/{file}" for file in os.listdir(FAQ_PATH)] if FAQ_PATH else []

if not FILES:
    print("No files found to process. Check FAQ_PATH path.")
    exit()

create_table()
total_inserted = 0

for file_path in FILES:
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Skipping.")
        continue

    print(f"Processing file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read().splitlines()

    parsed_docs = []
    current_entry = {}
    is_answer = False

    for line in raw_content:
        line = line.strip()
        if not line:
            continue
        try:
            if line.lower().startswith("question id"):
                if current_entry:
                    parsed_docs.append(current_entry)

                # Reset current entry with empty defaults
                current_entry = {
                    "id": "",
                    "question": "",
                    "answer": "",
                    "context": "",
                    "references": "",
                    "keywords": []
                }

                current_entry["id"] = line.split(":", 1)[1].strip()
                is_answer = False

            elif line.lower().startswith("question"):
                current_entry["question"] = line.split(":", 1)[1].strip()
                is_answer = False

            elif line.lower().startswith("answer"):
                is_answer = True
                current_entry["answer"] = line.split(":", 1)[1].strip()

            elif line.lower().startswith("context"):
                current_entry["context"] = line.split(":", 1)[1].strip()
                is_answer = False

            elif line.lower().startswith("references"):
                current_entry["references"] = line.split(":", 1)[1].strip()
                is_answer = False

            elif line.lower().startswith("keyword"):
                keywords = line.split(":", 1)[1].strip()
                current_entry["keywords"] = [k.strip() for k in keywords.split(",")]
                is_answer = False

            elif is_answer:
                # Append additional answer lines
                current_entry["answer"] += "\n" + line.strip()

        except Exception as e:
            print(f"Error processing line: {line}")
            print(f"Exception: {e}")

    # Add last entry if exists
    if current_entry:
        parsed_docs.append(current_entry)

    if not parsed_docs:
        print(f"No valid entries found in the file: {file_path}. Skipping.")
        continue

    # Insert into DB
    for doc in parsed_docs:
        if "question" not in doc or "answer" not in doc:
            print(f"Skipping entry with missing question/answer: {doc.get('id', 'Unknown ID')}")
            continue
        insert_faq(
            question=doc["question"],
            answer=doc["answer"],
            keywords=doc.get("keywords", []),
            reference=doc.get("references", "")
        )
        total_inserted += 1

print(f"✅ Successfully inserted {total_inserted} FAQs into the database.")