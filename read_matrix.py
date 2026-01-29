import pandas as pd
import sys

# Đọc file Excel với rich_content note
file_path = r'E:\App\matrixquesgen\data\input\Ma trận_DIALY_KNTT_C12.xlsx'
df_dict = pd.read_excel(file_path, sheet_name=None, header=None)

print('=' * 100)
print(f'FILE: {file_path}')
print('=' * 100)

print(f'\nSheets: {list(df_dict.keys())}')

for sheet_name, df in df_dict.items():
    print(f'\n{"=" * 100}')
    print(f'SHEET: {sheet_name}')
    print(f'Shape: {df.shape[0]} rows x {df.shape[1]} columns')
    print('=' * 100)
    
    print('\nFirst 20 rows:')
    for i in range(min(20, len(df))):
        row_data = df.iloc[i].tolist()
        # Truncate long cells
        row_data_str = []
        for cell in row_data:
            if pd.isna(cell):
                row_data_str.append('NaN')
            else:
                cell_str = str(cell)
                if len(cell_str) > 50:
                    row_data_str.append(cell_str[:47] + '...')
                else:
                    row_data_str.append(cell_str)
        print(f'Row {i:2d}: {row_data_str}')
    
    # Print column info
    print(f'\nColumn count: {df.shape[1]}')
    print('\nColumn analysis (non-empty cells per column):')
    for col_idx in range(df.shape[1]):
        non_empty = df.iloc[:, col_idx].notna().sum()
        print(f'  Col {col_idx:2d}: {non_empty} non-empty cells')
