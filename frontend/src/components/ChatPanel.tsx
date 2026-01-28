import { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Loader2, ChevronDown, ChevronUp, MessageSquare, RotateCcw, RefreshCw } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { ChartTypeSelector, ChartType } from './ChartTypeSelector';
import { getApiUrl } from '@/config/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  suggestedFields?: string[];
  isError?: boolean;
}

interface ChatPanelProps {
  onChartGenerated: (chartData: {
    title: string;
    chartJson: any;
    rawData: any[];
    suggestions: string[];
  }) => void;
  suggestions: string[];
}

export const ChatPanel = ({ onChartGenerated, suggestions }: ChatPanelProps) => {
  const { t, language, direction } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: t.welcomeMessage }
  ]);
  const [input, setInput] = useState('');
  const [selectedChartType, setSelectedChartType] = useState<ChartType>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const requestInFlightRef = useRef<boolean>(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastPendingMessageRef = useRef<string>('');

  useEffect(() => {
    setMessages([{ id: '1', role: 'assistant', content: t.welcomeMessage }]);
  }, [t.welcomeMessage]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const messageToSend = input.trim();
    
    // Guard: Only send if message is provided AND chart type is selected AND no request in flight
    if (!messageToSend || !selectedChartType || requestInFlightRef.current) return;
    
    // Idempotency: If the new message equals the last pending message, do nothing
    if (messageToSend === lastPendingMessageRef.current && requestInFlightRef.current) return;

    // Set request guard and store pending message
    requestInFlightRef.current = true;
    lastPendingMessageRef.current = messageToSend;
    
    // Create AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageToSend,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(getApiUrl('chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageToSend,
          language: language,
          forced_chart_type: selectedChartType,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Network error occurred' }));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Log debug info if available (development mode)
      if (data._debug) {
        console.log('[DB_VERIFY] Backend database info:', data._debug);
        console.log('[DB_VERIFY] Database path:', data._debug.db_path);
        console.log('[DB_VERIFY] Tables:', data._debug.tables);
        console.log('[DB_VERIFY] Row count:', data._debug.row_count);
      }

      // Detect validation errors: check for error_type, error, or details fields
      const isValidationError = data.error_type || data.error || data.details || data.success === false;
      
      if (isValidationError) {
        // Handle validation error response
        const errorMessage = data.details || data.message || data.error || t.errorMessage;
        const suggestedFields = data.suggested_fields || [];
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: errorMessage,
          suggestedFields: Array.isArray(suggestedFields) ? suggestedFields : [],
          isError: true,
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else if (data.ok === true && data.rows && data.rows.length > 0) {
        // Handle response: manual chart selection mode (chart_json only)
        const chartData = data.chart_json
          ? {
              title: data.chart?.title || messageToSend,
              chartJson: data.chart_json,
              rawData: data.rows || data.raw_data || [],
              suggestions: data.suggestions || [],
            }
          : null;

        if (chartData) {
          onChartGenerated(chartData);

          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: data.answer || (language === 'ar' 
              ? 'تم إنشاء الرسم البياني بنجاح! يمكنك رؤيته في الشبكة على اليسار.'
              : 'Chart generated successfully! You can see it in the grid.'),
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else {
          // Fallback: no chart data available
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: data.answer || t.noDataMessage,
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
      } else if (data.chart_json) {
        // Backward compatibility: old format
        onChartGenerated({
          title: messageToSend,
          chartJson: data.chart_json,
          rawData: data.raw_data || [],
          suggestions: data.suggestions || [],
        });

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: language === 'ar' 
            ? 'تم إنشاء الرسم البياني بنجاح! يمكنك رؤيته في الشبكة على اليسار.'
            : 'Chart generated successfully! You can see it in the grid.',
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Only show "No data available" when success is true but chart_json is null/empty AND no error
        const isNoDataCase = (data.success === true || data.ok === true) && !data.chart_json && !isValidationError;
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.answer || (isNoDataCase ? t.noDataMessage : t.errorMessage),
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      // Ignore abort errors (user cancelled or new request started)
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: t.errorMessage,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      // Reset request guard and clear pending message
      requestInFlightRef.current = false;
      lastPendingMessageRef.current = '';
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Only send if both message and chart type are selected
    if (!input.trim() || !selectedChartType) return;
    sendMessage();
  };

  const handleReset = () => {
    // Reset chat UI: clear messages and restore default greeting
    setMessages([{ id: '1', role: 'assistant', content: t.welcomeMessage }]);
    setInput('');
    setSelectedChartType(null);
    // Do NOT affect charts, queries, or backend calls - UI state only
  };

  // Large pool of suggested questions using translation keys (frontend-only, no backend calls)
  const questionKeys = useMemo(() => [
    // Account-based questions
    'suggestionTotalRevenueByRegion',
    'suggestionTop10AccountsByRevenue',
    'suggestionRevenueByIndustry',
    'suggestionAccountsCreatedByMonth',
    'suggestionAverageRevenuePerAccount',
    'suggestionAccountDistributionByRegion',
    'suggestionHighestRevenueAccounts',
    'suggestionAccountsByIndustryType',
    
    // Contact-based questions
    'suggestionContactsByRole',
    'suggestionContactsCreatedOverTime',
    'suggestionContactsPerAccount',
    'suggestionTopRolesDistribution',
    
    // Lead-based questions
    'suggestionLeadsByStatus',
    'suggestionLeadsBySource',
    'suggestionLeadBudgetDistribution',
    'suggestionLeadsCreatedByMonth',
    'suggestionConversionRateBySource',
    'suggestionAverageLeadBudget',
    
    // Opportunity-based questions
    'suggestionOpportunitiesByStage',
    'suggestionTotalOpportunityValue',
    'suggestionOpportunitiesByStageAndValue',
    'suggestionExpectedCloseDates',
    'suggestionWonOpportunitiesValue',
    'suggestionPipelineByStage',
    
    // Time-based questions
    'suggestionRevenueDistributionLast30Days',
    'suggestionMonthlyRevenueTrends',
    'suggestionQuarterlyPerformance',
    'suggestionYearOverYearGrowth',
    
    // Aggregated questions
    'suggestionTotalPipelineValue',
    'suggestionConversionFunnelAnalysis',
    'suggestionRevenueVsOpportunities'
  ] as const, []);

  // Get translated questions based on current language
  const questionPool = useMemo(() => {
    return questionKeys.map(key => t[key as keyof typeof t]);
  }, [questionKeys, t]);

  // State for managing rotating suggestions
  // Use array of objects with IDs for stable keys during replacement
  const [currentSuggestions, setCurrentSuggestions] = useState<Array<{ id: number; text: string }>>([]);
  const [recentlyUsed, setRecentlyUsed] = useState<string[]>([]);
  const [nextId, setNextId] = useState(0);
  const MAX_RECENT = 10; // Track last 10 used suggestions

  // Initialize with 4 random suggestions from pool (re-initialize when language changes)
  useEffect(() => {
    const shuffled = [...questionPool].sort(() => Math.random() - 0.5);
    setCurrentSuggestions(
      shuffled.slice(0, 4).map((text, idx) => ({ id: idx, text }))
    );
    setNextId(4);
    // Reset recently used when language changes
    setRecentlyUsed([]);
  }, [questionPool, language]);

  // Get a new suggestion that's not currently visible and not recently used
  const getNewSuggestion = (excludeList: string[]): string | null => {
    const available = questionPool.filter(
      q => !excludeList.includes(q) && !recentlyUsed.includes(q)
    );
    
    if (available.length === 0) {
      // If pool is exhausted, reset recently used and try again
      const resetAvailable = questionPool.filter(q => !excludeList.includes(q));
      if (resetAvailable.length === 0) {
        // If still empty, just use any from pool
        return questionPool[Math.floor(Math.random() * questionPool.length)];
      }
      return resetAvailable[Math.floor(Math.random() * resetAvailable.length)];
    }
    
    return available[Math.floor(Math.random() * available.length)];
  };

  // Add to recently used (with max limit)
  const addToRecentlyUsed = (question: string) => {
    setRecentlyUsed(prev => {
      const updated = [question, ...prev.filter(q => q !== question)];
      return updated.slice(0, MAX_RECENT);
    });
  };

  const handleSuggestedQuestionClick = (question: string) => {
    // Fill input with suggested question, but don't auto-send
    setInput(question);
    
    // Add to recently used
    addToRecentlyUsed(question);
    
    // Replace the clicked chip with a new suggestion
    const currentTexts = currentSuggestions.map(s => s.text);
    const newSuggestion = getNewSuggestion(currentTexts);
    if (newSuggestion) {
      setCurrentSuggestions(prev => 
        prev.map(s => s.text === question ? { id: nextId, text: newSuggestion } : s)
      );
      setNextId(prev => prev + 1);
    }
  };

  // Handle "More" button - replace all 4 chips
  const handleMoreSuggestions = () => {
    const newSuggestions: string[] = [];
    for (let i = 0; i < 4; i++) {
      const suggestion = getNewSuggestion(newSuggestions);
      if (suggestion) {
        newSuggestions.push(suggestion);
      }
    }
    // If we couldn't get 4 unique ones, fill with random from pool
    while (newSuggestions.length < 4) {
      const random = questionPool[Math.floor(Math.random() * questionPool.length)];
      if (!newSuggestions.includes(random)) {
        newSuggestions.push(random);
      }
    }
    setCurrentSuggestions(
      newSuggestions.map((text, idx) => ({ id: nextId + idx, text }))
    );
    setNextId(prev => prev + 4);
  };

  return (
    <motion.div
      layout
      className={`glass-card flex flex-col ${isMinimized ? 'h-14' : 'h-full min-h-[500px] max-h-[calc(100vh-8rem)]'}`}
    >
      {/* Header - Fixed at top */}
      <div className="flex items-center justify-between border-b border-border/50 px-4 py-3 shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/20">
            <Bot className="h-4 w-4 text-accent" />
          </div>
          <span className="font-semibold text-foreground">{t.chatTitle}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleReset}
            className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-muted transition-colors"
            aria-label="Reset chat"
            title="Reset chat"
          >
            <RotateCcw className="h-4 w-4 text-muted-foreground" />
          </button>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-muted"
            aria-label={isMinimized ? t.expandChat : t.minimizeChat}
          >
            {isMinimized ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {!isMinimized && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="flex flex-1 flex-col overflow-hidden min-h-0"
          >
            {/* Messages Area - Scrollable */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0 scroll-smooth">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${message.role === 'user' ? (direction === 'rtl' ? 'flex-row-reverse' : 'flex-row') : ''}`}
                >
                  <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                    message.role === 'user' ? 'bg-primary/20' : 'bg-accent/20'
                  }`}>
                    {message.role === 'user' ? (
                      <User className="h-4 w-4 text-primary" />
                    ) : (
                      <Bot className="h-4 w-4 text-accent" />
                    )}
                  </div>
                  <div className={message.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'}>
                    <p className={`text-sm leading-relaxed ${message.isError ? 'text-destructive' : ''}`}>
                      {message.content}
                    </p>
                    {message.suggestedFields && message.suggestedFields.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {message.suggestedFields.map((field, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 text-xs font-medium bg-muted/50 text-muted-foreground rounded-md border border-border/50"
                          >
                            {field}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
              
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/20">
                    <Bot className="h-4 w-4 text-accent" />
                  </div>
                  <div className="chat-bubble-assistant flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-accent" />
                    <span className="text-sm text-muted-foreground">{t.generating}</span>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Composer Area - Fixed at bottom */}
            <div className="shrink-0 border-t border-border/50 bg-card/50">
              {/* Chart Type Selector */}
              <div className="px-4 pt-3">
                <ChartTypeSelector
                  selectedChartType={selectedChartType}
                  onSelect={setSelectedChartType}
                />
              </div>

              {/* Suggested Questions */}
              <div className="px-4 pt-3 pb-2">
                <div className="flex flex-wrap items-center gap-2">
                  <AnimatePresence mode="popLayout">
                    {currentSuggestions.map((suggestion) => (
                      <motion.button
                        key={suggestion.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        onClick={() => handleSuggestedQuestionClick(suggestion.text)}
                        className="px-3 py-1.5 text-xs font-medium text-muted-foreground bg-muted/50 hover:bg-muted hover:text-foreground rounded-full transition-colors border border-border/50"
                        type="button"
                        dir={direction}
                      >
                        {suggestion.text}
                      </motion.button>
                    ))}
                  </AnimatePresence>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleMoreSuggestions}
                    className="px-2 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
                    type="button"
                    title={t.moreSuggestions}
                    dir={direction}
                  >
                    <RefreshCw className="h-3 w-3" />
                    <span>{t.moreSuggestions}</span>
                  </motion.button>
                </div>
              </div>

              {/* Input */}
              <form onSubmit={handleSubmit} className="p-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={t.chatPlaceholder}
                    disabled={isLoading}
                    className="input-premium flex-1"
                    dir={direction}
                  />
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="submit"
                    disabled={isLoading || !input.trim() || !selectedChartType || requestInFlightRef.current}
                    className="btn-accent disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className={`h-4 w-4 ${direction === 'rtl' ? 'rotate-180' : ''}`} />
                  </motion.button>
                </div>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// Mobile floating chat button
export const MobileChatButton = ({ onClick, hasUnread }: { onClick: () => void; hasUnread?: boolean }) => {
  const { t } = useLanguage();
  
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full shadow-lg lg:hidden"
      style={{ background: 'var(--gradient-accent)' }}
      aria-label={t.expandChat}
    >
      <MessageSquare className="h-6 w-6 text-accent-foreground" />
      {hasUnread && (
        <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-destructive" />
      )}
    </motion.button>
  );
};
