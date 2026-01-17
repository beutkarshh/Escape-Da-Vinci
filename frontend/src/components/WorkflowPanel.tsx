import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Play, 
  Square, 
  RotateCcw, 
  Clock,
  CheckCircle,
  AlertCircle,
  Workflow
} from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import { analyzePatientCase } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

const WorkflowPanel = () => {
  const { 
    currentCase, 
    analysisInProgress, 
    setAnalysisInProgress, 
    updateAgentResult,
    clearResults,
    agentResults 
  } = useAppStore();
  const { toast } = useToast();

  const workflowSteps = [
    { 
      id: "symptom", 
      name: "Symptom Analysis", 
      description: "Analyzing patient symptoms" 
    },
    { 
      id: "literature", 
      name: "Literature Review", 
      description: "Searching medical literature" 
    },
    { 
      id: "case", 
      name: "Case Matching", 
      description: "Finding similar cases" 
    },
    { 
      id: "treatment", 
      name: "Treatment Suggestions", 
      description: "Generating treatment options" 
    },
    { 
      id: "summary", 
      name: "Final Summary", 
      description: "Creating comprehensive report" 
    }
  ];

  const getStepStatus = (stepId: string) => {
    const result = agentResults.find(r => r.agentName === stepId);
    return result?.status || 'pending';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-status-completed" />;
      case 'running':
        return <Clock className="h-4 w-4 text-status-running animate-spin" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-status-error" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-status-completed text-white';
      case 'running': return 'bg-status-running text-white';
      case 'error': return 'bg-status-error text-white';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const calculateProgress = () => {
    const completedSteps = agentResults.filter(r => r.status === 'completed').length;
    return (completedSteps / workflowSteps.length) * 100;
  };

  const handleStartAnalysis = async () => {
    if (!currentCase) {
      toast({
        title: "No Patient Case",
        description: "Please enter patient case information first.",
        variant: "destructive",
      });
      return;
    }

    setAnalysisInProgress(true);
    clearResults();
    
    // Update progress to show analysis starting
    const { updateStats } = useAppStore.getState();
    updateStats({ progress: 0 });

    const startTime = Date.now();

    try {
      // Show agents activating incrementally in real-time
      const activateAgents = async () => {
        for (let i = 0; i < workflowSteps.length; i++) {
          await new Promise(resolve => setTimeout(resolve, i * 300)); // 300ms between each
          updateAgentResult(workflowSteps[i].id, 'running');
          updateStats({ progress: Math.min(20, ((i + 1) / workflowSteps.length) * 20) });
        }
      };

      // Start agent activation animation
      activateAgents();

      // Simulate progress while waiting for backend
      const progressInterval = setInterval(() => {
        const { analysisInProgress, stats } = useAppStore.getState();
        if (analysisInProgress && stats.progress < 90) {
          updateStats({ progress: Math.min(90, stats.progress + 2) });
        }
      }, 1000);

      // Call backend once to run the full orchestrator
      const response = await analyzePatientCase(currentCase);

      // Stop progress simulation
      clearInterval(progressInterval);

      // Map backend keys to frontend agent ids
      const mapping: Record<string, any> = {
        symptom: response?.symptom_analysis,
        literature: response?.literature,
        case: response?.case_matcher,
        treatment: response?.treatment,
        summary: response?.summary,
      };

      // Complete agents incrementally with visual feedback
      for (let i = 0; i < workflowSteps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 400)); // 400ms between completions
        const step = workflowSteps[i];
        updateAgentResult(step.id, 'completed', mapping[step.id]);
        const progress = ((i + 1) / workflowSteps.length) * 100;
        updateStats({ progress });
      }

      // Update stats - analysis completed successfully
      const { incrementCompletedCases, incrementCasesAnalyzed } = useAppStore.getState();
      const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
      
      incrementCompletedCases();
      incrementCasesAnalyzed();
      updateStats({ 
        progress: 100,
        totalAnalysisTime: useAppStore.getState().stats.totalAnalysisTime + elapsedSeconds
      });

      toast({
        title: "Analysis Complete",
        description: "Patient case analysis has completed.",
      });

    } catch (error: any) {
      // Mark steps as error
      for (const step of workflowSteps) {
        updateAgentResult(step.id, 'error', { message: error?.message || 'Request failed' });
      }
      
      // Still increment cases analyzed (even if failed)
      const { incrementCasesAnalyzed, updateStats } = useAppStore.getState();
      incrementCasesAnalyzed();
      updateStats({ progress: 0 });
      
      toast({
        title: "Analysis Failed",
        description: error?.message || "An error occurred during analysis.",
        variant: "destructive",
      });
    } finally {
      setAnalysisInProgress(false);
    }
  };

  const handleStopAnalysis = () => {
    setAnalysisInProgress(false);
    toast({
      title: "Analysis Stopped",
      description: "The analysis process has been stopped.",
    });
  };

  const handleResetWorkflow = () => {
    clearResults();
    setAnalysisInProgress(false);
    toast({
      title: "Workflow Reset",
      description: "The workflow has been reset and is ready for a new analysis.",
    });
  };

  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Workflow className="h-5 w-5 text-primary" />
            <span>Multi-Agent Workflow</span>
          </div>
          <div className="flex space-x-2">
            {!analysisInProgress ? (
              <Button 
                onClick={handleStartAnalysis}
                disabled={!currentCase}
                className="bg-primary hover:bg-primary-hover"
              >
                <Play className="w-4 h-4 mr-2" />
                Start Analysis
              </Button>
            ) : (
              <Button 
                onClick={handleStopAnalysis}
                variant="destructive"
              >
                <Square className="w-4 h-4 mr-2" />
                Stop
              </Button>
            )}
            <Button 
              onClick={handleResetWorkflow}
              variant="outline"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">{Math.round(calculateProgress())}%</span>
          </div>
          <Progress value={calculateProgress()} className="h-2" />
        </div>

        {/* Workflow Steps */}
        <div className="space-y-3">
          {workflowSteps.map((step, index) => {
            const status = getStepStatus(step.id);
            
            return (
              <div
                key={step.id}
                className="flex items-center space-x-3 p-3 rounded-lg border bg-card"
              >
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-sm font-medium">
                  {index + 1}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-sm text-foreground">
                      {step.name}
                    </h4>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(status)}
                      <Badge className={getStatusColor(status)} variant="secondary">
                        {status}
                      </Badge>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default WorkflowPanel;