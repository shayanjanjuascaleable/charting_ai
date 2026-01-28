import React, { createContext, useContext, useEffect, useState } from 'react';

type Language = 'en' | 'ar';
type Direction = 'ltr' | 'rtl';

interface Translations {
  // Landing page
  heroTitle: string;
  heroSubtitle: string;
  heroDescription: string;
  ctaButton: string;
  featureAITitle: string;
  featureAIDesc: string;
  featureChartsTitle: string;
  featureChartsDesc: string;
  featureInsightsTitle: string;
  featureInsightsDesc: string;
  featureRealtimeTitle: string;
  featureRealtimeDesc: string;
  
  // Dashboard
  dashboardTitle: string;
  chatPlaceholder: string;
  sendButton: string;
  generating: string;
  noCharts: string;
  noChartsDesc: string;
  suggestionsTitle: string;
  chartTypeTitle: string;
  chartTypeHelper: string;
  viewData: string;
  exportPng: string;
  removeChart: string;
  dataTable: string;
  close: string;
  chatTitle: string;
  minimizeChat: string;
  expandChat: string;
  welcomeMessage: string;
  errorMessage: string;
  noDataMessage: string;
  backToHome: string;
  // Chart types
  chartTypeBar: string;
  chartTypeLine: string;
  chartTypePie: string;
  chartTypeDonut: string;
  chartTypeScatter: string;
  chartTypeHistogram: string;
  chartType3D: string;
  // Suggested questions
  moreSuggestions: string;
  suggestionTotalRevenueByRegion: string;
  suggestionTop10AccountsByRevenue: string;
  suggestionRevenueByIndustry: string;
  suggestionAccountsCreatedByMonth: string;
  suggestionAverageRevenuePerAccount: string;
  suggestionAccountDistributionByRegion: string;
  suggestionHighestRevenueAccounts: string;
  suggestionAccountsByIndustryType: string;
  suggestionContactsByRole: string;
  suggestionContactsCreatedOverTime: string;
  suggestionContactsPerAccount: string;
  suggestionTopRolesDistribution: string;
  suggestionLeadsByStatus: string;
  suggestionLeadsBySource: string;
  suggestionLeadBudgetDistribution: string;
  suggestionLeadsCreatedByMonth: string;
  suggestionConversionRateBySource: string;
  suggestionAverageLeadBudget: string;
  suggestionOpportunitiesByStage: string;
  suggestionTotalOpportunityValue: string;
  suggestionOpportunitiesByStageAndValue: string;
  suggestionExpectedCloseDates: string;
  suggestionWonOpportunitiesValue: string;
  suggestionPipelineByStage: string;
  suggestionRevenueDistributionLast30Days: string;
  suggestionMonthlyRevenueTrends: string;
  suggestionQuarterlyPerformance: string;
  suggestionYearOverYearGrowth: string;
  suggestionTotalPipelineValue: string;
  suggestionConversionFunnelAnalysis: string;
  suggestionRevenueVsOpportunities: string;
  // Dashboard utility buttons
  refreshCharts: string;
  downloadDashboard: string;
}

const translations: Record<Language, Translations> = {
  en: {
    heroTitle: 'AI-Powered',
    heroSubtitle: 'Business Intelligence',
    heroDescription: 'Transform your data into actionable insights with natural language queries. Ask questions, get beautiful visualizations instantly.',
    ctaButton: 'Generate Insights',
    featureAITitle: 'Natural Language AI',
    featureAIDesc: 'Ask questions in plain English and get instant answers with intelligent data analysis.',
    featureChartsTitle: 'Dynamic Charts',
    featureChartsDesc: 'Beautiful, interactive Plotly visualizations generated automatically from your queries.',
    featureInsightsTitle: 'Smart Insights',
    featureInsightsDesc: 'AI-powered suggestions help you discover hidden patterns in your data.',
    featureRealtimeTitle: 'Real-time Analysis',
    featureRealtimeDesc: 'Get instant responses and visualizations as you explore your data.',
    dashboardTitle: 'Insights Dashboard',
    chatPlaceholder: 'Ask a question about your data...',
    sendButton: 'Send',
    generating: 'Generating chart...',
    noCharts: 'No charts yet',
    noChartsDesc: 'Start by asking a question in the chat panel to generate your first visualization.',
    suggestionsTitle: 'Suggested queries',
    chartTypeTitle: 'Choose chart type',
    chartTypeHelper: 'Select a chart type to visualize your data',
    viewData: 'View Data',
    exportPng: 'Export PNG',
    removeChart: 'Remove',
    dataTable: 'Data Table',
    close: 'Close',
    chatTitle: 'AI Assistant',
    minimizeChat: 'Minimize',
    expandChat: 'Expand Chat',
    welcomeMessage: 'Hello! I\'m your AI data assistant. Ask me anything about your data and I\'ll create visualizations for you.',
    errorMessage: 'Sorry, something went wrong. Please try again.',
    noDataMessage: 'No data available for this query. Try a different question.',
    backToHome: 'Back to Home',
    // Chart types
    chartTypeBar: 'Bar Chart',
    chartTypeLine: 'Line Chart',
    chartTypePie: 'Pie Chart',
    chartTypeDonut: 'Donut Chart',
    chartTypeScatter: 'Scatter Plot',
    chartTypeHistogram: 'Histogram',
    chartType3D: '3D Chart',
    // Suggested questions
    moreSuggestions: 'More',
    suggestionTotalRevenueByRegion: 'Total revenue by region',
    suggestionTop10AccountsByRevenue: 'Top 10 accounts by revenue',
    suggestionRevenueByIndustry: 'Revenue by industry',
    suggestionAccountsCreatedByMonth: 'Accounts created by month',
    suggestionAverageRevenuePerAccount: 'Average revenue per account',
    suggestionAccountDistributionByRegion: 'Account distribution by region',
    suggestionHighestRevenueAccounts: 'Highest revenue accounts',
    suggestionAccountsByIndustryType: 'Accounts by industry type',
    suggestionContactsByRole: 'Contacts by role',
    suggestionContactsCreatedOverTime: 'Contacts created over time',
    suggestionContactsPerAccount: 'Contacts per account',
    suggestionTopRolesDistribution: 'Top roles distribution',
    suggestionLeadsByStatus: 'Leads by status',
    suggestionLeadsBySource: 'Leads by source',
    suggestionLeadBudgetDistribution: 'Lead budget distribution',
    suggestionLeadsCreatedByMonth: 'Leads created by month',
    suggestionConversionRateBySource: 'Conversion rate by source',
    suggestionAverageLeadBudget: 'Average lead budget',
    suggestionOpportunitiesByStage: 'Opportunities by stage',
    suggestionTotalOpportunityValue: 'Total opportunity value',
    suggestionOpportunitiesByStageAndValue: 'Opportunities by stage and value',
    suggestionExpectedCloseDates: 'Expected close dates',
    suggestionWonOpportunitiesValue: 'Won opportunities value',
    suggestionPipelineByStage: 'Pipeline by stage',
    suggestionRevenueDistributionLast30Days: 'Revenue distribution (last 30 days)',
    suggestionMonthlyRevenueTrends: 'Monthly revenue trends',
    suggestionQuarterlyPerformance: 'Quarterly performance',
    suggestionYearOverYearGrowth: 'Year-over-year growth',
    suggestionTotalPipelineValue: 'Total pipeline value',
    suggestionConversionFunnelAnalysis: 'Conversion funnel analysis',
    suggestionRevenueVsOpportunities: 'Revenue vs opportunities',
    // Dashboard utility buttons
    refreshCharts: 'Refresh Charts',
    downloadDashboard: 'Download Dashboard',
  },
  ar: {
    heroTitle: 'ذكاء اصطناعي',
    heroSubtitle: 'لتحليل الأعمال',
    heroDescription: 'حوّل بياناتك إلى رؤى قابلة للتنفيذ باستخدام استعلامات اللغة الطبيعية. اطرح أسئلة واحصل على تصورات بصرية جميلة فوراً.',
    ctaButton: 'ابدأ التحليل',
    featureAITitle: 'ذكاء اصطناعي طبيعي',
    featureAIDesc: 'اطرح أسئلتك بلغتك الطبيعية واحصل على إجابات فورية مع تحليل ذكي للبيانات.',
    featureChartsTitle: 'رسوم بيانية ديناميكية',
    featureChartsDesc: 'تصورات بصرية تفاعلية وجميلة تُنشأ تلقائياً من استفساراتك.',
    featureInsightsTitle: 'رؤى ذكية',
    featureInsightsDesc: 'اقتراحات مدعومة بالذكاء الاصطناعي تساعدك على اكتشاف الأنماط المخفية في بياناتك.',
    featureRealtimeTitle: 'تحليل فوري',
    featureRealtimeDesc: 'احصل على ردود وتصورات فورية أثناء استكشاف بياناتك.',
    dashboardTitle: 'لوحة الرؤى',
    chatPlaceholder: 'اطرح سؤالاً عن بياناتك...',
    sendButton: 'إرسال',
    generating: 'جارٍ إنشاء الرسم البياني...',
    noCharts: 'لا توجد رسوم بيانية بعد',
    noChartsDesc: 'ابدأ بطرح سؤال في لوحة المحادثة لإنشاء أول تصور بصري لك.',
    suggestionsTitle: 'استعلامات مقترحة',
    chartTypeTitle: 'اختر نوع الرسم البياني',
    chartTypeHelper: 'حدد نوع الرسم البياني لتصور بياناتك',
    viewData: 'عرض البيانات',
    exportPng: 'تصدير PNG',
    removeChart: 'إزالة',
    dataTable: 'جدول البيانات',
    close: 'إغلاق',
    chatTitle: 'المساعد الذكي',
    minimizeChat: 'تصغير',
    expandChat: 'توسيع المحادثة',
    welcomeMessage: 'مرحباً! أنا مساعدك الذكي للبيانات. اسألني أي شيء عن بياناتك وسأنشئ تصورات بصرية لك.',
    errorMessage: 'عذراً، حدث خطأ ما. يرجى المحاولة مرة أخرى.',
    noDataMessage: 'لا تتوفر بيانات لهذا الاستعلام. جرب سؤالاً مختلفاً.',
    backToHome: 'العودة للرئيسية',
    // Chart types
    chartTypeBar: 'رسم بياني عمودي',
    chartTypeLine: 'رسم بياني خطي',
    chartTypePie: 'رسم بياني دائري',
    chartTypeDonut: 'رسم بياني دائري مجوف',
    chartTypeScatter: 'مخطط مبعثر',
    chartTypeHistogram: 'رسم بياني تكراري',
    chartType3D: 'رسم بياني ثلاثي الأبعاد',
    // Suggested questions
    moreSuggestions: 'المزيد',
    suggestionTotalRevenueByRegion: 'إجمالي الإيرادات حسب المنطقة',
    suggestionTop10AccountsByRevenue: 'أفضل 10 حسابات حسب الإيرادات',
    suggestionRevenueByIndustry: 'الإيرادات حسب الصناعة',
    suggestionAccountsCreatedByMonth: 'الحسابات المنشأة حسب الشهر',
    suggestionAverageRevenuePerAccount: 'متوسط الإيرادات لكل حساب',
    suggestionAccountDistributionByRegion: 'توزيع الحسابات حسب المنطقة',
    suggestionHighestRevenueAccounts: 'الحسابات ذات أعلى إيرادات',
    suggestionAccountsByIndustryType: 'الحسابات حسب نوع الصناعة',
    suggestionContactsByRole: 'جهات الاتصال حسب الدور',
    suggestionContactsCreatedOverTime: 'جهات الاتصال المنشأة بمرور الوقت',
    suggestionContactsPerAccount: 'جهات الاتصال لكل حساب',
    suggestionTopRolesDistribution: 'توزيع الأدوار الرئيسية',
    suggestionLeadsByStatus: 'العملاء المحتملين حسب الحالة',
    suggestionLeadsBySource: 'العملاء المحتملين حسب المصدر',
    suggestionLeadBudgetDistribution: 'توزيع ميزانية العملاء المحتملين',
    suggestionLeadsCreatedByMonth: 'العملاء المحتملين المنشأون حسب الشهر',
    suggestionConversionRateBySource: 'معدل التحويل حسب المصدر',
    suggestionAverageLeadBudget: 'متوسط ميزانية العميل المحتمل',
    suggestionOpportunitiesByStage: 'الفرص حسب المرحلة',
    suggestionTotalOpportunityValue: 'إجمالي قيمة الفرص',
    suggestionOpportunitiesByStageAndValue: 'الفرص حسب المرحلة والقيمة',
    suggestionExpectedCloseDates: 'تواريخ الإغلاق المتوقعة',
    suggestionWonOpportunitiesValue: 'قيمة الفرص المكتسبة',
    suggestionPipelineByStage: 'خط الأنابيب حسب المرحلة',
    suggestionRevenueDistributionLast30Days: 'توزيع الإيرادات (آخر 30 يوماً)',
    suggestionMonthlyRevenueTrends: 'اتجاهات الإيرادات الشهرية',
    suggestionQuarterlyPerformance: 'الأداء الربعي',
    suggestionYearOverYearGrowth: 'النمو السنوي',
    suggestionTotalPipelineValue: 'إجمالي قيمة خط الأنابيب',
    suggestionConversionFunnelAnalysis: 'تحليل قمع التحويل',
    suggestionRevenueVsOpportunities: 'الإيرادات مقابل الفرص',
    // Dashboard utility buttons
    refreshCharts: 'تحديث الرسوم البيانية',
    downloadDashboard: 'تحميل لوحة المعلومات',
  },
};

interface LanguageContextType {
  language: Language;
  direction: Direction;
  t: Translations;
  toggleLanguage: () => void;
  setLanguage: (lang: Language) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('language') as Language;
      if (stored) return stored;
    }
    return 'en';
  });

  const direction: Direction = language === 'ar' ? 'rtl' : 'ltr';

  useEffect(() => {
    const root = window.document.documentElement;
    root.setAttribute('dir', direction);
    root.setAttribute('lang', language);
    localStorage.setItem('language', language);
  }, [language, direction]);

  const toggleLanguage = () => {
    setLanguageState(prev => prev === 'en' ? 'ar' : 'en');
  };

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
  };

  return (
    <LanguageContext.Provider value={{ 
      language, 
      direction, 
      t: translations[language], 
      toggleLanguage, 
      setLanguage 
    }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
