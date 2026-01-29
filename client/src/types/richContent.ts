/**
 * Rich Content TypeScript Interfaces
 * Supports text, images, tables, charts, LaTeX, and mixed content
 */

export type ContentType = 'text' | 'image' | 'table' | 'chart' | 'latex' | 'mixed';

export type ChartType = 'line' | 'bar' | 'pie' | 'scatter' | 'heatmap' | 'radar';

export interface ContentMetadata {
  // Image metadata
  alt?: string;
  width?: number;
  height?: number;
  caption?: string;
  
  // Table metadata
  bordered?: boolean;
  striped?: boolean;
  
  // LaTeX metadata
  display?: 'inline' | 'block';
  
  // Generic metadata
  [key: string]: any;
}

export interface TableContent {
  headers: string[];
  rows: string[][];
}

export interface ChartContent {
  chartType: ChartType;
  echarts: any; // ECharts configuration object
}

export interface ContentBlock {
  type: ContentType;
  content: string | TableContent | ChartContent | ContentBlock[];
  metadata?: ContentMetadata;
}

// Simple text (backward compatibility)
export type SimpleContent = string;

// Rich content (new format)
export type RichContent = ContentBlock | SimpleContent;

export interface RichOption {
  [key: string]: RichContent;
}

export interface RichExplanation {
  [key: string]: RichContent;
}

export interface Statement {
  text: RichContent;
  is_correct: boolean;
}

export interface Statements {
  a: Statement;
  b: Statement;
  c: Statement;
  d: Statement;
}

export interface BaseQuestion {
  question_code: string;
  question_type: 'TN' | 'DS' | 'TLN' | 'TL';
  lesson_name: string;
  chapter_number: string;
  lesson_number: string;
  level: string;
}

export interface TNQuestion extends BaseQuestion {
  question_type: 'TN';
  question_stem: RichContent;
  options: RichOption;
  correct_answer: string;
  explanation: RichContent;
}

export interface DSQuestion extends BaseQuestion {
  question_type: 'DS';
  source_text: RichContent;
  statements: Statements;
  explanation: RichExplanation;
}

export interface TLNQuestion extends BaseQuestion {
  question_type: 'TLN';
  question_stem: RichContent;
  correct_answer: RichContent;
  explanation: RichContent;
}

export interface TLQuestion extends BaseQuestion {
  question_type: 'TL';
  question_stem: RichContent;
  correct_answer: RichContent;
  explanation: RichContent;
}

export type Question = TNQuestion | DSQuestion | TLNQuestion | TLQuestion;

export interface QuestionMetadata {
  session_id: string;
  subject: string;
  grade: string;
  curriculum: string;
  matrix_file: string;
  total_questions: number;
  tn_count: number;
  ds_count: number;
  tln_count: number;
  tl_count: number;
  generated_at: string;
  status: string;
  content_version?: string;
  supports_rich_content?: boolean;
}

export interface QuestionSet {
  metadata: QuestionMetadata;
  questions: {
    TN: TNQuestion[];
    DS: DSQuestion[];
    TLN: TLNQuestion[];
    TL: TLQuestion[];
  };
}

// Helper type guards

export function isContentBlock(content: RichContent): content is ContentBlock {
  return typeof content === 'object' && 'type' in content && 'content' in content;
}

export function isSimpleContent(content: RichContent): content is SimpleContent {
  return typeof content === 'string';
}

export function isTextBlock(block: ContentBlock): boolean {
  return block.type === 'text';
}

export function isImageBlock(block: ContentBlock): boolean {
  return block.type === 'image';
}

export function isTableBlock(block: ContentBlock): boolean {
  return block.type === 'table';
}

export function isChartBlock(block: ContentBlock): boolean {
  return block.type === 'chart';
}

export function isLatexBlock(block: ContentBlock): boolean {
  return block.type === 'latex';
}

export function isMixedBlock(block: ContentBlock): boolean {
  return block.type === 'mixed';
}

// Helper functions to normalize content

export function normalizeContent(content: RichContent): ContentBlock {
  if (isContentBlock(content)) {
    return content;
  }
  return {
    type: 'text',
    content: content
  };
}

export function getTextContent(content: RichContent): string {
  if (isSimpleContent(content)) {
    return content;
  }
  
  const block = content as ContentBlock;
  if (block.type === 'text') {
    return block.content as string;
  }
  
  if (block.type === 'mixed') {
    const blocks = block.content as ContentBlock[];
    return blocks
      .map(b => getTextContent(b))
      .join(' ');
  }
  
  return '';
}

// Example usage

export const exampleTNQuestion: TNQuestion = {
  question_code: 'C1',
  question_type: 'TN',
  lesson_name: 'Bài 1. Cấu trúc của chất',
  chapter_number: '1',
  lesson_number: '1',
  level: 'NB',
  question_stem: {
    type: 'mixed',
    content: [
      { type: 'text', content: 'Quan sát biểu đồ sau:' },
      {
        type: 'chart',
        content: {
          chartType: 'line',
          echarts: {
            title: { text: 'Nhiệt độ theo thời gian' },
            xAxis: { data: ['0s', '30s', '60s', '90s'] },
            yAxis: { type: 'value' },
            series: [{ data: [20, 50, 80, 100], type: 'line' }]
          }
        }
      },
      { type: 'text', content: 'Nhiệt độ tại 60s là bao nhiêu?' }
    ]
  },
  options: {
    A: '50°C',
    B: '80°C',
    C: '100°C',
    D: '120°C'
  },
  correct_answer: 'B',
  explanation: 'Từ biểu đồ ta thấy tại 60s, nhiệt độ là 80°C'
};

export const exampleDSQuestion: DSQuestion = {
  question_code: 'C1',
  question_type: 'DS',
  lesson_name: 'Bài 2. Nội năng',
  chapter_number: '1',
  lesson_number: '2',
  level: 'mixed',
  source_text: {
    type: 'mixed',
    content: [
      { type: 'text', content: 'Xét thí nghiệm:' },
      {
        type: 'image',
        content: 'experiment.png',
        metadata: { width: 500, caption: 'Hình 1: Thí nghiệm' }
      },
      {
        type: 'table',
        content: {
          headers: ['Thời gian', 'Nhiệt độ'],
          rows: [['0s', '20°C'], ['60s', '80°C']]
        }
      }
    ]
  },
  statements: {
    a: { text: 'Nhiệt độ tăng theo thời gian', is_correct: true },
    b: { text: 'Thể tích không đổi', is_correct: false },
    c: { text: 'Áp suất tăng', is_correct: true },
    d: { text: 'Nội năng giảm', is_correct: false }
  },
  explanation: {
    a: 'Đúng. Nhiệt độ tăng từ 20°C lên 80°C',
    b: 'Sai. Thể tích có thể thay đổi',
    c: 'Đúng. Khi nhiệt độ tăng, áp suất tăng',
    d: 'Sai. Nội năng tăng khi nhiệt độ tăng'
  }
};
