import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Sparkles, Brain, FileCheck, TrendingUp } from "lucide-react";

// Utility for checking login (JWT in localStorage)
const isLoggedIn = () => !!localStorage.getItem("access_token");

const Landing = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (isLoggedIn()) {
      navigate("/upload");
    } else {
      navigate("/register");
    }
  };

  return (
    <div className="min-h-screen pt-20">
      <section className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center max-w-4xl mx-auto"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
            className="inline-block mb-6"
          >
            <Sparkles className="h-20 w-20 text-primary glow-primary" />
          </motion.div>

          <h1 className="text-6xl md:text-7xl font-bold mb-6">
            <span className="gradient-text">AI-Powered OCR</span>
            <br />
            for Smart Exam Evaluation
          </h1>

          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Extract, grade, and analyze student test papers automatically with
            Agentic AI. Save time, ensure fairness, and provide intelligent
            feedback.
          </p>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button
              onClick={handleGetStarted}
              className="gradient-primary text-lg px-8 py-6 glow-primary"
              size="lg"
            >
              Get Started
            </Button>
          </motion.div>

          {!isLoggedIn() && (
            <div className="flex justify-center gap-4 mt-8">
              {/* <Button variant="outline" onClick={() => navigate("/login")}>
                Login
              </Button>
              <Button variant="outline" onClick={() => navigate("/register")}>
                Register
              </Button> */}
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="mt-32 grid md:grid-cols-3 gap-8"
        >
          {[
            {
              icon: Brain,
              title: "Agentic AI",
              description:
                "Autonomous intelligent processing that understands context and evaluates fairly",
            },
            {
              icon: FileCheck,
              title: "Auto-Grading",
              description:
                "Instantly extract questions, answers, and calculate marks with high accuracy",
            },
            {
              icon: TrendingUp,
              title: "Smart Insights",
              description:
                "Get AI-driven feedback, improvement areas, and detailed performance analytics",
            },
          ].map((feature, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 + idx * 0.1 }}
              whileHover={{ y: -8 }}
            >
              <div className="glass-card p-8 rounded-2xl h-full">
                <feature.icon className="h-12 w-12 text-primary mb-4" />
                <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <footer className="py-8 text-center text-muted-foreground border-t border-border/50 mt-20">
        <p>© 2025 SmartExam OCR.</p>
      </footer>
    </div>
  );
};

export default Landing;
