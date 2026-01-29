import React from 'react';
import {
  ContentBlock,
  RichContent,
  isContentBlock,
  isSimpleContent,
  TableContent,
  ChartContent,
} from '../../types/richContent';
import * as echarts from 'echarts';
import { useEffect, useRef } from 'react';
import 'katex/dist/katex.min.css';
import katex from 'katex';

interface RichContentRendererProps {
  content: RichContent;
  className?: string;
}

export const RichContentRenderer: React.FC<RichContentRendererProps> = ({ content, className }) => {
  // Simple text (backward compatibility)
  if (isSimpleContent(content)) {
    return <div className={className}>{content}</div>;
  }

  // Rich content
  const block = content as ContentBlock;
  return <ContentBlockRenderer block={block} className={className} />;
};

interface ContentBlockRendererProps {
  block: ContentBlock;
  className?: string;
}

const ContentBlockRenderer: React.FC<ContentBlockRendererProps> = ({ block, className }) => {
  switch (block.type) {
    case 'text':
      return <TextBlock content={block.content as string} className={className} />;
    case 'image':
      return <ImageBlock url={block.content as string} metadata={block.metadata} className={className} />;
    case 'table':
      return <TableBlock content={block.content as TableContent} metadata={block.metadata} className={className} />;
    case 'chart':
      return <ChartBlock content={block.content as ChartContent} metadata={block.metadata} className={className} />;
    case 'latex':
      return <LatexBlock formula={block.content as string} metadata={block.metadata} className={className} />;
    case 'mixed':
      return <MixedBlock blocks={block.content as ContentBlock[]} className={className} />;
    default:
      return <div className={className}>Unsupported content type</div>;
  }
};

// Text Block
const TextBlock: React.FC<{ content: string; className?: string }> = ({ content, className }) => {
  return <div className={className} dangerouslySetInnerHTML={{ __html: content }} />;
};

// Image Block
const ImageBlock: React.FC<{ url: string; metadata?: any; className?: string }> = ({ url, metadata, className }) => {
  return (
    <figure className={`${className || ''} my-4`}>
      <img
        src={url}
        alt={metadata?.alt || ''}
        width={metadata?.width}
        height={metadata?.height}
        className="max-w-full h-auto rounded-lg shadow-md"
        loading="lazy"
      />
      {metadata?.caption && (
        <figcaption className="mt-2 text-sm text-gray-600 text-center italic">
          {metadata.caption}
        </figcaption>
      )}
    </figure>
  );
};

// Table Block
const TableBlock: React.FC<{ content: TableContent; metadata?: any; className?: string }> = ({
  content,
  metadata,
  className,
}) => {
  const bordered = metadata?.bordered !== false;
  const striped = metadata?.striped !== false;

  return (
    <div className={`${className || ''} my-4 overflow-x-auto`}>
      <table
        className={`min-w-full ${bordered ? 'border border-gray-300' : ''} ${
          striped ? 'divide-y divide-gray-300' : ''
        }`}
      >
        <thead className="bg-gray-50">
          <tr>
            {content.headers.map((header, index) => (
              <th
                key={index}
                className={`px-4 py-2 text-left text-sm font-semibold text-gray-900 ${
                  bordered ? 'border border-gray-300' : ''
                }`}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className={striped ? 'divide-y divide-gray-200 bg-white' : 'bg-white'}>
          {content.rows.map((row, rowIndex) => (
            <tr key={rowIndex} className={striped && rowIndex % 2 === 1 ? 'bg-gray-50' : ''}>
              {row.map((cell, cellIndex) => (
                <td
                  key={cellIndex}
                  className={`px-4 py-2 text-sm text-gray-700 ${bordered ? 'border border-gray-300' : ''}`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {metadata?.caption && (
        <p className="mt-2 text-sm text-gray-600 text-center italic">{metadata.caption}</p>
      )}
    </div>
  );
};

// Chart Block (ECharts)
const ChartBlock: React.FC<{ content: ChartContent; metadata?: any; className?: string }> = ({
  content,
  metadata,
  className,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chartRef.current) {
      const chart = echarts.init(chartRef.current);
      chart.setOption(content.echarts);

      // Cleanup
      return () => {
        chart.dispose();
      };
    }
  }, [content.echarts]);

  const width = metadata?.width || '100%';
  const height = metadata?.height || 400;

  return (
    <div className={`${className || ''} my-4`}>
      <div ref={chartRef} style={{ width, height }} />
      {metadata?.caption && (
        <p className="mt-2 text-sm text-gray-600 text-center italic">{metadata.caption}</p>
      )}
    </div>
  );
};

// LaTeX Block (KaTeX)
const LatexBlock: React.FC<{ formula: string; metadata?: any; className?: string }> = ({
  formula,
  metadata,
  className,
}) => {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (ref.current) {
      try {
        const displayMode = metadata?.display === 'block';
        katex.render(formula, ref.current, {
          displayMode,
          throwOnError: false,
        });
      } catch (error) {
        console.error('KaTeX rendering error:', error);
        if (ref.current) {
          ref.current.textContent = formula;
        }
      }
    }
  }, [formula, metadata]);

  const display = metadata?.display || 'inline';

  return (
    <span
      ref={ref}
      className={`${className || ''} ${display === 'block' ? 'block my-4 text-center' : 'inline'}`}
    />
  );
};

// Mixed Block (Recursive)
const MixedBlock: React.FC<{ blocks: ContentBlock[]; className?: string }> = ({ blocks, className }) => {
  return (
    <div className={className}>
      {blocks.map((block, index) => (
        <ContentBlockRenderer key={index} block={block} />
      ))}
    </div>
  );
};

export default RichContentRenderer;
