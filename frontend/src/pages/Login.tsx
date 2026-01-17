import { useState } from "react";
import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Activity, Github, Mail } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAppStore } from "@/store/useAppStore";
import { loginUser, signupUser, signInWithProvider } from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import EnvDebug from '@/components/EnvDebug';
import { config } from '@/config';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  const isAuthenticated = useAppStore((state) => state.isAuthenticated);
  const setAuth = useAppStore((state) => state.setAuth);
  const { toast } = useToast();

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
  // Dev-only fallback to bypass Supabase when explicitly enabled
  const useDevBypass = config.devAuth;
  if (useDevBypass) {
        const displayName = name || (email?.split?.('@')?.[0] ?? 'Dev User');
        setAuth({ id: 'dev-user-1', email: email || 'dev@local', name: displayName }, null);
        toast({ title: 'Dev auth', description: `Signed in locally as ${displayName}.` });
        navigate('/dashboard');
        return;
      }

      if (isLogin) {
        await loginUser(email, password);
        toast({
          title: "Welcome back!",
          description: "Successfully logged in.",
        });
      } else {
        await signupUser(email, password, name);
        toast({
          title: "Account created!",
          description: "Please check your email to verify your account.",
        });
      }
      
      navigate('/dashboard');
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || `Failed to ${isLogin ? 'login' : 'signup'}. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSocialLogin = async (provider: 'google' | 'github') => {
    try {
      await signInWithProvider(provider);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || `Failed to login with ${provider}.`,
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center p-4">
      {/* Dev runtime env debug panel */}
      {import.meta.env.MODE === 'development' && <EnvDebug />}
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Activity className="h-10 w-10 text-white" />
            <span className="text-3xl font-bold text-white">MedsAI</span>
          </div>
          <p className="text-blue-100">AI-Powered Medical Diagnostics</p>
        </div>

        <Card className="shadow-hover border-0">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">
              {isLogin ? "Welcome Back" : "Create Account"}
            </CardTitle>
            <CardDescription>
              {isLogin 
                ? "Sign in to access your diagnostic dashboard" 
                : "Join the future of medical diagnostics"
              }
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* Dev-only note (shown regardless; you can hide if not needed) */}
            {config.devAuth && (
              <div className="text-xs text-muted-foreground">
                Dev auth enabled: any email/password will sign you in locally.
              </div>
            )}
            {/* Social Login Buttons */}
            <div className="space-y-3">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => handleSocialLogin("google")}
              >
                <Mail className="mr-2 h-4 w-4" />
                Continue with Google
              </Button>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => handleSocialLogin("github")}
              >
                <Github className="mr-2 h-4 w-4" />
                Continue with GitHub
              </Button>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">
                  Or continue with email
                </span>
              </div>
            </div>

            {/* Email/Password Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="Dr. John Smith"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required={!isLogin}
                  />
                </div>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="doctor@hospital.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <Button
                type="submit"
                className="w-full bg-primary hover:bg-primary-hover"
                disabled={loading}
              >
                {loading ? "Please wait..." : (isLogin ? "Sign In" : "Create Account")}
              </Button>
            </form>

            {/* Toggle between login/signup */}
            <div className="text-center">
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="text-sm text-muted-foreground hover:text-foreground underline"
              >
                {isLogin 
                  ? "Don't have an account? Sign up" 
                  : "Already have an account? Sign in"
                }
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Login;
