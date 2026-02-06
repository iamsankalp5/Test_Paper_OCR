import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const isLoggedIn = () => !!localStorage.getItem("access_token");

const getUserRole = () => {
  const userStr = localStorage.getItem("current_user");
  if (!userStr) return null;
  try {
    const user = JSON.parse(userStr);
    return user.role;
  } catch {
    return null;
  }
};

const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const role = getUserRole();

  // Teacher links
  const teacherLinks = [
    { path: "/", label: "Home" },
    { path: "/teacher", label: "Dashboard" },
    { path: "/reference", label: "Upload Reference" },
    { path: "/about", label: "About" },
  ];

  // Student links
  const studentLinks = [
    { path: "/", label: "Home" },
    { path: "/upload", label: "Upload" },
    { path: "/files", label: "Files" },
    { path: "/history", label: "Results" },
    { path: "/reference", label: "References" },
    { path: "/about", label: "About" },
  ];

  // Guest links
  const guestLinks = [
    { path: "/", label: "Home" },
    { path: "/login", label: "Login" },
    { path: "/register", label: "Register" },
  ];

  // Determine which links to show
  const links = !isLoggedIn()
    ? guestLinks
    : role === "teacher"
    ? teacherLinks
    : studentLinks;

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("current_user");
    navigate("/");
    window.location.reload();
  };
 
  return (
    <nav className="glass-card fixed top-0 left-0 right-0 z-50 border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2">
            <Sparkles className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold gradient-text">
              SmartExam OCR
            </span>
          </Link>
          <div className="hidden md:flex items-center space-x-6">
            {links.map((link) => (
              <Link key={link.path} to={link.path} className="relative">
                <motion.span
                  className={`text-sm font-medium transition-colors ${
                    location.pathname === link.path
                      ? "text-primary"
                      : "text-foreground/70 hover:text-foreground"
                  }`}
                  whileHover={{ scale: 1.05 }}
                >
                  {link.label}
                </motion.span>
                {location.pathname === link.path && (
                  <motion.div
                    layoutId="navbar-indicator"
                    className="absolute -bottom-1 left-0 right-0 h-0.5 bg-primary"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </Link>
            ))}
            {isLoggedIn() && (
              <button
                onClick={handleLogout}
                className="ml-2 px-3 py-1 rounded text-sm font-medium bg-primary/10 text-primary hover:bg-primary/20 transition"
              >
                Logout
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
 
export default Navbar;