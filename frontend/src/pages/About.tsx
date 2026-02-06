import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const About = () => {
  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="container mx-auto px-4 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <Sparkles className="h-20 w-20 text-primary mx-auto mb-6 glow-primary" />
          
          <h1 className="text-5xl font-bold mb-6 gradient-text">About SmartExam OCR</h1>
          
          <div className="glass-card rounded-2xl p-8 text-left space-y-6">
            <p className="text-lg text-muted-foreground leading-relaxed">
              SmartExam OCR uses <span className="text-primary font-semibold">Agentic AI</span> to 
              automatically read, understand, and evaluate handwritten or printed test papers.
            </p>

            <div className="space-y-4">
              <h2 className="text-2xl font-bold">How It Works</h2>
              <ul className="space-y-3 text-muted-foreground">
                <li className="flex items-start">
                  <span className="text-primary mr-2">•</span>
                  <span><strong>OCR Technology:</strong> Advanced optical character recognition extracts text from scanned papers</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary mr-2">•</span>
                  <span><strong>AI Understanding:</strong> Natural language processing comprehends answers contextually</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary mr-2">•</span>
                  <span><strong>Autonomous Grading:</strong> Agentic AI evaluates answers against reference keys fairly</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary mr-2">•</span>
                  <span><strong>Intelligent Feedback:</strong> Generates personalized insights and improvement suggestions</span>
                </li>
              </ul>
            </div>

            <div className="space-y-4">
              <h2 className="text-2xl font-bold">Benefits</h2>
              <ul className="space-y-3 text-muted-foreground">
                <li className="flex items-start">
                  <span className="text-primary mr-2">✓</span>
                  <span>Save hours of manual grading time</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary mr-2">✓</span>
                  <span>Ensure consistent and fair evaluation</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary mr-2">✓</span>
                  <span>Provide actionable feedback instantly</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary mr-2">✓</span>
                  <span>Track student performance trends</span>
                </li>
              </ul>
            </div>

            <div className="pt-8 border-t border-border/50">
              <p className="text-center text-muted-foreground">
                Built for educators who want to focus more on teaching and less on paperwork.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default About;
