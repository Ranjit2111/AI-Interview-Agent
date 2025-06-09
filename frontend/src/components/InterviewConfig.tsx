import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { InterviewStartRequest, api } from '@/services/api';
import { UploadCloud, BriefcaseBusiness, Building2, FileText, Settings, Clock, MessageSquare, Loader2 } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";

interface InterviewConfigProps {
  onSubmit: (config: InterviewStartRequest) => void;
  isLoading: boolean;
}

const InterviewConfig: React.FC<InterviewConfigProps> = ({ onSubmit, isLoading }) => {
  const [jobRole, setJobRole] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [resumeContent, setResumeContent] = useState('');
  const [style, setStyle] = useState<'formal' | 'casual' | 'aggressive' | 'technical'>('formal');
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [interviewDuration, setInterviewDuration] = useState(10);
  const [company, setCompany] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const { toast } = useToast();

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validTypes = [
      'text/plain',
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    if (!validTypes.includes(file.type)) {
      toast({
        title: "Unsupported File Type",
        description: "Please upload a .txt, .pdf, or .docx file.",
        variant: "destructive",
      });
      return;
    }

    if (file.type === 'text/plain') {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setResumeContent(event.target.result as string);
          toast({ title: "Success", description: "TXT file content loaded into textarea." });
        }
      };
      reader.readAsText(file);
    } else {
      setIsUploading(true);
      try {
        const response = await api.uploadResumeFile(file);
        if (response.resume_text) {
          setResumeContent(response.resume_text);
          toast({
            title: "Resume Processed",
            description: `${response.filename} content extracted and loaded. Message: ${response.message}`,
          });
        } else {
          toast({
            title: "Processing Issue",
            description: response.message || "Could not extract text from file.",
            variant: "destructive",
          });
        }
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : "Failed to upload and process resume.";
        toast({
          title: "Upload Error",
          description: errorMsg,
          variant: "destructive",
        });
        console.error("Resume upload error:", error);
      } finally {
        setIsUploading(false);
      }
    }
    e.target.value = ' ';
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!jobRole.trim()) {
      toast({ title: "Missing Field", description: "Job Role is required.", variant: "destructive" });
      return;
    }
    
    if (interviewDuration < 5 || interviewDuration > 30) {
      toast({ title: "Invalid Duration", description: "Interview duration must be between 5 and 30 minutes.", variant: "destructive" });
      return;
    }
    
    const config: InterviewStartRequest = {
      job_role: jobRole,
      job_description: jobDescription || undefined,
      resume_content: resumeContent || undefined,
      style,
      difficulty,
      company_name: company || undefined,
      interview_duration_minutes: interviewDuration,
      use_time_based_interview: true,
    };
    
    onSubmit(config);
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card className="neo-effect border border-white/10 shadow-lg backdrop-blur-lg bg-black/50 max-w-4xl xl:max-w-5xl 2xl:max-w-6xl mx-auto overflow-hidden transition-all duration-300 hover:shadow-[0_0_30px_rgba(56,178,172,0.15)]">
        <CardHeader className="bg-gradient-to-r from-black/60 via-gray-900/60 to-black/60 border-b border-white/10 text-white p-4 sm:p-6">
          <CardTitle className="text-xl sm:text-2xl bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent">Configure Your Interview</CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-6 pt-6 bg-black/70 p-4 sm:p-6">
          {/* Job Role and Company */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2 group">
              <Label htmlFor="job-role" className="flex items-center gap-2 text-gray-300 group-focus-within:text-white">
                <BriefcaseBusiness className="h-4 w-4 text-cyan-500" />
                Job Role <span className="text-red-500">*</span>
              </Label>
              <Input
                id="job-role"
                placeholder="e.g., Software Engineer"
                value={jobRole}
                onChange={(e) => setJobRole(e.target.value)}
                required
                className="glass-effect border-white/10 bg-black/50 focus:border-cyan-500/50 focus:shadow-[0_0_10px_rgba(56,189,248,0.3)] transition-all duration-300"
              />
            </div>
            
            <div className="space-y-2 group">
              <Label htmlFor="company" className="flex items-center gap-2 text-gray-300 group-focus-within:text-white">
                <Building2 className="h-4 w-4 text-purple-500" />
                Company Name (Optional)
              </Label>
              <Input
                id="company"
                placeholder="e.g., Acme Corp"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="glass-effect border-white/10 bg-black/50 focus:border-purple-500/50 focus:shadow-[0_0_10px_rgba(168,85,247,0.3)] transition-all duration-300"
              />
            </div>
          </div>

          {/* Job Description */}
          <div className="space-y-2 group">
            <Label htmlFor="job-description" className="flex items-center gap-2 text-gray-300 group-focus-within:text-white">
              <FileText className="h-4 w-4 text-cyan-500" />
              Job Description (Optional)
            </Label>
            <Textarea
              id="job-description"
              placeholder="Paste the job description here..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={4}
              className="glass-effect border-white/10 bg-black/50 focus:border-cyan-500/50 focus:shadow-[0_0_10px_rgba(56,189,248,0.3)] transition-all duration-300"
            />
          </div>

          {/* Resume Content */}
          <div className="space-y-2 group">
            <Label htmlFor="resume" className="flex items-center gap-2 text-gray-300 group-focus-within:text-white">
              <UploadCloud className="h-4 w-4 text-purple-500" />
              Resume Content (Optional)
            </Label>
            <div className="flex flex-col gap-2">
              <Textarea
                id="resume"
                placeholder="Paste your resume content here or upload a file below..."
                value={resumeContent}
                onChange={(e) => setResumeContent(e.target.value)}
                rows={6}
                className="glass-effect border-white/10 bg-black/50 focus:border-purple-500/50 focus:shadow-[0_0_10px_rgba(168,85,247,0.3)] transition-all duration-300"
              />
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                 {isUploading ? (
                  <div className="flex items-center text-sm text-purple-400">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing resume...
                  </div>
                ) : (
                  <span className="text-sm text-gray-400">Or upload a file (TXT, PDF, DOCX):</span>
                )}
                <Input
                  type="file"
                  id="resume-upload-input"
                  accept=".txt,.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                  className="w-full sm:max-w-xs glass-effect border-white/10 bg-black/50 text-gray-300 focus:border-purple-500/50 focus:shadow-[0_0_10px_rgba(168,85,247,0.3)] transition-all duration-300 file:mr-2 file:py-1 file:px-2 file:rounded-sm file:border-0 file:text-xs file:bg-purple-600/30 file:text-purple-300 hover:file:bg-purple-600/50"
                />
              </div>
            </div>
          </div>

          {/* Interview Settings */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            <div className="space-y-2 group">
              <Label htmlFor="style" className="flex items-center gap-2 text-gray-300 group-focus-within:text-white">
                <MessageSquare className="h-4 w-4 text-pink-500" />
                Interview Style
              </Label>
              <Select
                value={style}
                onValueChange={(value: 'formal' | 'casual' | 'aggressive' | 'technical') => setStyle(value)}
              >
                <SelectTrigger className="glass-effect border-white/10 bg-black/50 focus:border-pink-500/50 focus:shadow-[0_0_10px_rgba(236,72,153,0.3)] transition-all duration-300">
                  <SelectValue placeholder="Select style" />
                </SelectTrigger>
                <SelectContent className="bg-black/90 border-white/10 backdrop-blur-lg">
                  <SelectItem value="formal">Formal</SelectItem>
                  <SelectItem value="casual">Casual</SelectItem>
                  <SelectItem value="aggressive">Aggressive</SelectItem>
                  <SelectItem value="technical">Technical</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2 group">
              <Label htmlFor="difficulty" className="flex items-center gap-2 text-gray-300 group-focus-within:text-white">
                <Settings className="h-4 w-4 text-cyan-500" />
                Difficulty
              </Label>
              <Select 
                value={difficulty}
                onValueChange={(value: 'easy' | 'medium' | 'hard') => setDifficulty(value)}
              >
                <SelectTrigger className="glass-effect border-white/10 bg-black/50 focus:border-cyan-500/50 focus:shadow-[0_0_10px_rgba(56,189,248,0.3)] transition-all duration-300">
                  <SelectValue placeholder="Select difficulty" />
                </SelectTrigger>
                <SelectContent className="bg-black/90 border-white/10 backdrop-blur-lg">
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2 group">
              <Label htmlFor="duration" className="flex items-center gap-2 text-gray-300 group-focus-within:text-white">
                <Clock className="h-4 w-4 text-purple-500" />
                Interview Duration (5-30 minutes)
              </Label>
              <Input
                id="duration"
                type="number"
                min={5}
                max={30}
                value={interviewDuration}
                onChange={(e) => setInterviewDuration(parseInt(e.target.value) || 10)}
                className="glass-effect border-white/10 bg-black/50 focus:border-purple-500/50 focus:shadow-[0_0_10px_rgba(168,85,247,0.3)] transition-all duration-300"
                placeholder="10"
              />
              <p className="text-xs text-gray-500">
                How long would you like the interview to last? Default is 10 minutes.
              </p>
            </div>
          </div>
        </CardContent>
        
        <CardFooter className="flex flex-col sm:flex-row justify-end bg-gradient-to-r from-black/80 via-gray-900/80 to-black/80 border-t border-white/10 p-4 sm:p-6">
          <Button 
            type="submit"
            disabled={isLoading || !jobRole.trim()}
            className="w-full sm:w-auto bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 shadow-lg hover:shadow-purple-500/20 transition-all duration-300 text-white font-medium halo-glow min-h-[48px]"
          >
            {isLoading ? 'Starting Interview...' : 'Start Interview'}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
};

export default InterviewConfig;
