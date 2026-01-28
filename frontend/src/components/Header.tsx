import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BarChart3, ArrowLeft, ArrowRight } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { LanguageToggle } from './LanguageToggle';
import { useLanguage } from '@/contexts/LanguageContext';

export const Header = () => {
  const { t, direction } = useLanguage();
  const location = useLocation();
  const isInsights = location.pathname === '/insights';

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl"
    >
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl" style={{ background: 'var(--gradient-primary)' }}>
            <BarChart3 className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold text-foreground">ChartingAI</span>
        </Link>

        <div className="flex items-center gap-3">
          {isInsights && (
            <Link to="/">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="btn-ghost flex items-center gap-2"
              >
                {direction === 'rtl' ? (
                  <ArrowRight className="h-4 w-4" />
                ) : (
                  <ArrowLeft className="h-4 w-4" />
                )}
                {t.backToHome}
              </motion.button>
            </Link>
          )}
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>
    </motion.header>
  );
};
