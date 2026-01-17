import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/store/useAppStore";
import { User, Calendar, Stethoscope, X, Plus } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const PatientCaseForm = () => {
  const { setCurrentCase, currentCase } = useAppStore();
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    patientId: currentCase?.patientId || "",
    age: currentCase?.age || 0,
    gender: currentCase?.gender || "",
    symptoms: currentCase?.symptoms || "",
    medicalHistory: currentCase?.medicalHistory || "",
    currentMedications: currentCase?.currentMedications || "",
    urgency: currentCase?.urgency || "medium"
  });

  // State for multi-input fields
  const [symptomsList, setSymptomsList] = useState<string[]>(
    currentCase?.symptoms ? currentCase.symptoms.split(',').map(s => s.trim()).filter(Boolean) : []
  );
  const [medicalHistoryList, setMedicalHistoryList] = useState<string[]>(
    currentCase?.medicalHistory ? currentCase.medicalHistory.split(',').map(s => s.trim()).filter(Boolean) : []
  );
  const [medicationsList, setMedicationsList] = useState<string[]>(
    currentCase?.currentMedications ? (
      Array.isArray(currentCase.currentMedications) 
        ? currentCase.currentMedications 
        : currentCase.currentMedications.split(',').map(s => s.trim()).filter(Boolean)
    ) : []
  );

  // Temporary input states
  const [symptomInput, setSymptomInput] = useState("");
  const [medicalHistoryInput, setMedicalHistoryInput] = useState("");
  const [medicationInput, setMedicationInput] = useState("");

  // Add item handlers
  const addSymptom = () => {
    if (symptomInput.trim()) {
      setSymptomsList([...symptomsList, symptomInput.trim()]);
      setSymptomInput("");
    }
  };

  const addMedicalHistory = () => {
    if (medicalHistoryInput.trim()) {
      setMedicalHistoryList([...medicalHistoryList, medicalHistoryInput.trim()]);
      setMedicalHistoryInput("");
    }
  };

  const addMedication = () => {
    if (medicationInput.trim()) {
      setMedicationsList([...medicationsList, medicationInput.trim()]);
      setMedicationInput("");
    }
  };

  // Remove item handlers
  const removeSymptom = (index: number) => {
    setSymptomsList(symptomsList.filter((_, i) => i !== index));
  };

  const removeMedicalHistory = (index: number) => {
    setMedicalHistoryList(medicalHistoryList.filter((_, i) => i !== index));
  };

  const removeMedication = (index: number) => {
    setMedicationsList(medicationsList.filter((_, i) => i !== index));
  };

  // Handle Enter key for quick add
  const handleKeyPress = (e: React.KeyboardEvent, addFunction: () => void) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addFunction();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.patientId || symptomsList.length === 0) {
      toast({
        title: "Missing Information",
        description: "Patient ID and at least one symptom are required.",
        variant: "destructive",
      });
      return;
    }

    // Combine lists into strings/arrays for storage
    const caseData = {
      ...formData,
      symptoms: symptomsList.join(', '),
      medicalHistory: medicalHistoryList.join(', '),
      currentMedications: medicationsList, // Keep as array
      urgency: formData.urgency as 'low' | 'medium' | 'high' | 'critical'
    };

    setCurrentCase(caseData);

    toast({
      title: "Case Saved",
      description: `Patient case with ${symptomsList.length} symptom(s), ${medicationsList.length} medication(s) saved successfully.`,
    });
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const urgencyColors = {
    low: "text-green-600",
    medium: "text-yellow-600", 
    high: "text-orange-600",
    critical: "text-red-600"
  };

  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <User className="h-5 w-5 text-primary" />
          <span>Patient Case Input</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="patientId">Patient ID *</Label>
              <Input
                id="patientId"
                placeholder="P-12345"
                value={formData.patientId}
                onChange={(e) => handleInputChange('patientId', e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="age">Age</Label>
              <Input
                id="age"
                type="number"
                placeholder="45"
                value={formData.age || ''}
                onChange={(e) => handleInputChange('age', parseInt(e.target.value) || 0)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="gender">Gender</Label>
            <Select value={formData.gender} onValueChange={(value) => handleInputChange('gender', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select gender" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="female">Female</SelectItem>
                <SelectItem value="other">Other</SelectItem>
                <SelectItem value="prefer-not-to-say">Prefer not to say</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="symptoms">Symptoms * (Press Enter or click + to add)</Label>
            <div className="flex gap-2">
              <Input
                id="symptoms"
                placeholder="e.g., Chest pain, Shortness of breath"
                value={symptomInput}
                onChange={(e) => setSymptomInput(e.target.value)}
                onKeyPress={(e) => handleKeyPress(e, addSymptom)}
              />
              <Button type="button" onClick={addSymptom} size="icon" variant="outline">
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {symptomsList.map((symptom, index) => (
                <Badge key={index} variant="secondary" className="flex items-center gap-1">
                  {symptom}
                  <X 
                    className="h-3 w-3 cursor-pointer hover:text-destructive" 
                    onClick={() => removeSymptom(index)}
                  />
                </Badge>
              ))}
            </div>
            {symptomsList.length === 0 && (
              <p className="text-sm text-muted-foreground">No symptoms added yet</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="medicalHistory">Medical History (Press Enter or click + to add)</Label>
            <div className="flex gap-2">
              <Input
                id="medicalHistory"
                placeholder="e.g., Hypertension, Type 2 Diabetes"
                value={medicalHistoryInput}
                onChange={(e) => setMedicalHistoryInput(e.target.value)}
                onKeyPress={(e) => handleKeyPress(e, addMedicalHistory)}
              />
              <Button type="button" onClick={addMedicalHistory} size="icon" variant="outline">
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {medicalHistoryList.map((history, index) => (
                <Badge key={index} variant="outline" className="flex items-center gap-1">
                  {history}
                  <X 
                    className="h-3 w-3 cursor-pointer hover:text-destructive" 
                    onClick={() => removeMedicalHistory(index)}
                  />
                </Badge>
              ))}
            </div>
            {medicalHistoryList.length === 0 && (
              <p className="text-sm text-muted-foreground">No medical history added yet</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="currentMedications">Current Medications (Press Enter or click + to add)</Label>
            <div className="flex gap-2">
              <Input
                id="currentMedications"
                placeholder="e.g., Metformin 500mg, Lisinopril 10mg"
                value={medicationInput}
                onChange={(e) => setMedicationInput(e.target.value)}
                onKeyPress={(e) => handleKeyPress(e, addMedication)}
              />
              <Button type="button" onClick={addMedication} size="icon" variant="outline">
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {medicationsList.map((medication, index) => (
                <Badge key={index} variant="default" className="flex items-center gap-1 bg-blue-500">
                  {medication}
                  <X 
                    className="h-3 w-3 cursor-pointer hover:text-destructive" 
                    onClick={() => removeMedication(index)}
                  />
                </Badge>
              ))}
            </div>
            {medicationsList.length === 0 && (
              <p className="text-sm text-muted-foreground">No medications added yet</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="urgency">Case Urgency</Label>
            <Select value={formData.urgency} onValueChange={(value) => handleInputChange('urgency', value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">
                  <span className={urgencyColors.low}>Low Priority</span>
                </SelectItem>
                <SelectItem value="medium">
                  <span className={urgencyColors.medium}>Medium Priority</span>
                </SelectItem>
                <SelectItem value="high">
                  <span className={urgencyColors.high}>High Priority</span>
                </SelectItem>
                <SelectItem value="critical">
                  <span className={urgencyColors.critical}>Critical</span>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" className="w-full">
            <Stethoscope className="w-4 h-4 mr-2" />
            Save Patient Case
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default PatientCaseForm;