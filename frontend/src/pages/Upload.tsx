import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { Upload as UploadIcon, File, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import { uploadStudentPaper } from "@/lib/api";
import { studentUploadSchema } from "@/lib/validation";

const Upload = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    student_name: "",
    student_id: "",
    reference_id: "",
    exam_name: "",
    subject: "",
    total_marks: "",
  });
  const { toast } = useToast();
  const navigate = useNavigate();

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      toast({
        title: "Error",
        description: "Please upload a file",
        variant: "destructive",
      });
      return;
    }

    const validation = studentUploadSchema.safeParse(formData);
    if (!validation.success) {
      toast({
        title: "Validation Error",
        description: validation.error.errors[0].message,
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    const data = new FormData();
    data.append("file", file);
    Object.entries(formData).forEach(([key, value]) => {
      data.append(key, value);
    });

    try {
      const response = await uploadStudentPaper(data);
      // Now response = { job_id: "...", ... }
      if (!response.job_id) {
        toast({
          title: "Error",
          description:
            "Job ID not received from backend. Please check your API.",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      toast({
        title: "Success!",
        description: "Processing complete. Redirecting to results...",
      });

      setTimeout(() => {
        const refId = formData.reference_id;
        navigate(
          `/results/${response.job_id}${refId ? `?ref_id=${refId}` : ""}`
        );
      }, 1500);
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to process file. Please try again.";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="container mx-auto px-4 max-w-3xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold mb-2 gradient-text">
            Upload Test Paper
          </h1>
          <p className="text-muted-foreground mb-8">
            Upload a scanned test paper and let AI handle the rest
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div
              {...getRootProps()}
              className={`glass-card rounded-2xl p-12 border-2 border-dashed cursor-pointer transition-all hover:scale-[1.01] ${
                isDragActive
                  ? "border-primary bg-primary/5"
                  : "border-border/50"
              }`}
            >
              <input {...getInputProps()} />
              <div className="text-center">
                {file ? (
                  <div className="space-y-4">
                    <File className="h-16 w-16 text-primary mx-auto" />
                    <div>
                      <p className="font-medium">{file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setFile(null);
                      }}
                    >
                      <X className="h-4 w-4 mr-2" />
                      Remove
                    </Button>
                  </div>
                ) : (
                  <>
                    <UploadIcon className="h-16 w-16 text-primary mx-auto mb-4" />
                    <p className="text-lg font-medium mb-2">
                      {isDragActive
                        ? "Drop your file here"
                        : "Drag & drop or click to upload"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      PDF or Image files (PNG, JPG)
                    </p>
                  </>
                )}
              </div>
            </div>

            <div className="glass-card rounded-2xl p-6 space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="student_name">Student Name</Label>
                  <Input
                    id="student_name"
                    value={formData.student_name}
                    onChange={(e) =>
                      setFormData({ ...formData, student_name: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="student_id">Student ID</Label>
                  <Input
                    id="student_id"
                    value={formData.student_id}
                    onChange={(e) =>
                      setFormData({ ...formData, student_id: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="exam_name">Exam Name</Label>
                  <Input
                    id="exam_name"
                    value={formData.exam_name}
                    onChange={(e) =>
                      setFormData({ ...formData, exam_name: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="subject">Subject</Label>
                  <Input
                    id="subject"
                    value={formData.subject}
                    onChange={(e) =>
                      setFormData({ ...formData, subject: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="total_marks">Total Marks</Label>
                  <Input
                    id="total_marks"
                    type="number"
                    value={formData.total_marks}
                    onChange={(e) =>
                      setFormData({ ...formData, total_marks: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reference_id">Reference ID</Label>
                  <Input
                    id="reference_id"
                    value={formData.reference_id}
                    onChange={(e) =>
                      setFormData({ ...formData, reference_id: e.target.value })
                    }
                    placeholder="Optional"
                  />
                </div>
              </div>
            </div>

            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                type="submit"
                className="w-full gradient-primary text-lg py-6"
                disabled={loading || !file}
              >
                {loading ? "Processing with AI..." : "Process with OCR  "}
              </Button>
            </motion.div>
          </form>
        </motion.div>
      </div>
    </div>
  );
};

export default Upload;
