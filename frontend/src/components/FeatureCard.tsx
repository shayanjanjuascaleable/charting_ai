import { motion, useReducedMotion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  delay?: number;
}

export const FeatureCard = ({ icon: Icon, title, description, delay = 0 }: FeatureCardProps) => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.6, ease: 'easeOut' }}
      viewport={{ once: true, margin: '-50px' }}
      whileHover={shouldReduceMotion ? {} : { 
        y: -8,
        transition: { duration: 0.2, ease: 'easeOut' }
      }}
      className="glass-card p-8 group relative overflow-hidden"
    >
      {/* Hover glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/0 via-primary/0 to-accent/0 group-hover:from-primary/5 group-hover:via-primary/0 group-hover:to-accent/5 transition-all duration-500 rounded-2xl" />
      
      <div className="relative z-10">
        <motion.div 
          className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-accent/10 transition-all duration-300 group-hover:bg-accent/20 group-hover:scale-110 group-hover:shadow-lg group-hover:shadow-accent/20"
          whileHover={shouldReduceMotion ? {} : { rotate: [0, -5, 5, -5, 0] }}
          transition={{ duration: 0.5 }}
        >
          <Icon className="h-7 w-7 text-accent transition-transform group-hover:scale-110" />
        </motion.div>
        <h3 className="mb-3 text-xl font-bold text-foreground group-hover:text-primary transition-colors duration-300">
          {title}
        </h3>
        <p className="text-base leading-relaxed text-muted-foreground font-light">
          {description}
        </p>
      </div>
    </motion.div>
  );
};
