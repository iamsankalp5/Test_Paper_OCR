import { z } from "zod";

export const studentUploadSchema = z.object({
  student_name: z
    .string()
    .trim()
    .min(1, "Student name is required")
    .max(100, "Name too long"),
  student_id: z
    .string()
    .trim()
    .min(1, "Student ID is required")
    .max(50, "ID too long"),
  reference_id: z.string().trim().max(50, "Reference ID too long").optional(),
  exam_name: z
    .string()
    .trim()
    .min(1, "Exam name is required")
    .max(100, "Exam name too long"),
  subject: z
    .string()
    .trim()
    .min(1, "Subject is required")
    .max(100, "Subject name too long"),
  total_marks: z
    .string()
    .refine((val) => !isNaN(Number(val)) && Number(val) > 0, {
      message: "Total marks must be a positive number",
    }),
});

// Updated: No longer need teacher_name and teacher_id from form
// These will come from the authenticated user
export const referenceUploadSchema = z.object({
  exam_name: z
    .string()
    .trim()
    .min(1, "Exam name is required")
    .max(100, "Exam name too long"),
  subject: z
    .string()
    .trim()
    .min(1, "Subject is required")
    .max(100, "Subject name too long"),
  total_marks: z
    .string()
    .refine((val) => !isNaN(Number(val)) && Number(val) > 0, {
      message: "Total marks must be a positive number",
    }),
});

export const reviewUpdateSchema = z.object({
  job_id: z.string().trim().min(1, "Job ID is required"),
  question_number: z
    .number()
    .int()
    .positive("Question number must be positive"),
  marks_obtained: z.number().min(0, "Marks cannot be negative"),
  explanation: z.string().trim().max(500, "Explanation too long").optional(),
});

export type StudentUploadInput = z.infer<typeof studentUploadSchema>;
export type ReferenceUploadInput = z.infer<typeof referenceUploadSchema>;
export type ReviewUpdateInput = z.infer<typeof reviewUpdateSchema>;
