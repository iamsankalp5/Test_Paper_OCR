import { useState } from "react";
import { motion } from "framer-motion";
import { RefreshCw, FileText, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { reassessAnswers, generateReport, generateFeedback } from "@/lib/api";

const Actions = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [jobId, setJobId] = useState("");
  const { toast } = useToast();

  const actions = [
    {
      id: "reevaluate",
      icon: RefreshCw,
      title: "Re-evaluate Answers",
      description: "Run AI analysis again to verify grades and scoring accuracy",
      color: "from-blue-500 to-cyan-500",
    },
    {
      id: "generate",
      icon: FileText,
      title: "Generate Report Card",
      description: "Create a comprehensive PDF report with detailed analytics",
      color: "from-purple-500 to-pink-500",
    },
    {
      id: "suggest",
      icon: Lightbulb,
      title: "Suggest Improvements",
      description: "Get AI-powered recommendations for student learning paths",
      color: "from-orange-500 to-red-500",
    },
  ];

  const handleAction = async (actionId: string) => {
    if (!jobId.trim()) {
      toast({
        title: "Error",
        description: "Please enter a Job ID",
        variant: "destructive",
      });
      return;
    }

    setLoading(actionId);
    
    try {
      let response;
      
      switch (actionId) {
        case "reevaluate":
          response = await reassessAnswers({ job_id: jobId });
          break;
        case "generate":
          response = await generateReport({ job_id: jobId });
          break;
        case "suggest":
          response = await generateFeedback({ job_id: jobId });
          break;
        default:
          throw new Error("Unknown action");
      }
      
      toast({
        title: "Success!",
        description: `${actions.find(a => a.id === actionId)?.title} completed successfully.`,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || error.response?.data?.detail || "Operation failed. Please try again.";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="container mx-auto px-4 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold mb-2 gradient-text">Agentic AI Actions</h1>
          <p className="text-muted-foreground mb-8">
            Execute autonomous AI operations for advanced analysis
          </p>

          <Card className="glass-card p-6 mb-12 max-w-md">
            <Label htmlFor="job_id" className="text-lg font-semibold mb-2 block">
              Enter Job ID
            </Label>
            <p className="text-sm text-muted-foreground mb-4">
              Enter the Job ID from your upload to run AI actions on it
            </p>
            <Input
              id="job_id"
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              placeholder="e.g., job_abc123xyz"
              className="bg-input/50"
            />
          </Card>

          <div className="grid md:grid-cols-3 gap-8">
            {actions.map((action, idx) => (
              <motion.div
                key={action.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                whileHover={{ y: -8 }}
              >
                <Card className="glass-card p-8 h-full flex flex-col">
                  <div className={`h-16 w-16 rounded-2xl bg-gradient-to-br ${action.color} flex items-center justify-center mb-6`}>
                    <action.icon className="h-8 w-8 text-white" />
                  </div>
                  
                  <h3 className="text-2xl font-bold mb-3">{action.title}</h3>
                  <p className="text-muted-foreground mb-6 flex-1">{action.description}</p>
                  
                  <Button
                    onClick={() => handleAction(action.id)}
                    disabled={loading === action.id}
                    className="w-full gradient-primary"
                  >
                    {loading === action.id ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        className="h-5 w-5 border-2 border-white border-t-transparent rounded-full"
                      />
                    ) : (
                      "Run Action"
                    )}
                  </Button>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Actions;
