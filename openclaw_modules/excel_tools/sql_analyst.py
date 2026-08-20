import duckdb
import pandas as pd
import sys

def execute_query(file_path: str, query: str) -> str:
    """Выполняет SQL-запрос по листам Excel-файла."""
    try:
        conn = duckdb.connect(database=':memory:')
        excel_file = pd.ExcelFile(file_path)
        for sheet in excel_file.sheet_names:
            tbl_name = sheet.strip().replace(" ", "_").lower()
            df = pd.read_excel(file_path, sheet_name=sheet)
            df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
            conn.register(tbl_name, df)
        
        res = conn.execute(query).df()
        if res.empty:
            return "Результат пуст."
        return res.to_markdown(index=False)
    except Exception as e:
        return f"Ошибка SQL: {e}"

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print(execute_query(sys.argv[1], sys.argv[2]))
