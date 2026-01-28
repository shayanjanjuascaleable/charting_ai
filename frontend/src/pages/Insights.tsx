import { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, RotateCcw, Download } from 'lucide-react';
import { Header } from '@/components/Header';
import { ChartCard } from '@/components/ChartCard';
import { ChatPanel, MobileChatButton } from '@/components/ChatPanel';
import { EmptyState } from '@/components/EmptyState';
import { ChartSkeleton } from '@/components/ChartSkeleton';
import { useLanguage } from '@/contexts/LanguageContext';

interface ChartData {
  id: string;
  title: string;
  chartJson?: any; // Plotly JSON for rendering
  rawData: any[];
}

const Insights = () => {
  const { t, direction } = useLanguage();
  const [charts, setCharts] = useState<ChartData[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showMobileChat, setShowMobileChat] = useState(false);

  const handleChartGenerated = useCallback((data: {
    title: string;
    chartJson?: any;
    rawData: any[];
    suggestions?: string[];
  }) => {
    const newChart: ChartData = {
      id: Date.now().toString(),
      title: data.title,
      chartJson: data.chartJson,
      rawData: data.rawData,
    };
    setCharts(prev => [newChart, ...prev]);
    if (data.suggestions && data.suggestions.length > 0) {
      setSuggestions(data.suggestions);
    }
  }, []);

  const handleRemoveChart = useCallback((id: string) => {
    setCharts(prev => prev.filter(chart => chart.id !== id));
  }, []);

  const handleRefreshCharts = useCallback(() => {
    // UI-only: Clear all charts from the UI
    setCharts([]);
    setSuggestions([]);
  }, []);

  const chartsContainerRef = useRef<HTMLDivElement>(null);

  const handleDownloadDashboard = useCallback(async () => {
    // Frontend-only: Export dashboard as image
    if (!chartsContainerRef.current || charts.length === 0) {
      return;
    }

    try {
      // Dynamically import html2canvas if available
      const html2canvas = (await import('html2canvas')).default;
      
      // Get background color from CSS variable or computed style
      const root = document.documentElement;
      const bgColor = getComputedStyle(root).getPropertyValue('--background').trim() || 
                      getComputedStyle(root).backgroundColor || 
                      '#ffffff';
      
      const canvas = await html2canvas(chartsContainerRef.current, {
        backgroundColor: bgColor,
        scale: 2,
        useCORS: true,
        logging: false,
        scrollY: 0, // Start from top
        windowWidth: chartsContainerRef.current.scrollWidth,
        windowHeight: chartsContainerRef.current.scrollHeight,
      });

      // Convert canvas to blob and download
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `dashboard-${new Date().toISOString().split('T')[0]}.png`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }
      }, 'image/png');
    } catch (error) {
      console.error('Failed to export dashboard:', error);
      // Fallback: Try browser print
      window.print();
    }
  }, [charts.length]);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 pt-24 pb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-foreground">{t.dashboardTitle}</h1>
        </motion.div>

        <div className="flex flex-col gap-6 lg:flex-row">
          {/* Chart Grid */}
          <div className="flex-1 order-2 lg:order-1 flex flex-col">
            {/* Utility Bar */}
            {charts.length > 0 && (
              <div className="flex items-center justify-end gap-3 mb-4 pb-3 border-b border-border/50">
                <button
                  onClick={handleRefreshCharts}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
                  title={t.refreshCharts}
                  dir={direction}
                >
                  <RotateCcw className="h-4 w-4" />
                  <span>{t.refreshCharts}</span>
                </button>
                <button
                  onClick={handleDownloadDashboard}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
                  title={t.downloadDashboard}
                  dir={direction}
                >
                  <Download className="h-4 w-4" />
                  <span>{t.downloadDashboard}</span>
                </button>
              </div>
            )}

            {/* Charts Container with Scroll */}
            <div
              ref={chartsContainerRef}
              className="flex-1 overflow-y-auto"
              style={{ maxHeight: '70vh' }}
            >
              {charts.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="grid gap-6 sm:grid-cols-1 xl:grid-cols-2 pb-4">
                  <AnimatePresence mode="popLayout">
                    {isLoading && <ChartSkeleton key="skeleton" />}
                    {charts.map((chart) => (
                      <ChartCard
                        key={chart.id}
                        id={chart.id}
                        title={chart.title}
                        chartJson={chart.chartJson}
                        rawData={chart.rawData}
                        onRemove={handleRemoveChart}
                      />
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </div>
          </div>

          {/* Desktop Chat Panel */}
          <div className="hidden lg:block w-full lg:w-[400px] order-1 lg:order-2">
            <div className="sticky top-24">
              <ChatPanel
                onChartGenerated={handleChartGenerated}
                suggestions={suggestions}
              />
            </div>
          </div>
        </div>
      </main>

      {/* Mobile Chat */}
      <AnimatePresence>
        {showMobileChat && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm lg:hidden"
          >
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 25 }}
              className="absolute bottom-0 left-0 right-0 max-h-[85vh]"
            >
              <div className="relative">
                <button
                  onClick={() => setShowMobileChat(false)}
                  className="absolute -top-12 right-4 flex h-10 w-10 items-center justify-center rounded-full bg-card shadow-lg"
                >
                  <X className="h-5 w-5 text-foreground" />
                </button>
                <ChatPanel
                  onChartGenerated={(data) => {
                    handleChartGenerated(data);
                    setShowMobileChat(false);
                  }}
                  suggestions={suggestions}
                />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <MobileChatButton onClick={() => setShowMobileChat(true)} />
    </div>
  );
};

export default Insights;
