import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { loginUser } from "@/lib/api";
 
const Login = () => {
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
 
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await loginUser(form);

      // Store both token and user info
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("current_user", JSON.stringify(data.user));

      toast({ title: "Login successful!" });

      // Redirect based on role
      if (data.user.role === "teacher") {
        navigate("/teacher");
      } else {
        navigate("/");
      }
    } catch (err: any) {
      toast({
        title: "Login failed",
        description: err?.response?.data?.detail || err.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-full max-w-md p-8 glass-card shadow-xl">
        <h2 className="text-3xl font-bold mb-2 text-center">Welcome Back</h2>
        <p className="text-muted-foreground mb-6 text-center">
          Login to your account
        </p>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              required
              autoComplete="email"
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              required
              autoComplete="current-password"
            />
          </div>
          <Button
            className="w-full gradient-primary py-5"
            type="submit"
            disabled={loading}
          >
            {loading ? "Logging in..." : "Log in"}
          </Button>
        </form>
        <div className="pt-4 text-center text-muted-foreground">
          Don't have an account?{" "}
          <a href="/register" className="underline text-primary">
            Register
          </a>
        </div>
      </Card>
    </div>
  );
};

export default Login;
