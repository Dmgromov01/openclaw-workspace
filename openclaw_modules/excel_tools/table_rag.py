import pandas as pd
import json

def parse_excel_to_chunks(file_path: str) -> list:
    """Конвертирует строки таблицы в смысловые чанки с метаданными."""
    excel_data = pd.read_excel(file_path, sheet_name=None)
    chunks = []
    
    for sheet_name, df in excel_data.items():
        df = df.dropna(how='all').fillna('')
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            text_desc = f"Лист: {sheet_name} | " + " | ".join([f"{k}: {v}" for k, v in row_dict.items() if v != ''])
            chunks.append({
                "text": text_desc,
                "metadata": {
                    "source": file_path,
                    "sheet": sheet_name,
                    "row_index": int(idx) + 2
                },
                "raw": row_dict
            })
    return chunks

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        chunks = parse_excel_to_chunks(sys.argv[1])
        print(f"Сформировано чанков: {len(chunks)}")
        if chunks:
            print("Пример первого чанка:\n", json.dumps(chunks[0], ensure_ascii=False, indent=2))
