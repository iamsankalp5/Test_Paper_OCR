import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileText,
  File,
  X,
  Calendar,
  Hash,
  User,
  BookOpen,
  Award,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { uploadReference, getReferenceList, getReferenceById } from "@/lib/api";
import { referenceUploadSchema } from "@/lib/validation";
 
interface Reference {
  reference_id: string;
  teacher_name: string;
  teacher_email: string;
  teacher_id: string;
  exam_name: string;
  subject: string;
  total_marks: number;
  created_at: string;
  is_active: boolean;
  ocr_completed: boolean;
  submission_count?: number;
}
 
const Reference = () => {
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [references, setReferences] = useState<Reference[]>([]);
  const [formData, setFormData] = useState({
    exam_name: "",
    subject: "",
    total_marks: "",
  });
  const { toast } = useToast();
 
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  }, []);
 
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".png", ".jpg", ".jpeg"],
      "application/pdf": [".pdf"],
    },
    maxFiles: 1,
  });
 
  useEffect(() => {
    fetchReferences();
  }, []);

  const fetchReferences = async () => {
    try {
      setLoading(true);
      const response = await getReferenceList();

      // Handle the nested data structure from your API
      let referencesData = [];
      if (response?.data?.references) {
        referencesData = response.data.references;
      } else if (Array.isArray(response?.data)) {
        referencesData = response.data;
      } else if (response?.data) {
        referencesData = [response.data];
      }

      setReferences(referencesData);
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to fetch references";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
      setReferences([]);
    } finally {
      setLoading(false);
    }
  };
 
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
 
    if (!file) {
      toast({
        title: "Error",
        description: "Please upload a file",
        variant: "destructive",
      });
      return;
    }
 
    // Validate form data
    const validation = referenceUploadSchema.safeParse(formData);
    if (!validation.success) {
      toast({
        title: "Validation Error",
        description: validation.error.errors[0].message,
        variant: "destructive",
      });
      return;
    }
 
    setUploading(true);
    const data = new FormData();
    data.append("file", file);
    Object.entries(formData).forEach(([key, value]) => {
      data.append(key, value);
    });
 
    try {
      await uploadReference(data);
 
      toast({
        title: "Success!",
        description: "Reference answer key uploaded successfully.",
      });
 
      setFile(null);
      setFormData({
        exam_name: "",
        subject: "",
        total_marks: "",
      });
 
      fetchReferences();
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to upload reference";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };
 
  const handleReferenceClick = async (referenceId: string) => {
    try {
      const response = await getReferenceById(referenceId);
      const details = response?.data || response;

      toast({
        title: "Reference Details",
        description: `${details.exam_name} - ${details.subject}`,
      });
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to fetch reference details";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };
 
  return (
    <div className="min-h-screen pt-24 pb-12 bg-background">
      <div className="container mx-auto px-4 max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold mb-2 gradient-text">
            Reference Answer Keys
          </h1>
          <p className="text-muted-foreground mb-12">
            Upload and manage teacher reference materials for grading
          </p>

          <div className="grid lg:grid-cols-2 gap-8 mb-12">
            {/* Upload Section */}
            <Card className="glass-card p-6">
              <h2 className="text-2xl font-bold mb-6">Upload New Reference</h2>
              <form onSubmit={handleUpload} className="space-y-4">
                <div
                  {...getRootProps()}
                  className={`rounded-xl p-8 border-2 border-dashed cursor-pointer transition-all hover:scale-[1.01] ${
                    isDragActive
                      ? "border-primary bg-primary/5"
                      : "border-border/50"
                  }`}
                >
                  <input {...getInputProps()} />
                  <div className="text-center">
                    {file ? (
                      <div className="space-y-2">
                        <File className="h-12 w-12 text-primary mx-auto" />
                        <p className="font-medium text-sm">{file.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {(file.size / 1024).toFixed(2)} KB
                        </p>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setFile(null);
                          }}
                        >
                          <X className="h-3 w-3 mr-1" />
                          Remove
                        </Button>
                      </div>
                    ) : (
                      <>
                        <Upload className="h-12 w-12 text-primary mx-auto mb-2" />
                        <p className="text-sm font-medium">
                          {isDragActive
                            ? "Drop file here"
                            : "Click or drag answer key"}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          PDF, JPG, or PNG (Max 10MB)
                        </p>
                      </>
                    )}
                  </div>
                </div>

                <div>
                  <Label htmlFor="ref-exam">Exam Name</Label>
                  <Input
                    id="ref-exam"
                    value={formData.exam_name}
                    onChange={(e) =>
                      setFormData({ ...formData, exam_name: e.target.value })
                    }
                    placeholder="e.g., Mid-Term Mathematics"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="ref-subject">Subject</Label>
                  <Input
                    id="ref-subject"
                    value={formData.subject}
                    onChange={(e) =>
                      setFormData({ ...formData, subject: e.target.value })
                    }
                    placeholder="e.g., Mathematics"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="ref-marks">Total Marks</Label>
                  <Input
                    id="ref-marks"
                    type="number"
                    value={formData.total_marks}
                    onChange={(e) =>
                      setFormData({ ...formData, total_marks: e.target.value })
                    }
                    placeholder="e.g., 100"
                    required
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full gradient-primary"
                  disabled={uploading || !file}
                >
                  {uploading ? "Uploading..." : "Upload Reference"}
                </Button>
              </form>
            </Card>

            {/* Existing References Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">Existing References</h2>
                {!loading && references.length > 0 && (
                  <span className="text-sm text-muted-foreground">
                    {references.length} reference
                    {references.length !== 1 ? "s" : ""}
                  </span>
                )}
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full"
                  />
                </div>
              ) : references.length === 0 ? (
                <Card className="glass-card p-8 text-center">
                  <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-2">
                    No references uploaded yet
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Upload your first reference answer key to get started
                  </p>
                </Card>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                  {references.map((ref, idx) => (
                    <motion.div
                      key={ref.reference_id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      whileHover={{ x: 4 }}
                    >
                      <Card
                        className="glass-card p-5 cursor-pointer hover:border-primary/50 transition-all"
                        onClick={() => handleReferenceClick(ref.reference_id)}
                      >
                        <div className="space-y-3">
                          {/* Header */}
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-3 flex-1 min-w-0">
                              <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                                <FileText className="h-5 w-5 text-primary" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <h3 className="font-bold text-base mb-1 truncate">
                                  {ref.exam_name}
                                </h3>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                  <BookOpen className="h-3 w-3" />
                                  <span>{ref.subject}</span>
                                </div>
                              </div>
                            </div>
                            <div
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                ref.is_active
                                  ? "bg-green-500/20 text-green-400"
                                  : "bg-red-500/20 text-red-400"
                              }`}
                            >
                              {ref.is_active ? "Active" : "Inactive"}
                            </div>
                          </div>

                          {/* Details Grid */}
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            <div className="flex items-start gap-2 text-muted-foreground">
                              <Hash className="h-3 w-3 mt-1 flex-shrink-0" />
                              <span className="break-all font-mono text-xs">
                                {ref.reference_id}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground">
                              <Award className="h-3 w-3" />
                              <span>{ref.total_marks} marks</span>
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground col-span-2">
                              <User className="h-3 w-3" />
                              <span className="truncate">
                                {ref.teacher_name}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground col-span-2">
                              <Calendar className="h-3 w-3" />
                              <span>
                                {new Date(ref.created_at).toLocaleDateString(
                                  "en-US",
                                  {
                                    year: "numeric",
                                    month: "short",
                                    day: "numeric",
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  }
                                )}
                              </span>
                            </div>
                          </div>

                          {/* Footer */}
                          {ref.submission_count !== undefined && (
                            <div className="pt-2 border-t border-border/50">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">
                                  Submissions:
                                </span>
                                <span className="font-semibold text-primary">
                                  {ref.submission_count}
                                </span>
                              </div>
                            </div>
                          )}

                          {/* OCR Status */}
                          <div className="flex items-center gap-2">
                            <div
                              className={`h-2 w-2 rounded-full ${
                                ref.ocr_completed
                                  ? "bg-green-400"
                                  : "bg-yellow-400"
                              }`}
                            ></div>
                            <span className="text-xs text-muted-foreground">
                              {ref.ocr_completed
                                ? "OCR Completed"
                                : "OCR Pending"}
                            </span>
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
 
export default Reference;