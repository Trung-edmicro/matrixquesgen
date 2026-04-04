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
import { useEffect, useRef, useCallback, useMemo, useState } from 'react';
import 'katex/dist/katex.min.css';
import katex from 'katex';
import { resolveChartPlaceholders } from './chartPlaceholderResolver';

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

// Chart Block (ECharts) - REWRITTEN v2.0
const ChartBlock: React.FC<{ content: ChartContent; metadata?: any; className?: string }> = ({
  content,
  metadata,
  className,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<any>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  // Parse metadata once
  const parsedMetadata = useMemo(() => {
    if (typeof metadata === 'string') {
      try {
        return JSON.parse(metadata);
      } catch (e) {
        return null;
      }
    }
    return metadata;
  }, [metadata]);

  // Get container CSS dimensions
  const getContainerSize = useCallback(() => {
    const sw = window.innerWidth;

    if (parsedMetadata?.width && parsedMetadata?.height) {
      const w = typeof parsedMetadata.width === 'number'
        ? parsedMetadata.width
        : parseInt(parsedMetadata.width);
      const h = typeof parsedMetadata.height === 'number'
        ? parsedMetadata.height
        : parseInt(parsedMetadata.height);
      return { width: w, height: h };
    }

    // Responsive fallback
    if (sw < 640) return { width: '100%', height: 300 };
    if (sw < 1024) return { width: '95%', height: 450 };
    if (sw < 1280) return { width: 820, height: 480 };
    return { width: 850, height: 500 };
  }, [parsedMetadata]);

  // Calculate canvas DOM dimensions from actual container size
  const calculateCanvasDimensions = useCallback(() => {
    if (!chartRef.current) return null;

    try {
      const rect = chartRef.current.getBoundingClientRect();
      let containerWidth = Math.round(rect.width);
      let containerHeight = Math.round(rect.height);

      if (containerWidth <= 0 && chartRef.current.offsetWidth) {
        containerWidth = chartRef.current.offsetWidth;
      }
      if (containerHeight <= 0 && chartRef.current.offsetHeight) {
        containerHeight = chartRef.current.offsetHeight;
      }

      if (containerWidth <= 0 || containerHeight <= 0) {
        console.warn(`⚠️  Invalid container: ${containerWidth}x${containerHeight}`);
        return null;
      }

      const aspectRatio = containerWidth / containerHeight;
      const isPieChart = Math.abs(aspectRatio - 1) < 0.2;

      let canvasWidth, canvasHeight;

      if (isPieChart) {
        const size = Math.min(containerWidth, containerHeight);
        canvasWidth = Math.round(size);
        canvasHeight = Math.round(size);
      } else {
        const bufferPercent = 0.05;
        const buffer = Math.max(50, Math.round(containerWidth * bufferPercent));
        canvasWidth = Math.round(containerWidth + buffer);
        canvasHeight = Math.round(containerHeight);
      }

      canvasWidth = Math.max(50, canvasWidth);
      canvasHeight = Math.max(50, canvasHeight);

      return { canvasWidth, canvasHeight, containerWidth, containerHeight, isPieChart };
    } catch (e) {
      console.error('Error calculating canvas dimensions:', e);
      return null;
    }
  }, []);

  // Apply canvas DOM attributes
  const applyCanvasDimensions = useCallback(() => {
    if (!chartRef.current || !chartInstanceRef.current) return;

    const dims = calculateCanvasDimensions();
    if (!dims) return;

    try {
      const canvas = chartRef.current.querySelector('canvas');
      if (!canvas) return;

      const currentWidth = parseInt(canvas.getAttribute('width') || '0');
      const currentHeight = parseInt(canvas.getAttribute('height') || '0');

      if (
        Math.abs(currentWidth - dims.canvasWidth) > 2 ||
        Math.abs(currentHeight - dims.canvasHeight) > 2
      ) {
        canvas.setAttribute('width', dims.canvasWidth.toString());
        canvas.setAttribute('height', dims.canvasHeight.toString());
        chartInstanceRef.current.resize();

        console.log(
          `📊 Canvas: ${currentWidth}×${currentHeight} → ` +
          `${dims.canvasWidth}×${dims.canvasHeight} (${dims.isPieChart ? 'pie' : 'bar'})`
        );
      }
    } catch (e) {
      console.error('Error applying canvas dimensions:', e);
    }
  }, [calculateCanvasDimensions]);

  // Main Effect: init chart + setup observers
  useEffect(() => {
    if (!chartRef.current || !content.echarts) return;

    try {
      // 1. Resolve chart options
      let resolvedOption;
      try {
        resolvedOption = resolveChartPlaceholders(content.echarts);
      } catch (resolveErr) {
        console.error('Failed to resolve chart placeholders:', resolveErr);
        return;
      }

      // 2. Initialize echarts
      if (!chartInstanceRef.current) {
        chartInstanceRef.current = echarts.init(chartRef.current, null, {
          useDirtyRect: true
        });
      }

      chartInstanceRef.current.setOption(resolvedOption);
      console.log('📊 Chart initialized');

      // 3. Setup DUAL dimension tracking (RAF + ResizeObserver)
      let lastObservedWidth = 0;
      let lastObservedHeight = 0;
      let rAFId: number | null = null;

      // Core function: applies canvas dimensions
      const syncCanvasDimensions = () => {
        const dims = calculateCanvasDimensions();
        if (!dims) return;

        try {
          const canvas = chartRef.current?.querySelector('canvas');
          if (!canvas) return;

          const currentWidth = parseInt(canvas.getAttribute('width') || '0');
          const currentHeight = parseInt(canvas.getAttribute('height') || '0');

          if (
            Math.abs(currentWidth - dims.canvasWidth) > 2 ||
            Math.abs(currentHeight - dims.canvasHeight) > 2
          ) {
            canvas.setAttribute('width', dims.canvasWidth.toString());
            canvas.setAttribute('height', dims.canvasHeight.toString());
            chartInstanceRef.current?.resize();

            console.log(
              `📊 Canvas sync: ${currentWidth}×${currentHeight} ` +
              `→ ${dims.canvasWidth}×${dims.canvasHeight}`
            );
          }
        } catch (e) {
          console.error('Error syncing canvas dimensions:', e);
        }
      };

      // Monitor: Use RAF for continuous dimension tracking
      const monitorDimensions = () => {
        if (!chartRef.current) {
          if (rAFId) cancelAnimationFrame(rAFId);
          return;
        }

        const rect = chartRef.current.getBoundingClientRect();
        const currWidth = Math.round(rect.width);
        const currHeight = Math.round(rect.height);

        if (Math.abs(currWidth - lastObservedWidth) > 2 || 
            Math.abs(currHeight - lastObservedHeight) > 2) {
          lastObservedWidth = currWidth;
          lastObservedHeight = currHeight;
          syncCanvasDimensions();
        }

        rAFId = requestAnimationFrame(monitorDimensions);
      };

      monitorDimensions();

      // Also use ResizeObserver as backup
      if (!resizeObserverRef.current) {
        resizeObserverRef.current = new ResizeObserver(() => {
          syncCanvasDimensions();
        });
      }

      resizeObserverRef.current.observe(chartRef.current);

      // 4. Handle window resize
      const handleWindowResize = () => {
        syncCanvasDimensions();
      };
      window.addEventListener('resize', handleWindowResize, { passive: true });

      // 5. Initial sync
      syncCanvasDimensions();

      return () => {
        window.removeEventListener('resize', handleWindowResize);
        if (rAFId) cancelAnimationFrame(rAFId);
        if (resizeObserverRef.current) {
          resizeObserverRef.current.disconnect();
          resizeObserverRef.current = null;
        }
        if (chartInstanceRef.current) {
          chartInstanceRef.current.dispose();
          chartInstanceRef.current = null;
        }
      };
    } catch (error) {
      console.error('Failed to initialize chart:', error);
    }
  }, [content.echarts, calculateCanvasDimensions]);

  const { width: containerWidth, height: containerHeight } = getContainerSize();

  return (
    <div
      ref={chartRef}
      style={{
        width: typeof containerWidth === 'number' ? `${containerWidth}px` : containerWidth,
        height: typeof containerHeight === 'number' ? `${containerHeight}px` : containerHeight,
        margin: '0 auto',
        padding: 0,
        border: 'none',
        display: 'block',
        overflow: 'visible',
        boxSizing: 'border-box'
      }}
    />
  );
}
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
