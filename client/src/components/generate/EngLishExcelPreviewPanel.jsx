import { useEffect, useState } from "react";
import * as XLSX from "xlsx";

const LEVELS = ["Đọc hiểu", "Thông hiểu", "Vận dụng", "Vận dụng cao"];

function detectTypeColumns(columns) {
  const map = {};

  columns.forEach((col, i) => {
    const colLower = String(col).toLowerCase();

    if (colLower.includes("điền từ")) map["Điền từ"] = i;
    else if (colLower.includes("sắp xếp từ")) map["Sắp xếp từ"] = i;
    else if (colLower.includes("sắp xếp")) map["Sắp xếp"] = i;
    else if (colLower.includes("đọc hiểu")) map["Đọc hiểu"] = i;
    else if (colLower.includes("điền cụm")) map["Điền cụm từ/điền câu"] = i;
    else if (colLower.includes("hoàn thành câu")) map["Hoàn thành câu"] = i;
    else if (colLower.includes("đồng nghĩa") || colLower.includes("trái nghĩa")) map["Đồng nghĩa/Trái nghĩa"] = i;
    else if (colLower.includes("tìm lỗi sai")) map["Tìm lỗi sai"] = i;
    else if (colLower.includes("kết hợp") || colLower.includes("viết lại")) map["Kết hợp/viết lại câu"] = i;
    else if (colLower.includes("phát âm") || colLower.includes("trọng âm")) map["Phát âm/Trọng âm"] = i;
    else if (colLower.includes("giao tiếp")) map["Câu giao tiếp"] = i;
    else if (colLower.includes("tình huống") || colLower.includes("tư duy")) map["Tư duy/Tình huống"] = i;
  });

  return map;
}

function detectAllLevels(rowValues, startIndex) {
  const found = [];

  for (let i = 0; i < 4; i++) {
    const cell = rowValues[startIndex + i];
    if (cell && String(cell).trim() !== "") {
      found.push(LEVELS[i]);
    }
  }

  return found;
}

function groupBySTT(rows) {
  const groups = {};

  rows.forEach((row) => {
    const key = row["STT"];
    if (!groups[key]) groups[key] = [];
    groups[key].push(row);
  });

  return groups;
}

function buildBlocks(rows, columns, typeColMap) {
  const groups = groupBySTT(rows);
  const blocks = [];

  Object.entries(groups).forEach(([stt, group]) => {
    const first = group[0];
    const questionTypes = {};

    group.forEach((row) => {
      const spec = row["Đặc tả ma trận"];
      if (!spec) return;

      const rowValues = columns.map((col) => row[col]);

      Object.entries(typeColMap).forEach(([type, colIndex]) => {
        const levels = detectAllLevels(rowValues, colIndex);

        levels.forEach((lv) => {
          if (!questionTypes[type]) questionTypes[type] = [];
          questionTypes[type].push({ spec, level: lv });
        });
      });
    });

    blocks.push({
      stt,
      topic: first["Chủ đề"],
      difficulty: first["Độ khó"],
      questionTypes,
    });
  });

  return blocks;
}

export default function EnglishExcelPreviewPanel({ file }) {
  const [rows, setRows] = useState([]);
  const [columns, setColumns] = useState([]);
  const [typeMap, setTypeMap] = useState({});
  const [blocks, setBlocks] = useState([]);

  useEffect(() => {
    if (!file) return;

    const reader = new FileReader();

    reader.onload = (e) => {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: "array" });

      const sheet = workbook.Sheets["Ma trận"];
      const json = XLSX.utils.sheet_to_json(sheet, { defval: "" });

      if (json.length === 0) return;

      const cols = Object.keys(json[0]);
      const detected = detectTypeColumns(cols);
      const builtBlocks = buildBlocks(json, cols, detected);

      setRows(json);
      setColumns(cols);
      setTypeMap(detected);
      setBlocks(builtBlocks);
    };

    reader.readAsArrayBuffer(file);
  }, [file]);

  return (
    <div className="p-4 space-y-6 overflow-auto h-full">
      {/* Column Mapping */}
      <div>
        <h2 className="font-semibold mb-2">Column Mapping</h2>
        <div className="text-sm bg-gray-50 p-3 rounded">
          {Object.entries(typeMap).map(([type, index]) => (
            <div key={type}>
              {type} → Column {index + 1}
            </div>
          ))}
        </div>
      </div>

      {/* Raw Table */}
      <div>
        <h2 className="font-semibold mb-2">Excel Raw</h2>
        <div className="overflow-auto max-h-80 border rounded">
          <table className="min-w-full text-xs">
            <thead className="bg-gray-100">
              <tr>
                {columns.map((col) => (
                  <th key={col} className="px-2 py-1 border">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 20).map((row, i) => (
                <tr key={i}>
                  {columns.map((col) => (
                    <td key={col} className="px-2 py-1 border">{row[col]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Blocks Preview */}
      <div>
        <h2 className="font-semibold mb-2">Blocks Preview</h2>
        <div className="space-y-4">
          {blocks.map((block, idx) => (
            <div key={idx} className="border rounded p-3 bg-white shadow-sm">
              <div className="font-medium">STT: {block.stt}</div>
              <div className="text-sm text-gray-600">
                Topic: {block.topic} | Difficulty: {block.difficulty}
              </div>

              <div className="mt-2 space-y-1 text-sm">
                {Object.entries(block.questionTypes).map(([type, list]) => (
                  <div key={type}>
                    <strong>{type}</strong>: {list.length} questions
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
