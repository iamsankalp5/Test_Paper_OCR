import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import ChatBot from "@/components/ChatBot";
import Landing from "@/pages/Landing";
import Upload from "@/pages/Upload";
import Results from "@/pages/Results";
import Actions from "@/pages/Actions";
import Reference from "@/pages/Reference";
import About from "@/pages/About";
import NotFound from "@/pages/NotFound";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import History from "@/pages/History";
import SavedFiles from "@/pages/SavedFiles";
import TeacherDashboard from "@/pages/TeacherDashboard";

const queryClient = new QueryClient();

// Protected Route Component for Teachers
const ProtectedTeacherRoute = ({ children }: { children: React.ReactNode }) => {
  const userStr = localStorage.getItem("current_user");
  const token = localStorage.getItem("access_token");

  if (!token || !userStr) {
    return <Navigate to="/login" replace />;
  }

  try {
    const user = JSON.parse(userStr);
    if (user.role !== "teacher") {
      return <Navigate to="/" replace />;
    }
  } catch {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Protected Route Component for Students
const ProtectedStudentRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem("access_token");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Navbar />
        <ChatBot />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/about" element={<About />} />

          {/* Teacher-only routes */}
          <Route
            path="/teacher"
            element={
              <ProtectedTeacherRoute>
                <TeacherDashboard />
              </ProtectedTeacherRoute>
            }
          />

          {/* Student routes (also accessible by teachers) */}
          <Route
            path="/upload"
            element={
              <ProtectedStudentRoute>
                <Upload />
              </ProtectedStudentRoute>
            }
          />
          <Route
            path="/files"
            element={
              <ProtectedStudentRoute>
                <SavedFiles />
              </ProtectedStudentRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedStudentRoute>
                <History />
              </ProtectedStudentRoute>
            }
          />
          <Route
            path="/results/:jobId"
            element={
              <ProtectedStudentRoute>
                <Results />
              </ProtectedStudentRoute>
            }
          />
          <Route
            path="/actions"
            element={
              <ProtectedStudentRoute>
                <Actions />
              </ProtectedStudentRoute>
            }
          />
          <Route
            path="/reference"
            element={
              <ProtectedStudentRoute>
                <Reference />
              </ProtectedStudentRoute>
            }
          />

          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);
 
export default App;
 