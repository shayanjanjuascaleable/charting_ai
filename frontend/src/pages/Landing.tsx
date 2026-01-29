import { motion, useReducedMotion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Sparkles, BarChart2, Lightbulb, Zap, ArrowRight, ArrowLeft, MessageSquare, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { Header } from '@/components/Header';
import { FeatureCard } from '@/components/FeatureCard';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTheme } from '@/contexts/ThemeContext';

const Landing = () => {
  const navigate = useNavigate();
  const { t, direction } = useLanguage();
  const { theme } = useTheme();
  const shouldReduceMotion = useReducedMotion();
  
  // Demo state
  const [demoState, setDemoState] = useState<'typing' | 'processing' | 'complete'>('typing');
  const [typedText, setTypedText] = useState('');
  const [showCursor, setShowCursor] = useState(true);
  
  const exampleQuery = 'Total sales by region';
  
  // Typing animation
  useEffect(() => {
    if (demoState === 'typing' && typedText.length < exampleQuery.length) {
      const timer = setTimeout(() => {
        setTypedText(exampleQuery.slice(0, typedText.length + 1));
      }, 80);
      return () => clearTimeout(timer);
    } else if (demoState === 'typing' && typedText.length === exampleQuery.length) {
      const timer = setTimeout(() => {
        setDemoState('processing');
        setShowCursor(false);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [demoState, typedText, exampleQuery]);
  
  // Processing to complete
  useEffect(() => {
    if (demoState === 'processing') {
      const timer = setTimeout(() => {
        setDemoState('complete');
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [demoState]);
  
  // Mock chart data (static, frontend-only)
  // Use direct HSL values matching the CSS variables
  const chartColors = theme === 'dark' 
    ? ['hsl(243 75% 65%)', 'hsl(187 85% 50%)', 'hsl(262 83% 58%)', 'hsl(142 71% 45%)', 'hsl(38 92% 50%)']
    : ['hsl(243 75% 59%)', 'hsl(187 85% 43%)', 'hsl(262 83% 58%)', 'hsl(142 71% 45%)', 'hsl(38 92% 50%)'];

  const mockChartData = {
    data: [{
      type: 'bar',
      x: ['North America', 'EMEA', 'APAC', 'Latin America', 'Other'],
      y: [125000, 98000, 87000, 45000, 32000],
      marker: {
        color: chartColors,
        line: {
          color: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
          width: 1
        }
      },
      text: ['$125K', '$98K', '$87K', '$45K', '$32K'],
      textposition: 'outside',
    }],
    layout: {
      title: {
        text: 'Total Sales by Region',
        font: { size: 20, family: 'Inter, sans-serif' },
        x: 0.5,
        xanchor: 'center'
      },
      xaxis: {
        title: 'Region',
        gridcolor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
      },
      yaxis: {
        title: 'Sales ($)',
        gridcolor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
      },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: {
        color: theme === 'dark' ? '#e2e8f0' : '#1e293b',
        family: 'Inter, sans-serif',
      },
      margin: { t: 60, r: 20, b: 60, l: 60 },
      autosize: true,
    },
  };

  const features = [
    { icon: Sparkles, title: t.featureAITitle, description: t.featureAIDesc },
    { icon: BarChart2, title: t.featureChartsTitle, description: t.featureChartsDesc },
    { icon: Lightbulb, title: t.featureInsightsTitle, description: t.featureInsightsDesc },
    { icon: Zap, title: t.featureRealtimeTitle, description: t.featureRealtimeDesc },
  ];

  return (
    <div className="min-h-screen hero-gradient relative">
      <Header />
      
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-32 pb-24">
        {/* Enhanced background decorations with depth */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {/* Primary gradient blob */}
          <motion.div
            animate={shouldReduceMotion ? {} : { 
              rotate: 360,
              scale: [1, 1.1, 1],
            }}
            transition={{ 
              rotate: { duration: 50, repeat: Infinity, ease: 'linear' },
              scale: { duration: 8, repeat: Infinity, ease: 'easeInOut' }
            }}
            className="absolute -top-1/2 -right-1/4 h-[800px] w-[800px] rounded-full opacity-25 blur-3xl"
            style={{ background: 'radial-gradient(circle, hsl(var(--primary) / 0.3) 0%, transparent 70%)' }}
          />
          {/* Accent gradient blob */}
          <motion.div
            animate={shouldReduceMotion ? {} : { 
              rotate: -360,
              scale: [1, 1.15, 1],
            }}
            transition={{ 
              rotate: { duration: 60, repeat: Infinity, ease: 'linear' },
              scale: { duration: 10, repeat: Infinity, ease: 'easeInOut' }
            }}
            className="absolute -bottom-1/2 -left-1/4 h-[600px] w-[600px] rounded-full opacity-20 blur-3xl"
            style={{ background: 'radial-gradient(circle, hsl(var(--accent) / 0.35) 0%, transparent 70%)' }}
          />
          {/* Subtle floating shape */}
          <motion.div
            animate={shouldReduceMotion ? {} : {
              y: [0, -30, 0],
              opacity: [0.1, 0.15, 0.1],
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: 'easeInOut'
            }}
            className="absolute top-1/3 right-1/3 h-[400px] w-[400px] rounded-full opacity-10 blur-2xl"
            style={{ background: 'radial-gradient(circle, hsl(var(--primary) / 0.4) 0%, transparent 70%)' }}
          />
        </div>

        <div className="container mx-auto px-4 relative z-10">
          <div className="mx-auto max-w-5xl text-center">
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              className="mb-8"
            >
              <motion.span 
                whileHover={{ scale: 1.05 }}
                className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 backdrop-blur-sm px-5 py-2 text-sm font-semibold text-primary shadow-sm"
              >
                <Sparkles className="h-4 w-4" />
                {direction === 'rtl' ? 'مدعوم بالذكاء الاصطناعي' : 'Powered by AI'}
              </motion.span>
            </motion.div>

            {/* Hero Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1, ease: 'easeOut' }}
              className="mb-8 text-5xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl xl:text-8xl leading-[1.1]"
            >
              <span className="text-gradient-primary block mb-2">{t.heroTitle}</span>
              <span className="block text-foreground">{t.heroSubtitle}</span>
            </motion.h1>

            {/* Hero Description */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2, ease: 'easeOut' }}
              className="mx-auto mb-12 max-w-3xl text-xl text-muted-foreground leading-relaxed font-light"
            >
              {t.heroDescription}
            </motion.p>

            {/* CTA Button */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.3, ease: 'easeOut' }}
            >
              <motion.button
                whileHover={shouldReduceMotion ? {} : { 
                  scale: 1.02,
                  boxShadow: '0 0 60px hsl(var(--primary) / 0.4)'
                }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/insights')}
                className="btn-primary group text-lg px-8 py-4 relative overflow-hidden"
              >
                <span className="relative z-10 flex items-center gap-2">
                  {t.ctaButton}
                  {direction === 'rtl' ? (
                    <ArrowLeft className="h-5 w-5 transition-transform group-hover:-translate-x-1" />
                  ) : (
                    <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
                  )}
                </span>
                {/* Shimmer effect */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                  initial={{ x: '-100%' }}
                  whileHover={{ x: '200%' }}
                  transition={{ duration: 0.6 }}
                />
              </motion.button>
            </motion.div>
          </div>

          {/* Query to Chart Demo */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4, ease: 'easeOut' }}
            className="mx-auto mt-20 max-w-6xl"
          >
            <div className="space-y-6">
              {/* 1. Large Chat Input */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.6 }}
                className="relative"
              >
                <div className="glass-card overflow-hidden p-1.5">
                  <div className="relative rounded-2xl bg-card/70 backdrop-blur-xl p-6 border border-border/50">
                    <div className="flex items-center gap-4">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                        <MessageSquare className="h-6 w-6 text-primary" />
                      </div>
                      <div className="flex-1 relative">
                        <div className="flex items-center min-h-[48px]">
                          <span className="text-lg font-medium text-foreground">
                            {typedText}
                            {showCursor && demoState === 'typing' && (
                              <motion.span
                                animate={{ opacity: [1, 0, 1] }}
                                transition={{ duration: 0.8, repeat: Infinity }}
                                className="inline-block w-0.5 h-5 bg-primary ml-1 align-middle"
                              />
                            )}
                          </span>
                          {demoState === 'typing' && typedText.length === 0 && (
                            <span className="text-lg text-muted-foreground">
                              Ask your data a question…
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* 2. AI Processing State */}
              <AnimatePresence>
                {demoState === 'processing' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="flex items-center justify-center gap-3 py-4"
                  >
                    <Loader2 className="h-5 w-5 text-primary animate-spin" />
                    <span className="text-sm font-medium text-muted-foreground">
                      Analyzing data...
                    </span>
                    <div className="flex gap-1">
                      {[0, 1, 2].map((i) => (
                        <motion.div
                          key={i}
                          className="h-2 w-2 rounded-full bg-primary"
                          animate={shouldReduceMotion ? { opacity: 0.6 } : {
                            opacity: [0.3, 1, 0.3],
                            scale: [1, 1.2, 1],
                          }}
                          transition={shouldReduceMotion ? {} : {
                            duration: 1,
                            repeat: Infinity,
                            delay: i * 0.2,
                            ease: 'easeInOut'
                          }}
                        />
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* 3. Chart Output */}
              <AnimatePresence>
                {demoState === 'complete' && (
                  <motion.div
                    initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={{ duration: shouldReduceMotion ? 0.3 : 0.6, ease: 'easeOut' }}
                    className="glass-card overflow-hidden"
                  >
                    <div className="p-6">
                      <div className="plotly-container" style={{ height: '400px', width: '100%' }}>
                        <Plot
                          data={mockChartData.data}
                          layout={mockChartData.layout}
                          config={{
                            responsive: true,
                            displayModeBar: false,
                            staticPlot: true,
                          }}
                          style={{ width: '100%', height: '100%' }}
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section - Enhanced */}
      <section className="py-24 relative">
        {/* Subtle background accent */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-accent/5 to-transparent" />
        
        <div className="container mx-auto px-4 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="mb-16 text-center"
          >
            <h2 className="mb-5 text-4xl font-bold text-foreground sm:text-5xl lg:text-6xl tracking-tight">
              {direction === 'rtl' ? 'قدرات قوية' : 'Powerful Capabilities'}
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-muted-foreground leading-relaxed font-light">
              {direction === 'rtl' 
                ? 'كل ما تحتاجه لتحويل بياناتك إلى قرارات ذكية'
                : 'Everything you need to transform data into smart decisions'
              }
            </p>
          </motion.div>

          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <FeatureCard
                key={feature.title}
                icon={feature.icon}
                title={feature.title}
                description={feature.description}
                delay={index * 0.1}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          © 2026 Scaleable Solutions. {direction === 'rtl' ? 'جميع الحقوق محفوظة.' : 'All rights reserved.'}
          {import.meta.env.VITE_BUILD_SHA && (
            <span className="block mt-2 text-xs opacity-60">
              Build: {import.meta.env.VITE_BUILD_SHA.substring(0, 7)}
            </span>
          )}
        </div>
      </footer>
    </div>
  );
};

export default Landing;
