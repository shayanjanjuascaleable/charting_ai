import { motion } from 'framer-motion';
import { useLanguage } from '@/contexts/LanguageContext';
import { Languages } from 'lucide-react';

export const LanguageToggle = () => {
  const { language, toggleLanguage } = useLanguage();

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={toggleLanguage}
      className="relative flex h-10 items-center gap-2 rounded-xl border border-border bg-card/50 px-3 backdrop-blur-sm transition-colors hover:bg-muted"
      aria-label={language === 'en' ? 'Switch to Arabic' : 'Switch to English'}
    >
      <Languages className="h-4 w-4 text-muted-foreground" />
      <span className="text-sm font-medium text-foreground">
        {language === 'en' ? 'عربي' : 'EN'}
      </span>
    </motion.button>
  );
};
