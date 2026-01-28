import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';

interface ChartSpec {
  chart_type: string;
  x_field: string | null;
  y_field: string | null;
  z_field?: string | null;
  bins?: number;
  reason?: string;
}

interface AutoChartProps {
  data: any[];
  chartSpec: ChartSpec;
  title?: string;
}

/**
 * Normalize chart type to canonical format (backward compatibility).
 * Maps old formats ("bar", "scatter") to new formats ("bar_chart", "scatter_plot").
 */
function normalizeChartType(chartType: string): string {
  const normalized = chartType.toLowerCase().trim();
  
  // Map old formats to canonical formats
  const typeMap: Record<string, string> = {
    'bar': 'bar_chart',
    'line': 'line_chart',
    'pie': 'pie_chart',
    'donut': 'donut_chart',
    'scatter': 'scatter_plot',
    'histogram': 'histogram',
    '3d_scatter': '3d_scatter_plot',
    '3d': '3d_scatter_plot',
    'table': 'table',
  };
  
  return typeMap[normalized] || normalized;
}

/**
 * Extract field names with robust fallback (backward compatibility).
 * Tries: x_field -> x -> labels (for pie/donut)
 */
function extractFields(chartSpec: ChartSpec, data: any[]): {
  x: string | null;
  y: string | null;
  z: string | null;
} {
  // Try canonical field names first
  let x = chartSpec.x_field ?? chartSpec.x ?? null;
  let y = chartSpec.y_field ?? chartSpec.y ?? null;
  let z = chartSpec.z_field ?? chartSpec.z ?? null;
  
  // For pie/donut, try labels/values as fallback
  if (!x && (chartSpec.chart_type === 'pie_chart' || chartSpec.chart_type === 'donut_chart')) {
    x = (chartSpec as any).labels ?? null;
  }
  if (!y && (chartSpec.chart_type === 'pie_chart' || chartSpec.chart_type === 'donut_chart')) {
    y = (chartSpec as any).values ?? null;
  }
  
  return { x, y, z };
}

export const AutoChart = ({ data, chartSpec, title }: AutoChartProps) => {
  const { theme } = useTheme();
  const { t } = useLanguage();
  const isDark = theme === 'dark';

  const plotlyConfig = useMemo(() => {
    if (!data || data.length === 0) {
      return null;
    }

    // Normalize chart type (backward compatibility)
    const chartType = normalizeChartType(chartSpec.chart_type);
    
    // Extract fields with robust fallback
    const { x: xField, y: yField, z: zField } = extractFields(chartSpec, data);

    // Get available columns for error messages
    const availableColumns = data.length > 0 ? Object.keys(data[0]) : [];
    
    try {
      switch (chartType) {
        // Canonical format
        case 'bar_chart':
        // Backward compatibility: old format (normalizeChartType should handle this, but extra safety)
        case 'bar': {
          if (!xField || !yField) return null;
          const xValues = data.map(row => String(row[xField] ?? ''));
          const yValues = data.map(row => Number(row[yField] ?? 0));
          
          return {
            data: [{
              type: 'bar',
              x: xValues,
              y: yValues,
              marker: { color: isDark ? '#3b82f6' : '#2563eb' }
            }],
            layout: {
              title: title || `${yField} by ${xField}`,
              xaxis: { title: xField },
              yaxis: { title: yField },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: isDark ? '#e2e8f0' : '#1e293b' }
            }
          };
        }

        case 'line_chart':
        // Backward compatibility: old format
        case 'line': {
          if (!xField || !yField) return null;
          const xValues = data.map(row => {
            const val = row[xField];
            return val instanceof Date ? val : new Date(val);
          });
          const yValues = data.map(row => Number(row[yField] ?? 0));
          
          return {
            data: [{
              type: 'scatter',
              mode: 'lines+markers',
              x: xValues,
              y: yValues,
              line: { color: isDark ? '#10b981' : '#059669' }
            }],
            layout: {
              title: title || `${yField} over time`,
              xaxis: { title: xField, type: 'date' },
              yaxis: { title: yField },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: isDark ? '#e2e8f0' : '#1e293b' }
            }
          };
        }

        case 'pie_chart':
        // Backward compatibility: old format
        case 'pie': {
          if (!xField || !yField) return null;
          const labels = data.map(row => String(row[xField] ?? ''));
          const values = data.map(row => Number(row[yField] ?? 0));
          
          return {
            data: [{
              type: 'pie',
              labels,
              values,
              hole: 0
            }],
            layout: {
              title: title || `${yField} by ${xField}`,
              paper_bgcolor: 'transparent',
              font: { color: isDark ? '#e2e8f0' : '#1e293b' }
            }
          };
        }

        case 'donut_chart':
        // Backward compatibility: old format
        case 'donut': {
          if (!xField || !yField) return null;
          const labels = data.map(row => String(row[xField] ?? ''));
          const values = data.map(row => Number(row[yField] ?? 0));
          
          return {
            data: [{
              type: 'pie',
              labels,
              values,
              hole: 0.4
            }],
            layout: {
              title: title || `${yField} by ${xField}`,
              paper_bgcolor: 'transparent',
              font: { color: isDark ? '#e2e8f0' : '#1e293b' }
            }
          };
        }

        case 'scatter_plot':
        // Backward compatibility: old format
        case 'scatter': {
          if (!xField || !yField) return null;
          const xValues = data.map(row => Number(row[xField] ?? 0));
          const yValues = data.map(row => Number(row[yField] ?? 0));
          
          return {
            data: [{
              type: 'scatter',
              mode: 'markers',
              x: xValues,
              y: yValues,
              marker: { color: isDark ? '#8b5cf6' : '#7c3aed', size: 8 }
            }],
            layout: {
              title: title || `${yField} vs ${xField}`,
              xaxis: { title: xField },
              yaxis: { title: yField },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: isDark ? '#e2e8f0' : '#1e293b' }
            }
          };
        }

        case 'histogram': {
          if (!xField) return null;
          const values = data.map(row => Number(row[xField] ?? 0)).filter(v => !isNaN(v));
          
          return {
            data: [{
              type: 'histogram',
              x: values,
              nbinsx: chartSpec.bins || 20,
              marker: { color: isDark ? '#f59e0b' : '#d97706' }
            }],
            layout: {
              title: title || `Distribution of ${xField}`,
              xaxis: { title: xField },
              yaxis: { title: 'Frequency' },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: isDark ? '#e2e8f0' : '#1e293b' }
            }
          };
        }

        case '3d_scatter_plot':
        // Backward compatibility: old format
        case '3d_scatter':
        case '3d': {
          if (!xField || !yField || !zField) return null;
          const xValues = data.map(row => Number(row[xField] ?? 0));
          const yValues = data.map(row => Number(row[yField] ?? 0));
          const zValues = data.map(row => Number(row[zField] ?? 0));
          
          return {
            data: [{
              type: 'scatter3d',
              mode: 'markers',
              x: xValues,
              y: yValues,
              z: zValues,
              marker: { 
                size: 5,
                color: zValues,
                colorscale: 'Viridis',
                showscale: true
              }
            }],
            layout: {
              title: title || `${zField} vs ${xField} vs ${yField}`,
              scene: {
                xaxis: { title: xField },
                yaxis: { title: yField },
                zaxis: { title: zField },
                bgcolor: 'transparent'
              },
              paper_bgcolor: 'transparent',
              font: { color: isDark ? '#e2e8f0' : '#1e293b' }
            }
          };
        }

        case 'table':
        default: {
          // Render as HTML table
          const columns = data.length > 0 ? Object.keys(data[0]) : [];
          const displayData = data.slice(0, 200); // Limit to 200 rows
          
          return {
            type: 'table',
            columns,
            data: displayData
          };
        }
      }
    } catch (error) {
      console.error('Error preparing chart data:', error);
      return null;
    }
  }, [data, chartSpec, title, isDark]);

  // Helper function to render helpful error message
  const renderErrorMessage = (message: string) => {
    const availableColumns = data.length > 0 ? Object.keys(data[0]) : [];
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground p-4 border border-dashed border-border rounded-lg">
        <p className="font-medium mb-2">{message}</p>
        <div className="text-xs text-center space-y-1">
          <p><strong>Chart Type:</strong> {chartSpec.chart_type}</p>
          <p><strong>Available Columns:</strong> {availableColumns.length > 0 ? availableColumns.join(', ') : 'None'}</p>
          {chartSpec.x_field && <p><strong>X Field:</strong> {chartSpec.x_field}</p>}
          {chartSpec.y_field && <p><strong>Y Field:</strong> {chartSpec.y_field}</p>}
          {chartSpec.z_field && <p><strong>Z Field:</strong> {chartSpec.z_field}</p>}
        </div>
      </div>
    );
  };

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <p>{t.noDataMessage || 'No data available'}</p>
      </div>
    );
  }

  if (!plotlyConfig) {
    // Extract fields for error message
    const { x: xField, y: yField, z: zField } = extractFields(chartSpec, data);
    const chartType = normalizeChartType(chartSpec.chart_type);
    
    let errorMessage = 'Unable to render chart. Missing required fields.';
    if (!xField && (chartType === 'bar_chart' || chartType === 'line_chart' || chartType === 'scatter_plot' || chartType === 'pie_chart' || chartType === 'donut_chart')) {
      errorMessage = `Missing X field (x_field). Required for ${chartType}.`;
    } else if (!yField && (chartType === 'bar_chart' || chartType === 'line_chart' || chartType === 'scatter_plot' || chartType === 'pie_chart' || chartType === 'donut_chart')) {
      errorMessage = `Missing Y field (y_field). Required for ${chartType}.`;
    } else if (!zField && chartType === '3d_scatter_plot') {
      errorMessage = `Missing Z field (z_field). Required for ${chartType}.`;
    }
    
    return renderErrorMessage(errorMessage);
  }

  // Handle table rendering
  if (plotlyConfig.type === 'table') {
    const { columns, data: tableData } = plotlyConfig as any;
    return (
      <div className="overflow-auto max-h-96">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-border">
              {columns.map((col: string) => (
                <th key={col} className="px-4 py-2 text-left font-semibold text-foreground">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.map((row: any, i: number) => (
              <tr key={i} className="border-b border-border/50 hover:bg-muted/50">
                {columns.map((col: string) => (
                  <td key={col} className="px-4 py-2 text-muted-foreground">
                    {String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Render Plotly chart
  return (
    <div className="w-full h-full">
      <Plot
        data={plotlyConfig.data}
        layout={plotlyConfig.layout}
        config={{
          responsive: true,
          displayModeBar: false,
        }}
        style={{ width: '100%', height: '400px' }}
      />
    </div>
  );
};

