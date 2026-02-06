import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { registerUser } from "@/lib/api";

const Register = () => {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm: "",
    role: "student",
    institution: "",
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirm) {
      toast({
        title: "Passwords do not match",
        variant: "destructive",
      });
      return;
    }
    setLoading(true);
    try {
      await registerUser({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        role: form.role,
        institution: form.institution,
      });
      toast({
        title: "Registration successful! Please log in.",
      });
      navigate("/login");
    } catch (err: any) {
      toast({
        title: "Registration failed",
        description:
          err?.response?.data?.detail ?? err.message ?? "Unknown error",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background overflow-y-auto">
      <div className="flex justify-center">
        <Card className="w-full max-w-md p-8 glass-card shadow-xl my-8">
          <h2 className="text-3xl font-bold mb-2 text-center">
            Create an Account
          </h2>
          <p className="text-muted-foreground mb-6 text-center">
            Register as a student or teacher to get started.
          </p>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                name="full_name"
                value={form.full_name}
                onChange={handleChange}
                required
                autoComplete="name"
              />
            </div>
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
              <Label htmlFor="institution">Institution</Label>
              <Input
                id="institution"
                name="institution"
                value={form.institution}
                onChange={handleChange}
                required
              />
            </div>
            <div>
              <Label htmlFor="role">Role</Label>
              <select
                id="role"
                name="role"
                className="w-full px-3 py-2 rounded-md border bg-[#1e1d2d] text-white focus:outline-none focus:ring-2 focus:ring-primary"
                value={form.role}
                onChange={handleChange}
              >
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
              </select>
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
                minLength={6}
              />
            </div>
            <div>
              <Label htmlFor="confirm">Confirm Password</Label>
              <Input
                id="confirm"
                name="confirm"
                type="password"
                value={form.confirm}
                onChange={handleChange}
                required
                minLength={6}
              />
            </div>
            <Button
              className="w-full gradient-primary py-5"
              type="submit"
              disabled={loading}
            >
              {loading ? "Registering..." : "Register"}
            </Button>
          </form>
          <div className="pt-4 text-center text-muted-foreground">
            Already have an account?{" "}
            <a href="/login" className="underline text-primary">
              Log in
            </a>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Register;
