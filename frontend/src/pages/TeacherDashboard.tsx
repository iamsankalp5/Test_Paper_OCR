import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import {
  getTeacherReferences,
  getSubmissionsForReference,
  getClassStatistics,
  downloadReport,
} from "@/lib/api";
import {
  BookOpen,
  Users,
  TrendingUp,
  FileText,
  ChevronRight,
  Download,
  ArrowLeft,
  BarChart3,
  Award,
  Clock,
} from "lucide-react";
import { motion } from "framer-motion";

interface Reference {
  reference_id: string;
  exam_name: string;
  subject: string;
  total_marks: number;
  created_at: string;
  submission_count: number;
  teacher_name: string;
}

interface Submission {
  job_id: string;
  student_name: string;
  student_id: string;
  percentage: number;
  grade: string;
  total_marks_obtained: number;
  total_marks: number;
  submitted_at: string;
  status: string;
}

interface Statistics {
  total_students: number;
  average_score: number;
  highest_score: number;
  lowest_score: number;
  pass_rate: number;
  grade_distribution: {
    A: number;
    B: number;
    C: number;
    D: number;
    F: number;
  };
}

const TeacherDashboard = () => {
  const [references, setReferences] = useState<Reference[]>([]);
  const [selectedRef, setSelectedRef] = useState<any>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"references" | "submissions" | "statistics">(
    "references"
  );
  const { toast } = useToast();

  useEffect(() => {
    loadReferences();
  }, []);

  const loadReferences = async () => {
    try {
      setLoading(true);
      const response = await getTeacherReferences();
      setReferences(response.data || []);
    } catch (err: any) {
      toast({
        title: "Failed to load references",
        description: err?.response?.data?.message || err.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadSubmissions = async (referenceId: string) => {
    try {
      setLoading(true);
      const response = await getSubmissionsForReference(referenceId);
      setSubmissions(response.data?.submissions || []);
      setSelectedRef(response.data);
      setView("submissions");
    } catch (err: any) {
      toast({
        title: "Failed to load submissions",
        description: err?.response?.data?.message || err.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async (referenceId: string) => {
    try {
      setLoading(true);
      const response = await getClassStatistics(referenceId);
      setStatistics(response.data);
      setView("statistics");
    } catch (err: any) {
      toast({
        title: "Failed to load statistics",
        description: err?.response?.data?.message || err.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async (jobId: string, studentName: string) => {
    try {
      const blob = await downloadReport(jobId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${studentName}_report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Report downloaded successfully",
      });
    } catch (err: any) {
      toast({
        title: "Failed to download report",
        description: err?.response?.data?.message || err.message,
        variant: "destructive",
      });
    }
  };

  const viewStudentReport = (jobId: string) => {
    window.open(`/results/${jobId}`, "_blank");
  };

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case "A":
        return "bg-green-500/20 text-green-400";
      case "B":
        return "bg-blue-500/20 text-blue-400";
      case "C":
        return "bg-yellow-500/20 text-yellow-400";
      case "D":
        return "bg-orange-500/20 text-orange-400";
      case "F":
        return "bg-red-500/20 text-red-400";
      default:
        return "bg-gray-500/20 text-gray-400";
    }
  };

  const getGradeTextColor = (grade: string) => {
    switch (grade) {
      case "A":
        return "text-green-400";
      case "B":
        return "text-blue-400";
      case "C":
        return "text-yellow-400";
      case "D":
        return "text-orange-400";
      case "F":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  if (loading && references.length === 0) {
    return (
      <div className="min-h-screen pt-24 px-4 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 px-4 pb-12 bg-background">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold mb-2 gradient-text">
            Teacher Dashboard
          </h1>
          <p className="text-muted-foreground">
            Manage your exams and monitor student performance
          </p>
        </motion.div>

        {/* Navigation Tabs */}
        <div className="flex gap-4 mb-6 flex-wrap">
          {view !== "references" && (
            <Button
              variant="outline"
              onClick={() => {
                setView("references");
                setSelectedRef(null);
                setStatistics(null);
              }}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Exams
            </Button>
          )}

          {view === "references" && (
            <Button
              variant="default"
              className="flex items-center gap-2 pointer-events-none"
            >
              <BookOpen className="h-4 w-4" />
              My Exams ({references.length})
            </Button>
          )}

          {selectedRef && view !== "references" && (
            <>
              <Button
                variant={view === "submissions" ? "default" : "outline"}
                onClick={() => loadSubmissions(selectedRef.reference_id)}
                className="flex items-center gap-2"
                disabled={loading}
              >
                <Users className="h-4 w-4" />
                Submissions ({submissions.length})
              </Button>
              <Button
                variant={view === "statistics" ? "default" : "outline"}
                onClick={() => loadStatistics(selectedRef.reference_id)}
                className="flex items-center gap-2"
                disabled={loading}
              >
                <TrendingUp className="h-4 w-4" />
                Statistics
              </Button>
            </>
          )}
        </div>

        {/* References View */}
        {view === "references" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {references.length === 0 ? (
              <Card className="p-8 col-span-full text-center glass-card">
                <BookOpen className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Exams Yet</h3>
                <p className="text-muted-foreground mb-6">
                  Upload your first reference answer key to get started
                </p>
                <Button onClick={() => (window.location.href = "/reference")}>
                  Upload Reference Answer Key
                </Button>
              </Card>
            ) : (
              references.map((ref, index) => (
                <motion.div
                  key={ref.reference_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="p-6 hover:shadow-lg transition-all glass-card hover:border-primary/50">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="font-bold text-lg mb-1 line-clamp-2">
                          {ref.exam_name}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          {ref.subject}
                        </p>
                      </div>
                      <div className="text-right ml-4">
                        <div className="text-3xl font-bold text-primary">
                          {ref.submission_count || 0}
                        </div>
                        <p className="text-xs text-muted-foreground whitespace-nowrap">
                          {ref.submission_count === 1
                            ? "submission"
                            : "submissions"}
                        </p>
                      </div>
                    </div>

                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground flex items-center gap-1">
                          <Award className="h-3 w-3" />
                          Total Marks:
                        </span>
                        <span className="font-medium">{ref.total_marks}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Created:
                        </span>
                        <span className="font-medium">
                          {new Date(ref.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    <Button
                      onClick={() => loadSubmissions(ref.reference_id)}
                      className="w-full gradient-primary"
                      disabled={loading}
                    >
                      View Details <ChevronRight className="h-4 w-4 ml-2" />
                    </Button>
                  </Card>
                </motion.div>
              ))
            )}
          </motion.div>
        )}

        {/* Submissions View */}
        {view === "submissions" && selectedRef && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <Card className="p-6 glass-card">
              <div className="mb-6">
                <h2 className="text-2xl font-bold mb-2">
                  {selectedRef.exam_name}
                </h2>
                <div className="flex gap-4 text-sm text-muted-foreground">
                  <span>Subject: {selectedRef.subject}</span>
                  <span>•</span>
                  <span>Total Marks: {selectedRef.total_marks}</span>
                </div>
              </div>

              {submissions.length === 0 ? (
                <div className="text-center py-12">
                  <Users className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">
                    No Submissions Yet
                  </h3>
                  <p className="text-muted-foreground">
                    Students haven't submitted any papers for this exam yet
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-muted">
                        <th className="text-left py-3 px-4 font-semibold">
                          Student
                        </th>
                        <th className="text-left py-3 px-4 font-semibold">
                          Student ID
                        </th>
                        <th className="text-center py-3 px-4 font-semibold">
                          Score
                        </th>
                        <th className="text-center py-3 px-4 font-semibold">
                          Percentage
                        </th>
                        <th className="text-center py-3 px-4 font-semibold">
                          Grade
                        </th>
                        <th className="text-center py-3 px-4 font-semibold">
                          Submitted
                        </th>
                        <th className="text-center py-3 px-4 font-semibold">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {submissions.map((sub, index) => (
                        <motion.tr
                          key={sub.job_id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="border-b border-muted/50 hover:bg-muted/30 transition-colors"
                        >
                          <td className="py-3 px-4 font-medium">
                            {sub.student_name}
                          </td>
                          <td className="py-3 px-4 text-muted-foreground">
                            {sub.student_id}
                          </td>
                          <td className="text-center py-3 px-4">
                            <span className="font-semibold">
                              {sub.total_marks_obtained}/{sub.total_marks}
                            </span>
                          </td>
                          <td className="text-center py-3 px-4">
                            <span className="text-lg font-bold">
                              {sub.percentage}%
                            </span>
                          </td>
                          <td className="text-center py-3 px-4">
                            <span
                              className={`px-3 py-1 rounded-full text-sm font-semibold ${getGradeColor(
                                sub.grade
                              )}`}
                            >
                              {sub.grade}
                            </span>
                          </td>
                          <td className="text-center py-3 px-4 text-sm text-muted-foreground">
                            {new Date(sub.submitted_at).toLocaleDateString()}
                          </td>
                          <td className="text-center py-3 px-4">
                            <div className="flex gap-2 justify-center">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => viewStudentReport(sub.job_id)}
                              >
                                <FileText className="h-4 w-4 mr-1" />
                                View
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() =>
                                  handleDownloadReport(
                                    sub.job_id,
                                    sub.student_name
                                  )
                                }
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </motion.div>
        )}

        {/* Statistics View */}
        {view === "statistics" && statistics && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <Card className="p-6 glass-card">
                <div className="flex items-center gap-3 mb-2">
                  <Users className="h-5 w-5 text-primary" />
                  <h3 className="text-sm text-muted-foreground">
                    Total Students
                  </h3>
                </div>
                <p className="text-3xl font-bold">
                  {statistics.total_students}
                </p>
              </Card>

              <Card className="p-6 glass-card">
                <div className="flex items-center gap-3 mb-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  <h3 className="text-sm text-muted-foreground">
                    Average Score
                  </h3>
                </div>
                <p className="text-3xl font-bold text-primary">
                  {statistics.average_score}%
                </p>
              </Card>

              <Card className="p-6 glass-card">
                <div className="flex items-center gap-3 mb-2">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  <h3 className="text-sm text-muted-foreground">Pass Rate</h3>
                </div>
                <p className="text-3xl font-bold text-green-400">
                  {statistics.pass_rate}%
                </p>
              </Card>

              <Card className="p-6 glass-card">
                <div className="flex items-center gap-3 mb-2">
                  <Award className="h-5 w-5 text-yellow-400" />
                  <h3 className="text-sm text-muted-foreground">Highest</h3>
                </div>
                <p className="text-3xl font-bold">
                  {statistics.highest_score}%
                </p>
              </Card>

              <Card className="p-6 glass-card">
                <div className="flex items-center gap-3 mb-2">
                  <Award className="h-5 w-5 text-red-400" />
                  <h3 className="text-sm text-muted-foreground">Lowest</h3>
                </div>
                <p className="text-3xl font-bold">{statistics.lowest_score}%</p>
              </Card>
            </div>

            <Card className="p-6 glass-card">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                <BarChart3 className="h-6 w-6" />
                Grade Distribution
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                {Object.entries(statistics.grade_distribution).map(
                  ([grade, count]) => (
                    <div key={grade} className="text-center">
                      <div
                        className={`text-5xl font-bold mb-2 ${getGradeTextColor(
                          grade
                        )}`}
                      >
                        {count}
                      </div>
                      <div
                        className={`text-sm font-semibold px-3 py-1 rounded-full inline-block ${getGradeColor(
                          grade
                        )}`}
                      >
                        Grade {grade}
                      </div>
                      <div className="text-xs text-muted-foreground mt-2">
                        {statistics.total_students > 0
                          ? `${(
                              (count / statistics.total_students) *
                              100
                            ).toFixed(1)}%`
                          : "0%"}
                      </div>
                    </div>
                  )
                )}
              </div>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default TeacherDashboard;
