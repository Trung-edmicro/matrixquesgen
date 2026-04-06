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

// Chart Block (ECharts) - Image-based rendering v3.0
const ChartBlock: React.FC<{ content: ChartContent; metadata?: any; className?: string }> = ({
  content,
  metadata,
  className,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<any>(null);
  const [chartImageUrl, setChartImageUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  // Memoize content parsing to prevent unnecessary re-renders
  const memoizedContent = useMemo(() => {
    if (typeof content === 'string') {
      try {
        return JSON.parse(content);
      } catch {
        return content;
      }
    }
    return content;
  }, [content]);

  // Main effect: Initialize echarts, render, convert to image, display
  useEffect(() => {
    if (!chartRef.current) return;

    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let retryCount = 0;
    const MAX_RETRIES = 20; // Max 2 seconds of retries (20 × 100ms)

    const initAndRenderChart = async () => {
      try {
        setIsLoading(true);

        // 1️⃣ Parse chart options
        let options = memoizedContent?.echarts || memoizedContent;
        if (!options || typeof options !== 'object') {
          console.warn('❌ No chart options found in content');
          setIsLoading(false);
          return;
        }

        // 2️⃣ Resolve chart placeholders
        let resolvedOptions;
        try {
          resolvedOptions = resolveChartPlaceholders(options);
        } catch (resolveErr) {
          console.error('❌ Failed to resolve placeholders:', resolveErr);
          setIsLoading(false);
          return;
        }

        // 3️⃣ Wait for container to be sized
        if (!chartRef.current) {
          console.warn('❌ Chart ref not available');
          setIsLoading(false);
          return;
        }
        void chartRef.current.offsetHeight; // Force reflow
        const rect = chartRef.current.getBoundingClientRect();

        if (rect.width <= 0 || rect.height <= 0) {
          if (retryCount < MAX_RETRIES) {
            retryCount++;
            console.log(`⏳ Container sizing... (${retryCount}/${MAX_RETRIES})`);
            timeoutId = setTimeout(initAndRenderChart, 100);
            return;
          } else {
            console.warn('❌ Container never sized after retries');
            setIsLoading(false);
            return;
          }
        }

        const containerWidth = Math.round(rect.width);
        const containerHeight = Math.round(rect.height);

        // 4️⃣ Initialize echarts
        if (!chartInstance.current) {
          chartInstance.current = echarts.init(chartRef.current!, null, { useDirtyRect: true });
        }

        chartInstance.current.setOption(resolvedOptions);

        // CRITICAL: Ensure echarts resizes to match container
        chartInstance.current.resize();

        // Wait for echarts to render initial frame
        await new Promise(resolve => setTimeout(resolve, 100));

        // After initial render, get actual canvas and check if we need to resize
        const canvasAfterInit = chartRef.current?.querySelector('canvas');
        if (canvasAfterInit) {
          const canvasWidth = parseInt(canvasAfterInit.getAttribute('width') || '0');
          const canvasHeight = parseInt(canvasAfterInit.getAttribute('height') || '0');

          console.log(
            `📊 Initial canvas: ${canvasWidth}×${canvasHeight}px (container: ${containerWidth}×${containerHeight}px)`
          );

          // The issue: echarts already set canvas attributes with DPR
          // We need to ensure the CSS style matches for proper display
          (canvasAfterInit as HTMLCanvasElement).style.width = containerWidth + 'px';
          (canvasAfterInit as HTMLCanvasElement).style.height = containerHeight + 'px';
        }

        console.log(
          `📊 Chart initialized (${containerWidth}×${containerHeight}px, dpr=${window.devicePixelRatio})`
        );

        // 5️⃣ Wait for echarts to finish rendering before converting to image
        // For complex charts (bar, line), need more time to render all elements
        await new Promise(resolve => setTimeout(resolve, 800));

        // 6️⃣ Convert canvas to image with proper sizing
        const canvas2 = chartRef.current?.querySelector('canvas');
        if (!canvas2) {
          console.warn('⚠️  Canvas not found after render');
          setIsLoading(false);
          return;
        }

        const canvasDataUrl = canvas2.toDataURL('image/png', 1.0);
        const canvasRect = canvas2.getBoundingClientRect();

        console.log(
          `🎨 Canvas attributes: width=${canvas2.getAttribute('width')}, height=${canvas2.getAttribute('height')}, ` +
          `CSS: ${(canvas2 as HTMLCanvasElement).style.width} × ${(canvas2 as HTMLCanvasElement).style.height}, ` +
          `DOMRect: ${canvasRect.width}×${canvasRect.height}, ` +
          `Image size: ${(canvasDataUrl.length / 1024).toFixed(1)}KB`
        );

        // 7️⃣ Display the image
        setChartImageUrl(canvasDataUrl);
        console.log(
          `✅ Chart converted to image (${Math.round(canvasDataUrl.length / 1024)}KB)`
        );

        setIsLoading(false);
      } catch (error) {
        console.error('❌ Error initializing chart:', error);
        setIsLoading(false);
      }
    };

    // Wait for layout to settle, then initialize
    timeoutId = setTimeout(initAndRenderChart, 50);

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, [memoizedContent]);

  // Parse metadata
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

  // Get container size
  const getContainerSize = useCallback(() => {
    if (parsedMetadata?.width && parsedMetadata?.height) {
      const w =
        typeof parsedMetadata.width === 'number'
          ? parsedMetadata.width
          : parseInt(parsedMetadata.width);
      const h =
        typeof parsedMetadata.height === 'number'
          ? parsedMetadata.height
          : parseInt(parsedMetadata.height);
      return { width: w, height: h };
    }

    // Default chart size: 800x500 for all charts
    return { width: 800, height: 500 };
  }, [parsedMetadata]);

  const { width: containerWidth, height: containerHeight } = getContainerSize();

  return (
    <>
      {/* Hidden echarts container - positioned off-screen but with real dimensions */}
      <div
        ref={chartRef}
        style={{
          position: 'fixed',
          left: '-9999px',
          top: '-9999px',
          width: '800px',
          height: '500px',
          visibility: 'hidden',
          pointerEvents: 'none',
          overflow: 'visible',
          zIndex: -9999
        }}
      />

      {/* Visible image display */}
      <div
        style={{
          width: typeof containerWidth === 'number' ? `${containerWidth}px` : containerWidth,
          height: 'auto',
          margin: '0 auto',
          padding: 0,
          border: 'none',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'stretch',
          justifyContent: 'flex-start',
          overflow: 'hidden',
          boxSizing: 'border-box',
          backgroundColor: isLoading ? '#f5f5f5' : 'transparent',
          position: 'relative'
        }}
      >
        {isLoading ? (
          <div style={{ color: '#999', fontSize: '14px' }}>📊 Rendering chart...</div>
        ) : chartImageUrl ? (
          <img
            src={chartImageUrl}
            style={{
              width: '100%',
              height: 'auto',
              objectFit: 'contain',
              display: 'block',
            }}
            alt="Chart"
          />
        ) : (
          <div style={{ color: '#999', fontSize: '14px' }}>Chart failed to load</div>
        )}
      </div>
    </>
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
