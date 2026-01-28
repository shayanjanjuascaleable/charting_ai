import { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MoreVertical, Table, Download, Trash2, X } from 'lucide-react';
import Plot from 'react-plotly.js';
// @ts-ignore
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { translateChartJson, initializePlotlyLocale } from '@/utils/plotlyLocalization';
interface ChartCardProps {
  id: string;
  title: string;
  chartJson?: any; // Plotly JSON for rendering
  rawData: any[];
  onRemove: (id: string) => void;
}

export const ChartCard = ({ id, title, chartJson, rawData, onRemove }: ChartCardProps) => {
  const { theme } = useTheme();
  const { t, direction, language } = useLanguage();
  const [showMenu, setShowMenu] = useState(false);
  const [showDataModal, setShowDataModal] = useState(false);
  const plotRef = useRef<any>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Initialize Plotly locale when language changes
  useEffect(() => {
    initializePlotlyLocale(language);
  }, [language]);

  // Translate chart JSON based on current language
  const translatedChartJson = useMemo(() => {
    if (!chartJson || language === 'en') return chartJson;
    return translateChartJson(chartJson);
  }, [chartJson, language]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExportPng = () => {
    if (plotRef.current?.el) {
      import('plotly.js-dist-min').then((Plotly) => {
        Plotly.downloadImage(plotRef.current.el, {
          format: 'png',
          filename: title.replace(/\s+/g, '_'),
          width: 1200,
          height: 800,
        });
      });
    }
    setShowMenu(false);
  };

  const getChartLayout = () => {
    const isDark = theme === 'dark';
    const baseLayout = translatedChartJson?.layout || {};
    
    return {
      ...baseLayout,
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: {
        ...baseLayout.font,
        color: isDark ? '#e2e8f0' : '#1e293b',
        family: direction === 'rtl' ? 'Noto Sans Arabic, Inter, sans-serif' : 'Inter, Noto Sans Arabic, sans-serif',
      },
      xaxis: {
        ...baseLayout.xaxis,
        gridcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
        linecolor: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)',
        tickfont: { color: isDark ? '#94a3b8' : '#64748b' },
      },
      yaxis: {
        ...baseLayout.yaxis,
        gridcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
        linecolor: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)',
        tickfont: { color: isDark ? '#94a3b8' : '#64748b' },
      },
      legend: {
        ...baseLayout.legend,
        font: { color: isDark ? '#e2e8f0' : '#1e293b' },
      },
      margin: { t: 40, r: 20, b: 60, l: 60 },
      autosize: true,
    };
  };

  const columns = rawData.length > 0 ? Object.keys(rawData[0]) : [];

  return (
    <>
      <motion.div
        layout
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="glass-card group"
      >
        <div className="flex items-center justify-between border-b border-border/50 px-4 py-3">
          <h3 className="text-sm font-semibold text-foreground line-clamp-1">{title}</h3>
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="flex h-8 w-8 items-center justify-center rounded-lg opacity-0 transition-opacity group-hover:opacity-100 hover:bg-muted"
            >
              <MoreVertical className="h-4 w-4 text-muted-foreground" />
            </button>
            <AnimatePresence>
              {showMenu && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: -10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: -10 }}
                  className={`absolute ${direction === 'rtl' ? 'left-0' : 'right-0'} top-full z-50 mt-1 w-40 overflow-hidden rounded-xl border border-border bg-card shadow-lg`}
                >
                  <button
                    onClick={() => { setShowDataModal(true); setShowMenu(false); }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted"
                  >
                    <Table className="h-4 w-4" />
                    {t.viewData}
                  </button>
                  <button
                    onClick={handleExportPng}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted"
                  >
                    <Download className="h-4 w-4" />
                    {t.exportPng}
                  </button>
                  <button
                    onClick={() => { onRemove(id); setShowMenu(false); }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="h-4 w-4" />
                    {t.removeChart}
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
        <div className="plotly-container p-4">
          {translatedChartJson ? (
            // Manual chart selection mode: Use Plotly JSON rendering with locale
            <Plot
              key={`${id}-${language}`} // Force re-render on language change
              ref={plotRef}
              data={translatedChartJson?.data || []}
              layout={getChartLayout()}
              config={{
                responsive: true,
                displayModeBar: true, // Keep modebar for zoom/pan/download
                locale: language, // Set Plotly locale (ar or en)
                modeBarButtonsToRemove: [], // Keep all buttons (zoom, pan, download, etc.)
                toImageButtonOptions: {
                  format: 'png',
                  filename: title.replace(/\s+/g, '_'),
                  height: 800,
                  width: 1200,
                  scale: 1,
                },
              }}
              style={{ width: '100%', height: '300px' }}
            />
          ) : (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
              <p>No chart data available</p>
            </div>
          )}
        </div>
      </motion.div>

      {/* Data Modal */}
      <AnimatePresence>
        {showDataModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4"
            onClick={() => setShowDataModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              className="glass-card max-h-[80vh] w-full max-w-4xl overflow-hidden"
            >
              <div className="flex items-center justify-between border-b border-border/50 px-6 py-4">
                <h2 className="text-lg font-semibold text-foreground">{t.dataTable}</h2>
                <button
                  onClick={() => setShowDataModal(false)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-muted"
                >
                  <X className="h-5 w-5 text-muted-foreground" />
                </button>
              </div>
              <div className="max-h-[60vh] overflow-auto p-6">
                {rawData.length > 0 ? (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        {columns.map(col => (
                          <th key={col} className="px-4 py-3 text-start font-semibold text-foreground">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rawData.map((row, i) => (
                        <tr key={i} className="border-b border-border/50 hover:bg-muted/50">
                          {columns.map(col => (
                            <td key={col} className="px-4 py-3 text-muted-foreground">
                              {String(row[col] ?? '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-center text-muted-foreground">{t.noDataMessage}</p>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
