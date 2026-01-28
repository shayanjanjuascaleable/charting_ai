import { motion } from "framer-motion";
import { useNavigate, useLocation } from "react-router-dom";
import { Home, ArrowLeft } from "lucide-react";
import { useEffect } from "react";
import { useLanguage } from "@/contexts/LanguageContext";

const NotFound = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { direction } = useLanguage();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="min-h-screen hero-gradient flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card max-w-md w-full p-8 text-center"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring" }}
          className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10"
        >
          <span className="text-4xl font-bold text-primary">404</span>
        </motion.div>
        
        <h1 className="mb-3 text-2xl font-bold text-foreground">
          {direction === 'rtl' ? 'الصفحة غير موجودة' : 'Page Not Found'}
        </h1>
        <p className="mb-8 text-muted-foreground">
          {direction === 'rtl' 
            ? 'عذراً، الصفحة التي تبحث عنها غير موجودة.'
            : "Sorry, the page you're looking for doesn't exist."
          }
        </p>
        
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => navigate("/")}
          className="btn-primary w-full"
        >
          {direction === 'rtl' ? (
            <>
              <ArrowLeft className="h-4 w-4 rotate-180" />
              العودة للرئيسية
            </>
          ) : (
            <>
              <Home className="h-4 w-4" />
              Back to Home
            </>
          )}
        </motion.button>
      </motion.div>
    </div>
  );
};

export default NotFound;
