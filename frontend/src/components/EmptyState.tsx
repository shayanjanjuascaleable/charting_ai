import { motion } from 'framer-motion';
import { BarChart3, MessageSquare } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

export const EmptyState = () => {
  const { t } = useLanguage();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card flex flex-col items-center justify-center p-12 text-center"
    >
      <motion.div
        animate={{ y: [0, -10, 0] }}
        transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
        className="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-accent/10"
      >
        <BarChart3 className="h-10 w-10 text-accent" />
      </motion.div>
      <h3 className="mb-2 text-xl font-semibold text-foreground">{t.noCharts}</h3>
      <p className="mb-6 max-w-sm text-muted-foreground">{t.noChartsDesc}</p>
      <div className="flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-2">
        <MessageSquare className="h-4 w-4 text-accent" />
        <span className="text-sm font-medium text-accent">{t.chatPlaceholder}</span>
      </div>
    </motion.div>
  );
};
