import os
import json
import duckdb
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter

class ExcelSkillsHandler:

    @staticmethod
    def excel_sql_query(file_path: str, query: str) -> str:
        if not os.path.exists(file_path):
            return f"Ошибка: Файл {file_path} не найден."
        try:
            conn = duckdb.connect(database=':memory:')
            excel_file = pd.ExcelFile(file_path)
            for sheet in excel_file.sheet_names:
                tbl_name = sheet.strip().replace(" ", "_").lower()
                df = pd.read_excel(file_path, sheet_name=sheet)
                df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
                conn.register(tbl_name, df)
            
            res_df = conn.execute(query).df()
            if res_df.empty:
                return "Запрос выполнен успешно, записей не найдено."
            return res_df.to_markdown(index=False)
        except Exception as err:
            return f"Ошибка выполнения SQL: {str(err)}"

    @staticmethod
    def excel_table_search(file_path: str, keyword: str) -> str:
        if not os.path.exists(file_path):
            return f"Ошибка: Файл {file_path} не найден."
        try:
            excel_data = pd.read_excel(file_path, sheet_name=None)
            matches = []
            kw = str(keyword).lower()
            
            for sheet_name, df in excel_data.items():
                df = df.dropna(how='all').fillna('')
                for idx, row in df.iterrows():
                    row_dict = row.to_dict()
                    row_str = " | ".join([f"{k}: {v}" for k, v in row_dict.items() if str(v).strip() != ''])
                    if kw in row_str.lower():
                        matches.append({
                            "sheet": sheet_name,
                            "row": int(idx) + 2,
                            "data": row_dict
                        })
            
            if not matches:
                return f"По запросу '{keyword}' совпадений в таблице не найдено."
            return json.dumps(matches[:15], ensure_ascii=False, indent=2)
        except Exception as err:
            return f"Ошибка поиска по таблице: {str(err)}"

    @staticmethod
    def excel_generate_report(output_path: str, title: str, categories: list, plan_values: list, fact_values: list) -> str:
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Сводка"
            ws.views.sheetView[0].showGridLines = True

            ws["A1"] = title
            ws["A1"].font = Font(name="Segoe UI", size=14, bold=True, color="1A365D")

            headers = ["Категория", "План, ₽", "Факт, ₽", "Отклонение, ₽", "% Выполнения"]
            ws.append([])
            ws.append(headers)

            header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
            for col in range(1, 6):
                cell = ws.cell(row=3, column=col)
                cell.fill = header_fill
                cell.font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
                cell.alignment = Alignment(horizontal="center", vertical="center")

            thin_border = Border(left=Side(style='thin', color='CBD5E0'), right=Side(style='thin', color='CBD5E0'),
                                 top=Side(style='thin', color='CBD5E0'), bottom=Side(style='thin', color='CBD5E0'))

            start_row = 4
            for i, (cat, p, f) in enumerate(zip(categories, plan_values, fact_values), start_row):
                ws.cell(row=i, column=1, value=cat).border = thin_border
                ws.cell(row=i, column=2, value=p).number_format = '#,##0'
                ws.cell(row=i, column=3, value=f).number_format = '#,##0'
                ws.cell(row=i, column=4, value=f"=C{i}-B{i}").number_format = '#,##0'
                ws.cell(row=i, column=5, value=f"=C{i}/B{i}").number_format = '0.0%'
                for c in range(1, 6):
                    ws.cell(row=i, column=c).border = thin_border

            tot_row = start_row + len(categories)
            ws.cell(row=tot_row, column=1, value="ИТОГО").font = Font(name="Segoe UI", bold=True)
            ws.cell(row=tot_row, column=2, value=f"=SUM(B4:B{tot_row-1})").number_format = '#,##0'
            ws.cell(row=tot_row, column=3, value=f"=SUM(C4:C{tot_row-1})").number_format = '#,##0'
            ws.cell(row=tot_row, column=4, value=f"=C{tot_row}-B{tot_row}").number_format = '#,##0'
            ws.cell(row=tot_row, column=5, value=f"=C{tot_row}/B{tot_row}").number_format = '0.0%'
            for c in range(1, 6):
                ws.cell(row=tot_row, column=c).border = thin_border

            chart = BarChart()
            chart.title = "План vs Факт"
            chart.width = 14
            chart.height = 8
            chart.add_data(Reference(ws, min_col=2, min_row=3, max_col=3, max_row=tot_row-1), titles_from_data=True)
            chart.set_categories(Reference(ws, min_col=1, min_row=4, max_row=tot_row-1))
            ws.add_chart(chart, "G3")

            for col in ws.columns:
                ws.column_dimensions[get_column_letter(col[0].column)].width = 20

            wb.save(output_path)
            return f"Отчёт успешно сгенерирован и сохранён: {output_path}"
        except Exception as err:
            return f"Ошибка генерации отчёта: {str(err)}"

    def execute_tool(self, tool_name: str, arguments: dict) -> str:
        method = getattr(self, tool_name, None)
        if not method:
            return f"Инструмент '{tool_name}' не зарегистрирован."
        return method(**arguments)
