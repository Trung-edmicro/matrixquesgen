import pandas as pd

df = pd.read_excel(r'E:\App\matrixquesgen\data\input\Ma trận_VATLY_KNTT_C12.xlsx', 
                   sheet_name='Ma trận', header=None)

print("=" * 100)
print("ANALYZING EXCEL STRUCTURE")
print("=" * 100)

print("\nRow 0 (Headers):")
for i in range(min(10, df.shape[1])):
    print(f"  Col {i}: [{df.iloc[0, i]}]")

print("\nRow 1 (Sub-headers):")
for i in range(min(10, df.shape[1])):
    print(f"  Col {i}: [{df.iloc[1, i]}]")

print("\nRow 2 (First data):")
for i in range(min(10, df.shape[1])):
    val = str(df.iloc[2, i])
    if len(val) > 60:
        val = val[:57] + "..."
    print(f"  Col {i}: [{val}]")

print("\nRow 10 (Another data):")
for i in range(min(10, df.shape[1])):
    val = str(df.iloc[10, i])
    if len(val) > 60:
        val = val[:57] + "..."
    print(f"  Col {i}: [{val}]")
