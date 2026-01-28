import { motion } from 'framer-motion';

export const ChartSkeleton = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="glass-card overflow-hidden"
    >
      <div className="border-b border-border/50 px-4 py-3">
        <div className="skeleton h-5 w-3/4" />
      </div>
      <div className="p-4">
        <div className="relative h-[300px] overflow-hidden rounded-lg">
          <div className="skeleton absolute inset-0" />
          <div className="absolute inset-0 flex items-end justify-around p-4">
            {[0.6, 0.8, 0.4, 0.9, 0.5, 0.7].map((height, i) => (
              <motion.div
                key={i}
                initial={{ height: 0 }}
                animate={{ height: `${height * 100}%` }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="w-8 rounded-t-md bg-muted-foreground/20"
              />
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
