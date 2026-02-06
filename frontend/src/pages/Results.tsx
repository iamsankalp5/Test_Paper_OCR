import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useParams, useSearchParams } from "react-router-dom";
import { Download, Edit, Save, X, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import {
  getJobStatus,
  downloadReport,
  updateReview,
  reassessAnswers,
  generateReport,
  generateFeedback,
} from "@/lib/api";

interface FeedbackData {
  feedback: string;
  strengths: string[];
  improvements: string[];
  recommendations: string[];
}

interface ResultData {
  student_name: string;
  exam_name: string;
  subject: string;
  total_marks: number;
  marks_obtained: number;
  grade?: string;
  percentage: number;
  state?: string; // Job state from backend
  insights?: FeedbackData;
  feedback?: any;
  answers: Array<{
    question_number: number;
    question_text?: string;
    answer_text: string | string[];
    max_marks: number;
    marks_obtained: number;
    is_correct?: boolean;
    explanation?: string;
    suggestions?: string[];
    question_type?: string;
  }>;
}

const getInsights = (data: any): FeedbackData => {
  if (data?.insights)
    return {
      feedback: data.insights.feedback || data.feedback?.overall_feedback || "",
      strengths: data.insights.strengths || data.feedback?.strengths || [],
      improvements:
        data.insights.improvements ||
        data.insights.areas_for_improvement ||
        data.feedback?.areas_for_improvement ||
        [],
      recommendations:
        data.insights.recommendations || data.feedback?.recommendations || [],
    };
  if (data?.feedback && typeof data.feedback === "object") {
    return {
      feedback: data.feedback.overall_feedback || "",
      strengths: data.feedback.strengths || [],
      improvements: data.feedback.areas_for_improvement || [],
      recommendations: data.feedback.recommendations || [],
    };
  }
  return { feedback: "", strengths: [], improvements: [], recommendations: [] };
};

const Results = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const [searchParams] = useSearchParams();
  const referenceId = searchParams.get("ref_id");
  const [data, setData] = useState<ResultData | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingQuestion, setEditingQuestion] = useState<number | null>(null);
  const [editMarks, setEditMarks] = useState<number>(0);
  const [isReGrading, setIsReGrading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    const fetchResults = async () => {
      if (!jobId || jobId === "undefined") {
        toast({
          title: "Error",
          description:
            "No valid Job ID provided (job_id missing or null). This may be an upload or navigation error.",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }
      try {
        const result = await getJobStatus(jobId);
        if (!result.data || Object.keys(result.data).length === 0) {
          setData(null);
        } else {
          setData(result.data);
        }
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.message ||
          error.response?.data?.detail ||
          "Failed to fetch results";
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        });
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, [jobId, toast]);

  const handleDownload = async () => {
    if (!jobId) return;

    // Check job state before allowing download
    const validStates = ["feedback_generated", "reviewed", "completed"];
    if (data?.state && !validStates.includes(data.state)) {
      toast({
        title: "Cannot download report",
        description: `Job is in state: ${data.state}. Please wait for processing to complete.`,
        variant: "destructive",
      });
      return;
    }

    setIsDownloading(true);
    try {
      // 1. Generate the report first
      await generateReport({ job_id: jobId });

      // 2. Then download it
      const blob = await downloadReport(jobId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `report-${jobId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast({
        title: "Success",
        description: "Report downloaded successfully",
      });
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to download report";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const handleEditClick = (questionNumber: number, currentMarks: number) => {
    setEditingQuestion(questionNumber);
    setEditMarks(currentMarks);
  };

  const handleSaveEdit = async (questionNumber: number, maxMarks: number) => {
    if (!jobId) return;
    if (editMarks < 0 || editMarks > maxMarks) {
      toast({
        title: "Invalid Marks",
        description: `Marks must be between 0 and ${maxMarks}`,
        variant: "destructive",
      });
      return;
    }

    try {
      await updateReview({
        job_id: jobId,
        updates: [
          {
            question_number: questionNumber,
            marks_obtained: editMarks,
          },
        ],
      });

      if (data) {
        const updatedAnswers = data.answers.map((ans) =>
          ans.question_number === questionNumber
            ? { ...ans, marks_obtained: editMarks }
            : ans
        );
        const totalMarks = updatedAnswers.reduce(
          (sum, ans) => sum + ans.marks_obtained,
          0
        );
        const percentage = (totalMarks / data.total_marks) * 100;

        setData({
          ...data,
          answers: updatedAnswers,
          marks_obtained: totalMarks,
          percentage: percentage,
        });
      }

      setEditingQuestion(null);
      toast({ title: "Success", description: "Marks updated successfully" });
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to update marks";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleReGrade = async () => {
    if (!jobId || !data) {
      // ✅ No referenceId check
      toast({
        title: "Error",
        description: "Missing Job ID",
        variant: "destructive",
      });
      return;
    }

    setIsReGrading(true);
    try {
      const response = await reassessAnswers({
        job_id: jobId,
        reference_id: referenceId || null, // ✅ Can be null
      });

      setData({
        ...data,
        answers: response.data.assessed_answers,
        marks_obtained: response.data.total_marks_obtained,
        percentage: response.data.percentage,
      });

      toast({ title: "Success", description: "Re-assessment complete!" });
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to re-grade";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsReGrading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-24 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="h-16 w-16 border-4 border-primary border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (!jobId || jobId === "undefined" || !data) {
    return (
      <div className="min-h-screen pt-24 flex items-center justify-center">
        <p className="text-muted-foreground">
          {!jobId || jobId === "undefined"
            ? "No valid Job ID found. Please re-upload or contact support."
            : "No results found"}
        </p>
      </div>
    );
  }

  // Check if job failed
  if (data.state === "failed") {
    return (
      <div className="min-h-screen pt-24 flex items-center justify-center">
        <Card className="glass-card p-8 text-center max-w-md">
          <h2 className="text-2xl font-bold text-destructive mb-4">
            Processing Failed
          </h2>
          <p className="text-muted-foreground mb-4">
            The job processing has failed. Please retry uploading or contact
            support.
          </p>
          <Button onClick={() => (window.location.href = "/upload")}>
            Upload Again
          </Button>
        </Card>
      </div>
    );
  }

  const insights = getInsights(data);
  const canDownload =
    data.state &&
    ["feedback_generated", "reviewed", "completed"].includes(data.state);

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="container mx-auto px-4 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex justify-between items-start mb-8">
            <div>
              <h1 className="text-4xl font-bold mb-2 gradient-text">
                Exam Results
              </h1>
              <p className="text-muted-foreground">
                AI-generated evaluation and insights
              </p>
            </div>
            <div className="flex space-x-2">
              <Button
                onClick={handleReGrade}
                variant="outline"
                disabled={isReGrading}
              >
                {isReGrading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    className="h-4 w-4 mr-2"
                  >
                    <RotateCw />
                  </motion.div>
                ) : (
                  <RotateCw className="h-4 w-4 mr-2" />
                )}
                {isReGrading ? "Re-grading..." : "Re-Grade with AI"}
              </Button>
              <Button
                onClick={handleDownload}
                className="gradient-primary"
                disabled={!canDownload || isDownloading}
              >
                <Download className="h-4 w-4 mr-2" />
                {isDownloading ? "Preparing..." : "Download Report"}
              </Button>
            </div>
          </div>
          {/* Rest of your UI stays the same */}
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            {[
              { label: "Student", value: data.student_name },
              { label: "Subject", value: data.subject },
              {
                label: "Marks",
                value: `${data.marks_obtained}/${data.total_marks}`,
              },
              {
                label: "Grade",
                value: data.grade || (data.feedback?.grade ?? ""),
              },
            ].map((item, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <Card className="glass-card p-6">
                  <p className="text-sm text-muted-foreground mb-1">
                    {item.label}
                  </p>
                  <p className="text-2xl font-bold">{item.value}</p>
                </Card>
              </motion.div>
            ))}
          </div>
          {/* AI Insights and Answer Breakdown sections remain unchanged */}
          <Card className="glass-card p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">AI Insights</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-primary mb-2">
                  Overall Feedback
                </h3>
                <p className="text-muted-foreground">{insights.feedback}</p>
              </div>
              <div>
                <h3 className="font-semibold text-primary mb-2">Strengths</h3>
                <ul className="list-disc list-inside space-y-1">
                  {(insights.strengths ?? []).map((item, idx) => (
                    <li key={idx} className="text-muted-foreground">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-primary mb-2">
                  Areas for Improvement
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {(insights.improvements ?? []).map((item, idx) => (
                    <li key={idx} className="text-muted-foreground">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-primary mb-2">
                  Recommendations
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {(insights.recommendations ?? []).map((item, idx) => (
                    <li key={idx} className="text-muted-foreground">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
          <Card className="glass-card p-6">
            <h2 className="text-2xl font-bold mb-4">Answer Breakdown</h2>
            <div className="space-y-4">
              {(data.answers ?? []).map((answer, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="border border-border/50 rounded-xl p-4"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold">
                      Question {answer.question_number}
                    </h3>
                    {editingQuestion === answer.question_number ? (
                      <div className="flex items-center space-x-2">
                        <Input
                          type="number"
                          min="0"
                          max={answer.max_marks}
                          value={editMarks}
                          onChange={(e) => setEditMarks(Number(e.target.value))}
                          className="w-20"
                        />
                        <span className="text-muted-foreground">
                          / {answer.max_marks}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            handleSaveEdit(
                              answer.question_number,
                              answer.max_marks
                            )
                          }
                        >
                          <Save className="h-4 w-4 text-green-500" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setEditingQuestion(null)}
                        >
                          <X className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <span className="text-primary font-bold">
                          {answer.marks_obtained}/{answer.max_marks}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            handleEditClick(
                              answer.question_number,
                              answer.marks_obtained
                            )
                          }
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                  <p className="text-muted-foreground mb-2">
                    {Array.isArray(answer.answer_text)
                      ? answer.answer_text.join(" ")
                      : answer.answer_text}
                  </p>
                  {answer.explanation && (
                    <p className="text-sm text-muted-foreground italic">
                      {answer.explanation}
                    </p>
                  )}
                  {Array.isArray(answer.suggestions) &&
                    answer.suggestions.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-primary mb-2">
                          Suggestions
                        </h3>
                        <ul className="list-disc list-inside space-y-1">
                          {answer.suggestions.map((item, idx) => (
                            <li key={idx} className="text-muted-foreground">
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                </motion.div>
              ))}
            </div>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default Results;
