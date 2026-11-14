import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';
import { StatCard } from '../components/common/StatCard';
import { QuestionApprovalCard } from '../components/faculty/QuestionApprovalCard';
import { CourseMaterialProcessor } from '../components/faculty/CourseMaterialProcessor';
import { QuestionGeneratorStudio } from '../components/faculty/QuestionGeneratorStudio';
import ClassMasteryMatrixHeatmap from '../components/faculty/ClassMasteryMatrixHeatmap';
import AssessmentReportView from '../components/common/AssessmentReportView';
import {
  BookOpen,
  CheckSquare,
  Users,
  Sparkles,
  AlertCircle,
  RefreshCw,
  Layers,
  UploadCloud,
  ChevronRight,
  Grid,
  BarChart2
} from 'lucide-react';

export const FacultyDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('MATERIAL'); // 'MATERIAL' | 'QUESTIONS' | 'MASTERY_MATRIX' | 'REPORTS' | 'COURSES'
  const [selectedCourseId, setSelectedCourseId] = useState('');
  const [facultyReport, setFacultyReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  const fetchDashboard = async () => {
    setIsLoading(true);
    setErrorMessage('');
    try {
      const data = await authApi.getFacultyDashboard();
      setDashboardData(data);
      if (data.assigned_courses?.length > 0 && !selectedCourseId) {
        setSelectedCourseId(data.assigned_courses[0].id);
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load faculty dashboard metrics.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchReport = async (courseId) => {
    if (!courseId) return;
    try {
      const data = await authApi.getFacultyAssessmentReport(courseId);
      setFacultyReport(data);
    } catch (err) {
      console.error('Failed to load faculty assessment report:', err);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      fetchReport(selectedCourseId);
    }
  }, [selectedCourseId]);

  const handleApproveQuestion = async (questionId, isApproved, isPublished) => {
    try {
      await authApi.approveQuestion(questionId, isApproved, isPublished);
      await fetchDashboard();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update question approval status.');
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm font-medium text-slate-600">Loading Faculty Academic Workspace...</p>
      </div>
    );
  }

  const selectedCourse = dashboardData?.assigned_courses?.find((c) => c.id === selectedCourseId) ||
    dashboardData?.assigned_courses?.[0];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Faculty Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 mb-2">
            <span className="w-2 h-2 rounded-full bg-purple-600 animate-ping" />
            Active Faculty Session (30-Min Protected Lifetime)
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Welcome, {dashboardData?.faculty_name || user?.full_name}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {dashboardData?.department || 'Department of Computer Science'} • Course Allocation & Question Approval Hub
          </p>
        </div>

        <button
          onClick={fetchDashboard}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors self-start md:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Metrics
        </button>
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2.5 text-sm text-rose-700">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Assigned Courses"
          value={dashboardData?.assigned_courses?.length || 0}
          subtitle="Active curriculum assignments"
          icon={BookOpen}
          color="purple"
        />
        <StatCard
          title="Approval Queue"
          value={dashboardData?.total_pending_approvals || 0}
          subtitle="AI questions awaiting review"
          badge={dashboardData?.total_pending_approvals > 0 ? 'Action Needed' : 'Cleared'}
          icon={CheckSquare}
          color="amber"
        />
        <StatCard
          title="Enrolled Candidates"
          value={dashboardData?.total_active_students || 0}
          subtitle="Across assigned classes"
          icon={Users}
          color="blue"
        />
        <StatCard
          title="NLP Mapping"
          value="Online"
          subtitle="Cosine similarity & gap engine"
          icon={Sparkles}
          color="emerald"
        />
      </div>

      {/* Course Selector Bar (if multiple assigned courses) */}
      {dashboardData?.assigned_courses && dashboardData.assigned_courses.length > 1 && (
        <div className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider pl-2">
            Selected Course Context:
          </span>
          <select
            value={selectedCourseId}
            onChange={(e) => setSelectedCourseId(e.target.value)}
            className="py-1.5 px-3 text-xs bg-slate-50 border border-slate-300 rounded-lg text-slate-800 font-semibold focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            {dashboardData.assigned_courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.course_code}: {c.title}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Primary Navigation Tabs */}
      <div className="flex border-b border-slate-200 text-sm font-semibold gap-2">
        <button
          onClick={() => setActiveTab('MATERIAL')}
          className={`pb-3 px-4 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'MATERIAL'
              ? 'border-purple-600 text-purple-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          Course Material & Objective Mapping
        </button>

        <button
          onClick={() => setActiveTab('QUESTIONS')}
          className={`pb-3 px-4 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'QUESTIONS'
              ? 'border-purple-600 text-purple-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <CheckSquare className="w-4 h-4" />
          Question Review & Approvals
          {dashboardData?.total_pending_approvals > 0 && (
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-amber-100 text-amber-800 font-bold">
              {dashboardData.total_pending_approvals}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('MASTERY_MATRIX')}
          className={`pb-3 px-4 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'MASTERY_MATRIX'
              ? 'border-purple-600 text-purple-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Grid className="w-4 h-4" />
          Class Mastery Matrix |O| × |T|
        </button>

        <button
          onClick={() => setActiveTab('REPORTS')}
          className={`pb-3 px-4 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'REPORTS'
              ? 'border-purple-600 text-purple-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          Cohort Gain & Reports
        </button>

        <button
          onClick={() => setActiveTab('COURSES')}
          className={`pb-3 px-4 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'COURSES'
              ? 'border-purple-600 text-purple-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" />
          Curriculum Overview
        </button>
      </div>

      {/* Tab Content 1: Course Material & Objective Mapping */}
      {activeTab === 'MATERIAL' && (
        <CourseMaterialProcessor
          courseId={selectedCourse?.id || ''}
          courseTitle={`${selectedCourse?.course_code || 'CS401'}: ${selectedCourse?.title || 'Design and Analysis of Algorithms'}`}
        />
      )}

      {/* Tab Content: Class Mastery Matrix */}
      {activeTab === 'MASTERY_MATRIX' && (
        <ClassMasteryMatrixHeatmap
          courseId={selectedCourse?.id || ''}
          courseCode={selectedCourse?.course_code || ''}
          courseTitle={selectedCourse?.title || ''}
        />
      )}

      {/* Tab Content: Cohort Gain & Assessment Reports */}
      {activeTab === 'REPORTS' && (
        <AssessmentReportView
          report={facultyReport}
          isFaculty={true}
        />
      )}

      {/* Tab Content 2: Question Review & Approvals */}
      {activeTab === 'QUESTIONS' && (
        <div className="space-y-8">
          {/* Adaptive Question Generation Studio */}
          <QuestionGeneratorStudio
            courseId={selectedCourse?.id || ''}
            courseTitle={`${selectedCourse?.course_code || 'CS401'}: ${selectedCourse?.title || 'Design and Analysis of Algorithms'}`}
            onQuestionsGenerated={fetchDashboard}
          />

          {/* Current Question Approval & Review Queue */}
          <div className="space-y-4 pt-4 border-t border-slate-200">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-purple-600" />
                Active Course Question Bank & Review Queue ({dashboardData?.recent_questions?.length || 0})
              </h2>
              <span className="text-xs text-slate-500 font-mono">
                Privileged Rubrics & Model Answers (Faculty Only)
              </span>
            </div>

            <div className="space-y-4">
              {dashboardData?.recent_questions?.length === 0 ? (
                <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-sm">
                  No questions currently generated for review. Use the studio above to allocate and generate questions.
                </div>
              ) : (
                dashboardData?.recent_questions?.map((q) => (
                  <QuestionApprovalCard
                    key={q.id}
                    question={q}
                    onApprove={handleApproveQuestion}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab Content 3: Curriculum Overview */}
      {activeTab === 'COURSES' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {dashboardData?.assigned_courses?.map((course) => (
            <div
              key={course.id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-purple-300 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-md">
                    {course.course_code}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">
                    {course.student_count} Enrolled Candidates
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900">
                  {course.title}
                </h3>
                <p className="text-xs text-slate-500 mt-2 line-clamp-3 leading-relaxed">
                  {course.description}
                </p>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-600">
                  Questions: <strong className="text-slate-900">{course.question_count}</strong>
                </span>
                <button
                  onClick={() => {
                    setSelectedCourseId(course.id);
                    setActiveTab('MATERIAL');
                  }}
                  className="font-semibold text-purple-700 hover:text-purple-900 inline-flex items-center gap-1"
                >
                  Manage Material <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
