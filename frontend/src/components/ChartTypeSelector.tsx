import { motion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

// Chart types mapping: display label key -> backend enum value
const CHART_TYPES = [
  { id: 'bar_chart', labelKey: 'chartTypeBar' as const },
  { id: 'line_chart', labelKey: 'chartTypeLine' as const },
  { id: 'pie_chart', labelKey: 'chartTypePie' as const },
  { id: 'donut_chart', labelKey: 'chartTypeDonut' as const },
  { id: 'scatter_plot', labelKey: 'chartTypeScatter' as const },
  { id: 'histogram', labelKey: 'chartTypeHistogram' as const },
  { id: '3d_scatter_plot', labelKey: 'chartType3D' as const },
] as const;

export type ChartType = typeof CHART_TYPES[number]['id'] | null;

interface ChartTypeSelectorProps {
  selectedChartType: ChartType;
  onSelect: (chartType: ChartType) => void;
}

export const ChartTypeSelector = ({ selectedChartType, onSelect }: ChartTypeSelectorProps) => {
  const { t, direction } = useLanguage();

  return (
    <div className="space-y-3 border-t border-border/50 px-4 py-3">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <BarChart3 className="h-4 w-4 text-accent" />
        <span>{t.chartTypeTitle}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {CHART_TYPES.map((chartType, index) => {
          const isSelected = selectedChartType === chartType.id;
          return (
            <motion.button
              key={chartType.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.03 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(isSelected ? null : chartType.id)}
              className={`
                px-4 py-2 rounded-full text-sm font-medium transition-all duration-200
                ${isSelected
                  ? 'bg-accent text-accent-foreground shadow-md shadow-accent/30'
                  : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'
                }
              `}
              dir={direction}
            >
              {t[chartType.labelKey]}
            </motion.button>
          );
        })}
      </div>
      {!selectedChartType && (
        <p className="text-xs text-muted-foreground mt-2">{t.chartTypeHelper}</p>
      )}
    </div>
  );
};

